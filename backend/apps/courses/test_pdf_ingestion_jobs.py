import uuid
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.ai_assistant.models import KnowledgeSource
from apps.users.models import User

from .ingestion import IngestionQueueError, queue_pdf_ingestion
from .models import Course, Lesson, LessonIngestionJob
from .services import PDFIngestionError
from .tasks import process_pdf_lesson_job


@pytest.fixture
def queued_lesson(teacher_user):
    owned_course = Course.objects.create(
        title='Course ingestion jobs',
        slug='course-ingestion-jobs',
        description='Kiểm thử worker',
        teacher=teacher_user,
    )
    return Lesson.objects.create(
        course=owned_course,
        title='PDF chạy nền',
        slug='pdf-chay-nen',
        uploaded_file=SimpleUploadedFile(
            'lesson.pdf',
            b'%PDF-test-placeholder',
            content_type='application/pdf',
        ),
        processing_status='pending',
    )


def _source_for(lesson):
    return KnowledgeSource.objects.create(
        lesson=lesson,
        source_type='extracted_text',
        version=1,
        content_checksum='a' * 64,
        normalized_text='--- Trang 1 ---\nNội dung.',
        status='ready',
        is_active=True,
        embedding_provider='test',
        embedding_model='test-model',
        embedding_revision='v1',
        embedding_dimension=3,
        chunker_version='test-v1',
        chunk_size=100,
        chunk_overlap=10,
    )


@pytest.mark.django_db
def test_queue_deduplicates_one_active_job(teacher_user, queued_lesson):
    with patch('apps.courses.tasks.process_pdf_lesson_job.apply_async') as dispatch:
        first, first_created = queue_pdf_ingestion(
            actor=teacher_user,
            lesson=queued_lesson,
        )
        second, second_created = queue_pdf_ingestion(
            actor=teacher_user,
            lesson=queued_lesson,
        )

    assert first_created is True
    assert second_created is False
    assert second.id == first.id
    assert LessonIngestionJob.objects.count() == 1
    dispatch.assert_called_once_with(
        args=[first.id],
        task_id=str(first.task_id),
    )


@pytest.mark.django_db
def test_broker_failure_is_persisted_and_never_leaves_false_pending_state(
    teacher_user, queued_lesson
):
    with patch(
        'apps.courses.tasks.process_pdf_lesson_job.apply_async',
        side_effect=RuntimeError('private broker detail'),
    ):
        with pytest.raises(IngestionQueueError, match='tạm thời không khả dụng'):
            queue_pdf_ingestion(actor=teacher_user, lesson=queued_lesson)

    job = LessonIngestionJob.objects.get(lesson=queued_lesson)
    queued_lesson.refresh_from_db()
    assert job.status == 'failed'
    assert job.failure_code == 'queue_unavailable'
    assert 'private broker detail' not in job.safe_error
    assert queued_lesson.processing_status == 'failed'
    assert queued_lesson.processing_error == job.safe_error


@pytest.mark.django_db
def test_transient_worker_failure_retries_then_completes(
    teacher_user, queued_lesson, settings
):
    settings.LESSON_INGESTION_MAX_RETRIES = 2
    settings.LESSON_INGESTION_RETRY_BASE_SECONDS = 0
    source = _source_for(queued_lesson)
    job = LessonIngestionJob.objects.create(
        lesson=queued_lesson,
        requested_by=teacher_user,
        task_id=uuid.uuid4(),
    )

    with patch(
        'apps.courses.tasks.process_pdf_lesson',
        side_effect=[
            PDFIngestionError('Lỗi index an toàn', retryable=True),
            (source, True),
        ],
    ) as process:
        result = process_pdf_lesson_job.apply(args=[job.id])

    job.refresh_from_db()
    assert result.successful()
    assert process.call_count == 2
    assert job.status == 'completed'
    assert job.attempts == 2
    assert job.knowledge_source_id == source.id
    assert job.index_created is True


