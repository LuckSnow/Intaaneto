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
- Ba assessment blueprint đại diện gồm 27 câu nằm tách khỏi lesson/RAG; mỗi
  objective có 3 câu và mặc định import ở trạng thái draft chờ teacher review.
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
- Blueprint importer kiểm tra teacher ownership, chỉ nhận lesson do corpus
  importer quản lý, không ghi đè attempt và chỉ publish khi có xác nhận review.

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

Tại ngày 2026-07-17:

- 197 backend tests pass trong isolated Django test settings, gồm một hành trình
  tích hợp course draft → PDF/RAG index → assessment → enroll → progression.
- Django system check pass; migration drift check pass.
- Frontend ESLint, production build pass và `npm audit` báo 0 lỗ hổng đã biết.
- PostgreSQL migration `courses.0005` đã áp dụng ở development.
- Bundle chính đã giảm từ khoảng 997 kB xuống 465 kB nhờ tách Google Auth; build
  còn cảnh báo Browserslist data cũ.

Các test bao phủ indexing atomic/idempotent, retrieval authorization, grounded
citations/fallback, PDF ingestion, auth/role, assessment/progression,
reinforcement, reports, corpus import và SadTalker adapter. Test pass không thay
thế evaluation chất lượng mô hình hoặc penetration test production.

Teacher report hiện tổng hợp objective từ attempt mới nhất của mỗi learner trên
mỗi assessment version hiện hành, cho biết số learner cần củng cố và tỷ lệ trả
lời đúng mà không trả danh tính/đáp án. Đây là mô tả dữ liệu quan sát được, không
phải bằng chứng về tác động học tập.

## 5. Thí nghiệm còn phải thực hiện

### E1 — Grounded answer evaluation

- Harness full-pipeline đã được implement với authorization, xác nhận provider
  cost, grounded/refusal contract, citation scope, lexical marker, latency và
  token metrics. Live Gemini baseline V1 trên 8 case đạt contract pass `0,75`,
  citation scope `1,00`, refusal `1,00`; strict lexical proxy pass chỉ `0,50`.
- Mean warm latency là `1.515,62 ms/case`, provider báo 2.283 token cho 4 call.
  Hai answerable case bị threshold từ chối; hai output grounded khác cách diễn
  đạt source marker. Không coi contract hoặc lexical proxy là answer accuracy.
- Mở rộng dataset và tách development/holdout.
- Chấm thủ công answer correctness, groundedness, citation correctness và
  refusal quality; lexical marker không thay thế semantic judgment.
- Ghi model/config/version, latency và cost; không ghi secret/full prompt.

Chi tiết cấu hình, per-case state không chứa raw answer và giới hạn được lưu tại
`docs/RAG_GROUNDED_ANSWER_BASELINE_V1.md`.

### E2 — Assessment consistency

- Protocol thực nghiệm, mẫu dữ liệu, quy trình hai người chấm và chỉ số agreement
  đã được định nghĩa tại `docs/ASSESSMENT_EVALUATION_PROTOCOL.md`.
- Software baseline trên 3 assessment/27 câu/9 objective sinh 81 response row và
  12 attempt profile. Fixture contract và pass-boundary accuracy đều `1,00`; 7/9
  đạt `77,78` và pass, 6/9 đạt `66,67` và fail tại threshold 70%.
- Kết quả trên chỉ chứng minh scoring consistency. Hai template review private
  đã sẵn sàng nhưng chưa có rating, adjudication hoặc human agreement.
- Teacher tạo bộ câu hỏi/rubric theo learning objective cho lesson đại diện.
- So sánh deterministic score với đánh giá hội thoại chỉ ở chế độ recommendation.
- Có ít nhất hai người chấm và đo agreement trước khi AI grade ảnh hưởng learner.

### E3 — Reinforcement outcome

- Audit event tối thiểu và report paired đã được implement: lấy exposure có
  evidence đầu tiên của failed attempt và attempt tiếp theo cùng version, báo
  before/after/change/pass conversion/pending mà không trả identity.
- Chưa có baseline từ usage thật; cần learner sử dụng reinforcement rồi làm lại.
- Một learner có thể đóng góp nhiều cặp attempt; không suy ra causal effect nếu
  không có thiết kế nhóm/điều kiện và xử lý repeated measures phù hợp.

### E4 — SadTalker real smoke

- Pin commit/checkpoint và ghi GPU/CUDA/PyTorch/FFmpeg.
- Đo audio duration, render latency, output size và peak GPU memory.
- Rà soát lip-sync, facial stability, artifacts và intelligibility tiếng Việt.
- Chỉ dùng portrait/audio có quyền và thông báo đây là video tổng hợp.

Technical smoke ngày 2026-07-17 đã tạo MP4 H.264/AAC 256×256 dài 1,48 giây,
40.522 byte trong 53 giây trên NVIDIA T1200. Ca này dùng asset demo upstream và
chỉ chứng minh pipeline/runtime, không được dùng làm bằng chứng quyền nội dung,
chất lượng tiếng Việt hay chất lượng sư phạm. E4 chỉ hoàn tất sau một render bằng
asset đã được duyệt, đo tài nguyên và review định tính theo rubric trên.

## 6. Giới hạn và đe dọa tới tính hợp lệ

- Dataset retrieval hiện quá nhỏ và cùng miền với demo content.
- Threshold/model chưa được tuning trên holdout; exact search phù hợp corpus nhỏ
  nhưng chưa chứng minh khả năng mở rộng.
- Assessment hiện là trắc nghiệm teacher-authored, chưa phải AI dialogue grading.
- Progress/mastery phản ánh quy tắc sản phẩm, không tự động đồng nghĩa với năng
  lực thực tế hoặc tác động giáo dục.
- PDF parser và embedding chạy đồng bộ; chưa có durable worker/rate limit đầy đủ.
- SadTalker đã có adapter tests và technical GPU render; chưa có render học liệu
  bằng portrait/audio đã duyệt hoặc đánh giá chất lượng tiếng Việt.
- Token localStorage và production settings vẫn cần security hardening; dependency
  audit sạch chỉ là bằng chứng tại một thời điểm và cần được chạy định kỳ.

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
