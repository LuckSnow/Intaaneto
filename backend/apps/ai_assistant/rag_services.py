"""Explicit lesson indexing and authorized retrieval services for RAG."""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from dataclasses import dataclass
from typing import Protocol, Sequence

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import connection, transaction
from django.db.models import Max
from django.utils import timezone
from pgvector.django import CosineDistance

from apps.courses.models import Lesson

from .access import accessible_lesson_queryset
from .models import KnowledgeChunk, KnowledgeSource


CHUNKER_VERSION = 'char-boundary-v1'


class LessonIndexingError(Exception):
    """Raised when approved lesson text cannot be indexed completely."""


class LessonRetrievalError(Exception):
    """Raised when a lesson retrieval request cannot be completed safely."""


class EmbeddingProviderError(Exception):
    """Provider-neutral embedding failure without private implementation detail."""


class EmbeddingValidationError(Exception):
    """Raised when a provider returns unusable vectors."""


class EmbeddingProvider(Protocol):
    """Provider-neutral batch embedding contract."""

    provider_name: str
    model_name: str
    model_revision: str
    dimension: int

    def embed_documents(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        """Return one fixed-size numeric vector for every supplied document."""

    def embed_query(self, text: str) -> Sequence[float]:
        """Return one fixed-size vector in the same space as the documents."""


class FastEmbedEmbeddingProvider:
    """Lazy local ONNX adapter; model weights load only when indexing."""

    provider_name = 'fastembed'

    def __init__(self):
        self.model_name = settings.RAG_EMBEDDING_MODEL
        self.model_revision = settings.RAG_EMBEDDING_REVISION
        self.dimension = settings.RAG_EMBEDDING_DIMENSION
        self._model = None

    def _get_model(self):
        try:
            from fastembed import TextEmbedding

            if self._model is None:
                self._model = TextEmbedding(model_name=self.model_name)
            return self._model
        except Exception as exc:
            raise EmbeddingProviderError('Local embedding provider failed') from exc

    def embed_documents(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        try:
            embeddings = self._get_model().embed(list(texts))
            return [embedding.tolist() for embedding in embeddings]
        except EmbeddingProviderError:
            raise
        except Exception as exc:
            raise EmbeddingProviderError('Local embedding provider failed') from exc

    def embed_query(self, text: str) -> Sequence[float]:
        embeddings = self.embed_documents([text])
        if len(embeddings) != 1:
            raise EmbeddingProviderError('Local embedding provider failed')
        return embeddings[0]


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


@dataclass(frozen=True)
class RetrievedChunk:
    """One authorized, ranked chunk with stable source metadata."""

    chunk_id: int
    source_id: int
    source_version: int
    lesson_id: int
    source_type: str
    ordinal: int
    text: str
    start_offset: int
    end_offset: int
    score: float
    page_start: int | None = None
    page_end: int | None = None


@dataclass(frozen=True)
class LessonRetrievalResult:
    """Result of retrieval before any answer-generation provider is invoked."""

    lesson_id: int
    status: str
    chunks: tuple[RetrievedChunk, ...]
    source_id: int | None = None
    source_version: int | None = None

    @property
    def has_sufficient_evidence(self) -> bool:
        return self.status == 'ready'


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


PDF_PAGE_MARKER_PATTERN = re.compile(r'^--- Trang ([1-9]\d*) ---$', re.MULTILINE)


def pdf_page_ranges(text: str, chunks: Sequence[TextChunk]):
    """Map normalized extracted-text offsets to original PDF page ranges."""

    markers = [
        (match.start(), int(match.group(1)))
        for match in PDF_PAGE_MARKER_PATTERN.finditer(text)
    ]
    if not markers:
        return [(None, None) for _chunk in chunks]

    page_intervals = [
        (
            marker_offset,
            markers[index + 1][0] if index + 1 < len(markers) else len(text),
            page_number,
        )
        for index, (marker_offset, page_number) in enumerate(markers)
    ]
    ranges = []
    for chunk in chunks:
        pages = [
            page_number
            for interval_start, interval_end, page_number in page_intervals
            if interval_start < chunk.end_offset and interval_end > chunk.start_offset
        ]
        ranges.append((pages[0], pages[-1]) if pages else (None, None))
    return ranges


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
        raise EmbeddingValidationError('Embedding provider returned the wrong vector count')

    validated = []
    for embedding in embeddings:
        try:
            vector = [float(value) for value in embedding]
        except (TypeError, ValueError, OverflowError) as exc:
            raise EmbeddingValidationError(
                'Embedding provider returned a non-numeric value'
            ) from exc
        if len(vector) != expected_dimension:
            raise EmbeddingValidationError('Embedding provider returned the wrong dimension')
        if not all(math.isfinite(value) for value in vector):
            raise EmbeddingValidationError('Embedding provider returned a non-finite value')
        if not any(value != 0 for value in vector):
            raise EmbeddingValidationError('Embedding provider returned a zero vector')
        validated.append(vector)
    return validated


def _embed_chunks(provider: EmbeddingProvider, chunks: Sequence[TextChunk]):
    try:
        raw_embeddings = provider.embed_documents([chunk.text for chunk in chunks])
        return _validate_embeddings(
            raw_embeddings,
            expected_count=len(chunks),
            expected_dimension=provider.dimension,
        )
    except LessonIndexingError:
        raise
    except EmbeddingValidationError as exc:
        raise LessonIndexingError(str(exc)) from exc
    except Exception as exc:
        raise LessonIndexingError('Embedding provider failed') from exc


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

    embeddings = _embed_chunks(provider, chunks)
    page_ranges = (
        pdf_page_ranges(normalized.text, chunks)
        if normalized.source_type == 'extracted_text'
        else [(None, None) for _chunk in chunks]
    )

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
                page_start=page_range[0],
                page_end=page_range[1],
            )
            for chunk, embedding, page_range in zip(chunks, embeddings, page_ranges)
        ])

        KnowledgeSource.objects.filter(
            lesson=locked_lesson,
            is_active=True,
        ).update(is_active=False, status='archived')
        source.is_active = True
        source.activated_at = timezone.now()
        source.save(update_fields=['is_active', 'activated_at'])

    return source, True


