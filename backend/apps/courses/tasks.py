"""Celery tasks for bounded, durable lesson PDF ingestion."""

from celery import shared_task
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from .models import Lesson, LessonIngestionJob, LessonVideoGenerationJob
from .services import PDFIngestionError, process_pdf_lesson
from .video_generation import (
    VideoGenerationError,
    process_stored_video_job,
)


def _mark_failed(job_id, *, code, message):
    now = timezone.now()
    with transaction.atomic():
        job = LessonIngestionJob.objects.select_for_update().filter(pk=job_id).first()
        if job is None:
            return False
        if job.status == 'completed':
            return False
        job.status = 'failed'
        job.failure_code = code
        job.safe_error = message[:255]
        job.completed_at = now
        job.save(update_fields=['status', 'failure_code', 'safe_error', 'completed_at'])
        Lesson.objects.filter(pk=job.lesson_id).update(
            processing_status='failed',
            processing_error=message[:255],
        )
    return True


@shared_task(bind=True, acks_late=True, reject_on_worker_lost=True)
def process_pdf_lesson_job(self, job_id):
    """Run one idempotent attempt and retry only transient processing failures."""

    now = timezone.now()
    with transaction.atomic():
        job = (
            LessonIngestionJob.objects.select_for_update()
            .select_related('lesson__course')
            .filter(pk=job_id)
            .first()
        )
        if job is None:
            return {'job_id': job_id, 'status': 'discarded'}
        if job.status in ('completed', 'failed'):
            return {'job_id': job.id, 'status': job.status}
        if job.status == 'running' and job.started_at is not None:
            age = (now - job.started_at).total_seconds()
            if age < settings.LESSON_INGESTION_LEASE_SECONDS:
                return {'job_id': job.id, 'status': 'running'}
        job.status = 'running'
        job.attempts += 1
        job.started_at = now
        job.failure_code = ''
        job.safe_error = ''
        job.save(update_fields=[
            'status', 'attempts', 'started_at', 'failure_code', 'safe_error',
        ])

    if job.requested_by is None:
        message = 'Người yêu cầu xử lý không còn tồn tại.'
        _mark_failed(job.id, code='requester_unavailable', message=message)
        return {'job_id': job.id, 'status': 'failed'}

    try:
        source, created = process_pdf_lesson(
            actor=job.requested_by,
            lesson=job.lesson,
        )
    except PermissionDenied:
        message = 'Quyền xử lý bài học đã bị thu hồi.'
        _mark_failed(job.id, code='authorization_revoked', message=message)
        return {'job_id': job.id, 'status': 'failed'}
    except PDFIngestionError as exc:
        max_retries = max(0, min(settings.LESSON_INGESTION_MAX_RETRIES, 5))
        if exc.retryable and self.request.retries < max_retries:
            with transaction.atomic():
                retry_job = LessonIngestionJob.objects.select_for_update().filter(
                    pk=job.id
                ).first()
                if retry_job is None:
                    return {'job_id': job.id, 'status': 'discarded'}
                retry_job.status = 'queued'
                retry_job.failure_code = 'temporary_processing_failure'
                retry_job.safe_error = str(exc)[:255]
                retry_job.save(update_fields=['status', 'failure_code', 'safe_error'])
                Lesson.objects.filter(pk=job.lesson_id).update(
                    processing_status='pending',
                    processing_error='',
                )
            countdown = settings.LESSON_INGESTION_RETRY_BASE_SECONDS * (
                2 ** self.request.retries
            )
            raise self.retry(countdown=countdown, max_retries=max_retries)
        _mark_failed(job.id, code='processing_failed', message=str(exc))
        return {'job_id': job.id, 'status': 'failed'}

    completed_at = timezone.now()
    with transaction.atomic():
        completed_job = LessonIngestionJob.objects.select_for_update().filter(
            pk=job.id
        ).first()
        if completed_job is None:
            return {'job_id': job.id, 'status': 'discarded'}
        completed_job.status = 'completed'
        completed_job.knowledge_source = source
        completed_job.index_created = created
        completed_job.failure_code = ''
        completed_job.safe_error = ''
        completed_job.completed_at = completed_at
        completed_job.save(update_fields=[
            'status', 'knowledge_source', 'index_created', 'failure_code',
            'safe_error', 'completed_at',
        ])
    return {
        'job_id': job.id,
        'status': 'completed',
        'knowledge_source_id': source.id,
        'index_created': created,
    }


@shared_task(bind=True, acks_late=True, reject_on_worker_lost=True)
def process_sadtalker_video_job(self, job_id):
    """Consume one approved video job only on the dedicated `video` queue."""

    job = LessonVideoGenerationJob.objects.select_related(
        'lesson__course', 'requested_by',
    ).filter(pk=job_id).first()
    if job is None:
        return {'job_id': job_id, 'status': 'discarded'}
    if job.status in ('completed', 'failed'):
        return {'job_id': job.id, 'status': job.status}
    try:
        process_stored_video_job(job=job)
    except PermissionDenied:
        job.status = 'failed'
        job.failure_code = 'authorization_revoked'
        job.safe_error = 'Quyền tạo video đã bị thu hồi.'
        job.completed_at = timezone.now()
        job.save(update_fields=[
            'status', 'failure_code', 'safe_error', 'completed_at',
        ])
        cleared_fields = []
        for field_name in ('audio_file', 'portrait_file'):
            field = getattr(job, field_name)
            if field:
                field.delete(save=False)
                setattr(job, field_name, None)
                cleared_fields.append(field_name)
        if cleared_fields:
            job.save(update_fields=cleared_fields)
        return {'job_id': job.id, 'status': 'failed'}
    except VideoGenerationError as exc:
        job.refresh_from_db()
        if job.status != 'failed':
            job.status = 'failed'
            job.failure_code = exc.code[:50]
            job.safe_error = str(exc)[:255]
            job.completed_at = timezone.now()
            job.save(update_fields=[
                'status', 'failure_code', 'safe_error', 'completed_at',
            ])
            cleared_fields = []
            for field_name in ('audio_file', 'portrait_file'):
                field = getattr(job, field_name)
                if field:
                    field.delete(save=False)
                    setattr(job, field_name, None)
                    cleared_fields.append(field_name)
            if cleared_fields:
                job.save(update_fields=cleared_fields)
        return {'job_id': job.id, 'status': 'failed'}
    return {'job_id': job.id, 'status': 'completed'}
