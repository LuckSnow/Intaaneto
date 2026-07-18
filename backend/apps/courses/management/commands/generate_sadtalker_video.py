"""Manually run the bounded local SadTalker research adapter."""

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import PermissionDenied

from apps.courses.models import Lesson
from apps.courses.video_generation import (
    VideoGenerationError,
    authorize_video_generation,
    generate_lesson_video,
)
from apps.users.models import User


class Command(BaseCommand):
    help = 'Generate one approved lesson video through local SadTalker'

    def add_arguments(self, parser):
        parser.add_argument('lesson_id', type=int)
        parser.add_argument('--actor-id', type=int, required=True)
        parser.add_argument('--script-file', type=Path, required=True)
        parser.add_argument('--audio-file', type=Path, required=True)
        parser.add_argument('--portrait-file', type=Path, required=True)
        parser.add_argument(
            '--confirm-rights-and-approval',
            action='store_true',
            help='Confirm approved script and rights/consent for audio and portrait',
        )

    def handle(self, *args, **options):
        actor = User.objects.filter(pk=options['actor_id']).first()
        lesson = Lesson.objects.select_related('course').filter(
            pk=options['lesson_id']
        ).first()
        if actor is None or lesson is None:
            raise CommandError('Không tìm thấy actor hoặc lesson.')
        try:
            authorize_video_generation(actor=actor, lesson=lesson)
        except PermissionDenied as exc:
            raise CommandError(str(exc)) from exc
        if not options['confirm_rights_and_approval']:
            raise CommandError(
                'approval_required: Cần xác nhận quyền sử dụng và phê duyệt.'
            )
        try:
            script_path = options['script_file'].expanduser().resolve()
            if not script_path.is_file() or script_path.stat().st_size > 50000:
                raise VideoGenerationError(
                    'invalid_script',
                    'File kịch bản không hợp lệ.',
                )
            script = script_path.read_text(encoding='utf-8')
            job = generate_lesson_video(
                actor=actor,
                lesson=lesson,
                approved_script=script,
                audio_path=options['audio_file'],
                portrait_path=options['portrait_file'],
                rights_and_approval_confirmed=True,
            )
        except (UnicodeDecodeError, OSError) as exc:
            raise CommandError('Không thể đọc file đầu vào.') from exc
        except VideoGenerationError as exc:
            raise CommandError(f'{exc.code}: {exc}') from exc
        self.stdout.write(self.style.SUCCESS(
            f'SadTalker job id={job.id} completed for lesson id={lesson.id}.'
        ))
