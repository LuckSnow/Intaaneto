"""Durable enqueue boundary for local Piper slide-video jobs."""

from hashlib import sha256
import uuid

from django.conf import settings
from django.db import IntegrityError, transaction

from .models import LessonMultimediaJob
from .multimedia_generation import (
    MultimediaGenerationError,
    authorize_multimedia_generation,
    split_narration_sentences,
    tutor_asset_checksum,
)
from .tutor_avatars import preset_path


class MultimediaQueueError(Exception):
    """Safe queue submission failure."""


def _active_job(lesson):
    return LessonMultimediaJob.objects.filter(
        lesson=lesson,
        status__in=("queued", "running"),
    ).first()


def _create_job(*, actor, lesson, script, asset_checksum, task_id):
    with transaction.atomic():
        return LessonMultimediaJob.objects.create(
            lesson=lesson,
            requested_by=actor,
            task_id=task_id,
            approved_script=script,
            script_checksum=sha256(script.encode("utf-8")).hexdigest(),
            tutor_asset_checksum=asset_checksum,
            tutor_preset=lesson.tutor_preset,
            tutor_avatar=lesson.tutor_avatar,
            voice=settings.PIPER_VOICE,
        )


def _approved_current_video_script(lesson):
    draft = getattr(lesson, "video_script_draft", None)
    if draft is None or draft.status != "approved":
        raise MultimediaQueueError(
            "Hãy duyệt kịch bản video hiện tại trước khi tạo video."
        )
    source = lesson.knowledge_sources.filter(is_active=True, status="ready").first()
    summary = getattr(lesson, "summary_draft", None)
    summary_is_current = bool(
        summary
        and summary.status == "approved"
        and summary.text == lesson.ai_summary
        and source
        and summary.source_checksum == source.content_checksum
        and summary.source_version == source.version
    )
    if (
        source is None
        or not summary_is_current
        or draft.source_checksum != source.content_checksum
        or draft.source_version != source.version
        or draft.summary_checksum
        != sha256(summary.text.encode("utf-8")).hexdigest()
    ):
        raise MultimediaQueueError(
            "Nguồn hoặc bản tóm tắt đã thay đổi; hãy tạo lại kịch bản video."
        )
    return draft


def _dispatch_job(job, task_id):
    try:
        from .tasks import process_lesson_multimedia_job

        process_lesson_multimedia_job.apply_async(
            args=[job.id], task_id=str(task_id), queue="celery"
        )
    except Exception as exc:
        job.status = "failed"
        job.stage = "failed"
        job.failure_code = "queue_unavailable"
        job.safe_error = "Hàng đợi multimedia tạm thời không khả dụng."
        job.save(update_fields=["status", "stage", "failure_code", "safe_error"])
        raise MultimediaQueueError(job.safe_error) from exc


def queue_lesson_multimedia(*, actor, lesson):
    authorize_multimedia_generation(actor=actor, lesson=lesson)
    draft = _approved_current_video_script(lesson)
    approved_script = draft.text
    try:
        split_narration_sentences(approved_script)
    except MultimediaGenerationError as exc:
        raise MultimediaQueueError(str(exc)) from exc
    try:
        if lesson.tutor_avatar_id:
            if lesson.tutor_avatar.owner_id not in {actor.pk, lesson.course.teacher_id}:
                raise MultimediaQueueError('Avatar không thuộc giáo viên của bài học.')
            asset_checksum = lesson.tutor_avatar.checksum
        else:
            asset_checksum = tutor_asset_checksum(preset_path(lesson.tutor_preset))
    except MultimediaGenerationError as exc:
        raise MultimediaQueueError(str(exc)) from exc

    existing = _active_job(lesson)
    if existing:
        return existing, False

    task_id = uuid.uuid4()
    try:
        job = _create_job(
            actor=actor,
            lesson=lesson,
            script=approved_script,
            asset_checksum=asset_checksum,
            task_id=task_id,
        )
    except IntegrityError:
        existing = _active_job(lesson)
        if existing:
            return existing, False
        raise

    _dispatch_job(job, task_id)
    return job, True