def _authorized_retrieval_lesson(actor, lesson_id: int) -> Lesson:
    if not getattr(actor, 'is_authenticated', False):
        raise PermissionDenied('Authentication is required to retrieve lesson evidence')

    lesson = (
        accessible_lesson_queryset(actor)
        .select_related('course')
        .filter(pk=lesson_id)
        .first()
    )
    if lesson is None:
        raise PermissionDenied('Lesson evidence is not available to this actor')
    return lesson


def _normalize_question(question: str) -> str:
    text = unicodedata.normalize('NFKC', question or '')
    text = re.sub(r'\s+', ' ', text).strip()
    if not text:
        raise LessonRetrievalError('Question must not be empty')
    if len(text) > settings.RAG_MAX_QUESTION_CHARS:
        raise LessonRetrievalError('Question exceeds the configured length limit')
    return text


def _cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise LessonRetrievalError('Stored embedding dimension is incompatible')
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return -1.0
    return max(-1.0, min(1.0, numerator / (left_norm * right_norm)))


def _rank_chunks(source: KnowledgeSource, query_vector, top_k: int):
    """Rank only chunks already constrained to one authorized active source."""

    queryset = KnowledgeChunk.objects.filter(source=source)
    if connection.vendor == 'postgresql':
        return [
            (chunk, max(-1.0, min(1.0, 1.0 - float(chunk.distance))))
            for chunk in queryset.annotate(
                distance=CosineDistance('embedding', query_vector),
            ).order_by('distance', 'ordinal', 'id')[:top_k]
        ]

    # SQLite is used only by the isolated test settings. Scope filtering still
    # happens in the database before the small candidate set is ranked here.
    ranked = [
        (chunk, _cosine_similarity(query_vector, list(chunk.embedding)))
        for chunk in queryset
    ]
    ranked.sort(key=lambda item: (-item[1], item[0].ordinal, item[0].id))
    return ranked[:top_k]


def retrieve_lesson_evidence(
    *,
    actor,
    lesson_id: int,
    question: str,
    provider: EmbeddingProvider | None = None,
    top_k: int | None = None,
    minimum_score: float | None = None,
) -> LessonRetrievalResult:
    """Authorize first, then return ranked evidence without invoking an LLM."""

    lesson = _authorized_retrieval_lesson(actor, lesson_id)
    question = _normalize_question(question)
    provider = provider or FastEmbedEmbeddingProvider()
    top_k = settings.RAG_RETRIEVAL_TOP_K if top_k is None else top_k
    minimum_score = (
        settings.RAG_RETRIEVAL_MIN_SCORE
        if minimum_score is None
        else minimum_score
    )
    if not 1 <= top_k <= settings.RAG_RETRIEVAL_MAX_TOP_K:
        raise LessonRetrievalError('top_k exceeds the configured retrieval limit')
    if not -1.0 <= minimum_score <= 1.0:
        raise LessonRetrievalError('minimum_score must be between -1 and 1')

    source = KnowledgeSource.objects.filter(
        lesson=lesson,
        is_active=True,
        status='ready',
        embedding_provider=provider.provider_name,
        embedding_model=provider.model_name,
        embedding_revision=provider.model_revision,
        embedding_dimension=provider.dimension,
    ).first()
    if source is None:
        return LessonRetrievalResult(
            lesson_id=lesson.id,
            status='not_indexed',
            chunks=(),
        )

    try:
        raw_vector = provider.embed_query(question)
        query_vector = _validate_embeddings(
            [raw_vector],
            expected_count=1,
            expected_dimension=source.embedding_dimension,
        )[0]
    except (EmbeddingProviderError, EmbeddingValidationError) as exc:
        raise LessonRetrievalError('Query embedding failed') from exc
    except Exception as exc:
        raise LessonRetrievalError('Query embedding failed') from exc

    ranked = _rank_chunks(source, query_vector, top_k)
    chunks = tuple(
        RetrievedChunk(
            chunk_id=chunk.id,
            source_id=source.id,
            source_version=source.version,
            lesson_id=lesson.id,
            source_type=source.source_type,
            ordinal=chunk.ordinal,
            text=chunk.text,
            start_offset=chunk.start_offset,
            end_offset=chunk.end_offset,
            score=round(score, 6),
            page_start=chunk.page_start,
            page_end=chunk.page_end,
        )
        for chunk, score in ranked
    )
    status = (
        'ready'
        if ranked and ranked[0][1] >= minimum_score
        else 'weak_evidence'
    )
    return LessonRetrievalResult(
        lesson_id=lesson.id,
        source_id=source.id,
        source_version=source.version,
        status=status,
        chunks=chunks,
    )
