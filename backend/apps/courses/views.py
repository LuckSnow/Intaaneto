import threading
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from .models import Course, Lesson, Enrollment, LessonProgress, Review, LessonComment
from .serializers import (
    CourseSerializer, CourseDetailSerializer, LessonSerializer,
    LessonUploadSerializer, LessonDetailSerializer, LessonCommentSerializer,
    EnrollmentSerializer, LessonProgressSerializer, ReviewSerializer
)
from .services import process_lesson

logger = logging.getLogger(__name__)


class IsTeacher(BasePermission):
    """Only allow teachers or admins."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ('teacher', 'admin')


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.filter(is_published=True)
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CourseDetailSerializer
        return CourseSerializer
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def enroll(self, request, pk=None):
        """Enroll in a course"""
        course = self.get_object()
        user = request.user
        
        enrollment, created = Enrollment.objects.get_or_create(
            user=user,
            course=course
        )
        
        if created:
            course.total_students += 1
            course.save()
            return Response(
                {'message': 'Enrolled successfully'},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'message': 'Already enrolled'},
                status=status.HTTP_200_OK
            )
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def progress(self, request, pk=None):
        """Get user's progress in this course"""
        course = self.get_object()
        enrollment = get_object_or_404(Enrollment, user=request.user, course=course)
        serializer = EnrollmentSerializer(enrollment)
        return Response(serializer.data)


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.filter(is_published=True)
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return LessonDetailSerializer
        if self.action in ('upload', 'create'):
            return LessonUploadSerializer
        return LessonSerializer
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark lesson as completed"""
        lesson = self.get_object()
        progress, created = LessonProgress.objects.get_or_create(
            user=request.user,
            lesson=lesson
        )
        
        progress.is_completed = True
        progress.save()
        
        return Response({'message': 'Lesson marked as completed'})
    
    @action(detail=False, methods=['post'], permission_classes=[IsTeacher])
    def upload(self, request):
        """
        Teacher uploads a PDF/PPT lesson.
        Triggers async AI processing: extract → summarize → generate video.
        """
        serializer = LessonUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lesson = serializer.save(
            lesson_type='text',
            processing_status='pending',
        )
        
        # Start async processing in background thread
        def _process():
            try:
                from django import db
                db.connections.close_all()
                process_lesson(lesson)
            except Exception as e:
                logger.error(f"Background processing failed for lesson {lesson.id}: {e}")
        
        thread = threading.Thread(target=_process, daemon=True)
        thread.start()
        
        return Response({
            'message': 'Bài giảng đã được tải lên! AI đang xử lý tạo video...',
            'lesson': LessonDetailSerializer(lesson).data,
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def processing_status(self, request, pk=None):
        """Check AI processing status of a lesson."""
        lesson = self.get_object()
        return Response({
            'id': lesson.id,
            'status': lesson.processing_status,
            'ai_video_url': lesson.ai_video_url,
            'ai_summary': lesson.ai_summary[:200] if lesson.ai_summary else '',
            'error': lesson.processing_error,
        })
    
    @action(detail=True, methods=['post'])
    def reprocess(self, request, pk=None):
        """Re-trigger AI processing for a failed lesson."""
        lesson = self.get_object()
        if lesson.processing_status not in ('failed', 'completed'):
            return Response({'error': 'Bài giảng đang được xử lý'}, status=400)
        
        lesson.processing_status = 'pending'
        lesson.processing_error = ''
        lesson.save(update_fields=['processing_status', 'processing_error'])
        
        def _process():
            try:
                from django import db
                db.connections.close_all()
                process_lesson(lesson)
            except Exception as e:
                logger.error(f"Reprocess failed for lesson {lesson.id}: {e}")
        
        thread = threading.Thread(target=_process, daemon=True)
        thread.start()
        
        return Response({'message': 'Đang xử lý lại...'})


class LessonCommentViewSet(viewsets.ModelViewSet):
    serializer_class = LessonCommentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        lesson_id = self.request.query_params.get('lesson')
        qs = LessonComment.objects.filter(parent__isnull=True)
        if lesson_id:
            qs = qs.filter(lesson_id=lesson_id)
        return qs.select_related('user').prefetch_related('replies__user')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class EnrollmentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Enrollment.objects.filter(user=self.request.user)


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.action == 'list':
            course_id = self.request.query_params.get('course')
            if course_id:
                return Review.objects.filter(course_id=course_id)
        return Review.objects.all()
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
