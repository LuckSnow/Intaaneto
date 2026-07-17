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
from apps.ai_assistant.services import AIService
from apps.exercises.models import AssessmentQuestion, LessonAssessment

from .models import LessonNarrationAudio, LessonSummaryDraft
from .video_generation import VideoGenerationError, validate_audio


def authorize_lesson_authoring(*, actor, lesson):
    if not getattr(actor, 'is_authenticated', False) or (
        actor.role != 'admin'
        and (actor.role != 'teacher' or lesson.course.teacher_id != actor.id)
    ):
        raise PermissionDenied('Bạn không có quyền biên soạn bài học này.')


def _active_source(lesson):
    source = KnowledgeSource.objects.filter(
        lesson=lesson,
        is_active=True,
        status='ready',
    ).first()
    if source is None:
        raise ValidationError({
            'detail': 'Bài học chưa có nguồn RAG active/ready để biên soạn.',
        })
    return source


def _provider_metadata():
    provider = settings.AI_GENERATION_PROVIDER[:32]
    model = (
        settings.GEMINI_GENERATION_MODEL
        if provider == 'gemini'
        else settings.AI_GENERATION_MODEL
    )[:100]
    return provider, model


def generate_summary_draft(*, actor, lesson, provider=None):
    authorize_lesson_authoring(actor=actor, lesson=lesson)
    source = _active_source(lesson)
    generated = AIService.generate_summary_draft(
        lesson_title=lesson.title,
        source_text=source.normalized_text[:settings.AI_AUTHORING_MAX_SOURCE_CHARS],
        provider=provider,
    )
    provider_name, model = _provider_metadata()
    draft, _ = LessonSummaryDraft.objects.update_or_create(
        lesson=lesson,
        defaults={
            'text': generated['text'],
            'status': 'draft',
            'source_checksum': source.content_checksum,
            'source_version': source.version,
            'provider': provider_name,
            'model': model,
            'generated_by': actor,
            'approved_by': None,
            'approved_at': None,
        },
    )
    return draft


@transaction.atomic
def approve_summary_draft(*, actor, lesson, text):
    authorize_lesson_authoring(actor=actor, lesson=lesson)
    source = _active_source(lesson)
    draft = LessonSummaryDraft.objects.select_for_update().filter(lesson=lesson).first()
    if draft is None:
        raise ValidationError({'detail': 'Chưa có bản tóm tắt nháp để duyệt.'})
    normalized = (text or '').strip()
    if not normalized or len(normalized) > 4000 or '\x00' in normalized:
        raise ValidationError({'text': 'Bản tóm tắt phải từ 1 đến 4.000 ký tự.'})
    if (
        draft.source_checksum != source.content_checksum
        or draft.source_version != source.version
    ):
        raise ValidationError({
            'detail': 'Nguồn học liệu đã thay đổi; hãy tạo lại bản tóm tắt.',
        })
    draft.text = normalized
    draft.status = 'approved'
    draft.approved_by = actor
    draft.approved_at = timezone.now()
    draft.save(update_fields=[
        'text', 'status', 'approved_by', 'approved_at', 'updated_at',
    ])
    lesson.ai_summary = normalized
    lesson.save(update_fields=['ai_summary'])
    return draft


def generate_assessment_draft(*, actor, lesson, provider=None):
    authorize_lesson_authoring(actor=actor, lesson=lesson)
    if LessonAssessment.objects.filter(lesson=lesson).exists():
        raise ValidationError({
            'detail': 'Bài học đã có assessment; hãy mở trang biên soạn để sửa.',
        })
    source = _active_source(lesson)
    generated = AIService.generate_assessment_draft(
        lesson_title=lesson.title,
        source_text=source.normalized_text[:settings.AI_AUTHORING_MAX_SOURCE_CHARS],
        provider=provider,
    )
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
            raise ValidationError({
                'detail': 'Nguồn học liệu đã thay đổi; hãy tạo lại assessment.',
            })
        if LessonAssessment.objects.select_for_update().filter(lesson=lesson).exists():
            raise ValidationError({
                'detail': 'Bài học đã có assessment; hãy mở trang biên soạn để sửa.',
            })
        assessment = LessonAssessment.objects.create(
            lesson=lesson,
            title=generated['title'],
            instructions=generated['instructions'],
            pass_threshold=70,
            is_published=False,
        )
        AssessmentQuestion.objects.bulk_create([
            AssessmentQuestion(assessment=assessment, **question)
            for question in generated['questions']
        ])
    return assessment


def generate_narration_audio(*, actor, lesson):
    authorize_lesson_authoring(actor=actor, lesson=lesson)
    draft = LessonSummaryDraft.objects.filter(
        lesson=lesson,
        status='approved',
    ).first()
    if draft is None or not lesson.ai_summary or draft.text != lesson.ai_summary:
        raise ValidationError({'detail': 'Hãy duyệt bản tóm tắt trước khi tạo giọng đọc.'})
    summary_checksum = sha256(draft.text.encode('utf-8')).hexdigest()
    command = [
        settings.TTS_ESPEAK_EXECUTABLE,
        '-v', settings.TTS_ESPEAK_VOICE,
        '-s', str(settings.TTS_ESPEAK_SPEED),
    ]
    with tempfile.TemporaryDirectory(prefix='intaaneto-tts-') as directory:
        output = Path(directory) / 'narration.wav'
        command.extend(['-w', str(output), draft.text])
        try:
            subprocess.run(
                command,
                check=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=settings.TTS_TIMEOUT_SECONDS,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise VideoGenerationError(
                'tts_failed',
                'Không thể tạo giọng đọc local.',
            ) from exc
        audio = validate_audio(output)
        audio_checksum = sha256(audio.read_bytes()).hexdigest()
        narration, _ = LessonNarrationAudio.objects.get_or_create(
            lesson=lesson,
            defaults={
                'summary_checksum': summary_checksum,
                'audio_checksum': audio_checksum,
                'provider': 'espeak-ng-local',
                'voice': settings.TTS_ESPEAK_VOICE,
                'generated_by': actor,
            },
        )
        if narration.audio_file:
            narration.audio_file.delete(save=False)
        with audio.open('rb') as stream:
            narration.audio_file.save(
                f'lesson-{lesson.id}-summary-{summary_checksum[:12]}.wav',
                File(stream),
                save=False,
            )
        narration.summary_checksum = summary_checksum
        narration.audio_checksum = audio_checksum
        narration.provider = 'espeak-ng-local'
        narration.voice = settings.TTS_ESPEAK_VOICE
        narration.generated_by = actor
        narration.save()
    return narration
