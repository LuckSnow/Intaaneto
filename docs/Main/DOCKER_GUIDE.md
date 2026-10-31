# Docker guide

## Các service

| Service | Container | Port | Vai trò |
|---|---|---:|---|
| `db` | `intaaneto_db` | 5434 | PostgreSQL 15 (container: 5432) |
| `backend` | `intaaneto_backend` | 8000 | Django development server |
| `frontend` | `intaaneto_frontend` | 5173 | Vite development server |
| `adminer` | `intaaneto_adminer` | 8888 | Giao diện quản trị database |

Cấu hình này chỉ dành cho development. Password database trong Compose không
được dùng cho production.

## Vòng đời thông thường

```bash
# Build và chạy
docker compose up -d --build

# Trạng thái và log
docker compose ps
docker compose logs -f backend frontend

# Dừng nhưng giữ database
docker compose down

# Recreate sau khi Docker Desktop/WSL bị restart hoặc bind mount lỗi
docker compose up -d --build --force-recreate
```

Backend tự chạy `python manage.py migrate` trước server. Không chạy
`makemigrations` trong quy trình deploy/start; migration phải được tạo, review và
commit cùng thay đổi model.

## Biến môi trường

Compose đọc `backend/.env` nếu file tồn tại, sau đó ghi đè các thông số kết nối
database cần thiết để backend dùng host `db`.

```bash
cp backend/.env.example backend/.env
```

`OPENAI_API_KEY` là tùy chọn cho việc khởi động web nhưng bắt buộc để gọi provider
AI thật. Giữ khóa ở backend; tuyệt đối không đưa vào `frontend/.env` hoặc commit.

## Quản trị Django và database

```bash
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py showmigrations
docker compose exec backend python manage.py check
docker compose exec db psql -U postgres -d intaaneto_db
```

Backup (chạy từ shell hỗ trợ redirect):

```bash
docker compose exec -T db pg_dump -U postgres intaaneto_db > backup.sql
```

Restore vào database development hiện tại:

```bash
docker compose exec -T db psql -U postgres intaaneto_db < backup.sql
```

## Chẩn đoán container không start

```bash
docker compose ps -a
docker compose logs --tail 100 db backend frontend
docker compose config
```

Các trường hợp thường gặp:

- Thiếu `/app/manage.py` hoặc `/app/package.json`: bind mount của container cũ
  không còn hợp lệ. Chạy `docker compose up -d --build --force-recreate` từ root.
- Backend chờ hoặc không kết nối DB: kiểm tra health/log của `db`; Compose dùng
  `DB_HOST=db`, không phải `localhost`.
- Port 5173, 8000, 8888 hoặc 5434 đã bị chiếm: dừng process/container đang dùng
  port hoặc đổi mapping trong Compose.
- Frontend thiếu package: rebuild frontend bằng
  `docker compose up -d --build --force-recreate frontend`.
- Backend không healthy: xem log migration trước; frontend được thiết kế chờ
  backend healthy rồi mới start.

Không dùng `docker compose down -v` để sửa lỗi khởi động thông thường vì tùy chọn
`-v` xóa dữ liệu PostgreSQL. Không fake/reset migration nếu chưa có backup và
chưa hiểu rõ migration conflict.

## Kiểm tra code trong container

```bash
docker compose exec backend pytest
docker compose exec frontend npm run lint
docker compose exec frontend npm run build
```
