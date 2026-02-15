from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()


class Exercise(models.Model):
    """Exercise/Assignment Model"""
    
    DIFFICULTY_CHOICES = [
        ('easy', 'Dễ'),
        ('medium', 'Trung bình'),
        ('hard', 'Khó'),
    ]
    
    title = models.CharField(_('title'), max_length=255)
    description = models.TextField(_('description'))
    instructions = models.TextField(_('instructions'))
    
    difficulty = models.CharField(_('difficulty'), max_length=20, choices=DIFFICULTY_CHOICES, default='easy')
    
    # Exercise content
    starter_code = models.TextField(_('starter code'), blank=True)
    solution_code = models.TextField(_('solution code'), blank=True)
    test_cases = models.JSONField(_('test cases'), default=list, blank=True)
    
    # Points
    max_points = models.PositiveIntegerField(_('maximum points'), default=100)
    
    # Hints for AI assistant
    hints = models.JSONField(_('hints'), default=list, blank=True)
    
    order = models.PositiveIntegerField(_('order'), default=0)
    is_published = models.BooleanField(_('published'), default=True)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('exercise')
        verbose_name_plural = _('exercises')
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return self.title


class Submission(models.Model):
    """Student Submission"""
    
    STATUS_CHOICES = [
        ('pending', 'Đang chờ'),
        ('passed', 'Đạt'),
        ('failed', 'Không đạt'),
        ('error', 'Lỗi'),
    ]
    
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='submissions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    
    code = models.TextField(_('submitted code'))
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Results
    points_earned = models.PositiveIntegerField(_('points earned'), default=0)
    feedback = models.TextField(_('feedback'), blank=True)
    test_results = models.JSONField(_('test results'), default=dict, blank=True)
    
    # Execution info
    execution_time_ms = models.PositiveIntegerField(_('execution time (ms)'), null=True, blank=True)
    memory_used_kb = models.PositiveIntegerField(_('memory used (KB)'), null=True, blank=True)
    
    submitted_at = models.DateTimeField(_('submitted at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('submission')
        verbose_name_plural = _('submissions')
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['user', 'exercise']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.exercise.title} ({self.status})"
