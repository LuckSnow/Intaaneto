from django.contrib import admin
from .models import Post, Comment, Like


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'views_count', 'likes_count', 'is_pinned', 'is_solved', 'created_at']
    list_filter = ['category', 'is_pinned', 'is_closed', 'is_solved', 'created_at']
    search_fields = ['title', 'content', 'author__full_name']
    raw_id_fields = ['author']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['post', 'author', 'likes_count', 'is_solution', 'created_at']
    list_filter = ['is_solution', 'created_at']
    search_fields = ['content', 'author__full_name', 'post__title']
    raw_id_fields = ['post', 'author', 'parent']


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'comment', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__full_name']
    raw_id_fields = ['user', 'post', 'comment']
