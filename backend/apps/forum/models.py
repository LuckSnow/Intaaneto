from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()


class Tag(models.Model):
    """Forum Tag"""
    name = models.CharField(_('name'), max_length=50, unique=True, db_index=True)
    slug = models.SlugField(_('slug'), max_length=50, unique=True)
    color = models.CharField(_('color'), max_length=7, default='#6366f1')
    posts_count = models.PositiveIntegerField(_('posts count'), default=0)

    class Meta:
        verbose_name = _('tag')
        verbose_name_plural = _('tags')
        ordering = ['name']

    def __str__(self):
        return self.name


class Post(models.Model):
    """Forum Post Model"""

    CATEGORY_CHOICES = [
        ('question', 'Câu hỏi'),
        ('discussion', 'Thảo luận'),
        ('showcase', 'Chia sẻ dự án'),
        ('announcement', 'Thông báo'),
    ]

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='forum_posts',
    )

    title = models.CharField(_('title'), max_length=255)
    content = models.TextField(_('content'))
    category = models.CharField(_('category'), max_length=20, choices=CATEGORY_CHOICES, default='question')

    # Images (up to 4)
    image_1 = models.ImageField(_('image 1'), upload_to='forum/posts/', null=True, blank=True)
    image_2 = models.ImageField(_('image 2'), upload_to='forum/posts/', null=True, blank=True)
    image_3 = models.ImageField(_('image 3'), upload_to='forum/posts/', null=True, blank=True)
    image_4 = models.ImageField(_('image 4'), upload_to='forum/posts/', null=True, blank=True)

    # Tags (M2M)
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')

    # Engagement
    views_count = models.PositiveIntegerField(_('views count'), default=0)
    likes_count = models.PositiveIntegerField(_('likes count'), default=0)
    comments_count = models.PositiveIntegerField(_('comments count'), default=0)

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
            models.Index(fields=['author', '-created_at']),
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
    image = models.ImageField(_('image'), upload_to='forum/comments/', null=True, blank=True)

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


class Reaction(models.Model):
    """Emoji Reaction for Posts and Comments"""

    REACTION_CHOICES = [
        ('like', '👍'),
        ('love', '❤️'),
        ('haha', '😂'),
        ('wow', '😮'),
        ('sad', '😢'),
        ('angry', '😡'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reactions')
    reaction_type = models.CharField(_('reaction'), max_length=10, choices=REACTION_CHOICES)

    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, related_name='reactions')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name='reactions')

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('reaction')
        verbose_name_plural = _('reactions')
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(post__isnull=False, comment__isnull=True)
                    | models.Q(post__isnull=True, comment__isnull=False)
                ),
                name='reaction_has_exactly_one_target',
            ),
            models.UniqueConstraint(
                fields=['user', 'post'],
                condition=models.Q(post__isnull=False),
                name='unique_post_reaction'
            ),
            models.UniqueConstraint(
                fields=['user', 'comment'],
                condition=models.Q(comment__isnull=False),
                name='unique_comment_reaction'
            ),
        ]

    def __str__(self):
        target = self.post or self.comment
        return f"{self.user.username} reacted {self.get_reaction_type_display()} on {target}"


class Report(models.Model):
    """Report a Post or Comment"""

    REASON_CHOICES = [
        ('spam', 'Spam'),
        ('harassment', 'Quấy rối'),
        ('inappropriate', 'Nội dung không phù hợp'),
        ('misinformation', 'Thông tin sai lệch'),
        ('other', 'Khác'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Đang chờ'),
        ('reviewed', 'Đã xem xét'),
        ('resolved', 'Đã xử lý'),
        ('dismissed', 'Bỏ qua'),
    ]

    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    reason = models.CharField(_('reason'), max_length=20, choices=REASON_CHOICES)
    description = models.TextField(_('description'), blank=True)
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='pending')

    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, related_name='reports')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name='reports')

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('report')
        verbose_name_plural = _('reports')
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(post__isnull=False, comment__isnull=True)
                    | models.Q(post__isnull=True, comment__isnull=False)
                ),
                name='report_has_exactly_one_target',
            ),
            models.UniqueConstraint(
                fields=['reporter', 'post'],
                condition=models.Q(post__isnull=False),
                name='unique_reporter_post_report',
            ),
            models.UniqueConstraint(
                fields=['reporter', 'comment'],
                condition=models.Q(comment__isnull=False),
                name='unique_reporter_comment_report',
            ),
        ]

    def __str__(self):
        return f"Report by {self.reporter.username} — {self.reason}"


class Follow(models.Model):
    """User follow another user"""

    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)

    class Meta:
        verbose_name = _('follow')
        verbose_name_plural = _('follows')
        unique_together = ['follower', 'following']

    def __str__(self):
        return f"{self.follower.username} → {self.following.username}"
