"""
AI Processing Services for Lessons
Legacy multimedia helpers plus the PDF-only RAG ingestion service.
"""

import io
import time
import logging
import unicodedata
import requests
from django.conf import settings
from django.core.exceptions import PermissionDenied

from apps.ai_assistant.rag_services import LessonIndexingError, index_lesson

logger = logging.getLogger(__name__)


class PDFIngestionError(Exception):
    """Safe, user-facing failure from the bounded PDF ingestion pipeline."""


# ═══════════════════════════════════════════════════════════
#  1. DOCUMENT TEXT EXTRACTION (PDF ONLY)
# ═══════════════════════════════════════════════════════════

def _read_bounded_pdf(file):
    from PyPDF2 import PdfReader

    data = file.read(settings.LESSON_PDF_MAX_BYTES + 1)
    if len(data) > settings.LESSON_PDF_MAX_BYTES:
        raise PDFIngestionError('File PDF vượt quá dung lượng cho phép')
    if not data.startswith(b'%PDF-'):
        raise PDFIngestionError('Nội dung tải lên không phải PDF hợp lệ')
    return PdfReader(io.BytesIO(data), strict=False)


def sanitize_extracted_text(text: str) -> str:
    """Normalize parser output and remove database-unsafe control characters."""

    normalized = unicodedata.normalize('NFKC', text or '')
    normalized = normalized.replace('\r\n', '\n').replace('\r', '\n')
    return ''.join(
        character
        for character in normalized
        if character in ('\n', '\t')
        or unicodedata.category(character) not in ('Cc', 'Cs')
    )


def _extract_pdf_pages(reader):
    if reader.is_encrypted:
        raise PDFIngestionError('Chưa hỗ trợ PDF được mã hóa hoặc đặt mật khẩu')
    if not reader.pages:
        raise PDFIngestionError('PDF không có trang nội dung')
    if len(reader.pages) > settings.LESSON_PDF_MAX_PAGES:
        raise PDFIngestionError('PDF vượt quá số trang cho phép')

    pages = []
    extracted_chars = 0
    for page_number, page in enumerate(reader.pages, start=1):
        text = sanitize_extracted_text(page.extract_text()).strip()
        if not text:
            continue
        extracted_chars += len(text)
        if extracted_chars > settings.LESSON_PDF_MAX_EXTRACTED_CHARS:
            raise PDFIngestionError('Nội dung PDF vượt quá giới hạn xử lý')
        pages.append(f'--- Trang {page_number} ---\n{text}')
    if not pages:
        raise PDFIngestionError('Không tìm thấy văn bản có thể trích xuất trong PDF')
    return '\n\n'.join(pages)


def extract_text_from_pdf(file) -> str:
    """Extract bounded text while retaining stable, human-readable page markers."""
    from PyPDF2.errors import PdfReadError

    try:
        file.seek(0)
        return _extract_pdf_pages(_read_bounded_pdf(file))
    except PDFIngestionError:
        raise
    except (PdfReadError, OSError, ValueError, TypeError, KeyError) as exc:
        raise PDFIngestionError('Không thể đọc file PDF') from exc
    finally:
        file.seek(0)


def extract_text(file, filename: str) -> str:
    """Extract text from the only supported lesson document format."""
    ext = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''
    
    if ext == 'pdf':
        return extract_text_from_pdf(file)
    raise PDFIngestionError('Chỉ hỗ trợ file PDF')


def process_pdf_lesson(*, actor, lesson, embedding_provider=None):
    """Authorize, extract, and synchronously index one uploaded lesson PDF."""

    if not getattr(actor, 'is_authenticated', False):
        raise PermissionDenied('Bạn không có quyền xử lý bài học này.')
    if actor.role != 'admin' and (
        actor.role != 'teacher' or lesson.course.teacher_id != actor.id
    ):
        raise PermissionDenied('Bạn không có quyền xử lý bài học này.')

    try:
        if not lesson.uploaded_file or not lesson.uploaded_file.name.lower().endswith('.pdf'):
            raise PDFIngestionError('Bài học không có file PDF hợp lệ')

        lesson.processing_status = 'extracting'
        lesson.processing_error = ''
        lesson.save(update_fields=['processing_status', 'processing_error'])

        extracted = extract_text_from_pdf(lesson.uploaded_file)
        lesson.extracted_text = extracted
        lesson.save(update_fields=['extracted_text'])

        source, created = index_lesson(
            actor=actor,
            lesson_id=lesson.id,
            provider=embedding_provider,
        )
        lesson.processing_status = 'completed'
        lesson.processing_error = ''
        lesson.save(update_fields=['processing_status', 'processing_error'])
        return source, created
    except PermissionDenied:
        raise
    except PDFIngestionError as exc:
        safe_error = str(exc)
    except LessonIndexingError:
        safe_error = 'Không thể lập chỉ mục nội dung PDF'
    except Exception:
        logger.exception('Unexpected PDF ingestion failure for lesson %s', lesson.id)
        safe_error = 'Không thể xử lý file PDF'

    lesson.processing_status = 'failed'
    lesson.processing_error = safe_error
    lesson.save(update_fields=['processing_status', 'processing_error'])
    raise PDFIngestionError(safe_error)


