import hashlib
import io
from unittest.mock import patch

import pytest
from django.test import override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from PyPDF2 import PdfWriter
from PyPDF2.generic import DecodedStreamObject, DictionaryObject, NameObject

from apps.ai_assistant.models import KnowledgeSource
from apps.ai_assistant.rag_services import EmbeddingProviderError
from apps.users.models import User

from .models import Course, Lesson
from .services import PDFIngestionError, extract_text_from_pdf, sanitize_extracted_text


class FakeEmbeddingProvider:
    provider_name = 'test-local'
    model_name = 'test-model-v1'
    model_revision = 'test-revision-1'
    dimension = 3

    def __init__(self, error=None):
        self.error = error

    def embed_documents(self, texts):
        if self.error:
            raise self.error
        return [
            [value / 255 for value in hashlib.sha256(text.encode()).digest()[:3]]
            for text in texts
        ]


def make_pdf(text=None, password=None):
    output = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    page = writer.pages[-1]
    if text:
        font = DictionaryObject({
            NameObject('/Type'): NameObject('/Font'),
            NameObject('/Subtype'): NameObject('/Type1'),
            NameObject('/BaseFont'): NameObject('/Helvetica'),
        })
        resources = DictionaryObject({
            NameObject('/Font'): DictionaryObject({
                NameObject('/F1'): writer._add_object(font),
            }),
        })
        stream = DecodedStreamObject()
        stream.set_data(f'BT /F1 12 Tf 72 720 Td ({text}) Tj ET'.encode('ascii'))
        page[NameObject('/Resources')] = resources
        page[NameObject('/Contents')] = writer._add_object(stream)
    if password:
        writer.encrypt(password)
    writer.write(output)
    return output.getvalue()


@pytest.fixture
def owned_course(teacher_user):
    return Course.objects.create(
        title='PDF RAG',
        slug='pdf-rag',
        description='Khóa học PDF',
        teacher=teacher_user,
        is_published=True,
    )


def upload_payload(course, filename='rag.pdf', content=None, content_type='application/pdf'):
    return {
        'course': course.id,
        'title': 'Bài học từ PDF',
        'description': 'Tài liệu thử nghiệm',
        'order': 1,
        'uploaded_file': SimpleUploadedFile(
            filename,
            content if content is not None else make_pdf('RAG uses retrieval and citations.'),
            content_type=content_type,
        ),
    }


def test_pdf_extraction_preserves_page_marker():
    uploaded = SimpleUploadedFile('rag.pdf', make_pdf('RAG uses retrieval.'))

    extracted = extract_text_from_pdf(uploaded)

    assert extracted == '--- Trang 1 ---\nRAG uses retrieval.'


def test_sanitize_extracted_text_removes_nul_and_unsafe_controls():
    extracted = sanitize_extracted_text('RAG\x00\tTutor\r\nNội dung\x01')

    assert extracted == 'RAG\tTutor\nNội dung'


def test_pdf_extraction_never_returns_nul_characters():
    uploaded = SimpleUploadedFile('nul.pdf', make_pdf('RAG\x00Tutor'))

    extracted = extract_text_from_pdf(uploaded)

    assert '\x00' not in extracted
    assert extracted.endswith('RAGTutor')


def test_empty_pdf_fails_safely():
    uploaded = SimpleUploadedFile('empty.pdf', make_pdf())

    with pytest.raises(PDFIngestionError, match='Không tìm thấy văn bản'):
        extract_text_from_pdf(uploaded)


def test_encrypted_pdf_fails_safely():
    uploaded = SimpleUploadedFile('encrypted.pdf', make_pdf('Private', password='secret'))

    with pytest.raises(PDFIngestionError, match='mã hóa'):
        extract_text_from_pdf(uploaded)


@pytest.mark.django_db
@pytest.mark.parametrize('filename', ['lesson.docx', 'lesson.ppt', 'lesson.pptx'])
def test_upload_rejects_every_non_pdf_target(api_client, teacher_user, owned_course, filename):
    api_client.force_authenticate(teacher_user)

    response = api_client.post(
        '/api/courses/lessons/upload/',
        upload_payload(owned_course, filename=filename, content=b'not a pdf'),
        format='multipart',
    )

    assert response.status_code == 400
    assert 'Chỉ hỗ trợ file PDF' in str(response.data)
    assert Lesson.objects.count() == 0


