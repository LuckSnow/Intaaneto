# Intaaneto - Nền Tảng Học Lập Trình Web Với AI

## 📖 Giới thiệu

Intaaneto là nền tảng học lập trình web được thiết kế dành cho người mới bắt đầu, với giao diện thân thiện và trợ lý AI hỗ trợ 24/7.

### 🎯 Tính năng chính
- Trang web __tập trung__ vào phát triển module kiểm tra kiến thức bài tập, cho 1 mốc điểm để kiểm tra bài tập của học sinh.__Nếu không vượt qua mốc điểm này, học sinh sẽ không hoàn thành module__ bài học đó. Cho nên sẽ cần AI hỗ trợ để củng cố lại kiến thức/Hoặc đọc lại phần bài giảng.
- Phần bài giảng sinh động, dễ hiểu với ví dụ minh họa cụ thể về HTML, CSS, JavaScript cơ bản.
- Nếu có thể thì phần bài giảng sẽ có 1 mô hình AI tạo avt tự động, video âm thanh để học sinh dễ hiểu, có 1 ô chức năng hỏi đáp với trợ lý AI nhưng mà không khô khan như việc chỉ có nhắn tin văn bản. 

- 🤖 **Trợ lý AI**: Giải đáp thắc mắc, hướng dẫn làm bài tập, 
- 📚 **Bài giảng sinh động**: HTML, CSS, JavaScript cơ bản, các kiến thức liên quan đến lập trình web, khả thi thì thêm các kiến thức hiện đại hơn.
- 💬 **Forum trao đổi**: Cộng đồng học sinh, phụ huynh, giáo viên, giáo viên xem xét để sau do phải phân quyền
- 📊 **Theo dõi tiến độ**: Analytics và achievements
- 👨‍🏫 **Hệ thống giáo viên**: Tạo và quản lý bài giảng (ĐỂ SAU)

## 🛠️ Tech Stack

### Backend
- **Framework**: Django 5.0 + Django REST Framework
- **Database**: PostgreSQL 15
- **Authentication**: JWT (Simple JWT)
- **AI**: OpenAI GPT-3.5
- **các option AI**: Kiểu AI mà có video khuôn mặt, có âm thanh video, tạo avt tự động (dùng DALL·E 2 hoặc Stable Diffusion)
- 
### Frontend
- **Framework**: React 18
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Data Fetching**: React Query
- **Routing**: React Router v6

## 📦 Cấu trúc dự án

```
intaaneto/
├── backend/                  # Django Backend
│   ├── config/              # Settings & URLs
│   ├── apps/                # Django apps
│   │   ├── users/          # User management
│   │   ├── courses/        # Courses & Lessons
│   │   ├── exercises/      # Exercises & Submissions
│   │   ├── ai_assistant/   # AI Chat
│   │   ├── forum/          # Forum & Comments
│   │   └── analytics/      # Analytics & Achievements
│   ├── requirements.txt
│   └── manage.py
│
├── frontend/                # React Frontend
│   ├── src/
│   │   ├── components/     # Reusable components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   ├── store/          # State management
│   │   └── utils/          # Utilities
│   ├── package.json
│   └── vite.config.js
│
├── docs/                    # Documentation
├── docker-compose.yml
└── README.md
```

## 🚀 Hướng dẫn cài đặt

### Yêu cầu hệ thống

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Docker & Docker Compose (optional)

### Cài đặt với Docker (Khuyến nghị)

```bash
# Clone repository
git clone <repository-url>
cd intaaneto

# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Chỉnh sửa các file .env với thông tin của bạn
# Đặc biệt quan trọng: OPENAI_API_KEY trong backend/.env

# Start all services
docker-compose up -d

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000/api
# Admin: http://localhost:8000/admin
```

### Cài đặt thủ công

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy and configure .env
copy .env.example .env
# Chỉnh sửa .env với thông tin database và API keys

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Copy and configure .env
copy .env.example .env

# Start development server
npm run dev
```

## 🔧 Cấu hình

### Backend (.env)

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=intaaneto_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

OPENAI_API_KEY=your-openai-api-key
```

### Frontend (.env)

```env
VITE_API_URL=http://localhost:8000/api
```

## 📚 API Documentation

API documentation được tạo tự động với Swagger:
- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/

### Các endpoints chính

#### Authentication
- POST `/api/auth/register/` - Đăng ký
- POST `/api/auth/login/` - Đăng nhập
- POST `/api/auth/logout/` - Đăng xuất
- GET `/api/auth/users/me/` - Thông tin user hiện tại

#### Courses
- GET `/api/courses/` - Danh sách khóa học
- GET `/api/courses/{id}/` - Chi tiết khóa học
- POST `/api/courses/{id}/enroll/` - Đăng ký khóa học

#### AI Assistant
- POST `/api/ai/chat/send_message/` - Gửi tin nhắn cho AI
- POST `/api/ai/chat/explain_code/` - Giải thích code
- POST `/api/ai/chat/get_hint/` - Xin gợi ý bài tập

#### Forum
- GET `/api/forum/posts/` - Danh sách bài đăng
- POST `/api/forum/posts/` - Tạo bài đăng mới
- POST `/api/forum/posts/{id}/like/` - Like bài đăng

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest
```

### Frontend Tests

```bash
cd frontend
npm test
```

## 📝 Database Schema

Xem chi tiết trong [docs/database-schema.md](docs/database-schema.md)

### Các models chính

- **User**: Người dùng (student, parent, teacher, admin)
- **Course**: Khóa học
- **Lesson**: Bài học trong khóa học
- **Exercise**: Bài tập
- **Submission**: Bài nộp của học sinh
- **Post**: Bài đăng forum
- **ChatSession**: Phiên chat với AI
- **LearningAnalytics**: Thống kê học tập

## 🎨 UI/UX Guidelines

- **Màu chủ đạo**: Primary (Blue), Secondary (Purple)
- **Typography**: Inter font family
- **Design system**: Tailwind CSS utilities
- **Responsive**: Mobile-first approach

## 🔐 Security

- JWT authentication với access & refresh tokens
- Password hashing với Django's built-in system
- CORS configuration cho production
- SQL injection prevention với ORM
- XSS protection với React

## 🚢 Deployment

### Production Settings

1. Set `DEBUG=False` trong backend/.env
2. Configure ALLOWED_HOSTS
3. Setup static files serving
4. Configure PostgreSQL production database
5. Setup SSL certificates
6. Use environment variables cho sensitive data

### Deployment Platforms

- **Backend**: Heroku, Railway, DigitalOcean
- **Frontend**: Vercel, Netlify, Cloudflare Pages
- **Database**: Railway PostgreSQL, AWS RDS

## 👥 Team

- **Nguyễn Thái Tuấn** - N23DCPT054
- **Phạng Anh Lộc** - N23DCPT033

## 📄 License

Xem file [LICENSE](LICENSE)

## 🤝 Contributing

1. Fork the project
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📞 Support

Email: n23dcpt054@student.ptithcm.edu.vn
