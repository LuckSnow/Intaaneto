from hashlib import sha256
from io import BytesIO
from pathlib import Path
import uuid
import wave
from unittest.mock import patch

import pytest
from django.core.exceptions import PermissionDenied
from PIL import Image

from apps.ai_assistant.models import KnowledgeSource
from apps.users.models import User

from .models import (
    Course,
    Lesson,
    LessonMultimediaJob,
    LessonNarrationAudio,
    LessonSummaryDraft,
    LessonVideoScriptDraft,
)
from .multimedia_generation import (
    MultimediaGenerationError,
    PiperVietnameseProvider,
    _split_narration_phrases,
    build_storyboard,
    narration_text,
    process_multimedia_job,
    tutor_asset_checksum,
    validate_wav,
)
from .multimedia_queue import MultimediaQueueError, queue_lesson_multimedia
from .tasks import process_lesson_multimedia_job


def _wav_bytes(seconds=1):
    output = BytesIO()
    with wave.open(output, "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(16000)
        stream.writeframes(b"\x00\x00" * 16000 * seconds)
    return output.getvalue()


def _png(path, size=(512, 512)):
    Image.new("RGBA", size, (255, 246, 220, 255)).save(path, format="PNG")
    return path


@pytest.fixture
def multimedia_lesson(teacher_user):
    course = Course.objects.create(
        title="Khóa multimedia local",
        slug="khoa-multimedia-local",
        description="Kiểm thử video slide",
        teacher=teacher_user,
        is_published=False,
    )
    lesson = Lesson.objects.create(
        course=course,
        title="API trong ứng dụng web",
        slug="api-trong-ung-dung-web",
        ai_summary=(
            "API giúp các ứng dụng trao đổi dữ liệu. "
            "HTTPS bảo vệ dữ liệu khi truyền qua mạng."
        ),
        processing_status="completed",
    )
    LessonSummaryDraft.objects.create(
        lesson=lesson,
        text=lesson.ai_summary,
        status="approved",
        source_checksum="a" * 64,
        source_version=1,
        provider="test",
        model="test",
        generated_by=teacher_user,
        approved_by=teacher_user,
    )
    KnowledgeSource.objects.create(
        lesson=lesson,
        source_type="text",
        content_checksum="a" * 64,
        normalized_text=lesson.ai_summary,
        version=1,
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
    LessonVideoScriptDraft.objects.create(
        lesson=lesson,
        text=lesson.ai_summary,
        status="approved",
        source_checksum="a" * 64,
        source_version=1,
        summary_checksum=sha256(lesson.ai_summary.encode()).hexdigest(),
        provider="test",
        model="test",
        generated_by=teacher_user,
        approved_by=teacher_user,
    )
    return lesson


def test_storyboard_keeps_display_terms_but_normalizes_vietnamese_narration(settings):
    settings.MULTIMEDIA_MAX_SENTENCES = 36
    script = "API kết nối frontend và backend. HTTPS bảo vệ request."

    scenes = build_storyboard(lesson_title="Web API", script=script)

    assert scenes[0].bullets[0].startswith("API")
    assert narration_text(script).startswith("ây pi ai")
    assert "hát tê tê pi ét" in narration_text(script)


def test_narration_phrases_keep_punctuation_for_controlled_pauses():
    assert _split_narration_phrases("Đầu tiên, kiểm tra dữ liệu; rồi lưu lại.") == (
        "Đầu tiên,",
        "kiểm tra dữ liệu;",
        "rồi lưu lại.",
    )


@pytest.mark.django_db
def test_other_teacher_is_denied_before_tutor_asset_read(
    multimedia_lesson,
):
    outsider = User.objects.create_user(
        email="multimedia-outsider@example.invalid",
        username="multimedia-outsider",
        password="LocalTestOnly-123!",
        role="teacher",
        is_verified=True,
    )

    with patch("apps.courses.multimedia_queue.tutor_asset_checksum") as asset_read:
        with pytest.raises(PermissionDenied):
            queue_lesson_multimedia(actor=outsider, lesson=multimedia_lesson)

    asset_read.assert_not_called()
    assert LessonMultimediaJob.objects.count() == 0


@pytest.mark.django_db
def test_queue_deduplicates_active_local_multimedia_job(
    settings,
    teacher_user,
    multimedia_lesson,
):
    settings.PIPER_VOICE = "vi_VN-test"
    with (
        patch(
            "apps.courses.multimedia_queue.tutor_asset_checksum",
            return_value="b" * 64,
        ),
        patch(
            "apps.courses.tasks.process_lesson_multimedia_job.apply_async"
        ) as enqueue,
    ):
        first, created = queue_lesson_multimedia(
            actor=teacher_user,
            lesson=multimedia_lesson,
        )
        second, second_created = queue_lesson_multimedia(
            actor=teacher_user,
            lesson=multimedia_lesson,
        )

    assert created is True
    assert second_created is False
    assert first == second
    assert first.voice == "vi_VN-test"
    assert (
        first.script_checksum
        == sha256(multimedia_lesson.ai_summary.encode("utf-8")).hexdigest()
    )
    assert LessonMultimediaJob.objects.count() == 1
    enqueue.assert_called_once()


@pytest.mark.django_db
def test_queue_preserves_approved_summary_before_narration_normalization(
    settings,
    teacher_user,
    multimedia_lesson,
):
    approved_script = "API  kết nối frontend và backend.\nHTTPS bảo vệ dữ liệu."
    multimedia_lesson.ai_summary = approved_script
    multimedia_lesson.save(update_fields=["ai_summary"])
    multimedia_lesson.summary_draft.text = approved_script
    multimedia_lesson.summary_draft.save(update_fields=["text"])
    multimedia_lesson.video_script_draft.text = approved_script
    multimedia_lesson.video_script_draft.summary_checksum = sha256(
        approved_script.encode()
    ).hexdigest()
    multimedia_lesson.video_script_draft.save(
        update_fields=["text", "summary_checksum"]
    )
    settings.PIPER_VOICE = "vi_VN-test"

    with (
        patch(
            "apps.courses.multimedia_queue.tutor_asset_checksum",
            return_value="b" * 64,
        ),
        patch("apps.courses.tasks.process_lesson_multimedia_job.apply_async"),
    ):
        job, created = queue_lesson_multimedia(
            actor=teacher_user,
            lesson=multimedia_lesson,
        )

    assert created is True
    assert job.approved_script == approved_script
    assert job.script_checksum == sha256(approved_script.encode()).hexdigest()
    assert narration_text(job.approved_script).startswith("ây pi ai kết nối")


@pytest.mark.django_db
def test_queue_rejects_too_many_segments_before_asset_read_or_job_creation(
    settings,
    teacher_user,
    multimedia_lesson,
):
    settings.MULTIMEDIA_MAX_SENTENCES = 2
    script = "Đoạn một. Đoạn hai. Đoạn ba."
    multimedia_lesson.ai_summary = script
    multimedia_lesson.save(update_fields=["ai_summary"])
    multimedia_lesson.summary_draft.text = script
    multimedia_lesson.summary_draft.save(update_fields=["text"])
    multimedia_lesson.video_script_draft.text = script
    multimedia_lesson.video_script_draft.summary_checksum = sha256(
        script.encode()
    ).hexdigest()
    multimedia_lesson.video_script_draft.save(
        update_fields=["text", "summary_checksum"]
    )

    with patch("apps.courses.multimedia_queue.tutor_asset_checksum") as asset_read:
        with pytest.raises(MultimediaQueueError, match="quá nhiều câu"):
            queue_lesson_multimedia(
                actor=teacher_user,
                lesson=multimedia_lesson,
            )

    asset_read.assert_not_called()
    assert LessonMultimediaJob.objects.count() == 0


@pytest.mark.django_db
def test_teacher_api_enqueues_local_multimedia_job(
    api_client,
    teacher_user,
    multimedia_lesson,
):
    api_client.force_authenticate(teacher_user)
    with (
        patch(
            "apps.courses.multimedia_queue.tutor_asset_checksum",
            return_value="b" * 64,
        ),
        patch(
            "apps.courses.tasks.process_lesson_multimedia_job.apply_async"
        ) as enqueue,
    ):
        response = api_client.post(
            f"/api/courses/lessons/{multimedia_lesson.id}/generate-multimedia/"
        )

    assert response.status_code == 202
    assert response.data["queue_created"] is True
    assert response.data["multimedia"]["status"] == "queued"
    assert response.data["multimedia"]["stage"] == "queued"
    enqueue.assert_called_once()


class FakePiperProvider:
    provider_name = "fake-piper-local"

    def __init__(self):
        self.text = ""

    def generate(self, *, text, output_path):
        self.text = text
        output_path.write_bytes(_wav_bytes(seconds=2))
        return output_path


class FakeComposer:
    def __init__(self):
        self.frames = []

    def compose(self, *, frames, audio_path, output_path, work_dir):
        self.frames = list(frames)
        assert audio_path.is_file()
        assert all(frame.is_file() and duration > 0 for frame, duration in frames)
        output_path.write_bytes(b"\x00\x00\x00\x18ftypmp42intaaneto-local-video")
        return output_path


@pytest.mark.django_db
def test_local_multimedia_render_attaches_video_and_piper_audio(
    settings,
    tmp_path,
    teacher_user,
    multimedia_lesson,
):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.MULTIMEDIA_MAX_SENTENCES = 36
    settings.MULTIMEDIA_MAX_DURATION_SECONDS = 300
    settings.MULTIMEDIA_MAX_OUTPUT_BYTES = 1024 * 1024
    settings.MULTIMEDIA_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    settings.MULTIMEDIA_BOLD_FONT_PATH = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    )
    settings.PIPER_VOICE = "vi_VN-test"
    tutor = _png(tmp_path / "tutor.png")
    checksum = tutor_asset_checksum(tutor)
    job = LessonMultimediaJob.objects.create(
        lesson=multimedia_lesson,
        requested_by=teacher_user,
        task_id=uuid.uuid4(),
        approved_script=multimedia_lesson.ai_summary,
        script_checksum=sha256(multimedia_lesson.ai_summary.encode()).hexdigest(),
        tutor_asset_checksum=checksum,
        voice=settings.PIPER_VOICE,
        status="running",
    )
    provider = FakePiperProvider()
    composer = FakeComposer()

    process_multimedia_job(
        job=job,
        narration_provider=provider,
        composer=composer,
        tutor_path=tutor,
    )

    job.refresh_from_db()
    multimedia_lesson.refresh_from_db()
    narration = LessonNarrationAudio.objects.get(lesson=multimedia_lesson)
    assert job.status == "completed"
    assert job.stage == "completed"
    assert job.scene_count == 1
    assert job.duration_seconds == 2
    assert job.output_file.name.endswith(".mp4")
    assert multimedia_lesson.video_file.name == job.output_file.name
    assert narration.provider == "fake-piper-local"
    assert narration.voice == "vi_VN-test"
    assert provider.text.startswith("ây pi ai")
    assert len(composer.frames) == 2


@pytest.mark.django_db
def test_changed_summary_fails_before_tts(
    tmp_path,
    teacher_user,
    multimedia_lesson,
):
    tutor = _png(tmp_path / "tutor.png")
    old_script = multimedia_lesson.ai_summary
    job = LessonMultimediaJob.objects.create(
        lesson=multimedia_lesson,
        requested_by=teacher_user,
        task_id=uuid.uuid4(),
        approved_script=old_script,
        script_checksum=sha256(old_script.encode()).hexdigest(),
        tutor_asset_checksum=tutor_asset_checksum(tutor),
        voice="vi_VN-test",
    )
    multimedia_lesson.ai_summary = "Bản tóm tắt mới."
    multimedia_lesson.save(update_fields=["ai_summary"])
    provider = FakePiperProvider()

    with pytest.raises(MultimediaGenerationError, match="đã thay đổi"):
        process_multimedia_job(
            job=job,
            narration_provider=provider,
            composer=FakeComposer(),
            tutor_path=tutor,
        )

    assert provider.text == ""


@pytest.mark.django_db
def test_worker_reauthorizes_before_local_tts(
    tmp_path,
    teacher_user,
    multimedia_lesson,
):
    tutor = _png(tmp_path / "tutor.png")
    script = multimedia_lesson.ai_summary
    job = LessonMultimediaJob.objects.create(
        lesson=multimedia_lesson,
        requested_by=teacher_user,
        task_id=uuid.uuid4(),
        approved_script=script,
        script_checksum=sha256(script.encode()).hexdigest(),
        tutor_asset_checksum=tutor_asset_checksum(tutor),
        voice="vi_VN-test",
    )
    teacher_user.role = "student"
    teacher_user.save(update_fields=["role"])
    provider = FakePiperProvider()

    with pytest.raises(PermissionDenied):
        process_multimedia_job(
            job=job,
            narration_provider=provider,
            composer=FakeComposer(),
            tutor_path=tutor,
        )

    assert provider.text == ""


def test_missing_piper_model_fails_closed_without_starting_process(
    settings,
    tmp_path,
):
    settings.PIPER_MODEL_PATH = str(tmp_path / "missing.onnx")
    provider = PiperVietnameseProvider()

    with patch("apps.courses.multimedia_generation.subprocess.run") as run:
        with pytest.raises(MultimediaGenerationError, match="chưa sẵn sàng"):
            provider.generate(text="Xin chào", output_path=tmp_path / "out.wav")

    run.assert_not_called()


def test_piper_uses_configured_slower_length_scale(settings, tmp_path):
    model = tmp_path / "voice.onnx"
    model.write_bytes(b"model")
    Path(f"{model}.json").write_text("{}", encoding="utf-8")
    settings.PIPER_MODEL_PATH = str(model)
    settings.PIPER_LENGTH_SCALE = 1.12
    provider = PiperVietnameseProvider()

    def fake_run(command, **kwargs):
        output_path = Path(command[command.index("-f") + 1])
        output_path.write_bytes(_wav_bytes())

    with patch(
        "apps.courses.multimedia_generation.subprocess.run",
        side_effect=fake_run,
    ) as run:
        provider.generate(text="Xin chào", output_path=tmp_path / "out.wav")

    command = run.call_args.args[0]
    assert command[command.index("--length-scale") + 1] == "1.12"


def test_piper_adds_configured_pause_and_returns_sentence_timings(settings, tmp_path):
    model = tmp_path / "voice.onnx"
    model.write_bytes(b"model")
    Path(f"{model}.json").write_text("{}", encoding="utf-8")
    settings.PIPER_MODEL_PATH = str(model)
    settings.PIPER_CLAUSE_PAUSE_MS = 100
    settings.PIPER_SENTENCE_PAUSE_MS = 300
    provider = PiperVietnameseProvider()

    def fake_run(command, **kwargs):
        output_path = Path(command[command.index("-f") + 1])
        output_path.write_bytes(_wav_bytes(seconds=1))

    with patch(
        "apps.courses.multimedia_generation.subprocess.run", side_effect=fake_run
    ) as run:
        audio, durations = provider.generate_with_timing(
            sentences=("Một, hai.", "Ba."), output_path=tmp_path / "out.wav"
        )

    assert run.call_count == 3
    assert durations == pytest.approx((2.4, 1.0))
    _, duration = validate_wav(audio)
    assert duration == pytest.approx(3.4)


@pytest.mark.django_db
def test_worker_persists_safe_terminal_failure(
    teacher_user,
    multimedia_lesson,
):
    script = multimedia_lesson.ai_summary
    job = LessonMultimediaJob.objects.create(
        lesson=multimedia_lesson,
        requested_by=teacher_user,
        task_id=uuid.uuid4(),
        approved_script=script,
        script_checksum=sha256(script.encode()).hexdigest(),
        tutor_asset_checksum="b" * 64,
        voice="vi_VN-test",
    )

    with patch(
        "apps.courses.tasks.process_multimedia_job",
        side_effect=MultimediaGenerationError(
            "tts_failed",
            "Không thể tạo giọng đọc tiếng Việt bằng Piper.",
        ),
    ):
        result = process_lesson_multimedia_job.run(job.id)

    job.refresh_from_db()
    assert result == {"job_id": job.id, "status": "failed"}
    assert job.status == "failed"
    assert job.stage == "failed"
    assert job.failure_code == "tts_failed"
    assert job.safe_error == "Không thể tạo giọng đọc tiếng Việt bằng Piper."


@pytest.mark.django_db
def test_authoring_api_exposes_bounded_multimedia_state_only(
    api_client,
    teacher_user,
    multimedia_lesson,
):
    LessonMultimediaJob.objects.create(
        lesson=multimedia_lesson,
        requested_by=teacher_user,
        task_id=uuid.uuid4(),
        approved_script=multimedia_lesson.ai_summary,
        script_checksum="a" * 64,
        tutor_asset_checksum="b" * 64,
        voice="vi_VN-test",
        failure_code="model_missing",
        safe_error="Model Piper chưa sẵn sàng.",
        status="failed",
        stage="failed",
    )
    api_client.force_authenticate(teacher_user)

    response = api_client.get(
        f"/api/courses/lessons/{multimedia_lesson.id}/authoring-status/"
    )

    assert response.status_code == 200
    payload = response.data["multimedia"]
    assert payload["failure_code"] == "model_missing"
    assert "approved_script" not in payload
    assert "task_id" not in payload
    assert "tutor_asset_checksum" not in payload


@pytest.mark.django_db
def test_legacy_sadtalker_web_trigger_is_not_exposed(
    api_client,
    teacher_user,
    multimedia_lesson,
):
    api_client.force_authenticate(teacher_user)

    response = api_client.post(
        f"/api/courses/lessons/{multimedia_lesson.id}/generate-video/",
        {},
        format="json",
    )

    assert response.status_code == 404
