"""Bounded local SadTalker adapter for a manually approved research PoC."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import wave

from django.conf import settings
from django.core.files import File
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from PIL import Image, UnidentifiedImageError

from .models import LessonVideoGenerationJob
from .storage_utils import StoredFileTooLarge, local_path_for_stored_file


class VideoGenerationError(Exception):
    """Safe SadTalker PoC failure with a bounded machine-readable code."""

    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class GeneratedVideo:
    path: Path
    cleanup_dir: Path | None = None


def authorize_video_generation(*, actor, lesson):
    if not getattr(actor, 'is_authenticated', False) or (
        actor.role != 'admin'
        and (actor.role != 'teacher' or lesson.course.teacher_id != actor.id)
    ):
        raise PermissionDenied('Bạn không có quyền tạo video cho bài học này.')


def _bounded_file(path, *, maximum_bytes, allowed_suffixes, label):
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_file() or resolved.suffix.lower() not in allowed_suffixes:
        raise VideoGenerationError('invalid_input', f'{label} không hợp lệ.')
    size = resolved.stat().st_size
    if size <= 0 or size > maximum_bytes:
        raise VideoGenerationError('input_too_large', f'{label} vượt giới hạn.')
    return resolved


def _checksum(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def validate_approved_script(script):
    normalized = (script or '').replace('\r\n', '\n').replace('\r', '\n').strip()
    if not normalized or len(normalized) > 12000 or '\x00' in normalized:
        raise VideoGenerationError('invalid_script', 'Kịch bản đã duyệt không hợp lệ.')
    return normalized


def validate_audio(path):
    audio = _bounded_file(
        path,
        maximum_bytes=settings.SADTALKER_MAX_AUDIO_BYTES,
        allowed_suffixes={'.wav'},
        label='Audio WAV',
    )
    try:
        with wave.open(str(audio), 'rb') as stream:
            frames = stream.getnframes()
            rate = stream.getframerate()
            duration = frames / rate if rate else 0
            if (
                stream.getnchannels() not in (1, 2)
                or stream.getsampwidth() not in (1, 2, 3, 4)
                or not 8000 <= rate <= 96000
                or duration <= 0
                or duration > settings.SADTALKER_MAX_AUDIO_SECONDS
            ):
                raise VideoGenerationError('invalid_audio', 'Audio WAV không hợp lệ.')
    except (wave.Error, EOFError, OSError) as exc:
        raise VideoGenerationError('invalid_audio', 'Audio WAV không hợp lệ.') from exc
    return audio


def validate_portrait(path):
    portrait = _bounded_file(
        path,
        maximum_bytes=settings.SADTALKER_MAX_PORTRAIT_BYTES,
        allowed_suffixes={'.jpg', '.jpeg', '.png'},
        label='Ảnh chân dung',
    )
    try:
        with Image.open(portrait) as image:
            image.verify()
        with Image.open(portrait) as image:
            width, height = image.size
            if (
                image.format not in ('JPEG', 'PNG')
                or min(width, height) < 256
                or max(width, height) > 4096
                or width * height > settings.SADTALKER_MAX_PORTRAIT_PIXELS
            ):
                raise VideoGenerationError(
                    'invalid_portrait',
                    'Ảnh chân dung không hợp lệ.',
                )
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise VideoGenerationError(
            'invalid_portrait',
            'Ảnh chân dung không hợp lệ.',
        ) from exc
    return portrait


class SadTalkerLocalProvider:
    provider_name = 'sadtalker-local'

    def generate(self, *, audio_path, portrait_path):
        if not settings.SADTALKER_ENABLED:
            raise VideoGenerationError('provider_disabled', 'SadTalker chưa được bật.')
        root = Path(settings.SADTALKER_ROOT).expanduser().resolve()
        inference_script = root / 'inference.py'
        python_executable = Path(
            settings.SADTALKER_PYTHON_EXECUTABLE
        ).expanduser().resolve()
        required_models = (
            root / 'checkpoints' / 'SadTalker_V0.0.2_256.safetensors',
            root / 'checkpoints' / 'mapping_00229-model.pth.tar',
            root / 'gfpgan' / 'weights' / 'alignment_WFLW_4HG.pth',
            root / 'gfpgan' / 'weights' / 'detection_Resnet50_Final.pth',
        )
        if (
            not inference_script.is_file()
            or not python_executable.is_file()
            or any(not model.is_file() or model.stat().st_size == 0 for model in required_models)
        ):
            raise VideoGenerationError(
                'provider_not_installed',
                'SadTalker runtime hoặc checkpoint chưa đầy đủ.',
            )
        work_root = Path(settings.SADTALKER_WORK_ROOT).expanduser().resolve()
        work_root.mkdir(parents=True, exist_ok=True)
        work_dir = Path(tempfile.mkdtemp(prefix='intaaneto-sadtalker-', dir=work_root))
        face_weights_dir = work_dir / 'gfpgan' / 'weights'
        command = [
            str(python_executable),
            str(inference_script),
            '--driven_audio',
            str(audio_path),
            '--source_image',
            str(portrait_path),
            '--checkpoint_dir',
            str(root / 'checkpoints'),
            '--result_dir',
            str(work_dir),
            '--size',
            '256',
            '--batch_size',
            '1',
            '--preprocess',
            'crop',
            '--still',
        ]
        runtime_env = os.environ.copy()
        runtime_env['PATH'] = os.pathsep.join(filter(None, (
            str(python_executable.parent),
            runtime_env.get('PATH', ''),
        )))
        runtime_env['PYTHONNOUSERSITE'] = '1'
        runtime_env.pop('PYTHONHOME', None)
        runtime_env.pop('PYTHONPATH', None)
        try:
            face_weights_dir.mkdir(parents=True)
            for model in required_models[2:]:
                (face_weights_dir / model.name).symlink_to(model)
            process = subprocess.Popen(
                command,
                cwd=work_dir,
                env=runtime_env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError as exc:
            shutil.rmtree(work_dir, ignore_errors=True)
            raise VideoGenerationError(
                'provider_failed',
                'Không thể khởi động SadTalker.',
            ) from exc
        try:
            return_code = process.wait(timeout=settings.SADTALKER_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired as exc:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
            shutil.rmtree(work_dir, ignore_errors=True)
            raise VideoGenerationError(
                'provider_timeout',
                'SadTalker xử lý quá thời gian cho phép.',
            ) from exc
        if return_code != 0:
            shutil.rmtree(work_dir, ignore_errors=True)
            raise VideoGenerationError('provider_failed', 'SadTalker tạo video thất bại.')
        videos = list(work_dir.rglob('*.mp4'))
        if len(videos) != 1:
            shutil.rmtree(work_dir, ignore_errors=True)
            raise VideoGenerationError(
                'invalid_provider_output',
                'SadTalker không trả đúng một video.',
            )
        return GeneratedVideo(path=videos[0], cleanup_dir=work_dir)


def _validate_video(path):
    video = _bounded_file(
        path,
        maximum_bytes=settings.SADTALKER_MAX_OUTPUT_BYTES,
        allowed_suffixes={'.mp4'},
        label='Video đầu ra',
    )
    with video.open('rb') as stream:
        header = stream.read(32)
    if b'ftyp' not in header:
        raise VideoGenerationError(
            'invalid_provider_output',
            'SadTalker trả video không hợp lệ.',
        )
    return video


def generate_lesson_video(
    *,
    actor,
    lesson,
    approved_script,
    audio_path,
    portrait_path,
    rights_and_approval_confirmed,
    provider=None,
):
    """Authorize, validate, render, and attach one audited lesson video."""

    authorize_video_generation(actor=actor, lesson=lesson)
    if not rights_and_approval_confirmed:
        raise VideoGenerationError(
            'approval_required',
            'Cần xác nhận quyền sử dụng ảnh, giọng nói và kịch bản.',
        )
    script = validate_approved_script(approved_script)
    audio = validate_audio(audio_path)
    portrait = validate_portrait(portrait_path)
    provider = provider or SadTalkerLocalProvider()
    job = LessonVideoGenerationJob.objects.create(
        lesson=lesson,
        requested_by=actor,
        provider=provider.provider_name,
        approved_script=script,
        script_checksum=hashlib.sha256(script.encode('utf-8')).hexdigest(),
        audio_checksum=_checksum(audio),
        portrait_checksum=_checksum(portrait),
        rights_and_approval_confirmed=True,
    )
    job.status = 'running'
    job.started_at = timezone.now()
    job.save(update_fields=['status', 'started_at'])

    generated = None
    try:
        generated = provider.generate(audio_path=audio, portrait_path=portrait)
        video = _validate_video(generated.path)
        with video.open('rb') as stream:
            job.output_file.save(
                f'lesson-{lesson.id}-sadtalker-job-{job.id}.mp4',
                File(stream),
                save=False,
            )
        job.status = 'completed'
        job.completed_at = timezone.now()
        job.failure_code = ''
        job.save(update_fields=[
            'output_file', 'status', 'completed_at', 'failure_code',
        ])
        lesson.video_file.name = job.output_file.name
        lesson.save(update_fields=['video_file'])
        return job
    except VideoGenerationError as exc:
        job.status = 'failed'
        job.failure_code = exc.code[:50]
        job.completed_at = timezone.now()
        job.save(update_fields=['status', 'failure_code', 'completed_at'])
        raise
    except Exception as exc:
        job.status = 'failed'
        job.failure_code = 'unexpected_failure'
        job.completed_at = timezone.now()
        job.save(update_fields=['status', 'failure_code', 'completed_at'])
        raise VideoGenerationError(
            'unexpected_failure',
            'Không thể tạo video bài học.',
        ) from exc
    finally:
        if generated and generated.cleanup_dir:
            shutil.rmtree(generated.cleanup_dir, ignore_errors=True)


def process_stored_video_job(*, job, provider=None):
    """Run one already-authorized queued web job on the dedicated GPU worker."""

    if job.status == 'completed':
        return job
    authorize_video_generation(actor=job.requested_by, lesson=job.lesson)
    if not job.rights_and_approval_confirmed:
        raise VideoGenerationError('approval_required', 'Thiếu xác nhận quyền sử dụng.')
    if not job.audio_file or not job.portrait_file:
        raise VideoGenerationError('invalid_input', 'Thiếu audio hoặc ảnh chân dung.')
    validate_approved_script(job.approved_script)
    try:
        with local_path_for_stored_file(
            job.audio_file,
            max_bytes=settings.SADTALKER_MAX_AUDIO_BYTES,
            suffix='.wav',
        ) as audio_path, local_path_for_stored_file(
            job.portrait_file,
            max_bytes=settings.SADTALKER_MAX_PORTRAIT_BYTES,
            suffix=Path(job.portrait_file.name).suffix,
        ) as portrait_path:
            audio = validate_audio(audio_path)
            portrait = validate_portrait(portrait_path)
            provider = provider or SadTalkerLocalProvider()
            job.status = 'running'
            job.started_at = timezone.now()
            job.failure_code = ''
            job.safe_error = ''
            job.save(update_fields=[
                'status', 'started_at', 'failure_code', 'safe_error',
            ])

            generated = None
            try:
                generated = provider.generate(
                    audio_path=audio,
                    portrait_path=portrait,
                )
                video = _validate_video(generated.path)
                with video.open('rb') as stream:
                    job.output_file.save(
                        f'lesson-{job.lesson_id}-sadtalker-job-{job.id}.mp4',
                        File(stream),
                        save=False,
                    )
                job.status = 'completed'
                job.completed_at = timezone.now()
                job.save(update_fields=['output_file', 'status', 'completed_at'])
                job.lesson.video_file.name = job.output_file.name
                job.lesson.save(update_fields=['video_file'])
                return job
            finally:
                if generated and generated.cleanup_dir:
                    shutil.rmtree(generated.cleanup_dir, ignore_errors=True)
    except (StoredFileTooLarge, VideoGenerationError) as exc:
        if isinstance(exc, StoredFileTooLarge):
            exc = VideoGenerationError(
                'invalid_input',
                'Tệp đầu vào vượt giới hạn xử lý.',
            )
        job.status = 'failed'
        job.failure_code = exc.code[:50]
        job.safe_error = str(exc)[:255]
        job.completed_at = timezone.now()
        job.save(update_fields=[
            'status', 'failure_code', 'safe_error', 'completed_at',
        ])
        raise exc
    except Exception as exc:
        job.status = 'failed'
        job.failure_code = 'unexpected_failure'
        job.safe_error = 'Không thể tạo video bài học.'
        job.completed_at = timezone.now()
        job.save(update_fields=[
            'status', 'failure_code', 'safe_error', 'completed_at',
        ])
        raise VideoGenerationError(
            'unexpected_failure',
            'Không thể tạo video bài học.',
        ) from exc
    finally:
        cleared_fields = []
        for field_name in ('audio_file', 'portrait_file'):
            field = getattr(job, field_name)
            if field:
                field.delete(save=False)
                setattr(job, field_name, None)
                cleared_fields.append(field_name)
        if cleared_fields:
            job.save(update_fields=cleared_fields)
