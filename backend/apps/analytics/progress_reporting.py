"""Read-only progress reports derived from authoritative learning records."""

from __future__ import annotations

from decimal import Decimal

from django.db.models import Avg, Count, F, Max, OuterRef, Q, Subquery
from django.shortcuts import get_object_or_404

from apps.courses.models import Course, Enrollment, LessonProgress
from apps.courses.services import available_lessons
from apps.exercises.models import AssessmentAnswer, AssessmentAttempt, LessonAssessment


MAX_LEARNER_COURSES = 100


def _decimal(value):
    return (value or Decimal('0.00')).quantize(Decimal('0.01'))


def learner_progress_report(user):
    """Return only the authenticated learner's current progress evidence."""

    enrollments = list(
        Enrollment.objects.filter(user=user)
        .select_related('course', 'last_accessed_lesson')
        .order_by('-enrolled_at', '-id')[:MAX_LEARNER_COURSES]
    )
    enrollment_queryset = Enrollment.objects.filter(user=user)
    enrollment_aggregate = enrollment_queryset.aggregate(
        average_progress=Avg('progress_percentage'),
        average_mastery=Avg('mastery_percentage'),
    )
    current_attempts_all = AssessmentAttempt.objects.filter(
        user=user,
        assessment__is_published=True,
        assessment__lesson__is_published=True,
        assessment_version=F('assessment__version'),
    )
    courses = []
    for enrollment in enrollments:
        course = enrollment.course
        available_ids = [lesson.id for lesson in available_lessons(course)]
        completed_lessons = LessonProgress.objects.filter(
            user=user,
            lesson_id__in=available_ids,
            is_completed=True,
        ).count()
        assessments = LessonAssessment.objects.filter(
            lesson__course=course,
            lesson__is_published=True,
            is_published=True,
        )
        current_attempts = AssessmentAttempt.objects.filter(
            user=user,
            assessment__in=assessments,
            assessment_version=F('assessment__version'),
        )
        attempted = current_attempts.values('assessment_id').distinct().count()
        passed = current_attempts.filter(passed=True).values(
            'assessment_id'
        ).distinct().count()
        courses.append({
            'course_id': course.id,
            'course_title': course.title,
            'progress_percentage': enrollment.progress_percentage,
            'mastery_percentage': enrollment.mastery_percentage,
            'lessons_completed': completed_lessons,
            'lessons_available': len(available_ids),
            'assessments_published': assessments.count(),
            'assessments_attempted': attempted,
            'assessments_passed': passed,
            'last_accessed_lesson': (
                {
                    'id': enrollment.last_accessed_lesson_id,
                    'title': enrollment.last_accessed_lesson.title,
                }
                if enrollment.last_accessed_lesson else None
            ),
            'enrolled_at': enrollment.enrolled_at,
            'completed_at': enrollment.completed_at,
        })

    enrollment_count = enrollment_queryset.count()
    return {
        'scope': 'learner',
        'summary': {
            'courses_enrolled': enrollment_count,
            'courses_completed': enrollment_queryset.filter(
                completed_at__isnull=False
            ).count(),
            'lessons_completed': LessonProgress.objects.filter(
                user=user,
                is_completed=True,
                lesson__course__enrollments__user=user,
            ).distinct().count(),
            'assessments_attempted': current_attempts_all.values(
                'assessment_id'
            ).distinct().count(),
            'assessments_passed': current_attempts_all.filter(
                passed=True
            ).values('assessment_id').distinct().count(),
            'average_progress_percentage': _decimal(
                enrollment_aggregate['average_progress']
            ),
            'average_mastery_percentage': _decimal(
                enrollment_aggregate['average_mastery']
            ),
        },
        'courses': courses,
        'truncated_courses': max(0, enrollment_count - len(enrollments)),
    }


def _teaching_courses(actor):
    queryset = Course.objects.all() if actor.role == 'admin' else Course.objects.filter(
        teacher=actor
    )
    return queryset.order_by('order', '-created_at', 'id')


