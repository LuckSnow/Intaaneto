from unittest.mock import patch
from decimal import Decimal

import pytest

from apps.ai_assistant.models import KnowledgeSource

from .models import Course, Enrollment, LessonProgress
from .test_pdf_ingestion import FakeEmbeddingProvider, upload_payload


@pytest.mark.django_db
def test_teacher_pdf_assessment_to_learner_progression_journey(
    api_client,
    teacher_user,
    student_user,
):
    api_client.force_authenticate(teacher_user)
    created_course = api_client.post(
        '/api/courses/',
        {
            'title': 'Hành trình RAG có đánh giá',
            'description': 'Course integration test',
            'difficulty': 'beginner',
            'is_published': False,
        },
        format='json',
    )
    assert created_course.status_code == 201
    course = Course.objects.get(pk=created_course.data['id'])

    with patch(
        'apps.ai_assistant.rag_services.FastEmbedEmbeddingProvider',
        return_value=FakeEmbeddingProvider(),
    ):
        uploaded = api_client.post(
            '/api/courses/lessons/upload/',
            upload_payload(course),
            format='multipart',
        )
    assert uploaded.status_code == 201
    lesson_id = uploaded.data['lesson']['id']
    assert KnowledgeSource.objects.filter(
        lesson_id=lesson_id,
        is_active=True,
        status='ready',
    ).exists()

    created_assessment = api_client.post(
        '/api/exercises/assessments/',
        {
            'lesson': lesson_id,
            'title': 'Kiểm tra retrieval',
            'instructions': 'Chọn đáp án đúng.',
            'pass_threshold': 70,
            'is_published': True,
            'questions': [
                {
                    'prompt': 'RAG dùng bước nào để tìm bằng chứng?',
                    'choices': ['Retrieval', 'Rendering'],
                    'correct_choice': 0,
                    'learning_objective': 'Nhận biết retrieval',
                    'explanation': 'Retrieval tìm bằng chứng liên quan.',
                    'order': 1,
                }
            ],
        },
        format='json',
    )
    assert created_assessment.status_code == 201
    assessment_id = created_assessment.data['id']
    question_id = created_assessment.data['questions'][0]['id']

    published = api_client.patch(
        f'/api/courses/{course.id}/',
        {'is_published': True},
        format='json',
    )
    assert published.status_code == 200

    api_client.force_authenticate(student_user)
    enrolled = api_client.post(f'/api/courses/{course.id}/enroll/')
    assert enrolled.status_code == 201

    learner_assessment = api_client.get(
        f'/api/exercises/assessments/?lesson={lesson_id}'
    )
    assert learner_assessment.status_code == 200
    learner_question = learner_assessment.data['results'][0]['questions'][0]
    assert learner_assessment.data['results'][0]['id'] == assessment_id
    assert 'correct_choice' not in learner_question
    assert 'explanation' not in learner_question

    submitted = api_client.post(
        f'/api/exercises/assessments/{assessment_id}/submit/',
        {
            'answers': [
                {'question_id': question_id, 'selected_choice': 0},
            ],
        },
        format='json',
    )
    assert submitted.status_code == 201
    assert submitted.data['passed'] is True
    assert submitted.data['progress_percentage'] == Decimal('100.00')
    assert submitted.data['mastery_percentage'] == Decimal('100.00')
    assert submitted.data['next_lesson'] is None

    enrollment = Enrollment.objects.get(user=student_user, course=course)
    assert enrollment.progress_percentage == 100
    assert enrollment.mastery_percentage == 100
    assert LessonProgress.objects.get(
        user=student_user,
        lesson_id=lesson_id,
    ).is_completed
