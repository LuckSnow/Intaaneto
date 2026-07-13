from unittest.mock import patch

import pytest

from apps.courses.models import Course, Enrollment, Lesson
from apps.users.models import User

from .models import ChatMessage
from .services import AIProviderError


@pytest.fixture
def authorized_lesson(teacher_user, student_user):
    course = Course.objects.create(
        title='Web cơ bản',
        slug='web-co-ban',
        description='Khóa học',
        teacher=teacher_user,
        is_published=True,
    )
    lesson = Lesson.objects.create(
        course=course,
        title='HTML',
        slug='html',
        content='HTML dùng để tạo cấu trúc trang web.',
        is_published=True,
    )
    Enrollment.objects.create(user=student_user, course=course)
    return lesson


@pytest.mark.django_db
@patch('apps.ai_assistant.views.AIService.chat')
def test_chat_contract_uses_authorized_lesson(mock_chat, authenticated_client, authorized_lesson):
    mock_chat.return_value = {
        'content': 'HTML tạo cấu trúc trang web.',
        'tokens_used': 10,
        'response_time_ms': 5,
    }

    response = authenticated_client.post(
        '/api/ai/chat/send_message/',
        {'message': 'HTML dùng để làm gì?', 'lesson_id': authorized_lesson.id},
        format='json',
    )

    assert response.status_code == 200
    assert response.data['answer'] == 'HTML tạo cấu trúc trang web.'
    assert response.data['citations'] == []
    assert response.data['grounded'] is False
    assert response.data['message']['content'] == response.data['answer']
    assert mock_chat.call_args.kwargs['context']['lesson_title'] == authorized_lesson.title


@pytest.mark.django_db
@patch('apps.ai_assistant.views.AIService.chat')
def test_chat_rejects_unauthorized_lesson_before_provider(mock_chat, api_client, authorized_lesson):
    outsider = User.objects.create_user(
        email='rag-outsider@example.com',
        username='rag-outsider',
        full_name='RAG Outsider',
        password='Testpass123!',
        is_verified=True,
    )
    api_client.force_authenticate(outsider)

    response = api_client.post(
        '/api/ai/chat/send_message/',
        {'message': 'Cho tôi nội dung', 'lesson_id': authorized_lesson.id},
        format='json',
    )

    assert response.status_code == 404
    mock_chat.assert_not_called()


@pytest.mark.django_db
@patch('apps.ai_assistant.views.AIService.chat')
def test_provider_failure_is_explicit_and_not_saved_as_assistant(
    mock_chat, authenticated_client, authorized_lesson
):
    mock_chat.side_effect = AIProviderError('private provider detail')

    response = authenticated_client.post(
        '/api/ai/chat/send_message/',
        {'message': 'Câu hỏi', 'lesson_id': authorized_lesson.id},
        format='json',
    )

    assert response.status_code == 502
    assert 'private provider detail' not in response.data['error']
    assert ChatMessage.objects.filter(role='assistant').count() == 0
