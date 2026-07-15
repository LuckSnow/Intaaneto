import json
from pathlib import Path

import pytest
from django.core.exceptions import PermissionDenied

from apps.courses.models import Course, Enrollment, Lesson
from apps.users.models import User

from .models import KnowledgeChunk, KnowledgeSource
from .rag_services import LessonRetrievalError, retrieve_lesson_evidence


FIXTURE_PATH = Path(__file__).parent / 'fixtures' / 'retrieval_baseline_vi.json'


class RetrievalEmbeddingProvider:
    provider_name = 'test-local'
    model_name = 'test-model-v1'
    model_revision = 'test-revision-1'
    dimension = 3

    def __init__(self, query_vectors=None, error=None):
        self.query_vectors = query_vectors or {}
        self.error = error
        self.query_calls = 0

    def embed_documents(self, texts):
        raise AssertionError('Retrieval must not embed documents')

    def embed_query(self, text):
        self.query_calls += 1
        if self.error:
            raise self.error
        return self.query_vectors[text]


def create_source(lesson, *, active=True, version=1, embeddings=None):
    embeddings = embeddings or [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]
    texts = [
        'RAG truy xuất các đoạn tài liệu phù hợp trước khi mô hình trả lời.',
        'Danh sách Python là kiểu dữ liệu có thể thay đổi sau khi được tạo.',
        'Bột mì và men là hai nguyên liệu thường dùng để làm bánh mì.',
    ]
    source = KnowledgeSource.objects.create(
        lesson=lesson,
        source_type='lesson_content',
        version=version,
        content_checksum=f'checksum-{lesson.id}-{version}',
        normalized_text='\n\n'.join(texts),
        status='ready' if active else 'archived',
        is_active=active,
        embedding_provider='test-local',
        embedding_model='test-model-v1',
        embedding_revision='test-revision-1',
        embedding_dimension=3,
        chunker_version='test-v1',
        chunk_size=100,
        chunk_overlap=10,
    )
    offset = 0
    for ordinal, (text, embedding) in enumerate(zip(texts, embeddings)):
        KnowledgeChunk.objects.create(
            source=source,
            ordinal=ordinal,
            text=text,
            start_offset=offset,
            end_offset=offset + len(text),
            char_count=len(text),
            embedding=embedding,
        )
        offset += len(text) + 2
    return source


@pytest.fixture
def retrieval_lesson(teacher_user, student_user):
    course = Course.objects.create(
        title='Kho tri thức được phép',
        slug='kho-tri-thuc-duoc-phep',
        description='Khóa học dùng cho kiểm thử retrieval',
        teacher=teacher_user,
        is_published=True,
    )
    lesson = Lesson.objects.create(
        course=course,
        title='RAG và Python',
        slug='rag-va-python',
        content='Nội dung đã được index.',
        is_published=True,
    )
    Enrollment.objects.create(user=student_user, course=course)
    return lesson


@pytest.mark.django_db
def test_vietnamese_relevance_fixture_ranks_expected_chunks(
    student_user, retrieval_lesson
):
    source = create_source(retrieval_lesson)
    cases = json.loads(FIXTURE_PATH.read_text(encoding='utf-8'))
    vectors = {
        cases[0]['question']: [1.0, 0.0, 0.0],
        cases[1]['question']: [0.0, 1.0, 0.0],
        cases[2]['question']: [-1.0, -1.0, -1.0],
    }
    provider = RetrievalEmbeddingProvider(vectors)

    for case in cases:
        result = retrieve_lesson_evidence(
            actor=student_user,
            lesson_id=retrieval_lesson.id,
            question=case['question'],
            provider=provider,
            top_k=3,
            minimum_score=0.45,
        )
        assert result.source_id == source.id
        assert result.source_version == source.version
        assert all(chunk.lesson_id == retrieval_lesson.id for chunk in result.chunks)
        assert all(chunk.source_id == source.id for chunk in result.chunks)
        if case['answerable']:
            assert result.status == 'ready'
            assert result.has_sufficient_evidence is True
            assert result.chunks[0].ordinal == case['expected_chunk_ordinal']
            assert result.chunks[0].score == 1.0
        else:
            assert result.status == 'weak_evidence'
            assert result.has_sufficient_evidence is False
            assert result.chunks[0].score < 0.45


@pytest.mark.django_db
@pytest.mark.parametrize('actor_role', ['student', 'teacher'])
def test_outsider_is_rejected_before_query_embedding(
    actor_role, retrieval_lesson
):
    outsider = User.objects.create_user(
        email=f'retrieval-{actor_role}-outsider@example.com',
        username=f'retrieval-{actor_role}-outsider',
        full_name='Retrieval Outsider',
        password='Testpass123!',
        role=actor_role,
    )
    provider = RetrievalEmbeddingProvider({'Câu hỏi': [1.0, 0.0, 0.0]})
    create_source(retrieval_lesson)

    with pytest.raises(PermissionDenied):
        retrieve_lesson_evidence(
            actor=outsider,
            lesson_id=retrieval_lesson.id,
            question='Câu hỏi',
            provider=provider,
        )

    assert provider.query_calls == 0


