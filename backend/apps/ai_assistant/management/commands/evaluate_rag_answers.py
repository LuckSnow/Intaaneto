import json

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.management.base import BaseCommand, CommandError

from apps.ai_assistant.access import accessible_lesson_queryset
from apps.ai_assistant.rag_evaluation import (
    EvaluationDatasetError,
    evaluate_grounded_answers,
    load_retrieval_evaluation_dataset,
)
from apps.ai_assistant.rag_services import LessonRetrievalError
from apps.ai_assistant.services import AIProviderError


class Command(BaseCommand):
    help = 'Evaluate grounded answers with an explicitly confirmed live provider.'

    def add_arguments(self, parser):
        parser.add_argument('lesson_id', type=int)
        parser.add_argument('--actor-id', type=int, required=True)
        parser.add_argument(
            '--confirm-provider-cost',
            action='store_true',
            help='Acknowledge that answerable cases may call the configured provider.',
        )
        parser.add_argument(
            '--include-answers',
            action='store_true',
            help='Include bounded demo questions/answers for deliberate human review.',
        )

    def handle(self, *args, **options):
        if not options['confirm_provider_cost']:
            raise CommandError(
                'Refusing live evaluation without --confirm-provider-cost'
            )

        user_model = get_user_model()
        try:
            actor = user_model.objects.get(pk=options['actor_id'])
            lesson = accessible_lesson_queryset(actor).filter(
                pk=options['lesson_id'],
            ).first()
            if lesson is None:
                raise PermissionDenied(
                    'Lesson evaluation is not available to this actor'
                )
            dataset = load_retrieval_evaluation_dataset()
            report = evaluate_grounded_answers(
                actor=actor,
                lesson=lesson,
                dataset=dataset,
                include_answers=options['include_answers'],
            )
        except user_model.DoesNotExist as exc:
            raise CommandError('Actor does not exist') from exc
        except (
            AIProviderError,
            EvaluationDatasetError,
            LessonRetrievalError,
            PermissionDenied,
        ) as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(json.dumps(report, ensure_ascii=False, indent=2))
