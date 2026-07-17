# Trạng thái dự án Intaaneto

Cập nhật: 2026-07-17. Đây là ảnh chụp trạng thái code đã kiểm tra, không phải danh
sách tính năng dự kiến.

## Đã có

- Django 5 + Django REST Framework, PostgreSQL, JWT và các app `users`,
  `courses`, `exercises`, `ai_assistant`, `forum`, `analytics`.
- React 18 + Vite 7, routing, Zustand, React Query và trang lesson có tab AI.
- Phân quyền course/lesson cơ bản theo learner enrollment, teacher owner và admin.
- Student API không trả `solution_code` và hidden test cases.
- AI generation đi qua provider adapter; lesson chat có scope backend kiểm tra,
  retrieval pgvector, grounded fallback, citation application-owned, history
  giới hạn/khôi phục sau reload và response contract ổn định.
- PDF-only ingestion có bounds/signature/page/text validation, normalization,
  deterministic chunk/version và atomic activation.
- Assessment trắc nghiệm teacher-authored được backend chấm deterministic; pass
  gate progression, weak objective dẫn tới reinforcement và dashboard/report.
- Hai corpus Markdown compile thành 2 course/15 lesson draft; 3 assessment
  blueprint/27 câu được giữ tách khỏi RAG và import ở trạng thái draft.
- Teacher application/admin approval, email verification và teacher login có
  boundary backend; CSV/objective/reinforcement reports chỉ theo course sở hữu.
- SadTalker adapter có consent/bounds/audit; technical GPU smoke đã tạo MP4.
- Docker Compose development cho PostgreSQL, backend, frontend và Adminer.
- Bộ test backend cô lập bằng SQLite; lint/build frontend đã chạy được ở lần kiểm
  tra gần nhất.

## Chưa có hoặc chưa hoàn thiện

- Ingestion/indexing vẫn đồng bộ; chưa có Celery/Redis durable worker, parser
  process isolation, malware scanning hoặc object storage production.
- Chưa có reranker/ANN và multi-lesson holdout/human evaluation đủ để kết luận
  chất lượng RAG hay tác động giáo dục.
- AI dialogue grading chưa ảnh hưởng điểm; baseline tin cậy vẫn là trắc nghiệm
  deterministic do teacher duyệt.
- SadTalker chưa có automatic TTS và chưa có render học liệu bằng portrait/audio
  đã duyệt kèm đánh giá tiếng Việt/lip-sync.
- Frontend chưa có test runner tự động riêng; Docker Compose là development.
- Một số frontend pages vẫn là prototype/placeholder; không nên xem các app model
  và endpoint tồn tại là bằng chứng UI end-to-end đã hoàn tất.

## Ưu tiên thực hiện

1. Teacher review/publish các assessment corpus draft và chạy E2 với response
   cases cùng hai người chấm độc lập.
2. Mở rộng RAG evaluation sang nhiều lesson, tách holdout và human review trước
   khi tune threshold/model.
3. Bổ sung durable background processing và production storage/security.
4. Chạy SadTalker với asset tiếng Việt có quyền sử dụng và ghi rubric tài nguyên,
   lip-sync, artifact; video vẫn là enhancement tùy chọn.

## Tiêu chí không được tuyên bố sớm

Hệ thống chỉ được gọi là RAG hoàn chỉnh khi retrieval dùng dữ liệu đã index,
authorization được áp dụng trước vector ranking, citation thuộc tập chunk đã truy
xuất và câu hỏi thiếu bằng chứng trả fallback. API provider trả lời được không tự
động đồng nghĩa với RAG đã hoạt động.

Xem [SETUP.md](SETUP.md) để chạy dự án và [DOCKER_GUIDE.md](DOCKER_GUIDE.md) để
xử lý container.
