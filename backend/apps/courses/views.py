from decimal import Decimal

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone

from .models import Course, Lesson, Enrollment, LessonProgress, Review, LessonComment
from .serializers import (
    CourseSerializer, CourseDetailSerializer, LessonSerializer,
    LessonUploadSerializer, LessonDetailSerializer, LessonCommentSerializer,
    EnrollmentSerializer, ReviewSerializer
)
from .services import PDFIngestionError, process_pdf_lesson


class IsTeacher(BasePermission):
    """Only allow teachers or admins."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ('teacher', 'admin')


class IsCourseOwnerOrAdmin(BasePermission):
    """Restrict course mutations to its teacher or an administrator."""

    def has_object_permission(self, request, view, obj):
        return request.user.role == 'admin' or obj.teacher_id == request.user.id


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()

    def get_queryset(self):
        if self.action in ('list', 'retrieve', 'enroll', 'progress'):
            return Course.objects.filter(is_published=True)
        if self.request.user.is_authenticated and self.request.user.role == 'admin':
            return Course.objects.all()
        if self.request.user.is_authenticated:
            return Course.objects.filter(teacher=self.request.user)
        return Course.objects.none()

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            permission_classes = [AllowAny]
        elif self.action in ('enroll', 'progress'):
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsTeacher, IsCourseOwnerOrAdmin]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CourseDetailSerializer
        return CourseSerializer

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)

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
    queryset = Lesson.objects.all()
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.action in ('upload', 'create', 'update', 'partial_update', 'destroy', 'reprocess'):
            permission_classes = [IsTeacher]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Lesson.objects.none()
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

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return LessonDetailSerializer
        if self.action in ('upload', 'create'):
            return LessonUploadSerializer
        return LessonSerializer

    def _validate_course_owner(self, course):
        user = self.request.user
        if user.role != 'admin' and course.teacher_id != user.id:
            raise PermissionDenied('Bạn không có quyền quản lý khóa học này.')

    def perform_create(self, serializer):
        self._validate_course_owner(serializer.validated_data['course'])
        serializer.save()

    @staticmethod
    def _available_lessons(course):
        """Published lessons that have readable text or an active RAG index."""
        return list(
            Lesson.objects.filter(course=course, is_published=True)
            .filter(
                ~Q(content='')
                | Q(
                    knowledge_sources__is_active=True,
                    knowledge_sources__status='ready',
                )
            )
            .distinct()
            .order_by('order', 'created_at', 'id')
        )

    def _next_available_lesson(self, lesson):
        user = self.request.user
        if user.role == 'student' and not Enrollment.objects.filter(
            user=user,
            course=lesson.course,
        ).exists():
            # A public preview must not reveal the next enrolled-only lesson.
            return None

        published_ids = list(
            Lesson.objects.filter(course=lesson.course, is_published=True)
            .order_by('order', 'created_at', 'id')
            .values_list('id', flat=True)
        )
        try:
            current_position = published_ids.index(lesson.id)
        except ValueError:
            return None

        available_by_id = {
            item.id: item for item in self._available_lessons(lesson.course)
        }
        for lesson_id in published_ids[current_position + 1:]:
            if lesson_id in available_by_id:
                return available_by_id[lesson_id]
        return None

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark lesson as completed"""
        lesson = self.get_object()
        progress, _ = LessonProgress.objects.get_or_create(
            user=request.user,
            lesson=lesson
        )

        progress.is_completed = True
        if progress.completed_at is None:
            progress.completed_at = timezone.now()
        progress.save(update_fields=['is_completed', 'completed_at', 'updated_at'])

        next_lesson = self._next_available_lesson(lesson)
        enrollment = Enrollment.objects.filter(
            user=request.user,
            course=lesson.course,
        ).first()
        progress_percentage = None
        if enrollment is not None:
            available_ids = [item.id for item in self._available_lessons(lesson.course)]
            completed_count = LessonProgress.objects.filter(
                user=request.user,
                lesson_id__in=available_ids,
                is_completed=True,
            ).count()
            if available_ids:
                progress_percentage = (
                    Decimal(completed_count * 100) / Decimal(len(available_ids))
                ).quantize(Decimal('0.01'))
            else:
                progress_percentage = Decimal('0.00')

            enrollment.progress_percentage = progress_percentage
            enrollment.last_accessed_lesson = next_lesson or lesson
            enrollment.completed_at = (
                timezone.now() if progress_percentage == Decimal('100.00') else None
            )
            enrollment.save(update_fields=[
                'progress_percentage',
                'last_accessed_lesson',
                'completed_at',
            ])

        return Response({
            'message': 'Lesson marked as completed',
            'is_completed': True,
            'progress_percentage': progress_percentage,
            'next_lesson': (
                LessonSerializer(next_lesson, context={'request': request}).data
                if next_lesson else None
            ),
        })

    @action(detail=False, methods=['post'], permission_classes=[IsTeacher])
    def upload(self, request):
        """
        Teacher uploads one PDF, then extraction and RAG indexing run synchronously.
        """
        course = Course.objects.filter(pk=request.data.get('course')).first()
        if course is not None:
            self._validate_course_owner(course)

        serializer = LessonUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self._validate_course_owner(serializer.validated_data['course'])
        lesson = serializer.save(
            lesson_type='text',
            processing_status='pending',
        )

        try:
            source, created = process_pdf_lesson(actor=request.user, lesson=lesson)
        except PDFIngestionError as exc:
            return Response(
                {'error': str(exc), 'lesson_id': lesson.id},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            'message': 'PDF đã được trích xuất và lập chỉ mục.',
            'lesson': LessonDetailSerializer(lesson).data,
            'knowledge_source_id': source.id,
            'index_created': created,
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
        """Safely extract and index the lesson PDF again."""
        lesson = self.get_object()
        if lesson.processing_status not in ('failed', 'completed'):
            return Response({'error': 'Bài giảng đang được xử lý'}, status=400)

        try:
            source, created = process_pdf_lesson(actor=request.user, lesson=lesson)
        except PDFIngestionError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'message': 'PDF đã được xử lý lại.',
            'lesson': LessonDetailSerializer(lesson).data,
            'knowledge_source_id': source.id,
            'index_created': created,
        })


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
