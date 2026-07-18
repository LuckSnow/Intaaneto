"""Server-owned exercise scopes shared by exercise and AI endpoints."""

from .models import Exercise


def accessible_exercises(user):
    if not getattr(user, 'is_authenticated', False):
        return Exercise.objects.none()
    if user.role == 'admin':
        return Exercise.objects.filter(is_published=True)
    if user.role == 'teacher':
        return Exercise.objects.filter(
            is_published=True,
            lesson__course__teacher=user,
        )
    return Exercise.objects.filter(
        is_published=True,
        lesson__is_published=True,
        lesson__course__is_published=True,
        lesson__course__enrollments__user=user,
    ).distinct()
