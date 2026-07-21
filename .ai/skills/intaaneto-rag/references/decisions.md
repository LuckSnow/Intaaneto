# Architecture decisions

Keep entries concise. `Proposed` means guidance, not an implemented fact. When a
decision is accepted or implemented, change its status and add the date plus
affected files or migration.

## RAG-001 — RAG before multimedia

- Status: Accepted by product direction
- Date: 2026-07-13
- Decision: Treat grounded retrieval and learning assistance as the AI core;
  defer avatar, video, and voice work until RAG MVP criteria are met.
- Reason: Other AI experiences depend on trustworthy lesson knowledge.

## RAG-002 — PostgreSQL vector storage for MVP

- Status: Implemented
- Date: 2026-07-13
- Affected: `docker-compose.yml`, `backend/requirements.txt`, and
  `ai_assistant.0003`
- Decision: Add pgvector to the existing PostgreSQL deployment instead of a
  separate vector database.
- Reason: Minimize infrastructure and keep authorization metadata with Django
  entities while corpus scale is still small.
- Revisit when: measured scale, filtering, latency, or operations demand a
  dedicated search system.

## RAG-003 — Explicit pipeline over orchestration framework

- Status: Implemented for lesson indexing
- Date: 2026-07-13
- Affected: `backend/apps/ai_assistant/rag_services.py`
- Decision: Implement narrow Python/Django service interfaces before adopting
  LangChain, LlamaIndex, or an agent framework.
- Reason: The MVP pipeline is small and needs transparent authorization,
  citations, failure handling, and tests.
- Revisit when: repeated orchestration complexity is demonstrated in code.

## RAG-004 — Lesson scope before course scope

- Status: Implemented for retrieval
- Date: 2026-07-14
- Affected: `backend/apps/ai_assistant/access.py`,
  `backend/apps/ai_assistant/rag_services.py`, and retrieval tests
- Decision: Ship retrieval scoped to one authorized lesson, then expand to an
  enrolled course.
- Reason: It gives a small vertical slice and clearer evaluation ground truth.

## RAG-005 — Hybrid local embedding and online generation

- Status: Implemented for the current provider seams
- Date: 2026-07-13
- Affected: `backend/apps/ai_assistant/rag_services.py` and
  `backend/config/settings/base.py`
- Decision: Run embeddings locally and access the response/generation model
  through a configurable online API for the first prototype.
- Reason: Local embedding controls indexing cost and document handling, while an
  online generator provides stronger response quality without hosting a large
  language model.
- Constraint: Persist embedding model name, version, and dimension. Changing any
  of them requires a controlled full re-index.

## RAG-006 — Object storage is not the knowledge index

- Status: Proposed
- Decision: Use Cloudflare R2 or equivalent for original/generated files and
  PostgreSQL plus pgvector for chunks and embeddings. Treat Google Drive only as
  an optional early research-data source, not the runtime vector store.
- Reason: Retrieval needs vector similarity, metadata filtering, versioning,
  transactional updates, and authorization relationships.

## RAG-007 — Defer a fixed vector dimension and ANN index

- Status: Accepted and implemented for Slice 1
- Date: 2026-07-13
- Decision: Store pgvector values without a schema-fixed dimension while
  persisting and validating provider, model, revision, and dimension on every
  source version. Add an ANN index only after the embedding baseline is
  evaluated; retrieval must filter to a compatible active source first.
- Reason: The initial 384-dimensional multilingual model is provisional. This
  avoids a schema migration merely to compare another local model while keeping
  each active lesson index internally dimension-consistent.

## RAG-008 — Exact filtered cosine retrieval baseline

- Status: Implemented
- Date: 2026-07-14
- Affected: `backend/apps/ai_assistant/rag_services.py`, retrieval settings, and
  `backend/apps/ai_assistant/test_rag_retrieval.py`
- Decision: Resolve one authorized lesson and compatible active source before
  exact pgvector cosine ranking. Use a configurable top-k and a provisional
  minimum similarity threshold of `0.45`; do not invoke an LLM in this service.
- Reason: Exact search is transparent and sufficient for the current small
  corpus, provides a measurable retrieval baseline, and prevents global search
  results from crossing the access boundary.
