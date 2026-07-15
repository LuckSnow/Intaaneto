from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.utils.text import slugify

User = get_user_model()


class Course(models.Model):
    """Course Model"""
    
    DIFFICULTY_CHOICES = [
        ('beginner', 'Cơ bản'),
        ('intermediate', 'Trung bình'),
        ('advanced', 'Nâng cao'),
    ]
    
    title = models.CharField(_('title'), max_length=255)
    slug = models.SlugField(_('slug'), unique=True, max_length=255)
    description = models.TextField(_('description'))
    thumbnail = models.ImageField(_('thumbnail'), upload_to='courses/thumbnails/', null=True, blank=True)
    
    difficulty = models.CharField(_('difficulty'), max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')
    duration_hours = models.PositiveIntegerField(_('duration (hours)'), default=0)
    
    # Content
    objectives = models.TextField(_('learning objectives'), blank=True)
    prerequisites = models.TextField(_('prerequisites'), blank=True)
    
    # Teacher/Author
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='courses_taught',
        limit_choices_to={'role': 'teacher'}
    )
    
    # Status
    is_published = models.BooleanField(_('published'), default=False)
    is_featured = models.BooleanField(_('featured'), default=False)
    
    # Ordering
    order = models.PositiveIntegerField(_('order'), default=0)
    
    # Stats
    total_students = models.PositiveIntegerField(_('total students'), default=0)
    average_rating = models.DecimalField(_('average rating'), max_digits=3, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('course')
        verbose_name_plural = _('courses')
        ordering = ['order', '-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_published', 'difficulty']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class Lesson(models.Model):
    """Lesson Model"""
    
    LESSON_TYPE_CHOICES = [
        ('video', 'Video'),
        ('text', 'Văn bản'),
        ('interactive', 'Tương tác'),
        ('quiz', 'Bài kiểm tra'),
    ]
    
    PROCESSING_STATUS_CHOICES = [
        ('pending', 'Chờ xử lý'),
        ('extracting', 'Đang trích xuất nội dung'),
        ('summarizing', 'Đang tóm tắt'),
        ('generating_video', 'Đang tạo video AI'),
        ('completed', 'Hoàn thành'),
        ('failed', 'Thất bại'),
    ]
    
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    
    title = models.CharField(_('title'), max_length=255)
    slug = models.SlugField(_('slug'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    
    lesson_type = models.CharField(_('lesson type'), max_length=20, choices=LESSON_TYPE_CHOICES, default='text')
    
    # Content
    content = models.TextField(_('content'), blank=True)
    video_url = models.URLField(_('video URL'), blank=True, max_length=500)
    video_file = models.FileField(_('video file'), upload_to='courses/videos/', null=True, blank=True)
    
    # Teacher uploaded document (PDF only)
    uploaded_file = models.FileField(_('uploaded file'), upload_to='courses/uploads/', null=True, blank=True)
    
    # AI Processing
    extracted_text = models.TextField(_('extracted text'), blank=True, help_text='Raw text extracted from uploaded PDF')
    ai_summary = models.TextField(_('AI summary'), blank=True, help_text='AI-generated lecture summary script')
    ai_video_url = models.URLField(_('AI video URL'), blank=True, max_length=500, help_text='D-ID generated video URL')
    ai_video_id = models.CharField(_('D-ID talk ID'), max_length=100, blank=True, help_text='D-ID talk ID for polling')
    processing_status = models.CharField(_('processing status'), max_length=20, choices=PROCESSING_STATUS_CHOICES, default='pending')
    processing_error = models.TextField(_('processing error'), blank=True)
    
    # Resources
    attachments = models.FileField(_('attachments'), upload_to='courses/attachments/', null=True, blank=True)
    
    # Duration
    duration_minutes = models.PositiveIntegerField(_('duration (minutes)'), default=0)
    
    # Ordering
    order = models.PositiveIntegerField(_('order'), default=0)
    
    # Status
    is_preview = models.BooleanField(_('free preview'), default=False)
    is_published = models.BooleanField(_('published'), default=True)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('lesson')
        verbose_name_plural = _('lessons')
        ordering = ['order', 'created_at']
        unique_together = ['course', 'slug']
        indexes = [
            models.Index(fields=['course', 'order']),
        ]
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class Enrollment(models.Model):
    """Student Enrollment in Course"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    
    enrolled_at = models.DateTimeField(_('enrolled at'), auto_now_add=True)
    completed_at = models.DateTimeField(_('completed at'), null=True, blank=True)
    
    progress_percentage = models.DecimalField(_('progress percentage'), max_digits=5, decimal_places=2, default=0.00)
    last_accessed_lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='last_accessed_by'
    )
    
    class Meta:
        verbose_name = _('enrollment')
        verbose_name_plural = _('enrollments')
        unique_together = ['user', 'course']
        indexes = [
            models.Index(fields=['user', 'course']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} - {self.course.title}"


class LessonProgress(models.Model):
    """Track lesson completion"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress')
    
    is_completed = models.BooleanField(_('completed'), default=False)
    completed_at = models.DateTimeField(_('completed at'), null=True, blank=True)
    time_spent_minutes = models.PositiveIntegerField(_('time spent (minutes)'), default=0)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('lesson progress')
        verbose_name_plural = _('lesson progress')
        unique_together = ['user', 'lesson']
    
    def __str__(self):
        return f"{self.user.username} - {self.lesson.title}"


class Review(models.Model):
    """Course Review"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    
    rating = models.PositiveSmallIntegerField(_('rating'), choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(_('comment'), blank=True)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('review')
        verbose_name_plural = _('reviews')
        unique_together = ['user', 'course']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.course.title} ({self.rating}⭐)"


class LessonComment(models.Model):
    """Comments on a lesson (interaction during learning)"""
    
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lesson_comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    content = models.TextField(_('content'))
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('lesson comment')
        verbose_name_plural = _('lesson comments')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}: {self.content[:50]}"
