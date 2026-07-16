# Current state

Last repository inspection: 2026-07-16.

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
- PDF-only lesson ingestion is implemented synchronously through the teacher
  upload and reprocess endpoints. The backend allowlists `.pdf`, checks MIME and
  `%PDF-` signature, bounds bytes/pages/extracted characters, rejects encrypted,
  malformed, and text-empty files, preserves page markers in extracted text,
  normalizes Unicode and removes database-unsafe NUL/control characters, and
  invokes the existing idempotent lesson indexer. DOCX/PPT/PPTX are outside
  the product target and `python-pptx` is no longer a runtime dependency.
- PDF ingestion authorizes the owning teacher or admin before extraction and
  embedding. A complete index is activated only after extraction and all
  embeddings succeed; failures persist a bounded safe status without activating
  partial knowledge. The request is deliberately synchronous for this first
  tested slice and does not invoke Groq, D-ID, Celery, Redis, or R2.
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
  teacher/student/enrollment/course and text-only RAG lesson for collaborators.
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
- The lesson chat UI keeps the server-owned session ID while the page is open and
  displays grounded/fallback status plus expandable source excerpts. React text
  rendering is used for excerpts; no raw HTML is injected.
- The first live run of the versioned eight-case Vietnamese retrieval dataset
  completed against PostgreSQL exact cosine and active demo source v1 on
  2026-07-16. Pass/status accuracy was `0.75`, expected-source recall was `1.00`,
  and mean latency including cold model initialization was `225.12 ms`. The
  authorization and prompt-injection questions were present in top-k but fell
  below the provisional `0.45` threshold (`0.275` and `0.442`); both unsupported
  cases correctly returned weak evidence. The measured result is recorded in
  `docs/RAG_RETRIEVAL_BASELINE_V1.md`; no threshold/model setting was changed.
- The test suite uses isolated SQLite settings and includes authorization/chat
  regression coverage. Ninety-two backend tests passed on 2026-07-16 in the
  Docker backend, including nine Slice 1 tests for deterministic
  normalization/chunking, unchanged and changed indexing, provider/DB failure
  rollback, a concurrent lesson-edit guard, owner denial, and admin access. A
  further eleven Slice 2 cases cover Vietnamese relevance, weak evidence,
  compatible active-source selection, enrolled/owner/admin access, outsider and
  other-teacher denial before embedding, cross-course isolation, bounds, and
  provider failures.
- Seven Slice 3 cases cover grounded API contracts, weak/not-indexed fallback
  without generation, prompt-injection placement, application-owned citations,
  retrieval/provider failure redaction, persisted metadata, and immutable chat
  session lesson scope.
- Six generation-provider cases cover OpenAI/Gemini selection, Gemini's
  OpenAI-compatible request contract, missing server-side keys, and an unknown
  provider failing closed.
- Four demo-seed cases cover idempotency, exclusion of private/RAG-derived state,
  environment-only passwords, collision safety, and removal of the legacy fixed
  seed password.
- Fourteen PDF-ingestion cases cover real PDF extraction with page markers, empty,
  encrypted, oversized, spoofed and non-PDF rejection, owner authorization before processing,
  NUL/control-character sanitization, upload-to-active-index, embedding failure
  without partial activation, and idempotent reprocessing.
- Lesson completion now returns the next authorized, published, usable lesson,
  updates enrollment progress and resume position, and skips PDF lessons without
  readable content or an active ready RAG source. The lesson page shows a
  server-confirmed next-lesson action, while enrolled learners can also open
  lessons directly from the course outline. Three API tests cover a ready PDF
  after an unusable upload, final-lesson completion, and preview isolation so an
  unenrolled viewer cannot discover the next enrolled-only lesson.
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
  Firebase values no longer crash React during module import; Google login and
  Firestore realtime helpers remain inactive until configured, while the normal
  REST-backed application can render.
- Frontend lint and a production build passed after the lesson-progression UI
  update on 2026-07-16. The build still warns about a JavaScript
  chunk above 500 kB and stale Browserslist data.

## Not implemented as of the inspection

- No reranking or comprehensive answer-generation RAG evaluation yet. The
  initial versioned dataset measures lesson retrieval only; groundedness,
  answer correctness, refusal quality, generation latency, and cost still need
  a repeatable evaluation harness. Citation objects are returned and shown for
  the current response, while only safe retrieval identifiers and scores are
  persisted; restoring citation excerpts after a page reload is not implemented.
- No ANN vector index is created yet. The pgvector column intentionally accepts
  configurable dimensions until embedding quality is evaluated; retrieval
  queries only vectors matching the active source's model/revision/dimension.
- The local model cache is not baked into the backend image. First use downloads
  about 0.22 GB and therefore still needs deployment cache/network planning.
- No Redis/Celery services in `docker-compose.yml`.
- PDF upload currently performs extraction and local embedding inside the HTTP
  request. Durable background execution, parser wall-clock isolation, structured
  per-chunk page fields, and orphan-file cleanup are not implemented yet.
- Chat history restoration in the lesson UI is not implemented; the current page
  keeps one server-owned session until navigation or reload.
- No validated teacher competency test or scoring rubric is implemented. A future
  assessment may provide evidence to the admin review, but must not automatically
  grant a privileged role without an explicitly accepted policy.

## Known integration risks

- `get_hint` fetches an exercise without an explicit enrollment/access check.
- PDF type/content/page/text bounds are enforced at the upload and extraction
  seams, but parser wall-clock isolation, malware scanning, and durable job
  recovery remain deployment work.
- A live OpenAI generation diagnostic reached the configured model but returned
  `insufficient_quota`. Gemini support is implemented but still needs a real
  AI Studio key and a deliberate grounded-chat smoke; automated generation
  tests use mocks and make no billable request.
- `npm ci` reports 18 known frontend dependency vulnerabilities (including one
  critical). No automatic `npm audit fix` has been applied because upgrades need
  review and regression testing.

## Session handoff — start here

- Product priority remains RAG. Slices 0 through 3 are complete; Slice 4
  now has a tested synchronous PDF-only upload-to-index path. Durable background
  jobs and structured page-location persistence remain intentionally deferred.
- For the live smoke, configure one generation provider, use an enrolled learner
  and an indexed lesson, ask one answerable and one unsupported question, and
  confirm citations/fallback in the UI without exposing provider or retrieval
  diagnostics. Free Gemini API usage must not receive sensitive, confidential,
  or personal lesson/student data.
- Expand the recorded Vietnamese retrieval baseline and add grounded-answer/
  refusal evaluation before tuning the provisional `0.45` threshold, changing
  the 384-dimensional model, or adding an ANN index. Exact pgvector search is
  sufficient for the current small corpus baseline.
- Do not add R2, Google Drive, Celery, Redis, avatar, voice, or video work to this
  slice. Original lesson fields are sufficient for the first indexing path.
- Collaborators should run migrations and `seed_demo_data` locally rather than
  sharing development database volumes or dumps containing accounts and chats.
- The worktree contains intentional uncommitted changes from stabilization,
  Docker/docs/environment cleanup, authorization/chat work, and frontend
  Firebase fallback. Inspect and preserve them; do not reset or overwrite them.
- Baseline verification for the next slice: `pytest`, `python manage.py check`,
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
