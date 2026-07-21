from io import BytesIO
from pathlib import Path
import wave
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.ai_assistant.models import KnowledgeChunk, KnowledgeSource
from apps.exercises.models import LessonAssessment
from apps.users.models import User

from .content_authoring import assessment_generation_plan
from .models import (
    Course,
    Lesson,
    LessonNarrationAudio,
    LessonSummaryDraft,
    LessonVideoScriptDraft,
    LessonVideoGenerationJob,
)
from .video_queue import VideoQueueError, queue_lesson_video


def _wav_bytes():
    output = BytesIO()
    with wave.open(output, "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(16000)
        stream.writeframes(b"\x00\x00" * 1600)
    return output.getvalue()


def _portrait_file():
    output = BytesIO()
    Image.new("RGB", (256, 256), "white").save(output, format="PNG")
    return SimpleUploadedFile(
        "portrait.png", output.getvalue(), content_type="image/png"
    )


def _record_approved_summary(*, lesson, teacher):
    return LessonSummaryDraft.objects.create(
        lesson=lesson,
        text=lesson.ai_summary,
        status="approved",
        source_checksum="a" * 64,
        source_version=1,
        provider="test",
        model="test",
        generated_by=teacher,
        approved_by=teacher,
    )


def _assessment_batch(*, start=1):
    return {
        "title": "Kiểm tra PHP",
        "instructions": "Chọn đáp án phù hợp.",
        "questions": [
            {
                "prompt": f"Câu PHP {index}?",
                "choices": ["A", "B", "C", "D"],
                "correct_choice": 0,
                "learning_objective": f"Mục tiêu {index}",
                "explanation": "Giải thích dành cho giáo viên.",
                "order": index,
            }
            for index in range(start, start + 5)
        ],
    }


def _add_source_chunks(lesson, count):
    source = lesson.knowledge_sources.get(is_active=True)
    KnowledgeChunk.objects.bulk_create([
        KnowledgeChunk(
            source=source,
            ordinal=index,
            text=f"Phần kiến thức PHP {index}",
            start_offset=index * 30,
            end_offset=index * 30 + 25,
            char_count=25,
            embedding=[0.1, 0.2],
        )
        for index in range(count)
    ])
    return source


@pytest.fixture
def authoring_lesson(teacher_user):
    course = Course.objects.create(
        title="PHP authoring",
        slug="php-authoring",
        description="PHP",
        teacher=teacher_user,
        is_published=False,
    )
    lesson = Lesson.objects.create(
        course=course,
        title="PHP config",
        slug="php-config-authoring",
        extracted_text="PHP sử dụng file cấu hình để thiết lập môi trường.",
        processing_status="completed",
        is_published=True,
    )
    KnowledgeSource.objects.create(
        lesson=lesson,
        source_type="extracted_text",
        version=1,
        content_checksum="a" * 64,
        normalized_text=lesson.extracted_text,
        status="ready",
        is_active=True,
        embedding_provider="test",
        embedding_model="test",
        embedding_revision="test",
        embedding_dimension=2,
        chunker_version="test",
        chunk_size=1000,
        chunk_overlap=100,
    )
    return lesson


@pytest.mark.django_db
def test_summary_is_draft_until_owner_explicitly_approves(
    api_client, teacher_user, authoring_lesson
):
    api_client.force_authenticate(teacher_user)
    with patch(
        "apps.courses.content_authoring.AIService.generate_summary_draft",
        return_value={"text": "Bản tóm tắt PHP.", "tokens_used": 10},
    ):
        generated = api_client.post(
            f"/api/courses/lessons/{authoring_lesson.id}/generate-summary/"
        )

    authoring_lesson.refresh_from_db()
    assert generated.status_code == 201
    assert generated.data["summary"]["status"] == "draft"
    assert authoring_lesson.ai_summary == ""

    approved = api_client.post(
        f"/api/courses/lessons/{authoring_lesson.id}/approve-summary/",
        {"text": "Bản tóm tắt đã được giáo viên sửa và duyệt."},
        format="json",
    )
    authoring_lesson.refresh_from_db()
    assert approved.status_code == 200
    assert approved.data["summary"]["status"] == "approved"
    assert authoring_lesson.ai_summary == "Bản tóm tắt đã được giáo viên sửa và duyệt."


@pytest.mark.django_db
def test_other_teacher_is_denied_before_summary_provider(api_client, authoring_lesson):
    outsider = User.objects.create_user(
        email="authoring-outsider@example.invalid",
        username="authoring-outsider",
        password="LocalTestOnly-123!",
        role="teacher",
        is_verified=True,
    )
    api_client.force_authenticate(outsider)
    with patch(
        "apps.courses.content_authoring.AIService.generate_summary_draft",
    ) as provider:
        response = api_client.post(
            f"/api/courses/lessons/{authoring_lesson.id}/generate-summary/"
        )

    assert response.status_code == 404
    provider.assert_not_called()


@pytest.mark.django_db
def test_stale_summary_cannot_be_approved(api_client, teacher_user, authoring_lesson):
    LessonSummaryDraft.objects.create(
        lesson=authoring_lesson,
        text="Bản cũ",
        status="draft",
        source_checksum="b" * 64,
        source_version=1,
        provider="test",
        model="test",
        generated_by=teacher_user,
    )
    api_client.force_authenticate(teacher_user)

    response = api_client.post(
        f"/api/courses/lessons/{authoring_lesson.id}/approve-summary/",
        {"text": "Không được duyệt"},
        format="json",
    )

    assert response.status_code == 400
    authoring_lesson.refresh_from_db()
    assert authoring_lesson.ai_summary == ""


@pytest.mark.django_db
def test_video_script_is_separate_reviewed_draft_from_current_summary(
    api_client,
    teacher_user,
    authoring_lesson,
):
    summary_text = "Tóm tắt PHP đã được duyệt."
    authoring_lesson.ai_summary = summary_text
    authoring_lesson.save(update_fields=["ai_summary"])
    _record_approved_summary(lesson=authoring_lesson, teacher=teacher_user)
    api_client.force_authenticate(teacher_user)

    with patch(
        "apps.courses.content_authoring.AIService.generate_video_script_draft",
        return_value={"text": "Kịch bản PHP chi tiết hơn.", "tokens_used": 20},
    ) as provider:
        generated = api_client.post(
            f"/api/courses/lessons/{authoring_lesson.id}/generate-video-script/"
        )

    draft = LessonVideoScriptDraft.objects.get(lesson=authoring_lesson)
    assert generated.status_code == 201
    assert generated.data["video_script"]["status"] == "draft"
    assert generated.data["video_script"]["is_current"] is True
    assert draft.text != authoring_lesson.ai_summary
    provider.assert_called_once()

    approved = api_client.post(
        f"/api/courses/lessons/{authoring_lesson.id}/approve-video-script/",
        {"text": "Kịch bản đã được giáo viên rà soát."},
        format="json",
    )

    draft.refresh_from_db()
    assert approved.status_code == 200
    assert draft.status == "approved"
    assert draft.text == "Kịch bản đã được giáo viên rà soát."


@pytest.mark.django_db
def test_other_teacher_is_denied_before_video_script_provider(
    api_client,
    teacher_user,
    authoring_lesson,
):
    authoring_lesson.ai_summary = "Tóm tắt đã duyệt."
    authoring_lesson.save(update_fields=["ai_summary"])
    _record_approved_summary(lesson=authoring_lesson, teacher=teacher_user)
    outsider = User.objects.create_user(
        email="video-script-outsider@example.invalid",
        username="video-script-outsider",
        password="LocalTestOnly-123!",
        role="teacher",
        is_verified=True,
    )
    api_client.force_authenticate(outsider)

    with patch(
        "apps.courses.content_authoring.AIService.generate_video_script_draft"
    ) as provider:
        response = api_client.post(
            f"/api/courses/lessons/{authoring_lesson.id}/generate-video-script/"
        )

    assert response.status_code == 404
    provider.assert_not_called()


@pytest.mark.django_db
def test_generated_assessment_is_unpublished_reviewable_draft(
    api_client, teacher_user, authoring_lesson
):
    generated = _assessment_batch()
    api_client.force_authenticate(teacher_user)
    with patch(
        "apps.courses.content_authoring.AIService.generate_assessment_draft",
        return_value=generated,
    ):
        response = api_client.post(
            f"/api/courses/lessons/{authoring_lesson.id}/generate-assessment/"
        )

    assert response.status_code == 201
    assessment = LessonAssessment.objects.get(lesson=authoring_lesson)
    assert assessment.is_published is False
    assert assessment.questions.count() == 5
    assert response.data["assessment"]["is_published"] is False


@pytest.mark.django_db
def test_auto_assessment_uses_two_source_batches_for_medium_lesson(
    api_client, teacher_user, authoring_lesson
):
    source = _add_source_chunks(authoring_lesson, 7)
    source.normalized_text = "\n".join(
        f"Vùng kiến thức PHP số {index}." for index in range(1, 41)
    )
    source.save(update_fields=["normalized_text"])
    api_client.force_authenticate(teacher_user)

    with patch(
        "apps.courses.content_authoring.AIService.generate_assessment_draft",
        side_effect=[_assessment_batch(start=1), _assessment_batch(start=6)],
    ) as provider:
        response = api_client.post(
            f"/api/courses/lessons/{authoring_lesson.id}/generate-assessment/",
            {"question_count": "auto"},
            format="json",
        )

    assessment = LessonAssessment.objects.get(lesson=authoring_lesson)
    assert response.status_code == 201
    assert assessment.questions.count() == 10
    assert list(assessment.questions.values_list("order", flat=True)) == list(
        range(1, 11)
    )
    assert response.data["assessment_generation"] == {
        "source_chunk_count": 7,
        "recommended_question_count": 10,
        "question_count": 10,
        "provider_call_count": 2,
    }
    assert provider.call_count == 2
    first_call, second_call = provider.call_args_list
    assert first_call.kwargs["batch_index"] == 1
    assert second_call.kwargs["batch_index"] == 2
    assert first_call.kwargs["batch_count"] == 2
    assert first_call.kwargs["source_text"] != second_call.kwargs["source_text"]


@pytest.mark.django_db
def test_assessment_plan_recommends_fifteen_and_allows_twenty_question_override(
    authoring_lesson,
):
    source = _add_source_chunks(authoring_lesson, 16)

    assert assessment_generation_plan(source) == {
        "source_chunk_count": 16,
        "recommended_question_count": 15,
        "question_count": 15,
        "provider_call_count": 3,
    }
    assert assessment_generation_plan(source, "20") == {
        "source_chunk_count": 16,
        "recommended_question_count": 15,
        "question_count": 20,
        "provider_call_count": 4,
    }


@pytest.mark.django_db
def test_invalid_assessment_count_is_rejected_before_provider(
    api_client, teacher_user, authoring_lesson
):
    api_client.force_authenticate(teacher_user)
    with patch(
        "apps.courses.content_authoring.AIService.generate_assessment_draft"
    ) as provider:
        response = api_client.post(
            f"/api/courses/lessons/{authoring_lesson.id}/generate-assessment/",
            {"question_count": "7"},
            format="json",
        )

    assert response.status_code == 400
    assert not LessonAssessment.objects.filter(lesson=authoring_lesson).exists()
    provider.assert_not_called()


@pytest.mark.django_db
def test_duplicate_batch_output_does_not_persist_partial_assessment(
    api_client, teacher_user, authoring_lesson
):
    _add_source_chunks(authoring_lesson, 7)
    api_client.force_authenticate(teacher_user)
    duplicate_batch = _assessment_batch()
    with patch(
        "apps.courses.content_authoring.AIService.generate_assessment_draft",
        side_effect=[duplicate_batch, duplicate_batch],
    ):
        response = api_client.post(
            f"/api/courses/lessons/{authoring_lesson.id}/generate-assessment/",
            {"question_count": "10"},
            format="json",
        )

    assert response.status_code == 503
    assert not LessonAssessment.objects.filter(lesson=authoring_lesson).exists()


@pytest.mark.django_db
def test_other_teacher_is_denied_before_assessment_provider(
    api_client, authoring_lesson
):
    outsider = User.objects.create_user(
        email="assessment-authoring-outsider@example.invalid",
        username="assessment-authoring-outsider",
        password="LocalTestOnly-123!",
        role="teacher",
        is_verified=True,
    )
    api_client.force_authenticate(outsider)
    with patch(
        "apps.courses.content_authoring.AIService.generate_assessment_draft"
    ) as provider:
        response = api_client.post(
            f"/api/courses/lessons/{authoring_lesson.id}/generate-assessment/",
            {"question_count": "20"},
            format="json",
        )

    assert response.status_code == 404
    provider.assert_not_called()


@pytest.mark.django_db
def test_local_tts_is_bound_to_approved_summary_checksum(
    api_client, teacher_user, authoring_lesson
):
    authoring_lesson.ai_summary = "Nội dung PHP đã được duyệt."
    authoring_lesson.save(update_fields=["ai_summary"])
    _record_approved_summary(lesson=authoring_lesson, teacher=teacher_user)

    def fake_run(command, **kwargs):
        output_path = Path(command[command.index("-w") + 1])
        output_path.write_bytes(_wav_bytes())

    api_client.force_authenticate(teacher_user)
    with patch("apps.courses.content_authoring.subprocess.run", side_effect=fake_run):
        response = api_client.post(
            f"/api/courses/lessons/{authoring_lesson.id}/generate-narration/"
        )
    narration = LessonNarrationAudio.objects.get(lesson=authoring_lesson)

    assert response.status_code == 201
    assert response.data["narration"]["audio_url"].startswith(
        "http://testserver/media/"
    )
    assert narration.provider == "espeak-ng-local"
    assert len(narration.summary_checksum) == 64
    assert narration.audio_file.name.endswith(".wav")


@pytest.mark.django_db
def test_video_queue_requires_current_narration_and_deduplicates_active_job(
    teacher_user, authoring_lesson
):
    authoring_lesson.ai_summary = "Kịch bản đã duyệt."
    authoring_lesson.save(update_fields=["ai_summary"])
    _record_approved_summary(lesson=authoring_lesson, teacher=teacher_user)
    from hashlib import sha256

    summary_checksum = sha256(authoring_lesson.ai_summary.encode()).hexdigest()
    narration = LessonNarrationAudio.objects.create(
        lesson=authoring_lesson,
        summary_checksum=summary_checksum,
        audio_checksum="c" * 64,
        generated_by=teacher_user,
    )
    narration.audio_file.save(
        "narration.wav",
        SimpleUploadedFile("narration.wav", _wav_bytes()),
    )

    with patch("apps.courses.tasks.process_sadtalker_video_job.apply_async") as enqueue:
        first, created = queue_lesson_video(
            actor=teacher_user,
            lesson=authoring_lesson,
            portrait=_portrait_file(),
            rights_confirmed=True,
        )
        second, second_created = queue_lesson_video(
            actor=teacher_user,
            lesson=authoring_lesson,
            portrait=_portrait_file(),
            rights_confirmed=True,
        )

    assert created is True
    assert second_created is False
    assert first == second
    assert first.audio_file.name != narration.audio_file.name
    assert first.audio_checksum == narration.audio_checksum
    assert LessonVideoGenerationJob.objects.count() == 1
    enqueue.assert_called_once()


@pytest.mark.django_db
def test_video_queue_failure_persists_safe_terminal_state(
    teacher_user, authoring_lesson
):
    authoring_lesson.ai_summary = "Kịch bản đã duyệt."
    authoring_lesson.save(update_fields=["ai_summary"])
    _record_approved_summary(lesson=authoring_lesson, teacher=teacher_user)
    from hashlib import sha256

    narration = LessonNarrationAudio.objects.create(
        lesson=authoring_lesson,
        summary_checksum=sha256(authoring_lesson.ai_summary.encode()).hexdigest(),
        audio_checksum="d" * 64,
        generated_by=teacher_user,
    )
    narration.audio_file.save(
        "narration-failure.wav",
        SimpleUploadedFile("narration.wav", _wav_bytes()),
    )

    with patch(
        "apps.courses.tasks.process_sadtalker_video_job.apply_async",
        side_effect=RuntimeError("private broker detail"),
    ):
        with pytest.raises(VideoQueueError, match="tạm thời"):
            queue_lesson_video(
                actor=teacher_user,
                lesson=authoring_lesson,
                portrait=_portrait_file(),
                rights_confirmed=True,
            )

    job = LessonVideoGenerationJob.objects.get()
    assert job.status == "failed"
    assert job.failure_code == "queue_unavailable"
    assert "private broker detail" not in job.safe_error
    assert not job.audio_file
    assert not job.portrait_file
