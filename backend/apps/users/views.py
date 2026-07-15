from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from .models import User, Profile
from .serializers import (
    UserSerializer, ProfileSerializer,
    RegisterSerializer, LoginSerializer
)


class AuthViewSet(viewsets.GenericViewSet):
    """Authentication ViewSet"""
    
    permission_classes = [AllowAny]

    def _send_verification_email(self, user):
        """Send email verification link to user"""
        token = get_random_string(64)
        user.verification_token = token
        user.save(update_fields=['verification_token'])

        verify_url = f"{settings.FRONTEND_URL}/verify-email/{token}"
        subject = 'Xác thực email - Intaaneto'
        html_message = f"""
        <div style="font-family: 'Inter', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 40px 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #ea580c; font-size: 28px; margin: 0;">Intaaneto</h1>
                <p style="color: #666; margin-top: 5px;">Nền tảng học lập trình</p>
            </div>
            <div style="background: #fff7ed; border-radius: 16px; padding: 30px; border: 1px solid #fed7aa;">
                <h2 style="color: #1a1a1a; font-size: 22px; margin-top: 0;">Xin chào {user.full_name}! 👋</h2>
                <p style="color: #444; line-height: 1.6;">
                    Cảm ơn bạn đã đăng ký tài khoản trên Intaaneto. 
                    Vui lòng nhấn nút bên dưới để xác thực email của bạn:
                </p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verify_url}" 
                       style="display: inline-block; padding: 14px 40px; background: linear-gradient(to right, #f97316, #ef4444); 
                              color: white; text-decoration: none; border-radius: 50px; font-weight: bold; font-size: 16px;">
                        Xác thực Email
                    </a>
                </div>
                <p style="color: #888; font-size: 13px; margin-bottom: 0;">
                    Nếu bạn không đăng ký tài khoản này, vui lòng bỏ qua email này.<br>
                    Link xác thực sẽ hết hạn sau 24 giờ.
                </p>
            </div>
        </div>
        """
        plain_message = f"Xin chào {user.full_name}, vui lòng xác thực email: {verify_url}"

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
        except Exception as e:
            print(f"Email send error: {e}")
            return False

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
        email_sent = self._send_verification_email(user)

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
        
        user = authenticate(
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password']
        )
        
        if not user:
            return Response(
                {'error': 'Email hoặc mật khẩu không đúng'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            return Response(
                {'error': 'Tài khoản đã bị vô hiệu hóa'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_verified:
            return Response(
                {'error': 'Email chưa được xác thực. Vui lòng kiểm tra hộp thư của bạn.', 'need_verification': True, 'email': user.email},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """Logout user (blacklist refresh token)"""
        try:
            refresh_token = request.data.get('refresh_token')
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
        if not token:
            return Response({'error': 'Token không hợp lệ'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(verification_token=token)
        except User.DoesNotExist:
            return Response({'error': 'Token không hợp lệ hoặc đã hết hạn'}, status=status.HTTP_400_BAD_REQUEST)

        user.is_verified = True
        user.verification_token = ''
        user.save(update_fields=['is_verified', 'verification_token'])

        return Response({'message': 'Email đã được xác thực thành công!'})

    @action(detail=False, methods=['post'])
    def resend_verification(self, request):
        """Resend verification email"""
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email là bắt buộc'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Không tìm thấy tài khoản với email này'}, status=status.HTTP_404_NOT_FOUND)

        if user.is_verified:
            return Response({'error': 'Email đã được xác thực rồi'}, status=status.HTTP_400_BAD_REQUEST)

        email_sent = self._send_verification_email(user)
        return Response({
            'message': 'Email xác thực đã được gửi lại!',
            'email_sent': email_sent,
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
        except Exception as e:
            return Response(
                {'error': f'Invalid token: {str(e)}'},
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


class UserViewSet(viewsets.GenericViewSet):
    """User ViewSet"""
    
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

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

    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def upgrade_to_teacher(self, request):
        """Upgrade current user from student to teacher"""
        user = request.user
        if user.role == 'teacher':
            return Response({'error': 'Bạn đã là giáo viên rồi'}, status=status.HTTP_400_BAD_REQUEST)
        if user.role == 'admin':
            return Response({'error': 'Admin không thể chuyển vai trò'}, status=status.HTTP_400_BAD_REQUEST)

        specialization = request.data.get('specialization', '')
        years_of_experience = request.data.get('years_of_experience', 0)
        reason = request.data.get('reason', '')

        if not specialization:
            return Response({'error': 'Vui lòng nhập chuyên môn của bạn'}, status=status.HTTP_400_BAD_REQUEST)

        user.role = 'teacher'
        user.save(update_fields=['role'])

        # Update profile
        profile = user.profile
        profile.specialization = specialization
        profile.years_of_experience = years_of_experience
        profile.save()

        return Response({
            'message': 'Chúc mừng! Bạn đã trở thành giáo viên.',
            'user': UserSerializer(user).data,
        })
