from rest_framework import serializers

from apps.users.models import User
from apps.courses.models import Course

from .models import Comment, Follow, Post, Reaction, Report, Tag


class ForumAuthorSerializer(serializers.ModelSerializer):
    """Public forum identity without account/profile contact data."""

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'role', 'avatar', 'google_avatar']
        read_only_fields = fields


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'color', 'posts_count']
        read_only_fields = ['id', 'posts_count']


class ReactionSummarySerializer(serializers.Serializer):
    like = serializers.IntegerField(default=0)
    love = serializers.IntegerField(default=0)
    haha = serializers.IntegerField(default=0)
    wow = serializers.IntegerField(default=0)
    sad = serializers.IntegerField(default=0)
    angry = serializers.IntegerField(default=0)
    total = serializers.IntegerField(default=0)
    user_reaction = serializers.CharField(allow_null=True, default=None)


class ReactionInputSerializer(serializers.Serializer):
    reaction_type = serializers.ChoiceField(
        choices=Reaction.REACTION_CHOICES,
        required=False,
        allow_null=True,
    )


class CommentSerializer(serializers.ModelSerializer):
    author = ForumAuthorSerializer(read_only=True)
    replies_count = serializers.SerializerMethodField()
    reactions_summary = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'post', 'author', 'parent', 'content', 'image',
            'likes_count', 'is_solution', 'replies_count',
            'reactions_summary', 'replies', 'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_replies_count(self, obj):
        return obj.replies.count()

    def get_reactions_summary(self, obj):
        return _reaction_summary(obj.reactions.all(), self.context.get('request'))

    def get_replies(self, obj):
        replies = obj.replies.select_related('author').prefetch_related('replies__author').all()
        return CommentSerializer(replies, many=True, context=self.context).data


class CommentCreateSerializer(serializers.ModelSerializer):
    content = serializers.CharField(max_length=10000, trim_whitespace=True)

    class Meta:
        model = Comment
        fields = ['id', 'post', 'parent', 'content', 'image']
        read_only_fields = ['id']

    def validate(self, attrs):
        post = attrs['post']
        parent = attrs.get('parent')
        if post.is_closed:
            raise serializers.ValidationError({'post': 'Bài viết đã đóng.'})
        if parent is not None and parent.post_id != post.id:
            raise serializers.ValidationError({
                'parent': 'Bình luận cha phải thuộc cùng bài viết.'
            })
        return attrs


class CommentUpdateSerializer(serializers.ModelSerializer):
    content = serializers.CharField(max_length=10000, trim_whitespace=True)

    class Meta:
        model = Comment
        fields = ['content', 'image']


class CommentWithRepliesSerializer(CommentSerializer):
    class Meta(CommentSerializer.Meta):
        fields = CommentSerializer.Meta.fields


class PostListSerializer(serializers.ModelSerializer):
    author = ForumAuthorSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comments_count = serializers.IntegerField(
        source='comments_count_field', default=0, read_only=True
    )
    reactions_summary = serializers.SerializerMethodField()
    course = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'author', 'title', 'content', 'category', 'course',
            'image_1', 'image_2', 'image_3', 'image_4',
            'tags', 'views_count', 'likes_count', 'comments_count',
            'is_pinned', 'is_closed', 'is_solved',
            'reactions_summary', 'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_reactions_summary(self, obj):
        return _reaction_summary(obj.reactions.all(), self.context.get('request'))

    def get_course(self, obj):
        if obj.course is None:
            return None
        return {
            'id': obj.course_id,
            'title': obj.course.title,
            'slug': obj.course.slug,
        }


class PostWriteSerializer(serializers.ModelSerializer):
    content = serializers.CharField(max_length=20000, trim_whitespace=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        source='tags',
        queryset=Tag.objects.all(),
        many=True,
        required=False,
        write_only=True,
    )
    course_id = serializers.PrimaryKeyRelatedField(
        source='course',
        queryset=Course.objects.filter(is_published=True),
        write_only=True,
        required=True,
    )

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'content', 'category',
            'image_1', 'image_2', 'image_3', 'image_4', 'tag_ids', 'course_id',
        ]
        read_only_fields = ['id']


class PostDetailSerializer(PostListSerializer):
    comments = serializers.SerializerMethodField()

    class Meta(PostListSerializer.Meta):
        fields = [*PostListSerializer.Meta.fields, 'comments']

    def get_comments(self, obj):
        top_comments = obj.comments.filter(parent=None).select_related('author')
        return CommentWithRepliesSerializer(
            top_comments, many=True, context=self.context
        ).data


class ReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reaction
        fields = ['id', 'reaction_type', 'post', 'comment', 'created_at']
        read_only_fields = fields


class ReportReasonSerializer(serializers.Serializer):
    reason = serializers.ChoiceField(choices=Report.REASON_CHOICES)
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=2000,
    )


class ReportCreateSerializer(ReportReasonSerializer):
    post = serializers.PrimaryKeyRelatedField(
        queryset=Post.objects.all(), required=False, allow_null=True
    )
    comment = serializers.PrimaryKeyRelatedField(
        queryset=Comment.objects.all(), required=False, allow_null=True
    )

    def validate(self, attrs):
        if (attrs.get('post') is None) == (attrs.get('comment') is None):
            raise serializers.ValidationError(
                'Cần chọn đúng một bài viết hoặc bình luận để báo cáo.'
            )
        request = self.context.get('request')
        if request and Report.objects.filter(
            reporter=request.user,
            post=attrs.get('post'),
            comment=attrs.get('comment'),
        ).exists():
            raise serializers.ValidationError('Bạn đã báo cáo nội dung này.')
        return attrs

    def create(self, validated_data):
        return Report.objects.create(**validated_data)


class ReportSerializer(serializers.ModelSerializer):
    reporter = ForumAuthorSerializer(read_only=True)

    class Meta:
        model = Report
        fields = [
            'id', 'reporter', 'reason', 'description', 'status',
            'post', 'comment', 'created_at',
        ]
        read_only_fields = ['id', 'reporter', 'post', 'comment', 'created_at']


class FollowTargetSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(min_value=1)


class FollowSerializer(serializers.ModelSerializer):
    follower = ForumAuthorSerializer(read_only=True)
    following = ForumAuthorSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = ['id', 'follower', 'following', 'created_at']
        read_only_fields = fields


def _reaction_summary(reactions, request):
    summary = {
        reaction: 0
        for reaction in ['like', 'love', 'haha', 'wow', 'sad', 'angry']
    }
    for reaction in reactions:
        summary[reaction.reaction_type] = summary.get(reaction.reaction_type, 0) + 1
    summary['total'] = sum(summary.values())
    summary['user_reaction'] = None
    if request and request.user.is_authenticated:
        user_reaction = reactions.filter(user=request.user).first()
        if user_reaction:
            summary['user_reaction'] = user_reaction.reaction_type
    return summary
