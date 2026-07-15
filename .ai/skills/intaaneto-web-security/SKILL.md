---
name: intaaneto-web-security
description: Secure, review, or test Intaaneto's Django, React, REST API, authentication, authorization, course content, exercises, uploads, RAG, AI Tutor, object storage, secrets, and deployment. Use for any change involving users or roles, permissions, serializers, API endpoints, JWT, Firebase, student data, teacher materials, hidden answers, vector retrieval, prompt construction, file processing, Cloudflare R2, logging, rate limits, or production configuration.
---

# Intaaneto Web Security

## Security objective

Protect learner data, teacher-owned material, assessment integrity, and RAG
knowledge boundaries without blocking the smallest useful RAG vertical slice.
Treat every identifier, role, file, prompt, model response, and frontend field as
untrusted until the backend validates it.

## Start every security-relevant task

1. Read [current-risks.md](references/current-risks.md) and verify affected facts
   against the repository.
2. Read [access-control.md](references/access-control.md) for user, course,
   lesson, exercise, or assessment changes.
3. Read [rag-security.md](references/rag-security.md) for ingestion, retrieval,
   chat, embedding, generation, citation, or AI evaluation changes.
4. Read [web-checklist.md](references/web-checklist.md) for authentication,
   uploads, storage, frontend, logging, deployment, or dependency work.
5. Identify protected assets, actors, trust boundaries, abuse cases, and the
   backend enforcement point before editing code.

## Non-negotiable rules

- Enforce authorization in backend querysets/services before reading or mutating
  objects. UI hiding and prompts are not security controls.
- Default to deny. Grant the narrowest action and object scope required.
- Separate serializers by actor and action. Never expose model fields through
  `fields = '__all__'` when records contain roles, secrets, solutions, hidden
  tests, internal status, provider data, or ownership fields.
- Never accept `user`, `teacher`, ownership, enrollment, role, score, completion,
  citation, source scope, or processing status as trusted client decisions.
- Never allow self-service elevation to teacher/admin without an explicit,
  auditable approval policy.
- Keep API keys and storage credentials server-side. Never return them, place
  them in Vite variables, commit them, or include them in logs/errors.
- Validate files by allowlisted extension plus content/type checks; bound size,
  page/slide count, extracted text, parser time, and decompression behavior.
- Treat document text, retrieved chunks, chat history, and model output as
  untrusted data. They cannot override system policy or access scope.
- Keep exercise solutions and hidden test cases out of student-facing APIs,
  prompts, citations, logs, and retrieval indexes.
- Return generic external errors and preserve structured internal diagnostics
  without secrets or unnecessary student content.
- Add negative tests. A happy-path test does not prove authorization.

## Required RAG security gate

Do not consider a RAG slice complete until tests prove:

1. An enrolled learner retrieves only active chunks from the authorized scope.
2. A non-enrolled learner and a different course receive no protected chunks.
3. Client-supplied lesson/course/session IDs cannot widen server-owned scope.
4. Prompt injection in source documents cannot change policy or disclose data.
5. Every citation belongs to a chunk retrieved and authorized for that request.
6. Weak evidence returns a grounded fallback instead of invented course facts.
7. Logs and traces exclude secrets, embeddings, hidden answers, and unnecessary
   personal or document content.

## Review workflow

1. Map endpoint → permission → queryset → serializer → service → external calls.
2. Test anonymous, learner, non-enrolled learner, teacher-owner, other teacher,
   and admin behavior where applicable.
3. Test list and detail access separately from create, update, delete, and custom
   actions; DRF custom actions do not inherit intent automatically.
4. Inspect both request and response schemas for writable privilege fields and
   accidental disclosure.
5. Check failure behavior, retry behavior, rate limits, logging, and cleanup.
6. Run focused security/contract tests, then broader backend/frontend checks.
7. Report findings by severity, evidence, exploit impact, and smallest safe fix.

Do not weaken a security boundary merely to make an existing frontend request
pass. Repair the contract and retain server-side enforcement.

## Finish every task

- Confirm no new secret or generated sensitive artifact entered Git.
- Confirm migrations and defaults do not create public access accidentally.
- Confirm authorization occurs before retrieval, provider calls, or expensive
  processing.
- Update `current-risks.md` only when code and tests prove a risk is fixed or a
  new risk exists.
- Record remaining P0/P1 risks explicitly; do not describe an untested control
  as secure.

