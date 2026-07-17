import json
import os
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.management.base import BaseCommand, CommandError

from apps.ai_assistant.access import accessible_lesson_queryset
from apps.ai_assistant.rag_evaluation import (
    EvaluationDatasetError,
    evaluate_grounded_answers,
    load_retrieval_evaluation_dataset,
)
from apps.ai_assistant.rag_human_review import (
    RAGHumanReviewError,
    build_rag_review_template,
    serialize_rag_review_template,
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
        parser.add_argument('--export-review-dir', type=Path)
        parser.add_argument('--rater-a')
        parser.add_argument('--rater-b')
        parser.add_argument('--confirm-sensitive-export', action='store_true')
        parser.add_argument('--overwrite', action='store_true')

    @staticmethod
    def _write_private_review(path, serialized, *, overwrite):
        if path.is_symlink():
            raise RAGHumanReviewError('Review target cannot be a symbolic link')
        if path.exists() and not overwrite:
            raise RAGHumanReviewError(
                'Review target already exists; use --overwrite deliberately'
            )
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        if hasattr(os, 'O_NOFOLLOW'):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(path, flags, 0o600)
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            stream.write(serialized)
        os.chmod(path, 0o600)

    @staticmethod
    def _validated_export_dir(options):
        export_dir = options['export_review_dir']
        if export_dir is None:
            return None
        if not options['confirm_sensitive_export']:
            raise CommandError(
                'Refusing raw answer export without --confirm-sensitive-export'
            )
        if not options['rater_a'] or not options['rater_b']:
            raise CommandError(
                '--rater-a and --rater-b are required for review export'
            )
        if options['rater_a'] == options['rater_b']:
            raise CommandError('Two distinct rater pseudonyms are required')
        resolved_dir = export_dir.expanduser().resolve()
        if export_dir.expanduser().is_symlink() or not resolved_dir.is_dir():
            raise RAGHumanReviewError(
                'Review export directory must exist and cannot be a symbolic link'
            )
        return resolved_dir

    def _export_reviews(self, report, export_dir, options):
        exports = []
        pending = []
        for rater_id in (options['rater_a'], options['rater_b']):
            template = build_rag_review_template(
                report=report,
                rater_id=rater_id,
            )
            serialized, digest = serialize_rag_review_template(template)
            path = export_dir / f'rag-answer-review-{rater_id}.json'
            if path.is_symlink() or (path.exists() and not options['overwrite']):
                raise RAGHumanReviewError(
                    'Review target already exists or is a symbolic link'
                )
            pending.append((path, serialized, digest))
        for path, serialized, digest in pending:
            self._write_private_review(
                path,
                serialized,
                overwrite=options['overwrite'],
            )
            exports.append({'filename': path.name, 'sha256': digest})
        return {
            'files': exports,
            'file_mode': '0600',
            'handling': 'local_sensitive_demo_output_do_not_commit',
        }

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
            export_dir = self._validated_export_dir(options)
            include_review_data = options['include_answers'] or export_dir is not None
            report = evaluate_grounded_answers(
                actor=actor,
                lesson=lesson,
                dataset=dataset,
                include_answers=include_review_data,
            )

            if export_dir is not None:
                export_metadata = self._export_reviews(report, export_dir, options)
                if not options['include_answers']:
                    for case in report['cases']:
                        case.pop('question', None)
                        case.pop('answer', None)
                        case.pop('citations', None)
                    report['configuration']['answers_included'] = False
                report['review_package_export'] = export_metadata
        except user_model.DoesNotExist as exc:
            raise CommandError('Actor does not exist') from exc
        except (
            AIProviderError,
            EvaluationDatasetError,
            LessonRetrievalError,
            PermissionDenied,
            RAGHumanReviewError,
            OSError,
        ) as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(json.dumps(report, ensure_ascii=False, indent=2))
