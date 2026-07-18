"""Import curated draft assessment blueprints for importer-managed lessons."""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.courses.learning_corpus import is_managed_content
from apps.courses.models import Lesson
from apps.exercises.assessment_blueprints import (
    AssessmentBlueprintError,
    assessment_matches_blueprint,
    question_blueprint_payload,
    validate_assessment_blueprints,
)
from apps.exercises.models import AssessmentQuestion, LessonAssessment
from apps.users.models import User


class Command(BaseCommand):
    help = 'Validate or import draft assessments for the learning corpus'

    def add_arguments(self, parser):
        parser.add_argument('--teacher-id', type=int)
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Validate checked-in blueprints without database access',
        )
        parser.add_argument(
            '--publish-reviewed',
            action='store_true',
            help='Confirm teacher review and publish imported assessments',
        )

    def handle(self, *args, **options):
        try:
            blueprints = validate_assessment_blueprints()
        except AssessmentBlueprintError as exc:
            raise CommandError(str(exc)) from exc

        question_count = sum(len(item.questions) for item in blueprints)
        self.stdout.write(
            f'Validated {len(blueprints)} assessments and {question_count} questions '
            f'at blueprint revision {self._revision()}.'
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
                'Assessment owner must be an active, verified user with the teacher role.'
            )

        assessments = self._import_blueprints(
            blueprints=blueprints,
            teacher=teacher,
            publish_reviewed=options['publish_reviewed'],
        )
        self.stdout.write(self.style.SUCCESS('Corpus assessment import completed.'))
        for assessment in assessments:
            self.stdout.write(
                f'Assessment id={assessment.id} lesson_id={assessment.lesson_id} '
                f'published={assessment.is_published} questions='
                f'{assessment.questions.count()}'
            )

    @staticmethod
    def _revision():
        from apps.exercises.assessment_blueprints import BLUEPRINT_REVISION

        return BLUEPRINT_REVISION

    @classmethod
    @transaction.atomic
    def _import_blueprints(cls, *, blueprints, teacher, publish_reviewed):
        imported = []
        for blueprint in blueprints:
            lesson = (
                Lesson.objects.select_related('course')
                .select_for_update()
                .filter(
                    course__slug=blueprint.course_slug,
                    slug=blueprint.lesson_slug,
                )
                .first()
            )
            if lesson is None:
                raise CommandError(
                    f'Importer-managed lesson {blueprint.course_slug}/'
                    f'{blueprint.lesson_slug} does not exist.'
                )
            if lesson.course.teacher_id != teacher.id:
                raise CommandError(
                    f'Lesson {blueprint.lesson_slug!r} belongs to another teacher.'
                )
            if (
                lesson.uploaded_file
                or lesson.extracted_text
                or not is_managed_content(lesson.content)
            ):
                raise CommandError(
                    f'Lesson {blueprint.lesson_slug!r} is not managed by the '
                    'reviewed learning-corpus importer.'
                )

            assessment = (
                LessonAssessment.objects.select_for_update()
                .filter(lesson=lesson)
                .first()
            )
            if assessment is None:
                assessment = LessonAssessment.objects.create(
                    lesson=lesson,
                    title=blueprint.title,
                    instructions=blueprint.instructions,
                    pass_threshold=blueprint.pass_threshold,
                    is_published=publish_reviewed,
                )
                AssessmentQuestion.objects.bulk_create([
                    AssessmentQuestion(
                        assessment=assessment,
                        **question_blueprint_payload(question),
                    )
                    for question in blueprint.questions
                ])
            elif not assessment_matches_blueprint(
                assessment=assessment,
                blueprint=blueprint,
            ):
                evidence = ' with learner attempts' if assessment.attempts.exists() else ''
                raise CommandError(
                    f'Existing assessment for {blueprint.lesson_slug!r} differs '
                    f'from the checked-in blueprint{evidence}; refusing to overwrite it.'
                )
            elif publish_reviewed and not assessment.is_published:
                assessment.is_published = True
                assessment.save(update_fields=['is_published', 'updated_at'])
            imported.append(assessment)
        return imported
