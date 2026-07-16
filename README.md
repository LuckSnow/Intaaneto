# Intaaneto — E-learning tích hợp AI Tutor dựa trên RAG

Đề tài nghiên cứu xây dựng một website E-learning nơi học viên học theo lesson,
hỏi AI Tutor trong phạm vi học liệu được cấp quyền, làm bài đánh giá trước khi
chuyển tiếp và theo dõi tiến độ. PostgreSQL + pgvector lưu kho tri thức; quyền
truy cập, citation, điểm và progression đều do backend kiểm soát.

## Phạm vi đã triển khai

| Lát cắt | Trạng thái có bằng chứng |
| --- | --- |
| Phân quyền | Đăng ký learner, xác thực email, JWT rotation/logout, teacher login, learner xin nâng role và admin duyệt |
| Quản lý khóa học | Teacher tạo course draft, upload PDF thành lesson, publish course khi có lesson usable |
| Kho tri thức | PDF-only extraction có bounds, deterministic normalization/chunking, FastEmbed local, PostgreSQL/pgvector, source versioning và atomic activation |
| AI Tutor | Retrieval trong lesson đã authorize, OpenAI/Gemini generation, fallback khi thiếu bằng chứng, citation do ứng dụng tạo |
| Đánh giá | Teacher biên soạn trắc nghiệm, backend chấm deterministic, immutable attempt, weak objectives và RAG reinforcement có audit event tối thiểu |
| Tiến độ | Lesson completion, mastery/progress, roster/CSV, objective distribution và paired reinforcement outcome theo course sở hữu |
| Cộng đồng | Forum, lesson comments và reviews với ownership/role boundary |
| Video ảo | Adapter SadTalker local có consent/bounds/timeout/audit; technical GPU smoke đã tạo MP4, còn thiếu render học liệu với asset được duyệt và đánh giá chất lượng |

Luồng tích hợp chính đã có regression test:

```text
Teacher tạo course draft
  → upload/index PDF
  → biên soạn và publish assessment
  → publish course
  → learner enroll
  → học + hỏi RAG Tutor
  → backend chấm assessment
  → progression/mastery/report
```

## Không được coi là đã hoàn thiện

- AI dialogue grading ảnh hưởng điểm hoặc progression. Baseline hiện tại là
  trắc nghiệm teacher-authored, chấm deterministic.
- Tự động tạo/tóm tắt assessment từ PDF.
- TTS tự động và bằng chứng chất lượng SadTalker bằng portrait/audio học liệu đã
  được duyệt. Technical smoke trên GPU đã pass nhưng không thay thế bước này.
- Celery/Redis durable ingestion, parser process isolation, malware scanning và
  object storage production.
- Kết luận về độ chính xác/chất lượng sư phạm của RAG. Retrieval mới có baseline
  nhỏ; grounded-answer harness chưa có live-provider/human-review baseline.
- Cấu hình Docker Compose hiện tại là development, không phải production.

## Kiến trúc cốt lõi

```text
PDF đã được teacher-owner phê duyệt
  → kiểm tra signature/size/pages/text
  → normalize + chunk deterministic
  → local embedding
  → KnowledgeSource version + KnowledgeChunk/pgvector

Learner/teacher đã authorize + lesson_id + câu hỏi
  → lọc đúng active ready source
  → exact cosine retrieval trong source đó
  → weak-evidence fallback hoặc bounded generation
  → citation từ selected chunks
```

RAG similarity không được dùng làm điểm học viên. Assessment/progression dùng dữ
liệu server-owned riêng.

## Công nghệ

- Backend: Python 3.11, Django 5, Django REST Framework, Simple JWT.
- Database: PostgreSQL 15 + pgvector.
- Embedding: FastEmbed ONNX local, model multilingual cấu hình bằng environment.
- Generation: OpenAI hoặc Gemini qua provider adapter.
- Frontend: React 18, Vite, Tailwind CSS, Zustand, React Router.
- Email: Django email backend; Mailjet qua Anymail là cấu hình tùy chọn.
- Video PoC: SadTalker self-hosted, không dùng API key.
- Runtime development: Docker Compose.

## Chạy development bằng Docker

Yêu cầu Docker và Docker Compose:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose up -d --build
docker compose exec backend python manage.py createsuperuser
```

Các service mặc định:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/api
- Swagger: http://localhost:8000/api/docs/
- Django Admin: http://localhost:8000/admin/
- Adminer: http://localhost:8888

Migrations được backend container áp dụng khi startup. Xem hướng dẫn đầy đủ và
luồng kiểm tra database/admin/frontend tại
[docs/MANUAL_TESTING_GUIDE.md](docs/MANUAL_TESTING_GUIDE.md).

## Dữ liệu demo và corpus

Không có mật khẩu demo cố định trong repository. Có thể đặt mật khẩu local trong
file `.env` bị ignore rồi chạy:

```bash
docker compose exec backend python manage.py seed_demo_data
```

Hai tài liệu `docs/computer-networks.md` và `docs/web-programming.md` có thể được
compile thành 2 course/15 lesson draft bằng importer đã kiểm thử. Import không tự
publish, index, tạo assessment hoặc answer key; xem [docs/SETUP.md](docs/SETUP.md).

## Cấu hình AI

Chọn một generation provider trong `backend/.env`:

```env
AI_GENERATION_PROVIDER=openai
OPENAI_API_KEY=
AI_GENERATION_MODEL=gpt-4o-mini

# Hoặc Gemini
GEMINI_API_KEY=
GEMINI_GENERATION_MODEL=gemini-3.1-flash-lite
```

Embedding RAG chạy local và không cần API key. SadTalker self-host cũng không
cần API key; nó cần repository/checkpoint/runtime Python, FFmpeg và phần cứng phù
hợp. Không commit `.env`, key, raw prompt chứa dữ liệu riêng tư hoặc output thử
nghiệm nhạy cảm.

## Kiểm thử và bằng chứng hiện tại

```bash
docker compose exec backend pytest -q
docker compose exec backend python manage.py check
docker compose exec backend python manage.py makemigrations --check --dry-run
docker compose exec frontend npm run lint
docker compose exec frontend npm run build
```

Baseline ngày 2026-07-17: 176 backend tests pass; Django check và migration drift
check pass; frontend lint/build pass; `npm audit` báo 0 lỗ hổng đã biết. Bundle
JavaScript chính còn khoảng 461 kB và Google Auth được tách thành các chunk tải
khi cần. Build vẫn cảnh báo Browserslist data cũ. Frontend chưa có test runner
tự động riêng.

## Tài liệu chính

- [Hướng dẫn kiểm thử thủ công](docs/MANUAL_TESTING_GUIDE.md)
- [API core](docs/api-documentation.md)
- [Database schema](docs/database-schema.md)
- [Grounded-answer evaluation](docs/RAG_GROUNDED_ANSWER_EVALUATION.md)
- [Protocol đánh giá assessment/progression](docs/ASSESSMENT_EVALUATION_PROTOCOL.md)
- [Retrieval baseline v1](docs/RAG_RETRIEVAL_BASELINE_V1.md)
- [SadTalker PoC](docs/SADTALKER_POC.md)
- [Bản thảo báo cáo nghiên cứu](docs/RESEARCH_REPORT_DRAFT.md)
- [Living current state](.ai/skills/intaaneto-rag/references/current-state.md)

## Thành viên

- Nguyễn Thái Tuấn — N23DCPT054
- Phùng Anh Lực — N23DCPT033

## License

Xem [LICENSE](LICENSE).
