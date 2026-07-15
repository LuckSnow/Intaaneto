# Trạng thái dự án Intaaneto

Cập nhật: 2026-07-13. Đây là ảnh chụp trạng thái code đã kiểm tra, không phải danh
sách tính năng dự kiến.

## Đã có

- Django 5 + Django REST Framework, PostgreSQL, JWT và các app `users`,
  `courses`, `exercises`, `ai_assistant`, `forum`, `analytics`.
- React 18 + Vite 7, routing, Zustand, React Query và trang lesson có tab AI.
- Phân quyền course/lesson cơ bản theo learner enrollment, teacher owner và admin.
- Student API không trả `solution_code` và hidden test cases.
- AI generation đi qua provider adapter; lesson chat có scope backend kiểm tra,
  history giới hạn và response contract ổn định.
- Docker Compose development cho PostgreSQL, backend, frontend và Adminer.
- Bộ test backend cô lập bằng SQLite; lint/build frontend đã chạy được ở lần kiểm
  tra gần nhất.

## Chưa có hoặc chưa hoàn thiện

- RAG thật: chưa có document/chunk/vector model, embedding service, vector store,
  retrieval/reranking, ingestion job, citation thật hoặc evaluation dataset.
- Chat hiện chỉ dùng lesson summary/content giới hạn làm context; response chủ
  động trả `grounded=false` và citation rỗng.
- Exercise chưa gắn trực tiếp với course/lesson nên authorization cho hint chưa
  thể hoàn chỉnh.
- Upload parsing chạy bằng daemon thread, chưa có durable job queue; validation
  loại file/content còn thiếu.
- Chưa có rate limiting và security regression coverage đầy đủ.
- Avatar, giọng nói, video tương tác và báo cáo đánh giá AI chưa phải tính năng
  hoàn chỉnh.
- Một số frontend pages vẫn là prototype/placeholder; không nên xem các app model
  và endpoint tồn tại là bằng chứng UI end-to-end đã hoàn tất.

## Ưu tiên thực hiện

1. Ổn định môi trường chạy và giữ test/lint/build xanh.
2. Xây vertical slice RAG đầu tiên: nguồn lesson được teacher phê duyệt -> extract
   giới hạn -> chunk/version idempotent -> embedding -> retrieval đã filter quyền
   -> answer có citation hoặc grounded fallback.
3. Bổ sung negative tests cho learner không enroll, course khác, forged scope,
   prompt injection và citation membership.
4. Sau RAG MVP mới mở rộng chấm bài đối thoại, analytics, voice/avatar/video.

## Tiêu chí không được tuyên bố sớm

Hệ thống chỉ được gọi là RAG hoàn chỉnh khi retrieval dùng dữ liệu đã index,
authorization được áp dụng trước vector ranking, citation thuộc tập chunk đã truy
xuất và câu hỏi thiếu bằng chứng trả fallback. API provider trả lời được không tự
động đồng nghĩa với RAG đã hoạt động.

Xem [SETUP.md](SETUP.md) để chạy dự án và [DOCKER_GUIDE.md](DOCKER_GUIDE.md) để
xử lý container.
