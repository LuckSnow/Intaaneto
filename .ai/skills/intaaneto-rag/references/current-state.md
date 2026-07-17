# Current state

Last repository inspection: 2026-07-17.

This is a living factual snapshot, not a roadmap. Verify it against code before
relying on it and update it after material implementation changes.

## Implemented

- Django 5 and Django REST Framework backend with PostgreSQL configuration.
- React/Vite frontend and an authenticated lesson page with an AI chat tab.
- `courses.Lesson` stores content, uploaded file, extracted text, AI summary,
  processing status, and generated-video fields.
- `ai_assistant.ChatSession` and `ChatMessage` persist conversation history and
  latency/token metadata.
- `/api/ai/chat/` exposes session CRUD plus `send_message`, `explain_code`, and
  `get_hint` actions.
- `AIService` builds a Vietnamese tutoring system prompt and can add caller-
  supplied lesson, exercise, or code context.
- PDF-only lesson ingestion is implemented through durable database jobs and a
  Celery worker backed by Redis/AOF in development Compose. Upload/reprocess
  authorize and validate bounded file metadata/signature before returning `202`;
  the worker rechecks current ownership, then allowlists `.pdf`, checks MIME and
  `%PDF-` signature, bounds bytes/pages/extracted characters, rejects encrypted,
  malformed, and text-empty files, preserves page markers in extracted text,
  normalizes Unicode and removes database-unsafe NUL/control characters, and
  escapes untrusted text lines that could impersonate an app-owned page marker,
  then invokes the existing idempotent lesson indexer. DOCX/PPT/PPTX are outside
  the product target and `python-pptx` is no longer a runtime dependency.
- Migration `ai_assistant.0005` stores nullable, constrained `page_start` and
  `page_end` on each PDF-derived chunk. Indexing derives ranges deterministically
  from normalized page markers, retains original page numbers when empty pages
  were skipped, and supports chunks spanning pages. The migration backfilled all
  40 existing development PDF chunks with valid ranges on 2026-07-17.
- PDF ingestion authorizes the owning teacher or admin both before enqueue and
  before extraction/embedding in the worker. `LessonIngestionJob` enforces one
  queued/running job per lesson, records bounded attempts/status/failure/source
  metadata, and omits raw text, exception details and broker task IDs from the
  polling API. Tasks use late acknowledgement, one-at-a-time prefetch, a lease,
  bounded exponential retry for transient indexing failures, and idempotent
  source activation. Broker failure and terminal processing failure persist safe
  failed states instead of leaving false pending work. The worker runs as UID/GID
  10001 and shares media/model-cache volumes; this path does not invoke Groq,
  D-ID or R2.
- Completed PDF lessons expose bounded learner-safe `learning_content` (manual
  content first, otherwise extracted PDF text), a truncation flag, `rag_ready`,
  and the existing PDF URL on `LessonPage`; raw embeddings and internal source
  diagnostics are not serialized.
- The teacher upload page has a reviewed downstream-authoring panel for an owned
  ready lesson. It can generate an editable AI summary draft and only copy it to
  `Lesson.ai_summary` after explicit approval. It can also generate exactly five
  multiple-choice questions as an unpublished assessment draft; answer review
  and publishing remain manual. Both paths require an active/ready source,
  recheck mutable state, are owner/admin scoped and use OpenAI or Gemini.
- An approved current summary can be converted to a bounded PCM WAV with local
  Vietnamese `espeak-ng`; no TTS API key is used. Checksums bind narration and
  later video work to the reviewed text.
- An owner-scoped endpoint enqueues SadTalker only after current summary approval,
  matching narration, validated portrait and explicit rights confirmation. A
  dedicated one-at-a-time `video` Celery worker mounts the runtime read-only;
  the normal worker consumes only the PDF/default queue. Video remains optional
  and cannot block lesson, RAG or assessment readiness.
- AI generation now uses a provider adapter with the supported OpenAI client,
  configurable model/timeout, bounded history, and explicit provider failures.
