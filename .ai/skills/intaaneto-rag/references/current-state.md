# Current state

Last repository inspection: 2026-07-13.

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
- Lesson chat now sends a server-authorized `lesson_id` and returns a stable
  `answer`, `citations`, and `grounded` contract. It still uses lesson summary or
  content as temporary context; retrieval and citations are not implemented.
- The test suite uses isolated SQLite settings and includes authorization/chat
  regression coverage. Twenty-six backend tests passed on 2026-07-13 in the
  rebuilt Docker backend, including nine Slice 1 tests for deterministic
  normalization/chunking, unchanged and changed indexing, provider/DB failure
  rollback, a concurrent lesson-edit guard, owner denial, and admin access. A
  rollback-only PostgreSQL smoke test also persisted and read pgvector chunks
  successfully.
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
- Frontend lint and both container/host production builds passed after the
  optional-Firebase fix on 2026-07-13. The build still warns about a JavaScript
  chunk above 500 kB and stale Browserslist data.

## Not implemented as of the inspection

- No retrieval/reranking pipeline, citation persistence, RAG evaluation set, or
  lesson-chat integration with indexed chunks.
- No ANN vector index is created yet. The pgvector column intentionally accepts
  configurable dimensions until embedding quality is evaluated; Slice 2 must
  query only vectors matching the active source's model/revision/dimension.
- The local model cache is not baked into the backend image. First use downloads
  about 0.22 GB and therefore still needs deployment cache/network planning.
- No Redis/Celery services in `docker-compose.yml`.
- Lesson chat has a server-owned scope but still injects bounded lesson summary
  or content directly instead of retrieving indexed chunks.

## Known integration risks

- Live generation-provider behavior still requires a valid key and an
  integration test; automated generation tests use a mock and make no API calls.
- `get_hint` fetches an exercise without an explicit enrollment/access check.
- Uploaded lesson files allow broad types at the model level; size exists in
  global settings but type, parsing, and content safety need explicit handling.
- RAG endpoints currently return `grounded: false` and an empty citation list by
  design until indexed retrieval is implemented.
- `npm ci` reports 18 known frontend dependency vulnerabilities (including one
  critical). No automatic `npm audit fix` has been applied because upgrades need
  review and regression testing.

## Session handoff — start here

- Product priority remains RAG. Slice 0 and Slice 1 are complete; Slice 2
  (retrieve authorized lesson evidence without invoking an LLM) is next.
- Keep Slice 2 narrow: database-filter to one server-authorized lesson and its
  complete active source before cosine ranking, return stable chunk metadata,
  and add enrolled/non-enrolled/cross-course leakage tests plus a small
  Vietnamese relevance fixture set.
- Evaluate the current 384-dimensional multilingual model before adding an ANN
  index or treating its retrieval quality as accepted. Exact pgvector search is
  sufficient for the first small corpus baseline.
- Do not add R2, Google Drive, Celery, Redis, avatar, voice, or video work to this
  slice. Original lesson fields are sufficient for the first indexing path.
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
