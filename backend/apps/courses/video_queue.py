"""Durable enqueue boundary for approved SadTalker web jobs."""

from __future__ import annotations

from hashlib import sha256
import uuid

from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction

from .models import LessonVideoGenerationJob
from .video_generation import authorize_video_generation, validate_approved_script


class VideoQueueError(Exception):
    """Safe queue submission failure."""


def queue_lesson_video(*, actor, lesson, portrait, rights_confirmed):
    authorize_video_generation(actor=actor, lesson=lesson)
    if not rights_confirmed:
        raise VideoQueueError('Cần xác nhận quyền sử dụng và phê duyệt.')
    summary = validate_approved_script(lesson.ai_summary)
    draft = getattr(lesson, 'summary_draft', None)
    if draft is None or draft.status != 'approved' or draft.text != summary:
        raise VideoQueueError('Hãy duyệt bản tóm tắt hiện tại trước khi tạo video.')
    narration = getattr(lesson, 'narration_audio', None)
    expected_checksum = sha256(summary.encode('utf-8')).hexdigest()
    if narration is None or narration.summary_checksum != expected_checksum:
        raise VideoQueueError('Hãy tạo lại giọng đọc từ bản tóm tắt đã duyệt.')

    existing = LessonVideoGenerationJob.objects.filter(
        lesson=lesson,
        status__in=('queued', 'running'),
    ).first()
    if existing:
        return existing, False

    portrait.seek(0)
    portrait_bytes = portrait.read()
    portrait_checksum = sha256(portrait_bytes).hexdigest()
    task_id = uuid.uuid4()
    try:
        with transaction.atomic():
            job = LessonVideoGenerationJob.objects.create(
                lesson=lesson,
                requested_by=actor,
                task_id=task_id,
                approved_script=summary,
                script_checksum=expected_checksum,
                audio_checksum=narration.audio_checksum,
                portrait_checksum=portrait_checksum,
                rights_and_approval_confirmed=True,
            )
            job.audio_file.name = narration.audio_file.name
            suffix = '.png' if portrait.name.lower().endswith('.png') else '.jpg'
            job.portrait_file.save(
                f'lesson-{lesson.id}-job-{job.id}{suffix}',
                ContentFile(portrait_bytes),
                save=False,
            )
            job.save(update_fields=['audio_file', 'portrait_file'])
    except IntegrityError:
        existing = LessonVideoGenerationJob.objects.filter(
            lesson=lesson,
            status__in=('queued', 'running'),
        ).first()
        if existing:
            return existing, False
        raise

    try:
        from .tasks import process_sadtalker_video_job
        process_sadtalker_video_job.apply_async(args=[job.id], task_id=str(task_id), queue='video')
    except Exception as exc:
        job.status = 'failed'
        job.failure_code = 'queue_unavailable'
        job.safe_error = 'Hàng đợi video tạm thời không khả dụng.'
        if job.portrait_file:
            job.portrait_file.delete(save=False)
            job.portrait_file = None
        job.save(update_fields=[
            'status', 'failure_code', 'safe_error', 'portrait_file',
        ])
        raise VideoQueueError(job.safe_error) from exc
    return job, True
