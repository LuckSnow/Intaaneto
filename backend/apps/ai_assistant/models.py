from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

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
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('chat message')
        verbose_name_plural = _('chat messages')
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."
