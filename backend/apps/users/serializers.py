from django.contrib.auth import get_user_model
from PIL import Image, UnidentifiedImageError
from rest_framework import serializers
import re
from .models import Profile, TeacherApplication

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    """Profile Serializer"""
    
    class Meta:
        model = Profile
        fields = [
            'grade_level', 'school_name', 'learning_style',
            'specialization', 'years_of_experience',
            'notification_enabled', 'email_notification'
        ]


class UserSerializer(serializers.ModelSerializer):
    """User Serializer"""

    profile = ProfileSerializer(read_only=True)
    MAX_AVATAR_BYTES = 5 * 1024 * 1024
    MAX_AVATAR_PIXELS = 8_000_000

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'full_name', 'role',
            'phone_number', 'date_of_birth', 'avatar', 'google_avatar', 'bio',
            'is_active', 'is_verified', 'profile',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'role', 'is_active', 'is_verified', 'created_at', 'updated_at'
        ]

    def validate_avatar(self, value):
        if value is None:
            return value
        if value.size <= 0 or value.size > self.MAX_AVATAR_BYTES:
            raise serializers.ValidationError(
                'Ảnh đại diện vượt quá giới hạn 5MB.'
            )

        position = value.tell()
        try:
            value.seek(0)
            with Image.open(value) as image:
                image.verify()
            value.seek(0)
            with Image.open(value) as image:
                width, height = image.size
                if (
                    image.format not in ('JPEG', 'PNG', 'WEBP')
                    or min(width, height) < 64
                    or max(width, height) > 4096
                    or width * height > self.MAX_AVATAR_PIXELS
                ):
                    raise serializers.ValidationError(
                        'Ảnh đại diện phải là JPEG, PNG hoặc WebP hợp lệ.'
                    )
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise serializers.ValidationError(
                'Ảnh đại diện không hợp lệ.'
            ) from exc
        finally:
            value.seek(position)
        return value


class RegisterSerializer(serializers.ModelSerializer):
    """Registration Serializer"""

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['email', 'username', 'full_name', 'password', 'password_confirm']
    
    def validate_password(self, value):
        """Validate password strength"""
        # Check minimum length
        if len(value) < 8:
            raise serializers.ValidationError("Mật khẩu phải có ít nhất 8 ký tự.")
        
        # Check for uppercase letter
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Mật khẩu phải có ít nhất 1 chữ cái viết hoa.")
        
        # Check for lowercase letter
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("Mật khẩu phải có ít nhất 1 chữ cái viết thường.")
        
        # Check for digit
        if not re.search(r'\d', value):
            raise serializers.ValidationError("Mật khẩu phải có ít nhất 1 chữ số.")
        
        # Check for special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise serializers.ValidationError("Mật khẩu phải có ít nhất 1 ký tự đặc biệt (!@#$%^&*...)")
        
        return value
    
    def validate(self, data):
        """Validate password confirmation"""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password": "Mật khẩu xác nhận không khớp."})
        return data
    
    def create(self, validated_data):
        """Create user"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, role='student', **validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """Login Serializer"""
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class ResendVerificationSerializer(serializers.Serializer):
    """Validate an email without exposing account existence."""

    email = serializers.EmailField()


class TeacherApplicationSerializer(serializers.ModelSerializer):
    """Learner-owned teacher application contract."""

    class Meta:
        model = TeacherApplication
        fields = [
            'id',
            'specialization',
            'years_of_experience',
            'reason',
            'status',
            'review_note',
            'submitted_at',
            'reviewed_at',
        ]
        read_only_fields = [
            'id',
            'status',
            'review_note',
            'submitted_at',
            'reviewed_at',
        ]
        extra_kwargs = {
            'specialization': {'min_length': 2},
            'reason': {'min_length': 20},
            'years_of_experience': {'min_value': 0, 'max_value': 80},
        }

    def validate_specialization(self, value):
        return value.strip()

    def validate_reason(self, value):
        return value.strip()


class TeacherApplicationReviewSerializer(serializers.Serializer):
    """Admin-only review decision."""

    application_id = serializers.IntegerField(min_value=1)
    decision = serializers.ChoiceField(choices=['approved', 'rejected'])
    review_note = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1000,
    )

    def validate(self, attrs):
        note = attrs.get('review_note', '').strip()
        if attrs['decision'] == 'rejected' and len(note) < 10:
            raise serializers.ValidationError({
                'review_note': 'Cần nêu lý do từ chối rõ ràng.',
            })
        attrs['review_note'] = note
        return attrs