@pytest.mark.django_db
def test_retrieval_never_includes_cross_course_chunks(
    teacher_user, student_user, retrieval_lesson
):
    authorized_source = create_source(
        retrieval_lesson,
        embeddings=[[0.8, 0.2, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
    )
    other_teacher = User.objects.create_user(
        email='other-rag-teacher@example.com',
        username='other-rag-teacher',
        full_name='Other RAG Teacher',
        password='Testpass123!',
        role='teacher',
    )
    private_course = Course.objects.create(
        title='Khóa học riêng',
        slug='khoa-hoc-rieng',
        description='Không được phép truy cập',
        teacher=other_teacher,
    )
    private_lesson = Lesson.objects.create(
        course=private_course,
        title='Bài học riêng',
        slug='bai-hoc-rieng',
        content='Nội dung riêng',
    )
    private_source = create_source(private_lesson)
    provider = RetrievalEmbeddingProvider({'RAG là gì?': [1.0, 0.0, 0.0]})

    result = retrieve_lesson_evidence(
        actor=student_user,
        lesson_id=retrieval_lesson.id,
        question='RAG là gì?',
        provider=provider,
    )

    assert result.source_id == authorized_source.id
    assert private_source.id not in {chunk.source_id for chunk in result.chunks}
    with pytest.raises(PermissionDenied):
        retrieve_lesson_evidence(
            actor=student_user,
            lesson_id=private_lesson.id,
            question='RAG là gì?',
            provider=provider,
        )


@pytest.mark.django_db
def test_archived_source_is_excluded(student_user, retrieval_lesson):
    archived = create_source(retrieval_lesson, active=False, version=1)
    active = create_source(
        retrieval_lesson,
        active=True,
        version=2,
        embeddings=[[0.6, 0.8, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
    )
    provider = RetrievalEmbeddingProvider({'RAG là gì?': [1.0, 0.0, 0.0]})

    result = retrieve_lesson_evidence(
        actor=student_user,
        lesson_id=retrieval_lesson.id,
        question='RAG là gì?',
        provider=provider,
    )

    assert result.source_id == active.id
    assert archived.id not in {chunk.source_id for chunk in result.chunks}


@pytest.mark.django_db
def test_missing_compatible_index_is_reported_without_embedding(
    student_user, retrieval_lesson
):
    create_source(retrieval_lesson)
    provider = RetrievalEmbeddingProvider({'Câu hỏi': [1.0, 0.0, 0.0]})
    provider.model_revision = 'different-revision'

    result = retrieve_lesson_evidence(
        actor=student_user,
        lesson_id=retrieval_lesson.id,
        question='Câu hỏi',
        provider=provider,
    )

    assert result.status == 'not_indexed'
    assert result.chunks == ()
    assert provider.query_calls == 0


@pytest.mark.django_db
def test_query_embedding_failure_is_bounded(student_user, retrieval_lesson):
    create_source(retrieval_lesson)
    provider = RetrievalEmbeddingProvider(error=RuntimeError('private model detail'))

    with pytest.raises(LessonRetrievalError, match='Query embedding failed') as exc_info:
        retrieve_lesson_evidence(
            actor=student_user,
            lesson_id=retrieval_lesson.id,
            question='Câu hỏi',
            provider=provider,
        )

    assert 'private model detail' not in str(exc_info.value)


@pytest.mark.django_db
@pytest.mark.parametrize('actor_kind', ['owner', 'admin'])
def test_teacher_owner_and_admin_can_retrieve(
    actor_kind, teacher_user, retrieval_lesson
):
    source = create_source(retrieval_lesson)
    if actor_kind == 'owner':
        actor = teacher_user
    else:
        actor = User.objects.create_user(
            email='retrieval-admin@example.com',
            username='retrieval-admin',
            full_name='Retrieval Admin',
            password='Testpass123!',
            role='admin',
        )
    provider = RetrievalEmbeddingProvider({'RAG là gì?': [1.0, 0.0, 0.0]})

    result = retrieve_lesson_evidence(
        actor=actor,
        lesson_id=retrieval_lesson.id,
        question='RAG là gì?',
        provider=provider,
    )

    assert result.status == 'ready'
    assert result.source_id == source.id


@pytest.mark.django_db
def test_invalid_query_vector_dimension_is_rejected(student_user, retrieval_lesson):
    create_source(retrieval_lesson)
    provider = RetrievalEmbeddingProvider({'Câu hỏi': [1.0, 0.0]})

    with pytest.raises(LessonRetrievalError, match='Query embedding failed'):
        retrieve_lesson_evidence(
            actor=student_user,
            lesson_id=retrieval_lesson.id,
            question='Câu hỏi',
            provider=provider,
        )


@pytest.mark.django_db
def test_question_length_is_bounded_before_query_embedding(
    settings, student_user, retrieval_lesson
):
    settings.RAG_MAX_QUESTION_CHARS = 5
    create_source(retrieval_lesson)
    provider = RetrievalEmbeddingProvider({'quá dài': [1.0, 0.0, 0.0]})

    with pytest.raises(LessonRetrievalError, match='length limit'):
        retrieve_lesson_evidence(
            actor=student_user,
            lesson_id=retrieval_lesson.id,
            question='quá dài',
            provider=provider,
        )

    assert provider.query_calls == 0
