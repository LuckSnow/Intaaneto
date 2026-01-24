from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Post, Comment, Like
from .serializers import PostSerializer, PostDetailSerializer, CommentSerializer


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PostDetailSerializer
        return PostSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views_count += 1
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Like a post"""
        post = self.get_object()
        like, created = Like.objects.get_or_create(
            user=request.user,
            post=post
        )
        
        if created:
            post.likes_count += 1
            post.save()
            return Response({'message': 'Post liked'})
        else:
            like.delete()
            post.likes_count -= 1
            post.save()
            return Response({'message': 'Post unliked'})
    
    @action(detail=True, methods=['post'])
    def mark_solved(self, request, pk=None):
        """Mark post as solved"""
        post = self.get_object()
        if post.author != request.user:
            return Response(
                {'error': 'Only post author can mark as solved'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        post.is_solved = True
        post.save()
        return Response({'message': 'Post marked as solved'})


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        post_id = self.request.query_params.get('post')
        if post_id:
            return Comment.objects.filter(post_id=post_id, parent=None)
        return Comment.objects.all()
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Like a comment"""
        comment = self.get_object()
        like, created = Like.objects.get_or_create(
            user=request.user,
            comment=comment
        )
        
        if created:
            comment.likes_count += 1
            comment.save()
            return Response({'message': 'Comment liked'})
        else:
            like.delete()
            comment.likes_count -= 1
            comment.save()
            return Response({'message': 'Comment unliked'})
