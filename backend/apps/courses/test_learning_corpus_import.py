from io import StringIO
from pathlib import Path
import shutil

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.ai_assistant.models import KnowledgeSource
from apps.exercises.models import LessonAssessment
from apps.users.models import User

from .learning_corpus import compile_learning_corpus, is_managed_content
from .models import Course, Lesson


DOCS_ROOT = next(
    candidate
    for candidate in (
        Path(__file__).resolve().parents[3] / 'docs',
        Path('/project-docs'),
    )
    if candidate.is_dir()
)


def create_teacher(**overrides):
    values = {
        'email': 'corpus.teacher@example.invalid',
        'username': 'corpus-teacher',
        'full_name': 'Corpus Teacher',
        'role': 'teacher',
        'is_active': True,
        'is_verified': True,
    }
    values.update(overrides)
    return User.objects.create_user(password='LocalTestOnly-123!', **values)


def test_compile_learning_corpus_builds_structured_lessons():
    courses = compile_learning_corpus(DOCS_ROOT)

    assert len(courses) == 2
    assert sum(len(course.lessons) for course in courses) == 15
    first_lesson = courses[0].lessons[0]
    assert is_managed_content(first_lesson.content)
    assert '## Mục tiêu học tập' in first_lesson.content
    assert '## Nguồn tham khảo chính' in first_lesson.content
    assert '## Mô Hình OSI (Open Systems Interconnection)' in first_lesson.content


@pytest.mark.django_db
def test_import_creates_drafts_without_index_or_assessment():
    teacher = create_teacher()
    output = StringIO()

    call_command(
        'import_learning_corpus',
        teacher_id=teacher.id,
        source_root=DOCS_ROOT,
        stdout=output,
    )

    assert Course.objects.count() == 2
    assert Lesson.objects.count() == 15
    assert not Course.objects.filter(is_published=True).exists()
    assert not Lesson.objects.filter(is_published=True).exists()
    assert Lesson.objects.filter(
        lesson_type='text', processing_status='completed'
    ).count() == 15
    assert KnowledgeSource.objects.count() == 0
    assert LessonAssessment.objects.count() == 0
    assert 'Index command:' in output.getvalue()


@pytest.mark.django_db
def test_import_is_idempotent_and_publish_is_explicit():
    teacher = create_teacher()
    command_options = {
        'teacher_id': teacher.id,
        'source_root': DOCS_ROOT,
        'stdout': StringIO(),
    }

    call_command('import_learning_corpus', **command_options)
    lesson = Lesson.objects.order_by('id').first()
    original_content = lesson.content
    call_command(
        'import_learning_corpus',
        publish=True,
        **{**command_options, 'stdout': StringIO()},
    )

    assert Course.objects.count() == 2
    assert Lesson.objects.count() == 15
    assert Course.objects.filter(is_published=True).count() == 2
    assert Lesson.objects.filter(is_published=True).count() == 15
    lesson.refresh_from_db()
    assert lesson.content == original_content

    call_command(
        'import_learning_corpus',
        **{**command_options, 'stdout': StringIO()},
    )
    assert not Course.objects.filter(is_published=False).exists()
    assert not Lesson.objects.filter(is_published=False).exists()


@pytest.mark.django_db
def test_import_requires_an_active_verified_teacher():
    learner = create_teacher(role='student')

    with pytest.raises(CommandError, match='active, verified'):
        call_command(
            'import_learning_corpus',
            teacher_id=learner.id,
            source_root=DOCS_ROOT,
            stdout=StringIO(),
        )

    assert Course.objects.count() == 0


@pytest.mark.django_db
def test_course_owner_collision_rolls_back_all_changes():
    teacher = create_teacher()
    other_teacher = create_teacher(
        email='other.teacher@example.invalid',
        username='other-corpus-teacher',
    )
    Course.objects.create(
        title='Existing course',
        slug='hoc-lieu-lap-trinh-web',
        description='Owned by another teacher.',
        teacher=other_teacher,
    )

    with pytest.raises(CommandError, match='belongs to another teacher'):
        call_command(
            'import_learning_corpus',
            teacher_id=teacher.id,
            source_root=DOCS_ROOT,
            stdout=StringIO(),
        )

    assert not Course.objects.filter(slug='hoc-lieu-mang-may-tinh').exists()
    assert Lesson.objects.count() == 0


@pytest.mark.django_db
def test_manual_lesson_collision_is_not_overwritten():
    teacher = create_teacher()
    course = Course.objects.create(
        title='Existing network course',
        slug='hoc-lieu-mang-may-tinh',
        description='Teacher-authored course.',
        teacher=teacher,
    )
    lesson = Lesson.objects.create(
        course=course,
        title='Manual lesson',
        slug='tong-quan-va-mo-hinh-mang',
        content='Nội dung giáo viên tạo thủ công.',
    )

    with pytest.raises(CommandError, match='refusing to overwrite'):
        call_command(
            'import_learning_corpus',
            teacher_id=teacher.id,
            source_root=DOCS_ROOT,
            stdout=StringIO(),
        )

    lesson.refresh_from_db()
    assert lesson.content == 'Nội dung giáo viên tạo thủ công.'
    assert not Course.objects.filter(slug='hoc-lieu-lap-trinh-web').exists()


@pytest.mark.django_db
def test_dry_run_needs_no_teacher_and_does_not_touch_database():
    call_command(
        'import_learning_corpus',
        dry_run=True,
        source_root=DOCS_ROOT,
        stdout=StringIO(),
    )

    assert Course.objects.count() == 0
    assert Lesson.objects.count() == 0


def test_missing_expected_heading_fails_validation(tmp_path):
    for filename in ('computer-networks.md', 'web-programming.md'):
        shutil.copyfile(DOCS_ROOT / filename, tmp_path / filename)
    network_path = tmp_path / 'computer-networks.md'
    network_path.write_text(
        network_path.read_text(encoding='utf-8').replace(
            '## Network Security', '### Network Security', 1
        ),
        encoding='utf-8',
    )

    with pytest.raises(ValueError, match='Missing headings'):
        compile_learning_corpus(tmp_path)