@pytest.mark.django_db
def test_invalid_pdf_failure_is_not_retried(teacher_user, queued_lesson):
    job = LessonIngestionJob.objects.create(
        lesson=queued_lesson,
        requested_by=teacher_user,
        task_id=uuid.uuid4(),
    )
    with patch(
        'apps.courses.tasks.process_pdf_lesson',
        side_effect=PDFIngestionError('Không thể đọc file PDF'),
    ) as process:
        result = process_pdf_lesson_job.apply(args=[job.id])

    job.refresh_from_db()
    assert result.successful()
    assert process.call_count == 1
    assert job.status == 'failed'
    assert job.attempts == 1
    assert job.failure_code == 'processing_failed'


@pytest.mark.django_db
def test_worker_rechecks_authorization_after_role_is_revoked(
    teacher_user, queued_lesson
):
    job = LessonIngestionJob.objects.create(
        lesson=queued_lesson,
        requested_by=teacher_user,
        task_id=uuid.uuid4(),
    )
    teacher_user.role = 'student'
    teacher_user.save(update_fields=['role'])

    result = process_pdf_lesson_job.apply(args=[job.id])

    job.refresh_from_db()
    assert result.successful()
    assert job.status == 'failed'
    assert job.failure_code == 'authorization_revoked'
    assert job.attempts == 1
    assert not KnowledgeSource.objects.filter(lesson=queued_lesson).exists()


@pytest.mark.django_db
def test_worker_discards_job_deleted_before_delivery():
    result = process_pdf_lesson_job.apply(args=[999999])

    assert result.successful()
    assert result.result == {'job_id': 999999, 'status': 'discarded'}


@pytest.mark.django_db
def test_processing_status_exposes_bounded_job_state_without_task_identifier(
    api_client, teacher_user, queued_lesson
):
    api_client.force_authenticate(teacher_user)
    job = LessonIngestionJob.objects.create(
        lesson=queued_lesson,
        requested_by=teacher_user,
        task_id=uuid.uuid4(),
        status='failed',
        attempts=2,
        failure_code='processing_failed',
        safe_error='Lỗi an toàn',
    )
    queued_lesson.processing_status = 'failed'
    queued_lesson.processing_error = job.safe_error
    queued_lesson.save(update_fields=['processing_status', 'processing_error'])

    response = api_client.get(
        f'/api/courses/lessons/{queued_lesson.id}/processing_status/'
    )

    assert response.status_code == 200
    assert response.data['status'] == 'failed'
    assert response.data['error'] == 'Lỗi an toàn'
    assert response.data['ingestion_job'] == {
        'id': job.id,
        'status': 'failed',
        'attempts': 2,
        'failure_code': 'processing_failed',
        'knowledge_source_id': None,
        'index_created': None,
    }
    assert str(job.task_id) not in str(response.data)


@pytest.mark.django_db
def test_teacher_restores_only_owned_course_ingestion_statuses(
    api_client, teacher_user, queued_lesson
):
    job = LessonIngestionJob.objects.create(
        lesson=queued_lesson,
        requested_by=teacher_user,
        task_id=uuid.uuid4(),
        status='completed',
        attempts=1,
    )
    api_client.force_authenticate(teacher_user)

    response = api_client.get(
        '/api/courses/lessons/ingestion-statuses/',
        {'course': queued_lesson.course_id},
    )

    assert response.status_code == 200
    assert response.data['results'] == [{
        'lesson_id': queued_lesson.id,
        'lesson_title': queued_lesson.title,
        'processing_status': queued_lesson.processing_status,
        'error': '',
        'ingestion_job': {
            'id': job.id,
            'status': 'completed',
            'attempts': 1,
            'failure_code': '',
            'knowledge_source_id': None,
            'index_created': None,
        },
    }]
    assert str(job.task_id) not in str(response.data)

    outsider = User.objects.create_user(
        email='ingestion-outsider@example.invalid',
        username='ingestion-outsider',
        password='LocalTestOnly-123!',
        role='teacher',
        is_verified=True,
    )
    api_client.force_authenticate(outsider)
    denied = api_client.get(
        '/api/courses/lessons/ingestion-statuses/',
        {'course': queued_lesson.course_id},
    )
    assert denied.status_code == 403
