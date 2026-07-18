"""RAG-grounded, recommendation-only dialogue knowledge checks."""

from __future__ import annotations

from hashlib import sha256
import hmac

from django.conf import settings
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.ai_assistant.rag_services import retrieve_lesson_evidence
from apps.ai_assistant.services import AIService
from apps.courses.models import Enrollment

from .models import DialogueKnowledgeCheckEvent


UNAVAILABLE_FEEDBACK = (
    'Kho kiến thức chưa có đủ bằng chứng để thực hiện kiểm tra hội thoại này.'
)


def _answer_digest(answer: str) -> str:
    return hmac.new(
        settings.SECRET_KEY.encode('utf-8'),
        answer.encode('utf-8'),
        sha256,
    ).hexdigest()


def _generation_model() -> str:
    if settings.AI_GENERATION_PROVIDER == 'gemini':
        return settings.GEMINI_GENERATION_MODEL
    return settings.AI_GENERATION_MODEL


def _selected_evidence(retrieval):
    selected = []
    used_chars = 0
    if retrieval.status != 'ready':
        return selected
    for chunk in retrieval.chunks:
        if chunk.score < settings.RAG_RETRIEVAL_MIN_SCORE:
            continue
        if len(selected) >= settings.RAG_GENERATION_MAX_EVIDENCE_CHUNKS:
            break
        if used_chars + len(chunk.text) > settings.RAG_GENERATION_MAX_CONTEXT_CHARS:
            break
        selected.append(chunk)
        used_chars += len(chunk.text)
    return selected


def _citations(lesson, chunks):
    return [
        {
            'id': f'knowledge-chunk-{chunk.chunk_id}',
            'chunk_id': chunk.chunk_id,
            'lesson_id': lesson.id,
            'lesson_title': lesson.title,
            'source_id': chunk.source_id,
            'source_version': chunk.source_version,
            'location': {
                'start_offset': chunk.start_offset,
                'end_offset': chunk.end_offset,
                'page_start': chunk.page_start,
                'page_end': chunk.page_end,
            },
            'excerpt': chunk.text[:settings.RAG_CITATION_EXCERPT_CHARS].strip(),
        }
        for chunk in chunks
    ]


def run_dialogue_knowledge_check(
    *, assessment, user, question_id: int, learner_answer: str, provider=None,
):
    """Evaluate after a deterministic pass without changing learning state."""

    if user.role != 'student':
        raise PermissionDenied('Chỉ học viên mới có thể dùng kiểm tra hội thoại.')
    if not Enrollment.objects.filter(
        user=user,
        course=assessment.lesson.course,
    ).exists():
        raise PermissionDenied('Bạn chưa đăng ký khóa học này.')

    attempt = assessment.attempts.filter(
        user=user,
        assessment_version=assessment.version,
        passed=True,
    ).order_by('-submitted_at', '-id').first()
    if attempt is None:
        raise PermissionDenied(
            'Hãy hoàn thành bài đánh giá trắc nghiệm trước khi tự kiểm tra hội thoại.'
        )
    question = assessment.questions.filter(pk=question_id).first()
    if question is None:
        raise ValidationError({'question_id': 'Câu hỏi không thuộc bài đánh giá này.'})
    if question.correct_choice >= len(question.choices):
        raise ValidationError({'question_id': 'Rubric câu hỏi không hợp lệ.'})

    retrieval_query = ' '.join(
        part for part in (question.prompt, question.learning_objective) if part
    )[:settings.RAG_MAX_QUESTION_CHARS]
    retrieval = retrieve_lesson_evidence(
        actor=user,
        lesson_id=assessment.lesson_id,
        question=retrieval_query,
    )
    selected = _selected_evidence(retrieval)
    digest = _answer_digest(learner_answer)
    if not selected:
        event = DialogueKnowledgeCheckEvent.objects.create(
            attempt=attempt,
            question=question,
            assessment_version=assessment.version,
            learning_objective_snapshot=question.learning_objective,
            outcome='unavailable',
            answer_digest=digest,
        )
        return {
            'event_id': event.id,
            'recommendation_only': True,
            'outcome': 'unavailable',
            'feedback': UNAVAILABLE_FEEDBACK,
            'next_step': 'Hãy ôn bằng tài liệu hoặc hỏi giảng viên trước.',
            'learning_objective': question.learning_objective,
            'citations': [],
        }

    generated = AIService.assess_dialogue_response(
        rubric={
            'question': question.prompt,
            'learning_objective': question.learning_objective,
            'expected_answer': question.choices[question.correct_choice],
            'teacher_explanation': question.explanation,
        },
        evidence=[
            {'chunk_id': chunk.chunk_id, 'text': chunk.text}
            for chunk in selected
        ],
        learner_answer=learner_answer,
        provider=provider,
    )
    event = DialogueKnowledgeCheckEvent.objects.create(
        attempt=attempt,
        question=question,
        assessment_version=assessment.version,
        learning_objective_snapshot=question.learning_objective,
        outcome=generated['outcome'],
        answer_digest=digest,
        evidence_chunk_ids=[chunk.chunk_id for chunk in selected],
        generation_provider=settings.AI_GENERATION_PROVIDER[:32],
        generation_model=_generation_model()[:100],
        tokens_used=generated['tokens_used'],
        latency_ms=generated['response_time_ms'],
    )
    return {
        'event_id': event.id,
        'recommendation_only': True,
        'outcome': generated['outcome'],
        'feedback': generated['feedback'],
        'next_step': generated['next_step'],
        'learning_objective': question.learning_objective,
        'citations': _citations(assessment.lesson, selected),
    }
