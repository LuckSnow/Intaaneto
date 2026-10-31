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

Compose khởi động PostgreSQL và Redis trước, sau đó backend, Celery ingestion
worker và frontend. Backend tự chạy các migration đã commit khi container khởi
động. Xác minh cả broker/worker:

```bash
docker compose ps
docker compose logs --tail=50 worker
```

`redis` phải healthy; worker phải kết nối `redis://redis:6379/0`, đăng ký
`apps.courses.tasks.process_pdf_lesson_job` và chạy bằng user `appuser`, không
phải root. Tạo tài khoản quản trị bằng:

```bash
docker compose exec backend python manage.py createsuperuser
```

Nhập email, username, full name và một mật khẩu mạnh riêng trên từng máy. Không
dùng hoặc ghi một mật khẩu quản trị mặc định trong repository.

## Vận hành hàng đợi PDF

Upload/reprocess chỉ được coi là tiếp nhận khi API trả `202`. Trạng thái nguồn
sự thật nằm trong `Lesson.processing_status` và `LessonIngestionJob`; không dùng
Celery result backend. Kiểm tra nhanh:

```bash
docker compose ps
docker compose exec worker celery -A config inspect ping
docker compose logs --tail=100 worker
```

Trong Django Admin, mở `Courses > Lesson ingestion jobs`. Một lesson chỉ có tối
đa một job `queued/running`. `attempts`, `failure_code`, source kết quả và thời
điểm dùng để chẩn đoán; task UUID là nội bộ và không xuất hiện trong API.

Nếu Redis/worker tạm dừng:

1. Chạy `docker compose up -d redis worker` và kiểm tra worker báo `ready`.
2. Job đã được broker nhận sẽ tiếp tục theo late acknowledgement/visibility
   timeout. Không tự sửa `running` thành `completed` trong database.
3. Job enqueue thất bại được đánh dấu `failed`, không nằm pending giả. Sau khi
   broker khỏe, teacher dùng nút `Thử lại`; indexing idempotent không nhân đôi
   active source.

Không chạy `redis-cli FLUSHALL`, purge queue hoặc xóa volume khi còn job thật.
Development worker để `concurrency=1` nhằm giới hạn RAM/model load; chỉ tăng sau
khi đo resource. Redis AOF/DB job giúp khôi phục prototype nhưng không thay thế
broker HA, monitoring, backup đồng bộ PostgreSQL/media và quy trình production.

## Tạo dữ liệu mẫu dùng chung

Không copy Docker volume hoặc dump toàn bộ database development sang máy khác vì
chúng có thể chứa tài khoản, chat, uploads và vectors cục bộ. Repository cung cấp
command idempotent để mỗi thành viên tự tạo cùng một bộ dữ liệu demo an toàn:

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed_demo_data
```

Command tạo một giảng viên demo, một học viên đã enroll, course `Demo AI Tutor
với RAG`, lesson `RAG là gì?` và assessment 5 câu đã được biên tập. Chạy lại
command sẽ cập nhật đúng bộ dữ liệu đó thay vì tạo duplicate; assessment đã có
attempt không bị ghi đè. Command không tạo uploads, chat history hoặc vector index.

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

### Nhập assessment blueprint tách khỏi RAG

Repository có 3 assessment draft/27 câu cho ba lesson đại diện: mô hình mạng,
an toàn mạng và bảo mật web. Mỗi learning objective có đúng 3 câu; answer key nằm
trong module exercises và không được ghép vào lesson content. Kiểm tra blueprint
không đọc database:

```bash
docker compose exec backend python manage.py import_corpus_assessments --dry-run
```

Sau khi đã nhập corpus bằng đúng teacher-owner, tạo assessment ở trạng thái draft:

```bash
docker compose exec backend python manage.py import_corpus_assessments --teacher-id 45
```

Command idempotent, chạy trong transaction và từ chối lesson khác owner, lesson
không do corpus importer quản lý, assessment đã bị sửa hoặc assessment có attempt
khác blueprint. Nó không in answer key. Giảng viên phải đọc từng câu trên trang
`/teacher/assessments`; chỉ sau khi review mới dùng cờ xác nhận rõ ràng:

```bash
docker compose exec backend python manage.py import_corpus_assessments \
  --teacher-id 45 --publish-reviewed
```

Không dùng cờ này chỉ để làm cho demo “đủ trạng thái”; published assessment sẽ
trở thành gate progression của learner.

Chạy software baseline E2 mà không tạo attempt hoặc in answer key:

```bash
docker compose exec backend python manage.py evaluate_corpus_assessments \
  --teacher-id 45
