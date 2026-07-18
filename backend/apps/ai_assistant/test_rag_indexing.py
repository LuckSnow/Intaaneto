import hashlib
from unittest.mock import patch

import pytest
from django.core.exceptions import PermissionDenied

from apps.courses.models import Course, Lesson
from apps.users.models import User

from .models import KnowledgeChunk, KnowledgeSource
from .rag_services import (
    LessonIndexingError,
    TextChunk,
    chunk_text,
    index_lesson,
    normalize_lesson_text,
    pdf_page_ranges,
)


class FakeEmbeddingProvider:
    provider_name = 'test-local'
    model_name = 'test-model-v1'
    model_revision = 'test-revision-1'
    dimension = 3

    def __init__(self, error=None, callback=None):
        self.error = error
        self.callback = callback
        self.calls = 0

    def embed_documents(self, texts):
        self.calls += 1
        if self.error:
            raise self.error
        if self.callback:
            self.callback()
        vectors = []
        for text in texts:
            digest = hashlib.sha256(text.encode()).digest()
            vectors.append([digest[0] / 255, digest[1] / 255, digest[2] / 255])
        return vectors


@pytest.fixture
def indexable_lesson(teacher_user):
    course = Course.objects.create(
        title='RAG nhập môn',
        slug='rag-nhap-mon',
        description='Khóa học thử nghiệm',
        teacher=teacher_user,
    )
    return Lesson.objects.create(
        course=course,
        title='Nguồn tri thức',
        slug='nguon-tri-thuc',
        content='Đoạn đầu về RAG.\n\nĐoạn sau giải thích embedding và chunking.',
    )


def test_normalization_prefers_extracted_text_and_chunking_is_deterministic(indexable_lesson):
    indexable_lesson.extracted_text = '  Nội dung PDF.  \r\n\r\n\r\nPhần hai.  '
    normalized = normalize_lesson_text(indexable_lesson)

    assert normalized.source_type == 'extracted_text'
    assert normalized.text == 'Nội dung PDF.\n\nPhần hai.'
    first = chunk_text(normalized.text, chunk_size=16, overlap=4)
    second = chunk_text(normalized.text, chunk_size=16, overlap=4)
    assert first == second
    assert [chunk.ordinal for chunk in first] == list(range(len(first)))
    assert all(normalized.text[item.start_offset:item.end_offset] == item.text for item in first)
    assert all(len(item.text) <= 16 for item in first)


def test_pdf_page_ranges_preserve_original_page_numbers_and_cross_page_chunks():
    text = '--- Trang 1 ---\nAlpha\n\n--- Trang 3 ---\nBeta'
    page_three_offset = text.index('--- Trang 3 ---')
    chunks = [
        TextChunk(0, text[:page_three_offset].strip(), 0, page_three_offset),
        TextChunk(1, text[page_three_offset - 3:], page_three_offset - 3, len(text)),
        TextChunk(2, text[page_three_offset:], page_three_offset, len(text)),
    ]

    assert pdf_page_ranges(text, chunks) == [(1, 1), (1, 3), (3, 3)]


@pytest.mark.django_db
def test_indexed_pdf_chunks_store_deterministic_page_ranges(
    teacher_user, indexable_lesson
):
    indexable_lesson.extracted_text = (
        '--- Trang 1 ---\nNội dung trang đầu về retrieval.\n\n'
        '--- Trang 3 ---\nNội dung trang ba về citation.'
    )
    indexable_lesson.save(update_fields=['extracted_text'])

    source, created = index_lesson(
        actor=teacher_user,
        lesson_id=indexable_lesson.id,
        provider=FakeEmbeddingProvider(),
        chunk_size=48,
        chunk_overlap=8,
    )

    ranges = list(source.chunks.values_list('page_start', 'page_end'))
    assert created is True
    assert ranges
    assert all(start is not None and end >= start for start, end in ranges)
    assert ranges[0][0] == 1
    assert ranges[-1][1] == 3


@pytest.mark.django_db
def test_unchanged_lesson_index_is_idempotent(teacher_user, indexable_lesson):
    provider = FakeEmbeddingProvider()

    first, first_created = index_lesson(
        actor=teacher_user,
        lesson_id=indexable_lesson.id,
        provider=provider,
        chunk_size=30,
        chunk_overlap=5,
    )
    chunk_ids = list(first.chunks.values_list('id', flat=True))
    second, second_created = index_lesson(
        actor=teacher_user,
        lesson_id=indexable_lesson.id,
        provider=provider,
        chunk_size=30,
        chunk_overlap=5,
    )

    assert first_created is True
    assert second_created is False
    assert second.id == first.id
    assert provider.calls == 1
    assert KnowledgeSource.objects.filter(is_active=True).count() == 1
    assert list(KnowledgeChunk.objects.values_list('id', flat=True)) == chunk_ids


