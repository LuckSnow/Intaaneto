from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.ai_assistant.models import KnowledgeSource
from .models import Course, Lesson
from .management.commands.seed_demo_data import DEMO_TEACHER_EMAIL


def test_catalog_preview_does_not_access_database():
    output = StringIO()
    call_command('seed_demo_catalog', stdout=output)
    assert '8 lessons' in output.getvalue()
    assert '7 lessons' in output.getvalue()
    assert '5 lessons' in output.getvalue()


@pytest.mark.django_db
def test_catalog_is_additive_idempotent_and_preserves_media(teacher_user, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    teacher_user.email = DEMO_TEACHER_EMAIL
    teacher_user.save()
    call_command('seed_demo_catalog', apply=True, publish=True, stdout=StringIO())
    assert Course.objects.filter(teacher=teacher_user, is_published=True).count() == 3
    assert Lesson.objects.filter(is_published=True, processing_status='completed').count() == 20
    assert KnowledgeSource.objects.count() == 0
    lesson = Lesson.objects.first()
    lesson.content = 'Teacher-edited content'
    lesson.video_file = 'keep-video.mp4'
    lesson.save()
    before_files = sorted(p.name for p in tmp_path.rglob('*.svg'))
    call_command('seed_demo_catalog', apply=True, publish=True, stdout=StringIO())
    lesson.refresh_from_db()
    assert lesson.content == 'Teacher-edited content'
    assert lesson.video_file.name == 'keep-video.mp4'
    assert Lesson.objects.count() == 20
    assert sorted(p.name for p in tmp_path.rglob('*.svg')) == before_files


@pytest.mark.django_db
def test_catalog_rejects_other_owner_before_writes(teacher_user, student_user, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    teacher_user.email = DEMO_TEACHER_EMAIL
    teacher_user.save()
    Course.objects.create(slug='demo-php-co-ban', title='Existing', teacher=student_user)
    with pytest.raises(CommandError, match='another teacher'):
        call_command('seed_demo_catalog', apply=True, stdout=StringIO())
    assert Course.objects.count() == 1
    assert Lesson.objects.count() == 0
    assert not list(tmp_path.rglob('*.svg'))


@pytest.mark.django_db
def test_catalog_does_not_create_or_change_demo_account(teacher_user):
    with pytest.raises(CommandError, match='verified Demo Teacher'):
        call_command('seed_demo_catalog', apply=True, stdout=StringIO())
    assert not Course.objects.exists()


@pytest.mark.django_db
def test_catalog_defaults_to_drafts_and_rolls_back_files(teacher_user, settings, tmp_path, monkeypatch):
    settings.MEDIA_ROOT = tmp_path
    teacher_user.email = DEMO_TEACHER_EMAIL
    teacher_user.save()
    from .management.commands.seed_demo_catalog import Command
    original = Command._cover
    calls = []

    def fail_second(course, cover, saved_files):
        if calls:
            raise RuntimeError('Simulated storage failure')
        original(course, cover, saved_files)
        calls.append(course.id)

    with monkeypatch.context() as patch:
        patch.setattr(Command, '_cover', staticmethod(fail_second))
        with pytest.raises(RuntimeError):
            call_command('seed_demo_catalog', apply=True, stdout=StringIO())
    assert not Course.objects.exists()
    assert not list(tmp_path.rglob('*.svg'))
    call_command('seed_demo_catalog', apply=True, stdout=StringIO())
    assert not Course.objects.filter(is_published=True).exists()
    assert not Lesson.objects.filter(is_published=True).exists()
