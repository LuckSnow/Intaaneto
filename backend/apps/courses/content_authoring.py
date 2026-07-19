"""Teacher-reviewed summary, assessment-draft, and local narration services."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import subprocess
import tempfile

from django.conf import settings
from django.core.files import File
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.ai_assistant.models import KnowledgeSource
from apps.ai_assistant.services import AIProviderError, AIService
from apps.exercises.models import AssessmentQuestion, LessonAssessment

from .models import (
    LessonNarrationAudio,
    LessonSummaryDraft,
    LessonVideoScriptDraft,
)
from .video_generation import VideoGenerationError, validate_audio


ASSESSMENT_BATCH_SIZE = 5
ASSESSMENT_GENERATION_COUNTS = (5, 10, 15, 20)


def authorize_lesson_authoring(*, actor, lesson):
    if not getattr(actor, "is_authenticated", False) or (
        actor.role != "admin"
        and (actor.role != "teacher" or lesson.course.teacher_id != actor.id)
    ):
        raise PermissionDenied("Bạn không có quyền biên soạn bài học này.")


def _active_source(lesson):
    source = KnowledgeSource.objects.filter(
        lesson=lesson,
        is_active=True,
        status="ready",
    ).first()
    if source is None:
        raise ValidationError(
            {
                "detail": "Bài học chưa có nguồn RAG active/ready để biên soạn.",
            }
        )
    return source


def _provider_metadata():
    provider = settings.AI_GENERATION_PROVIDER[:32]
    model = (
        settings.GEMINI_GENERATION_MODEL
        if provider == "gemini"
        else settings.AI_GENERATION_MODEL
    )[:100]
    return provider, model


def assessment_generation_plan(source, requested_question_count="auto"):
    """Resolve one bounded, server-owned generation plan from source size."""

    chunk_count = source.chunks.count()
    if chunk_count <= settings.AI_ASSESSMENT_FIVE_QUESTION_MAX_CHUNKS:
        recommended = 5
    elif chunk_count <= settings.AI_ASSESSMENT_TEN_QUESTION_MAX_CHUNKS:
        recommended = 10
    else:
        recommended = 15

    requested = str(requested_question_count or "auto")
    if requested == "auto":
        resolved = recommended
    else:
        try:
            resolved = int(requested)
        except (TypeError, ValueError) as exc:
            raise ValidationError(
                {"question_count": "Số câu hỏi được yêu cầu không hợp lệ."}
            ) from exc
        if resolved not in ASSESSMENT_GENERATION_COUNTS:
            raise ValidationError(
                {"question_count": "Chỉ hỗ trợ tự động hoặc 5, 10, 15, 20 câu."}
            )

    return {
        "source_chunk_count": chunk_count,
        "recommended_question_count": recommended,
        "question_count": resolved,
        "provider_call_count": resolved // ASSESSMENT_BATCH_SIZE,
    }


def _sample_source_segment(segment, maximum_chars):
    segment = segment.strip()
    if len(segment) <= maximum_chars:
        return segment
    separator = "\n\n[Phần nguồn tiếp theo]\n\n"
    excerpt_size = max(1, (maximum_chars - 2 * len(separator)) // 3)
    positions = (
        0,
        max(0, (len(segment) - excerpt_size) // 2),
        max(0, len(segment) - excerpt_size),
    )
    excerpts = [
        segment[position : position + excerpt_size].strip()
        for position in positions
    ]
    return separator.join(excerpts)[:maximum_chars]


def _assessment_source_windows(source_text, batch_count):
    """Partition the complete source, then bound each provider payload."""

    text = (source_text or "").strip()
    if not text:
        raise ValidationError({"detail": "Nguồn học liệu không có nội dung."})
    maximum_chars = settings.AI_AUTHORING_MAX_SOURCE_CHARS
    windows = []
    for index in range(batch_count):
        start = len(text) * index // batch_count
        end = len(text) * (index + 1) // batch_count
        windows.append(_sample_source_segment(text[start:end], maximum_chars))
    return windows


def _normalized_question_prompt(prompt):
    return " ".join(prompt.casefold().split())


def _approved_current_summary(lesson, source):
    draft = getattr(lesson, "summary_draft", None)
    if (
        draft is None
        or draft.status != "approved"
        or draft.text != lesson.ai_summary
        or draft.source_checksum != source.content_checksum
        or draft.source_version != source.version
    ):
        raise ValidationError(
            {"detail": "Hãy duyệt bản tóm tắt hiện tại trước khi soạn kịch bản video."}
        )
    return draft


def generate_summary_draft(*, actor, lesson, provider=None):
    authorize_lesson_authoring(actor=actor, lesson=lesson)
    source = _active_source(lesson)
    generated = AIService.generate_summary_draft(
        lesson_title=lesson.title,
        source_text=source.normalized_text[: settings.AI_AUTHORING_MAX_SOURCE_CHARS],
        provider=provider,
    )
    provider_name, model = _provider_metadata()
    draft, _ = LessonSummaryDraft.objects.update_or_create(
        lesson=lesson,
        defaults={
            "text": generated["text"],
            "status": "draft",
            "source_checksum": source.content_checksum,
            "source_version": source.version,
            "provider": provider_name,
            "model": model,
            "generated_by": actor,
            "approved_by": None,
            "approved_at": None,
        },
    )
    return draft


def generate_video_script_draft(*, actor, lesson, provider=None):
    authorize_lesson_authoring(actor=actor, lesson=lesson)
    source = _active_source(lesson)
    summary = _approved_current_summary(lesson, source)
    source_text = _sample_source_segment(
        source.normalized_text,
        settings.AI_AUTHORING_MAX_SOURCE_CHARS,
    )
    generated = AIService.generate_video_script_draft(
        lesson_title=lesson.title,
        approved_summary=summary.text,
        source_text=source_text,
        provider=provider,
    )
    provider_name, model = _provider_metadata()
    draft, _ = LessonVideoScriptDraft.objects.update_or_create(
        lesson=lesson,
        defaults={
            "text": generated["text"],
            "status": "draft",
            "source_checksum": source.content_checksum,
            "source_version": source.version,
            "summary_checksum": sha256(summary.text.encode("utf-8")).hexdigest(),
            "provider": provider_name,
            "model": model,
            "generated_by": actor,
            "approved_by": None,
            "approved_at": None,
        },
    )
    return draft


@transaction.atomic
def approve_video_script_draft(*, actor, lesson, text):
    authorize_lesson_authoring(actor=actor, lesson=lesson)
    source = _active_source(lesson)
    summary = _approved_current_summary(lesson, source)
    draft = (
        LessonVideoScriptDraft.objects.select_for_update()
        .filter(lesson=lesson)
        .first()
    )
    if draft is None:
        raise ValidationError({"detail": "Chưa có kịch bản video nháp để duyệt."})
    normalized = (text or "").strip()
    if not normalized or len(normalized) > 4800 or "\x00" in normalized:
        raise ValidationError(
            {"text": "Kịch bản video phải từ 1 đến 4.800 ký tự."}
        )
    summary_checksum = sha256(summary.text.encode("utf-8")).hexdigest()
    if (
        draft.source_checksum != source.content_checksum
        or draft.source_version != source.version
        or draft.summary_checksum != summary_checksum
    ):
        raise ValidationError(
            {"detail": "Nguồn hoặc bản tóm tắt đã thay đổi; hãy tạo lại kịch bản."}
        )
    draft.text = normalized
    draft.status = "approved"
    draft.approved_by = actor
    draft.approved_at = timezone.now()
    draft.save(
        update_fields=[
            "text",
            "status",
            "approved_by",
            "approved_at",
            "updated_at",
        ]
    )
    return draft


@transaction.atomic
def approve_summary_draft(*, actor, lesson, text):
    authorize_lesson_authoring(actor=actor, lesson=lesson)
    source = _active_source(lesson)
    draft = LessonSummaryDraft.objects.select_for_update().filter(lesson=lesson).first()
    if draft is None:
        raise ValidationError({"detail": "Chưa có bản tóm tắt nháp để duyệt."})
    normalized = (text or "").strip()
    if not normalized or len(normalized) > 4000 or "\x00" in normalized:
        raise ValidationError({"text": "Bản tóm tắt phải từ 1 đến 4.000 ký tự."})
    if (
        draft.source_checksum != source.content_checksum
        or draft.source_version != source.version
    ):
        raise ValidationError(
            {
                "detail": "Nguồn học liệu đã thay đổi; hãy tạo lại bản tóm tắt.",
            }
        )
    draft.text = normalized
    draft.status = "approved"
    draft.approved_by = actor
    draft.approved_at = timezone.now()
    draft.save(
        update_fields=[
            "text",
            "status",
            "approved_by",
            "approved_at",
            "updated_at",
        ]
    )
    lesson.ai_summary = normalized
    lesson.save(update_fields=["ai_summary"])
    return draft


def generate_assessment_draft(
    *, actor, lesson, question_count="auto", provider=None
):
    authorize_lesson_authoring(actor=actor, lesson=lesson)
    if LessonAssessment.objects.filter(lesson=lesson).exists():
        raise ValidationError(
            {
                "detail": "Bài học đã có assessment; hãy mở trang biên soạn để sửa.",
            }
        )
    source = _active_source(lesson)
    plan = assessment_generation_plan(source, question_count)
    windows = _assessment_source_windows(
        source.normalized_text,
        plan["provider_call_count"],
    )
    batch_results = [
        AIService.generate_assessment_draft(
            lesson_title=lesson.title,
            source_text=window,
            provider=provider,
            batch_index=index,
            batch_count=plan["provider_call_count"],
        )
        for index, window in enumerate(windows, start=1)
    ]
    questions = []
    seen_prompts = set()
    for batch in batch_results:
        for question in batch["questions"]:
            normalized_prompt = _normalized_question_prompt(question["prompt"])
            if normalized_prompt in seen_prompts:
                raise AIProviderError(
                    "AI provider returned duplicate assessment questions"
                )
            seen_prompts.add(normalized_prompt)
            questions.append({**question, "order": len(questions) + 1})
    if len(questions) != plan["question_count"]:
        raise AIProviderError("AI provider returned an incomplete assessment draft")

    generated = {
        "title": batch_results[0]["title"],
        "instructions": batch_results[0]["instructions"],
        "questions": questions,
    }
    source_checksum = source.content_checksum
    source_version = source.version
    with transaction.atomic():
        # Recheck the mutable state after the external provider call so a stale
        # response cannot silently become the lesson's assessment draft.
        current_source = _active_source(lesson)
        if (
            current_source.content_checksum != source_checksum
            or current_source.version != source_version
        ):
            raise ValidationError(
                {
                    "detail": "Nguồn học liệu đã thay đổi; hãy tạo lại assessment.",
                }
            )
        if LessonAssessment.objects.select_for_update().filter(lesson=lesson).exists():
            raise ValidationError(
                {
                    "detail": "Bài học đã có assessment; hãy mở trang biên soạn để sửa.",
                }
            )
        assessment = LessonAssessment.objects.create(
            lesson=lesson,
            title=generated["title"],
            instructions=generated["instructions"],
            pass_threshold=70,
            is_published=False,
        )
        AssessmentQuestion.objects.bulk_create(
            [
                AssessmentQuestion(assessment=assessment, **question)
                for question in generated["questions"]
            ]
        )
    return assessment


def generate_narration_audio(*, actor, lesson):
    authorize_lesson_authoring(actor=actor, lesson=lesson)
    draft = LessonSummaryDraft.objects.filter(
        lesson=lesson,
        status="approved",
    ).first()
    if draft is None or not lesson.ai_summary or draft.text != lesson.ai_summary:
        raise ValidationError(
            {"detail": "Hãy duyệt bản tóm tắt trước khi tạo giọng đọc."}
        )
    summary_checksum = sha256(draft.text.encode("utf-8")).hexdigest()
    command = [
        settings.TTS_ESPEAK_EXECUTABLE,
        "-v",
        settings.TTS_ESPEAK_VOICE,
        "-s",
        str(settings.TTS_ESPEAK_SPEED),
    ]
    with tempfile.TemporaryDirectory(prefix="intaaneto-tts-") as directory:
        output = Path(directory) / "narration.wav"
        command.extend(["-w", str(output), draft.text])
        try:
            subprocess.run(
                command,
                check=True,
                input=draft.text,
                text=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=settings.TTS_TIMEOUT_SECONDS,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise VideoGenerationError(
                "tts_failed",
                "Không thể tạo giọng đọc local.",
            ) from exc
        audio = validate_audio(output)
        audio_checksum = sha256(audio.read_bytes()).hexdigest()
        narration, _ = LessonNarrationAudio.objects.get_or_create(
            lesson=lesson,
            defaults={
                "summary_checksum": summary_checksum,
                "audio_checksum": audio_checksum,
                "provider": "espeak-ng-local",
                "voice": settings.TTS_ESPEAK_VOICE,
                "generated_by": actor,
            },
        )
        if narration.audio_file:
            narration.audio_file.delete(save=False)
        with audio.open("rb") as stream:
            narration.audio_file.save(
                f"lesson-{lesson.id}-summary-{summary_checksum[:12]}.wav",
                File(stream),
                save=False,
            )
        narration.summary_checksum = summary_checksum
        narration.audio_checksum = audio_checksum
        narration.provider = "espeak-ng-local"
        narration.voice = settings.TTS_ESPEAK_VOICE
        narration.generated_by = actor
        narration.save()
    return narration
