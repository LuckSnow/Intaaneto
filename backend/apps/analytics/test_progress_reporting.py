import csv
import io
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.courses.models import Course, Enrollment, Lesson, LessonProgress
from apps.exercises.models import AssessmentAttempt, LessonAssessment
from apps.users.models import User


@pytest.fixture
def progress_records(teacher_user, student_user):
    course = Course.objects.create(
        title='Khóa báo cáo',
        slug='khoa-bao-cao',
        description='Dữ liệu báo cáo tiến độ',
        teacher=teacher_user,
        is_published=True,
    )
    first = Lesson.objects.create(
        course=course,
        title='Bài một',
        slug='bao-cao-bai-mot',
        content='Nội dung bài một',
        is_published=True,
        order=1,
    )
    second = Lesson.objects.create(
        course=course,
        title='Bài hai',
        slug='bao-cao-bai-hai',
        content='Nội dung bài hai',
        is_published=True,
        order=2,
    )
    enrollment = Enrollment.objects.create(
        user=student_user,
        course=course,
        progress_percentage=Decimal('50.00'),
        mastery_percentage=Decimal('75.00'),
        last_accessed_lesson=second,
    )
    LessonProgress.objects.create(
        user=student_user,
        lesson=first,
        is_completed=True,
        completed_at=timezone.now(),
    )
    assessment = LessonAssessment.objects.create(
        lesson=first,
        title='Đánh giá báo cáo',
        version=2,
        is_published=True,
    )
    AssessmentAttempt.objects.create(
        assessment=assessment,
        user=student_user,
        assessment_version=1,
        threshold_snapshot=70,
        score=Decimal('100.00'),
        passed=True,
        total_questions=1,
        correct_answers=1,
    )
    current_attempt = AssessmentAttempt.objects.create(
        assessment=assessment,
        user=student_user,
        assessment_version=2,
        threshold_snapshot=70,
        score=Decimal('50.00'),
        passed=False,
        total_questions=2,
        correct_answers=1,
        weak_objectives=['Mục tiêu yếu'],
    )
    return course, first, second, enrollment, current_attempt


@pytest.mark.django_db
def test_learner_report_uses_current_owned_learning_evidence(
    authenticated_client, student_user, progress_records
):
    course, _, second, _, _ = progress_records

    response = authenticated_client.get('/api/analytics/progress_report/')

    assert response.status_code == 200
    assert response.data['scope'] == 'learner'
    assert response.data['summary'] == {
        'courses_enrolled': 1,
        'courses_completed': 0,
        'lessons_completed': 1,
        'assessments_attempted': 1,
        'assessments_passed': 0,
        'average_progress_percentage': Decimal('50.00'),
        'average_mastery_percentage': Decimal('75.00'),
    }
    assert len(response.data['courses']) == 1
    report = response.data['courses'][0]
    assert report['course_id'] == course.id
    assert report['lessons_completed'] == 1
    assert report['lessons_available'] == 2
    assert report['assessments_attempted'] == 1
    assert report['assessments_passed'] == 0
    assert report['last_accessed_lesson'] == {
        'id': second.id,
        'title': second.title,
    }
    assert 'email' not in str(response.data)


@pytest.mark.django_db
def test_teacher_summary_contains_only_owned_courses(
    api_client, teacher_user, student_user, progress_records
):
    owned_course, _, _, _, _ = progress_records
    other_teacher = User.objects.create_user(
        email='report-other-teacher@example.invalid',
        username='report-other-teacher',
        full_name='Other Report Teacher',
        password='LocalTestOnly-123!',
        role='teacher',
        is_verified=True,
    )
    other_course = Course.objects.create(
        title='Khóa giáo viên khác',
        slug='khoa-giao-vien-khac-report',
        description='Không được lộ',
        teacher=other_teacher,
        is_published=True,
    )
    Enrollment.objects.create(user=student_user, course=other_course)
    api_client.force_authenticate(teacher_user)

    response = api_client.get('/api/analytics/progress_report/')

    assert response.status_code == 200
    assert response.data['scope'] == 'teaching'
    assert response.data['summary']['courses'] == 1
    assert [item['course_id'] for item in response.data['courses']] == [
        owned_course.id
    ]
    assert other_course.title not in str(response.data)


