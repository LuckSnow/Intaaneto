from pathlib import Path
from unittest.mock import patch

from django.core.exceptions import PermissionDenied
import pytest

from .models import Course, Lesson, LessonIngestionJob
from .pdf_batch_import import import_pdf_directory
from .test_pdf_ingestion import make_pdf


@pytest.fixture
def batch_setup(teacher_user, tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path / "media"
    folder = tmp_path / "pdfs"
    folder.mkdir()
    (folder / "lesson.pdf").write_bytes(make_pdf("Private RAG teaching content."))
    course = Course.objects.create(title="Batch", slug="batch", teacher=teacher_user)
    return folder, course


@pytest.mark.django_db
def test_batch_dry_run_validates_without_writes(teacher_user, batch_setup):
    folder, course = batch_setup
    with patch("apps.courses.pdf_batch_import.queue_pdf_ingestion") as queue:
        result = import_pdf_directory(
            actor=teacher_user, course_id=course.id, directory=folder
        )
    assert result["files"][0]["status"] == "validated"
    assert result["files"][0]["page_count"] == 1
    assert Lesson.objects.count() == 0
    queue.assert_not_called()


@pytest.mark.django_db
def test_batch_outsider_denied_before_reading_files(student_user, batch_setup):
    folder, course = batch_setup
    with patch.object(
        Path, "iterdir", side_effect=AssertionError("file read before authorization")
    ):
        with pytest.raises(PermissionDenied):
            import_pdf_directory(
                actor=student_user, course_id=course.id, directory=folder, execute=True
            )
    assert Lesson.objects.count() == 0


@pytest.mark.django_db
def test_batch_other_teacher_cannot_import(teacher_user, batch_setup):
    folder, course = batch_setup
    other = type(teacher_user).objects.create_user(
        email="other-batch@test.com",
        username="other-batch",
        password="temporary-test-password",
        role="teacher",
        is_verified=True,
    )
    with patch.object(
        Path, "iterdir", side_effect=AssertionError("unauthorized file read")
    ):
        with pytest.raises(PermissionDenied):
            import_pdf_directory(
                actor=other, course_id=course.pk, directory=folder, execute=True
            )


@pytest.mark.django_db
def test_batch_revoked_actor_is_denied_before_file_read(teacher_user, batch_setup):
    folder, course = batch_setup
    type(teacher_user).objects.filter(pk=teacher_user.pk).update(is_active=False)
    with patch.object(
        Path, "iterdir", side_effect=AssertionError("file read after revocation")
    ):
        with pytest.raises(PermissionDenied):
            import_pdf_directory(
                actor=teacher_user, course_id=course.pk, directory=folder, execute=True
            )


@pytest.mark.django_db
def test_batch_same_bytes_are_idempotent_and_private(teacher_user, batch_setup):
    folder, course = batch_setup
    (folder / "renamed.pdf").write_bytes((folder / "lesson.pdf").read_bytes())
    with patch("apps.courses.tasks.process_pdf_lesson_job.apply_async") as dispatch:
        first = import_pdf_directory(
            actor=teacher_user, course_id=course.id, directory=folder, execute=True
        )
        second = import_pdf_directory(
            actor=teacher_user, course_id=course.id, directory=folder, execute=True
        )
    assert Lesson.objects.count() == 1
    assert LessonIngestionJob.objects.count() == 1
    assert dispatch.call_count == 1
    lesson = Lesson.objects.get()
    assert not lesson.is_published and not lesson.is_preview
    assert {r["lesson_id"] for r in first["files"] + second["files"]} == {lesson.pk}


@pytest.mark.django_db
def test_batch_invalid_pdf_and_symlink_do_not_persist(teacher_user, batch_setup):
    folder, course = batch_setup
    (folder / "lesson.pdf").write_bytes(b"%PDF-malformed")
    (folder / "link.pdf").symlink_to(folder / "lesson.pdf")
    result = import_pdf_directory(
        actor=teacher_user, course_id=course.id, directory=folder, execute=True
    )
    assert all(r["status"] == "invalid" for r in result["files"])
    assert Lesson.objects.count() == 0


@pytest.mark.django_db
def test_batch_oversize_and_encrypted_files_are_rejected(
    teacher_user, batch_setup, settings
):
    folder, course = batch_setup
    (folder / "lesson.pdf").write_bytes(make_pdf("Text", password="secret"))
    result = import_pdf_directory(
        actor=teacher_user, course_id=course.id, directory=folder, execute=True
    )
    assert result["files"][0]["status"] == "invalid"
    settings.LESSON_PDF_MAX_BYTES = 5
    (folder / "lesson.pdf").write_bytes(b"%PDF-oversized")
    result = import_pdf_directory(
        actor=teacher_user, course_id=course.id, directory=folder, execute=True
    )
    assert result["files"][0]["status"] == "invalid"
    assert Lesson.objects.count() == 0


@pytest.mark.django_db
def test_batch_broker_failure_is_retryable_without_duplicate_lesson(
    teacher_user, batch_setup
):
    folder, course = batch_setup
    with patch(
        "apps.courses.tasks.process_pdf_lesson_job.apply_async",
        side_effect=RuntimeError("secret must not escape"),
    ):
        first = import_pdf_directory(
            actor=teacher_user, course_id=course.id, directory=folder, execute=True
        )
    assert first["files"][0]["status"] == "queue_failed"
    assert "secret must not escape" not in str(first)
    with patch("apps.courses.tasks.process_pdf_lesson_job.apply_async"):
        second = import_pdf_directory(
            actor=teacher_user, course_id=course.id, directory=folder, execute=True
        )
    assert second["files"][0]["status"] == "queued"
    assert Lesson.objects.count() == 1
    assert LessonIngestionJob.objects.count() == 2
