from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    """Profile Serializer"""
    
    class Meta:
        model = Profile
        fields = [
            'grade_level', 'school_name', 'learning_style',
            'student', 'specialization', 'years_of_experience',
            'notification_enabled', 'email_notification'
        ]


class UserSerializer(serializers.ModelSerializer):
    """User Serializer"""
    
    profile = ProfileSerializer(read_only=True)
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'full_name', 'role',
            'phone_number', 'date_of_birth', 'avatar', 'bio',
            'is_active', 'is_verified', 'profile',
            'created_at', 'updated_at', 'password'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_verified']
    
    def create(self, validated_data):
        """Create user with password"""
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
    
    def update(self, instance, validated_data):
        """Update user with password handling"""
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class RegisterSerializer(serializers.ModelSerializer):
    """Registration Serializer"""
    
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)
    
    class Meta:
        model = User
        fields = ['email', 'username', 'full_name', 'role', 'password', 'password_confirm']
    
    def validate(self, data):
        """Validate password confirmation"""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords must match"})
        return data
    
    def create(self, validated_data):
        """Create user"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Login Serializer"""
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
