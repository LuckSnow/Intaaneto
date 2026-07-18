import hashlib
import logging
import secrets
from datetime import timedelta

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.html import escape
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from config.throttling import ActionScopedThrottleMixin
from .models import User, TeacherApplication
from .permissions import IsRoleAdmin
from .role_services import (
    TeacherApplicationError,
    review_teacher_application,
    submit_teacher_application,
)
from .serializers import (
    UserSerializer,
    RegisterSerializer, LoginSerializer, ResendVerificationSerializer,
    TeacherApplicationReviewSerializer, TeacherApplicationSerializer,
)


logger = logging.getLogger(__name__)

GENERIC_RESEND_MESSAGE = (
    'Nếu tài khoản tồn tại và chưa được xác thực, email hướng dẫn sẽ được gửi.'
)


def _hash_verification_token(token):
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


class AuthViewSet(ActionScopedThrottleMixin, viewsets.GenericViewSet):
    """Authentication ViewSet"""
    
    permission_classes = [AllowAny]
    throttle_scope_by_action = {
        'register': 'auth_register',
        'login': 'auth_login',
        'teacher_login': 'auth_login',
        'google': 'auth_login',
        'verify_email': 'auth_verify',
        'resend_verification': 'auth_resend',
    }

    def _send_verification_email(self, user, request=None):
        """Send email verification link to user"""
        token = secrets.token_urlsafe(48)
        user.verification_token = _hash_verification_token(token)
        user.verification_token_created_at = timezone.now()
        user.save(update_fields=[
            'verification_token',
            'verification_token_created_at',
        ])

        if request is not None:
            verify_path = reverse('auth-verify-email-link', kwargs={'token': token})
            verify_url = request.build_absolute_uri(verify_path)
        else:
            verify_url = f"{settings.FRONTEND_URL}/verify-email/{token}"
        safe_full_name = escape(user.full_name)
        safe_verify_url = escape(verify_url)
        subject = 'Xác thực email - Intaaneto'
        html_message = f"""
        <div style="font-family: 'Inter', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #ea580c; font-size: 28px; margin: 0;">Intaaneto</h1>
                <p style="color: #666; margin-top: 5px;">Nền tảng học lập trình</p>
            </div>
            <div style="background: #fff7ed; border-radius: 16px; padding: 30px; border: 1px solid #fed7aa;">
                <h2 style="color: #1a1a1a; font-size: 22px; margin-top: 0;">Xin chào {safe_full_name}!</h2>
                <p style="color: #444; line-height: 1.6;">
                    Cảm ơn bạn đã đăng ký tài khoản trên Intaaneto. 
                    Vui lòng nhấn nút bên dưới để xác thực email của bạn:
                </p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{safe_verify_url}"
                       style="display: inline-block; padding: 14px 40px; background: linear-gradient(to right, #f97316, #ef4444); 
                              color: white; text-decoration: none; border-radius: 50px; font-weight: bold; font-size: 16px;">
                        Xác thực Email
                    </a>
                </div>
                <p style="color: #888; font-size: 13px; margin-bottom: 0;">
                    Nếu bạn không đăng ký tài khoản này, vui lòng bỏ qua email này.<br>
                    Link xác thực sẽ hết hạn sau {settings.EMAIL_VERIFICATION_TOKEN_TTL_HOURS} giờ.
                </p>
            </div>
        </div>
        """
        plain_message = (
            f"Xin chào {user.full_name}, vui lòng xác thực email: {verify_url}"
        )

        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            return True
        except Exception:
            logger.warning('Verification email delivery failed for user %s', user.pk)
            return False

    @staticmethod
    def _token_response(user):
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
        })

    @staticmethod
    def _authenticate(serializer):
        return authenticate(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
        )

    @staticmethod
    def _login_guard_response(user):
        if not user:
            return Response(
                {'error': 'Email hoặc mật khẩu không đúng'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not user.is_active:
            return Response(
                {'error': 'Tài khoản đã bị vô hiệu hóa'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        if not user.is_verified:
            return Response(
                {
                    'error': (
                        'Email chưa được xác thực. '
                        'Vui lòng kiểm tra hộp thư của bạn.'
                    ),
                    'need_verification': True,
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        return None

    @action(detail=False, methods=['post'])
    def register(self, request):
        """Register new user - requires email verification"""
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user = serializer.save()
        user.is_verified = False
        user.save(update_fields=['is_verified'])

        # Send verification email
        email_sent = self._send_verification_email(user, request=request)
        if not email_sent:
            return Response(
                {
                    'error': 'Không thể gửi email xác thực. Vui lòng thử lại sau hoặc liên hệ quản trị viên.',
                    'email_sent': False,
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response({
            'message': 'Đăng ký thành công! Vui lòng kiểm tra email để xác thực tài khoản.',
            'email_sent': email_sent,
            'user': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """Login user"""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = self._authenticate(serializer)
        guard_response = self._login_guard_response(user)
        if guard_response is not None:
            return guard_response
        return self._token_response(user)

    @action(detail=False, methods=['post'])
    def teacher_login(self, request):
        """Issue JWTs only to verified teacher or administrator accounts."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self._authenticate(serializer)
        guard_response = self._login_guard_response(user)
        if guard_response is not None:
            return guard_response
        if user.role not in {'teacher', 'admin'}:
            return Response(
                {'error': 'Tài khoản không có quyền truy cập cổng giáo viên'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return self._token_response(user)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """Logout user (blacklist refresh token)"""
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Successfully logged out'})
        except Exception:
            return Response(
                {'error': 'Invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def verify_email(self, request):
        """Verify user email with token"""
        token = request.data.get('token')
        if not isinstance(token, str) or not token or len(token) > 256:
            return Response({'error': 'Token không hợp lệ'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(
            verification_token=_hash_verification_token(token),
        ).first()
        if user is None:
            return Response({'error': 'Token không hợp lệ hoặc đã hết hạn'}, status=status.HTTP_400_BAD_REQUEST)

        expires_before = timezone.now() - timedelta(
            hours=settings.EMAIL_VERIFICATION_TOKEN_TTL_HOURS,
        )
        if (
            user.verification_token_created_at is None
            or user.verification_token_created_at <= expires_before
        ):
            user.verification_token = None
            user.verification_token_created_at = None
            user.save(update_fields=[
                'verification_token',
                'verification_token_created_at',
            ])
            return Response(
                {'error': 'Token không hợp lệ hoặc đã hết hạn'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_verified = True
        user.verification_token = None
        user.verification_token_created_at = None
        user.save(update_fields=[
            'is_verified',
            'verification_token',
            'verification_token_created_at',
        ])

        return Response({'message': 'Email đã được xác thực thành công!'})

    @action(detail=False, methods=['get'], url_path=r'verify-email/(?P<token>[^/.]+)')
    def verify_email_link(self, request, token=None):
        """Verify user email from a clickable email link."""
        if not token:
            return Response({'error': 'Token không hợp lệ'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(verification_token=token)
        except User.DoesNotExist:
            return Response({'error': 'Token không hợp lệ hoặc đã hết hạn'}, status=status.HTTP_400_BAD_REQUEST)

        user.is_verified = True
        user.verification_token = ''
        user.save(update_fields=['is_verified', 'verification_token'])

        return redirect(f"{settings.FRONTEND_URL}/login?verified=1")

    @action(detail=False, methods=['post'])
    def resend_verification(self, request):
        """Resend verification email"""
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email=serializer.validated_data['email']).first()
        if user is not None and not user.is_verified:
            self._send_verification_email(user, request=request)
        return Response({'message': GENERIC_RESEND_MESSAGE})

    @action(detail=False, methods=['post'])
    def google(self, request):
        """Authenticate with Firebase Google ID token"""
        token = request.data.get('id_token')
        if not token:
            return Response(
                {'error': 'id_token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Verify the Firebase ID token
            decoded_token = id_token.verify_firebase_token(
                token,
                google_requests.Request(),
                audience=settings.FIREBASE_PROJECT_ID,
            )
        except Exception:
            return Response(
                {'error': 'Google token không hợp lệ'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        email = decoded_token.get('email')
        name = decoded_token.get('name', '')
        picture = decoded_token.get('picture', '')

        if not email:
            return Response(
                {'error': 'Email not provided by Google'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get or create user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email.split('@')[0],
                'full_name': name or email.split('@')[0],
                'is_verified': True,
                'role': 'student',
                'google_avatar': picture,
            }
        )

        if created:
            # Set unusable password for social-auth users
            user.set_unusable_password()
            user.save()
        else:
            # Update Google avatar on every login
            if picture and user.google_avatar != picture:
                user.google_avatar = picture
                user.save(update_fields=['google_avatar'])

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'created': created,
        })


class UserViewSet(ActionScopedThrottleMixin, viewsets.GenericViewSet):
    """User ViewSet"""
    
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    throttle_scope_by_action = {
        ('teacher_application', 'post'): 'teacher_application',
    }

    def get_queryset(self):
        """Never expose the global user collection through this API."""
        return User.objects.filter(pk=self.request.user.pk)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        """Update current user profile"""
        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=False, methods=['get', 'post'])
    def teacher_application(self, request):
        """Return the actor's latest application or submit a new one."""
        if request.method == 'GET':
            application = TeacherApplication.objects.filter(
                applicant=request.user,
            ).first()
            return Response({
                'application': (
                    TeacherApplicationSerializer(application).data
                    if application else None
                ),
                'user': UserSerializer(request.user).data,
            })

        serializer = TeacherApplicationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            application = submit_teacher_application(
                applicant=request.user,
                validated_data=serializer.validated_data,
            )
        except TeacherApplicationError as exc:
            return Response(
                {'error': str(exc)},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(
            {
                'message': 'Hồ sơ đã được gửi và đang chờ quản trị viên duyệt.',
                'application': TeacherApplicationSerializer(application).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsRoleAdmin],
    )
    def review_teacher_application(self, request):
        """Approve or reject one pending application as an administrator."""
        serializer = TeacherApplicationReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            application = review_teacher_application(
                reviewer=request.user,
                **serializer.validated_data,
            )
        except TeacherApplicationError as exc:
            return Response(
                {'error': str(exc)},
                status=status.HTTP_409_CONFLICT,
            )
        return Response({
            'message': 'Hồ sơ giáo viên đã được xử lý.',
            'application': TeacherApplicationSerializer(application).data,
            'user': UserSerializer(application.applicant).data,
        })
