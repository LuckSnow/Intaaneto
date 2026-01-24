from django.contrib import admin
from .models import Achievement, UserAchievement, LearningAnalytics


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ['name', 'criteria_type', 'criteria_value', 'points', 'created_at']
    list_filter = ['criteria_type', 'created_at']
    search_fields = ['name', 'description']


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ['user', 'achievement', 'earned_at']
    list_filter = ['earned_at', 'achievement']
    search_fields = ['user__full_name', 'achievement__name']
    raw_id_fields = ['user', 'achievement']


@admin.register(LearningAnalytics)
class LearningAnalyticsAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'total_courses_enrolled', 'total_courses_completed',
        'total_exercises_passed', 'current_streak_days', 'total_points'
    ]
    search_fields = ['user__full_name']
    raw_id_fields = ['user']
    readonly_fields = ['updated_at']
