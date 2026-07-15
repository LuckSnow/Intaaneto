# Current state

Last repository inspection: 2026-07-15.

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
- PDF/PPT processing libraries are declared (`PyPDF2`, `python-pptx`).
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
- The test suite uses isolated SQLite settings and includes authorization/chat
  regression coverage. Fifty-four backend tests passed on 2026-07-15 in the
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
- Frontend lint and the container production build passed after the Slice 3 UI
  update on 2026-07-14. The build still warns about a JavaScript
  chunk above 500 kB and stale Browserslist data.

## Not implemented as of the inspection

- No reranking or comprehensive RAG evaluation set. Citation objects are returned
  and shown for the current response, while only safe retrieval identifiers and
  scores are persisted; restoring citation excerpts after a page reload is not
  implemented.
- No ANN vector index is created yet. The pgvector column intentionally accepts
  configurable dimensions until embedding quality is evaluated; retrieval
  queries only vectors matching the active source's model/revision/dimension.
- The local model cache is not baked into the backend image. First use downloads
  about 0.22 GB and therefore still needs deployment cache/network planning.
- No Redis/Celery services in `docker-compose.yml`.
- Chat history restoration in the lesson UI is not implemented; the current page
  keeps one server-owned session until navigation or reload.

## Known integration risks

- `get_hint` fetches an exercise without an explicit enrollment/access check.
- Uploaded lesson files allow broad types at the model level; size exists in
  global settings but type, parsing, and content safety need explicit handling.
- A live OpenAI generation diagnostic reached the configured model but returned
  `insufficient_quota`. Gemini support is implemented but still needs a real
  AI Studio key and a deliberate grounded-chat smoke; automated generation
  tests use mocks and make no billable request.
- `npm ci` reports 18 known frontend dependency vulnerabilities (including one
  critical). No automatic `npm audit fix` has been applied because upgrades need
  review and regression testing.

## Session handoff — start here

- Product priority remains RAG. Slices 0 through 3 are complete; Slice 4
  (safe upload ingestion) is next after a deliberate live grounded-chat smoke.
- For the live smoke, configure one generation provider, use an enrolled learner
  and an indexed lesson, ask one answerable and one unsupported question, and
  confirm citations/fallback in the UI without exposing provider or retrieval
  diagnostics. Free Gemini API usage must not receive sensitive, confidential,
  or personal lesson/student data.
- Expand the Vietnamese evaluation set before tuning the provisional `0.45`
  threshold, changing the 384-dimensional model, or adding an ANN index. Exact
  pgvector search is sufficient for the current small corpus baseline.
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
