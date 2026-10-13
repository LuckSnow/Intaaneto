# Hướng dẫn Thiết lập Supabase, pgvector và Hạ tầng Cloud cho Nghiên cứu Khoa học

Tài liệu này hướng dẫn chi tiết cách đưa Cơ sở dữ liệu và Vector Store lên **Supabase**, kết hợp kho lưu trữ tài liệu **Cloudflare R2**, chia sẻ môi trường `.env` giữa các thành viên nghiên cứu, và lộ trình đưa toàn bộ hệ thống Intaaneto lên Cloud (Cloud-Native).

---

## 1. Supabase có hỗ trợ pgvector không?

**CÓ, Supabase hỗ trợ pgvector mặc định và rất mạnh mẽ.**
- Toàn bộ cơ sở dữ liệu PostgreSQL trên Supabase đều đi kèm extension `vector`.
- Mã nguồn Intaaneto trong migration [`backend/apps/ai_assistant/migrations/0003_knowledgesource_knowledgechunk_and_more.py`](file:///home/luc/projects2/Intaaneto/backend/apps/ai_assistant/migrations/0003_knowledgesource_knowledgechunk_and_more.py) đã tích hợp sẵn lệnh:
  ```python
  def enable_vector_extension(apps, schema_editor):
      if schema_editor.connection.vendor == "postgresql":
          schema_editor.execute("CREATE EXTENSION IF NOT EXISTS vector")
  ```
- Khi chạy lệnh `python manage.py migrate`, extension `vector` sẽ được tự động kích hoạt trên Supabase. Trường `VectorField` (chứa embedding 384 chiều từ `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`) và hàm tính toán khoảng cách vector `CosineDistance` hoạt động hoàn toàn tương thích.

---

## 2. Khi tạo Project trên Supabase có cần bật "Auto RLS" không?

> [!IMPORTANT]
> **KHUYẾN NGHỊ: KHÔNG CẦN (NÊN TẮT / UNCHECK)** tùy chọn tự động bật Row Level Security (RLS) đối với các bảng của Django, hoặc giữ nguyên mặc định không can thiệp.

### Lý do:
1. **Kiến trúc của Django ORM:**
   - Django kết nối với database qua quyền người dùng sở hữu cơ sở dữ liệu (`postgres`). Mọi quyền kiểm soát truy cập (Access Control), phân quyền Học viên / Giảng viên / Quản trị viên, và giới hạn phạm vi truy vấn RAG (`lesson_scope`, `course_scope`) đều đã được thực thi và kiểm duyệt chặt chẽ ở tầng **Backend Application Layer** (thông qua Django Permissions, Serializers và Service Querysets).
2. **Tránh lỗi phân quyền không mong muốn:**
   - Nếu Supabase tự động bật RLS trên các bảng do Django tạo ra mà không có chính sách (Policy) tương ứng cho từng vai trò trên Supabase, các truy vấn ngoài backend (hoặc direct queries) có thể bị chặn hoặc trả về dữ liệu rỗng.
   - Do đó, hãy để Django toàn quyền quản lý schema và phân quyền truy cập.

---

## 3. Kiến trúc Kho dữ liệu chung cho Nhóm Nghiên cứu (Shared Research Repository)

Để hai hoặc nhiều thành viên cùng phát triển và chia sẻ kho tài liệu tri thức khoa học, hệ thống tách bạch 2 lớp lưu trữ:

```
[Máy của Thành viên A]    \
                           ===> [Supabase Cloud: PostgreSQL + pgvector]
[Máy của Thành viên B]    /     (Bảng dữ liệu, Users, Lessons, Chunks, Embeddings, Chat)
                           \
                           ===> [Cloudflare R2: S3 Object Storage]
                                (Kho file PDF gốc, Sách/Giáo trình, Media, Video)
```

1. **Lớp Dữ liệu Quan hệ & Vector (Supabase):**
   - Lưu trữ danh mục Khóa học, Bài học, Nội dung bài giảng, các đoạn văn bản phân mảnh (Chunks), Vector Embeddings (384 chiều), và Phiên hỏi đáp AI Tutor.
   - Bất kỳ thành viên nào index tài liệu thì dữ liệu vector đều đồng bộ tức thì lên Supabase.
2. **Lớp Lưu trữ Tài liệu Gốc (Cloudflare R2):**
   - Nếu lưu file trên ổ đĩa cục bộ (`media/`), khi bạn A upload PDF thì chỉ máy bạn A có file, máy bạn B truy cập sẽ bị lỗi 404.
   - Intaaneto đã tích hợp sẵn Cloudflare R2 (`STORAGE_BACKEND=r2`). File PDF được lưu trữ tập trung trên đám mây, cả 2 bạn đều có thể tải, đọc và xem trực tiếp từ bất kỳ đâu.

---

## 4. Các bước cài đặt chi tiết

### Bước 1: Tạo Project trên Supabase
1. Đăng ký/Đăng nhập tại [supabase.com](https://supabase.com).
2. Nhấn **New Project**:
   - **Name**: `intaaneto-dev` (hoặc tên đề tài).
   - **Database Password**: Đặt mật khẩu an toàn và lưu lại.
   - **Region**: Chọn **Singapore (`ap-southeast-1`)** hoặc **Tokyo (`ap-northeast-1`)** để đạt tốc độ truy vấn nhanh nhất từ Việt Nam.
3. Khi project tạo xong:
   - Vào **Project Settings** (biểu tượng bánh răng) -> **Database**.
   - Cuộn xuống phần **Connection parameters**:
     - **Host**: `db.<project-ref>.supabase.co`
     - **Database name**: `postgres`
     - **Port**: `5432`
     - **User**: `postgres`
   - *(Mẹo mạng IPv4: Nếu mạng của bạn không kết nối được qua Direct Connection, hãy dùng **Connection Pooling** với Port `5432` hoặc `6543`, Host `aws-0-ap-southeast-1.pooler.supabase.com`, User `postgres.<project-ref>`)*.

### Bước 2: Cấu hình `backend/.env`
Mở file [`backend/.env`](file:///home/luc/projects2/Intaaneto/backend/.env) trên máy của bạn và cập nhật:

```env
# ----------------------------------------------------
# DATABASE: SUPABASE POSTGRESQL + PGVECTOR
# ----------------------------------------------------
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=<Mật_khẩu_Supabase_của_bạn>
DB_HOST=db.<project-ref>.supabase.co
DB_PORT=5432
DB_SSLMODE=require

# ----------------------------------------------------
# KHO TÀI LIỆU CHUNG: CLOUDFLARE R2 OBJECT STORAGE
# ----------------------------------------------------
STORAGE_BACKEND=r2
R2_ACCOUNT_ID=43fc77fe2e78e68fbd9c41f5851f86b8
R2_BUCKET_NAME=intaaneto-dev
R2_ACCESS_KEY_ID=970c2da8d8b782a7ce5e7138963115b1
R2_SECRET_ACCESS_KEY=29397ea24786b606b18323ceb435fb285afb47dac376063e134f2adedfedbd9c
R2_ENDPOINT_URL=https://43fc77fe2e78e68fbd9c41f5851f86b8.r2.cloudflarestorage.com
R2_REGION=auto

# ----------------------------------------------------
# AI TUTOR PROVIDER
# ----------------------------------------------------
AI_GENERATION_PROVIDER=gemini
GEMINI_API_KEY=<Your_Gemini_API_Key>
GEMINI_GENERATION_MODEL=gemini-3.1-flash-lite
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/

# Cấu hình RAG Embedding cục bộ (0đ, 384 dimensions)
RAG_EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
RAG_EMBEDDING_REVISION=fastembed-0.8.0-mean-pooling
RAG_EMBEDDING_DIMENSION=384
```

### Bước 3: Chạy Database Migration
Mở terminal tại thư mục `backend/` và thực thi:
```bash
# Kích hoạt môi trường ảo
source venv/bin/activate

# Chạy migrations lên Supabase
python manage.py migrate
```

Tạo tài khoản quản trị viên / giảng viên đầu tiên:
```bash
python manage.py createsuperuser
# Hoặc nạp dữ liệu mẫu bài giảng:
# python manage.py seed_demo_data
```

### Bước 4: Chia sẻ cho thành viên cùng nghiên cứu
1. Gửi file `backend/.env` cho bạn của bạn qua kênh liên lạc riêng an toàn.
2. Bạn của bạn tải mã nguồn từ Git về, dán file `.env` vào thư mục `backend/` và khởi động:
   - Backend: `python manage.py runserver`
   - Frontend: `npm run dev`
   - Celery Worker (xử lý tài liệu PDF & RAG Indexing): `celery -A config worker -l info`
3. Lúc này, cả hai máy đều đọc và ghi chung vào một cơ sở dữ liệu Supabase và kho tài liệu Cloudflare R2.

---

## 5. Phân tích: Đưa toàn bộ hệ thống lên Cloud (Cloud-Native Matrix)

Để phục vụ báo cáo khoa học và triển khai thực tế trên Internet mà không tốn chi phí hạ tầng, toàn bộ các thành phần của Intaaneto có thể được đám mây hóa theo bảng sau:

| Thành phần | Công nghệ hiện tại | Dịch vụ Cloud đề xuất | Gói chi phí | Đánh giá & Khả năng đáp ứng |
| :--- | :--- | :--- | :--- | :--- |
| **Database & Vector DB** | PostgreSQL + pgvector | **Supabase** | Miễn phí (500MB) | Sẵn sàng 100%, hỗ trợ pgvector native, UI quản trị trực quan. |
| **Kho tài liệu (Object Storage)** | Local `media/` | **Cloudflare R2** | Miễn phí (10GB) | Đã code sẵn tích hợp, chuẩn S3, **0đ phí egress bandwidth**. |
| **AI LLM Generator** | Gemini / OpenAI | **Google AI Studio / OpenAI** | Free / Pay-as-you-go | Đã tích hợp sẵn cho RAG tiếng Việt, sinh bài tập trắc nghiệm, tóm tắt. |
| **AI Embeddings** | `fastembed` (MiniLM) | Local ONNX hoặc **Cloud Embedding API** | Miễn phí | Hiện chạy FastEmbed ONNX trên CPU rất nhanh và không tốn chi phí API. |
| **Task Queue / Broker** | Local Redis | **Upstash Redis** | Miễn phí (10k cmds/ngày) | Serverless Redis, giúp Celery worker của cả 2 bạn cùng nhận 1 hàng đợi chung. |
| **Frontend Web App** | React + Vite | **Vercel** / **Cloudflare Pages** | Miễn phí | Tự động build từ Git repo (CI/CD), CDN toàn cầu, tự cấp HTTPS. |
| **Backend REST API** | Django DRF | **Render.com** / **Railway** / **Fly.io** | Free / Hobby Tier | Triển khai qua Dockerfile hoặc Python environment, cấu hình env trực tiếp. |
| **Authentication** | Firebase / JWT | **Firebase Auth** | Miễn phí | Đã cấu hình Google OAuth Sign-in (`intaaneto-e2f0f`). |
| **Email Service** | Mailjet via Anymail | **Mailjet** | Miễn phí (200 emails/ngày) | Đã cấu hình sẵn trong mã nguồn để gửi mail kích hoạt, thông báo. |

---

## 6. Lưu ý an toàn thông tin (Security Checklist)

Căn cứ theo tiêu chuẩn bảo mật của dự án (`.ai/skills/intaaneto-web-security`):
1. **Tuyệt đối không commit file `.env` lên GitHub/GitLab.** File `.gitignore` đã chặn file này, hãy giữ nguyên quy tắc.
2. **Chia sẻ khóa an toàn:** Chia sẻ nội dung `.env` qua kênh mã hóa đầu cuối (Signal, tin nhắn bảo mật hoặc file nén có mật khẩu).
3. **Phân quyền người dùng:** Không cấp quyền `is_staff` / `is_superuser` tùy tiện; sử dụng đúng vai trò Teacher hoặc Student khi thử nghiệm chức năng đánh giá và RAG.
