# Cloudflare R2 private media cho Intaaneto

Tài liệu này mô tả phần Cloudflare R2 đã được tích hợp ngày 2026-07-26. Mục tiêu
là đưa PDF, video, audio và media động ra khỏi web server mà không phá quyền
enrollment/ownership hiện có.

R2 là tùy chọn theo cấu hình. `STORAGE_BACKEND=local` dùng filesystem;
`STORAGE_BACKEND=r2` dùng bucket private. Test tự động luôn ép filesystem để
không chạm dữ liệu cloud.

## Kiến trúc và tài sản được bảo vệ

Default Django storage chứa PDF giáo viên, video/audio bài học, attachment,
avatar và ảnh diễn đàn. Bucket phải giữ private. Django tiếp tục quyết định ai
được đọc bài học; URL R2 ký tạm thời chỉ là bearer URL sau khi đã qua backend,
không phải quy tắc phân quyền.

Không bật `r2.dev` public URL và không nối public custom domain vào bucket này.

```text
Teacher upload / generated media
              |
              v
    Django kiểm tra quyền
              |
              v
   private Cloudflare R2  <---->  Celery worker
              |
        signed URL 5 phút
              |
              v
      người dùng đã được phép

PostgreSQL + pgvector vẫn lưu metadata, chunks và embeddings;
R2 không phải vector database.
```

## Thiết lập trên Cloudflare

1. Mở **Storage & databases → R2**, tạo Standard bucket, ví dụ
   `intaaneto-dev-private`.
2. Tạo R2 API token chỉ giới hạn trong bucket này, có quyền đọc/ghi object.
3. Giữ public development URL của bucket ở trạng thái tắt.
4. Tách riêng bucket, token và prefix development với production sau này.

## Cấu hình backend

Chỉ đặt các giá trị sau trong `backend/.env`. Không dùng `VITE_*` cho storage
secret.

```dotenv
STORAGE_BACKEND=r2
R2_STORAGE_ENABLED=True
R2_ACCOUNT_ID=your-cloudflare-account-id
R2_ACCESS_KEY_ID=your-bucket-token-access-key
R2_SECRET_ACCESS_KEY=your-bucket-token-secret
R2_BUCKET_NAME=intaaneto-dev-private
R2_ENDPOINT_URL=https://your-account-id.r2.cloudflarestorage.com
R2_REGION=auto
R2_OBJECT_PREFIX=dev/private-media
R2_SIGNED_URL_EXPIRE_SECONDS=300
```

Restart cả `backend` và `worker`; hai service phải dùng cùng bucket. Nếu bật R2
nhưng thiếu credential, Django chủ động không khởi động. Không đặt access key hay
secret trong `VITE_*`, frontend bundle, log hoặc response API.

Environment cũ đã có `STORAGE_BACKEND=r2` sẽ tự bật R2. Biến
`R2_STORAGE_ENABLED` là override rõ ràng khi cần ép local hoặc R2 tạm thời.

Object mới giữ thư mục logic như `courses/uploads/`, nhưng filename do server
sinh bằng UUID; tên file người dùng không trở thành object key. URL đọc mặc định
hết hạn sau 300 giây và object có cache metadata `private`.

## Trình duyệt và CORS

Trình xem PDF hiện tải qua endpoint bài học đã kiểm tra quyền của Django nên
không cần browser-to-R2 CORS. Thẻ ảnh/video có thể tải signed URL trực tiếp. Nếu
luồng tương lai dùng JavaScript `fetch` hoặc upload trực tiếp lên R2, CORS của
bucket chỉ được cho phép chính xác frontend origin, method và header cần dùng.

## Migration đã thực hiện

Ngày 2026-07-26:

- Local volume có 525 file, tổng khoảng 52.6 MB.
- Database tham chiếu 22 giá trị media duy nhất.
- 17 file local thật sự còn được tham chiếu, khoảng 50.4 MB, đã được copy lên R2
  và kiểm tra tồn tại thành công.
- 5 giá trị còn lại là thumbnail khóa học dùng URL Unsplash bên ngoài, không
  phải local file bị mất và không cần copy vào R2.
- Không xóa file local sau migration; volume local hiện là bản rollback.
- Smoke test R2 đã ghi, đọc, tạo signed URL, xóa và xác nhận object chẩn đoán
  không còn tồn tại. Không log object key, URL ký hoặc credential.

Các file local không còn được database tham chiếu chưa bị xóa. Chỉ cleanup sau
khi có chính sách retention/orphan rõ ràng và backup được kiểm tra.

## Kiểm tra vận hành

1. Upload PDF bằng đúng giáo viên sở hữu và chờ indexing hoàn tất.
2. Kiểm tra object key bắt đầu bằng environment prefix đã cấu hình và dùng UUID
   thay vì filename người dùng gửi lên.
3. Kiểm tra bucket và `r2.dev` vẫn private.
4. Kiểm tra học viên đã enrollment xem được PDF bài học.
5. Kiểm tra học viên chưa enrollment và giáo viên khác không nhận được byte PDF.
6. Kiểm tra video slide sinh thành công, được upload và chỉ người có quyền bài
   học mới xem được.
7. Kiểm tra URL hết hạn đúng cấu hình và không chứa R2 secret.

Các lệnh kiểm tra code đã chạy tại thời điểm bàn giao:

```bash
docker compose run --rm backend pytest -q
docker compose run --rm backend python manage.py check
docker compose run --rm backend python manage.py makemigrations --check --dry-run
cd frontend && npm run lint && npm run build
```

Kết quả: 266 backend tests pass; frontend lint/build pass; không phát sinh
migration Django.

## Rollback về local

1. Giữ nguyên named volume `media_files`.
2. Đặt `STORAGE_BACKEND=local` hoặc `R2_STORAGE_ENABLED=False` trong
   `backend/.env`.
3. Recreate đồng thời backend và worker:

```bash
docker compose up -d --force-recreate backend worker
```

Rollback chỉ an toàn khi các object mới tạo sau lúc bật R2 cũng đã được copy về
local. Vì vậy không dùng rollback local như quy trình thường ngày sau khi hệ
thống bắt đầu nhận upload mới.

## Không được làm

- Không public toàn bucket hoặc `/media/`.
- Không dùng URL public cố định cho PDF/video bài học riêng tư.
- Không tin `lesson_id`, `course_id` hoặc object key do frontend gửi lên để mở
  rộng phạm vi đọc.
- Không cho frontend giữ R2 secret hay tự ký URL.
- Không gọi `.path` trực tiếp trên remote `FileField`; media processor phải dùng
  temporary file có giới hạn và xóa sau xử lý.
- Không xóa volume local hoặc orphan hàng loạt trước khi kiểm tra backup và
  retention.
