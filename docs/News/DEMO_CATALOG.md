# Khóa học demo và ảnh bìa

## Dữ liệu bổ sung

`seed_demo_catalog` thêm vào tài khoản hiện có `demo.teacher@example.invalid`:

| Khóa học | Số bài văn bản |
| --- | ---: |
| Nền tảng Mạng máy tính | 8 |
| Nền tảng Lập trình Web | 7 |
| PHP cơ bản qua ví dụ | 5 |

Hai khóa đầu dùng bộ Markdown hiện có. Khóa PHP chứa ví dụ, bài tự luyện và
liên kết PHP Manual; đây là học liệu demo, không phải kết quả đánh giá nghiên cứu.
Mỗi khóa có ảnh SVG tĩnh do dự án biên soạn. Khóa Demo AI Tutor với RAG cũng được
bổ sung ảnh nếu chưa có ảnh. SVG này là tài sản tin cậy trong repository; API tải
ảnh của giáo viên chỉ nhận JPG, PNG và WebP tĩnh.

Từ thư mục backend, xem trước mà không đọc/ghi database:

```sh
python manage.py seed_demo_catalog
```

Sau khi kiểm tra đúng cấu hình database, thêm và xuất bản dữ liệu mới:

```sh
python manage.py seed_demo_catalog --apply --publish
```

Chạy qua Docker dùng `docker compose run --rm --no-deps -T backend` trước lệnh
Python. Lệnh dùng database và storage đang cấu hình trong backend; không tự chọn
local hay cloud. Bỏ `--publish` để tạo bản nháp.

Lệnh yêu cầu Demo Teacher đang active, đã xác minh và có role teacher. Không tạo
tài khoản, đổi mật khẩu, chuyển chủ sở hữu, di chuyển bài cũ hay sao chép kết quả
học tập. Nếu slug khóa trùng với khóa của người khác, toàn bộ thao tác bị từ chối.
Chạy lại không ghi đè nội dung, ảnh và video hiện có, không tạo thêm bản sao; cờ
`--publish` chỉ áp dụng cho bản ghi mới. Chỉnh nội dung cũ qua luồng quản lý riêng.

Bài mới có nội dung đọc được, chưa có PDF/video/assessment/chỉ mục RAG. Nếu cần
AI Tutor, kiểm tra và lập chỉ mục từng bài bằng lệnh hiện có:

```sh
python manage.py index_lesson LESSON_ID --actor-id TEACHER_ID
```

Không dùng `seed_demo_data` để cập nhật khóa đang có học liệu cá nhân: lệnh demo
cũ có chủ đích đặt lại nội dung và xóa liên kết file của bài RAG mẫu.

## Giáo viên tự đổi ảnh

1. Mở **Quản lý khóa học** → **Chỉnh sửa**.
2. Ở **Ảnh bìa khóa học**, chọn JPG, PNG hoặc WebP tĩnh, tối đa 2 MB và 4096 pixel
   mỗi chiều. Tỷ lệ 16:9 phù hợp với thẻ khóa học.
3. Kiểm tra ảnh xem trước rồi chọn **Lưu thay đổi**. **Gỡ ảnh bìa** chỉ có hiệu lực
   sau khi lưu; hủy biểu mẫu giữ nguyên dữ liệu trên server.

API dùng multipart `thumbnail_upload` cho ảnh mới và `remove_thumbnail` cho gỡ
ảnh; trường `thumbnail` trong response vẫn là URL. Quyền sửa được kiểm tra tại
backend theo giáo viên sở hữu hoặc admin. File thay thế được lưu tên UUID; file
cũ không bị xóa tức thì để giữ khả năng khôi phục. Dọn object không còn tham chiếu
vẫn là tác vụ vận hành riêng.
