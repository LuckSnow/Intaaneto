# API Documentation

## Authentication

Tất cả các protected endpoints yêu cầu JWT token trong header:
```
Authorization: Bearer <access_token>
```

### Register
```
POST /api/auth/register/
```

**Request Body:**
```json
{
  "email": "student@example.com",
  "username": "student01",
  "full_name": "Nguyễn Văn A",
  "role": "student",
  "password": "SecurePass123",
  "password_confirm": "SecurePass123"
}
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "email": "student@example.com",
    "username": "student01",
    "full_name": "Nguyễn Văn A",
    "role": "student"
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

### Login
```
POST /api/auth/login/
```

**Request Body:**
```json
{
  "email": "student@example.com",
  "password": "SecurePass123"
}
```

### Get Current User
```
GET /api/auth/users/me/
Authorization: Bearer <token>
```

## Courses

### Get All Courses
```
GET /api/courses/
```

**Query Parameters:**
- `difficulty`: beginner, intermediate, advanced
- `search`: Search in title/description

### Get Course Detail
```
GET /api/courses/{id}/
```

### Enroll in Course
```
POST /api/courses/{id}/enroll/
Authorization: Bearer <token>
```

### Get My Progress
```
GET /api/courses/{id}/progress/
Authorization: Bearer <token>
```

## AI Assistant

### Send Message
```
POST /api/ai/chat/send_message/
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "message": "Em không hiểu về CSS flexbox",
  "session_id": 1,
  "context": {
    "lesson": "CSS Layout",
    "course": "HTML & CSS Basics"
  }
}
```

### Explain Code
```
POST /api/ai/chat/explain_code/
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "code": "function greeting(name) {\n  return 'Hello ' + name;\n}",
  "language": "javascript"
}
```

### Get Hint
```
POST /api/ai/chat/get_hint/
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "exercise_id": 5,
  "student_code": "// Code hiện tại của học sinh"
}
```

## Forum

### Get Posts
```
GET /api/forum/posts/
```

**Query Parameters:**
- `category`: question, discussion, showcase, announcement
- `search`: Search in title/content

### Create Post
```
POST /api/forum/posts/
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "title": "Làm thế nào để tạo button đẹp?",
  "content": "Em muốn tạo button có hiệu ứng hover...",
  "category": "question",
  "tags": ["css", "button", "styling"]
}
```

### Like Post
```
POST /api/forum/posts/{id}/like/
Authorization: Bearer <token>
```

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid input",
  "details": {
    "email": ["This field is required"]
  }
}
```

### 401 Unauthorized
```json
{
  "error": "Invalid credentials"
}
```

### 404 Not Found
```json
{
  "error": "Resource not found"
}
```

### 500 Server Error
```json
{
  "error": "Internal server error"
}
```
