from django.contrib import admin
from .models import Post, Comment, Reaction, Report, Follow, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'color', 'posts_count']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'views_count', 'likes_count', 'comments_count', 'is_pinned', 'is_solved', 'created_at']
    list_filter = ['category', 'is_pinned', 'is_closed', 'is_solved', 'created_at']
    search_fields = ['title', 'content', 'author__full_name']
    raw_id_fields = ['author']
    filter_horizontal = ['tags']


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['post', 'author', 'likes_count', 'is_solution', 'created_at']
    list_filter = ['is_solution', 'created_at']
    search_fields = ['content', 'author__full_name', 'post__title']
    raw_id_fields = ['post', 'author', 'parent']


@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'reaction_type', 'post', 'comment', 'created_at']
    list_filter = ['reaction_type', 'created_at']
    raw_id_fields = ['user', 'post', 'comment']


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['reporter', 'reason', 'status', 'post', 'comment', 'created_at']
    list_filter = ['reason', 'status', 'created_at']
    raw_id_fields = ['reporter', 'post', 'comment']


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'following', 'created_at']
    raw_id_fields = ['follower', 'following']
