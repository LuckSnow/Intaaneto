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
- Assessment authoring đề xuất 5/10/15 câu theo độ lớn source, cho teacher chọn
  tối đa 20 và sinh theo batch 5 câu trước khi lưu một draft để review/publish.
- SadTalker adapter có consent/bounds/audit; technical GPU smoke đã tạo MP4.
- Teacher web flow có seam video slide local dùng Piper/Pillow/FFmpeg, phụ đề
  đóng vào slide và ảnh AI Tutor cố định; không cần API key/GPU. Contract đã có
  test, nhưng model chưa được tải hoặc live-benchmark trước license review.
- Docker Compose development cho PostgreSQL, Redis, backend, non-root Celery
  ingestion worker, frontend và Adminer.
- Bộ test backend cô lập bằng SQLite; lint/build frontend đã chạy được ở lần kiểm
  tra gần nhất.

## Chưa có hoặc chưa hoàn thiện

- Ingestion/indexing đã chạy qua DB job + Celery/Redis worker; chưa có parser
  subprocess wall-clock isolation, malware scanning, broker HA/monitoring hoặc
  object storage production.
- Chưa có reranker/ANN và multi-lesson holdout/human evaluation đủ để kết luận
  chất lượng RAG hay tác động giáo dục.
- AI dialogue grading chưa ảnh hưởng điểm; baseline tin cậy vẫn là trắc nghiệm
  deterministic do teacher duyệt.
- SadTalker được giữ làm PoC không còn là web flow ưu tiên. Piper voice/model card,
  provenance avatar, chất lượng tiếng Việt, caption timing và cold/warm latency
  của video slide chưa có bằng chứng live.
- Frontend chưa có test runner tự động riêng; Docker Compose là development.
- Một số frontend pages vẫn là prototype/placeholder; không nên xem các app model
  và endpoint tồn tại là bằng chứng UI end-to-end đã hoàn tất.

## Ưu tiên thực hiện

1. Teacher review/publish các assessment corpus draft và chạy E2 với response
   cases cùng hai người chấm độc lập.
2. Mở rộng RAG evaluation sang nhiều lesson, tách holdout và human review trước
   khi tune threshold/model.
3. Bổ sung durable background processing và production storage/security.
4. Sau khi duyệt license Piper/model và quyền asset, chạy một video slide tiếng
   Việt 30–60 giây, ghi cold/warm latency và rà soát giọng/caption; video vẫn là
   enhancement tùy chọn.

## Tiêu chí không được tuyên bố sớm

Hệ thống chỉ được gọi là RAG hoàn chỉnh khi retrieval dùng dữ liệu đã index,
authorization được áp dụng trước vector ranking, citation thuộc tập chunk đã truy
xuất và câu hỏi thiếu bằng chứng trả fallback. API provider trả lời được không tự
động đồng nghĩa với RAG đã hoạt động.

Xem [SETUP.md](SETUP.md) để chạy dự án và [DOCKER_GUIDE.md](DOCKER_GUIDE.md) để
xử lý container.
