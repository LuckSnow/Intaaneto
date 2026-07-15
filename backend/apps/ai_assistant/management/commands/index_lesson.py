from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.management.base import BaseCommand, CommandError

from apps.ai_assistant.rag_services import LessonIndexingError, index_lesson


class Command(BaseCommand):
    help = 'Index one lesson as its teacher-owner or an administrator.'

    def add_arguments(self, parser):
        parser.add_argument('lesson_id', type=int)
        parser.add_argument(
            '--actor-id',
            type=int,
            required=True,
            help='Teacher-owner or administrator user ID used for authorization.',
        )

    def handle(self, *args, **options):
        user_model = get_user_model()
        try:
            actor = user_model.objects.get(pk=options['actor_id'])
            source, created = index_lesson(
                actor=actor,
                lesson_id=options['lesson_id'],
            )
        except user_model.DoesNotExist as exc:
            raise CommandError('Actor does not exist') from exc
        except (LessonIndexingError, PermissionDenied) as exc:
            raise CommandError(str(exc)) from exc

        action = 'created' if created else 'already current'
        self.stdout.write(self.style.SUCCESS(
            f'Lesson {options["lesson_id"]} index {action}: source {source.pk}, '
            f'version {source.version}, chunks {source.chunks.count()}'
        ))
