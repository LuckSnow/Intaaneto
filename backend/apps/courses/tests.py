import pytest

from apps.users.models import User

from .models import Course, Enrollment, Lesson


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
