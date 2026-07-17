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
2026-07-13. Retrieval was delivered separately in Slice 2.

- Add source/chunk persistence and vector capability.
- Normalize `Lesson.content` or `Lesson.extracted_text`.
- Implement deterministic chunking, embedding, and idempotent re-indexing.
- Expose indexing through an admin/service/management command first.

Exit: one lesson can be indexed twice without duplicates, and a changed lesson
atomically replaces active chunks.

## Slice 2 — Retrieve evidence

Status: Implemented and covered by authorization, source-version, relevance,
weak-evidence, and PostgreSQL exact-cosine checks on 2026-07-14. The retrieval
service intentionally has no public HTTP surface; Slice 3 consumes it from the
authorized lesson-chat boundary.

- Add lesson-scoped retrieval with authorization enforced before search.
- Return ranked chunks and stable metadata without invoking an LLM.
- Create a small Vietnamese question/relevance fixture set.

Exit: relevant lesson chunks beat irrelevant chunks on the fixture set, empty
or weak evidence is distinguishable, and cross-course leakage tests pass.

## Slice 3 — Grounded answers and citations

Status: Implemented on 2026-07-14 and extended on 2026-07-17. Lesson chat retrieves within its authorized
scope, avoids generation for weak/missing evidence, supplies bounded untrusted
evidence to the provider, constructs citations in application code, persists
safe retrieval metadata, restores the latest bounded authorized lesson session
and database-owned citations after reload, and displays grounded/fallback
evidence state. Revoked access hides persisted session data. OpenAI
and Gemini generation adapters are selectable; a successful live-provider smoke
remains an environment/quota-dependent check.

- Generate from retrieved chunks only under a strict tutoring prompt.
- Return structured citations and a grounded/fallback indicator.
- Persist useful latency/token/retrieval metadata without secrets.
- Update lesson chat to send `lesson_id`, never the lesson summary as prompt text.

Exit: answers cite actual chunks, unsupported questions decline or redirect,
and API contract tests pass.

## Slice 4 — Upload ingestion

Status: Implemented for the development prototype. The initial synchronous
PDF-only path landed on 2026-07-15. On 2026-07-17 structured per-chunk PDF page ranges were added,
backfilled in PostgreSQL, propagated through retrieval/chat/reinforcement
citations, and rendered in the lesson UI. Upload/reprocess now create constrained
database jobs and return `202`; a non-root Celery worker consumes Redis/AOF jobs,
rechecks authorization, retries transient failures within a hard bound, and
persists safe polling state. A live broker/worker idempotency smoke passed.

- Accept only PDF uploads; DOCX, PPT, and PPTX are deliberately out of scope.
- Validate the allowlisted file type, content signature, structure, and size.
- Extract PDF page locations.
- Move expensive work to a retriable background job when infrastructure exists.
- Surface processing status and safe error messages.

Exit: upload-to-query works for representative PDF fixtures, retries do not
duplicate data, and malformed/encrypted/empty files fail safely.

The exit criteria are met. Parser subprocess wall-clock isolation, malware
scanning, orphan cleanup, and production broker HA/monitoring remain deployment
hardening rather than claims of this development prototype.

## Slice 5 — Evaluate and harden

Status: In progress. A versioned eight-case Vietnamese retrieval dataset and an
authorized, generation-free evaluation command were implemented on 2026-07-16.
The first harness reports status accuracy, expected-source recall, pass rate,
latency, and retrieval configuration. The first PostgreSQL/FastEmbed run is
recorded with `0.75` pass rate and `1.00` expected-source recall. A second,
authorized full-pipeline command now measures grounded/refusal contract,
application-owned citation scope, a clearly labeled lexical marker proxy,
latency, and reported tokens. It requires explicit provider-cost confirmation
and omits raw questions/answers by default. The first live Gemini baseline was
recorded on 2026-07-17: contract pass `0.75`, citation scope `1.00`, refusal
`1.00`, strict lexical proxy pass `0.50`, and warm mean latency `1515.62 ms`.
Report schema 2 separates contract pass from exact-marker proxy so neither is
misstated as semantic accuracy. A private two-rater export and aggregate-only
agreement command now make semantic/pedagogical review reproducible without
committing raw provider output. Dataset expansion, holdout split, completed
human ratings, and adjudication remain.

- Version an evaluation set with answerability and expected sources.
- Track retrieval recall/precision proxy, citation correctness, groundedness,
  refusal quality, latency, and cost.
- Add prompt-injection fixtures embedded inside source documents.
- Tune chunk/retrieval settings from measured results.

## Assessment loop A — Deterministic progression baseline

Status: Implemented on 2026-07-16 with backend contract/security tests and a
learner lesson-page flow. This is the control baseline for later AI-dialogue
assessment, not a claim that AI grading is complete.

