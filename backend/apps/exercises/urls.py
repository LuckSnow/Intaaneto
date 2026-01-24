from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExerciseViewSet, SubmissionViewSet

router = DefaultRouter()
router.register(r'', ExerciseViewSet, basename='exercises')
router.register(r'submissions', SubmissionViewSet, basename='submissions')

urlpatterns = [
    path('', include(router.urls)),
]
