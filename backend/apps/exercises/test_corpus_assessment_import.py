from decimal import Decimal
from io import StringIO
from pathlib import Path

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.courses.learning_corpus import COURSE_DEFINITIONS
from apps.courses.models import Course, Lesson
from apps.users.models import User

from .assessment_blueprints import (
    ASSESSMENT_BLUEPRINTS,
    QUESTIONS_PER_OBJECTIVE,
    validate_assessment_blueprints,
)
from .models import AssessmentAttempt, AssessmentQuestion, LessonAssessment


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
        'email': 'assessment.corpus.teacher@example.invalid',
        'username': 'assessment-corpus-teacher',
        'full_name': 'Assessment Corpus Teacher',
        'role': 'teacher',
        'is_active': True,
        'is_verified': True,
    }
    values.update(overrides)
    return User.objects.create_user(password='LocalTestOnly-123!', **values)


def import_corpus(teacher):
    call_command(
        'import_learning_corpus',
        teacher_id=teacher.id,
        source_root=DOCS_ROOT,
        stdout=StringIO(),
    )


def test_blueprints_cover_three_questions_per_declared_corpus_objective():
    blueprints = validate_assessment_blueprints()
    lesson_objectives = {
        (course.slug, lesson.slug): lesson.objectives
        for course in COURSE_DEFINITIONS
        for lesson in course.lessons
    }

    assert len(blueprints) == 3
    assert sum(len(item.questions) for item in blueprints) == 27
    for blueprint in blueprints:
        assert lesson_objectives[
            (blueprint.course_slug, blueprint.lesson_slug)
        ] == blueprint.objectives
        for objective in blueprint.objectives:
            assert sum(
                question.learning_objective == objective
                for question in blueprint.questions
            ) == QUESTIONS_PER_OBJECTIVE


@pytest.mark.django_db
def test_dry_run_validates_without_teacher_or_database_changes():
    output = StringIO()

    call_command('import_corpus_assessments', dry_run=True, stdout=output)

    assert '3 assessments and 27 questions' in output.getvalue()
    assert not Course.objects.exists()
    assert not LessonAssessment.objects.exists()


@pytest.mark.django_db
def test_import_creates_only_draft_assessments_for_managed_lessons():
    teacher = create_teacher()
    import_corpus(teacher)
    output = StringIO()

    call_command(
        'import_corpus_assessments',
        teacher_id=teacher.id,
        stdout=output,
    )

    assert LessonAssessment.objects.count() == 3
    assert AssessmentQuestion.objects.count() == 27
    assert not LessonAssessment.objects.filter(is_published=True).exists()
    assert set(
        LessonAssessment.objects.values_list('lesson__slug', flat=True)
    ) == {item.lesson_slug for item in ASSESSMENT_BLUEPRINTS}
    assert 'correct_choice' not in output.getvalue()


@pytest.mark.django_db
def test_import_is_idempotent_and_publish_requires_explicit_review_flag():
    teacher = create_teacher()
    import_corpus(teacher)

    call_command(
        'import_corpus_assessments',
        teacher_id=teacher.id,
        stdout=StringIO(),
    )
    assessment_ids = list(
        LessonAssessment.objects.order_by('id').values_list('id', flat=True)
    )
    call_command(
        'import_corpus_assessments',
        teacher_id=teacher.id,
        publish_reviewed=True,
        stdout=StringIO(),
    )
    call_command(
        'import_corpus_assessments',
        teacher_id=teacher.id,
        stdout=StringIO(),
    )

    assert list(
        LessonAssessment.objects.order_by('id').values_list('id', flat=True)
    ) == assessment_ids
    assert LessonAssessment.objects.filter(is_published=True).count() == 3
    assert set(LessonAssessment.objects.values_list('version', flat=True)) == {1}
    assert AssessmentQuestion.objects.count() == 27


@pytest.mark.django_db
def test_import_requires_active_verified_teacher_role():
    learner = create_teacher(role='student')

    with pytest.raises(CommandError, match='active, verified'):
        call_command(
            'import_corpus_assessments',
            teacher_id=learner.id,
            stdout=StringIO(),
        )

    assert not LessonAssessment.objects.exists()


@pytest.mark.django_db
def test_missing_target_lesson_rolls_back_all_new_assessments():
    teacher = create_teacher()
    import_corpus(teacher)
    Lesson.objects.filter(slug='bao-mat-web').delete()

    with pytest.raises(CommandError, match='does not exist'):
        call_command(
            'import_corpus_assessments',
            teacher_id=teacher.id,
            stdout=StringIO(),
        )

    assert not LessonAssessment.objects.exists()


@pytest.mark.django_db
def test_other_teacher_course_is_rejected_before_any_assessment_is_created():
    teacher = create_teacher()
    other_teacher = create_teacher(
        email='other.assessment.corpus.teacher@example.invalid',
        username='other-assessment-corpus-teacher',
    )
    import_corpus(teacher)
    Course.objects.filter(slug='hoc-lieu-mang-may-tinh').update(
        teacher=other_teacher
    )

    with pytest.raises(CommandError, match='belongs to another teacher'):
        call_command(
            'import_corpus_assessments',
            teacher_id=teacher.id,
            stdout=StringIO(),
        )

    assert not LessonAssessment.objects.exists()


@pytest.mark.django_db
def test_different_existing_assessment_with_attempt_is_never_overwritten():
    teacher = create_teacher()
    learner = User.objects.create_user(
        email='assessment.corpus.learner@example.invalid',
        username='assessment-corpus-learner',
        full_name='Assessment Corpus Learner',
        password='LocalTestOnly-123!',
        is_verified=True,
    )
    import_corpus(teacher)
    call_command(
        'import_corpus_assessments',
        teacher_id=teacher.id,
        stdout=StringIO(),
    )
    assessment = LessonAssessment.objects.get(
        lesson__slug='tong-quan-va-mo-hinh-mang'
    )
    assessment.title = 'Giảng viên đã chỉnh sửa thủ công'
    assessment.save(update_fields=['title', 'updated_at'])
    attempt = AssessmentAttempt.objects.create(
        assessment=assessment,
        user=learner,
        assessment_version=assessment.version,
        threshold_snapshot=assessment.pass_threshold,
        score=Decimal('0.00'),
        passed=False,
        total_questions=9,
        correct_answers=0,
        weak_objectives=['Mục tiêu cần củng cố'],
    )
    question_ids = list(
        assessment.questions.order_by('id').values_list('id', flat=True)
    )

    with pytest.raises(CommandError, match='with learner attempts'):
        call_command(
            'import_corpus_assessments',
            teacher_id=teacher.id,
            stdout=StringIO(),
        )

    assessment.refresh_from_db()
    assert assessment.title == 'Giảng viên đã chỉnh sửa thủ công'
    assert list(
        assessment.questions.order_by('id').values_list('id', flat=True)
    ) == question_ids
    assert AssessmentAttempt.objects.filter(pk=attempt.pk).exists()
