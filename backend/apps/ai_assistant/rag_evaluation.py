"""Repeatable retrieval evaluation for the bundled Vietnamese RAG dataset."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings

from .rag_services import (
    EmbeddingProvider,
    FastEmbedEmbeddingProvider,
    retrieve_lesson_evidence,
)


DATASET_SCHEMA_VERSION = 1
DEFAULT_DATASET_PATH = (
    Path(__file__).parent / 'fixtures' / 'retrieval_evaluation_vi_v1.json'
)


class EvaluationDatasetError(ValueError):
    """Raised when a checked-in evaluation dataset has an invalid contract."""


@dataclass(frozen=True)
class RetrievalEvaluationCase:
    case_id: str
    question: str
    answerable: bool
    expected_text: str | None
    tags: tuple[str, ...]


@dataclass(frozen=True)
class RetrievalEvaluationDataset:
    dataset_id: str
    version: str
    lesson_slug: str
    cases: tuple[RetrievalEvaluationCase, ...]


def _validate_dataset_metadata(payload: dict) -> None:
    required_strings = ('dataset_id', 'version', 'lesson_slug')
    for field in required_strings:
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            raise EvaluationDatasetError('Evaluation dataset metadata is invalid')


def _parse_evaluation_case(raw_case: object) -> RetrievalEvaluationCase:
    if not isinstance(raw_case, dict):
        raise EvaluationDatasetError('Evaluation case must be an object')
    case_id = raw_case.get('id')
    question = raw_case.get('question')
    answerable = raw_case.get('answerable')
    expected_text = raw_case.get('expected_text')
    tags = raw_case.get('tags', [])
    if not isinstance(case_id, str) or not case_id.strip():
        raise EvaluationDatasetError('Evaluation case ID is invalid')
    if not isinstance(question, str) or not question.strip():
        raise EvaluationDatasetError('Evaluation case question is invalid')
    if not isinstance(answerable, bool):
        raise EvaluationDatasetError('Evaluation case answerable flag is invalid')
    has_expected_text = isinstance(expected_text, str) and bool(expected_text.strip())
    if answerable != has_expected_text:
        raise EvaluationDatasetError(
            'Answerable cases require expected_text; unsupported cases must omit it'
        )
    if not isinstance(tags, list) or not all(
        isinstance(tag, str) and tag.strip() for tag in tags
    ):
        raise EvaluationDatasetError('Evaluation case tags are invalid')
    return RetrievalEvaluationCase(
        case_id=case_id,
        question=question.strip(),
        answerable=answerable,
        expected_text=expected_text.strip() if expected_text else None,
        tags=tuple(tags),
    )


def load_retrieval_evaluation_dataset(
    path: Path = DEFAULT_DATASET_PATH,
) -> RetrievalEvaluationDataset:
    """Load and strictly validate the versioned bundled dataset."""

    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvaluationDatasetError('Evaluation dataset could not be loaded') from exc

    if not isinstance(payload, dict):
        raise EvaluationDatasetError('Evaluation dataset must be an object')
    if payload.get('schema_version') != DATASET_SCHEMA_VERSION:
        raise EvaluationDatasetError('Unsupported evaluation dataset schema version')

    _validate_dataset_metadata(payload)

    raw_cases = payload.get('cases')
    if not isinstance(raw_cases, list) or not raw_cases:
        raise EvaluationDatasetError('Evaluation dataset must contain cases')

    cases = [_parse_evaluation_case(raw_case) for raw_case in raw_cases]
    case_ids = [case.case_id for case in cases]
    if len(set(case_ids)) != len(case_ids):
        raise EvaluationDatasetError('Evaluation case IDs must be unique strings')

    return RetrievalEvaluationDataset(
        dataset_id=payload['dataset_id'],
        version=payload['version'],
        lesson_slug=payload['lesson_slug'],
        cases=tuple(cases),
    )


def evaluate_lesson_retrieval(
    *,
    actor,
    lesson,
    dataset: RetrievalEvaluationDataset,
    provider: EmbeddingProvider | None = None,
) -> dict:
    """Evaluate authorized retrieval without invoking an answer-generation model."""

    if lesson.slug != dataset.lesson_slug:
        raise EvaluationDatasetError(
            'Evaluation dataset does not match the selected lesson'
        )

    provider = provider or FastEmbedEmbeddingProvider()
    results = []
    answerable_count = 0
    expected_source_hits = 0
    status_matches = 0
    passed_count = 0
    total_latency_ms = 0
    source_versions = set()

    for case in dataset.cases:
        started = time.monotonic()
        retrieval = retrieve_lesson_evidence(
            actor=actor,
            lesson_id=lesson.id,
            question=case.question,
            provider=provider,
        )
        latency_ms = int((time.monotonic() - started) * 1000)
        total_latency_ms += latency_ms
        if retrieval.source_version is not None:
            source_versions.add(retrieval.source_version)

        expected_status = 'ready' if case.answerable else 'weak_evidence'
        status_match = retrieval.status == expected_status
        source_hit = None
        if case.answerable:
            answerable_count += 1
            marker = case.expected_text.casefold()
            source_hit = any(marker in chunk.text.casefold() for chunk in retrieval.chunks)
            expected_source_hits += int(source_hit)

        passed = status_match and (source_hit is not False)
        status_matches += int(status_match)
        passed_count += int(passed)
        results.append({
            'id': case.case_id,
            'tags': list(case.tags),
            'expected_status': expected_status,
            'actual_status': retrieval.status,
            'status_match': status_match,
            'expected_source_hit': source_hit,
            'top_chunk_ordinal': (
                retrieval.chunks[0].ordinal if retrieval.chunks else None
            ),
            'top_score': retrieval.chunks[0].score if retrieval.chunks else None,
            'latency_ms': latency_ms,
            'passed': passed,
        })

    case_count = len(dataset.cases)
    return {
        'dataset': {
            'id': dataset.dataset_id,
            'version': dataset.version,
            'schema_version': DATASET_SCHEMA_VERSION,
        },
        'lesson_id': lesson.id,
        'source_scope': 'authorized_lesson',
        'configuration': {
            'embedding_provider': provider.provider_name,
            'embedding_model': provider.model_name,
            'embedding_revision': provider.model_revision,
            'embedding_dimension': provider.dimension,
            'retrieval_top_k': settings.RAG_RETRIEVAL_TOP_K,
            'minimum_score': settings.RAG_RETRIEVAL_MIN_SCORE,
            'source_versions': sorted(source_versions),
        },
        'metrics': {
            'case_count': case_count,
            'pass_rate': round(passed_count / case_count, 4),
            'status_accuracy': round(status_matches / case_count, 4),
            'expected_source_recall': round(
                expected_source_hits / answerable_count, 4
            ),
            'mean_latency_ms': round(total_latency_ms / case_count, 2),
        },
        'cases': results,
    }
