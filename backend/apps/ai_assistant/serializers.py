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
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_messages_count(self, obj):
        return obj.messages.count()


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField()
    session_id = serializers.IntegerField(required=False)
    context = serializers.JSONField(required=False)


class ExplainCodeSerializer(serializers.Serializer):
    code = serializers.CharField()
    language = serializers.CharField(default='javascript')


class HintRequestSerializer(serializers.Serializer):
    exercise_id = serializers.IntegerField()
    student_code = serializers.CharField(required=False, allow_blank=True)
