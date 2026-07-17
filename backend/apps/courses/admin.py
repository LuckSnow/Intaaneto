from django.contrib import admin
from .models import (
    Course,
    Enrollment,
    Lesson,
    LessonComment,
    LessonIngestionJob,
    LessonProgress,
    LessonVideoGenerationJob,
    Review,
)


@admin.register(LessonIngestionJob)
class LessonIngestionJobAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'lesson', 'requested_by', 'status', 'attempts', 'created_at',
    ]
    list_filter = ['status', 'failure_code', 'created_at']
    search_fields = ['lesson__title', 'requested_by__full_name']
    raw_id_fields = ['lesson', 'requested_by', 'knowledge_source']
    readonly_fields = [
        'lesson', 'requested_by', 'knowledge_source', 'status', 'task_id',
        'attempts', 'index_created', 'failure_code', 'safe_error', 'created_at',
        'started_at', 'completed_at',
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ['title', 'lesson_type', 'order', 'duration_minutes', 'is_published']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'teacher', 'difficulty', 'total_students', 'is_published', 'created_at']
    list_filter = ['difficulty', 'is_published', 'is_featured', 'created_at']
    search_fields = ['title', 'description', 'teacher__full_name']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [LessonInline]
    
    fieldsets = (
        ('Basic Info', {'fields': ('title', 'slug', 'description', 'thumbnail', 'teacher')}),
        ('Details', {'fields': ('difficulty', 'duration_hours', 'objectives', 'prerequisites')}),
        ('Status', {'fields': ('is_published', 'is_featured', 'order')}),
        ('Stats', {'fields': ('total_students', 'average_rating')}),
    )


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'lesson_type', 'order', 'processing_status', 'is_published']
    list_filter = ['lesson_type', 'is_published', 'processing_status', 'course']
    search_fields = ['title', 'content', 'course__title']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['extracted_text', 'ai_summary', 'ai_video_url', 'ai_video_id', 'processing_status', 'processing_error']
    
    fieldsets = (
        ('Basic Info', {'fields': ('title', 'slug', 'course', 'lesson_type', 'order', 'is_published', 'is_preview')}),
        ('Content', {'fields': ('content', 'video_url', 'duration_minutes')}),
        ('AI Processing', {'fields': ('uploaded_file', 'processing_status', 'processing_error', 'extracted_text', 'ai_summary', 'ai_video_url', 'ai_video_id')}),
    )


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'course', 'progress_percentage', 'mastery_percentage',
        'enrolled_at', 'completed_at',
    ]
    list_filter = ['enrolled_at', 'completed_at']
    search_fields = ['user__full_name', 'course__title']
    raw_id_fields = ['user', 'course', 'last_accessed_lesson']


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'lesson', 'is_completed', 'time_spent_minutes', 'completed_at']
    list_filter = ['is_completed', 'completed_at']
    search_fields = ['user__full_name', 'lesson__title']
    raw_id_fields = ['user', 'lesson']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__full_name', 'course__title', 'comment']
    raw_id_fields = ['user', 'course']


@admin.register(LessonComment)
class LessonCommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'lesson', 'short_content', 'parent', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content', 'user__full_name', 'lesson__title']
    raw_id_fields = ['user', 'lesson', 'parent']
    
    def short_content(self, obj):
        return obj.content[:60] + '...' if len(obj.content) > 60 else obj.content
    short_content.short_description = 'Content'


@admin.register(LessonVideoGenerationJob)
class LessonVideoGenerationJobAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'lesson', 'requested_by', 'provider', 'status', 'created_at',
    ]
    list_filter = ['provider', 'status', 'created_at']
    search_fields = ['lesson__title', 'requested_by__full_name']
    raw_id_fields = ['lesson', 'requested_by']
    readonly_fields = [
        'lesson', 'requested_by', 'provider', 'status', 'approved_script',
        'script_checksum', 'audio_checksum', 'portrait_checksum',
        'rights_and_approval_confirmed', 'output_file', 'failure_code',
        'created_at', 'started_at', 'completed_at',
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
