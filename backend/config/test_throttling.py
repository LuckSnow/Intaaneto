import pytest
from django.conf import settings
from django.core.cache import cache
from django.test import override_settings
from rest_framework.throttling import ScopedRateThrottle


THROTTLE_TEST_SETTINGS = {
    **settings.REST_FRAMEWORK,
    'DEFAULT_THROTTLE_RATES': {
        **settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'],
        'auth_login': '1/minute',
        'teacher_application': '1/day',
        'lesson_upload': '1/hour',
        'ai_chat': '1/minute',
        'assessment_submit': '1/hour',
        'assessment_dialogue': '1/hour',
    },
}


@pytest.fixture(autouse=True)
def configure_test_throttle_rates(monkeypatch):
    cache.clear()
    monkeypatch.setattr(
        ScopedRateThrottle,
        'THROTTLE_RATES',
        THROTTLE_TEST_SETTINGS['DEFAULT_THROTTLE_RATES'],
    )
    yield
    cache.clear()


@pytest.mark.django_db
@override_settings(REST_FRAMEWORK=THROTTLE_TEST_SETTINGS)
def test_anonymous_login_is_throttled_by_client(api_client):
    payload = {'email': 'missing@example.com', 'password': 'Wrongpass123!'}

    first = api_client.post('/api/auth/login/', payload, format='json')
    second = api_client.post('/api/auth/login/', payload, format='json')

    assert first.status_code == 401
    assert second.status_code == 429
    assert 'password' not in str(second.data).lower()


@pytest.mark.django_db
@override_settings(REST_FRAMEWORK=THROTTLE_TEST_SETTINGS)
def test_teacher_application_get_is_not_counted_as_submission(
    authenticated_client,
):
    first = authenticated_client.get('/api/auth/users/teacher_application/')
    second = authenticated_client.get('/api/auth/users/teacher_application/')

    assert first.status_code == 200
    assert second.status_code == 200


@pytest.mark.django_db
@override_settings(REST_FRAMEWORK=THROTTLE_TEST_SETTINGS)
def test_pdf_upload_is_throttled_before_repeated_processing(api_client, teacher_user):
    api_client.force_authenticate(teacher_user)

    first = api_client.post('/api/courses/lessons/upload/', {}, format='json')
    second = api_client.post('/api/courses/lessons/upload/', {}, format='json')

    assert first.status_code == 400
    assert second.status_code == 429


@pytest.mark.django_db
@override_settings(REST_FRAMEWORK=THROTTLE_TEST_SETTINGS)
def test_ai_chat_is_throttled_per_authenticated_user(authenticated_client):
    first = authenticated_client.post(
        '/api/ai/chat/send_message/', {}, format='json'
    )
    second = authenticated_client.post(
        '/api/ai/chat/send_message/', {}, format='json'
    )

    assert first.status_code == 400
    assert second.status_code == 429


@pytest.mark.django_db
@override_settings(REST_FRAMEWORK=THROTTLE_TEST_SETTINGS)
def test_assessment_submit_is_throttled_per_authenticated_user(
    authenticated_client,
):
    url = '/api/exercises/assessments/999999/submit/'

    first = authenticated_client.post(url, {'answers': []}, format='json')
    second = authenticated_client.post(url, {'answers': []}, format='json')

    assert first.status_code == 404
    assert second.status_code == 429


@pytest.mark.django_db
@override_settings(REST_FRAMEWORK=THROTTLE_TEST_SETTINGS)
def test_dialogue_assessment_is_throttled_per_authenticated_user(
    authenticated_client,
):
    url = '/api/exercises/assessments/999999/dialogue-check/'

    first = authenticated_client.post(url, {}, format='json')
    second = authenticated_client.post(url, {}, format='json')

    assert first.status_code == 404
    assert second.status_code == 429
