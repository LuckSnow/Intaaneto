from io import BytesIO

import pytest
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import Course


def image_upload(fmt='PNG', size=(160, 90)):
    output = BytesIO()
    Image.new('RGB', size, '#0f766e').save(output, format=fmt)
    return SimpleUploadedFile('cover.' + fmt.lower(), output.getvalue(), content_type='image/' + fmt.lower())


@pytest.mark.django_db
def test_owner_can_create_replace_and_remove_cover(api_client, teacher_user, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    api_client.force_authenticate(teacher_user)
    response = api_client.post('/api/courses/', {'title': 'Covered course', 'description': 'Demo', 'thumbnail_upload': image_upload()}, format='multipart')
    assert response.status_code == 201, response.data
    course = Course.objects.get(pk=response.data['id'])
    assert response.data['thumbnail'].startswith('http')
    assert 'thumbnail_upload' not in response.data
    original = course.thumbnail.name
    assert 'cover.png' not in original
    response = api_client.patch(f'/api/courses/{course.id}/', {'thumbnail_upload': image_upload('JPEG')}, format='multipart')
    assert response.status_code == 200, response.data
    course.refresh_from_db()
    assert course.thumbnail.name != original
    response = api_client.patch(f'/api/courses/{course.id}/', {'remove_thumbnail': True}, format='json')
    assert response.status_code == 200
    assert response.data['thumbnail'] is None


@pytest.mark.django_db
@pytest.mark.parametrize('kind', ['fake', 'gif', 'oversized', 'dimensions', 'conflict'])
def test_bad_covers_are_rejected(api_client, teacher_user, settings, tmp_path, kind):
    settings.MEDIA_ROOT = tmp_path
    course = Course.objects.create(title='Draft', slug='draft', teacher=teacher_user)
    api_client.force_authenticate(teacher_user)
    upload = image_upload()
    if kind == 'fake':
        upload = SimpleUploadedFile('bad.png', b'<svg onload="alert(1)"/>', content_type='image/png')
    elif kind == 'gif':
        upload = image_upload('GIF')
    elif kind == 'oversized':
        upload = SimpleUploadedFile('big.png', upload.read() + b' ' * (2 * 1024 * 1024), content_type='image/png')
    elif kind == 'dimensions':
        upload = image_upload(size=(4097, 1))
    data = {'thumbnail_upload': upload}
    if kind == 'conflict':
        data['remove_thumbnail'] = True
    response = api_client.patch(f'/api/courses/{course.id}/', data, format='multipart')
    assert response.status_code == 400, response.data
    course.refresh_from_db()
    assert not course.thumbnail
    assert not list(tmp_path.rglob('*.*'))


@pytest.mark.django_db
def test_cover_mutation_is_owner_scoped(api_client, teacher_user, student_user, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    course = Course.objects.create(title='Other course', slug='other', teacher=student_user)
    for actor in (teacher_user, student_user, None):
        api_client.force_authenticate(actor)
        response = api_client.patch(f'/api/courses/{course.id}/', {'thumbnail_upload': image_upload()}, format='multipart')
        assert response.status_code in (401, 403, 404)
    course.refresh_from_db()
    assert not course.thumbnail
    assert not list(tmp_path.rglob('*.*'))
