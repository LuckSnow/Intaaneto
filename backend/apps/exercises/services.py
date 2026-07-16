from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.courses.models import Enrollment
from apps.courses.services import complete_lesson, recalculate_enrollment_mastery

from .models import AssessmentAnswer, AssessmentAttempt


@transaction.atomic
def grade_assessment(*, assessment, user, submitted_answers):
    """Validate and deterministically grade one immutable learner attempt."""

    if user.role != 'student':
        raise PermissionDenied('Chỉ học viên mới có thể nộp bài đánh giá.')
    if (
        not assessment.is_published
        or not assessment.lesson.is_published
        or not assessment.lesson.course.is_published
    ):
        raise PermissionDenied('Bài đánh giá chưa sẵn sàng.')

    try:
        enrollment = Enrollment.objects.select_for_update().get(
            user=user,
            course=assessment.lesson.course,
        )
    except Enrollment.DoesNotExist as exc:
        raise PermissionDenied('Bạn chưa đăng ký khóa học này.') from exc

    questions = list(assessment.questions.all().order_by('order', 'id'))
    if not questions:
        raise ValidationError({'answers': 'Bài đánh giá chưa có câu hỏi.'})

    answers_by_id = {
        answer['question_id']: answer['selected_choice']
        for answer in submitted_answers
    }
    expected_ids = {question.id for question in questions}
    if set(answers_by_id) != expected_ids:
        raise ValidationError({
            'answers': 'Cần trả lời đầy đủ và chỉ gửi câu hỏi thuộc bài đánh giá này.'
        })

    answer_rows = []
    correct_answers = 0
    weak_objectives = []
    for question in questions:
        selected_choice = answers_by_id[question.id]
        if selected_choice >= len(question.choices):
            raise ValidationError({
                'answers': f'Lựa chọn của câu hỏi {question.id} không hợp lệ.'
            })
        is_correct = selected_choice == question.correct_choice
        if is_correct:
            correct_answers += 1
        else:
            objective = question.learning_objective.strip() or 'Nội dung bài học'
            if objective not in weak_objectives:
                weak_objectives.append(objective)
        answer_rows.append((question, selected_choice, is_correct))

    score = (
        Decimal(correct_answers * 100) / Decimal(len(questions))
    ).quantize(Decimal('0.01'))
    passed = score >= Decimal(assessment.pass_threshold)
    attempt = AssessmentAttempt.objects.create(
        assessment=assessment,
        user=user,
        assessment_version=assessment.version,
        threshold_snapshot=assessment.pass_threshold,
        score=score,
        passed=passed,
        total_questions=len(questions),
        correct_answers=correct_answers,
        weak_objectives=weak_objectives,
    )
    AssessmentAnswer.objects.bulk_create([
        AssessmentAnswer(
            attempt=attempt,
            question=question,
            prompt_snapshot=question.prompt,
            choices_snapshot=question.choices,
            learning_objective_snapshot=question.learning_objective,
            selected_choice=selected_choice,
            correct_choice_snapshot=question.correct_choice,
            is_correct=is_correct,
        )
        for question, selected_choice, is_correct in answer_rows
    ])

    mastery_percentage = recalculate_enrollment_mastery(enrollment)
    progression = None
    if passed:
        progression = complete_lesson(user=user, lesson=assessment.lesson)

    return attempt, mastery_percentage, progression