- Revisit when: the Vietnamese evaluation set justifies threshold/model tuning,
  reranking, hybrid retrieval, or an ANN index.

## RAG-009 — Application-owned grounded citations and fallback

- Status: Implemented
- Date: 2026-07-14
- Affected: `backend/apps/ai_assistant/rag_answering.py`, `services.py`,
  `views.py`, migration `0004`, and `frontend/src/pages/LessonPage.jsx`
- Decision: Skip generation unless lesson-scoped evidence clears the configured
  threshold. Supply bounded evidence as untrusted data, generate a plain answer,
  and construct citation objects only from the selected authorized chunks in
  application code.
- Reason: The generation model must not control access scope or fabricate source
  identifiers. Deterministic fallback also avoids cost and hallucination when the
  lesson cannot support an answer.
- Constraint: Persist only bounded retrieval identifiers/scores/latency with the
  message; do not persist embeddings, provider diagnostics, or full prompts.

## RAG-010 — Explicit online generation provider selection

- Status: Implemented
- Date: 2026-07-21
- Affected: `backend/apps/ai_assistant/services.py`, generation settings,
  environment example, and provider tests
- Decision: Select direct OpenAI, Gemini, or Groq generation explicitly through a
  server-side setting. Keep separate credentials and use each compatible endpoint
  through the existing SDK and provider protocol. Permit an evaluation command to
  select a provider explicitly without changing the runtime default.
- Reason: Provider choice must be replaceable without coupling lesson indexing,
  authorized retrieval, prompts, or application-owned citations to one vendor.
- Constraint: Fail closed for a missing key or unknown provider. Free-tier
  providers are for non-sensitive prototype material only unless their data
  handling terms meet the deployment's privacy requirements.

## RAG-011 — Reproducible source seed instead of shared development databases

- Status: Implemented
- Date: 2026-07-15
- Affected: `seed_demo_data`, its tests, environment example, and `docs/SETUP.md`
- Decision: Recreate a minimal text-only RAG course from an idempotent management
  command on each developer database. Do not distribute local database dumps,
  media, chat history, vectors, or fixed login credentials as demo data.
- Reason: Migrations plus deterministic source data are reviewable and portable,
  while database volumes contain machine-local and potentially private state.
- Constraint: Vector indexing remains explicit because it depends on the local
  embedding model/configuration and may download model weights on first use.

## RAG-012 — Limit lesson document ingestion to PDF

- Status: Implemented for the current upload contract
- Date: 2026-07-15
- Affected: course upload serializer/service/view, PDF ingestion tests, frontend
  teacher upload page, and document-processing dependencies
- Decision: Support teacher-uploaded PDF lesson documents only. DOCX, PPT, and
  PPTX uploads are outside the ingestion target.
- Reason: One format covers the required learning-material workflow while
  keeping parser validation, page metadata, fixtures, and security testing small
  enough for a focused vertical slice.
- Implementation note: Slice 4 replaced the legacy PDF/PPTX upload contract and
  later moved extraction/indexing to the bounded job design in RAG-019.

## RAG-013 — Evaluate retrieval before tuning it

- Status: Implemented for the initial Slice 5 harness
- Date: 2026-07-16
- Affected: `backend/apps/ai_assistant/rag_evaluation.py`, the bundled Vietnamese
  evaluation dataset, demo seed content, evaluation command, and tests
- Decision: Keep a versioned evaluation dataset tied to non-sensitive,
  reproducible demo lesson material and run it through the same authorized
  lesson-retrieval service used by chat. Record provider/source configuration and
  bounded metrics without invoking answer generation or logging raw evidence.
- Reason: Retrieval quality and threshold changes need repeatable evidence while
  authorization and observability boundaries remain identical to the product
  path.
- Revisit when: the dataset is large enough to split development and holdout
  cases, or grounded-answer evaluation requires a separately versioned rubric.

## RAG-014 — Deterministic assessment before AI grading

- Status: Implemented for the first lesson-assessment slice
- Date: 2026-07-16
- Affected: exercises assessment models/API/tests, course progression service,
  enrollment mastery, and `frontend/src/pages/LessonPage.jsx`
