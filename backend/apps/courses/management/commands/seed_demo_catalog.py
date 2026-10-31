"""Expand the existing demo teacher's catalog without overwriting authored work."""

from uuid import uuid4

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.courses.demo_catalog import COVER_ROOT, catalog_courses
from apps.courses.models import Course, Lesson
from apps.users.models import User
from .import_learning_corpus import Command as CorpusCommand
from .seed_demo_data import DEMO_COURSE_SLUG, DEMO_TEACHER_EMAIL


class Command(BaseCommand):
    help = 'Preview or add three demo courses; preserve existing lessons, media and users'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Write the previewed catalog')
        parser.add_argument('--publish', action='store_true', help='Publish only newly created records')

    def handle(self, *args, **options):
        catalog = catalog_courses(CorpusCommand._default_source_root())
        for item in catalog:
            self.stdout.write(f"{item['title']}: {len(item['lessons'])} lessons")
        if not options['apply']:
            self.stdout.write('Preview only. Use --apply to write; --publish to publish new records.')
            return
        saved_files = []
        created_courses = created_lessons = 0
        try:
            with transaction.atomic():
                teacher = User.objects.select_for_update().filter(
                    email=DEMO_TEACHER_EMAIL, role='teacher', is_active=True, is_verified=True,
                ).first()
                if teacher is None:
                    raise CommandError('An existing active, verified Demo Teacher is required.')
                # Check every owner before saving files or creating records.
                slugs = [item['slug'] for item in catalog] + [DEMO_COURSE_SLUG]
                if Course.objects.filter(slug__in=slugs).exclude(teacher=teacher).exists():
                    raise CommandError('A catalog slug belongs to another teacher; nothing changed.')
                for item in catalog:
                    defaults = {key: item[key] for key in (
                        'title', 'description', 'duration_hours', 'objectives', 'prerequisites',
                    )}
                    course, created = Course.objects.get_or_create(
                        slug=item['slug'], defaults={**defaults, 'teacher': teacher,
                        'is_published': options['publish'], 'difficulty': 'beginner'},
                    )
                    created_courses += created
                    for order, lesson in enumerate(item['lessons'], 1):
                        _, added = Lesson.objects.get_or_create(
                            course=course, slug=lesson['slug'],
                            defaults={**{k: v for k, v in lesson.items() if k != 'slug'},
                                      'order': order, 'lesson_type': 'text',
                                      'is_published': options['publish'], 'is_preview': False,
                                      'processing_status': 'completed'},
                        )
                        created_lessons += added
                    self._cover(course, item['cover'], saved_files)
                demo_course = Course.objects.filter(slug=DEMO_COURSE_SLUG, teacher=teacher).first()
                if demo_course:
                    self._cover(demo_course, 'rag', saved_files)
        except Exception:
            for storage, name in saved_files:
                try:
                    storage.delete(name)
                except Exception:
                    self.stderr.write('An unattached demo cover could not be cleaned up.')
            raise
        self.stdout.write(self.style.SUCCESS(
            f'Created {created_courses} courses, {created_lessons} lessons, {len(saved_files)} covers. '
            'Existing content preserved. RAG indexing remains a separate operation.'
        ))

    @staticmethod
    def _cover(course, cover, saved_files):
        if course.thumbnail:
            return
        # Trusted repository SVG illustrations, never user-uploaded SVG content.
        content = ContentFile((COVER_ROOT / f'{cover}.svg').read_bytes())
        course.thumbnail.save(f'{uuid4().hex}.svg', content, save=False)
        saved_files.append((course.thumbnail.storage, course.thumbnail.name))
        course.save(update_fields=['thumbnail', 'updated_at'])
