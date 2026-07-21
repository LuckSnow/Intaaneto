# Current security risks

Last repository audit: 2026-07-19. These are observed risks, not proof of
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
- A live Mailjet verification email reached Gmail Spam on 2026-07-18, proving
  basic delivery but not production deliverability. The current personal Gmail
  sender cannot provide project-owned SPF/DKIM/DMARC or BIMI alignment; move to
  an authenticated project domain before public use. Automated tests continue
  to use Django's in-memory email backend.
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
- Local multimedia has no provider credential or network call at render time.
  The project owner approved the current Piper voice and `AI_tutor.png` for
  school research use only; public/commercial distribution rights remain
  unapproved. Two real local performance runs now exist, but human Vietnamese
  voice/caption-timing review and generated-media retention remain operational
  gaps.

## Resolved with regression tests through 2026-07-19

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
- Password reset now returns an enumeration-resistant request response, sends a
  bounded one-hour Django reset token through the configured email backend,
  atomically validates and consumes it, enforces password policy, preserves
  server-owned role/verification state, throttles request and confirmation, and
  invalidates old JWTs through password-hash claims. Tests cover missing users,
  delivery failure, invalid/expired/replayed tokens, weak passwords and old
  access-token rejection.
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
- Assessment authoring authorizes the teacher-owner before provider work,
  accepts only Auto/5/10/15/20, bounds each provider payload to one source region
  and at most four calls, rejects duplicate/incomplete batches, then rechecks the
  active source and persists atomically. The UI confirmation communicates call
  count but is not treated as an authorization boundary.
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
- The historical SadTalker command authorizes ownership before input reads,
  requires an explicit rights/approval assertion, bounds local media, avoids
  shell invocation, kills timed-out process groups, validates output, and stores
  only checksums plus safe failure codes. Its portrait-upload/enqueue HTTP action
  has been removed from the lesson API; the adapter remains for report evidence.
- The active local slide-video endpoint authorizes the teacher-owner before
  reading the tutor asset, persists one active job per lesson, reauthorizes in
  the worker, rejects stale approved-summary or asset checksums, invokes Piper
  and FFmpeg without a shell under time/size bounds, and exposes only bounded
  stage/failure/render metadata. Negative tests cover owner and worker denial,
  missing-model fail-closed, stale state and API redaction. Narration segment
  bounds are also rechecked before tutor-asset access and durable job creation;
  frontend counters and disabled controls are only advisory UX.
- Long-form video scripts are separate teacher-reviewed records bound to the
  current active source and approved-summary checksum. Owner authorization occurs
  before the one provider call; queue and worker recheck mutable state. Lesson
  PDF embedding fetches through `accessible_lessons` and returns 404 to another
  teacher before streaming file bytes. Existing direct development media serving
  is not a production private-object-storage design.
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
