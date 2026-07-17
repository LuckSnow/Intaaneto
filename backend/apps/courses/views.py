from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.db.models import Q
from config.throttling import ActionScopedThrottleMixin

from .models import Course, Lesson, Enrollment, Review, LessonComment
from .ingestion import IngestionQueueError, queue_pdf_ingestion
from .serializers import (
    CourseSerializer, CourseDetailSerializer, LessonSerializer,
    LessonUploadSerializer, LessonDetailSerializer, LessonCommentSerializer,
    EnrollmentSerializer, ReviewSerializer
)
from .services import (
    AssessmentRequiredError,
    complete_lesson,
)


class IsTeacher(BasePermission):
    """Only allow teachers or admins."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ('teacher', 'admin')


class IsCourseOwnerOrAdmin(BasePermission):
    """Restrict course mutations to its teacher or an administrator."""

    def has_object_permission(self, request, view, obj):
        return request.user.role == 'admin' or obj.teacher_id == request.user.id


class IsRecordOwnerOrAdmin(BasePermission):
    """Restrict learner-created record mutations to its author or an admin."""

    def has_object_permission(self, request, view, obj):
        return request.user.role == 'admin' or obj.user_id == request.user.id


def accessible_lessons(user):
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

    @action(detail=False, methods=['get'], permission_classes=[IsTeacher])
    def managed(self, request):
        """Return draft and published courses the teacher may administer."""
        queryset = (
            Course.objects.all()
            if request.user.role == 'admin'
            else Course.objects.filter(teacher=request.user)
        ).order_by('order', 'id')
        page = self.paginate_queryset(queryset)
        serializer = CourseSerializer(
            page if page is not None else queryset,
            many=True,
            context={'request': request},
        )
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    def perform_create(self, serializer):
        if self.request.user.role != 'teacher':
            raise PermissionDenied(
                'Quản trị viên cần chọn giảng viên trong Django Admin.'
            )
        serializer.save(teacher=self.request.user)

    def destroy(self, request, *args, **kwargs):
        course = self.get_object()
        if course.lessons.exists() or course.enrollments.exists():
            return Response(
                {
                    'code': 'course_not_empty',
                    'detail': (
                        'Chỉ có thể xóa khóa học chưa có bài học hoặc học viên. '
                        'Hãy chuyển khóa học về bản nháp để lưu trữ.'
                    ),
                },
                status=status.HTTP_409_CONFLICT,
            )
        return super().destroy(request, *args, **kwargs)

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


class LessonViewSet(ActionScopedThrottleMixin, viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    throttle_scope_by_action = {
        'upload': 'lesson_upload',
        'reprocess': 'lesson_reprocess',
    }

    def get_permissions(self):
        if self.action in ('upload', 'create', 'update', 'partial_update', 'destroy', 'reprocess'):
            permission_classes = [IsTeacher]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = accessible_lessons(self.request.user)
        course_id = self.request.query_params.get('course')
        if course_id is not None:
            if not course_id.isdigit():
                return queryset.none()
            queryset = queryset.filter(course_id=course_id)
        return queryset

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

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark lesson as completed"""
        lesson = self.get_object()
        try:
            result = complete_lesson(user=request.user, lesson=lesson)
        except AssessmentRequiredError as exc:
            return Response(
                {
                    'code': 'assessment_required',
                    'detail': str(exc),
                    'assessment_id': exc.assessment_id,
                },
                status=status.HTTP_409_CONFLICT,
            )

        return Response({
            'message': 'Lesson marked as completed',
            'is_completed': result['is_completed'],
            'progress_percentage': result['progress_percentage'],
            'next_lesson': (
                LessonSerializer(
                    result['next_lesson'],
                    context={'request': request},
                ).data
                if result['next_lesson'] else None
            ),
        })

    @action(detail=False, methods=['post'], permission_classes=[IsTeacher])
    def upload(self, request):
        """Validate and persist one PDF lesson, then enqueue durable ingestion."""
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
            job, created = queue_pdf_ingestion(actor=request.user, lesson=lesson)
        except IngestionQueueError as exc:
            return Response(
                {'error': str(exc), 'lesson_id': lesson.id},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        lesson.refresh_from_db()
        job.refresh_from_db()
        return Response({
            'message': 'PDF đã được tiếp nhận để xử lý.',
            'lesson': LessonDetailSerializer(lesson).data,
            'ingestion_job': {
                'id': job.id,
                'status': job.status,
                'attempts': job.attempts,
            },
            'queue_created': created,
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=True, methods=['get'])
    def processing_status(self, request, pk=None):
        """Check AI processing status of a lesson."""
        lesson = self.get_object()
        job = lesson.ingestion_jobs.order_by('-created_at', '-id').first()
        return Response({
            'id': lesson.id,
            'status': lesson.processing_status,
            'ai_video_url': lesson.ai_video_url,
            'ai_summary': lesson.ai_summary[:200] if lesson.ai_summary else '',
            'error': lesson.processing_error,
            'ingestion_job': (
                {
                    'id': job.id,
                    'status': job.status,
                    'attempts': job.attempts,
                    'failure_code': job.failure_code,
                    'knowledge_source_id': job.knowledge_source_id,
                    'index_created': job.index_created,
                }
                if job else None
            ),
        })

    @action(detail=True, methods=['post'])
    def reprocess(self, request, pk=None):
        """Queue a safe, idempotent retry for the lesson PDF."""
        lesson = self.get_object()
        if lesson.processing_status not in ('failed', 'completed'):
            return Response({'error': 'Bài giảng đang được xử lý'}, status=400)

        try:
            job, created = queue_pdf_ingestion(actor=request.user, lesson=lesson)
        except IngestionQueueError as exc:
            return Response(
                {'error': str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        lesson.refresh_from_db()
        job.refresh_from_db()
        return Response({
            'message': 'PDF đã được đưa vào hàng đợi xử lý lại.',
            'lesson': LessonDetailSerializer(lesson).data,
            'ingestion_job': {
                'id': job.id,
                'status': job.status,
                'attempts': job.attempts,
            },
            'queue_created': created,
        }, status=status.HTTP_202_ACCEPTED)


class LessonCommentViewSet(viewsets.ModelViewSet):
    serializer_class = LessonCommentSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        permissions = [IsAuthenticated]
        if self.action in ('update', 'partial_update', 'destroy'):
            permissions.append(IsRecordOwnerOrAdmin)
        return [permission() for permission in permissions]

    def get_queryset(self):
        lesson_id = self.request.query_params.get('lesson')
        qs = LessonComment.objects.filter(
            lesson__in=accessible_lessons(self.request.user),
        )
        if self.action == 'list':
            qs = qs.filter(parent__isnull=True)
        if lesson_id:
            qs = qs.filter(lesson_id=lesson_id)
        return qs.select_related('user').prefetch_related('replies__user')

    def perform_create(self, serializer):
        lesson = serializer.validated_data['lesson']
        if not accessible_lessons(self.request.user).filter(pk=lesson.pk).exists():
            raise PermissionDenied('Bạn không có quyền bình luận trong bài học này.')
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

    def get_permissions(self):
        permissions = [IsAuthenticated]
        if self.action in ('update', 'partial_update', 'destroy'):
            permissions.append(IsRecordOwnerOrAdmin)
        return [permission() for permission in permissions]

    def get_queryset(self):
        if self.request.user.role == 'admin':
            queryset = Review.objects.all()
        elif self.request.user.role == 'teacher':
            queryset = Review.objects.filter(
                Q(course__is_published=True) | Q(course__teacher=self.request.user)
            )
        else:
            queryset = Review.objects.filter(course__is_published=True)
        if self.action == 'list':
            course_id = self.request.query_params.get('course')
            if course_id:
                queryset = queryset.filter(course_id=course_id)
        return queryset.select_related('user', 'course')

    def perform_create(self, serializer):
        course = serializer.validated_data['course']
        if not Enrollment.objects.filter(
            user=self.request.user,
            course=course,
        ).exists():
            raise PermissionDenied('Bạn phải đăng ký khóa học trước khi đánh giá.')
        serializer.save(user=self.request.user)
