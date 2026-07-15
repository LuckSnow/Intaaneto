from decimal import Decimal

import pytest

from apps.users.models import User

from apps.ai_assistant.models import KnowledgeSource

from .models import Course, Enrollment, Lesson, LessonProgress


@pytest.fixture
def course(teacher_user):
    return Course.objects.create(
        title='Lập trình web',
        slug='lap-trinh-web',
        description='Khóa học thử nghiệm',
        teacher=teacher_user,
        is_published=True,
    )


@pytest.fixture
def lesson(course):
    return Lesson.objects.create(
        course=course,
        title='HTML nhập môn',
        slug='html-nhap-mon',
        content='HTML tạo cấu trúc cho trang web.',
        is_published=True,
    )


@pytest.mark.django_db
def test_anonymous_user_cannot_create_course(api_client, teacher_user):
    response = api_client.post(
        '/api/courses/',
        {'title': 'Fake', 'description': 'Fake', 'teacher': teacher_user.id},
        format='json',
    )

    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_enrolled_student_can_read_lesson(authenticated_client, student_user, course, lesson):
    Enrollment.objects.create(user=student_user, course=course)

    response = authenticated_client.get(f'/api/courses/lessons/{lesson.id}/')

    assert response.status_code == 200
    assert response.data['id'] == lesson.id


@pytest.mark.django_db
def test_non_enrolled_student_cannot_read_lesson(api_client, course, lesson):
    outsider = User.objects.create_user(
        email='outsider@example.com',
        username='outsider',
        full_name='Outsider',
        password='Testpass123!',
        is_verified=True,
    )
    api_client.force_authenticate(outsider)

    response = api_client.get(f'/api/courses/lessons/{lesson.id}/')

    assert response.status_code == 404


@pytest.mark.django_db
def test_public_course_detail_hides_unpublished_lesson(api_client, course, lesson):
    Lesson.objects.create(
        course=course,
        title='Bản nháp bí mật',
        slug='ban-nhap-bi-mat',
        content='Nội dung chưa công bố',
        is_published=False,
    )

    response = api_client.get(f'/api/courses/{course.id}/')

    assert response.status_code == 200
    assert [item['id'] for item in response.data['lessons']] == [lesson.id]
    assert 'content' not in response.data['lessons'][0]


def create_ready_source(lesson):
    return KnowledgeSource.objects.create(
        lesson=lesson,
        source_type='extracted_text',
        version=1,
        content_checksum='a' * 64,
        normalized_text='Nội dung PDF đã được index.',
        status='ready',
        is_active=True,
        embedding_provider='test',
        embedding_model='test-model',
        embedding_revision='1',
        embedding_dimension=3,
        chunker_version='test-v1',
        chunk_size=100,
        chunk_overlap=10,
    )


@pytest.mark.django_db
def test_complete_lesson_returns_next_ready_lesson_and_updates_progress(
    authenticated_client, student_user, course, lesson
):
    Enrollment.objects.create(user=student_user, course=course)
    failed_pdf = Lesson.objects.create(
        course=course,
        title='PDF lỗi',
        slug='pdf-loi',
        order=1,
        processing_status='failed',
        is_published=True,
    )
    ready_pdf = Lesson.objects.create(
        course=course,
        title='PDF đã index',
        slug='pdf-da-index',
        order=1,
        extracted_text='Nội dung PDF',
        processing_status='completed',
        is_published=True,
    )
    create_ready_source(ready_pdf)

    response = authenticated_client.post(f'/api/courses/lessons/{lesson.id}/complete/')

    assert response.status_code == 200
    assert response.data['next_lesson']['id'] == ready_pdf.id
    assert response.data['progress_percentage'] == Decimal('50.00')
    assert response.data['next_lesson']['id'] != failed_pdf.id
    assert LessonProgress.objects.get(user=student_user, lesson=lesson).is_completed
    enrollment = Enrollment.objects.get(user=student_user, course=course)
    assert enrollment.last_accessed_lesson == ready_pdf


@pytest.mark.django_db
def test_complete_final_available_lesson_returns_no_next_lesson(
    authenticated_client, student_user, course, lesson
):
    Enrollment.objects.create(user=student_user, course=course)

    response = authenticated_client.post(f'/api/courses/lessons/{lesson.id}/complete/')

    assert response.status_code == 200
    assert response.data['next_lesson'] is None
    assert response.data['progress_percentage'] == Decimal('100.00')


@pytest.mark.django_db
def test_preview_completion_does_not_reveal_next_lesson(api_client, course, lesson):
    lesson.is_preview = True
    lesson.save(update_fields=['is_preview'])
    Lesson.objects.create(
        course=course,
        title='Bài dành cho học viên',
        slug='bai-danh-cho-hoc-vien',
        content='Nội dung riêng của khóa học.',
        order=2,
        is_published=True,
    )
    outsider = User.objects.create_user(
        email='preview@example.com',
        username='preview-user',
        full_name='Preview User',
        password='Testpass123!',
        is_verified=True,
    )
    api_client.force_authenticate(outsider)

    response = api_client.post(f'/api/courses/lessons/{lesson.id}/complete/')

    assert response.status_code == 200
    assert response.data['next_lesson'] is None
