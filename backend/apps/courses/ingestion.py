"""Authorization-first creation and dispatch of durable PDF ingestion jobs."""

import logging
import uuid

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from .models import Lesson, LessonIngestionJob


logger = logging.getLogger(__name__)


class IngestionQueueError(Exception):
    """A safe failure to submit a persisted job to the broker."""


def _authorize_ingestion(actor, lesson):
    if not getattr(actor, 'is_authenticated', False):
        raise PermissionDenied('Bạn không có quyền xử lý bài học này.')
    if actor.role != 'admin' and (
        actor.role != 'teacher' or lesson.course.teacher_id != actor.id
    ):
        raise PermissionDenied('Bạn không có quyền xử lý bài học này.')


def queue_pdf_ingestion(*, actor, lesson):
    """Persist one active job, then submit its server-owned task identifier."""

    _authorize_ingestion(actor, lesson)
    with transaction.atomic():
        locked_lesson = Lesson.objects.select_for_update().select_related('course').get(
            pk=lesson.pk
        )
        _authorize_ingestion(actor, locked_lesson)
        existing = locked_lesson.ingestion_jobs.filter(
            status__in=('queued', 'running'),
        ).first()
        if existing is not None:
            return existing, False

        job = LessonIngestionJob.objects.create(
            lesson=locked_lesson,
            requested_by=actor,
            task_id=uuid.uuid4(),
        )
        locked_lesson.processing_status = 'pending'
        locked_lesson.processing_error = ''
        locked_lesson.save(update_fields=['processing_status', 'processing_error'])

    from .tasks import process_pdf_lesson_job

    try:
        process_pdf_lesson_job.apply_async(
            args=[job.id],
            task_id=str(job.task_id),
        )
    except Exception:
        safe_error = 'Hàng đợi xử lý PDF tạm thời không khả dụng.'
        now = timezone.now()
        LessonIngestionJob.objects.filter(
            pk=job.pk,
            status__in=('queued', 'running'),
        ).update(
            status='failed',
            failure_code='queue_unavailable',
            safe_error=safe_error,
            completed_at=now,
        )
        Lesson.objects.filter(pk=lesson.pk).update(
            processing_status='failed',
            processing_error=safe_error,
        )
        logger.warning('PDF ingestion broker submission failed for job %s', job.id)
        raise IngestionQueueError(safe_error)
    return job, True
