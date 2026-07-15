import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    """Test User model"""
    
    def test_create_user(self):
        """Test creating a regular user"""
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            full_name='Test User',
            password='testpass123'
        )
        
        assert user.email == 'test@example.com'
        assert user.username == 'testuser'
        assert user.check_password('testpass123')
        assert user.role == 'student'  # default role
        assert user.is_active is True
        assert user.is_staff is False
    
    def test_create_superuser(self):
        """Test creating a superuser"""
        admin = User.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            full_name='Admin User',
            password='adminpass123'
        )
        
        assert admin.is_staff is True
        assert admin.is_superuser is True
        assert admin.role == 'admin'
    
    def test_user_profile_created(self):
        """Test that profile is automatically created"""
        user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            full_name='Test User',
            password='testpass123'
        )
        
        assert hasattr(user, 'profile')
        assert user.profile.user == user


@pytest.mark.django_db
class TestUserAPI:
    """Test User API endpoints"""
    
    def test_register_user(self, api_client):
        """Test user registration"""
        data = {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'full_name': 'New User',
            'role': 'teacher',
            'password': 'Newpass123!',
            'password_confirm': 'Newpass123!'
        }
        
        response = api_client.post('/api/auth/register/', data)
        
        assert response.status_code == 201
        assert 'user' in response.data
        assert 'tokens' not in response.data
        assert response.data['user']['email'] == data['email']
        assert response.data['user']['role'] == 'student'

    def test_user_cannot_change_role(self, authenticated_client, student_user):
        response = authenticated_client.patch(
            '/api/auth/users/update_profile/',
            {'role': 'admin', 'is_active': False, 'full_name': 'Updated Name'},
            format='json',
        )

        assert response.status_code == 200
        student_user.refresh_from_db()
        assert student_user.role == 'student'
        assert student_user.is_active is True
        assert student_user.full_name == 'Updated Name'

    def test_user_cannot_self_upgrade_to_teacher(self, authenticated_client):
        response = authenticated_client.post(
            '/api/auth/users/upgrade_to_teacher/',
            {'specialization': 'Web'},
            format='json',
        )

        assert response.status_code == 403
    
    def test_login_user(self, api_client, student_user):
        """Test user login"""
        data = {
            'email': 'student@test.com',
            'password': 'testpass123'
        }
        
        response = api_client.post('/api/auth/login/', data)
        
        assert response.status_code == 200
        assert 'tokens' in response.data
        assert 'access' in response.data['tokens']
        assert 'refresh' in response.data['tokens']
    
    def test_get_current_user(self, authenticated_client, student_user):
        """Test getting current user info"""
        response = authenticated_client.get('/api/auth/users/me/')
        
        assert response.status_code == 200
        assert response.data['email'] == student_user.email
