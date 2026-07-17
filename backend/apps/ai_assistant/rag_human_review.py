"""Private two-rater review workflow for grounded RAG answer evidence."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re
from statistics import median, quantiles


REVIEW_SCHEMA_VERSION = 1
MAX_REVIEW_FILE_BYTES = 2_000_000
RATER_ID_PATTERN = re.compile(r'^[A-Za-z0-9_-]{1,32}$')
RATING_FIELDS = ('answer_correct', 'evidence_aligned', 'pedagogically_helpful')


class RAGHumanReviewError(ValueError):
    """Safe validation failure for local review artifacts."""


def _validate_rater_id(rater_id: str) -> None:
    if not isinstance(rater_id, str) or not RATER_ID_PATTERN.fullmatch(rater_id):
        raise RAGHumanReviewError(
            'Rater ID must be a pseudonym using letters, numbers, underscore or dash'
        )


def _review_content(report: dict) -> dict:
    dataset = report.get('dataset')
    cases = report.get('cases')
    if not isinstance(dataset, dict) or not isinstance(cases, list) or not cases:
        raise RAGHumanReviewError('Grounded-answer report is invalid')

    items = []
    seen_ids = set()
    for case in cases:
        if not isinstance(case, dict):
            raise RAGHumanReviewError('Grounded-answer case is invalid')
        case_id = case.get('id')
        question = case.get('question')
        answer = case.get('answer')
        citations = case.get('citations')
        if (
            not isinstance(case_id, str)
            or not case_id
            or case_id in seen_ids
            or not isinstance(question, str)
            or not question
            or not isinstance(answer, str)
            or not answer
            or not isinstance(citations, list)
        ):
            raise RAGHumanReviewError(
                'Review export requires unique cases with bounded questions and answers'
            )
        seen_ids.add(case_id)
        safe_citations = []
        for citation in citations:
            if not isinstance(citation, dict):
                raise RAGHumanReviewError('Review citation is invalid')
            excerpt = citation.get('excerpt', '')
            if not isinstance(excerpt, str) or len(excerpt) > 1000:
                raise RAGHumanReviewError('Review citation excerpt is invalid')
            safe_citations.append({
                'lesson_title': str(citation.get('lesson_title', ''))[:200],
                'location': citation.get('location'),
                'excerpt': excerpt,
            })
        items.append({
            'case_id': case_id,
            'tags': case.get('tags', []),
            'question': question[:1000],
            'answer': answer[:2000],
            'grounded': bool(case.get('actual_grounded')),
            'citations': safe_citations,
        })

    return {
        'schema_version': REVIEW_SCHEMA_VERSION,
        'dataset': dataset,
        'lesson_id': report.get('lesson_id'),
        'items': items,
    }


def _package_digest(content: dict) -> str:
    encoded = json.dumps(
        content, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
    ).encode('utf-8')
    return sha256(encoded).hexdigest()


def build_rag_review_template(*, report: dict, rater_id: str) -> dict:
    """Create one independent review sheet from a single provider run."""

    _validate_rater_id(rater_id)
    content = _review_content(report)
    items = []
    for item in content['items']:
        items.append({
            **item,
            'answer_correct': None,
            'evidence_aligned': None,
            'pedagogically_helpful': None,
            'clarity': None,
            'notes': '',
        })
    return {
        'schema_version': REVIEW_SCHEMA_VERSION,
        'dataset': content['dataset'],
        'lesson_id': content['lesson_id'],
        'package_sha256': _package_digest(content),
        'rater_id': rater_id,
        'instructions': (
            'Review independently. Fill the three binary fields with true/false, '
            'clarity with 1-4, and keep notes non-sensitive.'
        ),
        'handling': 'local_sensitive_demo_output_do_not_commit',
        'items': items,
    }


def serialize_rag_review_template(template: dict) -> tuple[str, str]:
    serialized = json.dumps(template, ensure_ascii=False, indent=2) + '\n'
    return serialized, sha256(serialized.encode('utf-8')).hexdigest()


def _read_review(path: Path) -> dict:
    resolved = path.expanduser().resolve()
    try:
        size = resolved.stat().st_size
    except OSError as exc:
        raise RAGHumanReviewError('Review file does not exist') from exc
    if size <= 0 or size > MAX_REVIEW_FILE_BYTES or resolved.suffix.lower() != '.json':
        raise RAGHumanReviewError('Review file is invalid or too large')
    try:
        payload = json.loads(resolved.read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RAGHumanReviewError('Review file is not valid UTF-8 JSON') from exc
    if not isinstance(payload, dict):
        raise RAGHumanReviewError('Review payload must be an object')
    return payload


def _immutable_content(payload: dict) -> dict:
    items = []
    raw_items = payload.get('items')
    if not isinstance(raw_items, list) or not raw_items:
        raise RAGHumanReviewError('Review items must be a non-empty list')
    for item in raw_items:
        if not isinstance(item, dict):
            raise RAGHumanReviewError('Review item must be an object')
        items.append({
            key: item.get(key)
            for key in ('case_id', 'tags', 'question', 'answer', 'grounded', 'citations')
        })
    return {
        'schema_version': payload.get('schema_version'),
        'dataset': payload.get('dataset'),
        'lesson_id': payload.get('lesson_id'),
        'items': items,
    }


def _validate_completed_review(payload: dict) -> tuple[str, str, dict[str, dict]]:
    if payload.get('schema_version') != REVIEW_SCHEMA_VERSION:
        raise RAGHumanReviewError('Review schema version is invalid')
    rater_id = payload.get('rater_id')
    _validate_rater_id(rater_id)
    content = _immutable_content(payload)
    package_digest = payload.get('package_sha256')
    if package_digest != _package_digest(content):
        raise RAGHumanReviewError('Review package content or digest does not match')

    ratings = {}
    for item in payload['items']:
        case_id = item.get('case_id')
        if not isinstance(case_id, str) or not case_id or case_id in ratings:
            raise RAGHumanReviewError('Review case ID is invalid or duplicated')
        for field in RATING_FIELDS:
            if not isinstance(item.get(field), bool):
                raise RAGHumanReviewError('Review binary ratings are incomplete')
        clarity = item.get('clarity')
        if isinstance(clarity, bool) or not isinstance(clarity, int) or not 1 <= clarity <= 4:
            raise RAGHumanReviewError('Review clarity must be an integer from 1 to 4')
        notes = item.get('notes', '')
        if not isinstance(notes, str) or len(notes) > 500 or '\x00' in notes:
            raise RAGHumanReviewError('Review notes are invalid')
        ratings[case_id] = {
            **{field: item[field] for field in RATING_FIELDS},
            'clarity': clarity,
        }
    return rater_id, package_digest, ratings


def _cohen_kappa(values_a: list[bool], values_b: list[bool]) -> float | None:
    observed = sum(a == b for a, b in zip(values_a, values_b, strict=True)) / len(values_a)
    yes_a = sum(values_a) / len(values_a)
    yes_b = sum(values_b) / len(values_b)
    expected = yes_a * yes_b + (1 - yes_a) * (1 - yes_b)
    if expected == 1:
        return None
    return round((observed - expected) / (1 - expected), 4)


def _clarity_summary(values: list[int]) -> dict:
    if len(values) == 1:
        return {'median': float(values[0]), 'q1': float(values[0]), 'q3': float(values[0])}
    q1, _, q3 = quantiles(values, n=4, method='inclusive')
    return {'median': float(median(values)), 'q1': float(q1), 'q3': float(q3)}


def summarize_rag_reviews(*, rater_a_path: Path, rater_b_path: Path) -> dict:
    """Return agreement aggregates without raw outputs or reviewer identities."""

    rater_a, package_a, ratings_a = _validate_completed_review(_read_review(rater_a_path))
    rater_b, package_b, ratings_b = _validate_completed_review(_read_review(rater_b_path))
    if rater_a == rater_b:
        raise RAGHumanReviewError('Two distinct rater pseudonyms are required')
    if package_a != package_b or set(ratings_a) != set(ratings_b):
        raise RAGHumanReviewError('Reviews must cover the same immutable answer package')

    case_ids = sorted(ratings_a)
    binary_metrics = {}
    for field in RATING_FIELDS:
        values_a = [ratings_a[case_id][field] for case_id in case_ids]
        values_b = [ratings_b[case_id][field] for case_id in case_ids]
        binary_metrics[field] = {
            'percent_agreement': round(
                sum(a == b for a, b in zip(values_a, values_b, strict=True)) / len(case_ids),
                4,
            ),
            'cohen_kappa': _cohen_kappa(values_a, values_b),
            'positive_rate_rater_a': round(sum(values_a) / len(values_a), 4),
            'positive_rate_rater_b': round(sum(values_b) / len(values_b), 4),
        }
    clarity_a = [ratings_a[case_id]['clarity'] for case_id in case_ids]
    clarity_b = [ratings_b[case_id]['clarity'] for case_id in case_ids]
    return {
        'report_schema_version': 1,
        'evaluation_scope': 'independent_grounded_answer_review_agreement',
        'metrics': {
            'case_count': len(case_ids),
            **binary_metrics,
            'clarity_rater_a': _clarity_summary(clarity_a),
            'clarity_rater_b': _clarity_summary(clarity_b),
        },
        'limitations': [
            'aggregate_contains_no_raw_answers_ratings_or_rater_identity',
            'agreement_does_not_establish_correctness_or_learning_impact',
            'adjudication_is_still_required_for_final_quality_labels',
        ],
    }
