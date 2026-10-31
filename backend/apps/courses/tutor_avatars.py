"""Teacher-owned, immutable tutor images and allowlisted bundled presets."""

from contextlib import contextmanager
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import uuid
import warnings

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.urls import reverse
from PIL import Image, ImageOps, UnidentifiedImageError
from rest_framework.exceptions import ValidationError

from .models import Lesson, TutorAvatar, TUTOR_PRESET_CHOICES
from .multimedia_generation import MultimediaGenerationError, authorize_multimedia_generation
from .storage_utils import local_path_for_stored_file

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_IMAGE_BYTES = 10 * 1024 * 1024
PRESET_FILES = {'avt1': 'avt1.png', 'avt2': 'avt2.jpg', 'avt3': 'avt3.jpg', 'avt4': 'avt4.png', 'avt5': 'avt5.png'}


def preset_path(preset):
    if preset == 'ai_tutor':
        return Path(settings.MULTIMEDIA_TUTOR_IMAGE_PATH)
    if preset not in PRESET_FILES:
        raise ValidationError({'preset_id': 'Avatar mẫu không hợp lệ.'})
    return Path(settings.BASE_DIR) / 'media-assets' / PRESET_FILES[preset]


def normalize_upload(upload):
    suffix = Path(upload.name).suffix.lower()
    formats = {'.png': ('PNG', 'image/png'), '.jpg': ('JPEG', 'image/jpeg'), '.jpeg': ('JPEG', 'image/jpeg'), '.webp': ('WEBP', 'image/webp')}
    if suffix not in formats or not 0 < upload.size <= MAX_UPLOAD_BYTES:
        raise ValidationError({'image': 'Chọn ảnh PNG, JPEG hoặc WebP, tối đa 5 MB.'})
    expected_format, mime = formats[suffix]
    if upload.content_type not in (mime, 'application/octet-stream', ''):
        raise ValidationError({'image': 'Định dạng ảnh không khớp nội dung tải lên.'})
    upload.seek(0)
    data = upload.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValidationError({'image': 'Ảnh vượt quá 5 MB.'})
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as probe:
                if (probe.format != expected_format or getattr(probe, 'n_frames', 1) != 1
                        or min(probe.size) < 64 or max(probe.size) > 4096):
                    raise ValueError('Invalid dimensions or format')
                probe.verify()
            with Image.open(BytesIO(data)) as source:
                normalized = ImageOps.exif_transpose(source).convert('RGBA')
                normalized.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                output = BytesIO()
                normalized.save(output, format='PNG')
                return output.getvalue()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValidationError({'image': 'Ảnh không hợp lệ. Dùng ảnh tĩnh từ 64 đến 4096 px mỗi chiều.'}) from exc


def avatar_library(*, request, lesson):
    owners = {request.user.pk, lesson.course.teacher_id}
    uploads = TutorAvatar.objects.filter(owner_id__in=owners)
    return {
        'presets': [
            {'id': key, 'label': label, 'preview_url': request.build_absolute_uri(reverse('tutor-avatar-preset', args=[key]))}
            for key, label in TUTOR_PRESET_CHOICES
        ],
        'uploads': [
            {'id': avatar.pk, 'label': avatar.label, 'preview_url': request.build_absolute_uri(avatar.image.url)}
            for avatar in uploads
        ],
        'selected': {'preset_id': lesson.tutor_preset, 'upload_id': lesson.tutor_avatar_id},
    }


def select_avatar(*, actor, lesson, preset_id=None, upload_id=None):
    with transaction.atomic():
        locked = Lesson.objects.select_for_update().select_related('course').get(pk=lesson.pk)
        authorize_multimedia_generation(actor=actor, lesson=locked)
        if upload_id is not None:
            avatar = TutorAvatar.objects.filter(pk=upload_id, owner_id__in={actor.pk, locked.course.teacher_id}).first()
            if avatar is None:
                raise ValidationError({'upload_id': 'Avatar không tồn tại trong thư viện của bạn.'})
            locked.tutor_avatar = avatar
        else:
            preset_path(preset_id)
            locked.tutor_preset = preset_id
            locked.tutor_avatar = None
        locked.save(update_fields=['tutor_preset', 'tutor_avatar'])
    lesson.tutor_preset = locked.tutor_preset
    lesson.tutor_avatar = locked.tutor_avatar


def upload_avatar(*, actor, lesson, image, label):
    authorize_multimedia_generation(actor=actor, lesson=lesson)
    data = normalize_upload(image)
    avatar = TutorAvatar(owner=actor, label=label, checksum=sha256(data).hexdigest())
    try:
        with transaction.atomic():
            avatar.image.save(f'{uuid.uuid4().hex}.png', ContentFile(data), save=False)
            avatar.save()
            select_avatar(actor=actor, lesson=lesson, upload_id=avatar.pk)
    except Exception:
        if avatar.image and avatar.image._committed:
            avatar.image.delete(save=False)
        raise
    return avatar


@contextmanager
def job_tutor_path(job):
    if not job.tutor_avatar_id:
        yield preset_path(job.tutor_preset)
        return
    avatar = job.tutor_avatar
    if avatar.owner_id not in {job.requested_by_id, job.lesson.course.teacher_id}:
        raise MultimediaGenerationError('invalid_tutor_avatar', 'Avatar không thuộc giáo viên của bài học.')
    try:
        with local_path_for_stored_file(avatar.image, max_bytes=MAX_IMAGE_BYTES, suffix='.png') as path:
            yield path
    except MultimediaGenerationError:
        raise
    except (OSError, ValueError) as exc:
        raise MultimediaGenerationError('invalid_tutor_avatar', 'Không thể đọc ảnh AI Tutor đã chọn.') from exc
