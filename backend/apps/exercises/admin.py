from django.contrib import admin
from .models import Exercise, Submission


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['title', 'difficulty', 'max_points', 'is_published']
    list_filter = ['difficulty', 'is_published', 'created_at']
    search_fields = ['title', 'description']


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'exercise', 'status', 'points_earned', 'submitted_at']
    list_filter = ['status', 'submitted_at']
    search_fields = ['user__full_name', 'exercise__title']
    raw_id_fields = ['user', 'exercise']
    readonly_fields = ['submitted_at']
