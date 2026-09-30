# Quick Tunnel cho demo Intaaneto

Tài liệu này dùng để chia sẻ bản Intaaneto đang chạy trên máy cá nhân trong một
buổi demo ngắn. Cloudflare Quick Tunnel cấp một URL HTTPS tạm thời và chuyển tiếp
nó vào Vite trên cổng `5173`.

```text
Internet
  -> Cloudflare Quick Tunnel
  -> localhost:5173 (Vite)
  -> /api và /media được proxy nội bộ tới backend:8000
```

Chỉ tunnel frontend. Không mở trực tiếp backend `8000`, Adminer `8888`,
PostgreSQL hoặc Redis ra Internet.

## Chuẩn bị

- Docker và Docker Compose đang hoạt động.
- Máy có Node.js/npm để chạy `npx`.
- Chạy lệnh từ thư mục gốc của repository.
- Dùng dữ liệu và tài khoản demo, không dùng dữ liệu nhạy cảm.

Khởi động stack local và kiểm tra trạng thái:

```bash
docker compose up -d
docker compose ps
```

## Bật tunnel

Mở terminal thứ nhất và giữ terminal này chạy trong suốt buổi demo:

```bash
npx wrangler tunnel quick-start http://localhost:5173
```

Lần đầu chạy, `npx` có thể hỏi quyền tải Wrangler/cloudflared. Sau khi tunnel
khởi động, terminal sẽ hiện một URL dạng:

```text
https://random-words.trycloudflare.com
```

Sao chép phần hostname, bỏ `https://`. Mở terminal thứ hai và chạy:

```bash
export DEMO_TUNNEL_HOST=random-words.trycloudflare.com
docker compose -f docker-compose.yml -f docker-compose.demo.yml \
  up -d --force-recreate backend frontend
```

Mở `https://${DEMO_TUNNEL_HOST}` trên trình duyệt hoặc gửi URL đầy đủ cho người
test. Có thể smoke-test trước khi gửi:

```bash
curl -sS -o /dev/null -w 'Trang chủ: %{http_code}\n' \
  "https://${DEMO_TUNNEL_HOST}/"
curl -sS -o /dev/null -w 'Courses API: %{http_code}\n' \
  "https://${DEMO_TUNNEL_HOST}/api/courses/"
```

Mã `200` cho biết route public tương ứng đang truy cập được. Các API yêu cầu
đăng nhập trả `401` khi chưa có token là đúng hành vi.

## Google Login và Firebase

Đăng nhập bằng email/mật khẩu hoạt động ngay qua tunnel. Để popup Google Login
hoạt động, thêm chính xác hostname mới vào:

`Firebase Console -> Authentication -> Settings -> Authorized domains`

Chỉ nhập `random-words.trycloudflare.com`, không nhập `https://` hoặc đường dẫn.
Quick Tunnel thường cấp hostname mới sau mỗi lần bật lại, vì vậy bước này phải
lặp lại cho URL mới.

## Email xác thực và quên mật khẩu

Khi backend được recreate với `DEMO_TUNNEL_HOST`, email xác thực và email đặt
lại mật khẩu mới sẽ chứa URL HTTPS public. Không cần đưa khóa Mailjet hay bất kỳ
secret nào vào frontend.

Lưu ý:

- Link đã tạo bằng hostname tunnel cũ sẽ không dùng được sau khi tunnel đó dừng.
  Hãy yêu cầu gửi lại email sau khi tunnel mới hoạt động.
- Thư vào Spam hoặc hiển thị “qua Mailjet” là vấn đề uy tín sender/domain, không
  phải lỗi tunnel.
- Không in, chụp hoặc gửi nội dung `backend/.env` cho người test.

## Tắt tunnel

Trong terminal đang chạy tunnel, nhấn `Ctrl+C`. Sau đó khôi phục frontend và
backend về cấu hình localhost:

```bash
docker compose up -d --force-recreate backend frontend
```

Tắt máy, tắt WSL hoặc đóng tiến trình tunnel cũng làm URL public ngừng hoạt
động. Không cần xóa container hay database. Đặc biệt, không chạy
`docker compose down -v`, vì tùy chọn `-v` có thể xóa dữ liệu trong volume.

## Bật lại sau này

Mỗi lần bật lại:

1. Chạy `docker compose up -d`.
2. Chạy lại lệnh `npx wrangler tunnel quick-start ...`.
3. Lấy hostname mới và export `DEMO_TUNNEL_HOST`.
4. Chạy lại Compose với `docker-compose.demo.yml`.
5. Nếu dùng Google Login, thêm hostname mới vào Firebase Authorized domains.
6. Gửi lại email xác thực/reset nếu người test đang giữ link của tunnel cũ.
# Hoac la dung lenh sau:
~/.config/.wrangler/cloudflared/2026.7.2/cloudflared \
  tunnel --url http://localhost:5173 
# Neu gap loi QUIC/UDP dung http/2
~/.config/.wrangler/cloudflared/2026.7.2/cloudflared \
  tunnel --protocol http2 \
  --url http://localhost:5173
  
Không hard-code URL Quick Tunnel vào source hoặc `.env.example`; URL này chỉ là
địa chỉ tạm thời của từng phiên demo.

## Xử lý lỗi nhanh

### URL public báo lỗi hoặc không tải được

Kiểm tra terminal tunnel còn chạy và Vite đang lắng nghe ở cổng `5173`:

```bash
docker compose ps
```

Nếu đã đóng terminal tunnel, chạy lại toàn bộ mục “Bật tunnel”.

### Vite báo blocked host

Hostname trong container frontend chưa khớp URL mới. Export đúng hostname,
không kèm `https://`, rồi recreate lại:

```bash
docker compose -f docker-compose.yml -f docker-compose.demo.yml \
  up -d --force-recreate backend frontend
```

### Giao diện mở được nhưng API lỗi

Đảm bảo đã dùng cả hai file Compose và route trình duyệt gọi `/api/...`, không
gọi `localhost:8000`. Xem log không kèm secret:

```bash
docker compose logs --tail=100 frontend backend
```

### Google báo `auth/unauthorized-domain`

Thêm hostname hiện tại vào Firebase Authorized domains rồi thử lại. URL mới
không tự kế thừa quyền của URL tunnel cũ.

### Email vẫn trỏ về localhost hoặc URL cũ

Recreate backend với `DEMO_TUNNEL_HOST` hiện tại, sau đó gửi một email xác thực
hoặc reset mới:

```bash
docker compose -f docker-compose.yml -f docker-compose.demo.yml \
  up -d --force-recreate backend
```

### Local bị lỗi sau khi tắt tunnel

Khôi phục cấu hình base:

```bash
docker compose up -d --force-recreate backend frontend
```

## Giới hạn của Quick Tunnel

Quick Tunnel phù hợp để bạn bè kiểm thử trong thời gian ngắn, không phải môi
trường staging hoặc production: URL thay đổi, không có cam kết uptime và phụ
thuộc máy cá nhân còn bật. Sau buổi demo nên dừng tunnel; nếu cần một URL ổn
định, hãy chuyển sang named tunnel hoặc triển khai staging riêng.
