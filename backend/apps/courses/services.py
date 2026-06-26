"""
AI Processing Services for Lessons
Workflow: Upload PDF/PPT → Extract text → Llama summarize → D-ID generate video
"""

import io
import time
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
#  1. DOCUMENT TEXT EXTRACTION (PDF / PPT)
# ═══════════════════════════════════════════════════════════

def extract_text_from_pdf(file) -> str:
    """Extract text from a PDF file."""
    from PyPDF2 import PdfReader
    
    file.seek(0)
    reader = PdfReader(io.BytesIO(file.read()))
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            pages.append(f"--- Trang {i+1} ---\n{text.strip()}")
    return "\n\n".join(pages)


def extract_text_from_pptx(file) -> str:
    """Extract text from a PowerPoint (.pptx) file."""
    from pptx import Presentation
    
    file.seek(0)
    prs = Presentation(io.BytesIO(file.read()))
    slides = []
    for i, slide in enumerate(prs.slides):
        texts = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    text = para.text.strip()
                    if text:
                        texts.append(text)
        if texts:
            slides.append(f"--- Slide {i+1} ---\n" + "\n".join(texts))
    return "\n\n".join(slides)


def extract_text(file, filename: str) -> str:
    """Extract text from uploaded file based on extension."""
    ext = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''
    
    if ext == 'pdf':
        return extract_text_from_pdf(file)
    elif ext in ('pptx', 'ppt'):
        return extract_text_from_pptx(file)
    else:
        raise ValueError(f"Unsupported file type: .{ext}. Only PDF and PPT/PPTX are supported.")


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
