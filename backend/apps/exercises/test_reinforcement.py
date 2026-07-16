from unittest.mock import patch

import pytest
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.ai_assistant.models import KnowledgeChunk, KnowledgeSource
from apps.ai_assistant.rag_services import LessonRetrievalError
from apps.courses.models import Course, Enrollment, Lesson
from apps.users.models import User

from .models import AssessmentAttempt, LessonAssessment
from .reinforcement import build_reinforcement_packet


class ReinforcementEmbeddingProvider:
    provider_name = 'reinforcement-test'
    model_name = 'reinforcement-model-v1'
    model_revision = 'reinforcement-revision-v1'
    dimension = 3

    def __init__(self):
        self.query_calls = []

    def embed_documents(self, texts):
        raise AssertionError('Reinforcement must not embed lesson documents')

    def embed_query(self, text):
        self.query_calls.append(text)
        return [1.0, 0.0, 0.0]


@pytest.fixture
def reinforcement_context(teacher_user, student_user):
    course = Course.objects.create(
        title='Khóa củng cố',
        slug='khoa-cung-co',
        description='Kiểm thử RAG củng cố',
        teacher=teacher_user,
        is_published=True,
    )
    lesson = Lesson.objects.create(
        course=course,
        title='Bài RAG',
        slug='bai-rag-cung-co',
        content='RAG truy xuất bằng chứng trước khi sinh câu trả lời.',
        is_published=True,
    )
    Enrollment.objects.create(user=student_user, course=course)
    assessment = LessonAssessment.objects.create(
        lesson=lesson,
        title='Kiểm tra RAG',
        is_published=True,
    )
    attempt = AssessmentAttempt.objects.create(
        assessment=assessment,
        user=student_user,
        assessment_version=assessment.version,
        threshold_snapshot=70,
        score='0.00',
        passed=False,
        total_questions=1,
        correct_answers=0,
        weak_objectives=['Phân biệt retrieval và generation'],
    )
    source = KnowledgeSource.objects.create(
        lesson=lesson,
        source_type='lesson_content',
        version=1,
        content_checksum='reinforcement-checksum',
        normalized_text=lesson.content,
        status='ready',
        is_active=True,
        embedding_provider='reinforcement-test',
        embedding_model='reinforcement-model-v1',
        embedding_revision='reinforcement-revision-v1',
        embedding_dimension=3,
        chunker_version='test-v1',
        chunk_size=100,
        chunk_overlap=10,
    )
    chunk = KnowledgeChunk.objects.create(
        source=source,
        ordinal=0,
        text=lesson.content,
        start_offset=0,
        end_offset=len(lesson.content),
        char_count=len(lesson.content),
        embedding=[1.0, 0.0, 0.0],
    )
    return course, lesson, assessment, attempt, chunk


@pytest.mark.django_db
def test_failed_attempt_retrieves_authorized_citations_only(
    student_user, reinforcement_context
):
    _, lesson, assessment, attempt, chunk = reinforcement_context
    provider = ReinforcementEmbeddingProvider()

    packet = build_reinforcement_packet(
        attempt=attempt,
        actor=student_user,
        embedding_provider=provider,
    )

    assert packet['attempt_id'] == attempt.id
    assert packet['assessment_id'] == assessment.id
    assert packet['lesson_id'] == lesson.id
    assert packet['status'] == 'ready'
    assert provider.query_calls == ['Phân biệt retrieval và generation']
    assert packet['items'][0]['learning_objective'] == provider.query_calls[0]
    assert [item['chunk_id'] for item in packet['items'][0]['citations']] == [
        chunk.id
    ]
    assert packet['items'][0]['citations'][0]['lesson_id'] == lesson.id
    assert 'correct_choice' not in packet['items'][0]
    assert 'explanation' not in packet['items'][0]


@pytest.mark.django_db
def test_other_learner_is_denied_before_embedding(
    reinforcement_context,
):
    course, _, _, attempt, _ = reinforcement_context
    outsider = User.objects.create_user(
        email='reinforcement-outsider@example.invalid',
        username='reinforcement-outsider',
        full_name='Reinforcement Outsider',
        password='LocalTestOnly-123!',
        is_verified=True,
    )
    Enrollment.objects.create(user=outsider, course=course)
    provider = ReinforcementEmbeddingProvider()

    with pytest.raises(PermissionDenied):
        build_reinforcement_packet(
            attempt=attempt,
            actor=outsider,
            embedding_provider=provider,
        )

    assert provider.query_calls == []


@pytest.mark.django_db
def test_passed_or_stale_attempt_cannot_create_reinforcement(
    student_user, reinforcement_context
):
    _, _, assessment, attempt, _ = reinforcement_context
    attempt.passed = True
    attempt.save(update_fields=['passed'])
    with pytest.raises(ValidationError, match='đã đạt'):
        build_reinforcement_packet(attempt=attempt, actor=student_user)

    attempt.passed = False
    attempt.assessment_version = assessment.version - 1
    attempt.save(update_fields=['passed', 'assessment_version'])
    with pytest.raises(ValidationError, match='phiên bản'):
        build_reinforcement_packet(attempt=attempt, actor=student_user)


@pytest.mark.django_db
def test_not_indexed_reinforcement_falls_back_without_embedding(
    student_user, reinforcement_context
):
    _, _, _, attempt, chunk = reinforcement_context
    chunk.source.delete()
    provider = ReinforcementEmbeddingProvider()

    packet = build_reinforcement_packet(
        attempt=attempt,
        actor=student_user,
        embedding_provider=provider,
    )

    assert packet['status'] == 'not_indexed'
    assert packet['items'][0]['status'] == 'not_indexed'
    assert packet['items'][0]['citations'] == []
    assert provider.query_calls == []

@pytest.mark.django_db
def test_api_does_not_disclose_another_learners_attempt(
    api_client, student_user, reinforcement_context
):
    course, _, assessment, attempt, _ = reinforcement_context
    other = User.objects.create_user(
        email='reinforcement-api-other@example.invalid',
        username='reinforcement-api-other',
        full_name='Other Learner',
        password='LocalTestOnly-123!',
        is_verified=True,
    )
    Enrollment.objects.create(user=other, course=course)
    api_client.force_authenticate(other)

    response = api_client.post(
        f'/api/exercises/assessments/{assessment.id}/reinforcement/',
        {'attempt_id': attempt.id},
        format='json',
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_api_redacts_retrieval_failure(
    authenticated_client, reinforcement_context
):
    _, _, assessment, attempt, _ = reinforcement_context
    with patch(
        'apps.exercises.views.build_reinforcement_packet',
        side_effect=LessonRetrievalError('private embedding detail'),
    ):
        response = authenticated_client.post(
            f'/api/exercises/assessments/{assessment.id}/reinforcement/',
            {'attempt_id': attempt.id},
            format='json',
        )

    assert response.status_code == 503
    assert 'private embedding detail' not in str(response.data)
