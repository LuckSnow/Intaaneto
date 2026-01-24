from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import LearningAnalytics

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_analytics(sender, instance, created, **kwargs):
    """Create analytics automatically when user is created"""
    if created:
        LearningAnalytics.objects.create(user=instance)
