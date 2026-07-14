from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.db.models import Q
from pgvector.django import VectorField

User = get_user_model()


class ChatSession(models.Model):
    """AI Chat Session"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    
    title = models.CharField(_('title'), max_length=255, blank=True)
    context = models.JSONField(_('context'), default=dict, blank=True)  # Store lesson context, etc.
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('chat session')
        verbose_name_plural = _('chat sessions')
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Chat session {self.id} - {self.user.username}"


class ChatMessage(models.Model):
    """Chat Message"""
    
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'AI Assistant'),
        ('system', 'System'),
    ]
    
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    
    role = models.CharField(_('role'), max_length=20, choices=ROLE_CHOICES)
    content = models.TextField(_('content'))
    
    # Metadata
    tokens_used = models.PositiveIntegerField(_('tokens used'), null=True, blank=True)
    response_time_ms = models.PositiveIntegerField(_('response time (ms)'), null=True, blank=True)
    retrieval_metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('chat message')
        verbose_name_plural = _('chat messages')
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class KnowledgeSource(models.Model):
    """One complete, versioned lesson-text index."""

    SOURCE_TYPE_CHOICES = [
        ('lesson_content', 'Lesson content'),
        ('extracted_text', 'Extracted text'),
    ]
    STATUS_CHOICES = [
        ('ready', 'Ready'),
        ('archived', 'Archived'),
    ]

    lesson = models.ForeignKey(
        'courses.Lesson',
        on_delete=models.CASCADE,
        related_name='knowledge_sources',
    )
    source_type = models.CharField(max_length=30, choices=SOURCE_TYPE_CHOICES)
    version = models.PositiveIntegerField()
    content_checksum = models.CharField(max_length=64)
    normalized_text = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ready')
    is_active = models.BooleanField(default=False)

    embedding_provider = models.CharField(max_length=100)
    embedding_model = models.CharField(max_length=255)
    embedding_revision = models.CharField(max_length=100)
    embedding_dimension = models.PositiveIntegerField()
    chunker_version = models.CharField(max_length=50)
    chunk_size = models.PositiveIntegerField()
    chunk_overlap = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['lesson_id', '-version']
        constraints = [
            models.UniqueConstraint(
                fields=['lesson', 'version'],
                name='unique_knowledge_source_lesson_version',
            ),
            models.UniqueConstraint(
                fields=['lesson'],
                condition=Q(is_active=True),
                name='unique_active_knowledge_source_per_lesson',
            ),
        ]
        indexes = [
            models.Index(fields=['lesson', 'is_active', 'status']),
            models.Index(fields=['lesson', 'content_checksum']),
        ]

    def __str__(self):
        return f"Lesson {self.lesson_id} knowledge v{self.version}"


class KnowledgeChunk(models.Model):
    """A deterministic text span and its provider-generated embedding."""

    source = models.ForeignKey(
        KnowledgeSource,
        on_delete=models.CASCADE,
        related_name='chunks',
    )
    ordinal = models.PositiveIntegerField()
    text = models.TextField()
    start_offset = models.PositiveIntegerField()
    end_offset = models.PositiveIntegerField()
    char_count = models.PositiveIntegerField()
    embedding = VectorField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['source_id', 'ordinal']
        constraints = [
            models.UniqueConstraint(
                fields=['source', 'ordinal'],
                name='unique_knowledge_chunk_source_ordinal',
            ),
        ]

    def __str__(self):
        return f"Source {self.source_id} chunk {self.ordinal}"
