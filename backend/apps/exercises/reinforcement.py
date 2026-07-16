"""RAG-backed review packets for objectives missed in an assessment attempt."""

from __future__ import annotations

from django.conf import settings
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.ai_assistant.rag_services import retrieve_lesson_evidence

MAX_REINFORCEMENT_OBJECTIVES_HARD_LIMIT = 10


def _citation(lesson, chunk):
    return {
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
        'excerpt': chunk.text[:settings.RAG_CITATION_EXCERPT_CHARS].strip(),
        'score': chunk.score,
    }


def build_reinforcement_packet(*, attempt, actor, embedding_provider=None):
    """Retrieve bounded lesson evidence for server-recorded weak objectives."""

    if actor.role != 'student' or attempt.user_id != actor.id:
        raise PermissionDenied('Bạn không có quyền xem nội dung củng cố này.')
    assessment = attempt.assessment
    if attempt.assessment_version != assessment.version:
        raise ValidationError({
            'attempt_id': 'Kết quả này thuộc phiên bản bài đánh giá cũ.'
        })
    if attempt.passed:
        raise ValidationError({
            'attempt_id': 'Kết quả đã đạt không cần phiên củng cố bắt buộc.'
        })

    objective_limit = max(
        1,
        min(
            settings.RAG_REINFORCEMENT_MAX_OBJECTIVES,
            MAX_REINFORCEMENT_OBJECTIVES_HARD_LIMIT,
        ),
    )
    objectives = []
    for raw_objective in attempt.weak_objectives:
        if not isinstance(raw_objective, str) or not raw_objective.strip():
            continue
        objective = raw_objective.strip()
        if objective not in objectives:
            objectives.append(objective)
        if len(objectives) >= objective_limit:
            break
    if not objectives:
        raise ValidationError({
            'attempt_id': 'Kết quả này không có mục tiêu cần củng cố.'
        })

    lesson = assessment.lesson
    items = []
    for objective in objectives:
        result = retrieve_lesson_evidence(
            actor=actor,
            lesson_id=lesson.id,
            question=objective,
            provider=embedding_provider,
            top_k=max(
                1,
                min(
                    settings.RAG_REINFORCEMENT_TOP_K,
                    settings.RAG_RETRIEVAL_MAX_TOP_K,
                ),
            ),
        )
        selected = (
            [
                chunk
                for chunk in result.chunks
                if chunk.score >= settings.RAG_RETRIEVAL_MIN_SCORE
            ]
            if result.status == 'ready'
            else []
        )
        status = result.status if selected or result.status != 'ready' else 'weak_evidence'
        items.append({
            'learning_objective': objective,
            'status': status,
            'message': (
                'Đã tìm thấy phần học liệu phù hợp để ôn lại.'
                if status == 'ready'
                else 'Chưa tìm thấy phần học liệu đủ liên quan cho mục tiêu này.'
            ),
            'tutor_prompt': (
                'Hãy giải thích mục tiêu học tập này bằng nội dung của bài học và '
                f'cho mình một ví dụ: {objective}'
            ),
            'citations': [_citation(lesson, chunk) for chunk in selected],
        })

    ready_count = sum(item['status'] == 'ready' for item in items)
    if ready_count == len(items):
        status = 'ready'
    elif ready_count:
        status = 'partial'
    elif all(item['status'] == 'not_indexed' for item in items):
        status = 'not_indexed'
    else:
        status = 'weak_evidence'

    return {
        'attempt_id': attempt.id,
        'assessment_id': assessment.id,
        'lesson_id': lesson.id,
        'status': status,
        'items': items,
        'truncated_objectives': max(
            0,
            len(attempt.weak_objectives) - len(objectives),
        ),
    }
