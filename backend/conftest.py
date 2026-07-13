import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    """API client fixture"""
    return APIClient()


@pytest.fixture
def student_user(db):
    """Create a student user"""
    return User.objects.create_user(
        email='student@test.com',
        username='student',
        full_name='Test Student',
        password='testpass123',
        role='student',
        is_verified=True,
    )


@pytest.fixture
def teacher_user(db):
    """Create a teacher user"""
    return User.objects.create_user(
        email='teacher@test.com',
        username='teacher',
        full_name='Test Teacher',
        password='testpass123',
        role='teacher',
        is_verified=True,
    )


@pytest.fixture
def authenticated_client(api_client, student_user):
    """Authenticated API client"""
    api_client.force_authenticate(user=student_user)
    return api_client
