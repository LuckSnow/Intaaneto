from io import StringIO
import os
from pathlib import Path
import wave

import pytest
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction
from PIL import Image

from apps.users.models import User

from .models import Course, Lesson, LessonVideoGenerationJob
from .video_generation import (
    GeneratedVideo,
    SadTalkerLocalProvider,
    VideoGenerationError,
    generate_lesson_video,
)


class FakeSadTalkerProvider:
    provider_name = 'fake-sadtalker'

    def __init__(self, output_path, error=None):
        self.output_path = output_path
        self.error = error
        self.calls = []

    def generate(self, *, audio_path, portrait_path):
        self.calls.append((audio_path, portrait_path))
        if self.error:
            raise self.error
        self.output_path.write_bytes(
            b'\x00\x00\x00\x18ftypmp42intaaneto-test-video'
        )
        return GeneratedVideo(path=self.output_path)


@pytest.fixture
def video_lesson(teacher_user):
    course = Course.objects.create(
        title='Khóa video',
        slug='khoa-video',
        description='Kiểm thử SadTalker',
        teacher=teacher_user,
    )
    return Lesson.objects.create(
        course=course,
        title='Bài video',
        slug='bai-video',
        content='Nội dung video',
    )


@pytest.fixture
def video_inputs(tmp_path):
    audio = tmp_path / 'approved.wav'
    with wave.open(str(audio), 'wb') as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(16000)
        stream.writeframes(b'\x00\x00' * 16000)
    portrait = tmp_path / 'approved.png'
    Image.new('RGB', (256, 256), color=(240, 240, 240)).save(portrait)
    return audio, portrait


@pytest.mark.django_db
def test_owner_generates_audited_video_and_attaches_it(
    settings, tmp_path, teacher_user, video_lesson, video_inputs
):
    settings.MEDIA_ROOT = tmp_path / 'media'
    audio, portrait = video_inputs
    provider = FakeSadTalkerProvider(tmp_path / 'result.mp4')

    job = generate_lesson_video(
        actor=teacher_user,
        lesson=video_lesson,
        approved_script='Kịch bản đã được giảng viên duyệt.',
        audio_path=audio,
        portrait_path=portrait,
        rights_and_approval_confirmed=True,
        provider=provider,
    )

    assert job.status == 'completed'
    assert job.rights_and_approval_confirmed is True
    assert len(job.script_checksum) == 64
    assert len(job.audio_checksum) == 64
    assert len(job.portrait_checksum) == 64
    assert job.output_file.name.endswith('.mp4')
    assert provider.calls == [(audio.resolve(), portrait.resolve())]
    video_lesson.refresh_from_db()
    assert video_lesson.video_file.name == job.output_file.name


@pytest.mark.django_db
def test_other_teacher_is_denied_before_inputs_or_provider(
    tmp_path, video_lesson
):
    other_teacher = User.objects.create_user(
        email='other-video-teacher@example.invalid',
        username='other-video-teacher',
        full_name='Other Video Teacher',
        password='LocalTestOnly-123!',
        role='teacher',
        is_verified=True,
    )
    provider = FakeSadTalkerProvider(tmp_path / 'never.mp4')

    with pytest.raises(PermissionDenied):
        generate_lesson_video(
            actor=other_teacher,
            lesson=video_lesson,
            approved_script='Không được đọc.',
            audio_path=tmp_path / 'missing.wav',
            portrait_path=tmp_path / 'missing.png',
            rights_and_approval_confirmed=True,
            provider=provider,
        )

    assert provider.calls == []
    assert LessonVideoGenerationJob.objects.count() == 0


@pytest.mark.django_db
def test_rights_confirmation_is_required_before_reading_inputs(
    tmp_path, teacher_user, video_lesson
):
    provider = FakeSadTalkerProvider(tmp_path / 'never.mp4')

    with pytest.raises(VideoGenerationError, match='quyền sử dụng'):
        generate_lesson_video(
            actor=teacher_user,
            lesson=video_lesson,
            approved_script='Kịch bản.',
            audio_path=tmp_path / 'missing.wav',
            portrait_path=tmp_path / 'missing.png',
            rights_and_approval_confirmed=False,
            provider=provider,
        )

    assert provider.calls == []
    assert LessonVideoGenerationJob.objects.count() == 0


@pytest.mark.django_db
def test_provider_failure_is_audited_without_private_detail(
    settings, tmp_path, teacher_user, video_lesson, video_inputs
):
    settings.MEDIA_ROOT = tmp_path / 'media'
    audio, portrait = video_inputs
    provider = FakeSadTalkerProvider(
        tmp_path / 'never.mp4',
        error=VideoGenerationError('provider_failed', 'Chi tiết GPU riêng tư'),
    )

    with pytest.raises(VideoGenerationError, match='Chi tiết GPU riêng tư'):
        generate_lesson_video(
            actor=teacher_user,
            lesson=video_lesson,
            approved_script='Kịch bản được duyệt.',
            audio_path=audio,
            portrait_path=portrait,
            rights_and_approval_confirmed=True,
            provider=provider,
        )

    job = LessonVideoGenerationJob.objects.get()
    assert job.status == 'failed'
    assert job.failure_code == 'provider_failed'
    assert 'GPU' not in job.failure_code
    assert not job.output_file


