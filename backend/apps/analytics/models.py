from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()


class Achievement(models.Model):
    """Achievement/Badge Model"""
    
    name = models.CharField(_('name'), max_length=255)
    description = models.TextField(_('description'))
    icon = models.ImageField(_('icon'), upload_to='achievements/', null=True, blank=True)
    
    # Criteria
    criteria_type = models.CharField(_('criteria type'), max_length=50)
    criteria_value = models.PositiveIntegerField(_('criteria value'))
    
    points = models.PositiveIntegerField(_('points'), default=10)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('achievement')
        verbose_name_plural = _('achievements')
    
    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    """User earned achievement"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name='user_achievements')
    
    earned_at = models.DateTimeField(_('earned at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('user achievement')
        verbose_name_plural = _('user achievements')
        unique_together = ['user', 'achievement']
    
    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"


class LearningAnalytics(models.Model):
    """Track learning analytics"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='analytics')
    
    # Stats
    total_learning_time_minutes = models.PositiveIntegerField(_('total learning time'), default=0)
    total_courses_enrolled = models.PositiveIntegerField(_('total courses enrolled'), default=0)
    total_courses_completed = models.PositiveIntegerField(_('total courses completed'), default=0)
    total_exercises_submitted = models.PositiveIntegerField(_('total exercises submitted'), default=0)
    total_exercises_passed = models.PositiveIntegerField(_('total exercises passed'), default=0)
    
    # Engagement
    total_forum_posts = models.PositiveIntegerField(_('total forum posts'), default=0)
    total_forum_comments = models.PositiveIntegerField(_('total forum comments'), default=0)
    total_ai_interactions = models.PositiveIntegerField(_('total AI interactions'), default=0)
    
    # Streak
    current_streak_days = models.PositiveIntegerField(_('current streak'), default=0)
    longest_streak_days = models.PositiveIntegerField(_('longest streak'), default=0)
    last_activity_date = models.DateField(_('last activity date'), null=True, blank=True)
    
    # Points
    total_points = models.PositiveIntegerField(_('total points'), default=0)
    
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('learning analytics')
        verbose_name_plural = _('learning analytics')
    
    def __str__(self):
        return f"Analytics for {self.user.username}"
