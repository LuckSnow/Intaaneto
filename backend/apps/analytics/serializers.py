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


class ProgressReportQuerySerializer(serializers.Serializer):
    course_id = serializers.IntegerField(min_value=1, required=False)
    limit = serializers.IntegerField(min_value=1, max_value=100, default=50)
    offset = serializers.IntegerField(min_value=0, default=0)


class ProgressExportQuerySerializer(serializers.Serializer):
    course_id = serializers.IntegerField(min_value=1, required=True)


class ObjectiveReportQuerySerializer(serializers.Serializer):
    course_id = serializers.IntegerField(min_value=1, required=True)
    limit = serializers.IntegerField(min_value=1, max_value=200, default=100)


class ReinforcementOutcomeQuerySerializer(serializers.Serializer):
    course_id = serializers.IntegerField(min_value=1, required=True)
    limit = serializers.IntegerField(min_value=1, max_value=5000, default=1000)
