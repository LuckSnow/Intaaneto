from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Count, Q
from .models import Post, Comment, Reaction, Report, Follow, Tag
from .serializers import (
    PostListSerializer, PostDetailSerializer, PostCreateSerializer,
    CommentSerializer, CommentWithRepliesSerializer,
    ReactionSerializer, ReportSerializer, FollowSerializer, TagSerializer,
)


class IsAuthorOrReadOnly:
    """Owner can edit/delete, others readonly"""
    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return obj.author == request.user or request.user.role == 'admin'


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = 'slug'

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]


class PostViewSet(viewsets.ModelViewSet):
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = Post.objects.select_related('author').prefetch_related(
            'tags', 'reactions'
        ).annotate(comments_count_field=Count('comments'))

        # Filters
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)

        tag = self.request.query_params.get('tag')
        if tag:
            qs = qs.filter(tags__slug=tag)

        author = self.request.query_params.get('author')
        if author:
            qs = qs.filter(author_id=author)

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(content__icontains=search))

        return qs

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PostDetailSerializer
        if self.action == 'create':
            return PostCreateSerializer
        return PostListSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views_count += 1
        instance.save(update_fields=['views_count'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def react(self, request, pk=None):
        """Add/change/remove reaction on a post"""
        post = self.get_object()
        reaction_type = request.data.get('reaction_type')

        if not reaction_type:
            # Remove existing reaction
            Reaction.objects.filter(user=request.user, post=post).delete()
            post.likes_count = post.reactions.count()
            post.save(update_fields=['likes_count'])
            return Response({'message': 'Reaction removed'})

        reaction, created = Reaction.objects.update_or_create(
            user=request.user, post=post,
            defaults={'reaction_type': reaction_type}
        )
        post.likes_count = post.reactions.count()
        post.save(update_fields=['likes_count'])
        return Response(ReactionSerializer(reaction).data)

    @action(detail=True, methods=['post'])
    def mark_solved(self, request, pk=None):
        post = self.get_object()
        if post.author != request.user and request.user.role != 'admin':
            return Response({'error': 'Chỉ tác giả mới có thể đánh dấu đã giải quyết'},
                            status=status.HTTP_403_FORBIDDEN)
        post.is_solved = not post.is_solved
        post.save(update_fields=['is_solved'])
        return Response({'is_solved': post.is_solved})

    @action(detail=True, methods=['post'])
    def report(self, request, pk=None):
        post = self.get_object()
        serializer = ReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(reporter=request.user, post=post)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def pin(self, request, pk=None):
        if request.user.role not in ['admin', 'teacher']:
            return Response({'error': 'Không có quyền'}, status=status.HTTP_403_FORBIDDEN)
        post = self.get_object()
        post.is_pinned = not post.is_pinned
        post.save(update_fields=['is_pinned'])
        return Response({'is_pinned': post.is_pinned})

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        post = self.get_object()
        if post.author != request.user and request.user.role != 'admin':
            return Response({'error': 'Không có quyền'}, status=status.HTTP_403_FORBIDDEN)
        post.is_closed = not post.is_closed
        post.save(update_fields=['is_closed'])
        return Response({'is_closed': post.is_closed})


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = Comment.objects.select_related('author').prefetch_related('reactions')
        post_id = self.request.query_params.get('post')
        if post_id:
            qs = qs.filter(post_id=post_id, parent=None)
        return qs

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        comment = serializer.save(author=self.request.user)
        # Update post comments_count
        post = comment.post
        post.comments_count = post.comments.count()
        post.save(update_fields=['comments_count'])

    def perform_destroy(self, instance):
        post = instance.post
        instance.delete()
        post.comments_count = post.comments.count()
        post.save(update_fields=['comments_count'])

    @action(detail=True, methods=['post'])
    def react(self, request, pk=None):
        """Add/change/remove reaction on a comment"""
        comment = self.get_object()
        reaction_type = request.data.get('reaction_type')

        if not reaction_type:
            Reaction.objects.filter(user=request.user, comment=comment).delete()
            comment.likes_count = comment.reactions.count()
            comment.save(update_fields=['likes_count'])
            return Response({'message': 'Reaction removed'})

        reaction, created = Reaction.objects.update_or_create(
            user=request.user, comment=comment,
            defaults={'reaction_type': reaction_type}
        )
        comment.likes_count = comment.reactions.count()
        comment.save(update_fields=['likes_count'])
        return Response(ReactionSerializer(reaction).data)

    @action(detail=True, methods=['post'])
    def mark_solution(self, request, pk=None):
        comment = self.get_object()
        post = comment.post
        if post.author != request.user and request.user.role != 'admin':
            return Response({'error': 'Chỉ tác giả bài viết mới có quyền'},
                            status=status.HTTP_403_FORBIDDEN)
        # Unmark previous solution
        post.comments.filter(is_solution=True).update(is_solution=False)
        comment.is_solution = True
        comment.save(update_fields=['is_solution'])
        post.is_solved = True
        post.save(update_fields=['is_solved'])
        return Response({'is_solution': True})

    @action(detail=True, methods=['post'])
    def report(self, request, pk=None):
        comment = self.get_object()
        serializer = ReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(reporter=request.user, comment=comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def replies(self, request, pk=None):
        comment = self.get_object()
        replies = comment.replies.select_related('author').all()
        serializer = CommentSerializer(replies, many=True, context={'request': request})
        return Response(serializer.data)


class FollowViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = FollowSerializer

    @action(detail=False, methods=['post'])
    def toggle(self, request):
        """Follow / unfollow a user"""
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        if int(user_id) == request.user.id:
            return Response({'error': 'Không thể tự follow'}, status=status.HTTP_400_BAD_REQUEST)

        follow, created = Follow.objects.get_or_create(
            follower=request.user, following_id=user_id
        )
        if not created:
            follow.delete()
            return Response({'following': False})
        return Response({'following': True}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def my_following(self, request):
        follows = Follow.objects.filter(follower=request.user).select_related('following')
        data = FollowSerializer(follows, many=True).data
        return Response(data)

    @action(detail=False, methods=['get'])
    def my_followers(self, request):
        follows = Follow.objects.filter(following=request.user).select_related('follower')
        data = FollowSerializer(follows, many=True).data
        return Response(data)

    @action(detail=False, methods=['get'])
    def check(self, request):
        user_id = request.query_params.get('user_id')
        is_following = Follow.objects.filter(
            follower=request.user, following_id=user_id
        ).exists()
        return Response({'following': is_following})


class ReportViewSet(viewsets.ModelViewSet):
    """Reports — only admins can list/manage, anyone auth can create"""
    queryset = Report.objects.all()
    serializer_class = ReportSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)
