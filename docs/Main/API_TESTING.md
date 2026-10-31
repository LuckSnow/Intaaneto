# API Testing Guide - Intaaneto

## 🧪 Postman Collection Examples

### Setup

**Base URL:** `http://localhost:8000/api`

**Headers cho authenticated requests:**
```json
{
  "Authorization": "Bearer <access_token>",
  "Content-Type": "application/json"
}
```

---

## 1️⃣ Authentication Tests

### 1.1 Register User

**POST** `/auth/register/`

**Body:**
```json
{
  "email": "student1@example.com",
  "username": "student1",
  "full_name": "Nguyễn Văn A",
  "role": "student",
  "password": "SecurePass123",
  "password_confirm": "SecurePass123"
}
```

**Expected Response (201):**
```json
{
  "user": {
    "id": 1,
    "email": "student1@example.com",
    "username": "student1",
    "full_name": "Nguyễn Văn A",
    "role": "student",
    "avatar": null,
    "is_verified": false
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJh...",
    "access": "eyJ0eXAiOiJKV1QiLCJh..."
  }
}
```

### 1.2 Login

**POST** `/auth/login/`

**Body:**
```json
{
  "email": "student1@example.com",
  "password": "SecurePass123"
}
```

**Expected Response (200):**
```json
{
  "user": {
    "id": 1,
    "email": "student1@example.com",
    "username": "student1",
    "full_name": "Nguyễn Văn A",
    "role": "student"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJh...",
    "access": "eyJ0eXAiOiJKV1QiLCJh..."
  }
}
```

### 1.3 Get Current User

**GET** `/auth/users/me/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Expected Response (200):**
```json
{
  "id": 1,
  "email": "student1@example.com",
  "username": "student1",
  "full_name": "Nguyễn Văn A",
  "role": "student",
  "profile": {
    "grade_level": "",
    "school_name": "",
    "notification_enabled": true
  }
}
```

---

## 2️⃣ Course Tests

### 2.1 Get All Courses

**GET** `/courses/`

**Query Parameters:**
- `difficulty`: beginner, intermediate, advanced
- `search`: search term

**Expected Response (200):**
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "HTML & CSS Cơ Bản",
      "slug": "html-css-co-ban",
      "description": "Khóa học HTML CSS cho người mới bắt đầu",
      "thumbnail": "/media/courses/thumbnails/html-css.jpg",
      "difficulty": "beginner",
      "duration_hours": 10,
      "teacher_name": "Thầy Tuấn",
      "total_students": 25,
      "average_rating": "4.50",
      "lessons_count": 15,
      "is_published": true
    }
  ]
}
```

### 2.2 Get Course Detail

**GET** `/courses/{id}/`

**Expected Response (200):**
```json
{
  "id": 1,
  "title": "HTML & CSS Cơ Bản",
  "description": "Khóa học HTML CSS...",
  "difficulty": "beginner",
  "objectives": "- Hiểu cấu trúc HTML\n- Styling với CSS",
  "prerequisites": "Không cần kiến thức trước",
  "teacher": {
    "id": 2,
    "full_name": "Thầy Tuấn",
    "avatar": null
  },
  "lessons": [
    {
      "id": 1,
      "title": "Giới thiệu HTML",
      "slug": "gioi-thieu-html",
      "lesson_type": "video",
      "duration_minutes": 30,
      "order": 1,
      "is_preview": true
    }
  ]
}
```

### 2.3 Enroll in Course

**POST** `/courses/{id}/enroll/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Expected Response (201):**
```json
{
  "message": "Enrolled successfully"
}
```

### 2.4 Get Course Progress

**GET** `/courses/{id}/progress/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Expected Response (200):**
```json
{
  "id": 1,
  "user": 1,
  "course": 1,
  "progress_percentage": "45.50",
  "enrolled_at": "2026-01-24T10:00:00Z",
  "completed_at": null,
  "last_accessed_lesson": 5
}
```

---

## 3️⃣ Lesson Tests

### 3.1 Complete Lesson

**POST** `/courses/lessons/{id}/complete/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Expected Response (200):**
```json
{
  "message": "Lesson marked as completed"
}
```

---

## 4️⃣ Exercise Tests

### 4.1 Get Exercises

**GET** `/exercises/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Expected Response (200):**
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "lesson": 3,
      "lesson_title": "HTML Forms",
      "title": "Tạo Form Đăng Ký",
      "description": "Tạo form HTML với các input fields...",
      "difficulty": "easy",
      "max_points": 100,
      "order": 1
    }
  ]
}
```

### 4.2 Get Exercise Detail

**GET** `/exercises/{id}/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Expected Response (200):**
```json
{
  "id": 1,
  "title": "Tạo Form Đăng Ký",
  "description": "Tạo form HTML...",
  "instructions": "1. Tạo form với action và method\n2. Thêm input fields...",
  "difficulty": "easy",
  "starter_code": "<form>\n  <!-- Your code here -->\n</form>",
  "max_points": 100,
  "hints": [
    "Dùng thẻ <input> với type='text'",
    "Đừng quên thẻ <label>"
  ]
}
```

