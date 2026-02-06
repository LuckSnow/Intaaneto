# 🐳 Hướng Dẫn Sử Dụng Docker - Intaaneto Project

## 📋 Mục Lục
- [Khởi Động Dự Án](#khởi-động-dự-án)
- [Dừng và Khởi Động Lại](#dừng-và-khởi-động-lại)
- [Xem Logs](#xem-logs)
- [Quản Lý Database](#quản-lý-database)
- [Quản Lý User](#quản-lý-user)
- [Xử Lý Lỗi Thường Gặp](#xử-lý-lỗi-thường-gặp)
- [Các Lệnh Hữu Ích](#các-lệnh-hữu-ích)

---

## 🚀 Khởi Động Dự Án

### Lần đầu tiên khởi động:
```bash
# 1. Build và khởi động tất cả containers
docker compose up -d --build

# 2. Đợi containers khởi động (khoảng 10-15 giây)

# 3. Tạo migrations cho database
docker compose exec backend python manage.py makemigrations

# 4. Apply migrations
docker compose exec backend python manage.py migrate

# 5. Tạo superuser (admin)
docker compose exec backend python manage.py shell -c "from apps.users.models import User; User.objects.create_superuser(email='admin@intaaneto.com', username='admin', password='admin123', full_name='Administrator')"
```

### Các lần sau:
```bash
# Khởi động tất cả services
docker compose up -d
```

---

## 🛑 Dừng và Khởi Động Lại

### Dừng tất cả containers (giữ nguyên data):
```bash
docker compose down
```

### Dừng và XÓA TOÀN BỘ data (database, volumes):
```bash
docker compose down -v
```
⚠️ **Cảnh báo:** Lệnh này sẽ xóa toàn bộ dữ liệu database!

### Khởi động lại containers:
```bash
docker compose restart
```

### Khởi động lại một service cụ thể:
```bash
docker compose restart backend
docker compose restart frontend
docker compose restart db
```

### Rebuild và khởi động lại:
```bash
docker compose down
docker compose up -d --build
```

---

## 📊 Xem Logs

### Xem logs tất cả services:
```bash
docker compose logs
```

### Xem logs real-time (follow):
```bash
docker compose logs -f
```

### Xem logs của service cụ thể:
```bash
# Backend
docker compose logs backend

# Frontend
docker compose logs frontend

# Database
docker compose logs db

# Real-time logs
docker compose logs -f backend
```

### Xem 20 dòng logs mới nhất:
```bash
docker compose logs backend --tail 20
```

---

## 💾 Quản Lý Database

### Chạy migrations:
```bash
# Tạo migration files
docker compose exec backend python manage.py makemigrations

# Apply migrations vào database
docker compose exec backend python manage.py migrate

# Tạo migrations cho app cụ thể
docker compose exec backend python manage.py makemigrations users
```

### Xem migrations:
```bash
# Xem danh sách migrations
docker compose exec backend python manage.py showmigrations

# Xem SQL của migration
docker compose exec backend python manage.py sqlmigrate users 0001
```

### Truy cập PostgreSQL shell:
```bash
# Truy cập psql
docker compose exec db psql -U postgres -d intaaneto_db

# Các lệnh SQL trong psql:
# \dt                 - Xem danh sách tables
# \d users_user       - Xem cấu trúc table
# SELECT * FROM users_user;  - Query data
# \q                  - Thoát
```

### Backup database:
```bash
# Backup
docker compose exec db pg_dump -U postgres intaaneto_db > backup.sql

# Restore
docker compose exec -T db psql -U postgres intaaneto_db < backup.sql
```

---

## 👤 Quản Lý User

### Tạo superuser mới:
```bash
# Cách 1: Interactive (nhập từng field)
docker compose exec backend python manage.py createsuperuser

# Cách 2: Một lệnh (nhanh)
docker compose exec backend python manage.py shell -c "from apps.users.models import User; User.objects.create_superuser(email='admin@example.com', username='admin', password='yourpassword', full_name='Admin Name')"
```

### Đổi mật khẩu user:
```bash
docker compose exec backend python manage.py changepassword admin@intaaneto.com
```

### Reset mật khẩu bằng Django shell:
```bash
docker compose exec backend python manage.py shell

# Trong shell Python:
from apps.users.models import User
user = User.objects.get(email='admin@intaaneto.com')
user.set_password('new_password_123')
user.save()
exit()
```

### Xem danh sách users:
```bash
docker compose exec backend python manage.py shell -c "from apps.users.models import User; print('\n'.join([f'{u.email} - {u.username} - {u.role}' for u in User.objects.all()]))"
```

---

## 🔧 Xử Lý Lỗi Thường Gặp

### ❌ Lỗi: "Cannot connect to database"
```bash
# Giải pháp: Restart tất cả containers
docker compose down
docker compose up -d

# Kiểm tra database có chạy không
docker compose ps
docker compose logs db
```

### ❌ Lỗi: "Port already in use"
```bash
# Xem process nào đang dùng port
netstat -ano | findstr :8000
netstat -ano | findstr :5173

# Tắt process hoặc đổi port trong docker-compose.yml
```

### ❌ Lỗi: "Module not found" (Frontend)
```bash
# Rebuild frontend container
docker compose down frontend
docker compose up -d --build frontend
```

### ❌ Lỗi: "Migration conflicts"
```bash
# Xem trạng thái migrations
docker compose exec backend python manage.py showmigrations

# Reset migrations (XÓA DATA!)
docker compose exec backend python manage.py migrate --fake [app_name] zero
docker compose exec backend python manage.py migrate [app_name]
```

### ❌ Quên mật khẩu admin:
```bash
# Đổi mật khẩu
docker compose exec backend python manage.py changepassword admin@intaaneto.com

# Hoặc tạo superuser mới
docker compose exec backend python manage.py createsuperuser
```

### ❌ Container liên tục restart:
```bash
# Xem logs để tìm lỗi
docker compose logs backend --tail 50

# Rebuild container
docker compose down
docker compose up -d --build
```

---

## 🛠️ Các Lệnh Hữu Ích

### Kiểm tra trạng thái:
```bash
# Xem trạng thái containers
docker compose ps

# Xem resource usage
docker stats

# Xem images
docker images

# Xem networks
docker network ls
```

### Truy cập shell trong container:
```bash
# Backend (Python/Django shell)
docker compose exec backend bash
docker compose exec backend python manage.py shell

# Frontend (Node.js shell)
docker compose exec frontend sh

# Database (PostgreSQL shell)
docker compose exec db psql -U postgres -d intaaneto_db
```

### Chạy Django management commands:
```bash
# Collect static files
docker compose exec backend python manage.py collectstatic --noinput

# Tạo dummy data
docker compose exec backend python manage.py loaddata fixtures/sample_data.json

# Chạy tests
docker compose exec backend python manage.py test

# Chạy specific test
docker compose exec backend python manage.py test apps.users.tests
```

### Frontend commands:
```bash
# Install package mới
docker compose exec frontend npm install [package-name]

# Build production
docker compose exec frontend npm run build

# Lint code
docker compose exec frontend npm run lint
```

### Dọn dẹp Docker:
```bash
# Xóa containers không dùng
docker container prune

# Xóa images không dùng
docker image prune

# Xóa volumes không dùng
docker volume prune

# Xóa TẤT CẢ (NGUY HIỂM!)
docker system prune -a --volumes
```

---

## 🌐 Các URLs Quan Trọng

| Service | URL | Mô tả |
|---------|-----|-------|
| Frontend | http://localhost:5173 | React app |
| Backend API | http://localhost:8000/api | REST API |
| Django Admin | http://localhost:8000/admin | Admin panel |
| API Docs (Swagger) | http://localhost:8000/api/docs | Interactive API docs |
| API Docs (ReDoc) | http://localhost:8000/api/redoc | Alternative API docs |
| PostgreSQL | localhost:5434 | Database (external port) |

### Thông tin đăng nhập mặc định:
- **Email**: admin@intaaneto.com
- **Password**: admin123 (hoặc password bạn đã đổi)

---

## 📦 Cấu Trúc Docker

### Services trong docker-compose.yml:
- **db**: PostgreSQL 15 database
- **backend**: Django REST API (Python 3.11)
- **frontend**: React + Vite app (Node 20)

### Volumes (data persistence):
- **postgres_data**: Database data
- **media_files**: User uploads
- **static_files**: Static assets

### Networks:
- **intaaneto_network**: Bridge network kết nối các containers

---

## 🔄 Workflow Phát Triển

### 1. Bắt đầu làm việc:
```bash
docker compose up -d
docker compose logs -f backend
```

### 2. Thay đổi code:
- Backend: Code tự reload (Django development server)
- Frontend: Code tự reload (Vite HMR)

### 3. Thêm dependencies mới:

**Backend:**
```bash
# Thêm vào requirements.txt
docker compose down backend
docker compose up -d --build backend
```

**Frontend:**
```bash
# Cách 1: Trong container
docker compose exec frontend npm install [package]

# Cách 2: Rebuild
# Thêm vào package.json
docker compose down frontend
docker compose up -d --build frontend
```

### 4. Chạy migrations sau khi sửa models:
```bash
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate
```

### 5. Kết thúc làm việc:
```bash
# Dừng containers (giữ data)
docker compose down

# Hoặc để chạy trong background
# Không cần dừng
```

---

## 💡 Tips & Tricks

### Tăng tốc độ build:
- Sử dụng `.dockerignore` để exclude files không cần thiết
- Cache layers bằng cách tổ chức Dockerfile đúng cách

### Debug hiệu quả:
```bash
# Xem logs real-time nhiều services
docker compose logs -f backend frontend

# Theo dõi database queries
docker compose exec backend python manage.py shell
# Trong shell:
from django.db import connection
from django.db import reset_queries
import logging
l = logging.getLogger('django.db.backends')
l.setLevel(logging.DEBUG)
l.addHandler(logging.StreamHandler())
```

### Hot reload không hoạt động:
```bash
# Restart service
docker compose restart backend

# Rebuild nếu cần
docker compose up -d --build backend
```

---

## 📞 Trợ Giúp

Nếu gặp vấn đề:
1. Kiểm tra logs: `docker compose logs [service]`
2. Kiểm tra trạng thái: `docker compose ps`
3. Restart services: `docker compose restart`
4. Rebuild nếu cần: `docker compose up -d --build`

---

*Cập nhật lần cuối: 05/02/2026*
