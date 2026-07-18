"""Privacy-bounded E2 software baseline and independent-rater aggregation."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
from statistics import median, quantiles

from .assessment_blueprints import (
    ASSESSMENT_BLUEPRINTS,
    BLUEPRINT_REVISION,
    validate_assessment_blueprints,
)
from .scoring import calculate_assessment_score


E2_SCHEMA_VERSION = 1
E2_DATASET_ID = 'intaaneto-corpus-assessment-e2'
E2_DATASET_VERSION = '1.0.0'
MAX_REVIEW_FILE_BYTES = 1_000_000
RATER_ID_PATTERN = re.compile(r'^[A-Za-z0-9_-]{1,32}$')


class AssessmentEvaluationError(ValueError):
    """Safe validation failure for checked-in or local E2 evidence."""


def _item_id(blueprint, question) -> str:
    return f'{blueprint.lesson_slug}:q{question.order:02d}'


def _dataset_metadata() -> dict:
    return {
        'id': E2_DATASET_ID,
        'version': E2_DATASET_VERSION,
        'schema_version': E2_SCHEMA_VERSION,
        'blueprint_revision': BLUEPRINT_REVISION,
    }


def build_assessment_software_baseline(
    blueprints=ASSESSMENT_BLUEPRINTS,
    *,
    include_cases: bool = False,
) -> dict:
    """Exercise shared deterministic scoring over balanced synthetic cases."""

    blueprints = validate_assessment_blueprints(tuple(blueprints))
    response_cases = []
    profiles = []
    consistency_matches = 0
    valid_response_count = 0

    for blueprint in blueprints:
        total_questions = len(blueprint.questions)
        minimum_correct = (
            blueprint.pass_threshold * total_questions + 99
        ) // 100
        profile_specs = (
            ('all-correct', total_questions),
            ('threshold-pass', minimum_correct),
            ('below-threshold', max(0, minimum_correct - 1)),
            ('all-misconception', 0),
        )
        for profile_name, correct_answers in profile_specs:
            scoring = calculate_assessment_score(
                correct_answers=correct_answers,
                total_questions=total_questions,
                pass_threshold=blueprint.pass_threshold,
            )
            expected_pass = correct_answers >= minimum_correct
            profiles.append({
                'id': f'{blueprint.lesson_slug}:{profile_name}',
                'lesson_slug': blueprint.lesson_slug,
                'correct_answers': correct_answers,
                'total_questions': total_questions,
                'score': str(scoring.score),
                'passed': scoring.passed,
                'expected_pass': expected_pass,
                'matched': scoring.passed is expected_pass,
            })

        for question in blueprint.questions:
            misconception_choice = (question.correct_choice + 1) % len(
                question.choices
            )
            case_specs = (
                ('correct', question.correct_choice, True, True),
                ('misconception', misconception_choice, False, True),
                ('blank', None, None, False),
            )
            for response_type, selected_choice, expected_correct, is_valid in case_specs:
                observed_correct = (
                    selected_choice == question.correct_choice
                    if is_valid
                    else None
                )
                matched = observed_correct is expected_correct
                consistency_matches += int(matched)
                valid_response_count += int(is_valid)
                response_cases.append({
                    'id': f'{_item_id(blueprint, question)}:{response_type}',
                    'lesson_slug': blueprint.lesson_slug,
                    'assessment_version': 1,
                    'question_order': question.order,
                    'declared_objective': question.learning_objective,
                    'response_type': response_type,
                    'submission_valid': is_valid,
                    'server_is_correct': observed_correct,
                    'matched_fixture_contract': matched,
                })

    question_count = sum(len(item.questions) for item in blueprints)
    profile_matches = sum(item['matched'] for item in profiles)
    report = {
        'dataset': _dataset_metadata(),
        'evaluation_scope': 'deterministic_assessment_software_baseline',
        'configuration': {'response_cases_included': include_cases},
        'metrics': {
            'assessment_count': len(blueprints),
            'question_count': question_count,
            'objective_count': sum(len(item.objectives) for item in blueprints),
            'response_case_count': len(response_cases),
            'correct_case_count': question_count,
            'misconception_case_count': question_count,
            'blank_case_count': question_count,
            'valid_response_count': valid_response_count,
            'fixture_contract_accuracy': round(
                consistency_matches / len(response_cases), 4
            ),
            'attempt_profile_count': len(profiles),
            'pass_boundary_accuracy': round(
                profile_matches / len(profiles), 4
            ),
        },
        'limitations': [
            'synthetic_cases_are_not_learner_outcomes',
            'blank_rows_document_rejection_and_are_not_scored_attempts',
            'teacher_review_and_two_independent_raters_are_still_required',
        ],
        'attempt_profiles': profiles,
    }
    if include_cases:
        report['response_cases'] = response_cases
    return report


def build_review_template(*, rater_id: str) -> dict:
    """Create a local teacher-review sheet with proposed answers."""

    if not RATER_ID_PATTERN.fullmatch(rater_id):
        raise AssessmentEvaluationError(
            'Rater ID must be a pseudonym using letters, numbers, underscore or dash'
        )
    blueprints = validate_assessment_blueprints()
    items = []
    for blueprint in blueprints:
        for question in blueprint.questions:
            items.append({
                'item_id': _item_id(blueprint, question),
                'course_slug': blueprint.course_slug,
                'lesson_slug': blueprint.lesson_slug,
                'question_order': question.order,
                'prompt': question.prompt,
                'choices': list(question.choices),
                'proposed_answer': question.choices[question.correct_choice],
                'declared_objective': question.learning_objective,
                'explanation': question.explanation,
                'answer_key_valid': None,
                'objective_aligned': None,
                'clarity': None,
                'notes': '',
            })
    return {
        'dataset': _dataset_metadata(),
        'rater_id': rater_id,
        'instructions': (
            'Review independently. Fill answer_key_valid and objective_aligned '
            'with true/false, clarity with 1-4, and keep notes non-sensitive.'
        ),
        'answer_key_included': True,
        'explanations_included': True,
        'handling': 'local_sensitive_authoring_data_do_not_commit_or_share_with_learners',
        'items': items,
    }


def serialize_review_template(template: dict) -> tuple[str, str]:
    serialized = json.dumps(template, ensure_ascii=False, indent=2) + '\n'
    return serialized, sha256(serialized.encode('utf-8')).hexdigest()


def _read_review(path: Path) -> dict:
    resolved = path.expanduser().resolve()
    try:
        size = resolved.stat().st_size
    except OSError as exc:
        raise AssessmentEvaluationError('Review file does not exist') from exc
    if size <= 0 or size > MAX_REVIEW_FILE_BYTES or resolved.suffix.lower() != '.json':
        raise AssessmentEvaluationError('Review file is invalid or too large')
    try:
        payload = json.loads(resolved.read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AssessmentEvaluationError('Review file is not valid UTF-8 JSON') from exc
    if not isinstance(payload, dict):
        raise AssessmentEvaluationError('Review payload must be an object')
    return payload


def _validate_completed_review(payload: dict) -> tuple[str, dict[str, dict]]:
    if payload.get('dataset') != _dataset_metadata():
        raise AssessmentEvaluationError('Review dataset metadata does not match')
    rater_id = payload.get('rater_id')
    if not isinstance(rater_id, str) or not RATER_ID_PATTERN.fullmatch(rater_id):
        raise AssessmentEvaluationError('Review rater ID is invalid')
    raw_items = payload.get('items')
    if not isinstance(raw_items, list):
        raise AssessmentEvaluationError('Review items must be a list')

    expected_ids = {
        item['item_id'] for item in build_review_template(rater_id='expected')['items']
    }
    ratings = {}
    for item in raw_items:
        if not isinstance(item, dict):
            raise AssessmentEvaluationError('Review item must be an object')
        item_id = item.get('item_id')
        if not isinstance(item_id, str) or item_id in ratings:
            raise AssessmentEvaluationError('Review item ID is invalid or duplicated')
        answer_key_valid = item.get('answer_key_valid')
        objective_aligned = item.get('objective_aligned')
        clarity = item.get('clarity')
        notes = item.get('notes', '')
        if not isinstance(answer_key_valid, bool) or not isinstance(
            objective_aligned, bool
        ):
            raise AssessmentEvaluationError('Review binary ratings are incomplete')
        if isinstance(clarity, bool) or not isinstance(clarity, int) or not 1 <= clarity <= 4:
            raise AssessmentEvaluationError('Review clarity must be an integer from 1 to 4')
        if not isinstance(notes, str) or len(notes) > 500 or '\x00' in notes:
            raise AssessmentEvaluationError('Review notes are invalid')
        ratings[item_id] = {
            'answer_key_valid': answer_key_valid,
            'objective_aligned': objective_aligned,
            'clarity': clarity,
        }
    if set(ratings) != expected_ids:
        raise AssessmentEvaluationError('Review must contain every expected item once')
    return rater_id, ratings


def _cohen_kappa(values_a: list[bool], values_b: list[bool]) -> float | None:
    observed = sum(a == b for a, b in zip(values_a, values_b, strict=True)) / len(
        values_a
    )
    yes_a = sum(values_a) / len(values_a)
    yes_b = sum(values_b) / len(values_b)
    expected = yes_a * yes_b + (1 - yes_a) * (1 - yes_b)
    if expected == 1:
        return None
    return round((observed - expected) / (1 - expected), 4)


def _clarity_summary(values: list[int]) -> dict:
    q1, _, q3 = quantiles(values, n=4, method='inclusive')
    return {
        'median': float(median(values)),
        'q1': float(q1),
        'q3': float(q3),
    }


def summarize_independent_reviews(*, rater_a_path: Path, rater_b_path: Path) -> dict:
    """Validate two completed sheets and return aggregate agreement only."""

    rater_a, ratings_a = _validate_completed_review(_read_review(rater_a_path))
    rater_b, ratings_b = _validate_completed_review(_read_review(rater_b_path))
    if rater_a == rater_b:
        raise AssessmentEvaluationError('Two distinct rater pseudonyms are required')

    item_ids = sorted(ratings_a)
    binary_metrics = {}
    for field in ('answer_key_valid', 'objective_aligned'):
        values_a = [ratings_a[item_id][field] for item_id in item_ids]
        values_b = [ratings_b[item_id][field] for item_id in item_ids]
        binary_metrics[field] = {
            'percent_agreement': round(
                sum(a == b for a, b in zip(values_a, values_b, strict=True))
                / len(item_ids),
                4,
            ),
            'cohen_kappa': _cohen_kappa(values_a, values_b),
            'positive_rate_rater_a': round(sum(values_a) / len(values_a), 4),
            'positive_rate_rater_b': round(sum(values_b) / len(values_b), 4),
        }

    clarity_a = [ratings_a[item_id]['clarity'] for item_id in item_ids]
    clarity_b = [ratings_b[item_id]['clarity'] for item_id in item_ids]
    return {
        'dataset': _dataset_metadata(),
        'evaluation_scope': 'independent_question_review_agreement',
        'metrics': {
            'item_count': len(item_ids),
            **binary_metrics,
            'clarity_rater_a': _clarity_summary(clarity_a),
            'clarity_rater_b': _clarity_summary(clarity_b),
        },
        'limitations': [
            'aggregate_contains_no_raw_ratings_or_rater_identity',
            'adjudication_and_server_accuracy_are_not_computed',
            'agreement_does_not_measure_learning_impact',
        ],
    }