@pytest.mark.django_db
def test_teacher_course_report_is_paged_and_omits_email_and_old_attempts(
    api_client, teacher_user, progress_records
):
    course, _, second, _, current_attempt = progress_records
    api_client.force_authenticate(teacher_user)

    response = api_client.get(
        '/api/analytics/progress_report/',
        {'course_id': course.id, 'limit': 1, 'offset': 0},
    )

    assert response.status_code == 200
    assert response.data['scope'] == 'teaching_course'
    assert response.data['pagination'] == {'count': 1, 'limit': 1, 'offset': 0}
    learner = response.data['learners'][0]
    assert learner['full_name'] == current_attempt.user.full_name
    assert learner['assessment_attempts'] == 1
    assert learner['assessments_attempted'] == 1
    assert learner['assessments_passed'] == 0
    assert learner['last_accessed_lesson']['id'] == second.id
    assert 'email' not in learner


@pytest.mark.django_db
def test_teacher_cannot_request_another_teachers_course_report(
    api_client, teacher_user
):
    other_teacher = User.objects.create_user(
        email='private-report-teacher@example.invalid',
        username='private-report-teacher',
        full_name='Private Report Teacher',
        password='LocalTestOnly-123!',
        role='teacher',
        is_verified=True,
    )
    other_course = Course.objects.create(
        title='Báo cáo riêng',
        slug='bao-cao-rieng',
        description='Không được lộ',
        teacher=other_teacher,
    )
    api_client.force_authenticate(teacher_user)

    response = api_client.get(
        '/api/analytics/progress_report/',
        {'course_id': other_course.id},
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_progress_report_requires_authentication(api_client):
    response = api_client.get('/api/analytics/progress_report/')

    assert response.status_code == 401


@pytest.mark.django_db
def test_teacher_exports_owned_course_progress_as_safe_csv(
    api_client, teacher_user, student_user, progress_records
):
    course, _, _, _, _ = progress_records
    student_user.full_name = '=HYPERLINK("https://example.invalid","bad")'
    student_user.save(update_fields=['full_name'])
    api_client.force_authenticate(teacher_user)

    response = api_client.get(
        '/api/analytics/progress-export/',
        {'course_id': course.id},
    )

    assert response.status_code == 200
    assert response['Content-Type'].startswith('text/csv')
    assert response['Content-Disposition'] == (
        f'attachment; filename="course-{course.id}-progress.csv"'
    )
    rows = list(csv.DictReader(io.StringIO(response.content.decode('utf-8-sig'))))
    assert len(rows) == 1
    assert rows[0]['learner_id'] == str(student_user.id)
    assert rows[0]['full_name'].startswith("'=")
    assert rows[0]['progress_percentage'] == '50.00'
    assert rows[0]['mastery_percentage'] == '75.00'
    assert rows[0]['assessment_attempts'] == '1'
    assert rows[0]['assessments_passed'] == '0'
    assert 'email' not in response.content.decode('utf-8-sig').lower()


@pytest.mark.django_db
def test_progress_export_requires_teacher_role_and_owned_course(
    api_client, teacher_user, student_user
):
    private_teacher = User.objects.create_user(
        email='export-owner@example.invalid',
        username='export-owner',
        full_name='Export Owner',
        password='LocalTestOnly-123!',
        role='teacher',
        is_verified=True,
    )
    private_course = Course.objects.create(
        title='Private export',
        slug='private-export',
        description='Không được xuất',
        teacher=private_teacher,
    )

    api_client.force_authenticate(student_user)
    learner_response = api_client.get(
        '/api/analytics/progress-export/',
        {'course_id': private_course.id},
    )
    assert learner_response.status_code == 403

    api_client.force_authenticate(teacher_user)
    other_teacher_response = api_client.get(
        '/api/analytics/progress-export/',
        {'course_id': private_course.id},
    )
    assert other_teacher_response.status_code == 404
