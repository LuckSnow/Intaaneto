import logging

from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.courses.models import Lesson
from apps.exercises.models import Exercise

from .models import ChatMessage, ChatSession
from .serializers import (
    ChatMessageSerializer,
    ChatRequestSerializer,
    ChatSessionSerializer,
    ExplainCodeSerializer,
    HintRequestSerializer,
)
from .services import AIProviderError, AIService

logger = logging.getLogger(__name__)


def accessible_lessons(user):
    """Return lessons the actor may use as an AI/RAG scope."""
    if user.role == 'admin':
        return Lesson.objects.all()
    if user.role == 'teacher':
        return Lesson.objects.filter(
            Q(course__teacher=user) | Q(course__enrollments__user=user)
        ).distinct()
    return Lesson.objects.filter(
        Q(course__enrollments__user=user)
        | Q(is_preview=True, is_published=True, course__is_published=True)
    ).distinct()


class ChatViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, context={})

    @action(detail=False, methods=['post'])
    def send_message(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        session_id = data.get('session_id')
        requested_lesson_id = data.get('lesson_id')
        if session_id:
            session = get_object_or_404(self.get_queryset(), pk=session_id)
            lesson_id = session.context.get('lesson_id')
            if requested_lesson_id and requested_lesson_id != lesson_id:
                return Response(
                    {'error': 'Không thể thay đổi phạm vi bài học của phiên chat.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            lesson_id = requested_lesson_id
            session = None

        lesson = get_object_or_404(accessible_lessons(request.user), pk=lesson_id)
        if session is None:
            session = ChatSession.objects.create(
                user=request.user,
                title=data['message'][:50],
                context={'lesson_id': lesson.id},
            )

        user_message = ChatMessage.objects.create(
            session=session,
            role='user',
            content=data['message'],
        )
        history = list(
            session.messages.filter(created_at__lte=user_message.created_at)
            .order_by('-created_at')[:settings.AI_MAX_HISTORY_MESSAGES]
        )
        messages = [
            {'role': message.role, 'content': message.content}
            for message in reversed(history)
            if message.role in ('user', 'assistant')
        ]
        context = {
            'lesson_title': lesson.title,
            'lesson_summary': (lesson.ai_summary or lesson.content)[:12000],
        }

        try:
            ai_response = AIService.chat(messages, context=context)
        except AIProviderError:
            logger.exception('AI provider failed for chat session %s', session.id)
            return Response(
                {'error': 'Trợ lý AI tạm thời không khả dụng. Vui lòng thử lại sau.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        ai_message = ChatMessage.objects.create(
            session=session,
            role='assistant',
            content=ai_response['content'],
            tokens_used=ai_response.get('tokens_used'),
            response_time_ms=ai_response.get('response_time_ms'),
        )
        return Response({
            'session_id': session.id,
            'answer': ai_message.content,
            'citations': [],
            'grounded': False,
            'message': ChatMessageSerializer(ai_message).data,
        })

    @action(detail=False, methods=['post'])
    def explain_code(self, request):
        serializer = ExplainCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            explanation = AIService.explain_code(**serializer.validated_data)
        except AIProviderError:
            return Response(
                {'error': 'Trợ lý AI tạm thời không khả dụng.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response({'explanation': explanation})

    @action(detail=False, methods=['post'])
    def get_hint(self, request):
        serializer = HintRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        exercise = get_object_or_404(
            Exercise.objects.filter(is_published=True),
            pk=serializer.validated_data['exercise_id'],
        )
        try:
            hint = AIService.give_hint(
                exercise_description=f"{exercise.title}\n\n{exercise.description}",
                student_code=serializer.validated_data.get('student_code', ''),
            )
        except AIProviderError:
            return Response(
                {'error': 'Trợ lý AI tạm thời không khả dụng.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response({'hint': hint})
