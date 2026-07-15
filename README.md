# Intaaneto — Hệ thống E-learning tích hợp Giảng viên ảo AI

## Tổng quan đề tài

**Tên đề tài:** Nghiên cứu xây dựng hệ thống E-learning trên môi trường web tích
hợp giảng viên ảo dựa trên công nghệ Trí tuệ nhân tạo.

Intaaneto là nền tảng E-learning hướng đến việc tạo ra một môi trường học tập
chủ động. AI đóng vai trò gia sư (AI Tutor), hỗ trợ người học tiếp thu nội dung,
giải đáp thắc mắc và kiểm tra mức độ hiểu bài trước khi chuyển sang nội dung
tiếp theo.

Hệ thống đồng thời hướng đến việc giảm công việc lặp lại của giảng viên trong
khâu tóm tắt học liệu, xây dựng câu hỏi kiểm tra cơ bản và theo dõi kết quả học
tập của người học.

> **Ưu tiên hiện tại:** xây dựng RAG ở backend làm cơ sở tri thức đáng tin cậy
> cho AI Tutor. Các chức năng giọng nói, avatar và video sẽ được tích hợp sau
> khi vòng hỏi đáp và đánh giá dựa trên học liệu hoạt động ổn định.

## Mục tiêu nghiên cứu

- Xây dựng website E-learning có phân quyền giảng viên và người học.
- Quản lý khóa học, bài học, bài tập và tài liệu học thuật.
- Nghiên cứu phương pháp trích xuất nội dung từ PDF, PPT/PPTX và các học liệu
  được giảng viên phê duyệt.
- Xây dựng cơ sở tri thức RAG để AI trả lời dựa trên đúng nội dung bài học và có
  nguồn tham chiếu.
- Xây dựng AI Tutor có khả năng tóm tắt, giải đáp, gợi ý và kiểm tra kiến thức
  qua đối thoại.
- Áp dụng ngưỡng đánh giá để xác định người học đã đủ điều kiện chuyển tiếp nội
  dung hay cần được củng cố kiến thức.
- Tạo nội dung trình bày bằng giọng nói, hình ảnh hoặc avatar/video AI.
- Tổng hợp tiến độ học tập từ kết quả đánh giá của hệ thống.
- Xây dựng tài liệu báo cáo và kết quả đánh giá phục vụ nghiên cứu khoa học.

## Kết quả dự kiến

- Website E-learning có luồng giảng viên quản lý học liệu và người học tham gia
  khóa học.
- Giảng viên ảo có khả năng tóm tắt và trình bày bài học bằng giọng nói, hình ảnh
  hoặc video.
- Chatbot trả lời câu hỏi dựa trên học liệu được cấp quyền, kèm nguồn tham chiếu.
- Hệ thống kiểm tra kiến thức bằng đối thoại AI với tiêu chí đánh giá có thể
  giải thích và kiểm chứng.
- Cơ chế khóa/mở nội dung dựa trên kết quả tiếp thu của người học.
- Báo cáo tiến độ học tập và báo cáo kết quả nghiên cứu khoa học.

## Kiến trúc AI Tutor

RAG là lõi tri thức của AI Tutor, nhưng không phải toàn bộ hệ thống giảng viên
ảo. Luồng cốt lõi được định hướng như sau:

```text
Học liệu do giảng viên cung cấp
  → kiểm tra và trích xuất nội dung
  → chuẩn hóa và chia đoạn (chunking)
  → embedding model
  → PostgreSQL + pgvector

Câu hỏi của người học + phạm vi bài học được cấp quyền
  → truy xuất các đoạn liên quan
  → kiểm tra mức độ đủ bằng chứng
  → response model
  → câu trả lời tiếng Việt + nguồn tham chiếu
  → hỏi kiểm tra/đánh giá
  → lưu kết quả và cập nhật tiến độ
```

### Mô hình triển khai dự kiến

- **Embedding model:** chạy local hoặc trong dịch vụ nội bộ của backend để tạo
  vector cho tài liệu và câu hỏi.
