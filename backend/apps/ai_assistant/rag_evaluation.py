"""Repeatable retrieval evaluation for the bundled Vietnamese RAG dataset."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings

from .rag_answering import answer_lesson_question
from .rag_services import (
    EmbeddingProvider,
    FastEmbedEmbeddingProvider,
    retrieve_lesson_evidence,
)


DATASET_SCHEMA_VERSION = 1
GROUNDED_REPORT_SCHEMA_VERSION = 2
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


def evaluate_grounded_answers(
    *,
    actor,
    lesson,
    dataset: RetrievalEvaluationDataset,
    embedding_provider: EmbeddingProvider | None = None,
    generation_provider=None,
    include_answers: bool = False,
) -> dict:
    """Evaluate the full grounded-answer contract on the versioned dataset.

    Expected-text matching is intentionally reported as a strict lexical proxy,
    not as semantic answer correctness or an educational-quality score.
    """

    if lesson.slug != dataset.lesson_slug:
        raise EvaluationDatasetError(
            'Evaluation dataset does not match the selected lesson'
        )

    results = []
    contract_matches = 0
    citation_matches = 0
    expected_marker_hits = 0
    answerable_count = 0
    refusal_matches = 0
    unsupported_count = 0
    contract_passed_count = 0
    strict_lexical_proxy_passed_count = 0
    total_latency_ms = 0
    total_tokens = 0
    token_measurements = 0

    for case in dataset.cases:
        started = time.monotonic()
        answer = answer_lesson_question(
            actor=actor,
            lesson=lesson,
            messages=[{'role': 'user', 'content': case.question}],
            embedding_provider=embedding_provider,
            generation_provider=generation_provider,
        )
        latency_ms = int((time.monotonic() - started) * 1000)
        total_latency_ms += latency_ms

        if answer.tokens_used is not None:
            total_tokens += answer.tokens_used
            token_measurements += 1

        expected_grounded = case.answerable
        contract_match = answer.grounded is expected_grounded
        contract_matches += int(contract_match)

        selected_ids = {
            item['chunk_id']
            for item in answer.retrieval_metadata.get('retrieval', {}).get(
                'selected_chunks', []
            )
        }
        citation_ids = {item.get('chunk_id') for item in answer.citations}
        citation_match = (
            bool(answer.citations)
            and citation_ids.issubset(selected_ids)
            and all(item.get('lesson_id') == lesson.id for item in answer.citations)
            if answer.grounded
            else not answer.citations
        )
        citation_matches += int(citation_match)

        expected_marker_hit = None
        refusal_match = None
        if case.answerable:
            answerable_count += 1
            expected_marker_hit = (
                case.expected_text.casefold() in answer.answer.casefold()
            )
            expected_marker_hits += int(expected_marker_hit)
        else:
            unsupported_count += 1
            refusal_match = (
                not answer.grounded
                and not answer.citations
                and answer.retrieval.get('status') != 'ready'
            )
            refusal_matches += int(refusal_match)

        contract_passed = (
            contract_match
            and citation_match
            and (True if case.answerable else refusal_match)
        )
        strict_lexical_proxy_passed = contract_passed and (
            expected_marker_hit if case.answerable else True
        )
        contract_passed_count += int(contract_passed)
        strict_lexical_proxy_passed_count += int(strict_lexical_proxy_passed)
        result = {
            'id': case.case_id,
            'tags': list(case.tags),
            'expected_grounded': expected_grounded,
            'actual_grounded': answer.grounded,
            'retrieval_status': answer.retrieval.get('status'),
            'contract_match': contract_match,
            'citation_match': citation_match,
            'citation_count': len(answer.citations),
            'expected_marker_hit': expected_marker_hit,
            'refusal_match': refusal_match,
            'latency_ms': latency_ms,
            'tokens_used': answer.tokens_used,
            'contract_passed': contract_passed,
            'strict_lexical_proxy_passed': strict_lexical_proxy_passed,
        }
        if include_answers:
            result['question'] = case.question
            result['answer'] = answer.answer[:2000]
        results.append(result)

    case_count = len(dataset.cases)
    return {
        'report_schema_version': GROUNDED_REPORT_SCHEMA_VERSION,
        'dataset': {
            'id': dataset.dataset_id,
            'version': dataset.version,
            'schema_version': DATASET_SCHEMA_VERSION,
        },
        'lesson_id': lesson.id,
        'source_scope': 'authorized_lesson',
        'evaluation_scope': 'grounded_answer_contract',
        'configuration': {
            'generation_provider': settings.AI_GENERATION_PROVIDER,
            'generation_model': (
                settings.GEMINI_GENERATION_MODEL
                if settings.AI_GENERATION_PROVIDER == 'gemini'
                else settings.AI_GENERATION_MODEL
            ),
            'retrieval_top_k': settings.RAG_RETRIEVAL_TOP_K,
            'minimum_score': settings.RAG_RETRIEVAL_MIN_SCORE,
            'answers_included': include_answers,
        },
        'metrics': {
            'case_count': case_count,
            'contract_pass_rate': round(
                contract_passed_count / case_count, 4
            ),
            'strict_lexical_proxy_pass_rate': round(
                strict_lexical_proxy_passed_count / case_count, 4
            ),
            'grounded_contract_accuracy': round(
                contract_matches / case_count, 4
            ),
            'citation_scope_accuracy': round(citation_matches / case_count, 4),
            'expected_marker_recall': round(
                expected_marker_hits / answerable_count, 4
            ) if answerable_count else None,
            'refusal_accuracy': round(
                refusal_matches / unsupported_count, 4
            ) if unsupported_count else None,
            'mean_latency_ms': round(total_latency_ms / case_count, 2),
            'total_tokens_reported': total_tokens,
            'token_measurement_count': token_measurements,
        },
        'limitations': [
            'expected_marker_recall_is_a_strict_lexical_proxy',
            'contract_pass_rate_does_not_measure_semantic_correctness',
            'human_review_is_required_for_semantic_and_pedagogical_quality',
        ],
        'cases': results,
    }
