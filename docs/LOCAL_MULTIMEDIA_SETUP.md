# Video slide local với Piper và AI Tutor

Trạng thái: vertical slice local đã chạy live, không dùng SadTalker, D-ID hoặc
API TTS cloud.
Pipeline chỉ chạy sau khi giáo viên đã duyệt summary và kịch bản video hiện tại.

```text
Approved summary + active RAG source
  -> reviewable 4–5 minute video script (one explicit AI call)
  -> teacher approval
  -> Piper Vietnamese WAV
  -> deterministic storyboard
  -> Pillow slide + burned-in caption + AI Tutor asset
  -> FFmpeg MP4
  -> teacher preview / learner lesson video
```

Video là enhancement tùy chọn. Job lỗi không làm thay đổi RAG readiness,
assessment, score, mastery hoặc lesson progression.

## Việc chủ dự án cần xem xét

Không cần API key hoặc tài khoản provider. Tuy nhiên, trước khi tải model hoặc
phát hành artifact ra ngoài phạm vi nghiên cứu, cần xem ba mục sau:

1. Piper `1.4.2` dùng giấy phép GPL-3.0. Xem repository và license chính thức:
   https://github.com/OHF-Voice/piper1-gpl
2. Mỗi voice có model card và có thể có điều khoản riêng. Phải đọc file
   `vi/vi_VN/vais1000/medium/MODEL_CARD` trước khi dùng ngoài demo nghiên cứu:
   https://huggingface.co/rhasspy/piper-voices/tree/main/vi/vi_VN/vais1000/medium
   Metadata license ở cấp repository không tự động chứng minh quyền cho dataset,
   giọng hoặc output của từng model.
3. Xác nhận quyền sử dụng và phân phối
   `backend/assets/AI_tutor.png`. Việc file có trong repository không tự
   chứng minh provenance hoặc license.

Không commit model `.onnx`, file config tải về, generated WAV/MP4 hoặc dữ liệu
học viên. Compose lưu model trong named volume `tts_models` và artifact trong
media volume.

## Cài runtime

Slice cần Piper, FFmpeg và font DejaVu. Chúng đã được khai báo trong backend
image. Build lại image:

```bash
docker compose build backend worker
```

Sau khi đã đọc model card và chấp nhận phạm vi sử dụng, tải voice vào volume.
Đây là lần duy nhất cần Internet; runtime tạo video không gọi mạng:

```bash
docker compose run --rm --user root worker \
  python -m piper.download_voices \
  --data-dir /app/tts-models \
  vi_VN-vais1000-medium
```

Kiểm tra đúng hai file bắt buộc mà không in nội dung model:

```bash
docker compose run --rm --user root worker sh -lc \
  'test -s /app/tts-models/vi_VN-vais1000-medium.onnx && \
   test -s /app/tts-models/vi_VN-vais1000-medium.onnx.json'
```

Apply migration và recreate service:

```bash
docker compose up -d --force-recreate backend worker frontend
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py check
```

Không cần bật `docker-compose.sadtalker.yml` hoặc GPU worker.

## Sử dụng trên web

1. Giáo viên mở trang upload và chọn lesson đã RAG-ready.
2. Tạo, sửa và duyệt summary.
3. Chọn `AI soạn kịch bản 4–5 phút`, xác nhận một lượt provider, sửa và duyệt.
4. Kiểm tra bộ đếm ký tự, đoạn đọc và slide dự kiến. Kịch bản phải không quá
   4.800 ký tự và 50 đoạn đọc; câu dài hơn 180 ký tự có thể thành nhiều đoạn.
5. Chọn `Tạo video slide tiếng Việt`.
6. Có thể rời trang; DB giữ trạng thái `queued`, `narrating`,
   `rendering_slides`, `compositing`, `completed` hoặc `failed`.
7. Khi hoàn thành, nghe riêng WAV hoặc preview MP4 ngay trong panel.

Video dùng kịch bản đã duyệt làm immutable snapshot cho job. Worker kiểm tra lại
teacher ownership, checksum source/summary/script và checksum ảnh AI Tutor trước
khi chạy. Nếu nguồn, summary, script hoặc asset thay đổi, job dừng an toàn.

