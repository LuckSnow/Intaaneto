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

Nhập email, username, full name và một mật khẩu mạnh riêng trên từng máy. Không
dùng hoặc ghi một mật khẩu quản trị mặc định trong repository.

## Tạo dữ liệu mẫu dùng chung

Không copy Docker volume hoặc dump toàn bộ database development sang máy khác vì
chúng có thể chứa tài khoản, chat, uploads và vectors cục bộ. Repository cung cấp
command idempotent để mỗi thành viên tự tạo cùng một bộ dữ liệu demo an toàn:

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_demo_data
```

Command tạo một giảng viên demo, một học viên đã enroll, course `Demo AI Tutor
với RAG` và lesson `RAG là gì?`. Chạy lại command sẽ cập nhật đúng bộ dữ liệu đó
thay vì tạo duplicate. Command không tạo uploads, chat history hoặc vector index.

Mặc định hai tài khoản có password không sử dụng được. Nếu cần đăng nhập, mỗi
developer tự đặt các giá trị sau trong `backend/.env`; không commit hoặc gửi các
password này qua Git:

```env
DEMO_TEACHER_PASSWORD=your-local-teacher-password
DEMO_STUDENT_PASSWORD=your-local-student-password
```

Nếu container backend đã được tạo trước khi thêm các biến trên, recreate để Docker
nạp lại `.env`:

```bash
docker compose up -d --force-recreate backend
docker compose exec backend python manage.py seed_demo_data
```

Tài khoản demo:

- Teacher: `demo.teacher@example.invalid`
- Student: `demo.student@example.invalid`

Cuối output của `seed_demo_data` có lệnh `index_lesson` với ID đúng trên database
của từng máy. Chỉ chạy lệnh đó khi muốn kiểm tra RAG vì lần đầu có thể phải tải
embedding model local.

Sau khi seed và index lesson demo, có thể chạy bộ đánh giá retrieval tiếng Việt
đã version hóa bằng ID lesson và ID teacher mà command seed vừa in ra:

```bash
LESSON_ID=123 TEACHER_ID=45
docker compose exec backend python manage.py evaluate_rag_retrieval "$LESSON_ID" --actor-id "$TEACHER_ID"
```

Thay `123` và `45` bằng các ID tương ứng trong output của `seed_demo_data`.

Command chỉ đánh giá retrieval trong lesson mà actor được phép đọc; nó không gọi
mô hình sinh câu trả lời. Báo cáo JSON ghi dataset/config version, accuracy,
expected-source recall, latency và kết quả theo ID ca kiểm thử, không in raw chunk,
embedding hay provider diagnostics. Nếu nội dung demo vừa được cập nhật, chạy lại
`index_lesson` trước khi đánh giá để tạo source version hiện hành.

## Nhập kho học liệu Markdown

Hai bản thảo `docs/computer-networks.md` và `docs/web-programming.md` được biên
tập thành 2 khóa học gồm 15 bài có mục tiêu và nguồn tham khảo. Docker chỉ mount
thư mục này vào backend ở chế độ read-only. Luôn kiểm tra cấu trúc trước; lệnh
sau không đọc hoặc ghi database:

```bash
docker compose exec backend python manage.py import_learning_corpus --dry-run
```

Sau khi một giảng viên active, đã xác thực email và có role `teacher` duyệt nội
dung, nhập các khóa/bài ở trạng thái nháp bằng ID của giảng viên:

```bash
docker compose exec backend python manage.py import_learning_corpus --teacher-id 45
```

Lệnh có tính idempotent, không xóa dữ liệu và từ chối ghi đè bài tạo thủ công
hoặc bài PDF. Output in checksum cùng lệnh `index_lesson` cho từng bài, nhưng
không tự lập chỉ mục. Giảng viên cần rà soát trong Django admin trước, rồi mới
chủ động publish và index. Chỉ dùng `--publish` khi đã duyệt toàn bộ corpus:

```bash
docker compose exec backend python manage.py import_learning_corpus --teacher-id 45 --publish
```

Chạy lại không có `--publish` sẽ giữ nguyên bài đã xuất bản, không tự unpublish.
Không đưa đáp án bài đánh giá vào các file học liệu vì nội dung này sẽ được RAG
lập chỉ mục và hiển thị làm nguồn trích dẫn.

## PoC video SadTalker

SadTalker local không cần API key và không được cài chung vào backend mặc định.
Adapter thủ công, giới hạn input, audit job, cấu hình runtime tách biệt và mẫu
biên bản smoke được mô tả tại [SADTALKER_POC.md](SADTALKER_POC.md). Chưa có bằng
chứng render GPU thật thì không được ghi nhận video tutor là đã hoàn thành.

## Email xác thực và Mailjet

Môi trường development mặc định in email xác thực vào console backend. Để gửi
qua Mailjet, đặt ba giá trị sau trong `backend/.env` rồi recreate backend; không
đặt các key này trong biến `VITE_*` hoặc commit file `.env`:

```env
EMAIL_BACKEND=anymail.backends.mailjet.EmailBackend
MAILJET_API_KEY=your-local-mailjet-api-key
MAILJET_SECRET_KEY=your-local-mailjet-secret-key
```

Địa chỉ `DEFAULT_FROM_EMAIL` phải là sender/domain đã được xác minh trong tài
khoản Mailjet. Link xác thực mặc định hết hạn sau 24 giờ; có thể cấu hình bằng
`EMAIL_VERIFICATION_TOKEN_TTL_HOURS`. Sau khi đổi cấu hình:

```bash
docker compose up -d --force-recreate backend
```

Không dùng API key thật trong frontend hoặc ảnh chụp/log chia sẻ. Cổng giáo viên
ở `http://localhost:5173/teacher/login`; endpoint backend chỉ cấp JWT nếu tài
khoản đã được xác thực và role do server lưu là `teacher` hoặc `admin`.

### Duyệt hồ sơ giáo viên

Học viên đã xác thực có thể gửi hồ sơ tại trang Profile. Việc gửi hồ sơ không tự
đổi role. Các admin active/verified nhận một email ngắn chứa ID hồ sơ; nếu Mailjet
chưa sẵn sàng, hồ sơ vẫn được lưu trong database để không mất yêu cầu.

Admin đăng nhập Django admin tại `http://localhost:8000/admin/`, mở
`Users > Teacher applications`, chọn các hồ sơ `pending`, rồi dùng action duyệt
hoặc từ chối. Khi duyệt, backend đổi role và cập nhật specialization/experience
trong cùng transaction, đồng thời lưu reviewer và thời gian xử lý. Người nộp nhận
email kết quả nếu email backend hoạt động.

Hiện chưa có bài test năng lực giáo viên đã được kiểm chứng. Nếu bổ sung sau,
điểm test chỉ nên là dữ liệu hỗ trợ admin; không nên tự động cấp role đặc quyền.

### Đăng nhập trên web

Mở `http://localhost:5173/login` cho cả học viên và giáo viên. Đăng ký công khai
luôn tạo tài khoản học viên; quyền giáo viên phải được cấp bởi dữ liệu seed hoặc
quản trị viên, không được chọn từ form đăng ký.

- Giáo viên/admin đăng nhập thành công được đưa tới `/teacher/upload`.
- Học viên đăng nhập thành công được đưa tới `/dashboard`.
- Đặt `DEMO_TEACHER_PASSWORD` hoặc `DEMO_STUDENT_PASSWORD` trong `backend/.env`,
  rồi chạy lại `seed_demo_data` để đặt mật khẩu demo trên máy local.

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
