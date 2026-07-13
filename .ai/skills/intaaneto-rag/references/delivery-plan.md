# RAG delivery plan

Complete vertical slices in order. Do not build the full multimedia pipeline in
parallel with this core unless the user explicitly reprioritizes it.

## Slice 0 — Repair the chat seam

Status: Implemented and covered by contract tests on 2026-07-13. A live
provider smoke test remains environment-dependent.

- Align frontend/backend request and response schemas.
- Modernize or replace the broken provider call behind an interface.
- Add provider timeout/error behavior and bounded history.
- Add endpoint/service tests for the current non-RAG chat behavior.

Exit: authenticated lesson chat works predictably and failures are explicit.

## Slice 1 — Index one lesson

Status: Implemented and covered by idempotency, rollback, and ownership tests on
2026-07-13. Retrieval remains Slice 2.

- Add source/chunk persistence and vector capability.
- Normalize `Lesson.content` or `Lesson.extracted_text`.
- Implement deterministic chunking, embedding, and idempotent re-indexing.
- Expose indexing through an admin/service/management command first.

Exit: one lesson can be indexed twice without duplicates, and a changed lesson
atomically replaces active chunks.

## Slice 2 — Retrieve evidence

- Add lesson-scoped retrieval with authorization enforced before search.
- Return ranked chunks and stable metadata without invoking an LLM.
- Create a small Vietnamese question/relevance fixture set.

Exit: relevant lesson chunks beat irrelevant chunks on the fixture set, empty
or weak evidence is distinguishable, and cross-course leakage tests pass.

## Slice 3 — Grounded answers and citations

- Generate from retrieved chunks only under a strict tutoring prompt.
- Return structured citations and a grounded/fallback indicator.
- Persist useful latency/token/retrieval metadata without secrets.
- Update lesson chat to send `lesson_id`, never the lesson summary as prompt text.

Exit: answers cite actual chunks, unsupported questions decline or redirect,
and API contract tests pass.

## Slice 4 — Upload ingestion

- Validate approved file types and sizes.
- Extract PDF/PPT locations and preserve page/slide metadata.
- Move expensive work to a retriable background job when infrastructure exists.
- Surface processing status and safe error messages.

Exit: upload-to-query works for representative PDF/PPT fixtures, retries do not
duplicate data, and malformed/encrypted/empty files fail safely.

## Slice 5 — Evaluate and harden

- Version an evaluation set with answerability and expected sources.
- Track retrieval recall/precision proxy, citation correctness, groundedness,
  refusal quality, latency, and cost.
- Add prompt-injection fixtures embedded inside source documents.
- Tune chunk/retrieval settings from measured results.

## MVP acceptance criteria

- A student can ask in Vietnamese about an authorized lesson.
- The answer is supported by approved lesson material and includes usable
  citations to its source locations.
- Unsupported questions receive a clear fallback rather than invented facts.
- Re-indexing is deterministic and does not leave duplicate active knowledge.
- A student cannot retrieve chunks from an unauthorized course or lesson.
- Provider and parser failures are observable, bounded, and safe to retry.
- Automated tests cover ingestion, retrieval, grounding contract, citations,
  access isolation, and failure paths.
- A small checked-in evaluation dataset provides a repeatable baseline.
