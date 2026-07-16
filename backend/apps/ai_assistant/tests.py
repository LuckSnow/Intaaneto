from unittest.mock import patch

import pytest

from apps.courses.models import Course, Enrollment, Lesson
from apps.exercises.models import Exercise
from apps.users.models import User

from .models import ChatMessage, ChatSession
from .rag_answering import GroundedAnswer, WEAK_EVIDENCE_FALLBACK
from .rag_services import LessonRetrievalError
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
@patch('apps.ai_assistant.views.answer_lesson_question')
def test_chat_contract_uses_grounded_lesson_answer(
    mock_answer, authenticated_client, authorized_lesson, student_user
):
    citation = {
        'id': 'knowledge-chunk-11',
        'chunk_id': 11,
        'lesson_id': authorized_lesson.id,
        'lesson_title': authorized_lesson.title,
        'excerpt': 'HTML dùng để tạo cấu trúc trang web.',
    }
    mock_answer.return_value = GroundedAnswer(
        answer='HTML tạo cấu trúc trang web.',
        citations=[citation],
        grounded=True,
        retrieval={
            'status': 'ready',
            'source_version': 1,
            'candidate_count': 2,
            'evidence_count': 1,
        },
        retrieval_metadata={
            'grounded': True,
            'retrieval': {
                'status': 'ready',
                'source_id': 3,
                'source_version': 1,
                'selected_chunks': [{'chunk_id': 11, 'score': 0.8}],
                'latency_ms': 2,
            },
        },
        tokens_used=10,
        response_time_ms=5,
    )

    response = authenticated_client.post(
        '/api/ai/chat/send_message/',
        {'message': 'HTML dùng để làm gì?', 'lesson_id': authorized_lesson.id},
        format='json',
    )

    assert response.status_code == 200
    assert response.data['answer'] == 'HTML tạo cấu trúc trang web.'
    assert response.data['citations'] == [citation]
    assert response.data['grounded'] is True
    assert response.data['retrieval']['status'] == 'ready'
    assert response.data['message']['content'] == response.data['answer']
    saved = ChatMessage.objects.get(role='assistant')
    assert saved.retrieval_metadata['retrieval']['selected_chunks'] == [
        {'chunk_id': 11, 'score': 0.8}
    ]
    assert mock_answer.call_args.kwargs['lesson'] == authorized_lesson
    assert mock_answer.call_args.kwargs['actor'] == student_user


@pytest.mark.django_db
@patch('apps.ai_assistant.views.answer_lesson_question')
def test_chat_rejects_unauthorized_lesson_before_rag(
    mock_answer, api_client, authorized_lesson
):
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
    mock_answer.assert_not_called()


@pytest.mark.django_db
@patch('apps.ai_assistant.views.answer_lesson_question')
def test_provider_failure_is_explicit_and_not_saved_as_assistant(
    mock_answer, authenticated_client, authorized_lesson, caplog
):
    mock_answer.side_effect = AIProviderError('private provider detail')

    response = authenticated_client.post(
        '/api/ai/chat/send_message/',
        {'message': 'Câu hỏi', 'lesson_id': authorized_lesson.id},
        format='json',
    )

    assert response.status_code == 502
    assert 'private provider detail' not in response.data['error']
    assert 'private provider detail' not in caplog.text
    assert ChatMessage.objects.filter(role='assistant').count() == 0


@pytest.mark.django_db
@patch('apps.ai_assistant.views.answer_lesson_question')
def test_retrieval_failure_is_explicit_and_not_saved_as_assistant(
    mock_answer, authenticated_client, authorized_lesson, caplog
):
    mock_answer.side_effect = LessonRetrievalError('private embedding detail')

    response = authenticated_client.post(
        '/api/ai/chat/send_message/',
        {'message': 'Câu hỏi', 'lesson_id': authorized_lesson.id},
        format='json',
    )

    assert response.status_code == 503
    assert 'private embedding detail' not in response.data['error']
    assert 'private embedding detail' not in caplog.text
    assert ChatMessage.objects.filter(role='assistant').count() == 0