@pytest.mark.django_db
def test_changed_lesson_atomically_replaces_active_source(teacher_user, indexable_lesson):
    provider = FakeEmbeddingProvider()
    original, _ = index_lesson(
        actor=teacher_user,
        lesson_id=indexable_lesson.id,
        provider=provider,
        chunk_size=30,
        chunk_overlap=5,
    )
    indexable_lesson.content = 'Nội dung hoàn toàn mới về tìm kiếm vector và phân quyền.'
    indexable_lesson.save(update_fields=['content'])

    replacement, created = index_lesson(
        actor=teacher_user,
        lesson_id=indexable_lesson.id,
        provider=provider,
        chunk_size=30,
        chunk_overlap=5,
    )

    original.refresh_from_db()
    assert created is True
    assert replacement.version == original.version + 1
    assert replacement.is_active is True
    assert replacement.status == 'ready'
    assert original.is_active is False
    assert original.status == 'archived'
    assert KnowledgeSource.objects.filter(lesson=indexable_lesson, is_active=True).count() == 1
    assert replacement.chunks.count() > 0


@pytest.mark.django_db
def test_embedding_failure_keeps_previous_index_active(teacher_user, indexable_lesson):
    active, _ = index_lesson(
        actor=teacher_user,
        lesson_id=indexable_lesson.id,
        provider=FakeEmbeddingProvider(),
        chunk_size=30,
        chunk_overlap=5,
    )
    active_chunk_ids = list(active.chunks.values_list('id', flat=True))
    indexable_lesson.content = 'Nội dung thay đổi nhưng embedding sẽ thất bại.'
    indexable_lesson.save(update_fields=['content'])

    with pytest.raises(LessonIndexingError):
        index_lesson(
            actor=teacher_user,
            lesson_id=indexable_lesson.id,
            provider=FakeEmbeddingProvider(error=RuntimeError('private detail')),
            chunk_size=30,
            chunk_overlap=5,
        )

    active.refresh_from_db()
    assert active.is_active is True
    assert KnowledgeSource.objects.count() == 1
    assert list(KnowledgeChunk.objects.values_list('id', flat=True)) == active_chunk_ids


@pytest.mark.django_db
def test_database_failure_rolls_back_replacement(teacher_user, indexable_lesson):
    active, _ = index_lesson(
        actor=teacher_user,
        lesson_id=indexable_lesson.id,
        provider=FakeEmbeddingProvider(),
        chunk_size=30,
        chunk_overlap=5,
    )
    indexable_lesson.content = 'Một source mới sẽ lỗi khi lưu chunk.'
    indexable_lesson.save(update_fields=['content'])

    with patch.object(KnowledgeChunk.objects, 'bulk_create', side_effect=RuntimeError('db failure')):
        with pytest.raises(RuntimeError):
            index_lesson(
                actor=teacher_user,
                lesson_id=indexable_lesson.id,
                provider=FakeEmbeddingProvider(),
                chunk_size=30,
                chunk_overlap=5,
            )

    active.refresh_from_db()
    assert active.is_active is True
    assert KnowledgeSource.objects.count() == 1
    assert KnowledgeSource.objects.filter(is_active=True).count() == 1


@pytest.mark.django_db
def test_content_change_during_embedding_keeps_previous_index_active(
    teacher_user, indexable_lesson
):
    active, _ = index_lesson(
        actor=teacher_user,
        lesson_id=indexable_lesson.id,
        provider=FakeEmbeddingProvider(),
        chunk_size=30,
        chunk_overlap=5,
    )
    indexable_lesson.content = 'Phiên bản hai bắt đầu được embedding.'
    indexable_lesson.save(update_fields=['content'])

    def change_lesson_again():
        Lesson.objects.filter(pk=indexable_lesson.pk).update(
            content='Phiên bản ba được lưu trong lúc embedding.'
        )

    with pytest.raises(LessonIndexingError, match='changed during indexing'):
        index_lesson(
            actor=teacher_user,
            lesson_id=indexable_lesson.id,
            provider=FakeEmbeddingProvider(callback=change_lesson_again),
            chunk_size=30,
            chunk_overlap=5,
        )

    active.refresh_from_db()
    assert active.is_active is True
    assert KnowledgeSource.objects.count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize('actor_kind', ['student', 'other_teacher'])
def test_non_owner_is_rejected_before_embedding(
    actor_kind, student_user, teacher_user, indexable_lesson
):
    if actor_kind == 'student':
        actor = student_user
    else:
        actor = User.objects.create_user(
            email='other-teacher@example.com',
            username='other-teacher',
            full_name='Other Teacher',
            password='Testpass123!',
            role='teacher',
        )
    provider = FakeEmbeddingProvider()

    with pytest.raises(PermissionDenied):
        index_lesson(
            actor=actor,
            lesson_id=indexable_lesson.id,
            provider=provider,
            chunk_size=30,
            chunk_overlap=5,
        )

    assert provider.calls == 0
    assert KnowledgeSource.objects.count() == 0


@pytest.mark.django_db
def test_admin_can_index_any_lesson(indexable_lesson):
    admin = User.objects.create_user(
        email='admin-rag@example.com',
        username='admin-rag',
        full_name='RAG Admin',
        password='Testpass123!',
        role='admin',
    )

    source, created = index_lesson(
        actor=admin,
        lesson_id=indexable_lesson.id,
        provider=FakeEmbeddingProvider(),
        chunk_size=30,
        chunk_overlap=5,
    )

    assert created is True
    assert source.is_active is True
