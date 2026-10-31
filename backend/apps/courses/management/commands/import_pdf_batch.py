"""Import PDFs in a directory; dry-run by default, private lessons only."""

import json
import os
from pathlib import Path
import time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.courses.models import Lesson
from apps.courses.pdf_batch_import import authorized_course, import_pdf_directory


class Command(BaseCommand):
    help = "Validate/import a bounded PDF batch and optionally wait for RAG readiness"

    def add_arguments(self, parser):
        parser.add_argument("--directory", required=True, type=Path)
        parser.add_argument("--actor-id", required=True, type=int)
        parser.add_argument("--course-id", required=True, type=int)
        parser.add_argument("--output", required=True, type=Path)
        parser.add_argument("--execute", action="store_true")
        parser.add_argument("--wait", action="store_true")
        parser.add_argument("--wait-seconds", type=int, default=600)

    def handle(self, *args, **options):
        if options["wait"] and not options["execute"]:
            raise CommandError("--wait requires --execute")
        if not 1 <= options["wait_seconds"] <= 3600:
            raise CommandError("wait-seconds must be between 1 and 3600")
        try:
            actor = get_user_model().objects.get(pk=options["actor_id"])
            authorized_course(actor, options["course_id"])
            # Fail before writes if the output cannot be opened safely.
            descriptor = os.open(
                options["output"],
                os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW,
                0o600,
            )
            os.close(descriptor)
            report = import_pdf_directory(
                actor=actor,
                course_id=options["course_id"],
                directory=options["directory"],
                execute=options["execute"],
            )
            if options["wait"]:
                deadline = time.monotonic() + options["wait_seconds"]
                while True:
                    authorized_course(actor, options["course_id"])
                    pending = False
                    for row in report["files"]:
                        if row["status"] not in ("queued", "running", "pending"):
                            continue
                        lesson = Lesson.objects.get(
                            pk=row["lesson_id"], course_id=options["course_id"]
                        )
                        job = lesson.ingestion_jobs.order_by("-created_at").first()
                        if job and job.status == "failed":
                            row.update(status="failed", error=job.failure_code)
                        elif (
                            lesson.processing_status == "completed"
                            and lesson.knowledge_sources.filter(
                                is_active=True, status="ready"
                            ).exists()
                        ):
                            row["status"] = "ready"
                        else:
                            pending = True
                    if not pending or time.monotonic() >= deadline:
                        break
                    time.sleep(2)
                for row in report["files"]:
                    if row["status"] in ("queued", "running", "pending"):
                        row["status"] = "timeout"
            with os.fdopen(
                os.open(options["output"], os.O_WRONLY | os.O_TRUNC | os.O_NOFOLLOW),
                "w",
            ) as stream:
                json.dump(report, stream, ensure_ascii=False, indent=2)
            os.chmod(options["output"], 0o600)
        except Exception as exc:
            raise CommandError(f"Batch import stopped: {type(exc).__name__}") from None
        for row in report["files"]:
            self.stdout.write(
                f"{row['filename']}: {row['status']} (lesson {row['lesson_id']})"
            )
        if any(
            row["status"] not in ("validated", "ready", "queued", "running")
            for row in report["files"]
        ):
            raise CommandError(
                "Some PDFs failed or timed out; inspect the private manifest"
            )
