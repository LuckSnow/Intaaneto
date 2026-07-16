# PoC giảng viên video ảo với SadTalker

Trạng thái: adapter local và audit job đã được triển khai, nhưng chưa có bằng
chứng render thật trên GPU của máy triển khai. Không coi video SadTalker là hoàn
thành cho tới khi chạy manual smoke và lưu kết quả đánh giá.

## SadTalker làm gì và không làm gì

SadTalker nhận **một ảnh chân dung và một file audio** để tạo talking-head video.
Nó không tự viết kịch bản và không tự chuyển văn bản thành giọng nói. Luồng PoC:

```text
Nội dung lesson đã duyệt
  -> kịch bản do giáo viên duyệt
  -> WAV đã duyệt (thu âm hoặc TTS)
  + ảnh chân dung có quyền/đồng ý sử dụng
  -> SadTalker local
  -> MP4 gắn vào lesson
```

SadTalker self-hosted không có API key. Repository chính thức mô tả CLI
`inference.py --driven_audio ... --source_image ...`, yêu cầu FFmpeg, model
checkpoints và môi trường Python riêng. Tài liệu chính thức:

- https://github.com/OpenTalker/SadTalker
- https://github.com/OpenTalker/SadTalker/blob/main/docs/install.md
- https://github.com/OpenTalker/SadTalker/blob/main/LICENSE
- Bài báo: https://arxiv.org/abs/2211.12194

Repository công bố Apache 2.0 cho SadTalker nhưng loại trừ một số thành phần bên
thứ ba. Trước khi phát hành sản phẩm, phải rà soát license của checkpoint,
GFPGAN/facexlib và mọi ảnh, audio, font hoặc asset đi kèm. Không dùng chân dung
hoặc giọng nói của người thật nếu chưa có quyền và sự đồng ý phù hợp.

## Boundary của Intaaneto

PoC chỉ chạy qua management command, không có HTTP endpoint:

- Kiểm tra teacher ownership/admin trước khi đọc input.
- Bắt buộc cờ xác nhận quyền sử dụng và phê duyệt.
- Chỉ nhận script UTF-8 tối đa 12.000 ký tự.
- Chỉ nhận PCM WAV tối đa 25 MiB và 10 phút.
- Chỉ nhận JPEG/PNG 256–4096 px, tối đa 16 triệu pixel và 10 MiB.
- Gọi SadTalker bằng argument list, không qua shell.
- Timeout mặc định 900 giây và dừng process group khi quá hạn.
- Chỉ nhận đúng một MP4 có signature phù hợp, tối đa 250 MiB.
- Database lưu script đã duyệt, checksum input, actor, trạng thái và failure
  code an toàn; không lưu stdout/stderr hoặc đường dẫn input.

Mỗi lần chạy tạo `Courses > Lesson video generation jobs` trong Django Admin.
Job là audit record read-only. Thành công sẽ gắn file MP4 vào `Lesson.video_file`.

## Chuẩn bị SadTalker tách biệt

Không cài dependency SadTalker trực tiếp vào image/backend environment hiện tại:
upstream dùng Python/PyTorch cũ và có thể xung đột Django/RAG. Tạo một runtime
GPU tách biệt, ghi lại commit SadTalker, phiên bản CUDA/PyTorch/FFmpeg và checksum
checkpoint trong biên bản thí nghiệm.

Theo hướng dẫn upstream, quy trình tham khảo là clone repository, tạo môi trường
Python 3.8 riêng, cài PyTorch phù hợp GPU, FFmpeg, requirements và tải model bằng
script chính thức. Trước khi nối Intaaneto, chạy trực tiếp CLI upstream với một
ảnh/audio phi nhạy cảm để xác nhận môi trường tạo đúng một MP4.

Runtime chạy management command phải nhìn thấy:

- checkout SadTalker tại `SADTALKER_ROOT`;
- Python executable của môi trường SadTalker tại
  `SADTALKER_PYTHON_EXECUTABLE`;
- database/media của Intaaneto;
- thư mục work ghi được tại `SADTALKER_WORK_ROOT`.

Trong môi trường PoC riêng, đặt cấu hình server-side, không dùng `VITE_*`:

```env
SADTALKER_ENABLED=True
SADTALKER_ROOT=/opt/SadTalker
SADTALKER_PYTHON_EXECUTABLE=/opt/sadtalker-venv/bin/python
SADTALKER_WORK_ROOT=/var/lib/intaaneto/sadtalker-work
SADTALKER_TIMEOUT_SECONDS=900
```

## Chạy một render đã duyệt

Chuẩn bị ba file local, không commit chúng:

- `lesson-script.txt`: kịch bản khớp audio và đã được giáo viên duyệt;
- `lesson.wav`: giọng nói có quyền sử dụng;
- `portrait.png`: chân dung có quyền/đồng ý sử dụng.

Sau đó chạy trong runtime PoC:

```bash
python manage.py generate_sadtalker_video LESSON_ID \
  --actor-id TEACHER_ID \
  --script-file /private-input/lesson-script.txt \
  --audio-file /private-input/lesson.wav \
  --portrait-file /private-input/portrait.png \
  --confirm-rights-and-approval
```

Không thêm API key vì adapter không dùng dịch vụ SadTalker online. Nếu chọn TTS
cloud ở slice sau, key TTS mới cần được đặt server-side; PoC hiện chấp nhận WAV
đã chuẩn bị sẵn để tách đánh giá lip-sync khỏi chất lượng TTS.

## Biên bản manual smoke

Ghi ít nhất các bằng chứng sau cho báo cáo nghiên cứu:

- SadTalker commit, checkpoint/checksum, GPU, CUDA, PyTorch, FFmpeg.
- Độ dài audio, thời gian render, kích thước MP4 và peak GPU memory nếu có.
- Job ID và trạng thái; không đưa đường dẫn private hoặc dữ liệu cá nhân vào log.
- Rà soát thủ công: đồng bộ môi/âm thanh, ổn định khuôn mặt, chuyển động đầu,
  lỗi hình ảnh và khả năng nghe hiểu tiếng Việt.
- Ít nhất một ca input không hợp lệ, một ca timeout/failure và một ca thành công.
- Xác nhận video chỉ là nội dung trình bày tùy chọn; lỗi video không chặn learner
  đọc bài, dùng RAG Tutor hoặc làm assessment.

Giới hạn nghiên cứu phải nêu rõ: đánh giá bằng mắt trên một vài video không chứng
minh chất lượng tổng quát, và video tổng hợp cần được thông báo rõ cho người xem.