@pytest.mark.django_db
def test_upload_rejects_spoofed_pdf_before_creating_lesson(
    api_client, teacher_user, owned_course,
):
    api_client.force_authenticate(teacher_user)

    response = api_client.post(
        '/api/courses/lessons/upload/',
        upload_payload(owned_course, content=b'not really a pdf'),
        format='multipart',
    )

    assert response.status_code == 400
    assert 'không phải PDF hợp lệ' in str(response.data)
    assert Lesson.objects.count() == 0


@pytest.mark.django_db
@override_settings(LESSON_PDF_MAX_BYTES=10)
def test_upload_rejects_pdf_over_configured_size(
    api_client, teacher_user, owned_course,
):
    api_client.force_authenticate(teacher_user)

    response = api_client.post(
        '/api/courses/lessons/upload/',
        upload_payload(owned_course),
        format='multipart',
    )

    assert response.status_code == 400
    assert 'vượt quá dung lượng' in str(response.data)
    assert Lesson.objects.count() == 0


@pytest.mark.django_db
def test_other_teacher_is_denied_before_pdf_processing(
    api_client, teacher_user, owned_course,
):
    other_teacher = User.objects.create_user(
        email='other-teacher@example.com',
        username='other-teacher',
        password='Testpass123!',
        role='teacher',
        is_verified=True,
    )
    api_client.force_authenticate(other_teacher)

    with patch('apps.courses.views.process_pdf_lesson') as process:
        response = api_client.post(
            '/api/courses/lessons/upload/',
            upload_payload(owned_course, content=b'%PDF-invalid'),
            format='multipart',
        )

    assert response.status_code == 403
    process.assert_not_called()
    assert Lesson.objects.count() == 0


@pytest.mark.django_db
def test_owner_upload_extracts_and_indexes_pdf(api_client, teacher_user, owned_course):
    api_client.force_authenticate(teacher_user)

    with patch(
        'apps.ai_assistant.rag_services.FastEmbedEmbeddingProvider',
        return_value=FakeEmbeddingProvider(),
    ):
        response = api_client.post(
            '/api/courses/lessons/upload/',
            upload_payload(owned_course),
            format='multipart',
        )

    assert response.status_code == 201
    lesson = Lesson.objects.get(pk=response.data['lesson']['id'])
    source = KnowledgeSource.objects.get(lesson=lesson, is_active=True)
    assert lesson.processing_status == 'completed'
    assert lesson.extracted_text.startswith('--- Trang 1 ---')
    assert source.source_type == 'extracted_text'
    assert source.chunks.exists()
    assert not source.chunks.filter(page_start__isnull=True).exists()
    assert set(source.chunks.values_list('page_start', flat=True)) == {1}
    assert response.data['knowledge_source_id'] == source.id


@pytest.mark.django_db
def test_index_failure_never_activates_partial_pdf_chunks(
    api_client, teacher_user, owned_course,
):
    api_client.force_authenticate(teacher_user)

    with patch(
        'apps.ai_assistant.rag_services.FastEmbedEmbeddingProvider',
        return_value=FakeEmbeddingProvider(error=EmbeddingProviderError('offline')),
    ):
        response = api_client.post(
            '/api/courses/lessons/upload/',
            upload_payload(owned_course),
            format='multipart',
        )

    assert response.status_code == 400
    lesson = Lesson.objects.get(pk=response.data['lesson_id'])
    assert lesson.processing_status == 'failed'
    assert lesson.processing_error == 'Không thể lập chỉ mục nội dung PDF'
    assert not KnowledgeSource.objects.filter(lesson=lesson, is_active=True).exists()


@pytest.mark.django_db
def test_reprocess_unchanged_pdf_is_idempotent(api_client, teacher_user, owned_course):
    api_client.force_authenticate(teacher_user)
    provider = FakeEmbeddingProvider()

    with patch(
        'apps.ai_assistant.rag_services.FastEmbedEmbeddingProvider',
        return_value=provider,
    ):
        upload_response = api_client.post(
            '/api/courses/lessons/upload/',
            upload_payload(owned_course),
            format='multipart',
        )
        lesson_id = upload_response.data['lesson']['id']
        source_id = upload_response.data['knowledge_source_id']
        reprocess_response = api_client.post(
            f'/api/courses/lessons/{lesson_id}/reprocess/',
            format='json',
        )

    assert upload_response.status_code == 201
    assert reprocess_response.status_code == 200
    assert reprocess_response.data['index_created'] is False
    assert reprocess_response.data['knowledge_source_id'] == source_id
    assert KnowledgeSource.objects.filter(lesson_id=lesson_id, is_active=True).count() == 1
