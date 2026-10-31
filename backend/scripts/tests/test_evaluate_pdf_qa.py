import hashlib
import json
from unittest.mock import Mock, patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.ai_assistant.models import KnowledgeSource, KnowledgeChunk, ChatSession
from apps.ai_assistant.rag_answering import GroundedAnswer
from apps.courses.models import Course, Lesson
from apps.courses.test_pdf_ingestion import make_pdf
from scripts.evaluate_pdf_qa import main


@pytest.fixture
def runner_data(teacher_user, tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path / "media"
    course = Course.objects.create(
        title="Research", slug="runner-research", teacher=teacher_user
    )
    sources, files = [], []
    for i in range(4):
        content = make_pdf(f"Lecture {i} RAG content")
        lesson = Lesson.objects.create(
            course=course,
            title=f"PDF{i}",
            slug=f"pdf{i}",
            uploaded_file=SimpleUploadedFile(f"pdf{i}.pdf", content),
            is_published=False,
        )
        source = KnowledgeSource.objects.create(
            lesson=lesson,
            source_type="extracted_text",
            version=1,
            content_checksum="a" * 64,
            normalized_text="Lecture",
            status="ready",
            is_active=True,
            embedding_provider="test",
            embedding_model="test",
            embedding_revision="v1",
            embedding_dimension=3,
            chunker_version="test",
            chunk_size=100,
            chunk_overlap=10,
        )
        KnowledgeChunk.objects.create(
            source=source,
            ordinal=0,
            text="Lecture",
            start_offset=0,
            end_offset=7,
            char_count=7,
            embedding=[1, 0, 0],
            page_start=1,
            page_end=1,
        )
        digest = hashlib.sha256(content).hexdigest()
        sources.append(
            dict(
                id=f"PDF{i}",
                title=f"PDF{i}",
                storage_name="unbound",
                pdf_sha256=digest,
                page_count=1,
            )
        )
        files.append(
            dict(
                status="ready",
                pdf_sha256=digest,
                lesson_id=lesson.pk,
                storage_name=lesson.uploaded_file.name,
            )
        )
    cases = [
        dict(
            id=f"Q{i:02d}",
            source_id=f"PDF{i%4}",
            question=f"Question {i}",
            reference_answer="Reference",
            answerable=i % 6 != 5,
            expected_pages=[1] if i % 6 != 5 else [],
            rubric=["point"],
        )
        for i in range(24)
    ]
    dataset, manifest, output = (
        tmp_path / name for name in ("dataset.json", "manifest.json", "results.json")
    )
    dataset.write_text(
        json.dumps(
            dict(schema_version=1, dataset_id="SYNTHETIC", sources=sources, cases=cases)
        )
    )
    manifest.write_text(json.dumps(dict(mode="execute", files=files)))
    argv = [
        "evaluate_pdf_qa.py",
        "--dataset",
        str(dataset),
        "--ingestion-manifest",
        str(manifest),
        "--actor-id",
        str(teacher_user.pk),
        "--output",
        str(output),
        "--repeats",
        "2",
        "--confirm-provider-cost",
    ]
    return argv, manifest, output


@pytest.mark.django_db
def test_runner_binds_manifest_and_repeats_without_chat_writes(
    runner_data, monkeypatch
):
    monkeypatch.setattr("sys.argv", runner_data[0])
    answer = GroundedAnswer(
        answer="Reference",
        citations=[],
        grounded=False,
        retrieval={"status": "weak_evidence"},
        retrieval_metadata={"retrieval": {"selected_chunks": [], "latency_ms": 1}},
    )
    with patch(
        "apps.ai_assistant.rag_services.FastEmbedEmbeddingProvider",
        return_value=Mock(model_name="test", model_revision="v1"),
    ), patch(
        "apps.ai_assistant.services.get_generation_provider", return_value=Mock()
    ), patch(
        "apps.ai_assistant.rag_answering.answer_lesson_question", return_value=answer
    ) as call:
        main()
    report = json.loads(runner_data[2].read_text())
    assert len(report["cases"]) == 48 and report["repeat_count"] == 2
    assert len({row["id"] for row in report["cases"]}) == 48
    assert call.call_count == 48
    assert all(len(c.kwargs["messages"]) == 1 for c in call.call_args_list)
    assert all(s["chunk_count"] == 1 for s in report["sources"])
    assert ChatSession.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize("failure", ["no_chunks", "not_ready"])
def test_runner_rejects_unindexed_before_generation(runner_data, monkeypatch, failure):
    monkeypatch.setattr("sys.argv", runner_data[0])
    if failure == "no_chunks":
        KnowledgeChunk.objects.all().delete()
    else:
        manifest = json.loads(runner_data[1].read_text())
        manifest["files"][0]["status"] = "queued"
        runner_data[1].write_text(json.dumps(manifest))
    with patch("apps.ai_assistant.services.get_generation_provider") as provider:
        with pytest.raises(SystemExit):
            main()
    provider.assert_not_called()
