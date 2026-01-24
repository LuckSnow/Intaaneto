from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import ChatSession, ChatMessage
from .serializers import (
    ChatSessionSerializer, ChatMessageSerializer,
    ChatRequestSerializer, ExplainCodeSerializer, HintRequestSerializer
)
from .services import AIService
from apps.exercises.models import Exercise


class ChatViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def send_message(self, request):
        """Send message to AI"""
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        message = data['message']
        session_id = data.get('session_id')
        context = data.get('context', {})
        
        # Get or create session
        if session_id:
            session = ChatSession.objects.get(id=session_id, user=request.user)
        else:
            session = ChatSession.objects.create(
                user=request.user,
                title=message[:50],
                context=context
            )
        
        # Save user message
        ChatMessage.objects.create(
            session=session,
            role='user',
            content=message
        )
        
        # Get conversation history
        messages = []
        for msg in session.messages.all():
            messages.append({
                'role': msg.role,
                'content': msg.content
            })
        
        # Get AI response
        ai_response = AIService.chat(messages, context=session.context)
        
        # Save AI message
        ai_message = ChatMessage.objects.create(
            session=session,
            role='assistant',
            content=ai_response['content'],
            tokens_used=ai_response.get('tokens_used'),
            response_time_ms=ai_response.get('response_time_ms')
        )
        
        return Response({
            'session_id': session.id,
            'message': ChatMessageSerializer(ai_message).data
        })
    
    @action(detail=False, methods=['post'])
    def explain_code(self, request):
        """Explain code to student"""
        serializer = ExplainCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data['code']
        language = serializer.validated_data.get('language', 'javascript')
        
        explanation = AIService.explain_code(code, language)
        
        return Response({'explanation': explanation})
    
    @action(detail=False, methods=['post'])
    def get_hint(self, request):
        """Get hint for exercise"""
        serializer = HintRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        exercise_id = serializer.validated_data['exercise_id']
        student_code = serializer.validated_data.get('student_code', '')
        
        exercise = Exercise.objects.get(id=exercise_id)
        
        hint = AIService.give_hint(
            exercise_description=f"{exercise.title}\n\n{exercise.description}",
            student_code=student_code
        )
        
        return Response({'hint': hint})
