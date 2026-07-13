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

- Status: Proposed
- Decision: Add pgvector to the existing PostgreSQL deployment instead of a
  separate vector database.
- Reason: Minimize infrastructure and keep authorization metadata with Django
  entities while corpus scale is still small.
- Revisit when: measured scale, filtering, latency, or operations demand a
  dedicated search system.

## RAG-003 — Explicit pipeline over orchestration framework

- Status: Proposed
- Decision: Implement narrow Python/Django service interfaces before adopting
  LangChain, LlamaIndex, or an agent framework.
- Reason: The MVP pipeline is small and needs transparent authorization,
  citations, failure handling, and tests.
- Revisit when: repeated orchestration complexity is demonstrated in code.

## RAG-004 — Lesson scope before course scope

- Status: Proposed
- Decision: Ship retrieval scoped to one authorized lesson, then expand to an
  enrolled course.
- Reason: It gives a small vertical slice and clearer evaluation ground truth.

## RAG-005 — Hybrid local embedding and online generation

- Status: Proposed
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
