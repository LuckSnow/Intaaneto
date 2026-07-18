# RAG architecture

## MVP boundary

Start with approved lesson text and teacher-uploaded PDF material. Support
grounded questions scoped to one lesson first, then widen retrieval to an
enrolled course. Keep multimedia generation downstream and out of the RAG core.

## Data flow

```text
Teacher material
  -> validate and normalize
  -> create source version/checksum
  -> chunk with location metadata
  -> embed
  -> persist vectors + searchable metadata
  -> mark version ready

Student question + authorized lesson/course scope
  -> validate scope and enrollment
  -> retrieve filtered candidates
  -> optionally rerank
  -> apply evidence threshold
  -> generate grounded Vietnamese answer
  -> return citations and retrieval status
  -> persist safe observability metadata
```

## Recommended MVP components

Use these as a starting proposal, not as claims about existing code:

- PostgreSQL plus `pgvector` for vectors, keeping operational complexity low
  while the project already depends on PostgreSQL.
- Plain Django services and narrow provider protocols for extraction, embedding,
  retrieval, and generation.
- Background ingestion once file processing becomes slow or unreliable. A
  synchronous service is acceptable for the first tested slice, but never run
  it inside the chat path.
- Hybrid retrieval can follow dense retrieval after the baseline is evaluated;
  avoid adding it without evidence that it improves the learning corpus.

## Model and storage topology

Use a hybrid deployment for the first research prototype:

- Run an embedding model locally or in the backend's private inference service.
  This keeps document indexing predictable and can reduce per-request cost.
- Call an online generation model through a provider interface for answer
  quality and easier experimentation. Configure model and credentials through
  environment variables; do not couple retrieval to one vendor.
- Store original PDF and generated media in object storage such as
  Cloudflare R2. Google Drive may be used for early manual research data, but
  it is not the application's vector database and is less suitable as the
  production media layer.
- Store vectors, chunk text, source/version metadata, and authorization links in
  PostgreSQL with pgvector for the MVP.

Object storage and vector storage solve different problems:

```text
R2 / file storage       -> original documents, audio, images, generated video
PostgreSQL + pgvector   -> chunks, embeddings, source metadata, access scope
Django database         -> users, courses, lessons, assessments, progress
```

Two models are sufficient for the core RAG path: an embedding model and a
generation model. The full virtual-lecturer feature later adds separate speech
and media capabilities such as TTS, avatar/lip-sync, or video rendering; these
must remain downstream consumers of approved lesson knowledge.

## Suggested persistent concepts

- `KnowledgeSource`: owning lesson, file/content origin, checksum, status,
  version, parser metadata, timestamps, and processing error.
- `KnowledgeChunk`: source, ordinal, normalized text, token/character counts,
  PDF page metadata, embedding, and active/version status.
- Optional `RetrievalTrace`: non-sensitive question hash or text policy,
  selected chunk IDs/scores, model/config version, latency, and fallback status.

Choose final Django names after checking existing naming conventions. Add DB
constraints for source version uniqueness and chunk ordinal uniqueness.

## Service boundaries

- Extraction: file/content to normalized sections with locations.
- Chunking: deterministic sections to bounded, overlapping chunks.
- Embedding: text batch to vectors; validate configured dimension.
- Indexing: idempotent orchestration and atomic activation of a new version.
- Retrieval: authorized scope plus query to ranked evidence.
- Answering: evidence plus conversation context to structured answer/citations.

The generation provider must not decide authorization or fabricate citation
IDs. Build citations from retrieved database records after generation.

## Scope and conversation

Store lesson/course identifiers in server-owned session context after checking
access. Treat context IDs supplied on later requests as untrusted. Limit or
summarize conversation history independently from retrieved knowledge so old
chat messages do not displace evidence.

## Configuration

Configure, do not hardcode:

- generation and embedding provider/model;
- embedding dimension;
- chunk size and overlap;
- candidate count and final evidence count;
- minimum evidence threshold;
- timeouts, retries, and maximum input/history size.

Pin dependency versions and document any required PostgreSQL extension in the
runtime configuration when it is actually introduced.