### 4.3 Submit Exercise

**POST** `/exercises/submissions/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Body:**
```json
{
  "exercise": 1,
  "code": "<form action='/submit' method='POST'>\n  <label>Name:</label>\n  <input type='text' name='name'>\n</form>"
}
```

**Expected Response (201):**
```json
{
  "id": 1,
  "exercise": 1,
  "exercise_title": "Tạo Form Đăng Ký",
  "user": 1,
  "user_name": "Nguyễn Văn A",
  "code": "<form...>",
  "status": "pending",
  "points_earned": 0,
  "feedback": "Bài nộp đang được xử lý...",
  "submitted_at": "2026-01-24T10:30:00Z"
}
```

### 4.4 Get My Submissions

**GET** `/exercises/{exercise_id}/submissions/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Expected Response (200):**
```json
{
  "count": 3,
  "results": [
    {
      "id": 3,
      "status": "passed",
      "points_earned": 100,
      "feedback": "Tuyệt vời! Code của bạn đúng hoàn toàn.",
      "submitted_at": "2026-01-24T11:00:00Z"
    },
    {
      "id": 2,
      "status": "failed",
      "points_earned": 60,
      "feedback": "Còn thiếu attribute method trong form",
      "submitted_at": "2026-01-24T10:45:00Z"
    }
  ]
}
```

---

## 5️⃣ AI Assistant Tests

### 5.1 Send Message to AI

**POST** `/ai/chat/send_message/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Body:**
```json
{
  "message": "Em không hiểu về CSS Flexbox, thầy giải thích giúp em được không?",
  "session_id": 1,
  "context": {
    "lesson": "CSS Layout",
    "course": "HTML & CSS Cơ Bản"
  }
}
```

**Expected Response (200):**
```json
{
  "session_id": 1,
  "message": {
    "id": 5,
    "role": "assistant",
    "content": "Chào em! Flexbox là cách bố trí layout rất mạnh trong CSS...",
    "tokens_used": 250,
    "response_time_ms": 1500,
    "created_at": "2026-01-24T10:35:00Z"
  }
}
```

### 5.2 Explain Code

**POST** `/ai/chat/explain_code/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Body:**
```json
{
  "code": "function greeting(name) {\n  return 'Hello ' + name;\n}",
  "language": "javascript"
}
```

**Expected Response (200):**
```json
{
  "explanation": "Đây là một function JavaScript tên là 'greeting':\n\n1. Function này nhận 1 tham số 'name'\n2. Nó trả về một chuỗi text 'Hello ' cộng với tên được truyền vào\n3. Ví dụ: greeting('Nam') sẽ trả về 'Hello Nam'\n\nĐây là cách cơ bản để tạo function và nối chuỗi trong JavaScript!"
}
```

### 5.3 Get Hint for Exercise

**POST** `/ai/chat/get_hint/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Body:**
```json
{
  "exercise_id": 1,
  "student_code": "<form>\n  <input type='text'>\n</form>"
}
```

**Expected Response (200):**
```json
{
  "hint": "Code của em đã đúng hướng! Tuy nhiên:\n\n1. Em cần thêm attribute 'action' và 'method' cho thẻ <form>\n2. Nên thêm thẻ <label> để mô tả input field\n3. Đừng quên attribute 'name' cho input để server nhận được data\n\nThử thêm những điều này vào code nhé!"
}
```

---

## 6️⃣ Forum Tests

### 6.1 Get Posts

**GET** `/forum/posts/`

**Query Parameters:**
- `category`: question, discussion, showcase, announcement
- `search`: search term

**Expected Response (200):**
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "author": {
        "id": 1,
        "username": "student1",
        "full_name": "Nguyễn Văn A",
        "avatar": null
      },
      "title": "Làm thế nào để center div?",
      "content": "Em muốn căn giữa một div nhưng không biết cách...",
      "category": "question",
      "tags": ["css", "flexbox"],
      "views_count": 45,
      "likes_count": 12,
      "comments_count": 5,
      "is_solved": true,
      "is_pinned": false,
      "created_at": "2026-01-24T09:00:00Z"
    }
  ]
}
```

### 6.2 Create Post

