from rest_framework import serializers
from .models import Post, Comment, Reaction, Report, Follow, Tag
from apps.users.serializers import UserSerializer


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'color', 'posts_count']
        read_only_fields = ['posts_count']


class ReactionSummarySerializer(serializers.Serializer):
    """Aggregated reaction counts for a post/comment"""
    like = serializers.IntegerField(default=0)
    love = serializers.IntegerField(default=0)
    haha = serializers.IntegerField(default=0)
    wow = serializers.IntegerField(default=0)
    sad = serializers.IntegerField(default=0)
    angry = serializers.IntegerField(default=0)
    total = serializers.IntegerField(default=0)
    user_reaction = serializers.CharField(allow_null=True, default=None)


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    replies_count = serializers.SerializerMethodField()
    reactions_summary = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id', 'post', 'author', 'parent', 'content', 'image',
            'likes_count', 'is_solution', 'replies_count',
            'reactions_summary', 'created_at', 'updated_at'
        ]
        read_only_fields = ['author', 'likes_count', 'created_at', 'updated_at']

    def get_replies_count(self, obj):
        return obj.replies.count()

    def get_reactions_summary(self, obj):
        reactions = obj.reactions.all()
        summary = {r: 0 for r in ['like', 'love', 'haha', 'wow', 'sad', 'angry']}
        for r in reactions:
            summary[r.reaction_type] = summary.get(r.reaction_type, 0) + 1
        summary['total'] = sum(summary.values())
        request = self.context.get('request')
        summary['user_reaction'] = None
        if request and request.user.is_authenticated:
            user_r = reactions.filter(user=request.user).first()
            if user_r:
                summary['user_reaction'] = user_r.reaction_type
        return summary


class CommentWithRepliesSerializer(CommentSerializer):
    replies = serializers.SerializerMethodField()

    class Meta(CommentSerializer.Meta):
        fields = CommentSerializer.Meta.fields + ['replies']

    def get_replies(self, obj):
        replies = obj.replies.select_related('author').all()
        return CommentSerializer(replies, many=True, context=self.context).data


class PostListSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comments_count = serializers.IntegerField(source='comments_count_field', default=0, read_only=True)
    reactions_summary = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'author', 'title', 'content', 'category',
            'image_1', 'image_2', 'image_3', 'image_4',
            'tags', 'views_count', 'likes_count', 'comments_count',
            'is_pinned', 'is_closed', 'is_solved',
            'reactions_summary', 'created_at', 'updated_at'
        ]
        read_only_fields = ['author', 'views_count', 'likes_count', 'comments_count', 'created_at', 'updated_at']

    def get_reactions_summary(self, obj):
        reactions = obj.reactions.all()
        summary = {r: 0 for r in ['like', 'love', 'haha', 'wow', 'sad', 'angry']}
        for r in reactions:
            summary[r.reaction_type] = summary.get(r.reaction_type, 0) + 1
        summary['total'] = sum(summary.values())
        request = self.context.get('request')
        summary['user_reaction'] = None
        if request and request.user.is_authenticated:
            user_r = reactions.filter(user=request.user).first()
            if user_r:
                summary['user_reaction'] = user_r.reaction_type
        return summary


class PostCreateSerializer(serializers.ModelSerializer):
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )

    class Meta:
        model = Post
        fields = [
            'title', 'content', 'category',
            'image_1', 'image_2', 'image_3', 'image_4',
            'tag_ids'
        ]

    def create(self, validated_data):
        tag_ids = validated_data.pop('tag_ids', [])
        post = Post.objects.create(**validated_data)
        if tag_ids:
            post.tags.set(tag_ids)
        return post


class PostDetailSerializer(PostListSerializer):
    comments = serializers.SerializerMethodField()

    class Meta(PostListSerializer.Meta):
        fields = PostListSerializer.Meta.fields + ['comments']

    def get_comments(self, obj):
        top_comments = obj.comments.filter(parent=None).select_related('author')
        return CommentWithRepliesSerializer(
            top_comments, many=True, context=self.context
        ).data


class ReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reaction
        fields = ['id', 'user', 'reaction_type', 'post', 'comment', 'created_at']
        read_only_fields = ['user', 'created_at']


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['id', 'reporter', 'reason', 'description', 'status', 'post', 'comment', 'created_at']
        read_only_fields = ['reporter', 'status', 'created_at']


class FollowSerializer(serializers.ModelSerializer):
    follower = UserSerializer(read_only=True)
    following = UserSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = ['id', 'follower', 'following', 'created_at']
        read_only_fields = ['follower', 'created_at']