- Decision: Establish a teacher-authored multiple-choice assessment with a
  server-calculated configurable threshold, immutable attempt snapshots, and
  server-owned progression before allowing an AI-generated grade to affect
  learner state.
- Reason: The research project needs an explainable baseline for scoring,
  progression, consistency, and access control before comparing or calibrating
  conversational AI evaluation.
- Constraint: Retrieval similarity is evidence availability, not learner
  mastery. Future AI grades remain recommendations until a versioned rubric and
  evaluation set show sufficient accuracy and consistency.

## RAG-015 — Reviewed Markdown corpus imports as drafts before indexing

- Status: Implemented for the initial two-course corpus
- Date: 2026-07-16
- Affected: `backend/apps/courses/learning_corpus.py`,
  `import_learning_corpus`, its tests, the two authoring documents, Docker
  Compose, and `docs/SETUP.md`
- Decision: Compile versioned, repository-reviewed Markdown sections into stable
  text lessons through an idempotent management command. Database imports
  default to drafts and require an active verified teacher; publication and RAG
  indexing are explicit later operations.
- Reason: The project needs reusable learning content without treating raw
  notes as approved knowledge, coupling source editing to vectors, or sharing a
  development database. Stable slugs and deterministic content let existing
  source checksums/versioning handle later re-indexing.
- Constraint: Never overwrite a PDF lesson, a manually authored same-slug
  lesson, or a course owned by another teacher. Do not place assessment answer
  keys in indexed corpus documents.

## RAG-016 — Reinforcement retrieves weak objectives without grading by AI

- Status: Implemented for current-version failed attempts
- Date: 2026-07-16
- Affected: `backend/apps/exercises/reinforcement.py`, assessment API/tests,
  RAG settings, and `frontend/src/pages/LessonPage.jsx`
- Decision: Make reinforcement a separate learner-triggered retrieval action.
  Resolve the owned immutable attempt first, retrieve bounded evidence for its
  server-recorded weak objectives inside the assessment lesson, and construct
  citations in application code without calling an LLM.
- Reason: Retrieval can guide review immediately while deterministic grading
  remains the trusted control. Separating it from submission avoids making
  scoring depend on embedding availability or incurring hidden provider work.
- Constraint: Reinforcement never changes score, mastery, completion, or
  progression. Passed, stale, and foreign attempts are not eligible, and a
  generated Tutor question is only prefilled for the learner to send explicitly.

## RAG-017 — Progress reports derive from deterministic learning records

- Status: Implemented for learner and owned-course dashboards
- Date: 2026-07-16
- Affected: analytics progress reporting API/tests and frontend dashboard
- Decision: Calculate current reports from enrollment progress/mastery, lesson
  completion, and attempts matching the assessment's current version. Do not use
  the legacy mutable `LearningAnalytics` counters as assessment evidence.
- Reason: The research report needs reproducible metrics tied to the same
  server-owned progression baseline used by the product, without presenting
  stale counters or retrieval similarity as learner mastery.
- Constraint: Learners receive only their records. Teachers receive aggregates
  and a paged roster for owned courses; reports omit email, answers, chat, and
  old-version attempts. Admin scope remains explicit and audited separately.

## RAG-018 — SadTalker PoC is local, manual, bounded, and audited

- Status: Initial command implemented; technical GPU smoke verified; web queue
  extension is governed by RAG-022
- Date: 2026-07-16
- Affected: video job model/migration/admin, local provider/command/tests,
  lesson video serialization/UI, environment example, and `docs/SADTALKER_POC.md`
- Decision: Keep SadTalker outside HTTP and invoke its CLI only from a trusted
  management command after ownership and explicit rights/approval checks.
  Validate bounded WAV/portrait/script inputs, execute without a shell and with
  timeout, validate one MP4, and persist checksums plus a safe lifecycle record.
- Reason: SadTalker's GPU dependency stack must not destabilize Django/RAG, and
  generated likeness/audio introduces consent, provenance, abuse, resource, and
  failure concerns that an inline request cannot handle safely.