- AI Tutor generation can now select `openai` or `gemini` through
  `AI_GENERATION_PROVIDER`. Gemini uses its OpenAI-compatible endpoint behind a
  dedicated adapter, key, base URL, and model setting; missing keys and unknown
  providers fail closed without exposing credentials. Local embeddings and the
  lesson retrieval/citation path are unchanged.
- Slice 1 lesson indexing is implemented synchronously in
  `ai_assistant.rag_services`. It authorizes the teacher-owner or admin before
  reading lesson text, prefers non-empty `Lesson.extracted_text` over
  `Lesson.content`, normalizes it deterministically, chunks with stable offsets,
  embeds all chunks, and atomically activates a complete source version.
- `KnowledgeSource` and `KnowledgeChunk` persist lesson/version/checksum,
  chunker and embedding configuration, deterministic chunk locations, and
  pgvector embeddings. Database constraints allow only one active source per
  lesson and one chunk per source ordinal.
- Migration `ai_assistant.0003` conditionally enables the PostgreSQL `vector`
  extension and remains compatible with the SQLite test settings. Development
  Compose now uses the pinned `pgvector/pgvector:0.8.2-pg15-bookworm` image;
  the applied extension and vector column were verified on 2026-07-13.
- Local embeddings use a provider protocol and a lazy FastEmbed ONNX adapter.
  The initial configurable model is
  `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, revision label
  `fastembed-0.8.0-mean-pooling`, dimension 384. A live two-text embedding smoke
  test produced two 384-dimensional vectors; model quality is not yet evaluated.
- `python manage.py index_lesson <lesson_id> --actor-id <user_id>` is the first
  trusted entry point. It has no HTTP/upload/background-job surface.
- `python manage.py seed_demo_data` creates a deterministic, idempotent local
  teacher/student/enrollment/course, text-only RAG lesson, and reviewed five-
  question published assessment for collaborators. The assessment is updated
  only before attempts exist and is never overwritten after learner evidence.
  It excludes uploads, chat history, vectors, and fixed credentials; optional
  local login passwords come only from ignored environment values. Indexing is
  deliberately a separate command so setup does not unexpectedly download or
  run the embedding model.
- Slice 2 lesson retrieval is implemented in `ai_assistant.rag_services` without
  invoking an LLM. It resolves the actor's readable lesson scope before query
  embedding, selects only the compatible complete active source, and returns
  stable ranked chunk/source/version/location metadata with `ready`,
  `weak_evidence`, or `not_indexed` status.
- PostgreSQL retrieval uses exact pgvector cosine distance inside one authorized
  active source. The isolated SQLite test settings use an in-memory cosine
  fallback only after the database has constrained chunks to that source. No ANN
  index or global-then-filter search is used.
- Retrieval is bounded by configurable question length, top-k, provider identity,
  vector dimension, and a provisional minimum cosine similarity of `0.45`.
  A small checked-in Vietnamese fixture covers RAG, Python, and an unsupported
  weather question. The threshold remains subject to broader evaluation.
- Slice 5 now has an initial versioned Vietnamese retrieval-evaluation dataset
  tied to the deterministic demo RAG lesson. It contains six answerable cases,
  two unsupported cases, expected source-text markers, and a prompt-injection
  case embedded in the non-sensitive demo material. The
  `evaluate_rag_retrieval` management command reuses authorized lesson retrieval
  without calling a generation provider and emits dataset/config versions,
  status accuracy, expected-source recall, pass rate, latency, and bounded
  per-case metadata without questions, raw chunks, embeddings, or provider
  diagnostics.
- Lesson chat now sends a server-authorized `lesson_id` and returns a stable
  `answer`, `citations`, `grounded`, and retrieval-status contract. Slice 3 now
  calls authorized lesson retrieval, skips OpenAI for weak/missing evidence,
  sends only bounded sufficient chunks to a strict grounded prompt, and builds
  citation IDs/locations/excerpts from the retrieved records in application code.
- Assistant messages persist bounded retrieval metadata (status, source/version,
  selected chunk IDs/scores, and latency) through migration
  `ai_assistant.0004`. They do not persist embeddings, full prompts, provider
  errors, or citation excerpts.
- The lesson chat UI restores the latest bounded server-owned session for the
  authorized lesson after reload and displays grounded/fallback status plus
  expandable source excerpts. Persisted chunk references are rehydrated only
  from database chunks belonging to that lesson and matching the recorded
  source/version; revoked enrollment hides both history and session detail.
  React text rendering is used for excerpts; no raw HTML is injected.
- The first live run of the versioned eight-case Vietnamese retrieval dataset
  completed against PostgreSQL exact cosine and active demo source v1 on
  2026-07-16. Pass/status accuracy was `0.75`, expected-source recall was `1.00`,
  and mean latency including cold model initialization was `225.12 ms`. The
  authorization and prompt-injection questions were present in top-k but fell
  below the provisional `0.45` threshold (`0.275` and `0.442`); both unsupported
  cases correctly returned weak evidence. The measured result is recorded in
  `docs/RAG_RETRIEVAL_BASELINE_V1.md`; no threshold/model setting was changed.
- The test suite uses isolated SQLite settings and includes authorization/chat
  regression coverage. Two hundred and twenty-five backend tests passed on 2026-07-17 in the
  Docker backend, including eleven Slice 1/index-location tests for deterministic
  normalization/chunking, unchanged and changed indexing, provider/DB failure
  rollback, a concurrent lesson-edit guard, owner denial, and admin access. A
  further eleven Slice 2 cases cover Vietnamese relevance, weak evidence,
  compatible active-source selection, enrolled/owner/admin access, outsider and
  other-teacher denial before embedding, cross-course isolation, bounds, and
  provider failures.
- Seven original Slice 3 cases cover grounded API contracts, weak/not-indexed fallback
  without generation, prompt-injection placement, application-owned citations,
  retrieval/provider failure redaction, persisted metadata, and immutable chat
  session lesson scope.
- Four chat-history cases cover the explicit empty contract, latest-session
  restoration, database-owned citation hydration with cross-lesson tampering
  rejection, and enrollment-revocation denial for history/session detail.
- Six generation-provider cases cover OpenAI/Gemini selection, Gemini's
  OpenAI-compatible request contract, missing server-side keys, and an unknown
  provider failing closed.
- Five demo-seed cases cover idempotency, the attempt-preserving assessment,
  exclusion of private/RAG-derived state, environment-only passwords, collision
  safety, and removal of the legacy fixed seed password.
- Fifteen PDF-ingestion cases cover real PDF extraction with page markers, empty,
  encrypted, oversized, spoofed and non-PDF rejection, owner authorization before processing,
  NUL/control-character sanitization, upload-to-active-index, embedding failure
  without partial activation, and idempotent reprocessing.
- Eight durable-ingestion cases cover active-job deduplication, broker outage,
  bounded transient retry, non-retryable invalid input, authorization revocation
  before worker execution, deleted-job delivery, bounded polling metadata, and
  owner-scoped status restoration after a frontend reload.
  A live Redis broker smoke on 2026-07-17 delivered an idempotent completed job
  to the non-root Celery worker in about 18 ms; the temporary row was removed.
- Lesson completion now returns the next authorized, published, usable lesson,
  updates enrollment progress and resume position, and skips PDF lessons without
  readable content or an active ready RAG source. The lesson page shows a
  server-confirmed next-lesson action, while enrolled learners can also open
  lessons directly from the course outline. Three API tests cover a ready PDF
  after an unusable upload, final-lesson completion, and preview isolation so an
  unenrolled viewer cannot discover the next enrolled-only lesson.
- A first deterministic lesson-assessment vertical slice is implemented in the
  exercises app. One versioned assessment can be attached to a lesson with a
  configurable pass threshold and teacher-authored multiple-choice questions
  mapped to learning objectives. Enrolled learners receive no correct-answer or
  explanation fields; the backend validates a complete answer set, calculates
  score/pass state, stores immutable attempt and answer snapshots, aggregates
  best current-version scores into `Enrollment.mastery_percentage`, and
  completes/advances the lesson only after a passing result. Failed attempts
  return weak objectives for reinforcement. Assessment, score, pass, mastery,
  completion, and next-lesson decisions remain server-owned. Assessments with
  attempts cannot be edited or deleted in this initial slice.
- The lesson page now renders the learner-safe multiple-choice assessment and
  server-confirmed pass/reinforcement/next-lesson states. Lessons without a
  published assessment retain the explicit completion action.
- A recommendation-only dialogue knowledge check is available after a learner
  passes the current deterministic assessment. The backend resolves one
  assessment-owned question/rubric, retrieves evidence inside the authorized
  lesson, and strictly parses a Vietnamese provider recommendation. Weak evidence
  returns `unavailable` without generation. Application-owned citations accompany
  feedback; the action never changes score, mastery, completion, or progression.
  Its audit event stores the passed attempt/version, objective, HMAC answer digest,
  chunk IDs and bounded provider metadata—not raw answer, prompt, rubric, feedback,
  citation excerpt or answer key. Eleven focused service/API/provider/throttle
  cases cover access scope, fallback, redaction, malformed output and immutable
  learning state.
- Teachers/admins now have a role-gated `/teacher/assessments` authoring page.
  It loads draft and published managed courses through a dedicated paginated
  endpoint, filters lessons without expanding the backend ownership scope, and
  creates/updates/deletes draftable assessments with choices, correct answers,
  explanations, learning objectives, threshold, and publish state. Objectives
  are mandatory and authoring/submission are bounded to 50 questions. Five
  backend tests cover managed-course isolation, lesson-filter non-expansion,
  role denial, required objectives, and the bound; frontend lint/build pass.
- Teachers now have a role-gated `/teacher/courses` page for owned course CRUD.
  New courses must start as drafts and can publish only after at least one
  published lesson has text content or an active ready RAG source. Teacher
  payloads cannot set featured status; duplicate generated slugs fail with a
  validation response; other teachers cannot mutate the course; and deletion
  is rejected once lessons or enrollments exist to prevent cascade data loss.
  Six API tests cover these invariants. Teacher upload now consumes the managed
  course list, and the dashboard navigation remains reachable through a
  horizontally scrollable second row on small screens.
- A cross-app integration test now proves the main deterministic journey without
  network/provider calls: a teacher creates a draft course, uploads and indexes
  a real PDF fixture, authors/publishes an assessment, publishes the now-usable
  course, then an enrolled learner receives no answer key, passes the assessment,
  and reaches authoritative 100% progress/mastery with lesson completion.
- Failed current-version assessment attempts now expose an explicit,
  learner-triggered RAG reinforcement action. The backend resolves the attempt
  as owned by the authenticated learner, uses only its server-recorded weak
  objectives, bounds objective count and top-k, retrieves inside the assessment
  lesson, and constructs citation excerpts from authorized chunks without
  invoking a generation provider or changing score/progress/mastery. Passed,
  stale, foreign, and non-enrolled attempts are rejected; missing/weak indexes
  return explicit fallback states. The lesson UI shows the review evidence and
  lets the learner prefill—not auto-send—a grounded Tutor question.
- Successful reinforcement packet requests now create a minimal audit event with
  safe status and objective/evidence counts, but no prompt, excerpt, or repeated
  learner identity. Retrieval failures do not create successful evidence. An
  owned-course E3 report pairs the first usable event for a failed attempt with
  the first later attempt for the same learner/assessment/version and reports
  aggregate score change/pass conversion/pending follow-up only. It is explicitly
  observational; no real learner-usage baseline has been recorded yet.
- A read-only role-aware progress report now derives learner and teacher
  dashboards from authoritative `Enrollment`, `LessonProgress`, and
  current-version `AssessmentAttempt` records instead of the legacy mutable
  analytics counters. Learners receive only their course progress/mastery,
  completion, assessment counts, and resume lesson. Teachers receive paged
  aggregates for owned courses and may request a bounded learner roster for one
  owned course; email, answer keys, chat, and old-version attempt results are
  omitted. Teacher/admin may export one explicitly scoped course as CSV, capped
  at 5,000 learners with spreadsheet-formula escaping and no contact/chat/answer
  data. An owned-course objective report aggregates normalized objective
  snapshots from each learner's latest attempt for the current assessment
  version, returning only learner/answer counts and correctness rates. Old
  attempts, identities, selections, and answer keys are omitted. Admin uses the
  same explicit administrative scope. The React dashboard renders these states
  and no longer displays hard-coded zeroes.
- A reviewed Markdown learning-corpus importer now compiles
  `docs/computer-networks.md` and `docs/web-programming.md` into two stable,
  structured courses with fifteen text lessons, explicit learning objectives,
  revisions, and primary references. It validates source headings and size,
  defaults to drafts, requires an active verified teacher for database writes,
  preserves publication state on later runs, and atomically rejects ownership,
  PDF, or manually authored lesson collisions. Import does not create vectors,
  assessments, chats, or answer keys; indexing remains a separate explicit
  teacher operation. Docker mounts the authoring documents read-only, and a
  database-free dry run validates the real corpus.
- A separate `import_corpus_assessments` command now validates and imports three
  curated draft assessments with 27 multiple-choice questions for representative
  network-model, network-security, and web-security lessons. Each of the nine
  declared objectives has three questions. Answer keys remain in the exercises
  authoring module and are never appended to RAG lesson content. The command
  requires the active verified teacher-owner, accepts only importer-managed text
  lessons, defaults to draft, requires explicit `--publish-reviewed`, is atomic
  and idempotent, and refuses to overwrite different/manual assessment state or
  learner attempts. Eight focused tests cover blueprint/corpus alignment,
  database-free dry run, draft creation, explicit publication, role/ownership,
  rollback, idempotency, and attempt preservation. A real dry run validates all
  3 assessments/27 questions; teacher content review is still required before
  publication.
- The development PostgreSQL database was populated through both importers on
  2026-07-17 under the verified demo teacher: 2 draft courses, 15 draft lessons,
  3 draft assessments, 27 questions, zero published corpus records, and zero
  corpus knowledge sources. A second assessment import created no duplicates.
- Legacy coding exercises now have an optional lesson relationship for migration
  compatibility, while learner list/detail/submission and AI `get_hint` queries
  share the same published, lesson-scoped owner/enrollment boundary. Hint prompts
  contain title/description and optional learner code, never solution code or
  hidden tests; outsiders are denied before the generation provider.
- Course migrations `0004`/`0005` and exercises migrations `0002`–`0004` are applied in the
  development PostgreSQL database. The exercises migration conditionally reuses
  the complete `lesson_id` column/FK/index left by the removed legacy
  `exercises.0002_initial`, while still creating that relationship on a fresh
  database; both the existing PostgreSQL path and fresh isolated test path pass.
- A live retry of the previously failing uploaded PDF completed on 2026-07-16:
  33,683 sanitized characters with zero NUL characters produced one active
  source with 40 chunks. This proves the observed PostgreSQL NUL failure is fixed
  for that file; it is not a broad PDF-parser quality evaluation.
- The web auth flow now validates an existing JWT session against `/users/me/`
  during startup, preserves safe intended routes, directs teachers/admins to the
  PDF upload surface and learners to their dashboard, hides login/register from
  authenticated users, and keeps public registration learner-only. SimpleJWT
  refresh rotation/logout blacklisting is installed and covered by API tests.
- A dedicated `/teacher/login` frontend and `teacher_login` API now issue JWTs
  only to active, email-verified teacher/admin accounts; learner credentials are
  rejected without tokens. Verification tokens record issuance time, expire
  after a configurable 24-hour default, are stored as SHA-256 digests, are
  single-use, and resend responses do not disclose whether an account exists or
  is already verified. Mailjet remains server-side through Anymail; live delivery
  depends on local sender/key setup.
- Self-service teacher elevation has been replaced by an auditable application
  workflow. A verified learner can submit one pending specialization/experience/
  reason application without changing role. Active verified admins receive a
  bounded email notice and can approve or reject through an admin-only API or
  Django admin actions. Approval transactionally changes the applicant to
  teacher, copies specialization/experience to the profile, and records reviewer,
  note, and review time; rejection leaves the learner role unchanged and permits
  a later reapplication. The profile UI shows pending/rejected states instead of
  promising immediate elevation.
- Forum write boundaries now use action-specific serializers and backend object
  permissions: only post/comment authors or role-admin may update/delete, only
  role-admin may mutate tags or pin, and clients cannot write privileged status
  or owner fields through ordinary payloads. Public forum identity omits email,
  phone, birth date, verification and profile data. Reaction, report,
  reply-parent, and follow targets are validated; database constraints require
  exactly one reaction/report target and prevent duplicate reports. Ten
  negative/contract tests pass and migration `forum.0004` is applied in the
  development PostgreSQL database.
- Named course APIs are registered before the empty-prefix course detail route,
  so lesson comments, reviews, and enrollments are no longer shadowed as course
  primary keys. Lesson comments are scoped to readable lessons, cross-lesson
  parents are rejected, and comment/review mutations require record author or
  role-admin; creating a review requires enrollment. Five negative tests cover
  these boundaries.
- DRF scoped throttles now bound registration/login/email verification,
  teacher-application submission, PDF upload/reprocessing, AI chat/hints, and
  assessment submit/reinforcement. Rates are environment-configurable and five
  endpoint tests verify `429` behavior without counting teacher-application GET
  requests as submissions. The current cache is application-level; a shared
  cache and/or gateway limit is still required for multi-instance production.
- An authorized `evaluate_rag_answers` command now exercises the full grounded
  answer path over the versioned Vietnamese dataset. It requires explicit
  provider-cost confirmation, omits raw questions/answers by default, and
  reports grounded/refusal contract, application-owned citation scope, a
  labeled lexical-marker proxy, latency, and provider-reported token totals.
  Report schema 2 separates contract pass from strict lexical-proxy pass; five
  tests cover metrics, that separation, unsafe citations/marker misses, cost
  confirmation, and authorization before evaluation. A live Gemini
  `gemini-3.1-flash-lite` baseline was recorded on 2026-07-17 over the eight-case
  demo dataset: contract pass `0.75`, citation scope `1.00`, refusal `1.00`,
  strict lexical-proxy pass `0.50`, warm mean latency `1515.62 ms`, and 2,283
  provider-reported tokens across four generation calls. Raw answers were not
  committed; semantic and pedagogical claims still require human review.
- The grounded-answer harness can now export two private `0600` review sheets
  from one provider run, with distinct pseudonymous raters and an immutable
  package digest. A separate aggregate-only command validates complete ratings
  and reports agreement/kappa plus clarity summaries without raw questions,
  answers, citations, ratings, notes, or reviewer identities. Five focused tests
  cover aggregate output, tamper/same-rater/incomplete rejection, identical
  package export, file permissions, stdout redaction, and explicit sensitive-
  export confirmation. No human ratings or adjudicated E1 result exist yet.
- Rollback-only PostgreSQL smoke tests persisted and ranked pgvector chunks with
  exact cosine distance. A live FastEmbed smoke ranked the intended RAG and
  Python chunks first (`0.494` and `0.756`) and marked the unsupported weather
  question weak with negative scores; this is only an initial three-question
  baseline, not a model-quality conclusion.
- A rollback-only PostgreSQL Slice 3 smoke completed exact retrieval, grounded
  prompt construction, application-built citations, and retrieval-metadata
  persistence. No live OpenAI request was made automatically, to avoid spending
  the user's API credit without an explicit manual smoke action.
- Development Docker Compose has been repaired and verified end to end:
  PostgreSQL and backend report healthy, frontend runs through Vite, committed
  migrations are applied at backend startup, and frontend waits for backend
  health. Host ports are frontend `5173`, backend `8000`, PostgreSQL `5434`, and
  Adminer `8888`.
- Backend/frontend environment examples now distinguish required development
  values from optional OpenAI, Groq, D-ID, Firebase, Google OAuth, and Mailjet
  integrations. Real `.env` files are Git-ignored; no provider key is required
  merely to render and browse the local web application.
- Firebase initialization is optional in local frontend development. Missing
  Firebase values no longer crash React during module import. Google Auth is
  dynamically loaded only when a user starts Google login; forum data has one
  authoritative source through the authenticated Django REST API and no longer
  imports or subscribes to Firestore.
- Frontend lint and a production build passed after the lesson-progression UI
  update and dependency hardening on 2026-07-16. `npm audit` reports zero known
  vulnerabilities. The main JavaScript chunk fell from about 997 kB to 465 kB;
  the build still warns about stale Browserslist data.
- The E2 assessment-consistency protocol now defines sampling, two independent
  human raters, agreement metrics, privacy boundaries, and a recommendation-only
  boundary for any future dialogue grader. A database-verified E2 software
  harness now generates 81 balanced synthetic response rows and 12 pass-boundary
  profiles across the 3 corpus assessments, using the same pure score calculator
  as production grading. The first run reported fixture-contract and boundary
  accuracy `1.00`; it creates no attempts and omits response cases by default.
  Explicitly confirmed local review export creates `0600` files with authoring
  answer keys outside Git, while the two-rater aggregator validates complete
  pseudonymous sheets and returns agreement/kappa/clarity aggregates without raw
  ratings, identities, answers, or notes. Two blank review templates exist in
  the development private media volume. Eight focused tests cover shared score
  boundaries, balanced/safe output, sensitive template handling, aggregate-only
  agreement, incomplete/same-rater rejection, database scope, explicit export
  confirmation, and changed/non-owner denial. No human study or agreement result
  has been run yet.

## Not implemented as of the inspection

- No reranking or comprehensive multi-lesson answer-generation RAG evaluation
  yet. The first live demo baseline exists, but still needs an expanded dataset,
  holdout split and human semantic/pedagogical review. Citation objects are
  returned and shown for the current response; only safe retrieval identifiers
  and scores are persisted. Reloaded citations are rebuilt from authorized
  database chunks and PDF citations include structured page ranges.
- No ANN vector index is created yet. The pgvector column intentionally accepts
  configurable dimensions until embedding quality is evaluated; retrieval
  queries only vectors matching the active source's model/revision/dimension.
- The local model cache is not baked into the backend image. First use downloads
  about 0.22 GB and therefore still needs deployment cache/network planning.
- PDF parsing now runs outside the HTTP process, but an explicit parser wall-clock
  subprocess limit, malware scanning, production broker HA/monitoring, and
  orphan-file cleanup are not implemented yet.
- No validated teacher competency test or scoring rubric is implemented. A future
  assessment may provide evidence to the admin review, but must not automatically
  grant a privileged role without an explicitly accepted policy.
- A bounded post-pass AI dialogue recommendation is implemented, but no
  AI-generated grade affects learner state. The deterministic multiple-choice
  assessment remains the trusted score/progression baseline; teacher calibration,
  human-labeled dialogue cases, consistency evaluation and any policy for using
  AI recommendations in progression remain unimplemented.
- A local SadTalker PoC adapter is available through the trusted management
  command and the owner-scoped durable web queue. It authorizes ownership
  before reading files, requires explicit rights/approval confirmation, bounds
  and validates an approved script, PCM WAV, JPEG/PNG portrait, timeout, and MP4
  output, invokes `inference.py` without a shell, and records a read-only-admin audit
  job with input checksums and safe failure code. A successful job attaches a
  server-named MP4 to `Lesson.video_file`, which the lesson UI can play. Nine
  tests cover fake-provider success, ownership, consent, invalid input, safe
  provider failure, and command/runtime ordering. The provider preflights four
  required model files, supplies an isolated environment and absolute checkpoint
  directory, and uses a writable per-run cwd while the checkout remains mounted
  read-only. Migration `courses.0005` is applied
  in development PostgreSQL; migration `courses.0007` adds reviewed summaries,
  local narration and durable stored web-job state.
- A pinned separate SadTalker runtime produced a technical 1.48-second H.264/AAC
  MP4 on the NVIDIA T1200 GPU in 53 seconds on 2026-07-17. The test used an
  upstream demo asset only to prove execution and is not attached/published.
  A consented/licensed Vietnamese portrait/audio render, peak-resource measure,
  and qualitative review are still not proven. SadTalker needs no API key; the
  local TTS smoke is execution evidence, not a natural-voice quality claim.

## Known integration risks

- PDF type/content/page/text bounds are enforced at the upload and extraction
  seams, but parser wall-clock isolation, malware scanning, and durable job
  recovery remain deployment work.
- A live OpenAI generation diagnostic reached the configured model but returned
  `insufficient_quota`. Gemini support is implemented but still needs a real
  AI Studio key and a deliberate grounded-chat smoke; automated generation
  tests use mocks and make no billable request.
- Frontend dependency audit is clean after reviewed direct dependency upgrades
  and a non-forced `npm audit fix`; periodic audit and upgrade review are still
  required because this is a point-in-time result, not a production guarantee.

## Session handoff — start here

- Product priority remains RAG. Slices 0 through 3 are complete; Slice 4
  now has a tested PDF-only upload-to-index worker, durable DB job state,
  Redis-backed bounded retry, and structured/backfilled page locations.
- For the live smoke, configure one generation provider, use an enrolled learner
  and an indexed lesson, ask one answerable and one unsupported question, and
  confirm citations/fallback in the UI without exposing provider or retrieval
  diagnostics. Free Gemini API usage must not receive sensitive, confidential,
  or personal lesson/student data.
- Run and record the grounded-answer/refusal harness with a configured provider,
  have two independent reviewers complete the private E1 sheets, then expand the
  Vietnamese dataset and add a holdout before
  tuning the provisional `0.45` threshold, changing the 384-dimensional model,
  or adding an ANN index. Exact pgvector search is sufficient for the current
  small corpus baseline.
- The reviewed summary/assessment authoring seam, local TTS, durable SadTalker
  web queue and dedicated GPU worker are implemented. A consented Vietnamese
  render and measured voice/video-quality record remain; do not present the
  local WAV smoke or upstream demo render as pedagogical-quality evidence.
- Collaborators should run migrations and `seed_demo_data` locally rather than
  sharing development database volumes or dumps containing accounts and chats.
- The worktree contains intentional uncommitted changes from stabilization,
  Docker/docs/environment cleanup, authorization/chat work, and frontend
  Firebase fallback. Inspect and preserve them; do not reset or overwrite them.
- Baseline verification on 2026-07-17: all `235` backend tests, Django check,
  migration drift check, frontend lint/build, local Vietnamese WAV smoke and
  dedicated `video` worker startup passed. For the next slice rerun `pytest`, `python manage.py check`,
  `python manage.py makemigrations --check --dry-run`, `npm run lint`, and
  `npm run build`. Docker development startup is documented in `docs/SETUP.md`.

## Existing files to inspect first

- `backend/apps/ai_assistant/{models,serializers,services,views,urls}.py`
- `backend/apps/courses/{models,services,views,serializers}.py`
- `backend/apps/exercises/{models,views,serializers}.py`
- `backend/config/settings/base.py`
- `frontend/src/services/aiService.js`
- `frontend/src/pages/LessonPage.jsx`
- `docker-compose.yml` and `backend/requirements.txt`
