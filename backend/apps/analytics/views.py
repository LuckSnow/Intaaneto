import csv

from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Achievement, UserAchievement, LearningAnalytics
from .serializers import (
    AchievementSerializer, UserAchievementSerializer, LearningAnalyticsSerializer,
    ProgressExportQuerySerializer, ProgressReportQuerySerializer,
)
from .progress_reporting import learner_progress_report, teaching_progress_report


MAX_PROGRESS_EXPORT_LEARNERS = 5000
CSV_FORMULA_PREFIXES = ('=', '+', '-', '@', '\t', '\r')


def _safe_csv_cell(value):
    """Prevent user-controlled text from becoming a spreadsheet formula."""
    text = '' if value is None else str(value)
    return f"'{text}" if text.startswith(CSV_FORMULA_PREFIXES) else text


class AnalyticsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def my_stats(self, request):
        """Get current user's analytics"""
        analytics, created = LearningAnalytics.objects.get_or_create(user=request.user)
        serializer = LearningAnalyticsSerializer(analytics)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_achievements(self, request):
        """Get current user's achievements"""
        achievements = UserAchievement.objects.filter(user=request.user)
        serializer = UserAchievementSerializer(achievements, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def progress_report(self, request):
        """Return server-derived learner or owned-course progress evidence."""
        query = ProgressReportQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        if request.user.role == 'student':
            return Response(learner_progress_report(request.user))
        if request.user.role in ('teacher', 'admin'):
            return Response(teaching_progress_report(
                actor=request.user,
                **query.validated_data,
            ))
        return Response({'detail': 'Vai trò không được hỗ trợ.'}, status=403)

    @action(detail=False, methods=['get'], url_path='progress-export')
    def progress_export(self, request):
        """Export one owned course roster without contact or answer data."""
        if request.user.role not in ('teacher', 'admin'):
            return Response({'detail': 'Chỉ giảng viên hoặc quản trị viên được xuất báo cáo.'}, status=403)

        query = ProgressExportQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        report = teaching_progress_report(
            actor=request.user,
            course_id=query.validated_data['course_id'],
            limit=MAX_PROGRESS_EXPORT_LEARNERS + 1,
            offset=0,
        )
        if report['pagination']['count'] > MAX_PROGRESS_EXPORT_LEARNERS:
            return Response(
                {'detail': 'Báo cáo vượt quá giới hạn 5000 học viên.'},
                status=413,
            )

        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = (
            f'attachment; filename="course-{report["course"]["course_id"]}-progress.csv"'
        )
        response.write('\ufeff')
        writer = csv.writer(response)
        writer.writerow([
            'learner_id',
            'full_name',
            'progress_percentage',
            'mastery_percentage',
            'completed_at',
            'last_accessed_lesson',
            'assessment_attempts',
            'assessments_attempted',
            'assessments_passed',
            'latest_assessment_at',
        ])
        for learner in report['learners']:
            writer.writerow([
                learner['user_id'],
                _safe_csv_cell(learner['full_name']),
                learner['progress_percentage'],
                learner['mastery_percentage'],
                learner['completed_at'] or '',
                _safe_csv_cell(
                    (learner['last_accessed_lesson'] or {}).get('title', '')
                ),
                learner['assessment_attempts'],
                learner['assessments_attempted'],
                learner['assessments_passed'],
                learner['latest_assessment_at'] or '',
            ])
        return response
    
    @action(detail=False, methods=['get'])
    def leaderboard(self, request):
        """Get leaderboard"""
        top_users = LearningAnalytics.objects.order_by('-total_points')[:10]
        serializer = LearningAnalyticsSerializer(top_users, many=True)
        return Response(serializer.data)


class AchievementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer
    permission_classes = [IsAuthenticated]
