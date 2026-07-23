from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CommentViewSet,
    FollowViewSet,
    PostViewSet,
    PublicForumProfileViewSet,
    ReportViewSet,
    TagViewSet,
)

router = DefaultRouter()
router.register(r'posts', PostViewSet, basename='posts')
router.register(r'comments', CommentViewSet, basename='comments')
router.register(r'tags', TagViewSet, basename='tags')
router.register(r'follows', FollowViewSet, basename='follows')
router.register(r'profiles', PublicForumProfileViewSet, basename='profiles')
router.register(r'reports', ReportViewSet, basename='reports')

urlpatterns = [
    path('', include(router.urls)),
]
