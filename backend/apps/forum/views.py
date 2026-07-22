from django.db import IntegrityError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.response import Response

from apps.users.models import User

from .models import Comment, Follow, Post, Reaction, Report, Tag
from .serializers import (
    CommentCreateSerializer,
    CommentSerializer,
    CommentUpdateSerializer,
    FollowSerializer,
    FollowTargetSerializer,
    PostDetailSerializer,
    PostListSerializer,
    PostWriteSerializer,
    ReactionInputSerializer,
    ReactionSerializer,
    ReportCreateSerializer,
    ReportReasonSerializer,
    ReportSerializer,
    TagSerializer,
)


class IsAuthorOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.author_id == request.user.id or request.user.role == 'admin'


class IsRoleAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_active
            and request.user.role == 'admin'
        )


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = 'slug'

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        return [IsRoleAdmin()]


class PostViewSet(viewsets.ModelViewSet):
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        queryset = Post.objects.select_related('author', 'course').prefetch_related(
            'tags', 'reactions'
        ).annotate(comments_count_field=Count('comments'))
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        tag = self.request.query_params.get('tag')
        if tag:
            queryset = queryset.filter(tags__slug=tag)
        course = self.request.query_params.get('course')
        if course:
            queryset = queryset.filter(course__slug=course)
        author = self.request.query_params.get('author')
        if author:
            queryset = queryset.filter(author_id=author)
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(content__icontains=search)
            )
        return queryset.distinct()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PostDetailSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return PostWriteSerializer
        return PostListSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [AllowAny()]
        if self.action == 'pin':
            return [IsRoleAdmin()]
        if self.action in (
            'update', 'partial_update', 'destroy', 'mark_solved', 'close'
        ):
            return [IsAuthenticated(), IsAuthorOrAdmin()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views_count += 1
        instance.save(update_fields=['views_count'])
        return Response(self.get_serializer(instance).data)

    @action(detail=True, methods=['post'])
    def react(self, request, pk=None):
        post = self.get_object()
        serializer = ReactionInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reaction_type = serializer.validated_data.get('reaction_type')
        if not reaction_type:
            Reaction.objects.filter(user=request.user, post=post).delete()
            post.likes_count = post.reactions.count()
            post.save(update_fields=['likes_count'])
            return Response({'message': 'Reaction removed'})
        reaction, _ = Reaction.objects.update_or_create(
            user=request.user,
            post=post,
            defaults={'reaction_type': reaction_type},
        )
        post.likes_count = post.reactions.count()
        post.save(update_fields=['likes_count'])
        return Response(ReactionSerializer(reaction).data)

    @action(detail=True, methods=['post'])
    def mark_solved(self, request, pk=None):
        post = self.get_object()
        post.is_solved = not post.is_solved
        post.save(update_fields=['is_solved'])
        return Response({'is_solved': post.is_solved})

    @action(detail=True, methods=['post'])
    def report(self, request, pk=None):
        post = self.get_object()
        serializer = ReportReasonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report, created = Report.objects.get_or_create(
            reporter=request.user,
            post=post,
            defaults=serializer.validated_data,
        )
        if not created:
            return Response(
                {'detail': 'Bạn đã báo cáo nội dung này.'},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(ReportSerializer(report).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def pin(self, request, pk=None):
        post = self.get_object()
        post.is_pinned = not post.is_pinned
        post.save(update_fields=['is_pinned'])
        return Response({'is_pinned': post.is_pinned})

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        post = self.get_object()
        post.is_closed = not post.is_closed
        post.save(update_fields=['is_closed'])
        return Response({'is_closed': post.is_closed})


class CommentViewSet(viewsets.ModelViewSet):
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        queryset = Comment.objects.select_related('author', 'post').prefetch_related(
            'reactions'
        )
        post_id = self.request.query_params.get('post')
        if post_id:
            queryset = queryset.filter(post_id=post_id, parent=None)
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return CommentCreateSerializer
        if self.action in ('update', 'partial_update'):
            return CommentUpdateSerializer
        return CommentSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'replies'):
            return [AllowAny()]
        if self.action in ('update', 'partial_update', 'destroy'):
            return [IsAuthenticated(), IsAuthorOrAdmin()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        comment = serializer.save(author=self.request.user)
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
        comment = self.get_object()
        serializer = ReactionInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reaction_type = serializer.validated_data.get('reaction_type')
        if not reaction_type:
            Reaction.objects.filter(user=request.user, comment=comment).delete()
            comment.likes_count = comment.reactions.count()
            comment.save(update_fields=['likes_count'])
            return Response({'message': 'Reaction removed'})
        reaction, _ = Reaction.objects.update_or_create(
            user=request.user,
            comment=comment,
            defaults={'reaction_type': reaction_type},
        )
        comment.likes_count = comment.reactions.count()
        comment.save(update_fields=['likes_count'])
        return Response(ReactionSerializer(reaction).data)

    @action(detail=True, methods=['post'])
    def mark_solution(self, request, pk=None):
        comment = self.get_object()
        post = comment.post
        if post.author_id != request.user.id and request.user.role != 'admin':
            return Response(
                {'error': 'Chỉ tác giả bài viết mới có quyền'},
                status=status.HTTP_403_FORBIDDEN,
            )
        post.comments.filter(is_solution=True).update(is_solution=False)
        comment.is_solution = True
        comment.save(update_fields=['is_solution'])
        post.is_solved = True
        post.save(update_fields=['is_solved'])
        return Response({'is_solution': True})

    @action(detail=True, methods=['post'])
    def report(self, request, pk=None):
        comment = self.get_object()
        serializer = ReportReasonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        report, created = Report.objects.get_or_create(
            reporter=request.user,
            comment=comment,
            defaults=serializer.validated_data,
        )
        if not created:
            return Response(
                {'detail': 'Bạn đã báo cáo nội dung này.'},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(ReportSerializer(report).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def replies(self, request, pk=None):
        comment = self.get_object()
        replies = comment.replies.select_related('author').all()
        return Response(CommentSerializer(
            replies, many=True, context={'request': request}
        ).data)


class FollowViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = FollowSerializer

    @action(detail=False, methods=['post'])
    def toggle(self, request):
        serializer = FollowTargetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = serializer.validated_data['user_id']
        if user_id == request.user.id:
            return Response(
                {'error': 'Không thể tự follow'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        target = get_object_or_404(User.objects.filter(is_active=True), pk=user_id)
        follow, created = Follow.objects.get_or_create(
            follower=request.user,
            following=target,
        )
        if not created:
            follow.delete()
            return Response({'following': False})
        return Response({'following': True}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def my_following(self, request):
        follows = Follow.objects.filter(follower=request.user).select_related('following')
        return Response(FollowSerializer(follows, many=True).data)

    @action(detail=False, methods=['get'])
    def my_followers(self, request):
        follows = Follow.objects.filter(following=request.user).select_related('follower')
        return Response(FollowSerializer(follows, many=True).data)

    @action(detail=False, methods=['get'])
    def check(self, request):
        serializer = FollowTargetSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        is_following = Follow.objects.filter(
            follower=request.user,
            following_id=serializer.validated_data['user_id'],
        ).exists()
        return Response({'following': is_following})


class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.select_related('reporter')

    def get_serializer_class(self):
        return ReportCreateSerializer if self.action == 'create' else ReportSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        return [IsRoleAdmin()]

    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError:
            return Response(
                {'detail': 'Bạn đã báo cáo nội dung này.'},
                status=status.HTTP_409_CONFLICT,
            )