@pytest.mark.django_db
def test_invalid_audio_never_creates_a_job(
    tmp_path, teacher_user, video_lesson, video_inputs
):
    _, portrait = video_inputs
    audio = tmp_path / 'invalid.wav'
    audio.write_bytes(b'not-wave-audio')
    provider = FakeSadTalkerProvider(tmp_path / 'never.mp4')

    with pytest.raises(VideoGenerationError, match='Audio WAV'):
        generate_lesson_video(
            actor=teacher_user,
            lesson=video_lesson,
            approved_script='Kịch bản được duyệt.',
            audio_path=audio,
            portrait_path=portrait,
            rights_and_approval_confirmed=True,
            provider=provider,
        )

    assert provider.calls == []
    assert LessonVideoGenerationJob.objects.count() == 0


@pytest.mark.django_db
def test_management_command_requires_explicit_confirmation(
    teacher_user, video_lesson, tmp_path
):
    with pytest.raises(CommandError, match='approval_required'):
        call_command(
            'generate_sadtalker_video',
            video_lesson.id,
            actor_id=teacher_user.id,
            script_file=tmp_path / 'missing.txt',
            audio_file=tmp_path / 'missing.wav',
            portrait_file=tmp_path / 'missing.png',
            stdout=StringIO(),
        )


@pytest.mark.django_db
def test_management_command_denies_other_teacher_before_reading_files(
    video_lesson, tmp_path
):
    other_teacher = User.objects.create_user(
        email='command-other-video@example.invalid',
        username='command-other-video',
        full_name='Command Other Video',
        password='LocalTestOnly-123!',
        role='teacher',
        is_verified=True,
    )

    with pytest.raises(CommandError, match='không có quyền'):
        call_command(
            'generate_sadtalker_video',
            video_lesson.id,
            actor_id=other_teacher.id,
            script_file=tmp_path / 'missing.txt',
            audio_file=tmp_path / 'missing.wav',
            portrait_file=tmp_path / 'missing.png',
            confirm_rights_and_approval=True,
            stdout=StringIO(),
        )


@pytest.mark.django_db
def test_database_rejects_unconfirmed_video_job(teacher_user, video_lesson):
    with pytest.raises(IntegrityError), transaction.atomic():
        LessonVideoGenerationJob.objects.create(
            lesson=video_lesson,
            requested_by=teacher_user,
            approved_script='Kịch bản không được xác nhận.',
            script_checksum='a' * 64,
            audio_checksum='b' * 64,
            portrait_checksum='c' * 64,
            rights_and_approval_confirmed=False,
        )


def test_local_provider_uses_bounded_reproducible_runtime_environment(
    monkeypatch, settings, tmp_path
):
    root = tmp_path / 'SadTalker'
    checkpoints = root / 'checkpoints'
    checkpoints.mkdir(parents=True)
    face_weights = root / 'gfpgan' / 'weights'
    face_weights.mkdir(parents=True)
    (root / 'inference.py').write_text('pass', encoding='utf-8')
    (checkpoints / 'SadTalker_V0.0.2_256.safetensors').write_bytes(b'model')
    (checkpoints / 'mapping_00229-model.pth.tar').write_bytes(b'mapping')
    (face_weights / 'alignment_WFLW_4HG.pth').write_bytes(b'alignment')
    (face_weights / 'detection_Resnet50_Final.pth').write_bytes(b'detection')
    runtime_bin = tmp_path / 'runtime' / 'bin'
    runtime_bin.mkdir(parents=True)
    python_executable = runtime_bin / 'python'
    python_executable.write_bytes(b'python')
    work_root = tmp_path / 'work'
    settings.SADTALKER_ENABLED = True
    settings.SADTALKER_ROOT = str(root)
    settings.SADTALKER_PYTHON_EXECUTABLE = str(python_executable)
    settings.SADTALKER_WORK_ROOT = str(work_root)
    monkeypatch.setenv('PYTHONHOME', '/private/python-home')
    monkeypatch.setenv('PYTHONPATH', '/private/python-path')
    captured = {}

    class SuccessfulProcess:
        pid = 12345

        def wait(self, timeout=None):
            captured['timeout'] = timeout
            return 0

    def fake_popen(command, **kwargs):
        captured['command'] = command
        captured['kwargs'] = kwargs
        result_dir = Path(command[command.index('--result_dir') + 1])
        (result_dir / 'result.mp4').write_bytes(b'video')
        return SuccessfulProcess()

    monkeypatch.setattr('apps.courses.video_generation.subprocess.Popen', fake_popen)

    generated = SadTalkerLocalProvider().generate(
        audio_path=tmp_path / 'audio.wav',
        portrait_path=tmp_path / 'portrait.png',
    )

    assert generated.path.name == 'result.mp4'
    command = captured['command']
    assert command[0] == str(python_executable.resolve())
    assert command[command.index('--checkpoint_dir') + 1] == str(
        checkpoints.resolve()
    )
    assert command[-7:] == [
        '--size', '256', '--batch_size', '1', '--preprocess', 'crop', '--still',
    ]
    runtime_env = captured['kwargs']['env']
    assert runtime_env['PATH'].split(os.pathsep)[0] == str(runtime_bin.resolve())
    assert runtime_env['PYTHONNOUSERSITE'] == '1'
    assert 'PYTHONHOME' not in runtime_env
    assert 'PYTHONPATH' not in runtime_env
    assert captured['kwargs']['cwd'] == generated.cleanup_dir
    assert (
        generated.cleanup_dir / 'gfpgan' / 'weights' / 'alignment_WFLW_4HG.pth'
    ).is_symlink()
    assert captured['kwargs']['start_new_session'] is True
