# Handoff PoC video D-ID

Trạng thái: **chưa implement D-ID**. Tài liệu này là handoff cho vertical slice
tiếp theo; không được mô tả provider cloud là chức năng đã có.

## Vì sao cần PoC cloud

Ngày 2026-07-17, SadTalker job `1` của lesson PHP `141` dùng WAV tiếng Việt dài
`109,26` giây đã chạy `1.903` giây rồi kết thúc `provider_timeout`, không tạo
MP4. Trong lúc chạy, NVIDIA T1200 4 GiB đạt khoảng 99% GPU và 3,9/4 GiB VRAM.
Technical smoke SadTalker 1,48 giây trước đó vẫn là bằng chứng adapter local chạy
được; long-render failure là giới hạn tài nguyên, không xóa bằng chứng đó.

D-ID hiện công bố:

- API trial 14 ngày, tổng tối đa 3 phút offline video, có watermark;
- mỗi output Studio/API tối đa 5 phút;
- API `POST /images` nhận JPEG/PNG vào temporary storage 24–48 giờ;
- `POST /talks` nhận `source_url` và text hoặc audio script;
- `GET /talks/{id}` trả trạng thái/output;
- API key dùng `Authorization: Basic API_USERNAME:API_PASSWORD`.

Nguồn chính thức cần kiểm tra lại tại thời điểm triển khai:

- https://www.d-id.com/pricing/api
- https://www.d-id.com/faqs/
- https://docs.d-id.com/reference/get-started
- https://docs.d-id.com/reference/upload-an-image
- https://docs.d-id.com/reference/upload-an-audio
- https://docs.d-id.com/reference/createtalk
- https://docs.d-id.com/reference/gettalk

## Việc người dùng chuẩn bị

1. Đăng ký trial và xem rõ ngày hết hạn, watermark, credit còn lại và điều khoản
   phi thương mại/cá nhân.
2. Dùng D-ID Studio tạo một clip 30 giây với portrait tổng hợp, nội dung PHP
   không nhạy cảm để kiểm tra tiếng Việt, moderation và lip-sync trước khi code.
3. Nếu clip đạt, tạo API key trong account settings. Chỉ đặt key vào
   `backend/.env`; không gửi key qua chat, không đặt trong `VITE_*`, không commit
   `.env`, ảnh/audio private hoặc raw provider response.
4. Trial chỉ có tổng 3 phút: sau smoke 30 giây, video cuối nên khoảng 2–2,5 phút.
   Nếu bắt buộc đúng 5 phút thì trial không đủ credit.

Biến môi trường dự kiến (tên cuối cùng phải được review trong code):

```env
VIDEO_GENERATION_PROVIDER=did
DID_API_KEY=
DID_API_BASE_URL=https://api.d-id.com
DID_TIMEOUT_SECONDS=300
```

## Vertical slice đề xuất

1. Giữ `sadtalker-local` là default và thêm provider `did`; không thay đổi RAG,
   assessment hoặc lesson readiness.
2. Chỉ teacher-owner/admin được tạo job. Bắt buộc summary hiện tại đã duyệt,
   portrait hợp lệ, quyền sử dụng và một xác nhận riêng rằng portrait/script hoặc
   audio sẽ được gửi tới D-ID và có thể tiêu tốn credit.
3. Upload portrait server-side tới `POST /images`; không cần public hóa media
   local. PoC đầu tiên nên dùng text script + standard Vietnamese voice nếu Studio
   smoke xác nhận voice phù hợp. Audio upload là fallback; endpoint hiện giới hạn
   file 6 MiB nên WAV dài 5 phút không phù hợp.
4. Tạo talk, lưu provider/external job ID bounded trong DB, rồi poll từ Celery.
   HTTP request chỉ enqueue và trả DB state; không chờ D-ID inline.
5. Khi D-ID hoàn thành, tải MP4 qua HTTPS với host allowlist, byte bound, timeout
   và MP4 signature validation; lưu bằng server-generated name rồi gắn
   `Lesson.video_file` như SadTalker.
6. Provider/mạng/credit/moderation failure phải map sang failure code và thông
   báo an toàn. Không log Authorization, raw response, signed URL, script/audio
   hoặc portrait. Xóa temporary provider image/audio khi API và lifecycle cho phép.
7. Video vẫn optional: failure không chặn learner đọc bài, dùng RAG hoặc làm bài.

## Test bắt buộc trước live call

- Ownership bị từ chối trước khi đọc/upload input.
- Thiếu cloud-consent hoặc key fail closed và không gọi mạng.
- Mock create/poll/success lưu đúng một bounded MP4 và idempotent khi task retry.
- Timeout, 401, 402 insufficient credit, 451 moderation, malformed JSON, URL/host
  không hợp lệ, oversized/non-MP4 output đều thành safe terminal state.
- Không có key/raw provider detail trong API response, log hoặc database.
- Một active job/lesson; queue retry không trừ credit bằng cách create trùng.
- Full backend suite, Django check/migration drift, frontend lint/build pass.

## Live smoke có kiểm soát

Chỉ chạy sau khi user xác nhận key/credit/privacy/cost. Bắt đầu bằng tối đa 30
giây, portrait hư cấu và lesson PHP không nhạy cảm. Ghi provider job ID, thời gian,
duration, watermark, kích thước output và review lip-sync/âm thanh; không ghi key,
signed URL hoặc input private. Không tự chạy lại request có thể tính credit.

