import json
import os
from io import StringIO
from pathlib import Path

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.users.models import User

from .assessment_evaluation import (
    AssessmentEvaluationError,
    build_assessment_software_baseline,
    build_review_template,
    summarize_independent_reviews,
)
from .models import LessonAssessment
from .scoring import calculate_assessment_score


DOCS_ROOT = next(
    candidate
    for candidate in (
        Path(__file__).resolve().parents[3] / 'docs',
        Path('/project-docs'),
    )
    if candidate.is_dir()
)


def create_teacher(**overrides):
    values = {
        'email': 'e2.teacher@example.invalid',
        'username': 'e2-teacher',
        'full_name': 'E2 Teacher',
        'role': 'teacher',
        'is_active': True,
        'is_verified': True,
    }
    values.update(overrides)
    return User.objects.create_user(password='LocalTestOnly-123!', **values)


def import_e2_data(teacher):
    call_command(
        'import_learning_corpus',
        teacher_id=teacher.id,
        source_root=DOCS_ROOT,
        stdout=StringIO(),
    )
    call_command(
        'import_corpus_assessments',
        teacher_id=teacher.id,
        stdout=StringIO(),
    )


def completed_review(rater_id, *, disagree_item=None):
    payload = build_review_template(rater_id=rater_id)
    for item in payload['items']:
        item['answer_key_valid'] = item['item_id'] != disagree_item
        item['objective_aligned'] = item['item_id'] != disagree_item
        item['clarity'] = 2 if item['item_id'] == disagree_item else 4
        item['notes'] = ''
    return payload


def write_json(path, payload):
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')


def test_shared_scoring_covers_threshold_boundary_and_invalid_inputs():
    passing = calculate_assessment_score(
        correct_answers=7,
        total_questions=9,
        pass_threshold=70,
    )
    failing = calculate_assessment_score(
        correct_answers=6,
        total_questions=9,
        pass_threshold=70,
    )

    assert str(passing.score) == '77.78'
    assert passing.passed is True
    assert str(failing.score) == '66.67'
    assert failing.passed is False
    with pytest.raises(ValueError, match='inputs are invalid'):
        calculate_assessment_score(
            correct_answers=10,
            total_questions=9,
            pass_threshold=70,
        )


def test_software_baseline_is_balanced_and_omits_answer_keys():
    report = build_assessment_software_baseline(include_cases=True)

    assert report['metrics'] == {
        'assessment_count': 3,
        'question_count': 27,
        'objective_count': 9,
        'response_case_count': 81,
        'correct_case_count': 27,
        'misconception_case_count': 27,
        'blank_case_count': 27,
        'valid_response_count': 54,
        'fixture_contract_accuracy': 1.0,
        'attempt_profile_count': 12,
        'pass_boundary_accuracy': 1.0,
    }
    assert all(item['matched'] for item in report['attempt_profiles'])
    assert all(
        'selected_choice' not in item and 'prompt' not in item
        for item in report['response_cases']
    )


def test_review_template_requires_pseudonym_and_is_explicitly_sensitive():
    template = build_review_template(rater_id='reviewer_a')

    assert len(template['items']) == 27
    assert template['answer_key_included'] is True
    assert template['explanations_included'] is True
    assert all('correct_choice' not in item for item in template['items'])
    assert all(item['proposed_answer'] in item['choices'] for item in template['items'])
    with pytest.raises(AssessmentEvaluationError, match='pseudonym'):
        build_review_template(rater_id='person@example.com')


