# Google OAuth Setup Guide

## Hướng dẫn cấu hình Google OAuth cho đăng nhập

### Bước 1: Tạo Google Cloud Project

1. Truy cập [Google Cloud Console](https://console.cloud.google.com/)
2. Tạo project mới hoặc chọn project hiện có
3. Đặt tên project: **INTAANETO**

### Bước 2: Kích hoạt Google+ API

1. Vào **APIs & Services** > **Library**
2. Tìm kiếm **"Google+ API"**
3. Click **Enable**

### Bước 3: Tạo OAuth 2.0 Credentials

1. Vào **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. Nếu chưa có OAuth consent screen, click **Configure consent screen**:
   - User Type: **External**
   - App name: **INTAANETO**
   - User support email: your-email@gmail.com
   - Developer contact: your-email@gmail.com
   - Scopes: Thêm `email` và `profile`
   - Test users: Thêm email test của bạn

4. Tạo OAuth client ID:
   - Application type: **Web application**
   - Name: **INTAANETO Web Client**
   - Authorized JavaScript origins:
     - `http://localhost:5173`
     - `http://localhost:8000`
   - Authorized redirect URIs:
     - `http://localhost:8000/api/auth/google/callback/`
     - `http://localhost:8000/accounts/google/login/callback/`

5. Click **Create** và lưu lại:
   - **Client ID** (dạng: `xxxxx.apps.googleusercontent.com`)
   - **Client Secret**

### Bước 4: Cấu hình Backend

Mở file `backend/.env` và thêm:

```env
# Email Configuration (Gmail)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=noreply@intaaneto.com

# Frontend URL
FRONTEND_URL=http://localhost:5173

# Google OAuth
GOOGLE_OAUTH_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-secret-here
```

**Lưu ý về Gmail App Password:**
- Không dùng mật khẩu Gmail thông thường
- Tạo App Password tại: https://myaccount.google.com/apppasswords
- Bật 2-Step Verification trước khi tạo App Password

### Bước 5: Chạy Migrations

```bash
docker compose exec backend python manage.py migrate
```

### Bước 6: Tạo Social App trong Django Admin

1. Truy cập http://localhost:8000/admin/
2. Đăng nhập với admin account
3. Vào **Social applications** > **Add social application**
4. Điền thông tin:
   - Provider: **Google**
   - Name: **Google OAuth**
   - Client id: Paste Client ID từ Google Console
   - Secret key: Paste Client Secret
   - Sites: Chọn **example.com** (hoặc site bạn đã tạo)
5. Click **Save**

### Bước 7: Test

1. Khởi động lại backend:
```bash
docker compose restart backend
```

2. Truy cập http://localhost:5173/login
3. Click **"Đăng nhập với Google"**
4. Chọn Google account và cho phép quyền truy cập
5. Nếu thành công, bạn sẽ được redirect về dashboard

## Xử lý lỗi thường gặp

### Lỗi: `redirect_uri_mismatch`
- Kiểm tra lại **Authorized redirect URIs** trong Google Console
- Đảm bảo URL khớp chính xác (có/không có trailing slash)

### Lỗi: `invalid_client`
- Kiểm tra lại Client ID và Secret trong `.env`
- Đảm bảo không có khoảng trắng thừa

### Email không gửi được
- Kiểm tra Gmail App Password đã đúng chưa
- Kiểm tra 2-Step Verification đã bật chưa
- Test bằng cách đăng ký account mới

## Yêu cầu mật khẩu mạnh

Khi đăng ký bằng email/password, hệ thống yêu cầu:

✅ Tối thiểu **8 ký tự**  
✅ Có ít nhất **1 chữ hoa** (A-Z)  
✅ Có ít nhất **1 chữ thường** (a-z)  
✅ Có ít nhất **1 chữ số** (0-9)  
✅ Có ít nhất **1 ký tự đặc biệt** (!@#$%^&*...)

Ví dụ: `MyP@ssw0rd!`

## Email Verification

Sau khi đăng ký, user sẽ nhận email xác thực:
- Link có dạng: `http://localhost:5173/verify-email/{token}`
- Token có hiệu lực 24 giờ
- Sau khi verify, user có thể đăng nhập bình thường
