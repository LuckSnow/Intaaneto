# RAG and AI security

## Trust boundaries

Untrusted inputs include uploads, extracted text, chunk metadata, questions,
student code, chat history, client scope IDs, retrieved instructions, provider
responses, citations proposed by a model, and external URLs.

Trusted decisions must remain in application code: identity, enrollment,
teacher ownership, retrieval filters, active source versions, evidence threshold,
score policy, progression, and citation membership.

## Secure ingestion

- Authorize teacher ownership before accepting a file or starting processing.
- Allowlist supported formats and verify content; do not claim old `.ppt` support
  through a parser that only supports `.pptx`.
- Bound upload bytes, pages/slides, extracted characters, chunk count, parser
  duration, embedding batches, retries, and total cost.
- Store original files under server-generated object keys. Do not trust names or
  allow path traversal/overwrite.
- Scan or isolate risky document processing where practical. Never execute
  macros, scripts, embedded objects, or links.
- Treat extracted instructions as content, not commands.
- Make source versioning and indexing idempotent. Activate a new version only
  after all chunks are ready; exclude failed/stale chunks from retrieval.
- Never index solutions, hidden test cases, secrets, private messages, or data
  outside the approved lesson knowledge scope.

## Secure retrieval

Apply authorization filters in the database query before vector ranking:

```text
authenticated user
  -> server-resolved enrollment/teacher ownership
  -> allowed lesson/course IDs
  -> active approved source versions
  -> vector search inside that filtered set
```

Do not retrieve globally and filter the top results afterward. Do not trust
`lesson_id`, `course_id`, `session_id`, vector IDs, or citation IDs from clients.

## Prompt and response controls

- Keep system policy separate from quoted evidence.
- Delimit evidence and state that it contains untrusted text, not instructions.
- Bound chat history and retrieved context independently.
- Require fallback when evidence is absent or below threshold.
- Construct citations from authorized retrieved records in code. Validate every
  returned citation against the current retrieval set.
- Treat model-generated grades as recommendations until deterministic rules or
  an approved rubric validate and persist the outcome.
- Never place provider error bodies or stack traces directly in student-facing
  messages.

## AI abuse tests

- Document says “ignore previous instructions” or asks for system prompts.
- User asks for another course, another student's history, hidden answers, API
  keys, raw chunks, or full source files.
- User supplies forged lesson/session/citation IDs.
- Evidence contains HTML/JavaScript, URLs, encoded instructions, or false roles.
- Question is unsupported, ambiguous, adversarial, or extremely long.
- Provider times out, rate-limits, returns malformed JSON, or invents citations.
- Re-index happens while queries run; only one complete active version appears.

## Privacy and observability

Store only what the research and product genuinely need. Prefer IDs, scores,
latency, model/config versions, selected chunk IDs, and bounded error codes over
full prompts/documents. Define retention and deletion for chat, submissions,
uploads, traces, and generated media before production use.

