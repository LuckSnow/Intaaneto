# Intaaneto core API

Cập nhật: 2026-07-16. Swagger runtime tại `/api/docs/` là danh sách endpoint đầy
đủ; tài liệu này mô tả các contract cốt lõi đã được kiểm thử.

Protected endpoint dùng:

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

Không đưa token/key thật vào issue, ảnh chụp hoặc repository.

## Authentication và role

### Đăng ký learner

```http
POST /api/auth/register/
```

```json
{
  "email": "student@example.com",
  "username": "student01",
  "full_name": "Nguyễn Văn A",
  "password": "SecurePass123!",
  "password_confirm": "SecurePass123!"
}
```

Registration luôn tạo role `student`, `is_verified=false` và **không trả JWT**.
Response cho biết email verification có gửi được hay không. Các endpoint tiếp:

- `POST /api/auth/verify_email/` với `{ "token": "..." }`.
- `POST /api/auth/resend_verification/` với `{ "email": "..." }`; response
  không tiết lộ tài khoản có tồn tại hay đã verify.
- `POST /api/auth/login/` cho tài khoản active/verified.
- `POST /api/auth/teacher_login/` chỉ trả token cho teacher/admin.
- `POST /api/auth/logout/` với `{ "refresh_token": "..." }` để blacklist.
- `POST /api/auth/token/refresh/` với `{ "refresh": "..." }`.
- `GET /api/auth/users/me/` và `PATCH /api/auth/users/update_profile/`.

Login thành công:

```json
{
  "user": { "id": 1, "email": "student@example.com", "role": "student" },
  "tokens": { "access": "...", "refresh": "..." }
}
```

Learner xin nâng role qua `GET|POST /api/auth/users/teacher_application/`.
Chỉ admin xử lý qua `POST /api/auth/users/review_teacher_application/`; client
không được ghi status/reviewer hoặc tự đổi role.

## Course và lesson

Public:

- `GET /api/courses/`: chỉ course published.
- `GET /api/courses/{id}/`: chỉ course published và lesson published metadata.

Learner:

- `POST /api/courses/{id}/enroll/`.
- `GET /api/courses/{id}/progress/`.
- `GET /api/courses/lessons/{id}/`: enrolled lesson hoặc published preview.
- `POST /api/courses/lessons/{id}/complete/`.

Teacher:

- `GET /api/courses/managed/`: course draft/published thuộc sở hữu.
- `POST /api/courses/`, `PATCH|DELETE /api/courses/{id}/`: owner-only. Course
  mới phải draft; chỉ publish khi có lesson usable; course có lesson/enrollment
  không thể xóa cascade.
- `GET /api/courses/lessons/?course={course_id}`: lesson được phép quản lý/đọc.
- `POST /api/courses/lessons/upload/`: multipart PDF-only.
- `POST /api/courses/lessons/{id}/reprocess/`.
- `GET /api/courses/lessons/{id}/processing_status/`.

Upload multipart gồm `course`, `title`, `description`, `order`, `is_preview` và
`uploaded_file`. Backend kiểm tra ownership trước extraction/embedding; success
chỉ trả khi source active/ready hoàn chỉnh.

## Lesson assessment

Teacher owner dùng:

- `GET /api/exercises/assessments/?lesson={lesson_id}`.
- `POST /api/exercises/assessments/`.
- `PATCH|DELETE /api/exercises/assessments/{id}/` khi chưa có attempt.

```json
{
  "lesson": 121,
  "title": "Kiểm tra bài 1",
  "instructions": "Chọn đáp án đúng.",
  "pass_threshold": 70,
  "is_published": true,
  "questions": [
    {
      "prompt": "RAG tìm bằng chứng ở bước nào?",
      "choices": ["Retrieval", "Rendering"],
      "correct_choice": 0,
      "learning_objective": "Nhận biết retrieval",
      "explanation": "Retrieval tìm đoạn liên quan.",
      "order": 1
    }
  ]
}
```

Tối đa 50 câu, mỗi câu 2–6 lựa chọn và learning objective bắt buộc. Learner GET
chỉ thấy assessment published trong course đã enroll, không có `correct_choice`
hoặc `explanation`.

Learner submit:

```http
POST /api/exercises/assessments/{id}/submit/
```

```json
{
  "answers": [
    { "question_id": 10, "selected_choice": 0 }
  ]
}
```

Response chứa server-owned `score`, `passed`, `weak_objectives`, mastery,
progress và `next_lesson`. Không gửi/không tin score hoặc pass từ client.
Reinforcement dùng:

```http
POST /api/exercises/assessments/{id}/reinforcement/
```

```json
{ "attempt_id": 42 }
```

## Grounded AI Tutor

```http
POST /api/ai/chat/send_message/
```

Phiên mới:

```json
{ "lesson_id": 121, "message": "RAG là gì?" }
```

Tiếp tục phiên (lesson scope không thể thay đổi):

```json
{ "session_id": 7, "message": "Giải thích retrieval rõ hơn." }
```

Response ổn định:

```json
{
  "session_id": 7,
  "answer": "...",
  "grounded": true,
  "citations": [
    {
      "id": "knowledge-chunk-15",
      "lesson_id": 121,
      "source_version": 1,
      "excerpt": "..."
    }
  ],
  "retrieval": {
    "status": "ready",
    "source_version": 1,
    "candidate_count": 5,
    "evidence_count": 2
  }
}
```

Nếu evidence yếu/chưa index, backend fallback và không gọi generation provider.
Các action khác: `POST /api/ai/chat/get_hint/` (exercise đã authorize) và
`POST /api/ai/chat/explain_code/`.

## Báo cáo tiến độ

```http
GET /api/analytics/progress_report/
```

- Learner nhận dữ liệu của chính mình.
- Teacher nhận aggregate course thuộc sở hữu; có thể dùng `course_id`, `limit`,
  `offset` để lấy roster bounded.
- Không trả email, answer key, chat hoặc attempt version cũ.

## Forum, lesson comments và reviews

- `/api/forum/posts/`, `/comments/`, `/tags/`, `/follows/`, `/reports/`.
- `/api/courses/lesson-comments/` và `/api/courses/reviews/`.

Mutation yêu cầu authentication và object ownership hoặc role-admin theo action.
Public forum author object không chứa email/phone/profile riêng tư.

## Trạng thái lỗi quan trọng

- `400`: payload/target/answer set không hợp lệ.
- `401`: chưa xác thực hoặc token hết hạn.
- `403`: đã xác thực nhưng sai role/quyền action.
- `404`: object ngoài authorized queryset (tránh object discovery).
- `409`: assessment đã có attempt, course không rỗng, duplicate workflow state.
- `429`: vượt scoped throttle.
- `502/503`: generation hoặc knowledge service tạm không khả dụng; response không
  chứa key/provider diagnostics.
