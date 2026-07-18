"""Aggregate two completed E2 review sheets without exposing raw ratings."""

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.exercises.assessment_evaluation import (
    AssessmentEvaluationError,
    summarize_independent_reviews,
)


class Command(BaseCommand):
    help = 'Summarize two independent corpus-assessment review sheets'

    def add_arguments(self, parser):
        parser.add_argument('--rater-a', type=Path, required=True)
        parser.add_argument('--rater-b', type=Path, required=True)

    def handle(self, *args, **options):
        try:
            report = summarize_independent_reviews(
                rater_a_path=options['rater_a'],
                rater_b_path=options['rater_b'],
            )
        except AssessmentEvaluationError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(report, ensure_ascii=False, indent=2))
