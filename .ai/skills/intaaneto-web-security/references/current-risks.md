# Current security risks

Last repository audit: 2026-07-15. These are observed risks, not proof of
exploitation. Re-check code and tests before changing status.

## P0 — Resolve before exposing the application

- Exercises are not linked to a course or lesson, so exercise/hint authorization
  cannot yet be constrained by enrollment or teacher ownership.
- Course/lesson permissions now have an initial owner/enrollment boundary, but
  broader negative coverage is still required before production exposure.

## P1 — Resolve during the first stabilization/RAG slices

- `get_hint` loads exercises without explicit course/enrollment authorization.
- Forum object-owner permission logic exists but is not applied; authenticated
  users may be able to update/delete content owned by others.
- Logout attempts token blacklisting, but the Simple JWT blacklist app is not
  installed, so logout behavior requires verification.
- Upload processing runs in daemon threads, is not durable, and performs long
  external calls without a persistent job boundary.

## Operational gaps

- No rate limiting or request throttling is configured.
- Security regression coverage now includes initial role, lesson ownership,
  enrollment, hidden-answer, chat-scope, indexing-owner, and lesson-scoped vector
  retrieval boundaries. Upload abuse still lacks coverage.
- Docker Compose uses development mode and hard-coded database credentials.
- Compose is a development configuration with bind mounts and Django/Vite
  development servers; it is not a production deployment definition.
- Frontend dependency installation has reported known vulnerabilities and needs
  a reviewed dependency audit before production exposure.
- Lesson indexing, filtered retrieval, and grounded lesson answers are
  implemented. R2, durable background jobs, Celery, and Redis are not implemented.
- Free-tier Gemini generation may permit provider product-improvement use of
  submitted prompts/responses; do not send sensitive, confidential, or personal
  lesson/student data until an appropriate provider/data-processing tier is used.

## Resolved with regression tests through 2026-07-14

- User API no longer exposes global CRUD; role and active status are read-only,
  registration always creates a learner, and self-upgrade is admin-gated.
- Anonymous course mutation is denied; lesson access is filtered by enrollment,
  preview state, teacher ownership, or admin role.
- Student exercise responses omit `solution_code` and hidden `test_cases`, and
  the student-facing exercise endpoint is read-only.
- Lesson chat uses a backend-authorized lesson scope, bounded history, a stable
  response contract, and explicit provider failure responses. Unauthorized
  lesson scope is rejected before the provider is called.
- Lesson retrieval rejects non-enrolled learners and other teachers before query
  embedding, searches only the authorized complete active source, excludes
  archived and cross-course chunks, and bounds query length/top-k.
- Grounded lesson chat skips generation for weak or missing evidence, separates
  system policy from untrusted evidence, constructs citations only from selected
  retrieved chunks, redacts provider/retrieval failures, and persists no full
  prompt, embedding, provider error, or citation excerpt.
- OpenAI/Gemini generation selection and credentials remain server-side. Missing
  keys and unknown provider values fail closed, with provider error details kept
  out of the student response.
- Registration no longer logs the submitted payload or validation errors.
- Fresh Compose startup applies committed migrations, waits for database health,
  and gates frontend startup on backend health.

## Status discipline

Remove or downgrade an item only after adding a regression test and verifying
the intended enforcement point. Formatting cleanup alone does not change risk.
