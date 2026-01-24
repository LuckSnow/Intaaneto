from django.contrib import admin
from .models import Course, Lesson, Enrollment, LessonProgress, Review


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
    list_display = ['title', 'course', 'lesson_type', 'order', 'duration_minutes', 'is_published']
    list_filter = ['lesson_type', 'is_published', 'course']
    search_fields = ['title', 'content', 'course__title']
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'progress_percentage', 'enrolled_at', 'completed_at']
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
