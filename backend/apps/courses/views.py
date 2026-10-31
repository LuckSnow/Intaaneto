from hashlib import sha256

from django.conf import settings
from django.http import FileResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, BasePermission
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.exceptions import PermissionDenied
from apps.ai_assistant.services import AIProviderError
from django.shortcuts import get_object_or_404
from django.db.models import Q
from config.throttling import ActionScopedThrottleMixin

from .models import (
    Course,
    Enrollment,
    Lesson,
    LessonComment,
    LessonIngestionJob,
    LessonMultimediaJob,
    LessonNarrationAudio,
    LessonSummaryDraft,
    LessonVideoScriptDraft,
    LessonVideoGenerationJob,
    Review,
)
from .ingestion import IngestionQueueError, queue_pdf_ingestion
from .multimedia_queue import MultimediaQueueError, queue_lesson_multimedia
from .serializers import (
    CourseSerializer, CourseDetailSerializer, LessonSerializer,
    LessonUploadSerializer, LessonDetailSerializer, LessonCommentSerializer,
    AssessmentGenerationRequestSerializer, EnrollmentSerializer,
    ReviewSerializer, SummaryApprovalSerializer, VideoScriptApprovalSerializer,
    TutorAvatarSelectionSerializer, TutorAvatarUploadSerializer,
)
from .tutor_avatars import avatar_library, preset_path, select_avatar, upload_avatar
from .content_authoring import (
    approve_summary_draft,
    approve_video_script_draft,
    assessment_generation_plan,
    generate_assessment_draft,
    generate_narration_audio,
    generate_summary_draft,
    generate_video_script_draft,
)
from .services import (
    AssessmentRequiredError,
    complete_lesson,
)
from .video_generation import VideoGenerationError