# ═══════════════════════════════════════════════════════════
#  2. AI SUMMARIZATION (Groq - Llama)
# ═══════════════════════════════════════════════════════════

def summarize_with_llama(extracted_text: str, lesson_title: str = '') -> str:
    """
    Use Groq (Llama) to create a lecture script from extracted document text.
    Target: 5-7 minute spoken lecture (~800-1100 words Vietnamese).
    """
    from groq import Groq
    
    api_key = settings.GROQ_API_KEY
    if not api_key:
        raise ValueError("GROQ_API_KEY is not configured. Please set it in .env")
    
    client = Groq(api_key=api_key)
    
    prompt = f"""Bạn là một giảng viên chuyên nghiệp. Hãy tạo một bài giảng từ nội dung tài liệu dưới đây.

YÊU CẦU:
- Bài giảng khoảng 800-1100 từ (tương đương 5-7 phút nói)
- Viết bằng tiếng Việt tự nhiên, dễ hiểu
- Giọng văn thân thiện, gần gũi như đang giảng bài trực tiếp
- Cấu trúc rõ ràng: mở đầu chào hỏi → giới thiệu chủ đề → nội dung chính → tóm tắt → kết thúc
- KHÔNG dùng markdown, bullet points, hay ký hiệu đặc biệt
- Chỉ viết văn xuôi liền mạch, vì nội dung này sẽ được đọc thành giọng nói
- Giải thích các khái niệm kỹ thuật một cách đơn giản
- Đưa ra ví dụ thực tế khi có thể

TIÊU ĐỀ BÀI GIẢNG: {lesson_title}

NỘI DUNG TÀI LIỆU:
{extracted_text[:15000]}

Hãy viết bài giảng:"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "Bạn là một giảng viên chuyên nghiệp, giỏi tóm tắt và giảng bài bằng tiếng Việt."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=4096,
    )
    return response.choices[0].message.content.strip()


# ═══════════════════════════════════════════════════════════
#  3. D-ID VIDEO GENERATION
# ═══════════════════════════════════════════════════════════

DID_API_BASE = "https://api.d-id.com"

# Default presenter image (D-ID public presenter)
DEFAULT_PRESENTER_IMAGE = "https://d-id-public-bucket.s3.us-west-2.amazonaws.com/alice.jpg"


def _get_did_headers():
    """Get D-ID API headers."""
    api_key = settings.DID_API_KEY
    if not api_key:
        raise ValueError("DID_API_KEY is not configured. Please set it in .env")
    return {
        "Authorization": f"Basic {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def create_did_talk(script_text: str, presenter_image: str = None, max_retries: int = 3) -> dict:
    """
    Create a D-ID talk (AI video) from script text.
    Returns: { 'id': talk_id, 'status': 'created' }
    Retries on timeout/5xx errors.
    """
    headers = _get_did_headers()
    
    # Truncate script — D-ID free tier has ~1500 char limit for text input
    truncated = script_text[:1500]
    
    payload = {
        "source_url": presenter_image or DEFAULT_PRESENTER_IMAGE,
        "script": {
            "type": "text",
            "input": truncated,
            "provider": {
                "type": "microsoft",
                "voice_id": "vi-VN-HoaiMyNeural",  # Vietnamese female voice
            },
        },
        "config": {
            "fluent": True,
            "pad_audio": 0.5,
        },
    }
    
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"D-ID create talk attempt {attempt}/{max_retries} ({len(truncated)} chars)")
            response = requests.post(
                f"{DID_API_BASE}/talks",
                json=payload,
                headers=headers,
                timeout=120,
            )
            
            if response.status_code in (200, 201):
                data = response.json()
                logger.info(f"D-ID talk created: {data.get('id')}")
                return data
            elif response.status_code in (429, 502, 503, 504):
                # Retryable errors
                last_error = f"D-ID API error {response.status_code}: {response.text[:200]}"
                logger.warning(f"Attempt {attempt} failed (retryable): {last_error}")
                time.sleep(10 * attempt)  # backoff: 10s, 20s, 30s
                continue
            else:
                error_msg = f"D-ID API error {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
        except requests.exceptions.Timeout:
            last_error = f"D-ID API timeout on attempt {attempt}"
            logger.warning(last_error)
            time.sleep(10 * attempt)
            continue
        except requests.exceptions.ConnectionError as e:
            last_error = f"D-ID connection error on attempt {attempt}: {e}"
            logger.warning(last_error)
            time.sleep(10 * attempt)
            continue
    
    raise Exception(f"D-ID API failed after {max_retries} attempts. Last error: {last_error}")


def get_did_talk_status(talk_id: str) -> dict:
    """
    Poll D-ID talk status.
    Returns: { 'status': 'done'|'started'|'created'|'error', 'result_url': '...' }
    """
    headers = _get_did_headers()
    
    response = requests.get(
        f"{DID_API_BASE}/talks/{talk_id}",
        headers=headers,
        timeout=30,
    )
    
    if response.status_code == 200:
        data = response.json()
        return {
            'status': data.get('status', 'unknown'),
            'result_url': data.get('result_url', ''),
            'error': data.get('error', {}),
            'duration': data.get('duration', 0),
        }
    else:
        raise Exception(f"D-ID poll error {response.status_code}: {response.text}")


def wait_for_did_talk(talk_id: str, max_wait: int = 600, interval: int = 10) -> dict:
    """
    Wait for D-ID talk to complete (synchronous polling).
    max_wait: maximum seconds to wait (default 10 minutes)
    """
    elapsed = 0
    while elapsed < max_wait:
        result = get_did_talk_status(talk_id)
        status = result.get('status', '')
        
        if status == 'done':
            logger.info(f"D-ID talk {talk_id} completed: {result.get('result_url')}")
            return result
        elif status == 'error':
            error_detail = result.get('error', {})
            raise Exception(f"D-ID talk failed: {error_detail}")
        
        logger.info(f"D-ID talk {talk_id} status: {status}, waiting {interval}s...")
        time.sleep(interval)
        elapsed += interval
    
    raise TimeoutError(f"D-ID talk {talk_id} did not complete within {max_wait}s")


# ═══════════════════════════════════════════════════════════
#  4. FULL PROCESSING PIPELINE
# ═══════════════════════════════════════════════════════════

def process_lesson(lesson) -> None:
    """
    Full pipeline: Extract text → Summarize → Generate AI video
    Updates the lesson instance at each step.
    """
    try:
        # Step 1: Extract text
        lesson.processing_status = 'extracting'
        lesson.save(update_fields=['processing_status'])
        
        if not lesson.uploaded_file:
            raise ValueError("No file uploaded for this lesson")
        
        filename = lesson.uploaded_file.name
        extracted = extract_text(lesson.uploaded_file, filename)
        
        if not extracted.strip():
            raise ValueError("Could not extract any text from the uploaded file")
        
        lesson.extracted_text = extracted
        lesson.save(update_fields=['extracted_text'])
        logger.info(f"Lesson {lesson.id}: Extracted {len(extracted)} chars")
        
        # Step 2: Summarize with Llama
        lesson.processing_status = 'summarizing'
        lesson.save(update_fields=['processing_status'])
        
        summary = summarize_with_llama(extracted, lesson.title)
        lesson.ai_summary = summary
        lesson.save(update_fields=['ai_summary'])
        logger.info(f"Lesson {lesson.id}: Summary generated ({len(summary)} chars)")
        
        # Step 3: Generate D-ID video
        lesson.processing_status = 'generating_video'
        lesson.save(update_fields=['processing_status'])
        
        talk_result = create_did_talk(summary)
        talk_id = talk_result.get('id')
        lesson.ai_video_id = talk_id
        lesson.save(update_fields=['ai_video_id'])
        
        # Step 4: Wait for video completion
        final_result = wait_for_did_talk(talk_id)
        
        lesson.ai_video_url = final_result.get('result_url', '')
        lesson.processing_status = 'completed'
        lesson.lesson_type = 'video'
        lesson.duration_minutes = max(1, int(final_result.get('duration', 300) / 60))
        lesson.save(update_fields=['ai_video_url', 'processing_status', 'lesson_type', 'duration_minutes'])
        
        logger.info(f"Lesson {lesson.id}: AI video ready at {lesson.ai_video_url}")
        
    except Exception as e:
        lesson.processing_status = 'failed'
        lesson.processing_error = str(e)
        lesson.save(update_fields=['processing_status', 'processing_error'])
        logger.error(f"Lesson {lesson.id} processing failed: {e}")
        raise
