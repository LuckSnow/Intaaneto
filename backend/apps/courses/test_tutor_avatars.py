from hashlib import sha256
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.users.models import User
from .models import TutorAvatar, LessonMultimediaJob
from .multimedia_generation import MultimediaGenerationError, process_multimedia_job, _load_tutor
from .multimedia_queue import queue_lesson_multimedia
from .tutor_avatars import normalize_upload, select_avatar, upload_avatar
from .test_multimedia_generation import multimedia_lesson, FakePiperProvider, FakeComposer


def image_upload(fmt='PNG', size=(100, 120)):
    data = BytesIO()
    Image.new('RGBA' if fmt != 'JPEG' else 'RGB', size, (32, 160, 90)).save(data, format=fmt)
    ext = {'PNG': 'png', 'JPEG': 'jpg', 'WEBP': 'webp'}[fmt]
    return SimpleUploadedFile('teacher.' + ext, data.getvalue(), content_type='image/' + ('jpeg' if fmt == 'JPEG' else ext))


@pytest.fixture
def avatar_client(api_client, teacher_user, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / 'media'
    api_client.force_authenticate(teacher_user)
    return api_client


@pytest.mark.django_db
def test_six_presets_and_selection_survive_reload(avatar_client, multimedia_lesson):
    url = f'/api/courses/lessons/{multimedia_lesson.pk}'
    response = avatar_client.get(url + '/authoring-status/')
    assert response.status_code == 200
    library = response.data['tutor_avatars']
    assert len(library['presets']) == 6
    assert library['selected'] == {'preset_id': 'ai_tutor', 'upload_id': None}
    for preset in library['presets']:
        preview = avatar_client.get(f"/api/courses/tutor-avatar-presets/{preset['id']}/")
        assert preview.status_code == 200
        assert preview['Content-Type'].startswith('image/')
        preview.close()
    response = avatar_client.put(url + '/tutor-avatar/', {'preset_id': 'avt2'}, format='json')
    assert response.status_code == 200
    assert avatar_client.get(url + '/authoring-status/').data['tutor_avatars']['selected']['preset_id'] == 'avt2'
    multimedia_lesson.refresh_from_db()
    assert multimedia_lesson.tutor_preset == 'avt2'
    assert multimedia_lesson.tutor_avatar_id is None


@pytest.mark.django_db
@pytest.mark.parametrize('fmt', ['PNG', 'JPEG', 'WEBP'])
def test_upload_normalizes_selects_and_retains_private_library(avatar_client, multimedia_lesson, teacher_user, fmt):
    url = f'/api/courses/lessons/{multimedia_lesson.pk}/tutor-avatar/'
    response = avatar_client.post(url, {'image': image_upload(fmt), 'label': 'Giảng viên riêng', 'owner': 999}, format='multipart')
    assert response.status_code == 201
    avatar = TutorAvatar.objects.get()
    assert avatar.owner == teacher_user
    assert avatar.label == 'Giảng viên riêng'
    with avatar.image.open('rb') as stream:
        content = stream.read()
    assert sha256(content).hexdigest() == avatar.checksum
    with Image.open(BytesIO(content)) as decoded:
        assert decoded.format == 'PNG'
    assert 'teacher.' not in avatar.image.name
    assert response.data['tutor_avatars']['selected']['upload_id'] == avatar.pk
    assert 'checksum' not in response.data['tutor_avatars']['uploads'][0]
    assert avatar_client.put(url, {'preset_id': 'avt1'}, format='json').status_code == 200
    response = avatar_client.put(url, {'upload_id': avatar.pk}, format='json')
    assert response.data['tutor_avatars']['selected']['upload_id'] == avatar.pk


@pytest.mark.django_db
def test_cross_teacher_avatar_and_library_are_denied(avatar_client, multimedia_lesson):
    other = User.objects.create_user(username='avatar-other', email='avatar-other@example.invalid', role='teacher')
    avatar = TutorAvatar.objects.create(owner=other, image='private-other.png', checksum='a' * 64)
    response = avatar_client.put(f'/api/courses/lessons/{multimedia_lesson.pk}/tutor-avatar/', {'upload_id': avatar.pk}, format='json')
    assert response.status_code == 400
    library = avatar_client.get(f'/api/courses/lessons/{multimedia_lesson.pk}/authoring-status/').data['tutor_avatars']
    assert library['uploads'] == []


@pytest.mark.django_db
@pytest.mark.parametrize('actor', ['anonymous', 'student', 'other_teacher'])
def test_upload_authorizes_before_reading_image(api_client, student_user, multimedia_lesson, actor):
    if actor == 'student':
        api_client.force_authenticate(student_user)
    elif actor == 'other_teacher':
        user = User.objects.create_user(username='outsider', email='outsider@example.invalid', role='teacher')
        api_client.force_authenticate(user)
    with patch('apps.courses.tutor_avatars.normalize_upload') as normalize:
        response = api_client.post(f'/api/courses/lessons/{multimedia_lesson.pk}/tutor-avatar/', {'image': image_upload()}, format='multipart')
    assert response.status_code in (401, 403, 404)
    normalize.assert_not_called()
    assert not TutorAvatar.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize('selection', [{}, {'preset_id': '../secrets'}, {'upload_id': -1}, {'preset_id': 'avt1', 'upload_id': 1}])
def test_invalid_selection_rejected(avatar_client, multimedia_lesson, selection):
    response = avatar_client.put(f'/api/courses/lessons/{multimedia_lesson.pk}/tutor-avatar/', selection, format='json')
    assert response.status_code == 400


@pytest.mark.django_db
@pytest.mark.parametrize('kind', ['spoof', 'oversize', 'dimensions', 'tiny', 'mime', 'animated', 'svg'])
def test_invalid_uploads_leave_no_records(avatar_client, multimedia_lesson, kind):
    if kind == 'spoof':
        image = SimpleUploadedFile('x.png', b'not an image', content_type='image/png')
    elif kind == 'oversize':
        image = SimpleUploadedFile('x.png', b'x' * (5 * 1024 * 1024 + 1), content_type='image/png')
    elif kind == 'dimensions':
        image = image_upload(size=(4097, 64))
    elif kind == 'tiny':
        image = image_upload(size=(32, 32))
    elif kind == 'mime':
        image = image_upload()
        image.content_type = 'text/html'
    elif kind == 'svg':
        image = SimpleUploadedFile('x.svg', b'<svg/>', content_type='image/svg+xml')
    else:
        data = BytesIO()
        Image.new('RGB', (100, 100), 'red').save(data, format='PNG', save_all=True, append_images=[Image.new('RGB', (100, 100), 'blue')])
        image = SimpleUploadedFile('animated.png', data.getvalue(), content_type='image/png')
    response = avatar_client.post(f'/api/courses/lessons/{multimedia_lesson.pk}/tutor-avatar/', {'image': image}, format='multipart')
    assert response.status_code == 400
    assert not TutorAvatar.objects.exists()


@pytest.mark.django_db
def test_custom_avatar_render_uses_queued_snapshot(avatar_client, teacher_user, multimedia_lesson, settings):
    avatar = upload_avatar(actor=teacher_user, lesson=multimedia_lesson, image=image_upload(), label='Snapshot')
    with patch('apps.courses.tasks.process_lesson_multimedia_job.apply_async'):
        job, _ = queue_lesson_multimedia(actor=teacher_user, lesson=multimedia_lesson)
    select_avatar(actor=teacher_user, lesson=multimedia_lesson, preset_id='avt2')
    job.refresh_from_db()
    assert job.tutor_avatar_id == avatar.pk
    composer = FakeComposer()
    process_multimedia_job(job=job, narration_provider=FakePiperProvider(), composer=composer)
    job.refresh_from_db()
    assert job.status == 'completed'
    assert job.tutor_asset_checksum == avatar.checksum


@pytest.mark.django_db
def test_changed_custom_image_fails_before_narration(avatar_client, teacher_user, multimedia_lesson):
    avatar = upload_avatar(actor=teacher_user, lesson=multimedia_lesson, image=image_upload(), label='Snapshot')
    with patch('apps.courses.tasks.process_lesson_multimedia_job.apply_async'):
        job, _ = queue_lesson_multimedia(actor=teacher_user, lesson=multimedia_lesson)
    Path(avatar.image.path).write_bytes(b'changed')
    provider = FakePiperProvider()
    with patch.object(provider, 'generate') as generate:
        with pytest.raises(MultimediaGenerationError) as error:
            process_multimedia_job(job=job, narration_provider=provider)
    assert error.value.code == 'stale_tutor_asset'
    generate.assert_not_called()


@pytest.mark.django_db
def test_worker_denies_foreign_avatar_before_storage_read(avatar_client, teacher_user, multimedia_lesson):
    avatar = upload_avatar(actor=teacher_user, lesson=multimedia_lesson, image=image_upload(), label='Snapshot')
    with patch('apps.courses.tasks.process_lesson_multimedia_job.apply_async'):
        job, _ = queue_lesson_multimedia(actor=teacher_user, lesson=multimedia_lesson)
    other = User.objects.create_user(username='changed-owner', email='changed-owner@example.invalid', role='teacher')
    TutorAvatar.objects.filter(pk=avatar.pk).update(owner=other)
    job.refresh_from_db()
    with patch('apps.courses.tutor_avatars.local_path_for_stored_file') as read:
        with pytest.raises(MultimediaGenerationError) as error:
            process_multimedia_job(job=job)
    assert error.value.code == 'invalid_tutor_avatar'
    read.assert_not_called()


def test_transparency_survives_image_load(tmp_path):
    image = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
    image.putpixel((50, 50), (255, 0, 0, 255))
    path = tmp_path / 'transparent.png'
    image.save(path)
    loaded = _load_tutor(path)
    assert loaded.mode == 'RGBA'
    assert loaded.getpixel((0, 0))[3] == 0
