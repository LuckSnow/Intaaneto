"""Safe reconstruction of persisted lesson-chat history."""

from django.conf import settings

from .models import KnowledgeChunk


KNOWN_RETRIEVAL_STATUSES = {'ready', 'weak_evidence', 'not_indexed'}


def _citation_for_chunk(*, chunk, lesson, score):
    return {
        'id': f'knowledge-chunk-{chunk.id}',
        'chunk_id': chunk.id,
        'source_id': chunk.source_id,
        'source_version': chunk.source.version,
        'lesson_id': lesson.id,
        'lesson_title': lesson.title,
        'source_type': chunk.source.source_type,
        'ordinal': chunk.ordinal,
        'location': {
            'start_offset': chunk.start_offset,
            'end_offset': chunk.end_offset,
            'page_start': chunk.page_start,
            'page_end': chunk.page_end,
        },
        'excerpt': chunk.text[:settings.RAG_CITATION_EXCERPT_CHARS].strip(),
        'score': score,
    }


def serialize_lesson_chat_messages(*, messages, lesson):
    """Hydrate citations from DB records constrained to an authorized lesson.

    Retrieval JSON is treated only as a set of references. Citation text and
    source attributes always come from the database and must match the stored
    source/version contract before they are returned.
    """

    chunk_ids = set()
    for message in messages:
        retrieval = (message.retrieval_metadata or {}).get('retrieval', {})
        for selected in retrieval.get('selected_chunks', []):
            chunk_id = selected.get('chunk_id') if isinstance(selected, dict) else None
            if isinstance(chunk_id, int) and not isinstance(chunk_id, bool):
                chunk_ids.add(chunk_id)

    chunks = {
        chunk.id: chunk
        for chunk in KnowledgeChunk.objects.filter(
            id__in=chunk_ids,
            source__lesson=lesson,
        ).select_related('source')
    }

    serialized = []
    for message in messages:
        item = {
            'id': message.id,
            'role': message.role,
            'content': message.content,
            'created_at': message.created_at,
            'grounded': None,
            'retrieval_status': None,
            'citations': [],
        }
        if message.role == 'assistant':
            metadata = message.retrieval_metadata or {}
            retrieval = metadata.get('retrieval', {})
            status = retrieval.get('status')
            item['retrieval_status'] = (
                status if status in KNOWN_RETRIEVAL_STATUSES else 'unavailable'
            )
            expected_source_id = retrieval.get('source_id')
            expected_source_version = retrieval.get('source_version')
            citations = []
            for selected in retrieval.get('selected_chunks', []):
                if not isinstance(selected, dict):
                    continue
                chunk = chunks.get(selected.get('chunk_id'))
                if (
                    chunk is None
                    or chunk.source_id != expected_source_id
                    or chunk.source.version != expected_source_version
                ):
                    continue
                citations.append(_citation_for_chunk(
                    chunk=chunk,
                    lesson=lesson,
                    score=selected.get('score'),
                ))
            item['citations'] = citations
            item['grounded'] = bool(
                metadata.get('grounded') is True
                and status == 'ready'
                and citations
            )
        serialized.append(item)
    return serialized