- Attach one versioned, teacher-authored multiple-choice assessment to a lesson.
- Hide answer keys from learners and calculate score/pass state in the backend.
- Preserve immutable attempt/answer evidence and aggregate current mastery.
- Block normal lesson progression until the learner passes the published
  assessment; return weak learning objectives after a failed attempt.
- Keep an assessment immutable after attempts exist in this initial slice.

Exit: enrolled learners can take a lesson assessment, cannot forge score or
progression, receive an explainable result, and advance only after a passing
server-owned decision. Cross-enrollment and teacher-ownership tests pass.

RAG-grounded reinforcement tied to weak objectives was added on 2026-07-16 as a
separate bounded retrieval action with application-owned citations. It does not
change the deterministic result or invoke generation during grading.

## Assessment loop B — Post-pass dialogue recommendation

Status: Implemented as a bounded product/research seam on 2026-07-17; calibration
and human evaluation remain.

- Require enrollment and a passed current-version deterministic attempt.
- Resolve question, objective and rubric from the server-owned assessment.
- Retrieve only inside the authorized lesson and skip generation on weak evidence.
- Strictly parse a recommendation and return application-owned citations.
- Persist only an HMAC answer digest and bounded audit metadata.
- Never mutate score, mastery, completion or progression.

Software exit met: access/question scope, fallback, provider failure/malformed
output, prompt-data separation, no-state-mutation, throttling and lesson UI are
covered. Research exit remains: human-labeled Vietnamese free-text cases,
agreement/false-pass/false-fail/stability measurement, teacher calibration and a
separate policy decision before any AI outcome may affect progression.

Learner and owned-course teacher progress reports were implemented on
2026-07-16 from deterministic attempt/progression evidence. On 2026-07-17 the
owned-course report gained bounded CSV export and an aggregate objective
distribution based on each learner's latest current-version attempt; nine
reporting tests cover scope, versioning, privacy, and spreadsheet injection.
On 2026-07-17 reinforcement requests gained minimal audit events and a bounded
owned-course paired outcome report. It compares the first usable exposure for a
failed attempt with the first same-version follow-up, omits identities, and
labels the result observational rather than causal. A real usage baseline,
time-series exports, and a bounded conversational rubric remain later work.

Next: run a consented/approved Vietnamese-input SadTalker render and record the
quality/resource rubric; the technical upstream-asset smoke is not
video-quality or content-rights evidence.

## Virtual lecturer A — Local SadTalker adapter

Status: Adapter implemented on 2026-07-16 and hardened on 2026-07-17 with nine
focused tests. A pinned local runtime produced a technical GPU MP4, while the
consented Vietnamese-content quality experiment remains unverified.

- Authorize teacher ownership before reading inputs.
- Require explicit approval/rights confirmation and record input checksums.
- Validate bounded script, PCM WAV, portrait, runtime timeout, and MP4 output.
- Invoke upstream `inference.py` without a shell from a separately configured
  runtime; never run it in an HTTP request.
- Attach a successful server-named video to the lesson while keeping video
  optional for text/RAG/assessment readiness.

Exit for adapter: fake-provider success/failure and negative security tests pass,
job lifecycle is auditable, and the frontend can play the attached file.

Technical runtime exit met on 2026-07-17: the read-only mounted runtime generated
one 1.48-second H.264/AAC MP4 in 53 seconds on an NVIDIA T1200. This used an
upstream demo asset and is evidence of execution only.

Exit for real PoC (not yet met): record one consented-input render with pinned
SadTalker commit/checkpoints, environment, latency/resource data, and qualitative
lip-sync/artifact review.

## Learning corpus A — Reviewed Markdown to draft lessons

Status: Implemented on 2026-07-16 and extended on 2026-07-17. Eight corpus tests
and eight separate assessment-blueprint tests pass; both commands have a
database-free dry run against checked-in authoring data.

- Compile two versioned Markdown sources into 2 courses and 15 bounded lessons.
- Add lesson objectives and primary references without embedding assessment
  answer keys.
- Require a verified teacher for writes and default all new records to drafts.
- Keep publication and vector indexing as separate, explicit approval actions.
- Reject ownership/manual/PDF collisions atomically and remain idempotent.

Exit: the checked-in corpus validates reproducibly, imports without duplicates
or unrelated derived state, and can be reviewed before publication/indexing.

Three representative lessons now have curated assessment blueprints totaling 27
questions, with three questions for each declared objective. They import as
drafts through a separate owner-checked, atomic command and never enter RAG
content. Next: a teacher must review/publish them and E2 needs independent raters
and response cases; checked-in authoring is not human-study evidence. The generic
weak-objective reinforcement path is already implemented.

An E2 software baseline now covers 81 balanced response rows and 12 scoring
profiles, including the 7/9 pass and 6/9 fail boundary at 70%. Production grading
and the harness share the deterministic score calculator. Private `0600` review
templates and a strict two-rater aggregate command are ready, but no reviewer
ratings, adjudication, or agreement result may be claimed yet.

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
