# Đặc tả chức năng AI tương tác của Intaaneto

Cập nhật: 2026-07-16. Tài liệu này phân biệt rõ phần đã có bằng chứng triển khai,
adapter PoC và phần mới là hướng nghiên cứu.

## 1. Luồng đã triển khai

```text
PDF do teacher-owner tải lên
  -> kiểm tra PDF và giới hạn tài nguyên
  -> trích xuất, chuẩn hóa văn bản
  -> chunk + embedding local
  -> PostgreSQL/pgvector, source version active

Learner đã được phép
  -> câu hỏi theo lesson
  -> retrieval trong đúng active source
  -> fallback nếu bằng chứng yếu
  -> generation có căn cứ
  -> citation do ứng dụng tạo

Assessment trắc nghiệm do teacher soạn
  -> backend chấm deterministic
  -> attempt snapshot + weak objectives
  -> mastery/progression do backend quyết định
  -> RAG reinforcement theo weak objectives
  -> báo cáo learner/teacher
```

Teacher/admin có trang `/teacher/assessments` để chọn course và lesson thuộc
quyền quản lý, tạo/sửa/xóa assessment chưa có attempt, đặt ngưỡng đạt, khai báo
learning objective và xuất bản. Backend giới hạn tối đa 50 câu, không tin đáp án
hoặc score từ learner.

Teacher có trang `/teacher/courses` để tạo/sửa course thuộc sở hữu. Course mới
bắt buộc là draft và chỉ được publish sau khi có lesson đã publish với content
hoặc active ready RAG source. Course có lesson/học viên không thể bị xóa cascade
qua API; teacher không thể tự gắn trạng thái featured.

Các boundary đã có test:

- Teacher ownership được kiểm tra trước khi đọc/xử lý upload.
- Retrieval lọc lesson/course được phép trước embedding và ranking.
- Answer key không có trong learner API hoặc RAG index.
- Citation chỉ được xây từ chunk thực sự retrieved.
- Assessment score, mastery, completion và next lesson không do client/LLM ghi.
- Báo cáo learner chỉ có dữ liệu bản thân; teacher chỉ có khóa sở hữu.

## 2. Kho học liệu

Hệ thống dùng PostgreSQL và pgvector làm kho dữ liệu học tập và tri thức; không
cần một database riêng chỉ vì có RAG. Hai tài liệu Markdown mẫu được compile
deterministic thành 2 course/15 lesson dạng nháp. Việc publish và index là hai
thao tác phê duyệt riêng.

Ba lesson đại diện có assessment blueprint tách riêng gồm 27 câu, đúng 3 câu cho
mỗi objective. Import mặc định tạo draft, kiểm tra teacher-owner và không ghi đè
attempt; answer key không được nối vào lesson content/RAG.

PDF là định dạng upload duy nhất. DOCX, PPT và PPTX không thuộc phạm vi ingestion
hiện tại. Upload/reprocess trả `202`, lưu job trong database và Celery worker xử
lý qua Redis với reauthorization, retry hữu hạn và polling trạng thái thật.
Parser subprocess wall-clock isolation và production broker HA chưa có.

## 3. AI Tutor

AI Tutor nhận `lesson_id` do backend kiểm tra, truy xuất exact cosine trong active
source tương thích, chọn các chunk vượt threshold rồi mới gọi OpenAI hoặc Gemini.
Nếu lesson chưa index hoặc bằng chứng yếu, hệ thống không gọi generation và trả
fallback. Retrieved document text được coi là dữ liệu không tin cậy, không phải
system instruction.

Chat khôi phục phiên lesson gần nhất và citation excerpt sau reload trong giới
hạn backend. Citation được dựng lại từ chunk thuộc đúng lesson/source version;
quyền bị thu hồi sẽ ẩn history/session. Retrieval và grounded-answer đều có live
baseline trên 8 case; citation scope/refusal đạt contract trong tập demo nhưng
chưa đủ để kết luận chất lượng tổng quát.

## 4. Đánh giá và tiến trình học

Baseline hiện tại là multiple-choice do teacher soạn, có version và pass
threshold. Backend lưu immutable answer snapshot của mỗi attempt và tính:

- `progress_percentage`: phần lesson usable đã hoàn thành;
- `mastery_percentage`: trung bình best score của assessment published phiên bản
  hiện tại, assessment chưa làm đóng góp 0;
- `weak_objectives`: mục tiêu gắn với câu trả lời sai.

Dashboard tổng hợp learner progress và teacher roster từ dữ liệu authoritative.
Teacher/admin có thể xuất CSV cho một course thuộc phạm vi; file không chứa
email/chat/đáp án, giới hạn 5.000 học viên và chống spreadsheet formula injection.
Phần objective report dùng lần làm mới nhất trên assessment version hiện hành để
hiển thị số học viên cần củng cố và correct rate mà không lộ danh tính/đáp án.

RAG reinforcement là thao tác riêng sau attempt không đạt. Nó truy xuất học liệu
cho weak objective và không thay đổi score/mastery/progression. AI dialogue
grading với rubric/calibration chưa được triển khai và không được coi là kết quả
đã có.

Một audit event tối thiểu ghi nhận packet đã được lấy mà không lưu prompt/excerpt.
Teacher report ghép exposure có evidence với attempt tiếp theo cùng version để
hiển thị before/after; đây chỉ là association quan sát, không phải causal effect.

## 5. Giảng viên video ảo

Adapter SadTalker local đã có dưới dạng management command thủ công. Nó nhận
kịch bản đã duyệt, PCM WAV và JPEG/PNG có xác nhận quyền sử dụng, chạy
`inference.py` không qua shell, có timeout, validate MP4 và lưu audit job. Không
có HTTP trigger và không có automatic TTS.

SadTalker là image + audio -> talking-head video, không tự sinh lời thoại hoặc
giọng nói và không cần API key khi self-host. Technical GPU smoke đã tạo MP4 thật
trên NVIDIA T1200; vẫn chưa có portrait/audio học liệu được duyệt hoặc đánh giá
lip-sync/tiếng Việt. Xem
[SADTALKER_POC.md](SADTALKER_POC.md).

## 6. Thành phần chưa triển khai

- Production broker HA/monitoring và chuyển SadTalker sang worker có GPU riêng.
- Automatic TTS, storyboard, slide/image generation và ghép cảnh.
- WebSocket/realtime processing progress.
- AI dialogue assessment ảnh hưởng điểm hoặc progression.
- Grounded-answer/assessment evaluation đa lesson, holdout và hai người chấm.
- Production object storage, media retention/deletion và malware scanning.

Các thành phần này chỉ là roadmap; không được dùng trong demo hoặc báo cáo như
chức năng đã hoàn thành.
