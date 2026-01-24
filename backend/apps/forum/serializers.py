from rest_framework import serializers
from .models import Post, Comment, Like
from apps.users.serializers import UserSerializer


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    replies_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = '__all__'
        read_only_fields = ['author', 'likes_count', 'created_at', 'updated_at']
    
    def get_replies_count(self, obj):
        return obj.replies.count()


class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    comments_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = '__all__'
        read_only_fields = ['author', 'views_count', 'likes_count', 'created_at', 'updated_at']
    
    def get_comments_count(self, obj):
        return obj.comments.count()


class PostDetailSerializer(PostSerializer):
    comments = CommentSerializer(many=True, read_only=True)


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = '__all__'
        read_only_fields = ['user', 'created_at']
