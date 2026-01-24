from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AnalyticsViewSet, AchievementViewSet

router = DefaultRouter()
router.register(r'', AnalyticsViewSet, basename='analytics')
router.register(r'achievements', AchievementViewSet, basename='achievements')

urlpatterns = [
    path('', include(router.urls)),
]
