from decimal import Decimal

import pytest

from apps.courses.models import Course, Enrollment, Lesson, LessonProgress
from apps.users.models import User

from .models import (
    AssessmentAttempt,
    AssessmentQuestion,
    Exercise,
    LessonAssessment,
)


@pytest.fixture
def course(teacher_user):
    return Course.objects.create(
        title='Khóa đánh giá',
        slug='khoa-danh-gia',
        description='Khóa học kiểm thử đánh giá',
        teacher=teacher_user,
        is_published=True,
    )


@pytest.fixture
def lesson(course):
    return Lesson.objects.create(
        course=course,
        title='Bài một',
        slug='bai-mot',
        content='Nội dung bài một',
        is_published=True,
    )


@pytest.fixture
def enrollment(student_user, course):
    return Enrollment.objects.create(user=student_user, course=course)


@pytest.fixture
def assessment(lesson):
    assessment = LessonAssessment.objects.create(
        lesson=lesson,
        title='Kiểm tra bài một',
        pass_threshold=70,
        is_published=True,
    )
    AssessmentQuestion.objects.create(
        assessment=assessment,
        prompt='RAG dùng bước nào để tìm bằng chứng?',
        choices=['Retrieval', 'Rendering'],
        correct_choice=0,
        learning_objective='Phân biệt retrieval và generation',
        order=1,
    )
    AssessmentQuestion.objects.create(
        assessment=assessment,
        prompt='Câu trả lời RAG cần đi kèm gì?',
        choices=['Citation', 'Mật khẩu'],
        correct_choice=0,
        learning_objective='Sử dụng citation',
        order=2,
    )
    return assessment


@pytest.mark.django_db
def test_enrolled_learner_reads_questions_without_answer_key(
    authenticated_client, enrollment, assessment
):
    response = authenticated_client.get(
        f'/api/exercises/assessments/{assessment.id}/'
    )

    assert response.status_code == 200
    assert response.data['pass_threshold'] == 70
    assert len(response.data['questions']) == 2
    assert 'correct_choice' not in response.data['questions'][0]
    assert 'explanation' not in response.data['questions'][0]


@pytest.mark.django_db
def test_non_enrolled_learner_cannot_discover_or_submit_assessment(
    api_client, assessment
):
    outsider = User.objects.create_user(
        email='assessment-outsider@example.com',
        username='assessment-outsider',
        full_name='Assessment Outsider',
        password='Testpass123!',
        is_verified=True,
    )
    api_client.force_authenticate(outsider)

    detail = api_client.get(f'/api/exercises/assessments/{assessment.id}/')
    submit = api_client.post(
        f'/api/exercises/assessments/{assessment.id}/submit/',
        {'answers': []},
        format='json',
    )

    assert detail.status_code == 404
    assert submit.status_code == 404
    assert not AssessmentAttempt.objects.exists()


@pytest.mark.django_db
def test_owner_teacher_can_create_assessment_with_hidden_answers(
    api_client, teacher_user, lesson
):
    api_client.force_authenticate(teacher_user)
    response = api_client.post(
        '/api/exercises/assessments/',
        {
            'lesson': lesson.id,
            'title': 'Kiểm tra nhanh',
            'pass_threshold': 75,
            'is_published': True,
            'questions': [
                {
                    'prompt': 'Đâu là bằng chứng?',
                    'choices': ['Citation', 'Phỏng đoán'],
                    'correct_choice': 0,
                    'learning_objective': 'Nhận biết bằng chứng',
                    'explanation': 'Citation trỏ về nguồn.',
                    'order': 1,
                }
            ],
        },
        format='json',
    )

    assert response.status_code == 201
    assert response.data['questions'][0]['correct_choice'] == 0
    assert LessonAssessment.objects.get().lesson == lesson


@pytest.mark.django_db
def test_other_teacher_cannot_create_assessment_for_course(api_client, lesson):
    other_teacher = User.objects.create_user(
        email='other-assessment-teacher@example.com',
        username='other-assessment-teacher',
        full_name='Other Teacher',
        password='Testpass123!',
        role='teacher',
        is_verified=True,
    )
    api_client.force_authenticate(other_teacher)

    response = api_client.post(
        '/api/exercises/assessments/',
        {
            'lesson': lesson.id,
            'title': 'Không được phép',
            'is_published': False,
            'questions': [],
        },
        format='json',
    )

    assert response.status_code == 403
    assert not LessonAssessment.objects.exists()


@pytest.mark.django_db
def test_failed_attempt_records_mastery_and_requires_reinforcement(
    authenticated_client, student_user, enrollment, assessment
):
    questions = list(assessment.questions.all())

    completion = authenticated_client.post(
        f'/api/courses/lessons/{assessment.lesson_id}/complete/'
    )
    response = authenticated_client.post(
        f'/api/exercises/assessments/{assessment.id}/submit/',
        {
            'score': 100,
            'passed': True,
            'answers': [
                {'question_id': questions[0].id, 'selected_choice': 0},
                {'question_id': questions[1].id, 'selected_choice': 1},
            ],
        },
        format='json',
    )

    assert completion.status_code == 409
    assert completion.data['code'] == 'assessment_required'
    assert response.status_code == 201
    assert response.data['score'] == '50.00'
    assert response.data['passed'] is False
    assert response.data['mastery_percentage'] == Decimal('50.00')
    assert response.data['next_lesson'] is None
    assert response.data['weak_objectives'] == ['Sử dụng citation']
    assert not LessonProgress.objects.filter(
        user=student_user,
        lesson=assessment.lesson,
        is_completed=True,
    ).exists()


