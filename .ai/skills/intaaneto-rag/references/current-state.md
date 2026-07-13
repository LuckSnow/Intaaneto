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
- Lesson chat now sends a server-authorized `lesson_id` and returns a stable
  `answer`, `citations`, and `grounded` contract. It still uses lesson summary or
  content as temporary context; retrieval and citations are not implemented.
- The test suite uses isolated SQLite settings and includes authorization/chat
  regression coverage. Seventeen backend tests passed on 2026-07-13, including
  a clean run inside the rebuilt Docker backend container.

## Not implemented as of the inspection

- No chunk/document/vector models or migrations.
- No embedding service, vector store, retrieval/reranking pipeline, citation
  schema, ingestion job, RAG evaluation set, or RAG-specific tests.
- No Redis/Celery services in `docker-compose.yml`.
- No vector extension/client is declared in backend dependencies.
- Lesson chat has a server-owned scope but still injects bounded lesson summary
  or content directly instead of retrieving indexed chunks.

## Known integration risks

- Live provider behavior still requires a valid key and an integration test;
  automated tests use a mocked provider and do not make external calls.
- `get_hint` fetches an exercise without an explicit enrollment/access check.
- Uploaded lesson files allow broad types at the model level; size exists in
  global settings but type, parsing, and content safety need explicit handling.
- RAG endpoints currently return `grounded: false` and an empty citation list by
  design until indexed retrieval is implemented.

## Existing files to inspect first

- `backend/apps/ai_assistant/{models,serializers,services,views,urls}.py`
- `backend/apps/courses/{models,services,views,serializers}.py`
- `backend/apps/exercises/{models,views,serializers}.py`
- `backend/config/settings/base.py`
- `frontend/src/services/aiService.js`
- `frontend/src/pages/LessonPage.jsx`
- `docker-compose.yml` and `backend/requirements.txt`
