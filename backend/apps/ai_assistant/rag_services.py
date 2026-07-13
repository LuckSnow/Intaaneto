"""Small, synchronous lesson-indexing pipeline for the first RAG slice."""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from dataclasses import dataclass
from typing import Protocol, Sequence

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.courses.models import Lesson

from .models import KnowledgeChunk, KnowledgeSource


CHUNKER_VERSION = 'char-boundary-v1'


class LessonIndexingError(Exception):
    """Raised when approved lesson text cannot be indexed completely."""


class EmbeddingProvider(Protocol):
    """Provider-neutral batch embedding contract."""

    provider_name: str
    model_name: str
    model_revision: str
    dimension: int

    def embed_documents(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        """Return one fixed-size numeric vector for every supplied document."""


class FastEmbedEmbeddingProvider:
    """Lazy local ONNX adapter; model weights load only when indexing."""

    provider_name = 'fastembed'

    def __init__(self):
        self.model_name = settings.RAG_EMBEDDING_MODEL
        self.model_revision = settings.RAG_EMBEDDING_REVISION
        self.dimension = settings.RAG_EMBEDDING_DIMENSION
        self._model = None

    def embed_documents(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        try:
            from fastembed import TextEmbedding

            if self._model is None:
                self._model = TextEmbedding(model_name=self.model_name)
            embeddings = self._model.embed(list(texts))
            return [embedding.tolist() for embedding in embeddings]
        except Exception as exc:
            raise LessonIndexingError('Local embedding provider failed') from exc


@dataclass(frozen=True)
class NormalizedLessonText:
    source_type: str
    text: str
    checksum: str


@dataclass(frozen=True)
class TextChunk:
    ordinal: int
    text: str
    start_offset: int
    end_offset: int


def normalize_lesson_text(lesson: Lesson) -> NormalizedLessonText:
    """Select and normalize the stable teacher-approved text for one lesson."""

    if lesson.extracted_text and lesson.extracted_text.strip():
        source_type = 'extracted_text'
        raw_text = lesson.extracted_text
    else:
        source_type = 'lesson_content'
        raw_text = lesson.content

    text = unicodedata.normalize('NFKC', raw_text or '')
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = [line.rstrip() for line in text.split('\n')]
    text = '\n'.join(lines).strip()
    text = re.sub(r'\n{3,}', '\n\n', text)
    if not text:
        raise LessonIndexingError('Lesson has no indexable text')

    checksum_input = f'{source_type}\0{text}'.encode('utf-8')
    return NormalizedLessonText(
        source_type=source_type,
        text=text,
        checksum=hashlib.sha256(checksum_input).hexdigest(),
    )


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[TextChunk]:
    """Split normalized text deterministically, preferring nearby whitespace."""

    if chunk_size <= 0:
        raise ValueError('chunk_size must be positive')
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError('overlap must satisfy 0 <= overlap < chunk_size')

    chunks: list[TextChunk] = []
    cursor = 0
    text_length = len(text)
    while cursor < text_length:
        end = min(cursor + chunk_size, text_length)
        if end < text_length:
            minimum_break = cursor + (chunk_size // 2)
            break_at = max(
                text.rfind('\n', minimum_break, end),
                text.rfind(' ', minimum_break, end),
            )
            if break_at > cursor:
                end = break_at

        start_offset = cursor
        while start_offset < end and text[start_offset].isspace():
            start_offset += 1
        end_offset = end
        while end_offset > start_offset and text[end_offset - 1].isspace():
            end_offset -= 1

        if start_offset < end_offset:
            chunks.append(TextChunk(
                ordinal=len(chunks),
                text=text[start_offset:end_offset],
                start_offset=start_offset,
                end_offset=end_offset,
            ))

        if end >= text_length:
            break
        next_cursor = max(end - overlap, cursor + 1)
        cursor = next_cursor

    return chunks


def _authorized_lesson(actor, lesson_id: int) -> Lesson:
    if not getattr(actor, 'is_authenticated', False):
        raise PermissionDenied('Authentication is required to index a lesson')

    queryset = Lesson.objects.select_related('course')
    if actor.role != 'admin':
        if actor.role != 'teacher':
            raise PermissionDenied('Only a lesson owner or administrator may index')
        queryset = queryset.filter(course__teacher=actor)

    lesson = queryset.filter(pk=lesson_id).first()
    if lesson is None:
        raise PermissionDenied('Only a lesson owner or administrator may index')
    return lesson


def _validate_embeddings(
    embeddings: Sequence[Sequence[float]],
    expected_count: int,
    expected_dimension: int,
) -> list[list[float]]:
    if len(embeddings) != expected_count:
        raise LessonIndexingError('Embedding provider returned the wrong vector count')

    validated = []
    for embedding in embeddings:
        vector = [float(value) for value in embedding]
        if len(vector) != expected_dimension:
            raise LessonIndexingError('Embedding provider returned the wrong dimension')
        if not all(math.isfinite(value) for value in vector):
            raise LessonIndexingError('Embedding provider returned a non-finite value')
        validated.append(vector)
    return validated


def index_lesson(
    *,
    actor,
    lesson_id: int,
    provider: EmbeddingProvider | None = None,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> tuple[KnowledgeSource, bool]:
    """Authorize, embed, and atomically activate one complete lesson index."""

    lesson = _authorized_lesson(actor, lesson_id)
    normalized = normalize_lesson_text(lesson)
    provider = provider or FastEmbedEmbeddingProvider()
    chunk_size = chunk_size or settings.RAG_CHUNK_SIZE
    if chunk_overlap is None:
        chunk_overlap = settings.RAG_CHUNK_OVERLAP

    identity = {
        'content_checksum': normalized.checksum,
        'embedding_provider': provider.provider_name,
        'embedding_model': provider.model_name,
        'embedding_revision': provider.model_revision,
        'embedding_dimension': provider.dimension,
        'chunker_version': CHUNKER_VERSION,
        'chunk_size': chunk_size,
        'chunk_overlap': chunk_overlap,
    }
    existing = KnowledgeSource.objects.filter(
        lesson=lesson,
        is_active=True,
        status='ready',
        **identity,
    ).first()
    if existing:
        return existing, False

    chunks = chunk_text(normalized.text, chunk_size, chunk_overlap)
    if not chunks:
        raise LessonIndexingError('Lesson produced no chunks')
    if len(chunks) > settings.RAG_MAX_CHUNKS_PER_SOURCE:
        raise LessonIndexingError('Lesson exceeds the configured chunk limit')

    try:
        embeddings = provider.embed_documents([chunk.text for chunk in chunks])
    except LessonIndexingError:
        raise
    except Exception as exc:
        raise LessonIndexingError('Embedding provider failed') from exc
    embeddings = _validate_embeddings(embeddings, len(chunks), provider.dimension)

    with transaction.atomic():
        locked_lesson = Lesson.objects.select_for_update().get(pk=lesson.pk)
        locked_normalized = normalize_lesson_text(locked_lesson)
        if locked_normalized.checksum != normalized.checksum:
            raise LessonIndexingError('Lesson text changed during indexing; retry')
        existing = KnowledgeSource.objects.filter(
            lesson=locked_lesson,
            is_active=True,
            status='ready',
            **identity,
        ).first()
        if existing:
            return existing, False

        latest_version = (
            KnowledgeSource.objects.filter(lesson=locked_lesson)
            .aggregate(max_version=Max('version'))['max_version']
            or 0
        )
        source = KnowledgeSource.objects.create(
            lesson=locked_lesson,
            source_type=normalized.source_type,
            version=latest_version + 1,
            normalized_text=normalized.text,
            status='ready',
            is_active=False,
            **identity,
        )
        KnowledgeChunk.objects.bulk_create([
            KnowledgeChunk(
                source=source,
                ordinal=chunk.ordinal,
                text=chunk.text,
                start_offset=chunk.start_offset,
                end_offset=chunk.end_offset,
                char_count=len(chunk.text),
                embedding=embedding,
            )
            for chunk, embedding in zip(chunks, embeddings)
        ])

        KnowledgeSource.objects.filter(
            lesson=locked_lesson,
            is_active=True,
        ).update(is_active=False, status='archived')
        source.is_active = True
        source.activated_at = timezone.now()
        source.save(update_fields=['is_active', 'activated_at'])

    return source, True
