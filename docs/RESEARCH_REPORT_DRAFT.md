# Báo cáo nghiên cứu Intaaneto — bản thảo theo bằng chứng

## 1. Tên đề tài

Nghiên cứu xây dựng hệ thống E-learning trên môi trường web tích hợp giảng viên
ảo dựa trên công nghệ Trí tuệ nhân tạo.

## 2. Câu hỏi nghiên cứu

1. RAG lesson-scoped có giúp AI Tutor trả lời từ đúng học liệu và từ chối câu hỏi
   ngoài phạm vi hay không?
2. Một baseline đánh giá deterministic có thể tạo progression giải thích được
   trước khi thử nghiệm AI dialogue grading hay không?
3. Weak learning objectives có thể điều hướng learner về đúng đoạn tài liệu mà
   không làm thay đổi điểm hay không?
4. SadTalker local có phù hợp làm lớp trình bày video tùy chọn về chất lượng,
   latency, tài nguyên và rủi ro quyền chân dung hay không?

## 3. Phương pháp và kiến trúc

### 3.1. Dữ liệu

- PDF do teacher-owner phê duyệt; kiểm tra signature, size, page count và text.
- Hai nguồn Markdown mẫu: Mạng máy tính và Lập trình Web, compile thành 15 lesson.
- Không index answer key, hidden tests, chat hoặc dữ liệu ngoài lesson.

### 3.2. RAG

- Normalization NFKC và chunking deterministic có overlap/offset ổn định.
- Embedding local FastEmbed, multilingual MiniLM 384 chiều.
- Source checksum/version; activate atomic, re-index idempotent.
- Exact pgvector cosine trong một active source đã được authorize.
- Threshold tạm thời 0.45; citations do application tạo.

### 3.3. Assessment và progression

- Multiple-choice do teacher soạn, pass threshold cấu hình được.
- Giáo viên có giao diện web để chọn course/lesson thuộc quyền quản lý, biên
  soạn mục tiêu/câu hỏi/lựa chọn/đáp án, lưu draft và xuất bản assessment.
- Giáo viên có giao diện quản lý course theo vòng đời draft → thêm lesson usable
  → publish; backend không cho tự featured hoặc xóa cascade course đã có dữ liệu.
- Score và pass do backend tính; attempt/answer snapshot lưu theo version.
- Chỉ attempt đạt mới hoàn thành lesson và nhận next lesson.
- Mastery tách khỏi content progress.
- Failed attempt tạo weak objectives cho RAG reinforcement retrieval-only.

### 3.4. Video PoC

- Script/audio/portrait được phê duyệt ngoài luồng learner.
- SadTalker chạy local qua command có timeout, input/output bounds và audit job.
- Video là enhancement tùy chọn; lỗi video không chặn text/RAG/assessment.

## 4. Kết quả đã đo

### 4.1. Retrieval baseline v1

Nguồn đầy đủ: [RAG_RETRIEVAL_BASELINE_V1.md](RAG_RETRIEVAL_BASELINE_V1.md).

| Chỉ số | Kết quả |
| --- | ---: |
| Số case | 8 |
| Pass/status accuracy | 0.75 |
| Expected-source recall | 1.00 |
| Mean latency gồm cold start | 225.12 ms |

Hai case answerable bị threshold 0.45 từ chối dù expected marker nằm trong top-k.
Hai case unsupported fallback đúng. Không hạ threshold chỉ dựa trên tập nhỏ này.

### 4.2. Bằng chứng kiểm thử phần mềm

Tại ngày 2026-07-16:

- 168 backend tests pass trong isolated Django test settings, gồm một hành trình
  tích hợp course draft → PDF/RAG index → assessment → enroll → progression.
- Django system check pass; migration drift check pass.
- Frontend ESLint và production build pass.
- PostgreSQL migration `courses.0005` đã áp dụng ở development.
- Build còn cảnh báo JS chunk trên 500 kB và Browserslist data cũ.

Các test bao phủ indexing atomic/idempotent, retrieval authorization, grounded
citations/fallback, PDF ingestion, auth/role, assessment/progression,
reinforcement, reports, corpus import và SadTalker adapter. Test pass không thay
thế evaluation chất lượng mô hình hoặc penetration test production.

## 5. Thí nghiệm còn phải thực hiện

### E1 — Grounded answer evaluation

- Harness full-pipeline đã được implement với authorization, xác nhận provider
  cost, grounded/refusal contract, citation scope, lexical marker, latency và
  token metrics. Chưa có live-provider baseline.
- Mở rộng dataset và tách development/holdout.
- Chấm thủ công answer correctness, groundedness, citation correctness và
  refusal quality; lexical marker không thay thế semantic judgment.
- Ghi model/config/version, latency và cost; không ghi secret/full prompt.

### E2 — Assessment consistency

- Teacher tạo bộ câu hỏi/rubric theo learning objective cho lesson đại diện.
- So sánh deterministic score với đánh giá hội thoại chỉ ở chế độ recommendation.
- Có ít nhất hai người chấm và đo agreement trước khi AI grade ảnh hưởng learner.

### E3 — Reinforcement outcome

- So sánh điểm attempt trước/sau khi dùng RAG reinforcement.
- Không suy ra causal effect nếu không có thiết kế nhóm/điều kiện phù hợp.

### E4 — SadTalker real smoke

- Pin commit/checkpoint và ghi GPU/CUDA/PyTorch/FFmpeg.
- Đo audio duration, render latency, output size và peak GPU memory.
- Rà soát lip-sync, facial stability, artifacts và intelligibility tiếng Việt.
- Chỉ dùng portrait/audio có quyền và thông báo đây là video tổng hợp.

## 6. Giới hạn và đe dọa tới tính hợp lệ

- Dataset retrieval hiện quá nhỏ và cùng miền với demo content.
- Threshold/model chưa được tuning trên holdout; exact search phù hợp corpus nhỏ
  nhưng chưa chứng minh khả năng mở rộng.
- Assessment hiện là trắc nghiệm teacher-authored, chưa phải AI dialogue grading.
- Progress/mastery phản ánh quy tắc sản phẩm, không tự động đồng nghĩa với năng
  lực thực tế hoặc tác động giáo dục.
- PDF parser và embedding chạy đồng bộ; chưa có durable worker/rate limit đầy đủ.
- SadTalker mới có adapter tests, chưa có real-render evidence.
- Token localStorage, frontend dependency vulnerabilities và production settings
  vẫn cần security hardening.

## 7. Đạo đức, quyền riêng tư và an toàn

- Thu thập tối thiểu; report teacher không trả email/chat/answer.
- Không dùng retrieval similarity làm learner score.
- Không cho model quyết định authorization, citation membership hoặc progression.
- Xin quyền/consent cho chân dung và giọng nói; cấm giả mạo/lừa đảo.
- Không đưa dữ liệu nhạy cảm lên free-tier provider nếu điều khoản xử lý dữ liệu
  chưa phù hợp.

## 8. Kết luận tạm thời

Intaaneto đã có một vòng lặp có thể kiểm chứng từ học liệu được phê duyệt tới
RAG Tutor, đánh giá deterministic, progression, reinforcement và báo cáo. Kết
quả retrieval v1 cho thấy expected evidence được tìm thấy trong top-k nhưng
threshold còn false negative. Chưa đủ bằng chứng để kết luận AI dialogue grading
hoặc SadTalker video đạt chất lượng; các tuyên bố đó phụ thuộc E1–E4.
