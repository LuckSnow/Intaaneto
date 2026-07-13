import pytest

from .models import Exercise


@pytest.mark.django_db
def test_student_exercise_response_hides_solution_and_hidden_tests(authenticated_client):
    exercise = Exercise.objects.create(
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
def test_student_cannot_create_exercise(authenticated_client):
    response = authenticated_client.post(
        '/api/exercises/',
        {'title': 'Unauthorized'},
        format='json',
    )

    assert response.status_code == 405
