"""Bounded, owner-authorized PDF batch import into durable ingestion."""

import hashlib
from pathlib import Path

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from PyPDF2 import PdfReader

from .ingestion import IngestionQueueError, queue_pdf_ingestion
from .models import Course, Lesson
from .serializers import LessonUploadSerializer
from .services import extract_text_from_pdf


MAX_BATCH_FILES = 50


def authorized_course(actor, course_id, *, lock=False):
    if actor.is_authenticated and getattr(actor, "pk", None):
        actor.refresh_from_db(fields=["role", "is_active", "is_verified"])
    if not (
        actor.is_authenticated
        and actor.is_active
        and actor.is_verified
        and actor.role in ("teacher", "admin")
    ):
        raise PermissionDenied("Active verified teacher/admin required")
    queryset = Course.objects.all()
    if lock:
        queryset = queryset.select_for_update()
    if actor.role != "admin":
        queryset = queryset.filter(teacher_id=actor.pk)
    course = queryset.filter(pk=course_id).first()
    if course is None:
        raise PermissionDenied("Course is not available to this actor")
    return course


def import_pdf_directory(*, actor, course_id, directory, execute=False):
    # Authorization precedes directory/file reads, parsing, storage and broker calls.
    authorized_course(actor, course_id)
    directory = Path(directory)
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("Expected a real PDF directory")
    paths = sorted(p for p in directory.iterdir() if p.suffix.lower() == ".pdf")
    if not 1 <= len(paths) <= MAX_BATCH_FILES:
        raise ValueError(f"Expected 1–{MAX_BATCH_FILES} PDF files")
    report = {
        "schema_version": 1,
        "mode": "execute" if execute else "dry_run",
        "course_id": course_id,
        "files": [],
    }
    for path in paths:
        row = {"filename": path.name, "lesson_id": None, "status": "invalid"}
        try:
            if path.is_symlink() or not path.is_file():
                raise ValueError("Symlinks/non-files are not accepted")
            with path.open("rb") as stream:
                content = stream.read(settings.LESSON_PDF_MAX_BYTES + 1)
            uploaded = SimpleUploadedFile(
                path.name, content, content_type="application/pdf"
            )
            LessonUploadSerializer().validate_uploaded_file(uploaded)
            text = extract_text_from_pdf(uploaded)
            digest = hashlib.sha256(content).hexdigest()
            row.update(
                pdf_sha256=digest,
                extracted_char_count=len(text),
                page_count=len(PdfReader(uploaded).pages),
                status="validated",
            )
            if execute:
                with transaction.atomic():
                    course = authorized_course(actor, course_id, lock=True)
                    slug = "batch-pdf-" + digest[:32]
                    lesson = Lesson.objects.filter(course=course, slug=slug).first()
                    if lesson is None:
                        lesson = Lesson.objects.create(
                            course=course,
                            slug=slug,
                            title=path.stem[:255],
                            description="Imported by the PDF research batch tool",
                            uploaded_file=uploaded,
                            lesson_type="text",
                            is_published=False,
                            is_preview=False,
                            processing_status="pending",
                        )
                    else:
                        with lesson.uploaded_file.open("rb") as original:
                            actual = hashlib.sha256(
                                original.read(settings.LESSON_PDF_MAX_BYTES + 1)
                            ).hexdigest()
                        if actual != digest or lesson.is_published or lesson.is_preview:
                            raise ValueError(
                                "Existing lesson does not match private batch source"
                            )
                row.update(lesson_id=lesson.pk, storage_name=lesson.uploaded_file.name)
                if (
                    lesson.processing_status == "completed"
                    and lesson.knowledge_sources.filter(
                        is_active=True, status="ready"
                    ).exists()
                ):
                    row["status"] = "ready"
                else:
                    # Reuse active jobs; failed deliveries can be retried by rerunning.
                    job, _ = queue_pdf_ingestion(actor=actor, lesson=lesson)
                    row.update(status=job.status, job_id=job.pk)
        except IngestionQueueError:
            row.update(status="queue_failed", error="IngestionQueueError")
        except Exception as exc:
            # No provider/storage exception bodies, paths, or credentials in manifest.
            row.update(
                status="failed" if row["lesson_id"] else "invalid",
                error=type(exc).__name__,
            )
        report["files"].append(row)
    return report