- Constraint: SadTalker is not TTS and requires no API key. A fake-provider test
  proves the adapter contract only; the thesis cannot claim real video quality
  until a recorded run uses reviewed checkpoints and consented inputs.

## RAG-019 — PDF ingestion uses durable DB state plus Celery/Redis

- Status: Implemented for development Compose
- Date: 2026-07-17
- Affected: course ingestion job/model/task/API/tests, Celery configuration,
  Redis/worker Compose services, teacher upload polling UI, setup and API docs
- Decision: Persist one active ingestion job per lesson before dispatch. Return
  `202 Accepted`, process PDF extraction/embedding in a non-root Celery worker,
  reauthorize ownership in the worker, retry only safe transient failures within
  a fixed bound, and use lesson/job database state—not Celery results—as the
  product polling contract.
- Reason: PDF parsing and local embedding must not hold open an HTTP request;
  broker/process failures must be observable and retryable without duplicating
  active sources or exposing exception/broker metadata.
- Constraint: Redis/AOF in development is evidence of broker delivery, not a
  production HA guarantee. Parser wall-clock isolation, malware scanning,
  monitoring, orphan cleanup and production object storage remain separate.

## RAG-020 — Human RAG review uses one immutable private answer package

- Status: Implemented for the E1 review workflow
- Date: 2026-07-17
- Affected: grounded-answer evaluation, private review/aggregate commands,
  focused tests, and `docs/RAG_GROUNDED_ANSWER_EVALUATION.md`
- Decision: Generate both independent reviewer sheets from one provider run,
  bind their bounded demo questions/answers/citations to the same digest, store
  them as local `0600` files, and emit only agreement aggregates after review.
- Reason: Lexical markers do not measure semantic or pedagogical quality, while
  separate live runs would expose reviewers to different stochastic outputs.
- Constraint: Tooling and blank sheets are not human evidence. No accuracy,
  agreement, or pedagogical-quality claim is allowed before two real reviewers
  finish the same package and disagreements are adjudicated.

## RAG-021 — Dialogue assessment starts post-pass and recommendation-only

- Status: Implemented for the first software seam
- Date: 2026-07-17
- Affected: exercises dialogue-check model/service/API/tests, structured AI
  recommendation parser, lesson UI, throttling and documentation
- Decision: Permit a RAG-grounded free-text check only after the learner passes
  the current deterministic assessment. Its outcome is optional feedback and
  cannot affect progression.
- Reason: The thesis needs a dialogue-evaluation seam, but an uncalibrated model
  must not create false passes/fails or weaken the explainable baseline.
- Constraint: Audit stores an HMAC answer digest and bounded metadata, not raw
  answer/rubric/key/feedback. Grading use requires human-labeled evaluation,
  teacher review, an appeal path and a separate architecture decision.

## RAG-022 — Generated lesson artifacts remain reviewed drafts

- Status: Implemented for summary, assessment, local narration and video enqueue
- Date: 2026-07-17
- Affected: lesson authoring models/services/API/UI, AI provider adapter,
  dedicated video worker, migration `courses.0007`, tests and operations docs
- Decision: Generate summaries and five-question assessments only as teacher-
  reviewable drafts from the active ready lesson source. Only explicit summary
  approval updates learner-visible state; assessments remain unpublished until
  the existing teacher publish action. Bind local narration and SadTalker input
  to the approved summary checksum, require portrait rights confirmation, and
  render on a dedicated one-at-a-time GPU queue.
- Reason: LLM output is untrusted authoring assistance, not authoritative course
  content or grading policy. Review gates prevent hallucinated text/answer keys
  from silently reaching learners, while a separate queue keeps GPU work from
  delaying PDF ingestion.
- Constraint: Provider calls require deliberate server-side configuration and
  may send bounded lesson text to that provider. `espeak-ng` and SadTalker use no
  API key, but a technical smoke is not evidence of natural voice, lip-sync or
  pedagogical quality. Video remains optional; consented Vietnamese input and
  quality measurement are still required.

## RAG-023 — Local slide video replaces talking-head generation in the web flow

