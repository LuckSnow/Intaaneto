# Current security risks

Last repository audit: 2026-07-13. These are observed risks, not proof of
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
- Registration prints request data and validation errors, risking sensitive data
  in application logs.
- Upload processing runs in daemon threads, is not durable, and performs long
  external calls without a persistent job boundary.

## Operational gaps

- No rate limiting or request throttling is configured.
- No security regression tests cover roles, ownership, enrollment, hidden
  answers, uploads, chat scope, or cross-course retrieval.
- Docker Compose uses development mode and hard-coded database credentials.
- Fresh Compose startup does not run migrations because its command overrides
  the Dockerfile command.
- Dependency installation currently needs an undeclared compatible setuptools
  version for `drf-yasg`; frontend install reports known vulnerabilities.
- RAG, pgvector, R2, Celery, and Redis are planned but not implemented.

## Resolved with regression tests on 2026-07-13

- User API no longer exposes global CRUD; role and active status are read-only,
  registration always creates a learner, and self-upgrade is admin-gated.
- Anonymous course mutation is denied; lesson access is filtered by enrollment,
  preview state, teacher ownership, or admin role.
- Student exercise responses omit `solution_code` and hidden `test_cases`, and
  the student-facing exercise endpoint is read-only.
- Lesson chat uses a backend-authorized lesson scope, bounded history, a stable
  response contract, and explicit provider failure responses. Unauthorized
  lesson scope is rejected before the provider is called.

## Status discipline

Remove or downgrade an item only after adding a regression test and verifying
the intended enforcement point. Formatting cleanup alone does not change risk.