## Cấu hình local

Các giá trị mặc định đã có trong `.env.example`:

```env
PIPER_PYTHON_EXECUTABLE=python
PIPER_VOICE=vi_VN-vais1000-medium
PIPER_MODEL_PATH=/app/tts-models/vi_VN-vais1000-medium.onnx
PIPER_TIMEOUT_SECONDS=120
PIPER_LENGTH_SCALE=1.12
# Khoảng lặng chèn sau dấu phẩy/chấm phẩy/hai chấm và sau câu hoàn chỉnh.
PIPER_CLAUSE_PAUSE_MS=160
PIPER_SENTENCE_PAUSE_MS=500
MULTIMEDIA_FFMPEG_EXECUTABLE=ffmpeg
MULTIMEDIA_TUTOR_IMAGE_PATH=/app/media-assets/AI_tutor.png
MULTIMEDIA_TIMEOUT_SECONDS=180
MULTIMEDIA_MAX_DURATION_SECONDS=300
```

Không đặt các giá trị trên trong `VITE_*`. Không có secret nào cần cấu hình cho
pipeline này.

Piper tạo WAV riêng cho từng mệnh đề/câu, nối bằng khoảng lặng cấu hình và dùng
thời lượng WAV thực tế của từng câu để giữ caption trên slide đúng với lời đọc.
Tăng `PIPER_LENGTH_SCALE` để đọc chậm hơn; sau khi đổi cấu hình, recreate
`backend` và `worker`, rồi tạo một job video mới. Các WAV/MP4 đã có không thay đổi.

## Benchmark và bằng chứng báo cáo

Ngày 2026-07-19, hai job thật đã chạy trên lesson PHP 141 với summary đã duyệt
1.602 ký tự. Cả hai tạo 12 slide, WAV Piper tiếng Việt và MP4 H.264 1280x720,
không gọi provider mạng:

| Run | Thời lượng video | Thời gian pipeline | Kích thước MP4 |
| --- | ---: | ---: | ---: |
| Sau khi khởi động worker | 78,81 giây | 14,285 giây | 1.753.010 bytes |
| Warm run | 78,92 giây | 13,663 giây | 1.754.994 bytes |

Đây là bằng chứng kỹ thuật trên máy development, không phải đánh giá chất lượng
giọng, đồng bộ caption hoặc hiệu quả sư phạm. Chủ dự án đã chấp nhận voice và
ảnh AI Tutor cho phạm vi nghiên cứu học tập tại trường; chưa mở rộng kết luận đó
sang phát hành công khai hoặc thương mại.

Mỗi job hoàn thành lưu các metadata bounded sau:

- voice/provider;
- số slide;
- thời lượng video;
- thời gian render;
- checksum summary và tutor asset;
- failure code an toàn nếu thất bại.

Không ghi stdout/stderr Piper/FFmpeg, model bytes, full command diagnostics hoặc
đường dẫn private vào API. Trước khi tuyên bố pipeline “nhanh”, chạy ít nhất một
clip 30–60 giây trên máy development và ghi cold-start cùng warm-run riêng.

## Xử lý lỗi

- `Model giọng Việt Piper chưa sẵn sàng`: tải đủ `.onnx` và `.onnx.json` vào
  volume `tts_models`.
- `Không thể tạo giọng đọc`: kiểm tra worker đã rebuild với `piper-tts` và xem
  log bounded bằng `docker compose logs --tail=100 worker`.
- `Font dựng slide chưa sẵn sàng`: rebuild backend image để cài DejaVu.
- `Ảnh AI Tutor chưa sẵn sàng`: kiểm tra file nguồn còn tồn tại rồi recreate
  worker để bind mount lại.
- `Bản tóm tắt đã thay đổi`: duyệt summary mới và enqueue một job mới.
- `Không thể ghép video`: xác nhận FFmpeg có trong worker bằng
  `docker compose exec worker ffmpeg -version`.

Không tự động retry một job đã bắt đầu TTS/composition. Giáo viên chủ động tạo
lại sau khi đã sửa nguyên nhân để tránh nhiều render đồng thời.