@api_view(['GET'])
@permission_classes([AllowAny])
def tutor_avatar_preset(request, preset_id):
    """Only the six bundled public illustrations, never an uploaded file."""
    path = preset_path(preset_id)
    if not path.is_file():
        return Response({'detail': 'Ảnh mẫu chưa sẵn sàng.'}, status=404)
    response = FileResponse(path.open('rb'))
    response['Cache-Control'] = 'public, max-age=3600'
    response['X-Content-Type-Options'] = 'nosniff'
    return response


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
        'tutor_avatar': 'lesson_upload',
        'upload': 'lesson_upload',
        'reprocess': 'lesson_reprocess',
        'generate_summary': 'lesson_authoring',
        'generate_video_script': 'lesson_authoring',
        'approve_video_script': 'lesson_authoring',
        'approve_summary': 'lesson_authoring',
        'generate_assessment': 'lesson_authoring',
        'generate_narration': 'lesson_authoring',
        'generate_multimedia': 'video_generation',
    }

    def get_permissions(self):
        if self.action in (
            'upload', 'create', 'update', 'partial_update', 'destroy',
            'reprocess', 'authoring_status', 'generate_summary',
            'approve_summary', 'generate_video_script', 'approve_video_script',
            'generate_assessment', 'generate_narration',
            'generate_multimedia',
            'tutor_avatar',
        ):
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

    def _managed_lesson(self):
        lesson = self.get_object()
        self._validate_course_owner(lesson.course)
        return lesson

    def _authoring_payload(self, lesson):
        def media_url(field):
            if not field:
                return None
            return self.request.build_absolute_uri(field.url)

        summary = LessonSummaryDraft.objects.filter(lesson=lesson).first()
        video_script = LessonVideoScriptDraft.objects.filter(lesson=lesson).first()
        narration = LessonNarrationAudio.objects.filter(lesson=lesson).first()
        assessment = getattr(lesson, 'assessment', None)
        video_job = LessonVideoGenerationJob.objects.filter(
            lesson=lesson,
        ).order_by('-created_at', '-id').first()
        multimedia_job = LessonMultimediaJob.objects.filter(
            lesson=lesson,
        ).order_by('-created_at', '-id').first()
        active_source = lesson.knowledge_sources.filter(
            is_active=True, status='ready',
        ).first()
        generation_plan = (
            assessment_generation_plan(active_source)
            if active_source else None
        )
        summary_checksum = (
            sha256(summary.text.encode('utf-8')).hexdigest()
            if (
                summary
                and summary.status == 'approved'
                and summary.text == lesson.ai_summary
                and active_source
                and summary.source_checksum == active_source.content_checksum
                and summary.source_version == active_source.version
            ) else None
        )
        video_script_current = bool(
            video_script
            and active_source
            and summary_checksum
            and video_script.source_checksum == active_source.content_checksum
            and video_script.source_version == active_source.version
            and video_script.summary_checksum == summary_checksum
        )
        return {
            'lesson_id': lesson.id,
            'tutor_avatars': avatar_library(request=self.request, lesson=lesson),
            'lesson_title': lesson.title,
            'pdf_url': media_url(lesson.uploaded_file),
            'extracted_chars': len(lesson.extracted_text or ''),
            'rag_ready': active_source is not None,
            'rag_source_version': active_source.version if active_source else None,
            'summary': ({
                'status': summary.status,
                'text': summary.text,
                'source_version': summary.source_version,
            } if summary else None),
            'video_script': ({
                'status': video_script.status,
                'text': video_script.text,
                'source_version': video_script.source_version,
                'is_current': video_script_current,
            } if video_script else None),
            'video_script_limits': {
                'max_chars': 4800,
                'max_segments': settings.MULTIMEDIA_MAX_SENTENCES,
                'max_duration_seconds': settings.MULTIMEDIA_MAX_DURATION_SECONDS,
                'piper_length_scale': settings.PIPER_LENGTH_SCALE,
            },
            'narration': ({
                'ready': bool(narration.audio_file),
                'provider': narration.provider,
                'voice': narration.voice,
                'audio_url': media_url(narration.audio_file),
            } if narration else None),
            'assessment': ({
                'id': assessment.id,
                'is_published': assessment.is_published,
                'question_count': assessment.questions.count(),
            } if assessment else None),
            'assessment_generation': generation_plan,
            'video': ({
                'job_id': video_job.id,
                'status': video_job.status,
                'failure_code': video_job.failure_code,
                'safe_error': video_job.safe_error,
                'video_url': (
                    media_url(video_job.output_file)
                ),
            } if video_job else None),
            'multimedia': ({
                'job_id': multimedia_job.id,
                'status': multimedia_job.status,
                'stage': multimedia_job.stage,
                'provider': multimedia_job.provider,
                'voice': multimedia_job.voice,
                'tutor_avatar': {
                    'preset_id': multimedia_job.tutor_preset,
                    'upload_id': multimedia_job.tutor_avatar_id,
                    'label': multimedia_job.tutor_avatar.label if multimedia_job.tutor_avatar_id else dict(multimedia_job._meta.get_field('tutor_preset').choices).get(multimedia_job.tutor_preset),
                },
                'scene_count': multimedia_job.scene_count,
                'duration_seconds': multimedia_job.duration_seconds,
                'render_duration_ms': multimedia_job.render_duration_ms,
                'failure_code': multimedia_job.failure_code,
                'safe_error': multimedia_job.safe_error,
                'video_url': media_url(multimedia_job.output_file),
            } if multimedia_job else None),
        }

    @staticmethod
    def _job_payload(job):
        return {
            'id': job.id,
            'status': job.status,
            'attempts': job.attempts,
            'failure_code': job.failure_code,
            'knowledge_source_id': job.knowledge_source_id,
            'index_created': job.index_created,
        }

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
            'ingestion_job': self._job_payload(job) if job else None,
        })

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsTeacher],
        url_path='ingestion-statuses',
    )
    def ingestion_statuses(self, request):
        """Return each lesson's latest bounded job state for one owned course."""

        raw_course_id = request.query_params.get('course')
        if not raw_course_id or not raw_course_id.isdigit():
            return Response(
                {'course': 'course phải là ID hợp lệ.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        course = get_object_or_404(Course, pk=int(raw_course_id))
        self._validate_course_owner(course)
        jobs = (
            LessonIngestionJob.objects.filter(lesson__course=course)
            .select_related('lesson')
            .order_by('lesson_id', '-created_at', '-id')
        )
        latest = []
        seen_lessons = set()
        for job in jobs[:200]:
            if job.lesson_id in seen_lessons:
                continue
            seen_lessons.add(job.lesson_id)
            latest.append({
                'lesson_id': job.lesson_id,
                'lesson_title': job.lesson.title,
                'processing_status': job.lesson.processing_status,
                'error': job.lesson.processing_error,
                'ingestion_job': self._job_payload(job),
            })
            if len(latest) >= 50:
                break
        return Response({'results': latest})

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

    @action(detail=True, methods=['get'], url_path='authoring-status')
    def authoring_status(self, request, pk=None):
        lesson = self._managed_lesson()
        return Response(self._authoring_payload(lesson))

    @action(detail=True, methods=['get'], url_path='pdf')
    def pdf(self, request, pk=None):
        lesson = self.get_object()
        if not lesson.uploaded_file:
            return Response(
                {'detail': 'Bài học không có file PDF.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        lesson.uploaded_file.open('rb')
        return FileResponse(
            lesson.uploaded_file,
            content_type='application/pdf',
            as_attachment=False,
            filename=f'lesson-{lesson.id}.pdf',
        )

    @action(detail=True, methods=['post'], url_path='generate-summary')
    def generate_summary(self, request, pk=None):
        lesson = self._managed_lesson()
        try:
            generate_summary_draft(actor=request.user, lesson=lesson)
        except AIProviderError:
            return Response(
                {'detail': 'Provider tóm tắt tạm thời không khả dụng.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(self._authoring_payload(lesson), status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='approve-summary')
    def approve_summary(self, request, pk=None):
        lesson = self._managed_lesson()
        serializer = SummaryApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        approve_summary_draft(
            actor=request.user,
            lesson=lesson,
            text=serializer.validated_data['text'],
        )
        return Response(self._authoring_payload(lesson))

    @action(detail=True, methods=['post'], url_path='generate-video-script')
    def generate_video_script(self, request, pk=None):
        lesson = self._managed_lesson()
        try:
            generate_video_script_draft(actor=request.user, lesson=lesson)
        except AIProviderError:
            return Response(
                {'detail': 'Provider tạo kịch bản video tạm thời không khả dụng.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(self._authoring_payload(lesson), status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='approve-video-script')
    def approve_video_script(self, request, pk=None):
        lesson = self._managed_lesson()
        serializer = VideoScriptApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        approve_video_script_draft(
            actor=request.user,
            lesson=lesson,
            text=serializer.validated_data['text'],
        )
        return Response(self._authoring_payload(lesson))

    @action(detail=True, methods=['post'], url_path='generate-assessment')
    def generate_assessment(self, request, pk=None):
        lesson = self._managed_lesson()
        serializer = AssessmentGenerationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            generate_assessment_draft(
                actor=request.user,
                lesson=lesson,
                question_count=serializer.validated_data['question_count'],
            )
        except AIProviderError:
            return Response(
                {'detail': 'Provider tạo assessment tạm thời không khả dụng.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(self._authoring_payload(lesson), status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='generate-narration')
    def generate_narration(self, request, pk=None):
        lesson = self._managed_lesson()
        try:
            generate_narration_audio(actor=request.user, lesson=lesson)
        except VideoGenerationError as exc:
            return Response(
                {'detail': str(exc), 'code': exc.code},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(self._authoring_payload(lesson), status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['put', 'post'], url_path='tutor-avatar')
    def tutor_avatar(self, request, pk=None):
        lesson = self._managed_lesson()
        if request.method == 'POST':
            serializer = TutorAvatarUploadSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            upload_avatar(actor=request.user, lesson=lesson, **serializer.validated_data)
        else:
            serializer = TutorAvatarSelectionSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            select_avatar(actor=request.user, lesson=lesson, **serializer.validated_data)
        return Response(self._authoring_payload(lesson), status=201 if request.method == 'POST' else 200)

    @action(detail=True, methods=['post'], url_path='generate-multimedia')
    def generate_multimedia(self, request, pk=None):
        lesson = self._managed_lesson()
        try:
            _, created = queue_lesson_multimedia(
                actor=request.user,
                lesson=lesson,
            )
        except MultimediaQueueError as exc:
            return Response(
                {'detail': str(exc)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response(
            {**self._authoring_payload(lesson), 'queue_created': created},
            status=status.HTTP_202_ACCEPTED,
        )


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
