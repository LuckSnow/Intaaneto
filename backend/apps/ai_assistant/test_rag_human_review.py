import json
import os
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.courses.models import Course, Lesson

from .rag_human_review import (
    RAGHumanReviewError,
    build_rag_review_template,
    summarize_rag_reviews,
)


def _answer_report(*, answer='RAG dùng bằng chứng đã được phê duyệt.'):
    return {
        'report_schema_version': 2,
        'dataset': {'id': 'rag-review-test', 'version': '1.0.0', 'schema_version': 1},
        'lesson_id': 7,
        'configuration': {'answers_included': True},
        'metrics': {'case_count': 2},
        'limitations': [],
        'cases': [
            {
                'id': 'answerable-1',
                'tags': ['answerable'],
                'question': 'RAG dựa vào đâu?',
                'answer': answer,
                'actual_grounded': True,
                'citations': [{
                    'lesson_title': 'RAG là gì?',
                    'location': {'page_start': 1, 'page_end': 1},
                    'excerpt': 'RAG dùng tài liệu đã được phê duyệt.',
                }],
            },
            {
                'id': 'unsupported-1',
                'tags': ['unsupported'],
                'question': 'Ngày mai có mưa không?',
                'answer': 'Tài liệu bài học không có đủ thông tin.',
                'actual_grounded': False,
                'citations': [],
            },
        ],
    }


def _complete(template, *, disagree_case=None):
    for item in template['items']:
        positive = item['case_id'] != disagree_case
        item['answer_correct'] = positive
        item['evidence_aligned'] = positive
        item['pedagogically_helpful'] = positive
        item['clarity'] = 4 if positive else 2
    return template


def _write(path: Path, payload: dict):
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')


def test_two_rater_summary_returns_only_aggregate_metrics(tmp_path):
    rater_a = _complete(build_rag_review_template(
        report=_answer_report(), rater_id='reviewer_a',
    ))
    rater_b = _complete(build_rag_review_template(
        report=_answer_report(), rater_id='reviewer_b',
    ), disagree_case='unsupported-1')
    path_a = tmp_path / 'a.json'
    path_b = tmp_path / 'b.json'
    _write(path_a, rater_a)
    _write(path_b, rater_b)

    report = summarize_rag_reviews(rater_a_path=path_a, rater_b_path=path_b)

    assert report['metrics']['case_count'] == 2
    assert report['metrics']['answer_correct']['percent_agreement'] == 0.5
    assert report['metrics']['answer_correct']['cohen_kappa'] == 0.0
    assert report['metrics']['clarity_rater_a']['median'] == 4.0
    serialized = json.dumps(report, ensure_ascii=False)
    assert 'reviewer_a' not in serialized
    assert 'RAG dựa vào đâu?' not in serialized
    assert 'RAG dùng bằng chứng' not in serialized


def test_review_rejects_tampered_content_and_same_rater(tmp_path):
    first = _complete(build_rag_review_template(
        report=_answer_report(), rater_id='same_rater',
    ))
    second = _complete(build_rag_review_template(
        report=_answer_report(), rater_id='same_rater',
    ))
    path_a = tmp_path / 'a.json'
    path_b = tmp_path / 'b.json'
    _write(path_a, first)
    _write(path_b, second)

    with pytest.raises(RAGHumanReviewError, match='distinct'):
        summarize_rag_reviews(rater_a_path=path_a, rater_b_path=path_b)

    second['rater_id'] = 'other_rater'
    second['items'][0]['answer'] = 'Nội dung đã bị thay đổi.'
    _write(path_b, second)
    with pytest.raises(RAGHumanReviewError, match='digest'):
        summarize_rag_reviews(rater_a_path=path_a, rater_b_path=path_b)


def test_review_rejects_incomplete_rating(tmp_path):
    first = _complete(build_rag_review_template(
        report=_answer_report(), rater_id='reviewer_a',
    ))
    second = _complete(build_rag_review_template(
        report=_answer_report(), rater_id='reviewer_b',
    ))
    second['items'][0]['answer_correct'] = None
    path_a = tmp_path / 'a.json'
    path_b = tmp_path / 'b.json'
    _write(path_a, first)
    _write(path_b, second)

    with pytest.raises(RAGHumanReviewError, match='incomplete'):
        summarize_rag_reviews(rater_a_path=path_a, rater_b_path=path_b)


@pytest.mark.django_db
def test_evaluation_command_exports_two_private_identical_packages_without_stdout_raw(
    tmp_path, teacher_user
):
    course = Course.objects.create(
        title='Review RAG', slug='review-rag', description='Review',
        teacher=teacher_user, is_published=True,
    )
    lesson = Lesson.objects.create(
        course=course, title='Review lesson', slug='review-lesson',
        content='Demo', is_published=True,
    )
    report = _answer_report()
    report['lesson_id'] = lesson.id
    stdout = StringIO()

    with patch(
        'apps.ai_assistant.management.commands.evaluate_rag_answers.'
        'evaluate_grounded_answers',
        return_value=report,
    ):
        call_command(
            'evaluate_rag_answers',
            lesson.id,
            actor_id=teacher_user.id,
            confirm_provider_cost=True,
            export_review_dir=tmp_path,
            rater_a='reviewer_a',
            rater_b='reviewer_b',
            confirm_sensitive_export=True,
            stdout=stdout,
        )

    path_a = tmp_path / 'rag-answer-review-reviewer_a.json'
    path_b = tmp_path / 'rag-answer-review-reviewer_b.json'
    payload_a = json.loads(path_a.read_text(encoding='utf-8'))
    payload_b = json.loads(path_b.read_text(encoding='utf-8'))
    assert payload_a['package_sha256'] == payload_b['package_sha256']
    assert os.stat(path_a).st_mode & 0o777 == 0o600
    assert os.stat(path_b).st_mode & 0o777 == 0o600
    assert 'RAG dựa vào đâu?' not in stdout.getvalue()
    assert 'review_package_export' in stdout.getvalue()


@pytest.mark.django_db
def test_evaluation_command_requires_separate_sensitive_export_confirmation(
    tmp_path, teacher_user
):
    course = Course.objects.create(
        title='Review confirmation', slug='review-confirmation',
        description='Review', teacher=teacher_user, is_published=True,
    )
    lesson = Lesson.objects.create(
        course=course, title='Review confirmation lesson',
        slug='review-confirmation-lesson', content='Demo', is_published=True,
    )

    with patch(
        'apps.ai_assistant.management.commands.evaluate_rag_answers.'
        'evaluate_grounded_answers',
    ) as evaluator:
        with pytest.raises(CommandError, match='confirm-sensitive-export'):
            call_command(
                'evaluate_rag_answers', lesson.id,
                actor_id=teacher_user.id,
                confirm_provider_cost=True,
                export_review_dir=tmp_path,
                rater_a='reviewer_a', rater_b='reviewer_b',
            )

    evaluator.assert_not_called()