- **Response model:** gọi qua API trực tuyến thông qua một lớp provider độc lập,
  cho phép thử nghiệm hoặc thay đổi nhà cung cấp.
- **Object storage:** Cloudflare R2 hoặc dịch vụ tương đương để lưu PDF/PPTX,
  audio, ảnh và video. Google Drive có thể dùng cho dữ liệu nghiên cứu ban đầu,
  nhưng không thay thế vector database.
- **Vector storage:** PostgreSQL kết hợp pgvector để lưu chunk, embedding,
  metadata nguồn và phạm vi truy cập.
- **Multimedia:** TTS và avatar/lip-sync/video là pipeline phía sau, sử dụng nội
  dung bài học đã được kiểm duyệt.

## Vòng chức năng cốt lõi

Phiên bản nghiên cứu đầu tiên cần chứng minh được một vòng khép kín:

1. Giảng viên tải lên hoặc phê duyệt học liệu.
2. Backend trích xuất, chia đoạn, embedding và lập chỉ mục tài liệu.
3. Người học được cấp quyền đặt câu hỏi theo bài học.
4. AI trả lời dựa trên các đoạn được truy xuất và cung cấp nguồn tham chiếu.
5. AI thực hiện một phiên kiểm tra kiến thức có giới hạn và tiêu chí rõ ràng.
6. Hệ thống lưu kết quả, quyết định chuyển tiếp hoặc yêu cầu ôn tập.
7. Kết quả được dùng trong báo cáo tiến độ và đánh giá nghiên cứu.

## Trạng thái hiện tại

### Đã có trong repository

- Backend Django 5, Django REST Framework và cấu hình PostgreSQL.
- JWT authentication và mô hình người dùng có phân vai trò.
- Các Django app cho users, courses, exercises, AI assistant, forum và analytics.
- Course, Lesson, Exercise, Submission, ChatSession và ChatMessage models.
- API cơ bản cho khóa học, bài học, bài tập và AI chat.
- Frontend React/Vite với luồng đăng nhập, khóa học, bài học và giao diện hỏi AI.
- Các trường dữ liệu cho file bài học, nội dung trích xuất, tóm tắt AI và trạng
  thái xử lý.

### Đang nghiên cứu và chưa hoàn thiện

- Pipeline trích xuất và chuẩn hóa học liệu.
- Chunking, embedding, pgvector và truy xuất theo phạm vi bài học.
- Grounded answer và citation.
- Bộ dữ liệu đánh giá chất lượng RAG.
- Kiểm tra kiến thức bằng hội thoại và progression rule.
- Background processing với Celery/Redis.
- Lưu trữ object trên Cloudflare R2.
- TTS, avatar/lip-sync và tạo video giảng viên ảo.
- Báo cáo tiến độ dựa trên kết quả đánh giá AI.

## Công nghệ

### Đã sử dụng

- **Backend:** Python, Django 5, Django REST Framework.
- **Database:** PostgreSQL 15.
- **Authentication:** JWT với Simple JWT.
- **Frontend:** React 18, Vite, Tailwind CSS, Zustand và React Router.
- **Document libraries:** PyPDF2, python-pptx và Pillow.
- **AI integration hiện có:** OpenAI/Groq ở mức tích hợp ban đầu.
- **Infrastructure:** Docker và Docker Compose.

### Dự kiến cho RAG và giảng viên ảo

- **Vector search:** pgvector.
- **Embedding:** model mã nguồn mở chạy local.
- **Generation:** LLM API có thể cấu hình theo provider.
- **Object storage:** Cloudflare R2 hoặc S3-compatible storage.
- **Background jobs:** Celery và Redis.
- **Voice/video:** TTS kết hợp avatar hoặc lip-sync pipeline.

## Cấu trúc dự án

