from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from apps.courses.models import Lesson

User = get_user_model()


class Exercise(models.Model):
    """Exercise/Assignment Model"""
    
    DIFFICULTY_CHOICES = [
        ('easy', 'Dễ'),
        ('medium', 'Trung bình'),
        ('hard', 'Khó'),
    ]
    
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='exercises',
        null=True,
        blank=True,
    )
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


class LessonAssessment(models.Model):
    """Deterministically graded knowledge check for one lesson."""

    lesson = models.OneToOneField(
        Lesson,
        on_delete=models.CASCADE,
        related_name='assessment',
    )
    title = models.CharField(_('title'), max_length=255)
    instructions = models.TextField(_('instructions'), blank=True, max_length=2000)
    pass_threshold = models.PositiveSmallIntegerField(
        _('pass threshold'),
        default=70,
        validators=[MinValueValidator(1), MaxValueValidator(100)],
    )
    version = models.PositiveIntegerField(_('version'), default=1)
    is_published = models.BooleanField(_('published'), default=False)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('lesson assessment')
        verbose_name_plural = _('lesson assessments')
        ordering = ['lesson__course_id', 'lesson__order', 'id']
        constraints = [
            models.CheckConstraint(
                check=models.Q(pass_threshold__gte=1, pass_threshold__lte=100),
                name='assessment_threshold_between_1_and_100',
            ),
        ]

    def __str__(self):
        return f'{self.lesson}: {self.title}'


class AssessmentQuestion(models.Model):
    """Teacher-authored multiple-choice question tied to a learning objective."""

    assessment = models.ForeignKey(
        LessonAssessment,
        on_delete=models.CASCADE,
        related_name='questions',
    )
    prompt = models.TextField(_('prompt'), max_length=2000)
    choices = models.JSONField(_('choices'), default=list)
    correct_choice = models.PositiveSmallIntegerField(_('correct choice'))
    learning_objective = models.CharField(
        _('learning objective'),
        max_length=255,
        blank=True,
    )
    explanation = models.TextField(_('explanation'), max_length=2000, blank=True)
    order = models.PositiveIntegerField(_('order'), default=0)

    class Meta:
        verbose_name = _('assessment question')
        verbose_name_plural = _('assessment questions')
        ordering = ['order', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['assessment', 'order'],
                name='unique_assessment_question_order',
            ),
        ]

    def __str__(self):
        return f'{self.assessment.title} #{self.order}'


class AssessmentAttempt(models.Model):
    """Immutable server-owned assessment result used for mastery reporting."""

    assessment = models.ForeignKey(
        LessonAssessment,
        on_delete=models.PROTECT,
        related_name='attempts',
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assessment_attempts',
    )
    assessment_version = models.PositiveIntegerField()
    threshold_snapshot = models.PositiveSmallIntegerField()
    score = models.DecimalField(max_digits=5, decimal_places=2)
    passed = models.BooleanField(default=False)
    total_questions = models.PositiveIntegerField()
    correct_answers = models.PositiveIntegerField()
    weak_objectives = models.JSONField(default=list, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at', '-id']
        indexes = [
            models.Index(fields=['user', 'assessment', '-submitted_at']),
            models.Index(fields=['assessment', 'passed']),
        ]

    def __str__(self):
        return f'{self.user_id} - {self.assessment_id}: {self.score}'


class AssessmentAnswer(models.Model):
    """Auditable answer snapshot that remains stable when questions change."""

    attempt = models.ForeignKey(
        AssessmentAttempt,
        on_delete=models.CASCADE,
        related_name='answers',
    )
    question = models.ForeignKey(
        AssessmentQuestion,
        on_delete=models.SET_NULL,
        related_name='attempt_answers',
        null=True,
        blank=True,
    )
    prompt_snapshot = models.TextField(max_length=2000)
    choices_snapshot = models.JSONField(default=list)
    learning_objective_snapshot = models.CharField(max_length=255, blank=True)
    selected_choice = models.PositiveSmallIntegerField()
    correct_choice_snapshot = models.PositiveSmallIntegerField()
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(
                fields=['attempt', 'question'],
                condition=models.Q(question__isnull=False),
                name='unique_attempt_question_answer',
            ),
        ]
