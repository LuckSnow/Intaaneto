from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.permissions import BasePermission, IsAuthenticated
from apps.ai_assistant.rag_services import LessonRetrievalError

from apps.courses.models import Enrollment
from apps.courses.serializers import LessonSerializer
from apps.courses.services import recalculate_enrollment_mastery
from config.throttling import ActionScopedThrottleMixin

from .access import accessible_exercises
from .models import (
    AssessmentReinforcementEvent,
    Exercise,
    LessonAssessment,
    Submission,
)
from .serializers import (
    AssessmentAttemptSerializer,
    AssessmentSubmissionSerializer,
    ExerciseSerializer,
    LessonAssessmentLearnerSerializer,
    LessonAssessmentTeacherSerializer,
    ReinforcementRequestSerializer,
    SubmissionCreateSerializer,
    SubmissionSerializer,
)
from .reinforcement import build_reinforcement_packet
from .services import grade_assessment


class IsTeacherOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ('teacher', 'admin')


class ExerciseViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ExerciseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return accessible_exercises(self.request.user)
    
    @action(detail=True, methods=['get'])
    def submissions(self, request, pk=None):
        """Get user's submissions for this exercise"""
        exercise = self.get_object()
        submissions = Submission.objects.filter(
            exercise=exercise,
            user=request.user
        ).order_by('-submitted_at')
        serializer = SubmissionSerializer(submissions, many=True)
        return Response(serializer.data)


class SubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = SubmissionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Submission.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SubmissionCreateSerializer
        return SubmissionSerializer
    
    def perform_create(self, serializer):
        exercise = serializer.validated_data['exercise']
        if not accessible_exercises(self.request.user).filter(pk=exercise.pk).exists():
            raise PermissionDenied('Bạn không có quyền nộp bài tập này.')
        submission = serializer.save(user=self.request.user)
        # TODO: Implement code execution and testing logic
        # This would involve running the code against test cases
        # For now, just set it as pending
        submission.status = 'pending'
        submission.feedback = 'Bài nộp đang được xử lý...'
        submission.save()


class LessonAssessmentViewSet(ActionScopedThrottleMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    throttle_scope_by_action = {
        'submit': 'assessment_submit',
        'reinforcement': 'assessment_reinforcement',
    }

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [IsTeacherOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        queryset = LessonAssessment.objects.select_related(
            'lesson',
            'lesson__course',
        ).prefetch_related('questions')
        if user.role == 'admin':
            pass
        elif user.role == 'teacher':
            queryset = queryset.filter(lesson__course__teacher=user)
        else:
            queryset = queryset.filter(
                is_published=True,
                lesson__is_published=True,
                lesson__course__is_published=True,
                lesson__course__enrollments__user=user,
            ).distinct()

        lesson_id = self.request.query_params.get('lesson')
        if lesson_id:
            if not lesson_id.isdigit():
                return queryset.none()
            queryset = queryset.filter(lesson_id=lesson_id)
        return queryset

    def get_serializer_class(self):
        if self.request.user.role in ('teacher', 'admin'):
            return LessonAssessmentTeacherSerializer
        return LessonAssessmentLearnerSerializer

    def _validate_lesson_owner(self, lesson):
        user = self.request.user
        if user.role != 'admin' and lesson.course.teacher_id != user.id:
            raise PermissionDenied('Bạn không có quyền quản lý bài đánh giá này.')

    def perform_create(self, serializer):
        self._validate_lesson_owner(serializer.validated_data['lesson'])
        serializer.save()

    def perform_update(self, serializer):
        lesson = serializer.validated_data.get('lesson', serializer.instance.lesson)
        self._validate_lesson_owner(lesson)
        assessment = serializer.save()
        for enrollment in Enrollment.objects.filter(course=assessment.lesson.course):
            recalculate_enrollment_mastery(enrollment)

    def update(self, request, *args, **kwargs):
        assessment = self.get_object()
        if assessment.attempts.exists():
            return Response(
                {
                    'code': 'assessment_has_attempts',
                    'detail': 'Không thể sửa bài đánh giá đã có kết quả học tập.',
                },
                status=status.HTTP_409_CONFLICT,
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        assessment = self.get_object()
        if assessment.attempts.exists():
            return Response(
                {
                    'code': 'assessment_has_attempts',
                    'detail': 'Không thể xóa bài đánh giá đã có kết quả học tập.',
                },
                status=status.HTTP_409_CONFLICT,
            )
        course = assessment.lesson.course
        response = super().destroy(request, *args, **kwargs)
        for enrollment in Enrollment.objects.filter(course=course):
            recalculate_enrollment_mastery(enrollment)
        return response

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        assessment = self.get_object()
        input_serializer = AssessmentSubmissionSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        attempt, mastery_percentage, progression = grade_assessment(
            assessment=assessment,
            user=request.user,
            submitted_answers=input_serializer.validated_data['answers'],
        )

        response_data = AssessmentAttemptSerializer(attempt).data
        response_data['mastery_percentage'] = mastery_percentage
        response_data['reinforcement'] = [
            {
                'learning_objective': objective,
                'message': f'Hãy ôn lại mục tiêu: {objective}.',
            }
            for objective in attempt.weak_objectives
        ]
        response_data['progress_percentage'] = (
            progression['progress_percentage'] if progression else None
        )
        response_data['next_lesson'] = (
            LessonSerializer(
                progression['next_lesson'],
                context={'request': request},
            ).data
            if progression and progression['next_lesson'] else None
        )
        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def reinforcement(self, request, pk=None):
        assessment = self.get_object()
        input_serializer = ReinforcementRequestSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        attempt = assessment.attempts.filter(
            pk=input_serializer.validated_data['attempt_id'],
            user=request.user,
        ).first()
        if attempt is None:
            return Response(
                {'detail': 'Không tìm thấy kết quả đánh giá.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        try:
            packet = build_reinforcement_packet(
                attempt=attempt,
                actor=request.user,
            )
        except LessonRetrievalError:
            return Response(
                {
                    'detail': (
                        'Kho kiến thức tạm thời không khả dụng. '
                        'Vui lòng thử lại sau.'
                    )
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        AssessmentReinforcementEvent.objects.create(
            attempt=attempt,
            status=packet['status'],
            objective_count=len(packet['items']),
            ready_objective_count=sum(
                item['status'] == 'ready' for item in packet['items']
            ),
            evidence_count=sum(
                len(item['citations']) for item in packet['items']
            ),
        )
        return Response(packet)
