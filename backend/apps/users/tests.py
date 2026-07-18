import hashlib
from datetime import datetime, timedelta

import pytest
from django.core import mail
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils import timezone
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.tokens import AccessToken

from apps.users.models import TeacherApplication
from apps.users.views import AuthViewSet

User = get_user_model()


def verification_token_digest(token):
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


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
        created_user = User.objects.get(email=data['email'])
        assert len(created_user.verification_token) == 64
        assert created_user.verification_token_created_at is not None
        assert created_user.verification_token not in mail.outbox[0].body
        assert '/verify-email/' in mail.outbox[0].body
        assert mail.outbox[0].subject == 'Xác thực tài khoản Intaaneto'
        assert mail.outbox[0].from_email.startswith('Intaaneto <')
        html_body = mail.outbox[0].alternatives[0][0]
        assert '<html lang="vi">' in html_body
        assert 'Xác thực tài khoản' in html_body
        assert 'Liên kết chỉ dùng được một lần' in html_body
        assert '/verify-email/' in html_body

    def test_register_reports_email_delivery_failure_without_verifying_user(
        self, api_client, monkeypatch
    ):
        monkeypatch.setattr(
            AuthViewSet,
            '_send_verification_email',
            lambda self, user: False,
        )

        response = api_client.post('/api/auth/register/', {
            'email': 'delivery-failure@example.com',
            'username': 'delivery-failure',
            'full_name': 'Delivery Failure',
            'password': 'Newpass123!',
            'password_confirm': 'Newpass123!',
        })

        assert response.status_code == 201
        assert response.data['email_sent'] is False
        user = User.objects.get(email='delivery-failure@example.com')
        assert user.is_verified is False

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

    def test_teacher_application_does_not_self_upgrade(
        self, authenticated_client, student_user, django_capture_on_commit_callbacks
    ):
        admin = User.objects.create_user(
            email='application-admin@example.com',
            username='application-admin',
            full_name='Application Admin',
            password='Adminpass123!',
            role='admin',
            is_verified=True,
        )
        mail.outbox.clear()

        with django_capture_on_commit_callbacks(execute=True):
            response = authenticated_client.post(
                '/api/auth/users/teacher_application/',
                {
                    'specialization': 'Lập trình Python',
                    'years_of_experience': 3,
                    'reason': 'Tôi muốn chia sẻ kiến thức lập trình cho học viên.',
                    'status': 'approved',
                    'review_note': 'client-controlled',
                },
                format='json',
            )

        assert response.status_code == 201
        student_user.refresh_from_db()
        application = TeacherApplication.objects.get(applicant=student_user)
        assert student_user.role == 'student'
        assert application.status == 'pending'
        assert application.review_note == ''
        assert response.data['application']['status'] == 'pending'
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [admin.email]

    def test_duplicate_pending_teacher_application_is_rejected(
        self, authenticated_client, student_user
    ):
        data = {
            'specialization': 'Phát triển Web',
            'years_of_experience': 2,
            'reason': 'Tôi muốn xây dựng các khóa học web có bài tập thực hành.',
        }

        first_response = authenticated_client.post(
            '/api/auth/users/teacher_application/',
            data,
            format='json',
        )
        second_response = authenticated_client.post(
            '/api/auth/users/teacher_application/',
            data,
            format='json',
        )

        assert first_response.status_code == 201
        assert second_response.status_code == 409
        assert TeacherApplication.objects.filter(applicant=student_user).count() == 1

    def test_teacher_application_status_never_returns_another_users_record(
        self, authenticated_client
    ):
        other_student = User.objects.create_user(
            email='other-applicant@example.com',
            username='other-applicant',
            full_name='Other Applicant',
            password='Otherpass123!',
            role='student',
            is_verified=True,
        )
        TeacherApplication.objects.create(
            applicant=other_student,
            specialization='JavaScript',
            years_of_experience=2,
            reason='Tôi muốn hướng dẫn JavaScript cho các học viên mới.',
        )

        response = authenticated_client.get(
            '/api/auth/users/teacher_application/',
        )

        assert response.status_code == 200
        assert response.data['application'] is None
        assert other_student.email not in str(response.data)

    def test_teacher_cannot_submit_teacher_application(
        self, api_client, teacher_user
    ):
        api_client.force_authenticate(user=teacher_user)

        response = api_client.post(
            '/api/auth/users/teacher_application/',
            {
                'specialization': 'Python',
                'years_of_experience': 4,
                'reason': 'Tài khoản này đã là giáo viên nên không cần hồ sơ.',
            },
            format='json',
        )

        assert response.status_code == 409
        assert TeacherApplication.objects.count() == 0

    def test_student_cannot_review_teacher_application(
        self, authenticated_client, student_user
    ):
        application = TeacherApplication.objects.create(
            applicant=student_user,
            specialization='Python',
            years_of_experience=1,
            reason='Tôi muốn hướng dẫn học viên học Python từ căn bản.',
        )

        response = authenticated_client.post(
            '/api/auth/users/review_teacher_application/',
            {
                'application_id': application.id,
                'decision': 'approved',
            },
            format='json',
        )

        assert response.status_code == 403
        student_user.refresh_from_db()
        assert student_user.role == 'student'

    def test_admin_approval_changes_role_and_records_reviewer(
        self, api_client, student_user, django_capture_on_commit_callbacks
    ):
        admin = User.objects.create_user(
            email='review-admin@example.com',
            username='review-admin',
            full_name='Review Admin',
            password='Adminpass123!',
            role='admin',
            is_verified=True,
        )
        application = TeacherApplication.objects.create(
            applicant=student_user,
            specialization='Khoa học dữ liệu',
            years_of_experience=5,
            reason='Tôi muốn xây dựng khóa học dữ liệu có ví dụ thực tế.',
        )
        api_client.force_authenticate(user=admin)
        mail.outbox.clear()

        with django_capture_on_commit_callbacks(execute=True):
            response = api_client.post(
                '/api/auth/users/review_teacher_application/',
                {
                    'application_id': application.id,
                    'decision': 'approved',
                    'review_note': 'Hồ sơ đáp ứng yêu cầu ban đầu.',
                },
                format='json',
            )

        assert response.status_code == 200
        student_user.refresh_from_db()
        student_user.profile.refresh_from_db()
        application.refresh_from_db()
        assert student_user.role == 'teacher'
        assert student_user.profile.specialization == 'Khoa học dữ liệu'
        assert student_user.profile.years_of_experience == 5
        assert application.status == 'approved'
        assert application.reviewed_by == admin
        assert application.reviewed_at is not None
        assert mail.outbox[0].to == [student_user.email]

    def test_rejection_requires_admin_note(self, api_client, student_user):
        admin = User.objects.create_user(
            email='reject-admin@example.com',
            username='reject-admin',
            full_name='Reject Admin',
            password='Adminpass123!',
            role='admin',
            is_verified=True,
        )
        application = TeacherApplication.objects.create(
            applicant=student_user,
            specialization='Thiết kế Web',
            years_of_experience=1,
            reason='Tôi muốn chia sẻ kiến thức thiết kế web cho người mới.',
        )
        api_client.force_authenticate(user=admin)

        response = api_client.post(
            '/api/auth/users/review_teacher_application/',
            {
                'application_id': application.id,
                'decision': 'rejected',
                'review_note': 'Thiếu',
            },
            format='json',
        )

        assert response.status_code == 400
        application.refresh_from_db()
        assert application.status == 'pending'
    
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

    def test_teacher_login_returns_server_owned_role(self, api_client, teacher_user):
        response = api_client.post('/api/auth/login/', {
            'email': teacher_user.email,
            'password': 'testpass123',
        })

        assert response.status_code == 200
        assert response.data['user']['role'] == 'teacher'

    def test_teacher_portal_login_accepts_teacher(self, api_client, teacher_user):
        response = api_client.post('/api/auth/teacher_login/', {
            'email': teacher_user.email,
            'password': 'testpass123',
        })

        assert response.status_code == 200
        assert response.data['user']['role'] == 'teacher'
        assert response.data['tokens']['access']

    def test_teacher_portal_login_rejects_student_without_tokens(
        self, api_client, student_user
    ):
        response = api_client.post('/api/auth/teacher_login/', {
            'email': student_user.email,
            'password': 'testpass123',
        })

        assert response.status_code == 403
        assert 'tokens' not in response.data

    def test_teacher_portal_requires_verified_email(self, api_client, teacher_user):
        teacher_user.is_verified = False
        teacher_user.save(update_fields=['is_verified'])

        response = api_client.post('/api/auth/teacher_login/', {
            'email': teacher_user.email,
            'password': 'testpass123',
        })

        assert response.status_code == 403
        assert response.data['need_verification'] is True
        assert 'email' not in response.data
        assert 'tokens' not in response.data

    def test_verification_token_expires_after_configured_ttl(
        self, api_client, student_user, settings
    ):
        settings.EMAIL_VERIFICATION_TOKEN_TTL_HOURS = 24
        student_user.is_verified = False
        student_user.verification_token = verification_token_digest('expired-token')
        student_user.verification_token_created_at = (
            timezone.now() - timedelta(hours=25)
        )
        student_user.save(update_fields=[
            'is_verified',
            'verification_token',
            'verification_token_created_at',
        ])

        response = api_client.post('/api/auth/verify_email/', {
            'token': 'expired-token',
        })

        assert response.status_code == 400
        student_user.refresh_from_db()
        assert student_user.is_verified is False
        assert student_user.verification_token is None
        assert student_user.verification_token_created_at is None

    def test_valid_verification_token_is_single_use(self, api_client, student_user):
        student_user.is_verified = False
        student_user.verification_token = verification_token_digest('valid-token')
        student_user.verification_token_created_at = timezone.now()
        student_user.save(update_fields=[
            'is_verified',
            'verification_token',
            'verification_token_created_at',
        ])

        first_response = api_client.post('/api/auth/verify_email/', {
            'token': 'valid-token',
        })
        replay_response = api_client.post('/api/auth/verify_email/', {
            'token': 'valid-token',
        })

        assert first_response.status_code == 200
        assert replay_response.status_code == 400
        student_user.refresh_from_db()
        assert student_user.is_verified is True

    def test_resend_verification_does_not_disclose_account_state(
        self, api_client, student_user, teacher_user
    ):
        student_user.is_verified = False
        student_user.save(update_fields=['is_verified'])
        mail.outbox.clear()

        unverified_response = api_client.post('/api/auth/resend_verification/', {
            'email': student_user.email,
        })
        verified_response = api_client.post('/api/auth/resend_verification/', {
            'email': teacher_user.email,
        })
        missing_response = api_client.post('/api/auth/resend_verification/', {
            'email': 'missing@example.com',
        })

        assert unverified_response.status_code == 200
        assert verified_response.status_code == 200
        assert missing_response.status_code == 200
        assert unverified_response.data == verified_response.data
        assert verified_response.data == missing_response.data
        assert len(mail.outbox) == 1

    def test_password_reset_request_is_generic_and_sends_only_for_account(
        self, api_client, teacher_user
    ):
        mail.outbox.clear()

        existing_response = api_client.post(
            '/api/auth/password_reset_request/',
            {'email': teacher_user.email},
            format='json',
        )
        missing_response = api_client.post(
            '/api/auth/password_reset_request/',
            {'email': 'missing-reset@example.com'},
            format='json',
        )

        assert existing_response.status_code == 200
        assert missing_response.status_code == 200
        assert existing_response.data == missing_response.data
        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == 'Đặt lại mật khẩu Intaaneto'
        assert '/reset-password/' in mail.outbox[0].body
        assert teacher_user.email not in str(existing_response.data)

    def test_password_reset_delivery_failure_remains_generic(
        self, api_client, teacher_user, monkeypatch
    ):
        monkeypatch.setattr(
            AuthViewSet,
            '_send_password_reset_email',
            lambda self, user: False,
        )

        response = api_client.post(
            '/api/auth/password_reset_request/',
            {'email': teacher_user.email},
            format='json',
        )

        assert response.status_code == 200
        assert 'tồn tại' in response.data['message']

    def test_password_reset_changes_password_invalidates_token_and_old_jwt(
        self, api_client, teacher_user
    ):
        uid = urlsafe_base64_encode(force_bytes(teacher_user.pk))
        reset_token = default_token_generator.make_token(teacher_user)
        old_access = str(AccessToken.for_user(teacher_user))
        payload = {
            'uid': uid,
            'token': reset_token,
            'password': 'Freshpass123!',
            'password_confirm': 'Freshpass123!',
        }

        response = api_client.post(
            '/api/auth/password_reset_confirm/', payload, format='json'
        )
        replay_response = api_client.post(
            '/api/auth/password_reset_confirm/', payload, format='json'
        )

        assert response.status_code == 200
        assert response.data['login_path'] == '/teacher/login'
        assert replay_response.status_code == 400
        teacher_user.refresh_from_db()
        assert teacher_user.check_password('Freshpass123!')
        assert teacher_user.role == 'teacher'
        assert teacher_user.is_verified is True

        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {old_access}')
        old_session_response = api_client.get('/api/auth/users/me/')
        assert old_session_response.status_code == 401

    def test_password_reset_rejects_invalid_token_and_weak_password(
        self, api_client, teacher_user
    ):
        uid = urlsafe_base64_encode(force_bytes(teacher_user.pk))

        invalid_response = api_client.post(
            '/api/auth/password_reset_confirm/',
            {
                'uid': uid,
                'token': 'invalid-token',
                'password': 'Freshpass123!',
                'password_confirm': 'Freshpass123!',
            },
            format='json',
        )
        weak_response = api_client.post(
            '/api/auth/password_reset_confirm/',
            {
                'uid': uid,
                'token': default_token_generator.make_token(teacher_user),
                'password': 'weakpass',
                'password_confirm': 'weakpass',
            },
            format='json',
        )

        assert invalid_response.status_code == 400
        assert weak_response.status_code == 400
        teacher_user.refresh_from_db()
        assert teacher_user.check_password('testpass123')

    def test_password_reset_token_expires(
        self, api_client, teacher_user, settings, monkeypatch
    ):
        settings.PASSWORD_RESET_TIMEOUT = 1
        uid = urlsafe_base64_encode(force_bytes(teacher_user.pk))
        reset_token = default_token_generator.make_token(teacher_user)
        monkeypatch.setattr(
            default_token_generator,
            '_now',
            lambda: datetime.now() + timedelta(seconds=2),
        )

        response = api_client.post(
            '/api/auth/password_reset_confirm/',
            {
                'uid': uid,
                'token': reset_token,
                'password': 'Freshpass123!',
                'password_confirm': 'Freshpass123!',
            },
            format='json',
        )

        assert response.status_code == 400
        teacher_user.refresh_from_db()
        assert teacher_user.check_password('testpass123')

    def test_logout_blacklists_refresh_token(self, api_client, student_user):
        login_response = api_client.post('/api/auth/login/', {
            'email': student_user.email,
            'password': 'testpass123',
        })
        api_client.force_authenticate(student_user)

        response = api_client.post('/api/auth/logout/', {
            'refresh_token': login_response.data['tokens']['refresh'],
        })

        assert response.status_code == 200
        assert BlacklistedToken.objects.count() == 1

    def test_refresh_rotates_token_and_blacklists_previous_one(self, api_client, student_user):
        login_response = api_client.post('/api/auth/login/', {
            'email': student_user.email,
            'password': 'testpass123',
        })
        original_refresh = login_response.data['tokens']['refresh']

        response = api_client.post('/api/auth/token/refresh/', {
            'refresh': original_refresh,
        })

        assert response.status_code == 200
        assert response.data['access']
        assert response.data['refresh']
        assert response.data['refresh'] != original_refresh
        assert BlacklistedToken.objects.count() == 1

    def test_logout_requires_refresh_token(self, authenticated_client):
        response = authenticated_client.post('/api/auth/logout/', {})

        assert response.status_code == 400
    
    def test_get_current_user(self, authenticated_client, student_user):
        """Test getting current user info"""
        response = authenticated_client.get('/api/auth/users/me/')
        
        assert response.status_code == 200
        assert response.data['email'] == student_user.email
