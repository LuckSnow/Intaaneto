from rest_framework import serializers
from .models import Achievement, UserAchievement, LearningAnalytics


class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = '__all__'


class UserAchievementSerializer(serializers.ModelSerializer):
    achievement = AchievementSerializer(read_only=True)
    
    class Meta:
        model = UserAchievement
        fields = '__all__'


class LearningAnalyticsSerializer(serializers.ModelSerializer):
    achievements_count = serializers.SerializerMethodField()
    completion_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = LearningAnalytics
        fields = '__all__'
    
    def get_achievements_count(self, obj):
        return obj.user.achievements.count()
    
    def get_completion_rate(self, obj):
        if obj.total_courses_enrolled == 0:
            return 0
        return round((obj.total_courses_completed / obj.total_courses_enrolled) * 100, 2)