**POST** `/forum/posts/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Body:**
```json
{
  "title": "Share dự án đầu tiên của em",
  "content": "Mọi người xem và góp ý giúp em nhé...",
  "category": "showcase",
  "tags": ["html", "css", "beginner"]
}
```

**Expected Response (201):**
```json
{
  "id": 11,
  "title": "Share dự án đầu tiên của em",
  "content": "Mọi người xem...",
  "category": "showcase",
  "tags": ["html", "css", "beginner"],
  "views_count": 0,
  "likes_count": 0,
  "created_at": "2026-01-24T11:00:00Z"
}
```

### 6.3 Like Post

**POST** `/forum/posts/{id}/like/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Expected Response (200):**
```json
{
  "message": "Post liked"
}
```

### 6.4 Add Comment

**POST** `/forum/comments/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Body:**
```json
{
  "post": 1,
  "content": "Em có thể dùng Flexbox: display: flex; justify-content: center;",
  "parent": null
}
```

**Expected Response (201):**
```json
{
  "id": 1,
  "post": 1,
  "author": {
    "id": 2,
    "username": "student2",
    "full_name": "Trần Thị B"
  },
  "content": "Em có thể dùng Flexbox...",
  "parent": null,
  "likes_count": 0,
  "is_solution": false,
  "created_at": "2026-01-24T11:05:00Z"
}
```

---

## 7️⃣ Analytics Tests

### 7.1 Get My Stats

**GET** `/analytics/my_stats/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Expected Response (200):**
```json
{
  "id": 1,
  "user": 1,
  "total_learning_time_minutes": 450,
  "total_courses_enrolled": 3,
  "total_courses_completed": 1,
  "total_exercises_submitted": 25,
  "total_exercises_passed": 20,
  "total_forum_posts": 5,
  "total_forum_comments": 15,
  "total_ai_interactions": 50,
  "current_streak_days": 7,
  "longest_streak_days": 14,
  "total_points": 1250,
  "achievements_count": 5,
  "completion_rate": 33.33
}
```

### 7.2 Get My Achievements

**GET** `/analytics/my_achievements/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Expected Response (200):**
```json
{
  "count": 5,
  "results": [
    {
      "id": 1,
      "achievement": {
        "id": 1,
        "name": "First Steps",
        "description": "Hoàn thành bài học đầu tiên",
        "icon": "/media/achievements/first-steps.png",
        "points": 10
      },
      "earned_at": "2026-01-20T10:00:00Z"
    }
  ]
}
```

### 7.3 Get Leaderboard

**GET** `/analytics/leaderboard/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Expected Response (200):**
```json
{
  "count": 10,
  "results": [
    {
      "user": {
        "id": 5,
        "username": "topstudent",
        "full_name": "Học Sinh Giỏi"
      },
      "total_points": 5000,
      "total_courses_completed": 10,
      "current_streak_days": 30
    }
  ]
}
```

---

## 🧪 Error Response Examples

### 400 Bad Request

```json
{
  "error": "Validation error",
  "details": {
    "email": ["This field is required"],
    "password": ["Password must be at least 8 characters"]
  }
}
```

### 401 Unauthorized

```json
{
  "detail": "Authentication credentials were not provided."
}
```

or

```json
{
  "error": "Invalid credentials"
}
```

### 403 Forbidden

```json
{
  "error": "You do not have permission to perform this action"
}
```

### 404 Not Found

```json
{
  "error": "Resource not found"
}
```

### 500 Internal Server Error

```json
{
  "error": "Internal server error",
  "detail": "An unexpected error occurred"
}
```

---

## 📝 Testing Checklist

### Authentication Flow
- [ ] Register new user
- [ ] Login with credentials
- [ ] Get current user info
- [ ] Update profile
- [ ] Logout

### Course Flow
- [ ] List all courses
- [ ] Get course detail
- [ ] Enroll in course
- [ ] View lessons
- [ ] Complete lesson
- [ ] Track progress

### Exercise Flow
- [ ] List exercises
- [ ] Get exercise detail
- [ ] Submit solution
- [ ] View submission results
- [ ] Get hint from AI

### Forum Flow
- [ ] List posts
- [ ] Create post
- [ ] View post detail
- [ ] Add comment
- [ ] Like post/comment
- [ ] Mark as solved

### AI Flow
- [ ] Send message
- [ ] Explain code
- [ ] Get exercise hint
- [ ] View chat history

---

## 🔧 cURL Examples

### Register
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "full_name": "Test User",
    "role": "student",
    "password": "test123456",
    "password_confirm": "test123456"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123456"
  }'
```

### Get Courses (with token)
```bash
curl -X GET http://localhost:8000/api/courses/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

**Note**: Replace `<access_token>` và `{id}` với values thực tế khi test!
