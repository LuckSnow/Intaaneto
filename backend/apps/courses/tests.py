from decimal import Decimal

import pytest

from apps.users.models import User

from apps.ai_assistant.models import KnowledgeSource

from .models import (
    Course,
    Enrollment,
    Lesson,
    LessonComment,
    LessonProgress,
    Review,
)


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


@pytest.mark.django_db
def test_teacher_managed_courses_include_only_owned_drafts(
    api_client, teacher_user
):
    owned_draft = Course.objects.create(
        title='Bản nháp của tôi',
        slug='ban-nhap-cua-toi',
        description='Draft',
        teacher=teacher_user,
        is_published=False,
    )
    other_teacher = User.objects.create_user(
        email='managed-other@example.com',
        username='managed-other',
        full_name='Managed Other',
        password='Testpass123!',
        role='teacher',
        is_verified=True,
    )
    Course.objects.create(
        title='Bản nháp người khác',
        slug='ban-nhap-nguoi-khac',
        description='Private',
        teacher=other_teacher,
        is_published=False,
    )
    api_client.force_authenticate(teacher_user)

    response = api_client.get('/api/courses/managed/')

    assert response.status_code == 200
    results = response.data['results']
    assert [item['id'] for item in results] == [owned_draft.id]


@pytest.mark.django_db
def test_student_cannot_list_managed_courses(authenticated_client):
    response = authenticated_client.get('/api/courses/managed/')

    assert response.status_code == 403


@pytest.mark.django_db
def test_teacher_lesson_course_filter_cannot_expand_scope(
    api_client, teacher_user, course, lesson
):
    other_teacher = User.objects.create_user(
        email='lesson-filter-other@example.com',
        username='lesson-filter-other',
        full_name='Lesson Filter Other',
        password='Testpass123!',
        role='teacher',
        is_verified=True,
    )
    other_course = Course.objects.create(
        title='Course kín',
        slug='course-kin-filter',
        description='Private',
        teacher=other_teacher,
        is_published=False,
    )
    Lesson.objects.create(
        course=other_course,
        title='Lesson kín',
        slug='lesson-kin-filter',
        content='Private',
        is_published=False,
    )
    api_client.force_authenticate(teacher_user)

    owned = api_client.get(f'/api/courses/lessons/?course={course.id}')
    foreign = api_client.get(
        f'/api/courses/lessons/?course={other_course.id}'
    )
    invalid = api_client.get('/api/courses/lessons/?course=not-an-id')

    assert owned.status_code == 200
    assert [item['id'] for item in owned.data['results']] == [lesson.id]
    assert foreign.status_code == 200
    assert foreign.data['results'] == []
    assert invalid.status_code == 200
    assert invalid.data['results'] == []


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


@pytest.mark.django_db
def test_lesson_comment_requires_lesson_access(api_client, course, lesson):
    outsider = User.objects.create_user(
        email='comment-outsider@example.com',
        username='comment-outsider',
        full_name='Comment Outsider',
        password='Testpass123!',
        is_verified=True,
    )
    api_client.force_authenticate(outsider)

    response = api_client.post(
        '/api/courses/lesson-comments/',
        {'lesson': lesson.id, 'content': 'Không được phép'},
        format='json',
    )

    assert response.status_code == 403
    assert not LessonComment.objects.exists()


@pytest.mark.django_db
def test_lesson_comment_mutation_requires_author_or_admin(
    api_client, student_user, course, lesson
):
    Enrollment.objects.create(user=student_user, course=course)
    comment = LessonComment.objects.create(
        lesson=lesson,
        user=student_user,
        content='Bình luận gốc',
    )
    other = User.objects.create_user(
        email='other-commenter@example.com',
        username='other-commenter',
        full_name='Other Commenter',
        password='Testpass123!',
        is_verified=True,
    )
    Enrollment.objects.create(user=other, course=course)
    api_client.force_authenticate(other)

    update = api_client.patch(
        f'/api/courses/lesson-comments/{comment.id}/',
        {'content': 'Chiếm quyền'},
        format='json',
    )
    delete = api_client.delete(
        f'/api/courses/lesson-comments/{comment.id}/'
    )

    assert update.status_code == 403
    assert delete.status_code == 403
    comment.refresh_from_db()
    assert comment.content == 'Bình luận gốc'


@pytest.mark.django_db
def test_lesson_comment_rejects_parent_from_another_lesson(
    authenticated_client, student_user, course, lesson
):
    Enrollment.objects.create(user=student_user, course=course)
    other_lesson = Lesson.objects.create(
        course=course,
        title='Bài hai',
        slug='bai-hai-comment',
        content='Nội dung',
        is_published=True,
    )
    parent = LessonComment.objects.create(
        lesson=other_lesson,
        user=student_user,
        content='Bình luận bài hai',
    )

    response = authenticated_client.post(
        '/api/courses/lesson-comments/',
        {'lesson': lesson.id, 'parent': parent.id, 'content': 'Sai phạm vi'},
        format='json',
    )

    assert response.status_code == 400, response.data
    assert LessonComment.objects.count() == 1


@pytest.mark.django_db
def test_review_requires_enrollment(authenticated_client, course):
    response = authenticated_client.post(
        '/api/courses/reviews/',
        {'course': course.id, 'rating': 5, 'comment': 'Chưa đăng ký'},
        format='json',
    )

    assert response.status_code == 403
    assert not Review.objects.exists()


@pytest.mark.django_db
def test_review_mutation_requires_author_or_admin(
    api_client, student_user, course
):
    Enrollment.objects.create(user=student_user, course=course)
    review = Review.objects.create(
        user=student_user,
        course=course,
        rating=5,
        comment='Đánh giá gốc',
    )
    other = User.objects.create_user(
        email='other-reviewer@example.com',
        username='other-reviewer',
        full_name='Other Reviewer',
        password='Testpass123!',
        is_verified=True,
    )
    api_client.force_authenticate(other)

    update = api_client.patch(
        f'/api/courses/reviews/{review.id}/',
        {'rating': 1, 'course': course.id},
        format='json',
    )
    delete = api_client.delete(f'/api/courses/reviews/{review.id}/')

    assert update.status_code == 403
    assert delete.status_code == 403
    review.refresh_from_db()
    assert review.rating == 5
