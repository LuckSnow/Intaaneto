from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()


class Post(models.Model):
    """Forum Post Model"""
    
    CATEGORY_CHOICES = [
        ('question', 'Câu hỏi'),
        ('discussion', 'Thảo luận'),
        ('showcase', 'Chia sẻ dự án'),
        ('announcement', 'Thông báo'),
    ]
    
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    
    title = models.CharField(_('title'), max_length=255)
    content = models.TextField(_('content'))
    category = models.CharField(_('category'), max_length=20, choices=CATEGORY_CHOICES, default='question')
    
    # Tags
    tags = models.JSONField(_('tags'), default=list, blank=True)
    
    # Engagement
    views_count = models.PositiveIntegerField(_('views count'), default=0)
    likes_count = models.PositiveIntegerField(_('likes count'), default=0)
    
    # Status
    is_pinned = models.BooleanField(_('pinned'), default=False)
    is_closed = models.BooleanField(_('closed'), default=False)
    is_solved = models.BooleanField(_('solved'), default=False)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('post')
        verbose_name_plural = _('posts')
        ordering = ['-is_pinned', '-created_at']
        indexes = [
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['-is_pinned', '-created_at']),
        ]
    
    def __str__(self):
        return self.title


class Comment(models.Model):
    """Comment on Forum Post"""
    
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )
    
    content = models.TextField(_('content'))
    
    # Engagement
    likes_count = models.PositiveIntegerField(_('likes count'), default=0)
    
    # Status
    is_solution = models.BooleanField(_('is solution'), default=False)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('comment')
        verbose_name_plural = _('comments')
        ordering = ['-is_solution', 'created_at']
    
    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title}"


class Like(models.Model):
    """Like Model for Posts and Comments"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    
    # Using GenericForeignKey for flexibility
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, related_name='user_likes')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name='user_likes')
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('like')
        verbose_name_plural = _('likes')
        unique_together = [
            ['user', 'post'],
            ['user', 'comment'],
        ]
    
    def __str__(self):
        if self.post:
            return f"{self.user.username} likes post {self.post.id}"
        return f"{self.user.username} likes comment {self.comment.id}"
