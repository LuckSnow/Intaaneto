"""Import reviewed Markdown learning materials as draft courses and lessons."""

from hashlib import sha256
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.courses.learning_corpus import (
    LearningCorpusError,
    compile_learning_corpus,
    is_managed_content,
)
from apps.courses.models import Course, Lesson
from apps.users.models import User


class Command(BaseCommand):
    help = 'Validate or import the reviewed Markdown learning corpus'

    def add_arguments(self, parser):
        parser.add_argument('--teacher-id', type=int)
        parser.add_argument(
            '--source-root',
            type=Path,
            default=None,
            help='Directory containing computer-networks.md and web-programming.md',
        )
        parser.add_argument(
            '--publish',
            action='store_true',
            help='Explicitly publish imported courses and lessons',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Validate and compile sources without reading or writing the database',
        )

    def handle(self, *args, **options):
        source_root = options['source_root'] or self._default_source_root()
        try:
            compiled_courses = compile_learning_corpus(source_root)
        except LearningCorpusError as exc:
            raise CommandError(str(exc)) from exc

        lesson_count = sum(len(course.lessons) for course in compiled_courses)
        self.stdout.write(
            f'Validated {len(compiled_courses)} courses and {lesson_count} lessons.'
        )
        if options['dry_run']:
            self.stdout.write(self.style.SUCCESS('Dry run completed; database unchanged.'))
            return

        teacher_id = options['teacher_id']
        if teacher_id is None:
            raise CommandError('--teacher-id is required unless --dry-run is used.')
        teacher = User.objects.filter(pk=teacher_id).first()
        if teacher is None:
            raise CommandError(f'Teacher id={teacher_id} does not exist.')
        if not teacher.is_active or not teacher.is_verified or teacher.role != 'teacher':
            raise CommandError(
                'Import owner must be an active, verified user with the teacher role.'
            )

        imported = self._import_courses(
            compiled_courses=compiled_courses,
            teacher=teacher,
            publish=options['publish'],
        )
        self.stdout.write(self.style.SUCCESS('Learning corpus import completed.'))
        for lesson, digest in imported:
            self.stdout.write(
                f'Lesson id={lesson.id} sha256={digest} published={lesson.is_published}'
            )
            self.stdout.write(
                'Index command: '
                f'python manage.py index_lesson {lesson.id} --actor-id {teacher.id}'
            )

    @staticmethod
    def _default_source_root():
        local_root = Path(__file__).resolve().parents[5] / 'docs'
        if local_root.is_dir():
            return local_root
        return Path('/project-docs')

    @staticmethod
    @transaction.atomic
    def _import_courses(*, compiled_courses, teacher, publish):
        imported = []
        for compiled_course in compiled_courses:
            definition = compiled_course.definition
            course = Course.objects.select_for_update().filter(
                slug=definition.slug,
            ).first()
            if course is not None and course.teacher_id != teacher.id:
                raise CommandError(
                    f'Course slug {definition.slug!r} belongs to another teacher.'
                )
            course_defaults = {
                'title': definition.title,
                'description': definition.description,
                'difficulty': 'beginner',
                'duration_hours': definition.duration_hours,
                'objectives': '\n'.join(definition.objectives),
                'prerequisites': definition.prerequisites,
                'teacher': teacher,
                'is_featured': False,
            }
            if course is None:
                course = Course.objects.create(
                    slug=definition.slug,
                    is_published=publish,
                    **course_defaults,
                )
            else:
                for field, value in course_defaults.items():
                    setattr(course, field, value)
                if publish:
                    course.is_published = True
                course.save()

            for order, compiled_lesson in enumerate(compiled_course.lessons, start=1):
                lesson_definition = compiled_lesson.definition
                lesson = Lesson.objects.select_for_update().filter(
                    course=course,
                    slug=lesson_definition.slug,
                ).first()
                if lesson is not None and (
                    lesson.uploaded_file
                    or lesson.extracted_text
                    or not is_managed_content(lesson.content)
                ):
                    raise CommandError(
                        f'Lesson slug {lesson_definition.slug!r} is not an importer-managed '
                        'text lesson; refusing to overwrite it.'
                    )
                lesson_defaults = {
                    'title': lesson_definition.title,
                    'description': 'Mục tiêu: ' + '; '.join(lesson_definition.objectives),
                    'lesson_type': 'text',
                    'content': compiled_lesson.content,
                    'duration_minutes': lesson_definition.duration_minutes,
                    'order': order,
                    'is_preview': False,
                    'processing_status': 'completed',
                    'processing_error': '',
                }
                if lesson is None:
                    lesson = Lesson.objects.create(
                        course=course,
                        slug=lesson_definition.slug,
                        is_published=publish,
                        **lesson_defaults,
                    )
                else:
                    for field, value in lesson_defaults.items():
                        setattr(lesson, field, value)
                    if publish:
                        lesson.is_published = True
                    lesson.save()
                imported.append(
                    (lesson, sha256(compiled_lesson.content.encode('utf-8')).hexdigest())
                )
        return imported
