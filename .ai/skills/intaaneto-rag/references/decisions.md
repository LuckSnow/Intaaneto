# Architecture decisions

Keep entries concise. `Proposed` means guidance, not an implemented fact. When a
decision is accepted or implemented, change its status and add the date plus
affected files or migration.

## RAG-001 — RAG before multimedia

- Status: Accepted by product direction
- Date: 2026-07-13
- Decision: Treat grounded retrieval and learning assistance as the AI core;
  defer avatar, video, and voice work until RAG MVP criteria are met.
- Reason: Other AI experiences depend on trustworthy lesson knowledge.

## RAG-002 — PostgreSQL vector storage for MVP

- Status: Implemented
- Date: 2026-07-13
- Affected: `docker-compose.yml`, `backend/requirements.txt`, and
  `ai_assistant.0003`
- Decision: Add pgvector to the existing PostgreSQL deployment instead of a
  separate vector database.
- Reason: Minimize infrastructure and keep authorization metadata with Django
  entities while corpus scale is still small.
- Revisit when: measured scale, filtering, latency, or operations demand a
  dedicated search system.

## RAG-003 — Explicit pipeline over orchestration framework

- Status: Implemented for lesson indexing
- Date: 2026-07-13
- Affected: `backend/apps/ai_assistant/rag_services.py`
- Decision: Implement narrow Python/Django service interfaces before adopting
  LangChain, LlamaIndex, or an agent framework.
- Reason: The MVP pipeline is small and needs transparent authorization,
  citations, failure handling, and tests.
- Revisit when: repeated orchestration complexity is demonstrated in code.

## RAG-004 — Lesson scope before course scope

- Status: Implemented for retrieval
- Date: 2026-07-14
- Affected: `backend/apps/ai_assistant/access.py`,
  `backend/apps/ai_assistant/rag_services.py`, and retrieval tests
- Decision: Ship retrieval scoped to one authorized lesson, then expand to an
  enrolled course.
- Reason: It gives a small vertical slice and clearer evaluation ground truth.

## RAG-005 — Hybrid local embedding and online generation

- Status: Implemented for the current provider seams
- Date: 2026-07-13
- Affected: `backend/apps/ai_assistant/rag_services.py` and
  `backend/config/settings/base.py`
- Decision: Run embeddings locally and access the response/generation model
  through a configurable online API for the first prototype.
- Reason: Local embedding controls indexing cost and document handling, while an
  online generator provides stronger response quality without hosting a large
  language model.
- Constraint: Persist embedding model name, version, and dimension. Changing any
  of them requires a controlled full re-index.

## RAG-006 — Object storage is not the knowledge index

- Status: Proposed
- Decision: Use Cloudflare R2 or equivalent for original/generated files and
  PostgreSQL plus pgvector for chunks and embeddings. Treat Google Drive only as
  an optional early research-data source, not the runtime vector store.
- Reason: Retrieval needs vector similarity, metadata filtering, versioning,
  transactional updates, and authorization relationships.

## RAG-007 — Defer a fixed vector dimension and ANN index

- Status: Accepted and implemented for Slice 1
- Date: 2026-07-13
- Decision: Store pgvector values without a schema-fixed dimension while
  persisting and validating provider, model, revision, and dimension on every
  source version. Add an ANN index only after the embedding baseline is
  evaluated; retrieval must filter to a compatible active source first.
- Reason: The initial 384-dimensional multilingual model is provisional. This
  avoids a schema migration merely to compare another local model while keeping
  each active lesson index internally dimension-consistent.

## RAG-008 — Exact filtered cosine retrieval baseline

- Status: Implemented
- Date: 2026-07-14
- Affected: `backend/apps/ai_assistant/rag_services.py`, retrieval settings, and
  `backend/apps/ai_assistant/test_rag_retrieval.py`
- Decision: Resolve one authorized lesson and compatible active source before
  exact pgvector cosine ranking. Use a configurable top-k and a provisional
  minimum similarity threshold of `0.45`; do not invoke an LLM in this service.
- Reason: Exact search is transparent and sufficient for the current small
  corpus, provides a measurable retrieval baseline, and prevents global search
  results from crossing the access boundary.
- Revisit when: the Vietnamese evaluation set justifies threshold/model tuning,
  reranking, hybrid retrieval, or an ANN index.

## RAG-009 — Application-owned grounded citations and fallback

- Status: Implemented
- Date: 2026-07-14
- Affected: `backend/apps/ai_assistant/rag_answering.py`, `services.py`,
  `views.py`, migration `0004`, and `frontend/src/pages/LessonPage.jsx`
- Decision: Skip generation unless lesson-scoped evidence clears the configured
  threshold. Supply bounded evidence as untrusted data, generate a plain answer,
  and construct citation objects only from the selected authorized chunks in
  application code.
- Reason: The generation model must not control access scope or fabricate source
  identifiers. Deterministic fallback also avoids cost and hallucination when the
  lesson cannot support an answer.
- Constraint: Persist only bounded retrieval identifiers/scores/latency with the
  message; do not persist embeddings, provider diagnostics, or full prompts.

## RAG-010 — Explicit online generation provider selection

- Status: Implemented
- Date: 2026-07-15
- Affected: `backend/apps/ai_assistant/services.py`, generation settings,
  environment example, and provider tests
- Decision: Select direct OpenAI or Gemini generation explicitly through a
  server-side setting. Keep separate credentials and use Gemini's
  OpenAI-compatible endpoint through the existing SDK and provider protocol.
- Reason: Provider choice must be replaceable without coupling lesson indexing,
  authorized retrieval, prompts, or application-owned citations to one vendor.
- Constraint: Fail closed for a missing key or unknown provider. Free-tier
  providers are for non-sensitive prototype material only unless their data
  handling terms meet the deployment's privacy requirements.