@pytest.mark.django_db
@patch('apps.ai_assistant.views.answer_lesson_question')
def test_weak_evidence_fallback_is_saved_without_citations(
    mock_answer, authenticated_client, authorized_lesson
):
    mock_answer.return_value = GroundedAnswer(
        answer=WEAK_EVIDENCE_FALLBACK,
        citations=[],
        grounded=False,
        retrieval={
            'status': 'weak_evidence',
            'source_version': 1,
            'candidate_count': 3,
            'evidence_count': 0,
        },
        retrieval_metadata={
            'grounded': False,
            'retrieval': {
                'status': 'weak_evidence',
                'source_id': 3,
                'source_version': 1,
                'selected_chunks': [],
                'latency_ms': 2,
            },
        },
    )

    response = authenticated_client.post(
        '/api/ai/chat/send_message/',
        {'message': 'Thời tiết ngày mai?', 'lesson_id': authorized_lesson.id},
        format='json',
    )

    assert response.status_code == 200
    assert response.data['answer'] == WEAK_EVIDENCE_FALLBACK
    assert response.data['grounded'] is False
    assert response.data['citations'] == []
    assert response.data['retrieval']['status'] == 'weak_evidence'
    assert ChatMessage.objects.get(role='assistant').retrieval_metadata['grounded'] is False


@pytest.mark.django_db
@patch('apps.ai_assistant.views.answer_lesson_question')
def test_existing_session_cannot_change_lesson_scope(
    mock_answer, authenticated_client, authorized_lesson, student_user
):
    second_lesson = Lesson.objects.create(
        course=authorized_lesson.course,
        title='CSS',
        slug='css',
        content='CSS định dạng giao diện.',
    )
    session = ChatSession.objects.create(
        user=student_user,
        title='Phiên học HTML',
        context={'lesson_id': authorized_lesson.id},
    )

    response = authenticated_client.post(
        '/api/ai/chat/send_message/',
        {
            'message': 'Chuyển sang CSS',
            'session_id': session.id,
            'lesson_id': second_lesson.id,
        },
        format='json',
    )

    assert response.status_code == 400
    mock_answer.assert_not_called()


@pytest.mark.django_db
@patch('apps.ai_assistant.views.AIService.give_hint')
def test_enrolled_learner_can_request_scoped_exercise_hint(
    mock_hint, authenticated_client, authorized_lesson
):
    exercise = Exercise.objects.create(
        lesson=authorized_lesson,
        title='Tạo heading',
        description='Dùng HTML tạo một heading.',
        instructions='Không xem đáp án.',
        solution_code='<h1>Đáp án bí mật</h1>',
        test_cases=[{'hidden': True}],
    )
    mock_hint.return_value = 'Hãy nhớ lại thẻ heading cấp một.'

    response = authenticated_client.post(
        '/api/ai/chat/get_hint/',
        {'exercise_id': exercise.id, 'student_code': '<body></body>'},
        format='json',
    )

    assert response.status_code == 200
    assert response.data['hint'] == mock_hint.return_value
    sent_description = mock_hint.call_args.kwargs['exercise_description']
    assert exercise.title in sent_description
    assert exercise.description in sent_description
    assert exercise.solution_code not in sent_description
    assert 'hidden' not in sent_description


@pytest.mark.django_db
@patch('apps.ai_assistant.views.AIService.give_hint')
def test_non_enrolled_learner_is_denied_hint_before_provider(
    mock_hint, api_client, authorized_lesson
):
    exercise = Exercise.objects.create(
        lesson=authorized_lesson,
        title='Bài riêng',
        description='Không được lộ cho outsider.',
        instructions='Thực hiện bài.',
    )
    outsider = User.objects.create_user(
        email='hint-outsider@example.invalid',
        username='hint-outsider',
        full_name='Hint Outsider',
        password='LocalTestOnly-123!',
        is_verified=True,
    )
    api_client.force_authenticate(outsider)

    response = api_client.post(
        '/api/ai/chat/get_hint/',
        {'exercise_id': exercise.id},
        format='json',
    )

    assert response.status_code == 404
    mock_hint.assert_not_called()
