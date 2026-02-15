from rest_framework import serializers
from .models import Exercise, Submission


class ExerciseSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Exercise
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class SubmissionSerializer(serializers.ModelSerializer):
    exercise_title = serializers.CharField(source='exercise.title', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = Submission
        fields = '__all__'
        read_only_fields = ['user', 'status', 'points_earned', 'feedback', 'test_results', 'submitted_at']


class SubmissionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = ['exercise', 'code']
