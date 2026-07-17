# Current security risks

Last repository audit: 2026-07-17. These are observed risks, not proof of
exploitation. Re-check code and tests before changing status.

## P0 — Resolve before exposing the application

- Course/lesson permissions now have an initial owner/enrollment boundary, but
  broader negative coverage is still required before production exposure.

## P1 — Resolve during the first stabilization/RAG slices

- PDF extraction now runs in a bounded-retry Celery worker rather than the HTTP
  request, but the parser still lacks subprocess wall-clock isolation and
  malware scanning. Redis/AOF and one development worker are not production
  broker HA, monitoring, or disaster recovery.

## Operational gaps

- Scoped DRF throttles cover auth/email, teacher applications, PDF processing,
  AI chat/hints, and assessment submit/reinforcement. The current development
  cache is process-local, so multi-instance production still requires a shared
  cache and/or gateway-level enforcement; DRF throttling is not a DDoS control.
- Mailjet delivery still requires a verified sender and a deliberate local smoke
  test. Automated tests use Django's in-memory email backend and do not prove
  external deliverability.
- Security regression coverage now includes initial role, lesson ownership,
  enrollment, hidden-answer, chat-scope, indexing-owner, lesson-scoped vector
  retrieval boundaries, and initial PDF spoofing/type/size/owner failure paths.
- Docker Compose uses development mode and hard-coded database credentials.
- Compose is a development configuration with bind mounts and Django/Vite
  development servers; it is not a production deployment definition.
- The reviewed frontend dependency audit reported zero known vulnerabilities on
  2026-07-17; this point-in-time result still needs periodic review.
- Lesson indexing, filtered retrieval, grounded answers, and durable database
  jobs backed by Celery/Redis are implemented for development. R2/object storage,
  production broker HA/monitoring, orphan cleanup, and parser isolation are not.
- Free-tier Gemini generation may permit provider product-improvement use of
  submitted prompts/responses; do not send sensitive, confidential, or personal
  lesson/student data until an appropriate provider/data-processing tier is used.

## Resolved with regression tests through 2026-07-17

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
- Grounded-answer human review requires separate cost and sensitive-export
  confirmations, writes two same-package local files with mode `0600`, detects
  content tampering/incomplete or same-rater sheets, and emits aggregate-only
  agreement without raw answers, citations, notes, ratings, or identities.
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
- PDF upload/reprocess persists one active database job per lesson and returns
  `202`; the non-root worker reauthorizes ownership, retries only bounded
  transient failures, records safe terminal state, and does not expose broker
  task identifiers. Broker outage, duplicate delivery, deleted jobs, revoked
  authorization, and owner-scoped status restoration have regression coverage.
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
- Lesson assessments are scoped through their lesson/course, expose no answer
  key to learners, calculate score/mastery/progression on the backend, and have
  negative coverage for non-enrollment, other-teacher ownership, forged result
  fields, cross-assessment questions, and mutation after attempts. Legacy coding
  exercises now have an optional lesson link for migration compatibility;
  learner exercise queries and submissions deny unscoped or unenrolled records.
- Dialogue checks require current enrollment plus a passed current-version
  attempt, reject foreign questions before retrieval, search only the assessment
  lesson, skip generation on weak evidence, validate provider JSON and cannot
  mutate learning state. Audit omits raw answers, prompts, rubrics, feedback,
  answer keys and citation excerpts.
- Assessment reinforcement resolves an owned failed current-version attempt
  before embedding, bounds weak-objective retrieval inside the assessment
  lesson, returns only application-owned citations, redacts provider failures,
  and cannot mutate score, mastery, completion, or progression.
- Progress reporting derives from server-owned learning records: learners see
  only self data, teachers are filtered to owned courses before aggregation or
  roster lookup, rosters are bounded, and responses omit email, answer keys,
  chats, and old-version attempts.
- The SadTalker command authorizes ownership before input reads, requires an
  explicit rights/approval assertion, bounds local media, avoids shell
  invocation, kills timed-out process groups, validates output, and stores only
  checksums plus safe failure codes in its audit record. There is no HTTP trigger.
- AI exercise hints now reuse the same lesson/course owner-enrollment queryset as
  exercise reads/submissions, deny outsiders before generation, and never include
  solution code or hidden tests in the hint prompt.
- Forum post/comment updates and deletes now enforce author-or-role-admin object
  permission; privileged status fields have separate actions, public author
  serialization omits account contact/profile fields, and target/duplicate
  constraints cover reactions and reports. Negative tests include cross-owner
  mutation, forged status/targets, teacher pin denial, and public privacy.
- Named course router entries no longer sit behind the empty-prefix course
  detail matcher. Lesson-comment reads/creates require lesson access,
  cross-lesson reply targets are rejected, review creation requires enrollment,
  and comment/review mutations require author or role-admin.
- Scoped request throttles have endpoint-level `429` regression tests for login,
  PDF upload, AI chat, and assessment submission; teacher-application status GET
  remains outside its POST-only submission scope.
- Teacher course mutations are owner-scoped, ignore featured escalation, require
  a usable published lesson before publication, and reject deletion once lesson
  or enrollment data exists instead of cascading an entire learning history.

## Status discipline

Remove or downgrade an item only after adding a regression test and verifying
the intended enforcement point. Formatting cleanup alone does not change risk.
