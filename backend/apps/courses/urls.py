from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CourseViewSet, LessonViewSet, EnrollmentViewSet, ReviewViewSet

router = DefaultRouter()
router.register(r'', CourseViewSet, basename='courses')
router.register(r'lessons', LessonViewSet, basename='lessons')
router.register(r'enrollments', EnrollmentViewSet, basename='enrollments')
router.register(r'reviews', ReviewViewSet, basename='reviews')

urlpatterns = [
    path('', include(router.urls)),
]
