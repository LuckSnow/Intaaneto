"""Grounded lesson-answer orchestration on top of authorized retrieval."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

from django.conf import settings

from .rag_services import (
    EmbeddingProvider,
    LessonRetrievalResult,
    RetrievedChunk,
    retrieve_lesson_evidence,
)
from .services import AIService, ChatProvider


WEAK_EVIDENCE_FALLBACK = (
    'Mình chưa tìm thấy đủ thông tin trong tài liệu bài học để trả lời câu hỏi '
    'này. Bạn hãy hỏi cụ thể hơn hoặc trao đổi với giảng viên nhé.'
)
NOT_INDEXED_FALLBACK = (
    'Bài học này chưa có chỉ mục kiến thức để AI Tutor tra cứu. Giảng viên cần '
    'index nội dung bài học trước.'
)


@dataclass(frozen=True)
class GroundedAnswer:
    answer: str
    citations: list[dict]
    grounded: bool
    retrieval: dict
    retrieval_metadata: dict
    tokens_used: int | None = None
    response_time_ms: int | None = None


def _select_evidence(result: LessonRetrievalResult) -> list[RetrievedChunk]:
    selected = []
    used_chars = 0
    for chunk in result.chunks:
        if chunk.score < settings.RAG_RETRIEVAL_MIN_SCORE:
            continue
        if len(selected) >= settings.RAG_GENERATION_MAX_EVIDENCE_CHUNKS:
            break
        if used_chars + len(chunk.text) > settings.RAG_GENERATION_MAX_CONTEXT_CHARS:
            break
        selected.append(chunk)
        used_chars += len(chunk.text)
    return selected


def _build_citations(lesson, chunks: list[RetrievedChunk]) -> list[dict]:
    citations = []
    for chunk in chunks:
        excerpt = chunk.text[:settings.RAG_CITATION_EXCERPT_CHARS].strip()
        citations.append({
            'id': f'knowledge-chunk-{chunk.chunk_id}',
            'chunk_id': chunk.chunk_id,
            'source_id': chunk.source_id,
            'source_version': chunk.source_version,
            'lesson_id': lesson.id,
            'lesson_title': lesson.title,
            'source_type': chunk.source_type,
            'ordinal': chunk.ordinal,
            'location': {
                'start_offset': chunk.start_offset,
                'end_offset': chunk.end_offset,
            },
            'excerpt': excerpt,
            'score': chunk.score,
        })
    return citations


def _retrieval_contract(
    result: LessonRetrievalResult,
    *,
    status: str,
    evidence_count: int,
) -> dict:
    return {
        'status': status,
        'source_version': result.source_version,
        'candidate_count': len(result.chunks),
        'evidence_count': evidence_count,
    }


def _retrieval_metadata(
    result: LessonRetrievalResult,
    *,
    status: str,
    selected: list[RetrievedChunk],
    latency_ms: int,
) -> dict:
    return {
        'grounded': status == 'ready',
        'retrieval': {
            'status': status,
            'source_id': result.source_id,
            'source_version': result.source_version,
            'selected_chunks': [
                {'chunk_id': chunk.chunk_id, 'score': chunk.score}
                for chunk in selected
            ],
            'latency_ms': latency_ms,
        },
    }


def answer_lesson_question(
    *,
    actor,
    lesson,
    messages: list[dict[str, str]],
    embedding_provider: Optional[EmbeddingProvider] = None,
    generation_provider: Optional[ChatProvider] = None,
) -> GroundedAnswer:
    """Retrieve authorized evidence, fallback safely, or generate and cite."""

    question = messages[-1]['content'] if messages else ''
    retrieval_started = time.monotonic()
    result = retrieve_lesson_evidence(
        actor=actor,
        lesson_id=lesson.id,
        question=question,
        provider=embedding_provider,
    )
    retrieval_ms = int((time.monotonic() - retrieval_started) * 1000)

    selected = _select_evidence(result) if result.status == 'ready' else []
    status = result.status if selected or result.status != 'ready' else 'weak_evidence'
    retrieval = _retrieval_contract(
        result,
        status=status,
        evidence_count=len(selected),
    )
    metadata = _retrieval_metadata(
        result,
        status=status,
        selected=selected,
        latency_ms=retrieval_ms,
    )
    if status != 'ready':
        fallback = (
            NOT_INDEXED_FALLBACK
            if status == 'not_indexed'
            else WEAK_EVIDENCE_FALLBACK
        )
        return GroundedAnswer(
            answer=fallback,
            citations=[],
            grounded=False,
            retrieval=retrieval,
            retrieval_metadata=metadata,
        )

    evidence = [
        {
            'chunk_id': chunk.chunk_id,
            'ordinal': chunk.ordinal,
            'text': chunk.text,
        }
        for chunk in selected
    ]
    generation = AIService.grounded_chat(
        messages,
        lesson_title=lesson.title,
        evidence=evidence,
        provider=generation_provider,
    )
    return GroundedAnswer(
        answer=generation['content'],
        citations=_build_citations(lesson, selected),
        grounded=True,
        retrieval=retrieval,
        retrieval_metadata=metadata,
        tokens_used=generation.get('tokens_used'),
        response_time_ms=generation.get('response_time_ms'),
    )
