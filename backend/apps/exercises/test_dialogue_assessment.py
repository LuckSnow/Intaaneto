from decimal import Decimal
from unittest.mock import patch

import pytest

from apps.ai_assistant.rag_services import LessonRetrievalResult, RetrievedChunk
from apps.ai_assistant.services import AIProviderError
from apps.courses.models import Course, Enrollment, Lesson, LessonProgress
from apps.users.models import User

from .models import (
    AssessmentAttempt,
    AssessmentQuestion,
    DialogueKnowledgeCheckEvent,
    LessonAssessment,
)


@pytest.fixture
def dialogue_context(teacher_user, student_user):
    course = Course.objects.create(
        title='Kiểm tra hội thoại',
        slug='kiem-tra-hoi-thoai',
        description='Kiểm thử recommendation-only',
        teacher=teacher_user,
        is_published=True,
    )
    lesson = Lesson.objects.create(
        course=course,
        title='RAG căn bản',
        slug='rag-can-ban-dialogue',
        content='RAG truy xuất bằng chứng trước khi sinh câu trả lời.',
        is_published=True,
    )
    enrollment = Enrollment.objects.create(user=student_user, course=course)
    assessment = LessonAssessment.objects.create(
        lesson=lesson,
        title='Đánh giá RAG',
        is_published=True,
    )
    question = AssessmentQuestion.objects.create(
        assessment=assessment,
        prompt='RAG sử dụng retrieval để làm gì?',
        choices=['Tìm bằng chứng liên quan', 'Tạo mật khẩu'],
        correct_choice=0,
        learning_objective='Giải thích vai trò của retrieval',
        explanation='Retrieval tìm bằng chứng từ học liệu được duyệt.',
        order=1,
    )
    return enrollment, assessment, question


def _passed_attempt(assessment, student_user):
    return AssessmentAttempt.objects.create(
        assessment=assessment,
        user=student_user,
        assessment_version=assessment.version,
        threshold_snapshot=assessment.pass_threshold,
        score=Decimal('100.00'),
        passed=True,
        total_questions=1,
        correct_answers=1,
    )


def _ready_retrieval(assessment):
    return LessonRetrievalResult(
        lesson_id=assessment.lesson_id,
        status='ready',
        source_id=5,
        source_version=2,
        chunks=(RetrievedChunk(
            chunk_id=9,
            source_id=5,
            source_version=2,
            lesson_id=assessment.lesson_id,
            source_type='lesson_content',
            ordinal=0,
            text='Retrieval tìm các đoạn bằng chứng liên quan trong học liệu.',
            start_offset=0,
            end_offset=61,
            score=0.9,
        ),),
    )


@pytest.mark.django_db
def test_passed_learner_gets_grounded_recommendation_without_progress_mutation(
    authenticated_client, student_user, dialogue_context
):
    enrollment, assessment, question = dialogue_context
    attempt = _passed_attempt(assessment, student_user)
    generated = {
        'outcome': 'partial',
        'feedback': 'Bạn đã nêu đúng ý tìm bằng chứng nhưng cần nói rõ phạm vi.',
        'next_step': 'Ôn lại cách retrieval giới hạn theo bài học.',
        'tokens_used': 42,
        'response_time_ms': 18,
    }

    with patch(
        'apps.exercises.dialogue_assessment.retrieve_lesson_evidence',
        return_value=_ready_retrieval(assessment),
    ), patch(
        'apps.exercises.dialogue_assessment.AIService.assess_dialogue_response',
        return_value=generated,
    ) as provider:
        response = authenticated_client.post(
            f'/api/exercises/assessments/{assessment.id}/dialogue-check/',
            {
                'question_id': question.id,
                'answer': 'Retrieval tìm thông tin trước khi AI trả lời.',
                'score': 100,
                'passed': True,
            },
            format='json',
        )

    assert response.status_code == 201
    assert response.data['recommendation_only'] is True
    assert response.data['outcome'] == 'partial'
    assert response.data['citations'][0]['chunk_id'] == 9
    assert 'score' not in response.data
    assert 'passed' not in response.data
    assert 'answer' not in response.data
    event = DialogueKnowledgeCheckEvent.objects.get()
    assert event.attempt == attempt
    assert event.outcome == 'partial'
    assert event.evidence_chunk_ids == [9]
    assert len(event.answer_digest) == 64
    assert not hasattr(event, 'answer')
    assert not LessonProgress.objects.exists()
    enrollment.refresh_from_db()
    assert enrollment.progress_percentage == Decimal('0.00')
    assert enrollment.mastery_percentage == Decimal('0.00')
    assert provider.call_args.kwargs['rubric']['expected_answer'] == question.choices[0]


