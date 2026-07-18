"""Aggregate two completed private grounded-answer review sheets."""

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.ai_assistant.rag_human_review import (
    RAGHumanReviewError,
    summarize_rag_reviews,
)


class Command(BaseCommand):
    help = 'Summarize two independent RAG answer reviews without raw output'

    def add_arguments(self, parser):
        parser.add_argument('--rater-a', type=Path, required=True)
        parser.add_argument('--rater-b', type=Path, required=True)

    def handle(self, *args, **options):
        try:
            report = summarize_rag_reviews(
                rater_a_path=options['rater_a'],
                rater_b_path=options['rater_b'],
            )
        except RAGHumanReviewError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(report, ensure_ascii=False, indent=2))
