# 🚀 HƯỚNG DẪN SETUP DỰ ÁN - INTAANETO

## ✅ Checklist Setup

### Bước 1: Setup Backend Django

```bash
# Di chuyển vào thư mục backend
cd d:\Intaaneto\backend

# Tạo virtual environment
python -m venv venv

# Kích hoạt virtual environment
venv\Scripts\activate

# Cài đặt dependencies
pip install -r requirements.txt

# Copy file .env.example thành .env
copy .env.example .env
```

**📝 Chỉnh sửa file backend/.env:**
```env
SECRET_KEY=django-insecure-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL Database
DB_NAME=intaaneto_db
DB_USER=postgres
DB_PASSWORD=123456  # Đổi password của bạn
DB_HOST=localhost
DB_PORT=5432

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# OpenAI API Key (lấy tại https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-your-api-key-here
```

### Bước 2: Setup PostgreSQL Database

**Cách 1: Cài đặt PostgreSQL local**
1. Download PostgreSQL 15: https://www.postgresql.org/download/
2. Cài đặt và nhớ password
3. Mở pgAdmin hoặc psql
4. Tạo database:
```sql
CREATE DATABASE intaaneto_db;
```

**Cách 2: Dùng Docker**
```bash
docker run --name intaaneto_postgres -e POSTGRES_DB=intaaneto_db -e POSTGRES_PASSWORD=123456 -p 5432:5432 -d postgres:15
```

### Bước 3: Chạy Migrations

```bash
# Vẫn trong thư mục backend với venv đã activate
python manage.py makemigrations
python manage.py migrate
```

### Bước 4: Tạo Superuser (Admin)

```bash
python manage.py createsuperuser
```

Nhập thông tin:
- Email: admin@example.com
- Username: admin
- Full name: Admin User
- Password: (tối thiểu 8 ký tự)

### Bước 5: Chạy Backend Server

```bash
python manage.py runserver
```

✅ Backend đang chạy tại: http://localhost:8000
✅ Admin panel: http://localhost:8000/admin
✅ API Docs: http://localhost:8000/api/docs/

---

### Bước 6: Setup Frontend React

**Mở terminal mới**, giữ backend chạy:

```bash
# Di chuyển vào thư mục frontend
cd d:\Intaaneto\frontend

# Cài đặt dependencies
npm install

# Copy file .env.example thành .env
copy .env.example .env
```

**📝 File frontend/.env đã OK, không cần sửa:**
```env
VITE_API_URL=http://localhost:8000/api
```

### Bước 7: Chạy Frontend Server

```bash
npm run dev
```

✅ Frontend đang chạy tại: http://localhost:5173

---

## 🎉 HOÀN TẤT SETUP!

Bây giờ bạn có:
- ✅ Backend API: http://localhost:8000
- ✅ Frontend: http://localhost:5173
- ✅ Admin panel: http://localhost:8000/admin
- ✅ API Documentation: http://localhost:8000/api/docs/

---

## 📚 Bước Tiếp Theo

### 1. Tạo dữ liệu mẫu trong Admin

1. Truy cập http://localhost:8000/admin
2. Đăng nhập bằng superuser vừa tạo
3. Tạo:
   - **Users**: Tạo thêm học sinh, giáo viên test
   - **Courses**: Tạo khóa học HTML/CSS/JS
   - **Lessons**: Tạo bài giảng trong khóa học
   - **Exercises**: Tạo bài tập

### 2. Test Frontend

1. Truy cập http://localhost:5173
2. Click "Đăng ký" để tạo tài khoản học sinh
3. Đăng nhập
4. Test các chức năng

### 3. Test AI Assistant

**⚠️ Quan trọng**: Cần có OpenAI API key hợp lệ trong backend/.env

```bash
# Test trong Python shell
cd backend
python manage.py shell
```

```python
from apps.ai_assistant.services import AIService

# Test chat
response = AIService.chat([
    {"role": "user", "content": "Giải thích HTML là gì?"}
])
print(response)
```

---

## 🐛 Troubleshooting

### Lỗi: "No module named 'xxx'"
```bash
cd backend
venv\Scripts\activate
pip install -r requirements.txt
```

### Lỗi: Database connection failed
- Kiểm tra PostgreSQL đang chạy
- Kiểm tra thông tin DB trong .env
- Test connection:
```bash
python manage.py dbshell
```

### Lỗi: CORS error ở frontend
- Kiểm tra CORS_ALLOWED_ORIGINS trong backend/.env
- Restart backend server

### Lỗi: npm install failed
```bash
# Xóa node_modules và thử lại
cd frontend
rmdir /s node_modules
npm install
```

### OpenAI API không hoạt động
- Kiểm tra API key hợp lệ
- Kiểm tra credit còn trong tài khoản OpenAI
- Test với curl:
```bash
curl https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

---

## 📱 Chạy với Docker (Alternative)

Nếu muốn dùng Docker thay vì setup thủ công:

```bash
# Build và start tất cả services
docker-compose up -d

# Xem logs
docker-compose logs -f

# Chạy migrations
docker-compose exec backend python manage.py migrate

# Tạo superuser
docker-compose exec backend python manage.py createsuperuser

# Stop services
docker-compose down
```

---

## 🔥 Tips Development

1. **Hot Reload**: Cả backend và frontend đều có hot reload, chỉnh code sẽ tự động refresh

2. **Debug Backend**:
```python
# Thêm vào code để debug
import pdb; pdb.set_trace()
```

3. **Debug Frontend**:
- Dùng React DevTools extension
- Console.log() trong code
- Xem Network tab để check API calls

4. **Database GUI**:
- pgAdmin: https://www.pgadmin.org/
- DBeaver: https://dbeaver.io/

5. **API Testing**:
- Swagger UI: http://localhost:8000/api/docs/
- Postman: Import API endpoints
- Thunder Client (VS Code extension)

---

## 📞 Hỗ Trợ

Nếu gặp vấn đề:
1. Đọc error message kỹ
2. Google error message
3. Check docs trong thư mục `/docs`
4. Contact: n23dcpt054@student.ptithcm.edu.vn