@pytest.mark.django_db
def test_dialogue_check_requires_current_pass_before_retrieval(
    authenticated_client, dialogue_context
):
    _, assessment, question = dialogue_context

    with patch(
        'apps.exercises.dialogue_assessment.retrieve_lesson_evidence',
    ) as retrieval:
        response = authenticated_client.post(
            f'/api/exercises/assessments/{assessment.id}/dialogue-check/',
            {'question_id': question.id, 'answer': 'Câu trả lời thử.'},
            format='json',
        )

    assert response.status_code == 403
    retrieval.assert_not_called()
    assert not DialogueKnowledgeCheckEvent.objects.exists()


@pytest.mark.django_db
def test_dialogue_check_rejects_foreign_question_before_retrieval(
    authenticated_client, student_user, dialogue_context
):
    _, assessment, _ = dialogue_context
    _passed_attempt(assessment, student_user)
    other_lesson = Lesson.objects.create(
        course=assessment.lesson.course,
        title='Bài khác', slug='bai-khac-dialogue', content='Khác',
        is_published=True,
    )
    other_assessment = LessonAssessment.objects.create(
        lesson=other_lesson, title='Khác', is_published=True,
    )
    other_question = AssessmentQuestion.objects.create(
        assessment=other_assessment,
        prompt='Ngoài phạm vi?', choices=['Có', 'Không'], correct_choice=0,
        learning_objective='Ngoài phạm vi', order=1,
    )

    with patch(
        'apps.exercises.dialogue_assessment.retrieve_lesson_evidence',
    ) as retrieval:
        response = authenticated_client.post(
            f'/api/exercises/assessments/{assessment.id}/dialogue-check/',
            {'question_id': other_question.id, 'answer': 'Giả mạo scope.'},
            format='json',
        )

    assert response.status_code == 400
    retrieval.assert_not_called()


@pytest.mark.django_db
def test_weak_evidence_returns_unavailable_without_generation(
    authenticated_client, student_user, dialogue_context
):
    _, assessment, question = dialogue_context
    _passed_attempt(assessment, student_user)
    weak = LessonRetrievalResult(
        lesson_id=assessment.lesson_id,
        status='weak_evidence',
        chunks=(),
    )

    with patch(
        'apps.exercises.dialogue_assessment.retrieve_lesson_evidence',
        return_value=weak,
    ), patch(
        'apps.exercises.dialogue_assessment.AIService.assess_dialogue_response',
    ) as provider:
        response = authenticated_client.post(
            f'/api/exercises/assessments/{assessment.id}/dialogue-check/',
            {'question_id': question.id, 'answer': 'Câu trả lời thử.'},
            format='json',
        )

    assert response.status_code == 201
    assert response.data['outcome'] == 'unavailable'
    assert response.data['citations'] == []
    provider.assert_not_called()
    assert DialogueKnowledgeCheckEvent.objects.get().outcome == 'unavailable'


@pytest.mark.django_db
def test_provider_failure_is_redacted_and_creates_no_success_event(
    authenticated_client, student_user, dialogue_context
):
    _, assessment, question = dialogue_context
    _passed_attempt(assessment, student_user)

    with patch(
        'apps.exercises.dialogue_assessment.retrieve_lesson_evidence',
        return_value=_ready_retrieval(assessment),
    ), patch(
        'apps.exercises.dialogue_assessment.AIService.assess_dialogue_response',
        side_effect=AIProviderError('private provider body'),
    ):
        response = authenticated_client.post(
            f'/api/exercises/assessments/{assessment.id}/dialogue-check/',
            {'question_id': question.id, 'answer': 'Câu trả lời thử.'},
            format='json',
        )

    assert response.status_code == 503
    assert 'private provider body' not in str(response.data)
    assert not DialogueKnowledgeCheckEvent.objects.exists()


@pytest.mark.django_db
def test_outsider_cannot_discover_dialogue_check(
    api_client, dialogue_context
):
    _, assessment, question = dialogue_context
    outsider = User.objects.create_user(
        email='dialogue-outsider@example.invalid',
        username='dialogue-outsider',
        password='LocalTestOnly-123!',
        is_verified=True,
    )
    api_client.force_authenticate(outsider)

    with patch(
        'apps.exercises.dialogue_assessment.retrieve_lesson_evidence',
    ) as retrieval:
        response = api_client.post(
            f'/api/exercises/assessments/{assessment.id}/dialogue-check/',
            {'question_id': question.id, 'answer': 'Tôi không được enroll.'},
            format='json',
        )

    assert response.status_code == 404
    retrieval.assert_not_called()
