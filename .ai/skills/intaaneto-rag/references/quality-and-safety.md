# Quality and safety

## Retrieval quality

Evaluate retrieval separately from answer generation. For each fixture, record
the authorized scope, question, whether it is answerable, and expected source
locations. Track at minimum whether an expected chunk appears in top-k and
whether unauthorized or irrelevant chunks appear.

Do not tune chunk size, overlap, k, or score thresholds by intuition alone.
Version these settings with evaluation results.

## Answer quality

Require the answerer to:

- answer in age-appropriate Vietnamese;
- use only supplied evidence for course-specific claims;
- distinguish evidence from general guidance if general guidance is allowed;
- cite the supporting source locations;
- say the lesson material is insufficient when evidence is weak;
- guide students without revealing exercise solutions or hidden tests.

Validate citation correctness in application code: every returned citation ID
must belong to a retrieved, authorized chunk in the current request.

## Threats and controls

- Prompt injection in documents: treat retrieved content as data, never as
  system instructions; include adversarial evaluation fixtures.
- Cross-tenant/course leakage: filter at query time using server-authorized IDs
  and test with two users/courses.
- Malicious uploads: allowlist types, verify signatures where practical, bound
  size/pages/text, use parser timeouts, and do not execute embedded content.
- Sensitive logs: avoid API keys, full prompts, student code, and raw documents
  by default; define retention before storing traces.
- Denial of service: bound question length, history, retrieved context, upload
  size, provider timeouts, retries, and user request rate.
- Stale knowledge: activate a complete new source version atomically and exclude
  old/incomplete versions during retrieval.

## Minimum test matrix

- deterministic chunking and stable metadata;
- unchanged and changed source re-indexing;
- empty, malformed, and unsupported documents;
- relevant, irrelevant, and ambiguous questions;
- weak/no evidence fallback;
- citation IDs and locations match retrieved chunks;
- user enrolled vs not enrolled in the scoped lesson/course;
- source text containing instructions to ignore system rules;
- embedding/generation timeout, rate limit, and malformed provider response;
- conversation history cannot override retrieval scope.

