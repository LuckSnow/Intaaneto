# Current security risks

Last repository audit: 2026-07-16. These are observed risks, not proof of
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
- PDF extraction and local embedding run synchronously in the upload request;
  this removes the daemon-thread loss mode but still lacks parser wall-clock
  isolation and a durable background job boundary for production workloads.

## Operational gaps

- No rate limiting or request throttling is configured.
- Mailjet delivery still requires a verified sender and a deliberate local smoke
  test. Automated tests use Django's in-memory email backend and do not prove
  external deliverability.
- Security regression coverage now includes initial role, lesson ownership,
  enrollment, hidden-answer, chat-scope, indexing-owner, lesson-scoped vector
  retrieval boundaries, and initial PDF spoofing/type/size/owner failure paths.
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

## Resolved with regression tests through 2026-07-15

- User API no longer exposes global CRUD; role and active status are read-only,
  registration always creates a learner, and direct self-upgrade has been
  removed. Verified learners submit a pending teacher application; only an
  active verified admin can approve it and trigger the transactional role change.
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
- Collaborative demo data is recreated without copying development users, chats,
  uploads, or vectors. Demo accounts have unusable passwords unless each machine
  supplies ignored environment values. The legacy fixed seed password and its
  stale setup-documentation entry have been removed.
- Lesson upload now accepts PDF only, validates its signature and bounded parser
  inputs, rejects the removed document formats, authorizes ownership before
  extraction/embedding, and never activates partial chunks after an indexing
  failure. The old daemon-thread upload endpoint path is no longer used.
- JWT refresh rotation and logout blacklisting are enabled through SimpleJWT's
  blacklist app and covered by API tests. The frontend stores a rotated refresh
  token, validates the current user during app startup, and does not attempt a
  refresh when login or registration itself returns 401.
- Teacher-portal login checks the server-owned role and verified/active state
  before issuing JWTs; learner credentials receive no tokens. Verification links
  now have a persisted configurable expiry, SHA-256-at-rest token digest, and
  single-use behavior. Resend uses the same successful response for missing,
  verified, and unverified accounts, while sending only for an existing
  unverified account.
- Teacher applications enforce one pending request per learner, ignore
  client-controlled status/reviewer fields, record reviewer/time/note, and keep
  the learner role unchanged until admin approval. Negative tests cover direct
  self-elevation attempts, duplicate pending requests, teacher reapplication,
  learner review attempts, and rejection-note validation.

## Status discipline

Remove or downgrade an item only after adding a regression test and verifying
the intended enforcement point. Formatting cleanup alone does not change risk.
