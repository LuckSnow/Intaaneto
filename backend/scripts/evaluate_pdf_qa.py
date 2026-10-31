"""Run a private multi-PDF evaluation through the application's RAG services.

Run from backend: python scripts/evaluate_pdf_qa.py --help
No chat, enrollment, score, or progression records are written.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def private_json(path, value):
    with os.fdopen(
        os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600), "w"
    ) as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
    os.chmod(path, 0o600)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dataset", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--actor-id", required=True, type=int)
    p.add_argument(
        "--prepare-lessons",
        action="store_true",
        help="Create private draft evaluation lessons for unbound PDFs",
    )
    p.add_argument(
        "--ingestion-manifest",
        type=Path,
        help="Bind dataset PDFs to ready lessons by exact PDF checksum",
    )
    p.add_argument(
        "--repeats", type=int, default=1, help="Sequential repeats per question (1–5)"
    )
    p.add_argument("--confirm-provider-cost", action="store_true")
    p.add_argument("--request-delay-seconds", type=float, default=0, help="Pacing outside measured latency (0–60 seconds)")
    args = p.parse_args()
    if not args.confirm_provider_cost:
        p.error("--confirm-provider-cost is required for live generation")
    if not 1 <= args.repeats <= 5:
        p.error("--repeats must be between 1 and 5")
    if not 0 <= args.request_delay_seconds <= 60:
        p.error("--request-delay-seconds must be between 0 and 60")
    data = json.loads(args.dataset.read_text())
    if args.ingestion_manifest:
        manifest = json.loads(args.ingestion_manifest.read_text())
        if manifest.get("mode") != "execute":
            p.error("A dry-run manifest cannot be used to run evaluation")
        for source in data["sources"]:
            matches = [
                row
                for row in manifest["files"]
                if row.get("pdf_sha256") == source["pdf_sha256"]
                and row["status"] == "ready"
            ]
            lesson_ids = {row["lesson_id"] for row in matches}
            if len(lesson_ids) != 1:
                p.error(
                    "Every dataset PDF must have exactly one ready lesson in the manifest"
                )
            source.update(
                lesson_id=matches[0]["lesson_id"],
                storage_name=matches[0]["storage_name"],
            )
    if (
        data.get("schema_version") != 1
        or not 20 <= len(data["cases"]) <= 30
        or not 3 <= len(data["sources"]) <= 6
    ):
        p.error("Expected schema 1, 20–30 questions and 3–6 PDFs")
    ids = [c["id"] for c in data["cases"]]
    if len(set(ids)) != len(ids):
        p.error("Duplicate case IDs")
    sources = {source["id"]: source for source in data["sources"]}
    if len(sources) != len(data["sources"]):
        p.error("Duplicate source IDs")
    for case in data["cases"]:
        source = sources.get(case["source_id"])
        if (
            not source
            or not case["question"].strip()
            or not case["reference_answer"].strip()
        ):
            p.error("Invalid question or source reference")
        if bool(case["expected_pages"]) != case["answerable"] or any(
            not isinstance(page, int) or not 1 <= page <= source["page_count"]
            for page in case["expected_pages"]
        ):
            p.error("Invalid reference pages or answerability")

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
    import django

    django.setup()
    from django.conf import settings
    from django.contrib.auth import get_user_model
    from apps.courses.models import Course, Lesson
    from apps.courses.services import process_pdf_lesson
    from apps.ai_assistant.rag_services import (
        FastEmbedEmbeddingProvider,
        _authorized_retrieval_lesson,
    )
    from apps.ai_assistant.rag_answering import answer_lesson_question
    from apps.ai_assistant.services import get_generation_provider

    actor = get_user_model().objects.get(pk=args.actor_id, is_active=True)
    if actor.role not in ("teacher", "admin"):
        p.error("Use an authorized teacher/admin actor for this research service run")
    embedding = FastEmbedEmbeddingProvider()
    lessons = {}
    source_records = []
    for source in data["sources"]:
        needs_processing = False
        lid = source.get("lesson_id") or source.get("existing_lesson_id")
        if lid:
            lesson = _authorized_retrieval_lesson(actor, lid)
            if lesson.uploaded_file.name != source["storage_name"]:
                p.error("Lesson PDF does not match dataset storage reference")
        elif args.prepare_lessons:
            course, _ = Course.objects.get_or_create(
                slug="rag-pdf-evaluation-24-v1",
                defaults={
                    "title": "Thực nghiệm RAG 24 câu / 4 PDF",
                    "teacher": actor,
                    "description": "Private research evaluation corpus",
                    "is_published": False,
                },
            )
            if course.teacher_id != actor.id or course.is_published:
                p.error("Evaluation course must remain private and actor-owned")
            lesson, _ = Lesson.objects.get_or_create(
                course=course,
                slug=source["id"].lower(),
                defaults={
                    "title": source["title"],
                    "uploaded_file": source["storage_name"],
                    "is_published": False,
                    "is_preview": False,
                },
            )
            if (
                lesson.uploaded_file.name != source["storage_name"]
                or lesson.is_published
                or lesson.is_preview
            ):
                p.error("Existing draft does not match private evaluation source")
            needs_processing = True
        else:
            p.error("Unbound PDF: provide lesson_id or --prepare-lessons")
        # Verify actual remote PDF content, not just object name.
        with lesson.uploaded_file.open("rb") as f:
            digest = hashlib.sha256(f.read(20 * 1024 * 1024 + 1)).hexdigest()
        if digest != source["pdf_sha256"]:
            p.error("PDF checksum differs from the gold dataset")
        if needs_processing:
            process_pdf_lesson(actor=actor, lesson=lesson, embedding_provider=embedding)
        active = lesson.knowledge_sources.get(is_active=True, status="ready")
        if not active.chunks.exists():
            p.error("Active source has no chunks; finish indexing before evaluation")
        lessons[source["id"]] = lesson
        source_records.append(
            {
                "id": source["id"],
                "title": source["title"],
                "lesson_id": lesson.id,
                "pdf_sha256": digest,
                "source_id": active.id,
                "source_version": active.version,
                "source_checksum": active.content_checksum,
                "chunk_count": active.chunks.count(),
                "page_count": source["page_count"],
            }
        )
        print(f"Prepared {source['id']}: lesson {lesson.id}", flush=True)
    # Explicit warm-up excluded from timed cases; no generation request.
    embedding.embed_query("Khởi động mô hình nhúng câu hỏi")
    generation = get_generation_provider(settings.AI_GENERATION_PROVIDER)
    report = {
        "schema_version": 1,
        "dataset_id": data["dataset_id"],
        "dataset_sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "scope": "authorized teacher RAG service; warm embeddings; sequential repeats",
        "repeat_count": args.repeats,
        "question_count": len(data["cases"]),
        "expected_request_count": args.repeats * len(data["cases"]),
        "configuration": {
            "provider": settings.AI_GENERATION_PROVIDER,
            "model": {
                "gemini": settings.GEMINI_GENERATION_MODEL,
                "groq": settings.GROQ_GENERATION_MODEL,
                "openai": settings.AI_GENERATION_MODEL,
            }[settings.AI_GENERATION_PROVIDER],
            "embedding_model": embedding.model_name,
            "embedding_revision": embedding.model_revision,
            "top_k": settings.RAG_RETRIEVAL_TOP_K,
            "minimum_score": settings.RAG_RETRIEVAL_MIN_SCORE,
            "chunk_size": settings.RAG_CHUNK_SIZE,
            "chunk_overlap": settings.RAG_CHUNK_OVERLAP,
            "request_delay_seconds": args.request_delay_seconds,
        },
        "sources": source_records,
        "cases": [],
    }
    requests = [
        (run, case) for run in range(1, args.repeats + 1) for case in data["cases"]
    ]
    for run, case in requests:
        if report["cases"] and args.request_delay_seconds:
            time.sleep(args.request_delay_seconds)
        lesson = lessons[case["source_id"]]
        row = dict(case)
        row.update(question_id=case["id"], run=run)
        if args.repeats > 1:
            row["id"] = f"{case['id']}-R{run:02d}"
        expected_source = next(
            s for s in source_records if s["id"] == case["source_id"]
        )
        if not lesson.knowledge_sources.filter(
            pk=expected_source["source_id"],
            is_active=True,
            status="ready",
            content_checksum=expected_source["source_checksum"],
        ).exists():
            raise ValueError(
                "Source changed during evaluation; start a new versioned run"
            )
        started = time.perf_counter()
        try:
            result = answer_lesson_question(
                actor=actor,
                lesson=lesson,
                messages=[{"role": "user", "content": case["question"]}],
                embedding_provider=embedding,
                generation_provider=generation,
            )
            selected = {
                c["chunk_id"]
                for c in result.retrieval_metadata["retrieval"]["selected_chunks"]
            }
            row.update(
                answer=result.answer,
                grounded=result.grounded,
                retrieval=result.retrieval,
                citations=result.citations,
                tokens_used=result.tokens_used,
                retrieval_ms=result.retrieval_metadata["retrieval"]["latency_ms"],
                generation_ms=result.response_time_ms,
                error=None,
            )
            row["citation_scope_ok"] = (
                bool(result.citations)
                and all(
                    c["lesson_id"] == lesson.id and c["chunk_id"] in selected
                    for c in result.citations
                )
                if result.grounded
                else not result.citations
            )
            row["expected_page_hit"] = (
                any(
                    c["location"].get("page_start") is not None
                    and any(
                        c["location"]["page_start"] <= page <= c["location"]["page_end"]
                        for page in case["expected_pages"]
                    )
                    for c in result.citations
                )
                if case["answerable"]
                else None
            )
        except Exception as exc:
            row.update(
                answer="",
                grounded=False,
                citations=[],
                error=type(exc).__name__,
                citation_scope_ok=False,
                expected_page_hit=False if case["answerable"] else None,
            )
        row["latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
        report["cases"].append(row)
        private_json(args.output, report)
        print(
            f"{row['id']}: {row['latency_ms']} ms / {row['error'] or row['retrieval']['status']}",
            flush=True,
        )
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    private_json(args.output, report)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Never print provider/storage exception messages with private data.
        print(
            f"Evaluation stopped: {type(exc).__name__}. Check backend configuration privately.",
            file=sys.stderr,
        )
        sys.exit(1)