```

Việc export phiếu hai người chấm chứa authoring answer key nên cần cờ xác nhận,
được ghi `0600` vào private media volume và tuyệt đối không commit. Quy trình đầy
đủ nằm trong [ASSESSMENT_EVALUATION_PROTOCOL.md](ASSESSMENT_EVALUATION_PROTOCOL.md).

## PoC video SadTalker

SadTalker local không cần API key và không được cài chung vào backend mặc định.
Adapter, management command và audit job cũ được giữ làm bằng chứng PoC; lesson
API và teacher UI không còn trigger SadTalker. Cấu hình runtime tách biệt và mẫu
biên bản smoke được mô tả tại [SADTALKER_POC.md](SADTALKER_POC.md). Runtime local
đã pass technical GPU smoke; chưa có render bằng portrait/audio học liệu đã được
duyệt thì không được ghi nhận video tutor là hoàn thành về nội dung/chất lượng.

Runtime tách biệt hiện tại có thể được nối vào backend bằng Compose override:

```bash
SADTALKER_HOST_RUNTIME=/absolute/path/to/intaaneto-sadtalker \
  docker compose -f docker-compose.yml -f docker-compose.sadtalker.yml up -d video_worker
```

Không ghi đường dẫn này vào `VITE_*`. Override mount runtime read-only và chỉ cấp
GPU cho worker video một-at-a-time; file tạm/output nằm trong media volume ghi được.
Worker mặc định tiếp tục xử lý PDF trên queue `celery` và không nhận job video.

## Video slide local tiếng Việt

Luồng web hiện dùng Piper + Pillow + FFmpeg để tạo video slide có phụ đề và ảnh
AI Tutor cố định; không cần SadTalker, GPU, D-ID hoặc API key. Trước khi tải model
voice, đọc checklist license/provenance và hướng dẫn cài đặt tại
[LOCAL_MULTIMEDIA_SETUP.md](LOCAL_MULTIMEDIA_SETUP.md).

## Email xác thực và Mailjet

Môi trường development mặc định in email xác thực vào console backend. Để gửi
qua Mailjet, đặt ba giá trị sau trong `backend/.env` rồi recreate backend; không
đặt các key này trong biến `VITE_*` hoặc commit file `.env`:

```env
EMAIL_BACKEND=anymail.backends.mailjet.EmailBackend
MAILJET_API_KEY=your-local-mailjet-api-key
MAILJET_SECRET_KEY=your-local-mailjet-secret-key
DEFAULT_FROM_EMAIL_NAME=Intaaneto
```

Địa chỉ `DEFAULT_FROM_EMAIL` phải là sender/domain đã được xác minh trong tài
khoản Mailjet. Link xác thực mặc định hết hạn sau 24 giờ; có thể cấu hình bằng
`EMAIL_VERIFICATION_TOKEN_TTL_HOURS`. Sau khi đổi cấu hình:

Địa chỉ `@gmail.com` chỉ phù hợp cho smoke cục bộ: chủ dự án không thể cấu hình
SPF/DKIM cho domain `gmail.com`, nên thư gửi qua Mailjet có thể hiện “qua
Mailjet”, vào Spam và không có avatar thương hiệu. Trước demo công khai, dùng
một địa chỉ thuộc domain dự án, xác thực domain đó trong Mailjet, rồi cấu hình
SPF, DKIM và DMARC. Avatar thương hiệu trong Gmail là bước BIMI riêng ở cấp DNS
và chứng thư; ảnh đặt trong HTML không điều khiển avatar người gửi.

```bash
docker compose up -d --force-recreate backend
```

Luồng quên mật khẩu dùng cùng email backend. Cả học viên và giáo viên mở liên
kết `Quên mật khẩu?` tại trang đăng nhập, nhập email, rồi nhận link một lần tại
`/reset-password/<uid>/<token>`. Link mặc định hết hạn sau 60 phút, cấu hình bằng
`PASSWORD_RESET_TIMEOUT_SECONDS`. API yêu cầu reset luôn trả thông báo chung để
không tiết lộ email có tài khoản hay không; đổi mật khẩu thành công làm JWT cũ
mất hiệu lực và không thay đổi role hoặc trạng thái xác thực.

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

### Quick Tunnel cho demo ngắn

Hướng dẫn bật/tắt, bật lại, cấu hình Google Login và xử lý sự cố nằm tại
[QUICK_TUNNEL_DEMO.md](QUICK_TUNNEL_DEMO.md).

Chỉ tunnel Vite; `docker-compose.demo.yml` chuyển tiếp `/api` và `/media` nội bộ
sang Django để trình duyệt ngoài máy không phụ thuộc `localhost:8000`. Không
tunnel trực tiếp PostgreSQL, Adminer hoặc backend.

Terminal thứ nhất:

```bash
npx wrangler tunnel quick-start http://localhost:5173
```

Lấy hostname được cấp, bỏ phần `https://`, rồi chạy ở terminal thứ hai:

```bash
export DEMO_TUNNEL_HOST=random-words.trycloudflare.com
docker compose -f docker-compose.yml -f docker-compose.demo.yml \
  up -d --force-recreate backend frontend
```

Giữ terminal tunnel mở trong suốt buổi demo. Email xác thực tạo trong thời gian
này sẽ dùng URL HTTPS public. Google/Firebase popup chỉ hoạt động sau khi thêm
hostname ngẫu nhiên vào Firebase Authentication > Settings > Authorized domains;
đăng nhập email/mật khẩu không cần bước đó.

Sau demo, dừng tunnel bằng `Ctrl+C` và khôi phục cấu hình localhost:

```bash
docker compose up -d --force-recreate backend frontend
```

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
