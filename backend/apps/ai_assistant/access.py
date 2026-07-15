"""Server-owned lesson scopes shared by chat and RAG services."""

from django.db.models import Q

from apps.courses.models import Lesson


def accessible_lesson_queryset(actor):
    """Return lessons the authenticated actor may read or use for AI/RAG."""

    if not getattr(actor, 'is_authenticated', False):
        return Lesson.objects.none()
    if actor.role == 'admin':
        return Lesson.objects.all()
    if actor.role == 'teacher':
        return Lesson.objects.filter(
            Q(course__teacher=actor) | Q(course__enrollments__user=actor)
        ).distinct()
    return Lesson.objects.filter(
        Q(course__enrollments__user=actor)
        | Q(is_preview=True, is_published=True, course__is_published=True)
    ).distinct()
