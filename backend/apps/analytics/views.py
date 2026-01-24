from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Achievement, UserAchievement, LearningAnalytics
from .serializers import (
    AchievementSerializer, UserAchievementSerializer, LearningAnalyticsSerializer
)


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
    def leaderboard(self, request):
        """Get leaderboard"""
        top_users = LearningAnalytics.objects.order_by('-total_points')[:10]
        serializer = LearningAnalyticsSerializer(top_users, many=True)
        return Response(serializer.data)


class AchievementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer
    permission_classes = [IsAuthenticated]
