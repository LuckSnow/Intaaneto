"""Evaluate imported corpus assessments without creating learner attempts."""

import json
import os
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.courses.learning_corpus import is_managed_content
from apps.courses.models import Lesson
from apps.exercises.assessment_blueprints import (
    assessment_matches_blueprint,
    validate_assessment_blueprints,
)
from apps.exercises.assessment_evaluation import (
    AssessmentEvaluationError,
    build_assessment_software_baseline,
    build_review_template,
    serialize_review_template,
)
from apps.exercises.models import LessonAssessment
from apps.users.models import User


class Command(BaseCommand):
    help = 'Run the E2 software baseline for imported corpus assessments'

    def add_arguments(self, parser):
        parser.add_argument('--teacher-id', type=int, required=True)
        parser.add_argument('--export-review-template', type=Path)
        parser.add_argument('--rater-id')
        parser.add_argument('--confirm-answer-key-export', action='store_true')
        parser.add_argument('--overwrite', action='store_true')
        parser.add_argument('--include-cases', action='store_true')

    def handle(self, *args, **options):
        teacher = User.objects.filter(pk=options['teacher_id']).first()
        if teacher is None:
            raise CommandError('Teacher does not exist')
        if not teacher.is_active or not teacher.is_verified or teacher.role != 'teacher':
            raise CommandError(
                'Evaluation owner must be an active, verified teacher.'
            )

        blueprints = validate_assessment_blueprints()
        database_records = []
        for blueprint in blueprints:
            lesson = (
                Lesson.objects.select_related('course')
                .filter(
                    course__slug=blueprint.course_slug,
                    slug=blueprint.lesson_slug,
                )
                .first()
            )
            if lesson is None or lesson.course.teacher_id != teacher.id:
                raise CommandError('Assessment evaluation lesson is unavailable')
            if (
                lesson.uploaded_file
                or lesson.extracted_text
                or not is_managed_content(lesson.content)
            ):
                raise CommandError('Assessment evaluation lesson is not corpus-managed')
            assessment = LessonAssessment.objects.filter(lesson=lesson).first()
            if assessment is None or not assessment_matches_blueprint(
                assessment=assessment,
                blueprint=blueprint,
            ):
                raise CommandError(
                    'Persisted assessment does not match the checked-in blueprint'
                )
            database_records.append({
                'lesson_id': lesson.id,
                'assessment_id': assessment.id,
                'assessment_version': assessment.version,
                'published': assessment.is_published,
                'question_count': assessment.questions.count(),
            })

        report = build_assessment_software_baseline(
            blueprints,
            include_cases=options['include_cases'],
        )
        report['database_scope'] = {
            'owner_role': 'teacher',
            'blueprint_match': True,
            'records': database_records,
        }

        output_path = options['export_review_template']
        if output_path is not None:
            if not options['confirm_answer_key_export']:
                raise CommandError(
                    'Refusing answer-key export without '
                    '--confirm-answer-key-export'
                )
            rater_id = options['rater_id']
            if not rater_id:
                raise CommandError('--rater-id is required when exporting a template')
            try:
                template = build_review_template(rater_id=rater_id)
                serialized, digest = serialize_review_template(template)
                if output_path.expanduser().is_symlink():
                    raise AssessmentEvaluationError(
                        'Review template target cannot be a symbolic link'
                    )
                resolved = output_path.expanduser().resolve()
                if resolved.suffix.lower() != '.json' or not resolved.parent.is_dir():
                    raise AssessmentEvaluationError(
                        'Review template target must be a JSON file in an existing directory'
                    )
                if resolved.exists() and not options['overwrite']:
                    raise AssessmentEvaluationError(
                        'Review template already exists; use --overwrite deliberately'
                    )
                flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
                if hasattr(os, 'O_NOFOLLOW'):
                    flags |= os.O_NOFOLLOW
                descriptor = os.open(resolved, flags, 0o600)
                with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
                    stream.write(serialized)
                os.chmod(resolved, 0o600)
            except (AssessmentEvaluationError, OSError) as exc:
                raise CommandError(str(exc)) from exc
            report['review_template_export'] = {
                'filename': resolved.name,
                'sha256': digest,
                'answer_key_included': True,
                'explanations_included': True,
                'handling': 'local_sensitive_authoring_data_do_not_commit',
            }

        self.stdout.write(json.dumps(report, ensure_ascii=False, indent=2))