@pytest.mark.django_db
def test_passing_attempt_completes_lesson_and_returns_next_lesson(
    authenticated_client, student_user, enrollment, assessment, course
):
    next_lesson = Lesson.objects.create(
        course=course,
        title='Bài hai',
        slug='bai-hai',
        content='Nội dung bài hai',
        is_published=True,
        order=2,
    )
    questions = list(assessment.questions.all())

    response = authenticated_client.post(
        f'/api/exercises/assessments/{assessment.id}/submit/',
        {
            'answers': [
                {'question_id': question.id, 'selected_choice': 0}
                for question in questions
            ],
        },
        format='json',
    )

    assert response.status_code == 201
    assert response.data['score'] == '100.00'
    assert response.data['passed'] is True
    assert response.data['progress_percentage'] == Decimal('50.00')
    assert response.data['mastery_percentage'] == Decimal('100.00')
    assert response.data['next_lesson']['id'] == next_lesson.id
    assert LessonProgress.objects.get(
        user=student_user,
        lesson=assessment.lesson,
    ).is_completed
    enrollment.refresh_from_db()
    assert enrollment.last_accessed_lesson == next_lesson
    assert enrollment.mastery_percentage == Decimal('100.00')


@pytest.mark.django_db
def test_submission_rejects_question_from_another_assessment(
    authenticated_client, enrollment, assessment, course
):
    other_lesson = Lesson.objects.create(
        course=course,
        title='Bài khác',
        slug='bai-khac',
        content='Nội dung khác',
        is_published=True,
    )
    other_assessment = LessonAssessment.objects.create(
        lesson=other_lesson,
        title='Đánh giá khác',
        is_published=True,
    )
    other_question = AssessmentQuestion.objects.create(
        assessment=other_assessment,
        prompt='Câu ngoài phạm vi?',
        choices=['Có', 'Không'],
        correct_choice=1,
        order=1,
    )

    response = authenticated_client.post(
        f'/api/exercises/assessments/{assessment.id}/submit/',
        {
            'answers': [
                {'question_id': other_question.id, 'selected_choice': 1},
            ],
        },
        format='json',
    )

    assert response.status_code == 400
    assert not AssessmentAttempt.objects.exists()


@pytest.mark.django_db
def test_assessment_with_attempts_cannot_be_changed_or_deleted(
    api_client, authenticated_client, teacher_user, enrollment, assessment
):
    questions = list(assessment.questions.all())
    submitted = authenticated_client.post(
        f'/api/exercises/assessments/{assessment.id}/submit/',
        {
            'answers': [
                {'question_id': question.id, 'selected_choice': 0}
                for question in questions
            ],
        },
        format='json',
    )
    assert submitted.status_code == 201

    api_client.force_authenticate(teacher_user)
    changed = api_client.patch(
        f'/api/exercises/assessments/{assessment.id}/',
        {'pass_threshold': 90},
        format='json',
    )
    deleted = api_client.delete(f'/api/exercises/assessments/{assessment.id}/')

    assert changed.status_code == 409
    assert deleted.status_code == 409
    assessment.refresh_from_db()
    assert assessment.pass_threshold == 70


@pytest.mark.django_db
def test_student_exercise_response_hides_solution_and_hidden_tests(
    authenticated_client, enrollment, lesson
):
    exercise = Exercise.objects.create(
        lesson=lesson,
        title='HTML cơ bản',
        description='Tạo một tiêu đề',
        instructions='Dùng thẻ heading',
        starter_code='<body></body>',
        solution_code='<h1>Xin chào</h1>',
        test_cases=[{'hidden': True, 'expected': '<h1>Xin chào</h1>'}],
    )

    response = authenticated_client.get(f'/api/exercises/{exercise.id}/')

    assert response.status_code == 200
    assert 'solution_code' not in response.data
    assert 'test_cases' not in response.data


@pytest.mark.django_db
def test_unscoped_legacy_exercise_is_not_visible_to_student(authenticated_client):
    exercise = Exercise.objects.create(
        title='Legacy',
        description='Chưa có lesson',
        instructions='Không được công khai',
    )

    response = authenticated_client.get(f'/api/exercises/{exercise.id}/')

    assert response.status_code == 404


@pytest.mark.django_db
def test_student_cannot_create_exercise(authenticated_client):
    response = authenticated_client.post(
        '/api/exercises/',
        {'title': 'Unauthorized'},
        format='json',
    )

    assert response.status_code == 405
