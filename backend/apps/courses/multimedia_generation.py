"""Fast local Vietnamese narration and deterministic lesson slide rendering."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
import re
import subprocess
import tempfile
import time
import wave

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.files import File
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageChops, ImageDraw, ImageFont, UnidentifiedImageError

from .models import LessonNarrationAudio


class MultimediaGenerationError(Exception):
    """Bounded local multimedia failure safe to expose to a teacher-owner."""

    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class StoryboardScene:
    title: str
    bullets: tuple[str, ...]
    sentences: tuple[str, ...]


def authorize_multimedia_generation(*, actor, lesson):
    if not getattr(actor, "is_authenticated", False) or (
        actor.role != "admin"
        and (actor.role != "teacher" or lesson.course.teacher_id != actor.id)
    ):
        raise PermissionDenied("Bạn không có quyền tạo video cho bài học này.")


def validate_approved_script(script):
    normalized = re.sub(r"[ \t]+", " ", (script or "").replace("\r", "")).strip()
    if not normalized or len(normalized) > 4800 or "\x00" in normalized:
        raise MultimediaGenerationError(
            "invalid_script", "Bản tóm tắt đã duyệt không hợp lệ."
        )
    return normalized


def _split_long_text(text, maximum_chars=180):
    words = text.split()
    chunks = []
    current = []
    for word in words:
        candidate = " ".join((*current, word))
        if current and len(candidate) > maximum_chars:
            chunks.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        chunks.append(" ".join(current))
    return chunks


def split_narration_sentences(script):
    script = validate_approved_script(script)
    parts = re.split(r"(?<=[.!?])\s+|\n+", script)
    sentences = []
    for part in parts:
        cleaned = part.strip(" -•\t")
        if cleaned:
            sentences.extend(_split_long_text(cleaned))
    if not sentences or len(sentences) > settings.MULTIMEDIA_MAX_SENTENCES:
        raise MultimediaGenerationError(
            "script_too_complex",
            "Bản tóm tắt có quá nhiều câu để dựng video; hãy rút gọn rồi duyệt lại.",
        )
    return sentences


def build_storyboard(*, lesson_title, script):
    sentences = split_narration_sentences(script)
    scenes = []
    for offset in range(0, len(sentences), 2):
        scene_sentences = tuple(sentences[offset : offset + 2])
        number = len(scenes) + 1
        title = lesson_title if number == 1 else f"Nội dung chính · Phần {number}"
        scenes.append(
            StoryboardScene(
                title=title[:120],
                bullets=scene_sentences,
                sentences=scene_sentences,
            )
        )
    return scenes


_PRONUNCIATION = {
    "AI": "ây ai",
    "API": "ây pi ai",
    "CSS": "xi ét ét",
    "HTML": "hát tê em eo",
    "HTTP": "hát tê tê pi",
    "HTTPS": "hát tê tê pi ét",
    "PHP": "pi hát pi",
    "SQL": "ét kiu eo",
    "URL": "iu a eo",
}


def narration_text(script):
    text = validate_approved_script(script)
    for source, spoken in sorted(
        _PRONUNCIATION.items(), key=lambda item: -len(item[0])
    ):
        text = re.sub(rf"(?<!\w){re.escape(source)}(?!\w)", spoken, text)
    return text


def _bounded_file(path, *, maximum_bytes, suffixes, label):
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_file() or resolved.suffix.lower() not in suffixes:
        raise MultimediaGenerationError(
            "missing_runtime_asset", f"{label} chưa sẵn sàng."
        )
    size = resolved.stat().st_size
    if size <= 0 or size > maximum_bytes:
        raise MultimediaGenerationError(
            "invalid_runtime_asset", f"{label} không hợp lệ."
        )
    return resolved


def tutor_asset_checksum(path=None):
    asset = _bounded_file(
        path or settings.MULTIMEDIA_TUTOR_IMAGE_PATH,
        maximum_bytes=10 * 1024 * 1024,
        suffixes={".png"},
        label="Ảnh AI Tutor",
    )
    return sha256(asset.read_bytes()).hexdigest()


def validate_wav(path):
    audio = _bounded_file(
        path,
        maximum_bytes=25 * 1024 * 1024,
        suffixes={".wav"},
        label="Giọng đọc WAV",
    )
    try:
        with wave.open(str(audio), "rb") as stream:
            frames = stream.getnframes()
            rate = stream.getframerate()
            duration = frames / rate if rate else 0
            if (
                stream.getnchannels() not in (1, 2)
                or stream.getsampwidth() not in (1, 2, 3, 4)
                or not 8000 <= rate <= 96000
                or duration <= 0
                or duration > settings.MULTIMEDIA_MAX_DURATION_SECONDS
            ):
                raise MultimediaGenerationError(
                    "invalid_audio", "Giọng đọc local không hợp lệ."
                )
    except (wave.Error, EOFError, OSError) as exc:
        raise MultimediaGenerationError(
            "invalid_audio", "Giọng đọc local không hợp lệ."
        ) from exc
    return audio, duration


class PiperVietnameseProvider:
    provider_name = "piper-local"

    def generate(self, *, text, output_path):
        model = _bounded_file(
            settings.PIPER_MODEL_PATH,
            maximum_bytes=250 * 1024 * 1024,
            suffixes={".onnx"},
            label="Model giọng Việt Piper",
        )
        config_path = Path(f"{model}.json")
        _bounded_file(
            config_path,
            maximum_bytes=1024 * 1024,
            suffixes={".json"},
            label="Cấu hình model Piper",
        )
        command = [
            settings.PIPER_PYTHON_EXECUTABLE,
            "-m",
            "piper",
            "-m",
            str(model),
            "-f",
            str(output_path),
            "--length-scale",
            str(settings.PIPER_LENGTH_SCALE),
            "--",
            text,
        ]
        try:
            subprocess.run(
                command,
                check=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=settings.PIPER_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise MultimediaGenerationError(
                "tts_timeout", "Piper tạo giọng đọc quá thời gian cho phép."
            ) from exc
        except (OSError, subprocess.CalledProcessError) as exc:
            raise MultimediaGenerationError(
                "tts_failed", "Không thể tạo giọng đọc tiếng Việt bằng Piper."
            ) from exc
        return validate_wav(output_path)[0]


def _font(path, size):
    try:
        return ImageFont.truetype(str(Path(path).resolve()), size=size)
    except OSError as exc:
        raise MultimediaGenerationError(
            "missing_runtime_asset", "Font dựng slide chưa sẵn sàng."
        ) from exc


def _wrap_text(draw, text, font, maximum_width):
    lines = []
    current = []
    for word in text.split():
        candidate = " ".join((*current, word))
        width = draw.textbbox((0, 0), candidate, font=font)[2]
        if current and width > maximum_width:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines or [""]


def _load_tutor(path):
    asset = _bounded_file(
        path,
        maximum_bytes=10 * 1024 * 1024,
        suffixes={".png"},
        label="Ảnh AI Tutor",
    )
    try:
        with Image.open(asset) as source:
            source.load()
            if source.width * source.height > 16_000_000:
                raise MultimediaGenerationError(
                    "invalid_runtime_asset", "Ảnh AI Tutor không hợp lệ."
                )
            tutor = source.convert("RGBA")
    except (UnidentifiedImageError, OSError) as exc:
        raise MultimediaGenerationError(
            "invalid_runtime_asset", "Ảnh AI Tutor không hợp lệ."
        ) from exc
    white = Image.new("RGBA", tutor.size, (255, 255, 255, 255))
    bbox = ImageChops.difference(tutor, white).convert("RGB").getbbox()
    if bbox:
        left, top, right, bottom = bbox
        padding = 24
        tutor = tutor.crop(
            (
                max(0, left - padding),
                max(0, top - padding),
                min(tutor.width, right + padding),
                min(tutor.height, bottom + padding),
            )
        )
    tutor.thumbnail((250, 250), Image.Resampling.LANCZOS)
    return tutor


def _draw_slide(*, scene, active_sentence, tutor, output_path):
    canvas = Image.new("RGB", (1280, 720), "#f8fafc")
    draw = ImageDraw.Draw(canvas)
    title_font = _font(settings.MULTIMEDIA_BOLD_FONT_PATH, 42)
    body_font = _font(settings.MULTIMEDIA_FONT_PATH, 31)
    caption_font = _font(settings.MULTIMEDIA_BOLD_FONT_PATH, 25)
    small_font = _font(settings.MULTIMEDIA_FONT_PATH, 20)

    draw.rounded_rectangle(
        (48, 36, 1232, 684),
        radius=28,
        fill="#ffffff",
        outline="#e2e8f0",
        width=2,
    )
    draw.rounded_rectangle((48, 36, 62, 684), radius=7, fill="#ea580c")
    draw.text((88, 70), scene.title, font=title_font, fill="#0f172a")
    draw.text((90, 126), "BÀI GIẢNG TÓM TẮT", font=small_font, fill="#c2410c")

    y = 186
    for bullet in scene.bullets:
        lines = _wrap_text(draw, bullet, body_font, 720)
        draw.ellipse((92, y + 12, 104, y + 24), fill="#f97316")
        draw.multiline_text(
            (124, y), "\n".join(lines), font=body_font, fill="#1e293b", spacing=9
        )
        y += len(lines) * 43 + 24

    draw.rounded_rectangle(
        (930, 156, 1190, 440),
        radius=24,
        fill="#fff7ed",
        outline="#fed7aa",
        width=2,
    )
    tutor_x = 1060 - tutor.width // 2
    tutor_y = 168 + (250 - tutor.height) // 2
    canvas.paste(tutor.convert("RGB"), (tutor_x, tutor_y))
    draw.text((978, 406), "AI Tutor", font=caption_font, fill="#9a3412")

    draw.rounded_rectangle((82, 526, 1198, 654), radius=20, fill="#172033")
    caption_lines = _wrap_text(draw, active_sentence, caption_font, 1040)
    caption_height = len(caption_lines) * 34
    caption_y = 590 - caption_height // 2
    draw.multiline_text(
        (120, caption_y),
        "\n".join(caption_lines),
        font=caption_font,
        fill="#ffffff",
        spacing=7,
    )
    canvas.save(output_path, format="PNG", optimize=True)


def _sentence_durations(sentences, total_duration):
    weights = [max(1, len(narration_text(sentence))) for sentence in sentences]
    weight_total = sum(weights)
    durations = [total_duration * weight / weight_total for weight in weights]
    durations[-1] += total_duration - sum(durations)
    return durations


def render_slide_frames(*, scenes, audio_duration, tutor_path, work_dir):
    tutor = _load_tutor(tutor_path)
    sentences = [sentence for scene in scenes for sentence in scene.sentences]
    durations = _sentence_durations(sentences, audio_duration)
    frames = []
    sentence_index = 0
    for scene in scenes:
        for sentence in scene.sentences:
            output = Path(work_dir) / f"frame-{sentence_index:03d}.png"
            _draw_slide(
                scene=scene,
                active_sentence=sentence,
                tutor=tutor,
                output_path=output,
            )
            frames.append((output, durations[sentence_index]))
            sentence_index += 1
    return frames


class FFmpegSlideComposer:
    provider_name = "ffmpeg-local"

    def compose(self, *, frames, audio_path, output_path, work_dir):
        concat_path = Path(work_dir) / "slides.txt"
        lines = []
        for frame_path, duration in frames:
            lines.append(f"file '{frame_path}'")
            lines.append(f"duration {max(0.05, duration):.6f}")
        lines.append(f"file '{frames[-1][0]}'")
        concat_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        command = [
            settings.MULTIMEDIA_FFMPEG_EXECUTABLE,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_path),
            "-i",
            str(audio_path),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-tune",
            "stillimage",
            "-pix_fmt",
            "yuv420p",
            "-r",
            "24",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            "-shortest",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
        try:
            subprocess.run(
                command,
                check=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=settings.MULTIMEDIA_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise MultimediaGenerationError(
                "compose_timeout", "Ghép video quá thời gian cho phép."
            ) from exc
        except (OSError, subprocess.CalledProcessError) as exc:
            raise MultimediaGenerationError(
                "compose_failed", "Không thể ghép video bài giảng."
            ) from exc
        return validate_mp4(output_path)


def validate_mp4(path):
    video = _bounded_file(
        path,
        maximum_bytes=settings.MULTIMEDIA_MAX_OUTPUT_BYTES,
        suffixes={".mp4"},
        label="Video MP4",
    )
    with video.open("rb") as stream:
        if b"ftyp" not in stream.read(32):
            raise MultimediaGenerationError(
                "invalid_output", "Video local trả về không hợp lệ."
            )
    return video


def process_multimedia_job(
    *,
    job,
    narration_provider=None,
    composer=None,
    tutor_path=None,
):
    """Render one authorized job; task code owns terminal failure mapping."""

    authorize_multimedia_generation(actor=job.requested_by, lesson=job.lesson)
    approved_script = job.approved_script
    script = validate_approved_script(approved_script)
    draft = getattr(job.lesson, "video_script_draft", None)
    source = job.lesson.knowledge_sources.filter(
        is_active=True,
        status="ready",
    ).first()
    summary = getattr(job.lesson, "summary_draft", None)
    checksum = sha256(approved_script.encode("utf-8")).hexdigest()
    if (
        checksum != job.script_checksum
        or draft is None
        or draft.status != "approved"
        or draft.text != approved_script
        or source is None
        or summary is None
        or summary.status != "approved"
        or summary.text != job.lesson.ai_summary
        or summary.source_checksum != source.content_checksum
        or summary.source_version != source.version
        or draft.source_checksum != source.content_checksum
        or draft.source_version != source.version
        or draft.summary_checksum
        != sha256(summary.text.encode("utf-8")).hexdigest()
    ):
        raise MultimediaGenerationError(
            "stale_summary",
            "Bản tóm tắt đã thay đổi; hãy tạo lại video từ bản đã duyệt.",
        )
    tutor_path = tutor_path or settings.MULTIMEDIA_TUTOR_IMAGE_PATH
    if tutor_asset_checksum(tutor_path) != job.tutor_asset_checksum:
        raise MultimediaGenerationError(
            "stale_tutor_asset", "Ảnh AI Tutor đã thay đổi; hãy tạo lại job video."
        )

    scenes = build_storyboard(lesson_title=job.lesson.title, script=script)
    narration_provider = narration_provider or PiperVietnameseProvider()
    composer = composer or FFmpegSlideComposer()
    started = time.monotonic()

    with tempfile.TemporaryDirectory(prefix="intaaneto-multimedia-") as directory:
        work_dir = Path(directory)
        audio_path = work_dir / "narration.wav"
        output_path = work_dir / "lesson.mp4"

        job.stage = "narrating"
        job.save(update_fields=["stage"])
        narration_provider.generate(
            text=narration_text(script),
            output_path=audio_path,
        )
        audio, duration = validate_wav(audio_path)

        job.stage = "rendering_slides"
        job.save(update_fields=["stage"])
        frames = render_slide_frames(
            scenes=scenes,
            audio_duration=duration,
            tutor_path=tutor_path,
            work_dir=work_dir,
        )

        job.stage = "compositing"
        job.save(update_fields=["stage"])
        video = composer.compose(
            frames=frames,
            audio_path=audio,
            output_path=output_path,
            work_dir=work_dir,
        )
        video = validate_mp4(video)
        audio_checksum = sha256(audio.read_bytes()).hexdigest()
        render_duration_ms = max(0, round((time.monotonic() - started) * 1000))

        with transaction.atomic():
            (
                narration,
                _,
            ) = LessonNarrationAudio.objects.select_for_update().get_or_create(
                lesson=job.lesson,
                defaults={
                    "summary_checksum": checksum,
                    "audio_checksum": audio_checksum,
                    "provider": narration_provider.provider_name,
                    "voice": settings.PIPER_VOICE,
                    "generated_by": job.requested_by,
                },
            )
            if narration.audio_file:
                narration.audio_file.delete(save=False)
            with audio.open("rb") as stream:
                narration.audio_file.save(
                    f"lesson-{job.lesson_id}-piper-{checksum[:12]}.wav",
                    File(stream),
                    save=False,
                )
            narration.summary_checksum = checksum
            narration.audio_checksum = audio_checksum
            narration.provider = narration_provider.provider_name
            narration.voice = settings.PIPER_VOICE
            narration.generated_by = job.requested_by
            narration.save()

            if job.output_file:
                job.output_file.delete(save=False)
            with video.open("rb") as stream:
                job.output_file.save(
                    f"lesson-{job.lesson_id}-slides-job-{job.id}.mp4",
                    File(stream),
                    save=False,
                )
            job.status = "completed"
            job.stage = "completed"
            job.scene_count = len(scenes)
            job.duration_seconds = Decimal(f"{duration:.2f}")
            job.render_duration_ms = render_duration_ms
            job.failure_code = ""
            job.safe_error = ""
            job.completed_at = timezone.now()
            job.save(
                update_fields=[
                    "output_file",
                    "status",
                    "stage",
                    "scene_count",
                    "duration_seconds",
                    "render_duration_ms",
                    "failure_code",
                    "safe_error",
                    "completed_at",
                ]
            )
            job.lesson.video_file.name = job.output_file.name
            job.lesson.save(update_fields=["video_file"])
    return job
