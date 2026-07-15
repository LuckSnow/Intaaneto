---
name: intaaneto-rag
description: Build, review, debug, or extend Intaaneto's RAG-first learning assistant in the Django and React repository. Use for document ingestion, lesson knowledge indexing, chunking, embeddings, vector search, grounded chat, citations, exercise hints, RAG evaluation, AI provider integration, or changes under backend/apps/ai_assistant and related lesson APIs.
---

# Intaaneto RAG Core

## Mission

Make RAG the first dependable AI capability: answer from approved course and
lesson material, show evidence, respect access boundaries, and admit when the
material does not support an answer.

Do not prioritize avatar, video generation, voice, analytics, forum AI, or
agent orchestration until the RAG MVP acceptance criteria are met, unless the
user explicitly changes the priority.

## Start every task

1. Read [current-state.md](references/current-state.md).
2. Read `../intaaneto-web-security/SKILL.md` and its `rag-security.md` reference
   before changing ingestion, retrieval, chat scope, citations, uploads, student
   data, exercises, or deployment.
3. Read [project-scope.md](references/project-scope.md) when prioritizing product
   capabilities, defining research scope, or writing project reports.
4. Inspect the affected source files; repository code is the source of truth.
5. Read [architecture.md](references/architecture.md) for data flow, boundaries,
   or design work.
6. Read [delivery-plan.md](references/delivery-plan.md) for sequencing and MVP
   acceptance criteria.
7. Read [quality-and-safety.md](references/quality-and-safety.md) when changing
   retrieval, prompts, authorization, evaluation, or user-visible answers.
8. State the smallest vertical slice being changed and how it will be verified.

## Engineering rules

- Preserve Django app boundaries. Keep HTTP validation in serializers/views,
  RAG orchestration in services, and persistence in models/repositories.
- Keep ingestion separate from querying. Never parse or embed a document in a
  chat request.
- Index only a stable, normalized representation of teacher-approved lesson
  material. Track source, lesson, version or checksum, chunk position, and
  ingestion status.
- Filter retrieval by authorized course/lesson before ranking results. Never
  rely on the prompt to enforce data access.
- Put provider-specific embedding and generation calls behind interfaces.
  Keep model names, dimensions, limits, and keys in settings/environment.
- Make ingestion idempotent. Reprocessing unchanged content must not duplicate
  chunks; changed content must not leave active stale chunks.
- Return structured citations with stable IDs and lesson metadata. Do not use
  invented citations or raw prompt text as evidence.
- Prefer a grounded fallback when evidence is weak. Do not let general model
  knowledge masquerade as course content.
- Keep hints pedagogical: diagnose and guide without exposing `solution_code`
  or hidden test cases.
- Add focused tests for success, empty retrieval, authorization boundaries,
  stale re-indexing, provider failure, and malformed uploads as applicable.
- Do not add a framework such as LangChain unless it removes demonstrated
  complexity. A small explicit pipeline is preferred for the MVP.

## Target query contract

Treat this as the logical contract; evolve the HTTP schema deliberately:

```text
input:  question, optional session_id, required lesson_id or course scope
output: answer, citations[], retrieval metadata, grounded/fallback status
```

Each citation should identify at least the source document, lesson, chunk, and
a human-readable excerpt or location. Do not expose embeddings or private
provider diagnostics.

## Finish every RAG task

1. Run the narrowest relevant tests, then the broader backend suite when safe.
2. Check migrations when models change and API compatibility when schemas change.
3. Compare the result with the MVP criteria in `delivery-plan.md`.
4. Update `current-state.md` only for facts now proven by code or tests.
5. Record durable architecture choices in
   [decisions.md](references/decisions.md); replace the `Proposed` status only
   after the choice is implemented or explicitly accepted.
6. Report remaining risks and the next smallest vertical slice.
