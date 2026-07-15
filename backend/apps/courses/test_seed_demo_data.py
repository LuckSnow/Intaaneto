from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.ai_assistant.models import ChatMessage, KnowledgeSource
from apps.users.models import User

from .management.commands.seed_demo_data import (
    DEMO_COURSE_SLUG,
    DEMO_LESSON_SLUG,
    DEMO_RAG_CONTENT,
    DEMO_STUDENT_EMAIL,
    DEMO_TEACHER_EMAIL,
    DEMO_TEACHER_USERNAME,
)
from .models import Course, Enrollment, Lesson


@pytest.mark.django_db
def test_seed_demo_data_is_idempotent_and_contains_no_private_state(monkeypatch):
    monkeypatch.delenv('DEMO_TEACHER_PASSWORD', raising=False)
    monkeypatch.delenv('DEMO_STUDENT_PASSWORD', raising=False)

    call_command('seed_demo_data', stdout=StringIO())
    lesson = Lesson.objects.get(slug=DEMO_LESSON_SLUG)
    lesson.content = 'Nội dung cũ cần được đồng bộ lại.'
    lesson.save(update_fields=['content'])
    call_command('seed_demo_data', stdout=StringIO())

    teacher = User.objects.get(email=DEMO_TEACHER_EMAIL)
    student = User.objects.get(email=DEMO_STUDENT_EMAIL)
    course = Course.objects.get(slug=DEMO_COURSE_SLUG)
    lesson.refresh_from_db()

    assert User.objects.filter(email__in=[teacher.email, student.email]).count() == 2
    assert Course.objects.filter(slug=DEMO_COURSE_SLUG).count() == 1
    assert Lesson.objects.filter(course=course, slug=DEMO_LESSON_SLUG).count() == 1
    assert Enrollment.objects.filter(user=student, course=course).count() == 1
    assert teacher.has_usable_password() is False
    assert student.has_usable_password() is False
    assert lesson.content == DEMO_RAG_CONTENT
    assert not lesson.uploaded_file
    assert not lesson.attachments
    assert KnowledgeSource.objects.count() == 0
    assert ChatMessage.objects.count() == 0


@pytest.mark.django_db
def test_seed_demo_passwords_come_only_from_environment(monkeypatch):
    teacher_password = 'LocalTeacherOnly-123!'
    student_password = 'LocalStudentOnly-123!'
    monkeypatch.setenv('DEMO_TEACHER_PASSWORD', teacher_password)
    monkeypatch.setenv('DEMO_STUDENT_PASSWORD', student_password)
    output = StringIO()

    call_command('seed_demo_data', stdout=output)

    assert User.objects.get(email=DEMO_TEACHER_EMAIL).check_password(
        teacher_password
    )
    assert User.objects.get(email=DEMO_STUDENT_EMAIL).check_password(
        student_password
    )
    assert teacher_password not in output.getvalue()
    assert student_password not in output.getvalue()


@pytest.mark.django_db
def test_seed_demo_data_fails_before_overwriting_username_collision():
    User.objects.create_user(
        email='existing@example.com',
        username=DEMO_TEACHER_USERNAME,
        full_name='Existing User',
        password='ExistingPassword-123!',
    )

    with pytest.raises(CommandError, match='belongs to a different account'):
        call_command('seed_demo_data', stdout=StringIO())

    assert not User.objects.filter(email=DEMO_TEACHER_EMAIL).exists()
    assert not Course.objects.filter(slug=DEMO_COURSE_SLUG).exists()


@pytest.mark.django_db
def test_legacy_seed_courses_no_longer_creates_a_fixed_password(monkeypatch):
    monkeypatch.delenv('DEMO_TEACHER_PASSWORD', raising=False)

    call_command('seed_courses', stdout=StringIO())

    teacher = User.objects.get(email='teacher@intaaneto.com')
    assert teacher.has_usable_password() is False
