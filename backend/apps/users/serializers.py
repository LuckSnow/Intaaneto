from rest_framework import serializers
from django.contrib.auth import get_user_model
import re
from .models import Profile

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
