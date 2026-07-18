from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet, LessonViewSet, LessonCommentViewSet,
    EnrollmentViewSet, ReviewViewSet
)

router = DefaultRouter()
router.register(r'lessons', LessonViewSet, basename='lessons')
router.register(r'lesson-comments', LessonCommentViewSet, basename='lesson-comments')
router.register(r'enrollments', EnrollmentViewSet, basename='enrollments')
router.register(r'reviews', ReviewViewSet, basename='reviews')
# Keep the empty-prefix course routes last so /<pk>/ cannot shadow named APIs.
router.register(r'', CourseViewSet, basename='courses')

urlpatterns = [
    path('', include(router.urls)),
]