```text
intaaneto/
├── .ai/                       # Context và skill cho AI agents
│   └── skills/intaaneto-rag/  # Kiến trúc, roadmap và quy tắc RAG
├── backend/
│   ├── config/                # Django settings và URL configuration
│   ├── apps/
│   │   ├── users/             # Người dùng và phân quyền
│   │   ├── courses/           # Khóa học, bài học và học liệu
│   │   ├── exercises/         # Bài tập và bài nộp
│   │   ├── ai_assistant/      # Chat và RAG core
│   │   ├── forum/             # Bài viết và bình luận
│   │   └── analytics/         # Tiến độ và thống kê
│   ├── requirements.txt
│   └── manage.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── store/
│   │   └── utils/
│   ├── package.json
│   └── vite.config.js
├── docs/
├── docker-compose.yml
└── README.md
```

## Lộ trình ưu tiên

1. Ổn định contract chat giữa frontend và backend.
2. Lập chỉ mục được nội dung của một bài học và re-index không trùng dữ liệu.
3. Truy xuất đúng chunk theo quyền truy cập bài học/khóa học.
4. Sinh câu trả lời grounded kèm citation và cơ chế từ chối khi thiếu bằng chứng.
5. Hoàn thiện upload và ingestion PDF/PPTX.
6. Xây dựng hội thoại kiểm tra kiến thức, rubric và progression rule.
7. Đánh giá retrieval, groundedness, citation, độ nhất quán, latency và chi phí.
8. Tích hợp báo cáo tiến độ.
9. Tích hợp TTS, hình ảnh/avatar và video giảng viên ảo.

Chi tiết dành cho AI agents nằm tại
[`.ai/skills/intaaneto-rag/SKILL.md`](.ai/skills/intaaneto-rag/SKILL.md).

## Cài đặt

### Yêu cầu

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Docker và Docker Compose nếu chạy bằng container

### Chạy bằng Docker

```bash
git clone <repository-url>
cd intaaneto

cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

docker-compose up -d
docker-compose exec backend python manage.py createsuperuser
```

Các địa chỉ mặc định:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000/api`
- Django Admin: `http://localhost:8000/admin`
- Adminer: `http://localhost:8888`

### Chạy thủ công

Backend:

```bash
cd backend
python -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows PowerShell
# .\venv\Scripts\Activate.ps1

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Cấu hình môi trường

Ví dụ backend:

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=intaaneto_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

OPENAI_API_KEY=your-openai-api-key
GROQ_API_KEY=your-groq-api-key
```

Ví dụ frontend:

```env
VITE_API_URL=http://localhost:8000/api
```

Không commit API key, secret hoặc file `.env` thật vào repository.

## API hiện có

### Authentication

- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `POST /api/auth/logout/`
- `GET /api/auth/users/me/`

### Courses

- `GET /api/courses/`
- `GET /api/courses/{id}/`
- `POST /api/courses/{id}/enroll/`

### AI Assistant

- `POST /api/ai/chat/send_message/`
- `POST /api/ai/chat/explain_code/`
- `POST /api/ai/chat/get_hint/`

Các endpoint trên là API hiện có; chúng chưa đồng nghĩa với việc pipeline RAG
đã hoàn thiện.

## Kiểm thử

Backend:

```bash
cd backend
pytest
```

Frontend chưa có test runner riêng được cấu hình trong repository. Khi bổ sung
test frontend, cập nhật lại hướng dẫn này cùng `frontend/package.json`.

## Tài liệu

- [Database schema](docs/database-schema.md)
- [API documentation](docs/api-documentation.md)
- [Roadmap](docs/ROADMAP.md)
- [RAG architecture](.ai/skills/intaaneto-rag/references/architecture.md)
- [RAG delivery plan](.ai/skills/intaaneto-rag/references/delivery-plan.md)
- [RAG quality and safety](.ai/skills/intaaneto-rag/references/quality-and-safety.md)
- [Web and RAG security skill](.ai/skills/intaaneto-web-security/SKILL.md)

## Thành viên

- **Nguyễn Thái Tuấn** — N23DCPT054
- **Phùng Anh Lực** — N23DCPT033

## License

Xem [LICENSE](LICENSE).

## Liên hệ

n23dcpt054@student.ptithcm.edu.vn
