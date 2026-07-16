import json

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.management.base import BaseCommand, CommandError

from apps.ai_assistant.access import accessible_lesson_queryset
from apps.ai_assistant.rag_evaluation import (
    EvaluationDatasetError,
    evaluate_lesson_retrieval,
    load_retrieval_evaluation_dataset,
)
from apps.ai_assistant.rag_services import LessonRetrievalError


class Command(BaseCommand):
    help = 'Evaluate authorized retrieval against the bundled Vietnamese dataset.'

    def add_arguments(self, parser):
        parser.add_argument('lesson_id', type=int)
        parser.add_argument(
            '--actor-id',
            type=int,
            required=True,
            help='Enrolled learner, owning teacher, or administrator user ID.',
        )

    def handle(self, *args, **options):
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
            report = evaluate_lesson_retrieval(
                actor=actor,
                lesson=lesson,
                dataset=dataset,
            )
        except user_model.DoesNotExist as exc:
            raise CommandError('Actor does not exist') from exc
        except (EvaluationDatasetError, LessonRetrievalError, PermissionDenied) as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(json.dumps(report, ensure_ascii=False, indent=2))