- Status: Implemented for the first deterministic multimedia slice
- Date: 2026-07-19
- Affected: `LessonMultimediaJob`/migration `courses.0008`, local Piper/Pillow/
  FFmpeg services and task, authoring API/UI, Compose/runtime configuration,
  focused tests, and `docs/LOCAL_MULTIMEDIA_SETUP.md`
- Decision: Build optional lesson video only from the current teacher-approved
  summary. Run Vietnamese Piper TTS, deterministic slide/caption rendering and
  FFmpeg composition on the normal Celery worker, using the repository AI Tutor
  asset as a fixed corner presenter. Keep SadTalker and D-ID outside the active
  teacher web flow.
- Reason: Static slide composition is CPU-local, bounded and materially faster
  than the measured non-viable laptop SadTalker render while satisfying the
  requirement that lesson video contain readable instructional text.
- Constraint: The first two live local runs establish technical execution and
  bounded performance only, not Vietnamese voice or pedagogical quality. The
  owner approved the current voice and tutor asset for school research use;
  public/commercial distribution requires a separate rights review. The model is
  installed explicitly rather than downloaded during an HTTP request. Video
  failure never changes RAG readiness, assessment, score, mastery or progression.

## RAG-024 — Assessment coverage scales in atomic five-question batches

- Status: Implemented for teacher-reviewed assessment authoring
- Date: 2026-07-19
- Affected: lesson authoring service/API/UI, generation prompt/settings, focused
  authoring/provider tests, and current documentation
- Decision: Recommend 5, 10 or 15 questions from the active RAG source's chunk
  count, permit an explicit teacher override of 5, 10, 15 or 20, and generate
  each group of five from a different bounded source region. Show and confirm the
  resolved question count and provider-call count before generation.
- Reason: A fixed five-question draft under-covers dense lessons, while a fixed
  large minimum is wasteful for short material. Small batches preserve the
  provider's strict structured-output contract and make coverage/cost visible.
- Constraint: Each batch remains untrusted provider output. Reject duplicate or
  incomplete batches and persist nothing until all batches pass validation and
  the active source is rechecked. The result remains an unpublished teacher-
  reviewed draft and never changes learner state automatically.

## RAG-025 — Long-form video script is separate reviewed lesson state

- Status: Implemented for local slide-video authoring
- Date: 2026-07-19
- Affected: `LessonVideoScriptDraft`/migration `courses.0009`, authoring provider,
  service/API/UI, Piper configuration, multimedia queue/worker and focused tests
- Decision: Keep the learner summary bounded and concise. Generate a separate
  4–5 minute video-script draft from the current approved summary plus a bounded
  start/middle/end sample of the active RAG source, disclose that this is one
  provider call, and require explicit teacher approval. Bind the script to the
  source and summary checksums before local narration/rendering.
- Reason: Reusing a short summary forced short videos, while enlarging the
  learner summary would mix two different pedagogical purposes. A dedicated
  draft supports richer narration without silently changing learner-visible
  summary content.
- Constraint: Provider output remains untrusted and cannot enqueue video until
  reviewed. Script input is capped at 4,800 characters/50 narration segments,
  Piper uses a configurable `1.12` length scale, and measured audio must remain
  at or below 300 seconds. No live provider call is implementation evidence.

## RAG-026 — Protected native PDF viewer within existing ingestion bounds

- Status: Implemented for authorized lesson reading
- Date: 2026-07-19
- Affected: owner/enrollment-scoped lesson PDF action, `PdfLessonViewer`, lesson
  content UI, PDF authorization regression test and documentation
- Decision: Stream the original PDF only through the existing accessible-lesson
  queryset, load it into a browser-local blob, and embed the browser PDF viewer
  for native search, page navigation and zoom with fullscreen/new-tab controls.
- Reason: Extracted text is useful for RAG but is not an adequate reading UI for
  structured or long PDFs. Reusing native PDF controls avoids loading every page
  into the React tree or adding a second PDF rendering dependency.
- Constraint: This does not raise ingestion limits. The development pipeline
  remains capped at 20 MB, 100 pages and 250,000 extracted characters until PDF
  parser wall-clock isolation, malware scanning and measured larger fixtures
  justify a separate change.
