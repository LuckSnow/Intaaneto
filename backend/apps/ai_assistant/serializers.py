from django.conf import settings
from rest_framework import serializers
from .models import ChatSession, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'tokens_used', 'response_time_ms', 'created_at']
        read_only_fields = ['id', 'tokens_used', 'response_time_ms', 'created_at']


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)
    messages_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = ['id', 'title', 'context', 'messages_count', 'messages', 'created_at', 'updated_at']
        read_only_fields = ['id', 'context', 'created_at', 'updated_at']
    
    def get_messages_count(self, obj):
        return obj.messages.count()


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=settings.RAG_MAX_QUESTION_CHARS)
    session_id = serializers.IntegerField(required=False)
    lesson_id = serializers.IntegerField(required=False)

    def validate(self, attrs):
        if not attrs.get('session_id') and not attrs.get('lesson_id'):
            raise serializers.ValidationError('lesson_id is required for a new chat session')
        return attrs


class ChatHistoryQuerySerializer(serializers.Serializer):
    lesson_id = serializers.IntegerField(min_value=1)


class ExplainCodeSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=20000)
    language = serializers.CharField(default='javascript', max_length=30)


class HintRequestSerializer(serializers.Serializer):
    exercise_id = serializers.IntegerField()
    student_code = serializers.CharField(required=False, allow_blank=True)
