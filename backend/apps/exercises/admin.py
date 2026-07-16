from django.contrib import admin
from .models import (
    AssessmentAttempt,
    AssessmentQuestion,
    AssessmentReinforcementEvent,
    Exercise,
    LessonAssessment,
    Submission,
)


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


class AssessmentQuestionInline(admin.TabularInline):
    model = AssessmentQuestion
    extra = 1


@admin.register(LessonAssessment)
class LessonAssessmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'lesson', 'pass_threshold', 'version', 'is_published']
    list_filter = ['is_published', 'pass_threshold']
    search_fields = ['title', 'lesson__title', 'lesson__course__title']
    raw_id_fields = ['lesson']
    inlines = [AssessmentQuestionInline]


@admin.register(AssessmentAttempt)
class AssessmentAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'assessment', 'score', 'passed', 'submitted_at']
    list_filter = ['passed', 'submitted_at']
    search_fields = ['user__full_name', 'assessment__title']
    raw_id_fields = ['user', 'assessment']
    readonly_fields = [
        'assessment', 'user', 'assessment_version', 'threshold_snapshot',
        'score', 'passed', 'total_questions', 'correct_answers',
        'weak_objectives', 'submitted_at',
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AssessmentReinforcementEvent)
class AssessmentReinforcementEventAdmin(admin.ModelAdmin):
    list_display = [
        'attempt', 'status', 'objective_count', 'ready_objective_count',
        'evidence_count', 'requested_at',
    ]
    list_filter = ['status', 'requested_at']
    raw_id_fields = ['attempt']
    readonly_fields = [
        'attempt', 'status', 'objective_count', 'ready_objective_count',
        'evidence_count', 'requested_at',
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
