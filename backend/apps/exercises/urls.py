from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExerciseViewSet, LessonAssessmentViewSet, SubmissionViewSet

router = DefaultRouter()
router.register(r'assessments', LessonAssessmentViewSet, basename='lesson-assessments')
router.register(r'submissions', SubmissionViewSet, basename='submissions')
router.register(r'', ExerciseViewSet, basename='exercises')

urlpatterns = [
    path('', include(router.urls)),
]
