import logging

from django.conf import settings
from django.db.models import CharField
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.exercises.access import accessible_exercises
from config.throttling import ActionScopedThrottleMixin

from .access import accessible_lesson_queryset
from .chat_history import serialize_lesson_chat_messages
from .models import ChatMessage, ChatSession
from .rag_answering import answer_lesson_question
from .rag_services import LessonRetrievalError
from .serializers import (
    ChatMessageSerializer,
    ChatHistoryQuerySerializer,
    ChatRequestSerializer,
    ChatSessionSerializer,
    ExplainCodeSerializer,
    HintRequestSerializer,
)
from .services import AIProviderError, AIService

logger = logging.getLogger(__name__)


class ChatViewSet(ActionScopedThrottleMixin, viewsets.ModelViewSet):
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'delete', 'head', 'options']
    throttle_scope_by_action = {
        'send_message': 'ai_chat',
        'explain_code': 'ai_chat',
        'get_hint': 'ai_hint',
    }

    def get_queryset(self):
        lesson_ids = accessible_lesson_queryset(self.request.user).annotate(
            text_id=Cast('id', output_field=CharField()),
        ).values('text_id')
        return ChatSession.objects.alias(
            context_lesson_id=KeyTextTransform('lesson_id', 'context'),
        ).filter(
            user=self.request.user,
            context_lesson_id__in=lesson_ids,
        )

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

        lesson = get_object_or_404(
            accessible_lesson_queryset(request.user),
            pk=lesson_id,
        )
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
        # A session with new activity must become the latest lesson session even
        # when the downstream provider fails after the user message is saved.
        session.save(update_fields=['updated_at'])
        history = list(
            session.messages.filter(created_at__lte=user_message.created_at)
            .order_by('-created_at')[:settings.AI_MAX_HISTORY_MESSAGES]
        )
        messages = [
            {'role': message.role, 'content': message.content}
            for message in reversed(history)
            if message.role in ('user', 'assistant')
        ]
        try:
            answer = answer_lesson_question(
                actor=request.user,
                lesson=lesson,
                messages=messages,
            )
        except LessonRetrievalError:
            logger.warning('RAG retrieval failed for chat session %s', session.id)
            return Response(
                {'error': 'Kho kiến thức tạm thời không khả dụng. Vui lòng thử lại sau.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except AIProviderError:
            logger.warning('AI provider failed for chat session %s', session.id)
            return Response(
                {'error': 'Trợ lý AI tạm thời không khả dụng. Vui lòng thử lại sau.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        ai_message = ChatMessage.objects.create(
            session=session,
            role='assistant',
            content=answer.answer,
            tokens_used=answer.tokens_used,
            response_time_ms=answer.response_time_ms,
            retrieval_metadata=answer.retrieval_metadata,
        )
        return Response({
            'session_id': session.id,
            'answer': ai_message.content,
            'citations': answer.citations,
            'grounded': answer.grounded,
            'retrieval': answer.retrieval,
            'message': ChatMessageSerializer(ai_message).data,
        })

    @action(detail=False, methods=['get'])
    def history(self, request):
        query = ChatHistoryQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        lesson = get_object_or_404(
            accessible_lesson_queryset(request.user),
            pk=query.validated_data['lesson_id'],
        )
        session = self.get_queryset().filter(
            context__lesson_id=lesson.id,
        ).order_by('-updated_at', '-id').first()
        if session is None:
            return Response({
                'session_id': None,
                'lesson_id': lesson.id,
                'messages': [],
            })

        recent_messages = list(
            session.messages.filter(role__in=('user', 'assistant'))
            .order_by('-created_at', '-id')[:settings.AI_MAX_HISTORY_MESSAGES]
        )
        recent_messages.reverse()
        return Response({
            'session_id': session.id,
            'lesson_id': lesson.id,
            'messages': serialize_lesson_chat_messages(
                messages=recent_messages,
                lesson=lesson,
            ),
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
            accessible_exercises(request.user),
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
