# PoC giảng viên video ảo với SadTalker

Trạng thái: adapter local, audit job, runtime GPU cô lập và technical smoke đã
được triển khai. Technical smoke đã tạo MP4 thật nhưng dùng asset demo upstream;
không coi video học liệu là hoàn thành cho tới khi render portrait/audio đã được
duyệt và lưu kết quả đánh giá chất lượng.

## SadTalker làm gì và không làm gì

SadTalker nhận **một ảnh chân dung và một file audio** để tạo talking-head video.
Nó không tự viết kịch bản hoặc tự làm TTS; Intaaneto bổ sung summary draft có
teacher review và `espeak-ng` local trước adapter. Luồng PoC:

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

PoC có hai entry point: management command tin cậy và endpoint teacher-owner chỉ
enqueue database job cho worker `video`; không chạy GPU inline trong HTTP:

- Kiểm tra teacher ownership/admin trước khi đọc input.
- Bắt buộc cờ xác nhận quyền sử dụng và phê duyệt.
- Chỉ nhận script UTF-8 tối đa 12.000 ký tự.
- Chỉ nhận PCM WAV tối đa 25 MiB và 10 phút.
- Chỉ nhận JPEG/PNG 256–4096 px, tối đa 16 triệu pixel và 10 MiB.
- Gọi SadTalker bằng argument list, không qua shell.
- Timeout mặc định 900 giây và dừng process group khi quá hạn.
- Chỉ nhận đúng một MP4 có signature phù hợp, tối đa 250 MiB.
- Database lưu script đã duyệt, checksum input, actor, trạng thái và failure
  code an toàn; không lưu stdout/stderr hoặc đường dẫn input do client cung cấp.
- Web flow yêu cầu summary hiện tại đã duyệt, WAV checksum khớp summary và xóa
  portrait tạm sau trạng thái cuối; trạng thái DB là polling contract.

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

### Runtime đã kiểm chứng trên máy development

Biên bản ngày 2026-07-17:

- SadTalker commit `cd4c0465ae0b54a6f85af57f5c65fec9fe23e7f8` (checkout
  detached từ upstream chính thức), Python 3.8.20.
- Miniforge 26.3.2-3, PyTorch 1.12.1+cu113, torchvision 0.13.1+cu113,
  torchaudio 0.12.1+cu113 và FFmpeg 4.4.2.
- NVIDIA T1200 Laptop GPU 4 GiB; CUDA được PyTorch nhận trong container.
- Runtime host nằm ngoài repository và được mount read-only. Conda `glib` là
  dependency cần thiết để OpenCV chạy trong backend image.
- Cờ executable-stack của `libtorch_cpu.so` trong chính runtime cô lập phải được
  xóa bằng `patchelf --clear-execstack`; không nới seccomp/quyền container.

Các model tối thiểu mà adapter kiểm tra trước khi chạy:

| File | SHA-256 local |
| --- | --- |
| `SadTalker_V0.0.2_256.safetensors` | `c211f5d6de003516bf1bbda9f47049a4c9c99133b1ab565c6961e5af16477bff` |
| `mapping_00229-model.pth.tar` | `62a1e06006cc963220f6477438518ed86e9788226c62ae382ddc42fbcefb83f1` |
| `alignment_WFLW_4HG.pth` | `bbfd137307a4c7debd5c283b9b0ce539466cee417ac0a155e184d857f9f2899c` |
| `detection_Resnet50_Final.pth` | `6d1de9c2944f2ccddca5f5e010ea5ae64a39845a86311af6fdf30841b0a5a16d` |

Hai model cuối vẫn cần cho face alignment/detection dù không bật enhancer.
Digest là checksum file đã tải từ URL trong script upstream; GitHub release
không công bố checksum để đối chiếu độc lập, nên đây là giới hạn provenance cần
ghi trong báo cáo.

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

Repository có `docker-compose.sadtalker.yml` để mount runtime read-only và cấp
GPU. Dùng đường dẫn tuyệt đối của runtime trên máy local:

```bash
SADTALKER_HOST_RUNTIME=/absolute/path/to/intaaneto-sadtalker \
  docker compose -f docker-compose.yml -f docker-compose.sadtalker.yml config --quiet

SADTALKER_HOST_RUNTIME=/absolute/path/to/intaaneto-sadtalker \
  docker compose -f docker-compose.yml -f docker-compose.sadtalker.yml up -d video_worker
```

Adapter chạy upstream trong một work directory ghi được, truyền checkpoint bằng
đường dẫn tuyệt đối và chỉ symlink hai face-preprocessing weights vào work dir.
Điều này giữ checkout/model read-only dù upstream tạo MP4 tạm trong current
working directory.

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

Không thêm API key vì adapter không dùng dịch vụ SadTalker online. Web flow tạo
WAV bằng `espeak-ng` local từ summary đã duyệt; management command vẫn chấp nhận
WAV đã chuẩn bị riêng để có thể tách đánh giá lip-sync khỏi chất lượng TTS.

## Biên bản manual smoke

### Technical smoke đã chạy

Ngày 2026-07-17, asset demo đi kèm checkout upstream được dùng cho một phép thử
nội bộ, không attach vào lesson và không phát hành:

| Chỉ số | Kết quả |
| --- | --- |
| Audio input | 1,5 giây, mono PCM 16 kHz |
| GPU | NVIDIA T1200 Laptop GPU 4 GiB |
| Cấu hình | 256 px, batch 1, `crop`, `still`, không enhancer |
| Thời gian wall-clock | 53 giây |
| Output | H.264 + AAC, 256×256, 25 fps, 1,48 giây |
| Kích thước | 40.522 byte |
| SHA-256 output | `aa11ad32b249f747ac761a510a268d8c3f363c39a2a158d0ff243f55413d8673` |

Phép thử này chứng minh CUDA, model loading, face preprocessing, rendering và
FFmpeg mux hoạt động qua container read-only. Nó chưa đo peak GPU memory, chưa
đánh giá tiếng Việt/lip-sync và không chứng minh quyền tái sử dụng asset demo.
Output nằm trong development media volume, không được xem là artifact sản phẩm.

### Smoke bằng nội dung đã duyệt còn phải chạy

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
