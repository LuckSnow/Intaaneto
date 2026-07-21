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
from django.contrib.auth import password_validation
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.core.exceptions import ValidationError as DjangoValidationError
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.html import escape
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
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
    PasswordResetConfirmSerializer, PasswordResetRequestSerializer,
    TeacherApplicationReviewSerializer, TeacherApplicationSerializer,
)


logger = logging.getLogger(__name__)

GENERIC_RESEND_MESSAGE = (
    'Nếu tài khoản tồn tại và chưa được xác thực, email hướng dẫn sẽ được gửi.'
)
GENERIC_PASSWORD_RESET_MESSAGE = (
    'Nếu tài khoản tồn tại và có thể đặt lại mật khẩu, email hướng dẫn sẽ được gửi.'
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
        'password_reset_request': 'auth_password_reset_request',
        'password_reset_confirm': 'auth_password_reset_confirm',
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
        subject = 'Xác thực tài khoản Intaaneto'
        html_message = f"""
        <!doctype html>
        <html lang="vi">
          <body style="margin:0; padding:0; background:#f8fafc; color:#0f172a; font-family:Arial, Helvetica, sans-serif;">
            <div style="display:none; max-height:0; overflow:hidden; opacity:0; color:transparent;">
              Hoàn tất xác thực để bắt đầu học trên Intaaneto.
            </div>
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#f8fafc;">
              <tr>
                <td align="center" style="padding:32px 16px;">
                  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width:560px;">
                    <tr>
                      <td style="padding:0 0 20px;">
                        <table role="presentation" cellspacing="0" cellpadding="0" border="0">
                          <tr>
                            <td align="center" valign="middle" width="40" height="40" style="width:40px; height:40px; border-radius:10px; background:#c2410c; color:#ffffff; font-size:22px; font-weight:700;">I</td>
                            <td style="padding-left:12px;">
                              <div style="font-size:20px; line-height:24px; font-weight:700; color:#0f172a;">Intaaneto</div>
                              <div style="font-size:13px; line-height:18px; color:#64748b;">Học từ nội dung đáng tin cậy</div>
                            </td>
                          </tr>
                        </table>
                      </td>
                    </tr>
                    <tr>
                      <td style="background:#ffffff; border:1px solid #e2e8f0; border-radius:16px; padding:36px 32px;">
                        <div style="font-size:12px; line-height:18px; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; color:#c2410c;">Xác thực tài khoản</div>
                        <h1 style="margin:10px 0 16px; font-size:26px; line-height:34px; color:#0f172a;">Chào {safe_full_name},</h1>
                        <p style="margin:0; font-size:16px; line-height:26px; color:#475569;">
                          Cảm ơn bạn đã đăng ký Intaaneto. Hãy xác thực địa chỉ email để bảo vệ tài khoản và bắt đầu học.
                        </p>
                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin:28px 0;">
                          <tr>
                            <td align="center" bgcolor="#c2410c" style="border-radius:10px;">
                              <a href="{safe_verify_url}" style="display:inline-block; padding:14px 24px; color:#ffffff; font-size:16px; line-height:20px; font-weight:700; text-decoration:none;">Xác thực email</a>
                            </td>
                          </tr>
                        </table>
                        <div style="padding:16px; border-radius:10px; background:#fff7ed; border:1px solid #fed7aa;">
                          <p style="margin:0; font-size:14px; line-height:22px; color:#7c2d12;">
                            Liên kết chỉ dùng được một lần và hết hạn sau <strong>{settings.EMAIL_VERIFICATION_TOKEN_TTL_HOURS} giờ</strong>.
                          </p>
                        </div>
                        <p style="margin:24px 0 8px; font-size:13px; line-height:20px; color:#64748b;">Nếu nút không hoạt động, sao chép liên kết này vào trình duyệt:</p>
                        <p style="margin:0; font-size:12px; line-height:18px; word-break:break-all;">
                          <a href="{safe_verify_url}" style="color:#c2410c; text-decoration:underline;">{safe_verify_url}</a>
                        </p>
                      </td>
                    </tr>
                    <tr>
                      <td style="padding:20px 4px 0; font-size:12px; line-height:18px; color:#64748b;">
                        Bạn nhận được email này vì địa chỉ của bạn vừa được dùng để đăng ký Intaaneto. Nếu đó không phải bạn, bạn có thể bỏ qua email này.
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>
          </body>
        </html>
        """
        plain_message = (
            f"Chào {user.full_name},\n\n"
            "Cảm ơn bạn đã đăng ký Intaaneto. Xác thực email tại:\n"
            f"{verify_url}\n\n"
            "Liên kết chỉ dùng được một lần và hết hạn sau "
            f"{settings.EMAIL_VERIFICATION_TOKEN_TTL_HOURS} giờ.\n\n"
            "Nếu bạn không đăng ký tài khoản này, hãy bỏ qua email."
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

    def _send_password_reset_email(self, user):
        """Send a bounded one-time password reset link without logging it."""
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}"
        safe_full_name = escape(user.full_name)
        safe_reset_url = escape(reset_url)
        timeout_minutes = max(1, settings.PASSWORD_RESET_TIMEOUT // 60)
        subject = 'Đặt lại mật khẩu Intaaneto'
        html_message = f"""
        <!doctype html>
        <html lang="vi">
          <body style="margin:0; padding:0; background:#f8fafc; color:#0f172a; font-family:Arial, Helvetica, sans-serif;">
            <div style="display:none; max-height:0; overflow:hidden; opacity:0; color:transparent;">
              Dùng liên kết bảo mật để đặt lại mật khẩu Intaaneto.
            </div>
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background:#f8fafc;">
              <tr>
                <td align="center" style="padding:32px 16px;">
                  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width:560px;">
                    <tr>
                      <td style="padding:0 0 20px; font-size:20px; line-height:26px; font-weight:700; color:#0f172a;">
                        <span style="display:inline-block; width:40px; height:40px; margin-right:10px; border-radius:10px; background:#c2410c; color:#ffffff; line-height:40px; text-align:center;">I</span>
                        Intaaneto
                      </td>
                    </tr>
                    <tr>
                      <td style="background:#ffffff; border:1px solid #e2e8f0; border-radius:16px; padding:36px 32px;">
                        <div style="font-size:12px; line-height:18px; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; color:#c2410c;">Bảo mật tài khoản</div>
                        <h1 style="margin:10px 0 16px; font-size:26px; line-height:34px; color:#0f172a;">Chào {safe_full_name},</h1>
                        <p style="margin:0; font-size:16px; line-height:26px; color:#475569;">
                          Chúng tôi nhận được yêu cầu đặt lại mật khẩu cho tài khoản Intaaneto của bạn.
                        </p>
                        <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin:28px 0;">
                          <tr>
                            <td align="center" bgcolor="#c2410c" style="border-radius:10px;">
                              <a href="{safe_reset_url}" style="display:inline-block; padding:14px 24px; color:#ffffff; font-size:16px; line-height:20px; font-weight:700; text-decoration:none;">Đặt lại mật khẩu</a>
                            </td>
                          </tr>
                        </table>
                        <div style="padding:16px; border-radius:10px; background:#fff7ed; border:1px solid #fed7aa;">
                          <p style="margin:0; font-size:14px; line-height:22px; color:#7c2d12;">
                            Liên kết hết hạn sau <strong>{timeout_minutes} phút</strong> và mất hiệu lực ngay khi mật khẩu được đổi.
                          </p>
                        </div>
                        <p style="margin:24px 0 8px; font-size:13px; line-height:20px; color:#64748b;">Nếu nút không hoạt động, sao chép liên kết này vào trình duyệt:</p>
                        <p style="margin:0; font-size:12px; line-height:18px; word-break:break-all;">
                          <a href="{safe_reset_url}" style="color:#c2410c; text-decoration:underline;">{safe_reset_url}</a>
                        </p>
                      </td>
                    </tr>
                    <tr>
                      <td style="padding:20px 4px 0; font-size:12px; line-height:18px; color:#64748b;">
                        Nếu bạn không yêu cầu đổi mật khẩu, hãy bỏ qua email này. Mật khẩu hiện tại vẫn được giữ nguyên.
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>
          </body>
        </html>
        """
        plain_message = (
            f"Chào {user.full_name},\n\n"
            "Đặt lại mật khẩu Intaaneto tại:\n"
            f"{reset_url}\n\n"
            f"Liên kết hết hạn sau {timeout_minutes} phút và mất hiệu lực sau khi dùng.\n\n"
            "Nếu bạn không yêu cầu đổi mật khẩu, hãy bỏ qua email này."
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
            logger.warning('Password reset email delivery failed for user %s', user.pk)
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
    def password_reset_request(self, request):
        """Send a reset link while keeping account existence private."""
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(
            email=serializer.validated_data['email'],
            is_active=True,
        ).first()
        if user is not None and user.has_usable_password():
            self._send_password_reset_email(user)
        return Response({'message': GENERIC_PASSWORD_RESET_MESSAGE})

    @action(detail=False, methods=['post'])
    def password_reset_confirm(self, request):
        """Atomically consume a reset token and replace the password."""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user_id = int(force_str(urlsafe_base64_decode(
                serializer.validated_data['uid'],
            )))
        except (TypeError, ValueError, OverflowError, UnicodeDecodeError):
            return Response(
                {'error': 'Liên kết đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            user = User.objects.select_for_update().filter(
                pk=user_id,
                is_active=True,
            ).first()
            if user is None or not default_token_generator.check_token(
                user,
                serializer.validated_data['token'],
            ):
                return Response(
                    {'error': 'Liên kết đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                password_validation.validate_password(
                    serializer.validated_data['password'],
                    user=user,
                )
            except DjangoValidationError as exc:
                return Response(
                    {'password': exc.messages},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.set_password(serializer.validated_data['password'])
            user.save(update_fields=['password'])

        login_path = (
            '/teacher/login'
            if user.role in {'teacher', 'admin'}
            else '/login'
        )
        return Response({
            'message': 'Mật khẩu đã được đặt lại thành công.',
            'login_path': login_path,
        })

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
