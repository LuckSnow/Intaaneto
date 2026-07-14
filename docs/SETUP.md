# Thiết lập Intaaneto

Docker Compose là cách khởi động được khuyến nghị vì backend cần PostgreSQL.
Các lệnh trong tài liệu này phải chạy từ thư mục gốc của repository.

## Cách 1: Docker Desktop (khuyến nghị)

Yêu cầu: Docker Desktop đang chạy và đã bật WSL integration nếu dùng Windows/WSL.

```bash
cp backend/.env.example backend/.env
docker compose up -d --build --force-recreate
docker compose ps
```

Trên Windows Command Prompt, dùng `copy backend\.env.example backend\.env` thay
cho `cp`. Có thể để trống `OPENAI_API_KEY` khi chỉ kiểm tra web; endpoint AI sẽ
không hoạt động cho tới khi có khóa hợp lệ. Không đặt khóa bí mật vào biến
`VITE_*` vì các biến đó được đóng gói vào trình duyệt.

Compose khởi động theo thứ tự `db -> backend khỏe mạnh -> frontend`. Backend tự
chạy các migration đã commit khi container khởi động. Tạo tài khoản quản trị bằng:

```bash
docker compose exec backend python manage.py createsuperuser
```
=> superadmin@intaaneto.com
Tên đăng nhập: SuAdmin
Mật khẩu: 12345678
Full name: Supreme Admin

Các địa chỉ:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/api/
- Django admin: http://localhost:8000/admin/
- Swagger: http://localhost:8000/api/docs/
- Adminer: http://localhost:8888

## Khi bấm Start trong Docker Desktop nhưng frontend/backend tắt ngay

Không chỉ start riêng hai container cũ. Chúng phụ thuộc vào database, healthcheck
và bind mount của repository. Sau khi Docker Desktop hoặc WSL được khởi động lại,
container cũ đôi khi còn giữ mount không hợp lệ và báo thiếu `/app/manage.py` hoặc
`/app/package.json` dù file vẫn tồn tại trên máy.

Recreate từ đúng thư mục repository; lệnh này không xóa volume database:

```bash
docker compose up -d --build --force-recreate db backend frontend
docker compose ps
docker compose logs --tail 100 backend frontend
```

Chỉ dùng `docker compose down -v` khi chủ động muốn xóa toàn bộ database.

## Cách 2: Chạy trực tiếp trên máy

Yêu cầu: Python 3.11+, Node.js 20+, npm và PostgreSQL đang chạy. Copy rồi chỉnh
`backend/.env`; với cách này `DB_HOST=localhost`.

Linux/macOS/WSL:

```bash
./setup.sh
./start.sh
```

Windows Command Prompt:

```bat
setup.bat
start.bat
```

Các script tạo virtual environment, cài dependency theo lockfile và chạy
`migrate`. Không chạy `makemigrations` trong bước setup; chỉ tạo migration khi
chủ động thay đổi model.

## Kiểm tra sau setup

```bash
docker compose ps
docker compose exec backend python manage.py check
docker compose exec backend python manage.py showmigrations
```

Nếu một service lỗi, xem log của chính service đó:

```bash
docker compose logs --tail 100 db
docker compose logs --tail 100 backend
docker compose logs --tail 100 frontend
```