def teaching_objective_report(*, actor, course_id, limit=100):
    """Aggregate latest current-version answers by teacher-authored objective."""

    course = get_object_or_404(_teaching_courses(actor), pk=course_id)
    current_attempts = AssessmentAttempt.objects.filter(
        assessment__lesson__course=course,
        assessment__is_published=True,
        assessment__lesson__is_published=True,
        assessment_version=F('assessment__version'),
    )
    latest_attempt_id = current_attempts.filter(
        user_id=OuterRef('user_id'),
        assessment_id=OuterRef('assessment_id'),
    ).order_by('-submitted_at', '-id').values('id')[:1]
    latest_attempts = current_attempts.annotate(
        latest_attempt_id=Subquery(latest_attempt_id)
    ).filter(id=F('latest_attempt_id'))
    answers = AssessmentAnswer.objects.filter(
        attempt__in=latest_attempts,
    ).exclude(learning_objective_snapshot='')
    grouped = answers.values('learning_objective_snapshot').annotate(
        answer_count=Count('id'),
        correct_count=Count('id', filter=Q(is_correct=True)),
        learner_count=Count('attempt__user_id', distinct=True),
        learners_needing_review=Count(
            'attempt__user_id',
            filter=Q(is_correct=False),
            distinct=True,
        ),
    ).order_by('-learners_needing_review', 'learning_objective_snapshot')
    total = grouped.count()
    rows = list(grouped[:limit])

    return {
        'scope': 'teaching_objectives',
        'course': {
            'course_id': course.id,
            'course_title': course.title,
        },
        'objectives': [
            {
                'learning_objective': row['learning_objective_snapshot'],
                'learner_count': row['learner_count'],
                'learners_needing_review': row['learners_needing_review'],
                'answer_count': row['answer_count'],
                'correct_count': row['correct_count'],
                'correct_rate_percentage': _decimal(
                    Decimal(row['correct_count'] * 100) / Decimal(row['answer_count'])
                ),
            }
            for row in rows
        ],
        'pagination': {
            'count': total,
            'limit': limit,
            'truncated': total > len(rows),
        },
        'method': 'latest_current_version_attempt_per_learner_assessment',
    }


def teaching_progress_report(*, actor, course_id=None, limit=50, offset=0):
    """Return aggregate owned-course reports or one paged learner roster."""

    queryset = _teaching_courses(actor)
    if course_id is None:
        total = queryset.count()
        courses = list(
            queryset.annotate(
                learner_count=Count('enrollments', distinct=True),
                completed_count=Count(
                    'enrollments',
                    filter=Q(enrollments__completed_at__isnull=False),
                    distinct=True,
                ),
                average_progress=Avg('enrollments__progress_percentage'),
                average_mastery=Avg('enrollments__mastery_percentage'),
            )[offset:offset + limit]
        )
        return {
            'scope': 'teaching',
            'summary': {
                'courses': total,
                'learners': Enrollment.objects.filter(
                    course__in=queryset
                ).values('user_id').distinct().count(),
                'course_completions': Enrollment.objects.filter(
                    course__in=queryset,
                    completed_at__isnull=False,
                ).count(),
            },
            'courses': [
                {
                    'course_id': course.id,
                    'course_title': course.title,
                    'is_published': course.is_published,
                    'learner_count': course.learner_count,
                    'completed_count': course.completed_count,
                    'average_progress_percentage': _decimal(course.average_progress),
                    'average_mastery_percentage': _decimal(course.average_mastery),
                }
                for course in courses
            ],
            'pagination': {
                'count': total,
                'limit': limit,
                'offset': offset,
            },
        }

    course = get_object_or_404(queryset, pk=course_id)
    enrollments = Enrollment.objects.filter(course=course).select_related(
        'user', 'last_accessed_lesson'
    ).order_by('user__full_name', 'user_id')
    total = enrollments.count()
    page = list(enrollments[offset:offset + limit])
    learner_ids = [enrollment.user_id for enrollment in page]
    attempt_stats = {
        row['user_id']: row
        for row in AssessmentAttempt.objects.filter(
            user_id__in=learner_ids,
            assessment__lesson__course=course,
            assessment__is_published=True,
            assessment_version=F('assessment__version'),
        ).values('user_id').annotate(
            attempts=Count('id'),
            assessments_attempted=Count('assessment_id', distinct=True),
            assessments_passed=Count(
                'assessment_id',
                filter=Q(passed=True),
                distinct=True,
            ),
            latest_attempt_at=Max('submitted_at'),
        )
    }
    return {
        'scope': 'teaching_course',
        'course': {
            'course_id': course.id,
            'course_title': course.title,
            'is_published': course.is_published,
        },
        'learners': [
            {
                'user_id': enrollment.user_id,
                'full_name': enrollment.user.full_name,
                'progress_percentage': enrollment.progress_percentage,
                'mastery_percentage': enrollment.mastery_percentage,
                'completed_at': enrollment.completed_at,
                'last_accessed_lesson': (
                    {
                        'id': enrollment.last_accessed_lesson_id,
                        'title': enrollment.last_accessed_lesson.title,
                    }
                    if enrollment.last_accessed_lesson else None
                ),
                'assessment_attempts': attempt_stats.get(
                    enrollment.user_id, {}
                ).get('attempts', 0),
                'assessments_attempted': attempt_stats.get(
                    enrollment.user_id, {}
                ).get('assessments_attempted', 0),
                'assessments_passed': attempt_stats.get(
                    enrollment.user_id, {}
                ).get('assessments_passed', 0),
                'latest_assessment_at': attempt_stats.get(
                    enrollment.user_id, {}
                ).get('latest_attempt_at'),
            }
            for enrollment in page
        ],
        'pagination': {
            'count': total,
            'limit': limit,
            'offset': offset,
        },
    }