def test_two_completed_reviews_produce_aggregate_only(tmp_path):
    first_item = build_review_template(rater_id='lookup')['items'][0]['item_id']
    rater_a_path = tmp_path / 'rater-a.json'
    rater_b_path = tmp_path / 'rater-b.json'
    write_json(rater_a_path, completed_review('reviewer_alpha'))
    write_json(
        rater_b_path,
        completed_review('reviewer_beta', disagree_item=first_item),
    )

    report = summarize_independent_reviews(
        rater_a_path=rater_a_path,
        rater_b_path=rater_b_path,
    )

    assert report['metrics']['item_count'] == 27
    assert report['metrics']['answer_key_valid']['percent_agreement'] == round(
        26 / 27, 4
    )
    assert report['metrics']['answer_key_valid']['cohen_kappa'] == 0.0
    assert report['metrics']['objective_aligned']['percent_agreement'] == round(
        26 / 27, 4
    )
    assert report['metrics']['clarity_rater_a']['median'] == 4.0
    assert 'reviewer_alpha' not in json.dumps(report)
    assert 'items' not in report


def test_review_summary_rejects_incomplete_or_same_rater(tmp_path):
    rater_a_path = tmp_path / 'rater-a.json'
    rater_b_path = tmp_path / 'rater-b.json'
    incomplete = completed_review('rater_a')
    incomplete['items'][0]['clarity'] = None
    write_json(rater_a_path, incomplete)
    write_json(rater_b_path, completed_review('rater_b'))

    with pytest.raises(AssessmentEvaluationError, match='clarity'):
        summarize_independent_reviews(
            rater_a_path=rater_a_path,
            rater_b_path=rater_b_path,
        )

    write_json(rater_a_path, completed_review('same_rater'))
    write_json(rater_b_path, completed_review('same_rater'))
    with pytest.raises(AssessmentEvaluationError, match='distinct'):
        summarize_independent_reviews(
            rater_a_path=rater_a_path,
            rater_b_path=rater_b_path,
        )


@pytest.mark.django_db
def test_evaluation_command_verifies_database_and_exports_private_template(
    tmp_path,
):
    teacher = create_teacher()
    import_e2_data(teacher)
    output = StringIO()
    review_path = tmp_path / 'reviewer-a.json'

    call_command(
        'evaluate_corpus_assessments',
        teacher_id=teacher.id,
        export_review_template=review_path,
        rater_id='reviewer_a',
        confirm_answer_key_export=True,
        stdout=output,
    )

    report = json.loads(output.getvalue())
    exported = json.loads(review_path.read_text(encoding='utf-8'))
    assert report['database_scope']['blueprint_match'] is True
    assert len(report['database_scope']['records']) == 3
    assert report['review_template_export']['answer_key_included'] is True
    assert exported['rater_id'] == 'reviewer_a'
    assert oct(os.stat(review_path).st_mode & 0o777) == '0o600'


@pytest.mark.django_db
def test_evaluation_command_requires_explicit_answer_key_export_confirmation(
    tmp_path,
):
    teacher = create_teacher()
    import_e2_data(teacher)

    with pytest.raises(CommandError, match='confirm-answer-key-export'):
        call_command(
            'evaluate_corpus_assessments',
            teacher_id=teacher.id,
            export_review_template=tmp_path / 'review.json',
            rater_id='reviewer_a',
            stdout=StringIO(),
        )

    assert not (tmp_path / 'review.json').exists()


@pytest.mark.django_db
def test_evaluation_command_rejects_non_owner_and_changed_assessment():
    teacher = create_teacher()
    other_teacher = create_teacher(
        email='other.e2.teacher@example.invalid',
        username='other-e2-teacher',
    )
    import_e2_data(teacher)

    with pytest.raises(CommandError, match='unavailable'):
        call_command(
            'evaluate_corpus_assessments',
            teacher_id=other_teacher.id,
            stdout=StringIO(),
        )

    assessment = LessonAssessment.objects.get(
        lesson__slug='tong-quan-va-mo-hinh-mang'
    )
    assessment.pass_threshold = 80
    assessment.save(update_fields=['pass_threshold', 'updated_at'])
    with pytest.raises(CommandError, match='does not match'):
        call_command(
            'evaluate_corpus_assessments',
            teacher_id=teacher.id,
            stdout=StringIO(),
        )
