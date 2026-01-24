# ⚡ Quick Reference - Intaaneto

## 🚀 Quick Start

```bash
# First time setup
setup.bat

# Daily development
start.bat
```

---

## 🔗 Important URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | React app |
| Backend API | http://localhost:8000/api | REST API |
| Admin Panel | http://localhost:8000/admin | Django admin |
| API Docs (Swagger) | http://localhost:8000/api/docs | Interactive API docs |
| API Docs (ReDoc) | http://localhost:8000/api/redoc | Alternative docs |

---

## 📂 Project Structure

```
Intaaneto/
├── backend/          # Django (Python)
├── frontend/         # React (JavaScript)
├── docs/            # Documentation
├── docker-compose.yml
└── README.md
```

---

## 🛠️ Common Commands

### Backend

```bash
# Activate venv
cd backend
venv\Scripts\activate

# Run server
python manage.py runserver

# Migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Django shell
python manage.py shell

# Run tests
pytest

# Format code
black .
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev

# Build for production
npm run build

# Lint code
npm run lint
```

### Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild
docker-compose up -d --build
```

---

## 📝 File Locations

### Configuration

| File | Location | Purpose |
|------|----------|---------|
| Backend Settings | `backend/config/settings/` | Django settings |
| Backend URLs | `backend/config/urls.py` | URL routing |
| Frontend Config | `frontend/vite.config.js` | Vite config |
| Tailwind Config | `frontend/tailwind.config.js` | Styling |
| Docker Compose | `docker-compose.yml` | Container orchestration |

### Environment Variables

| File | Location | Purpose |
|------|----------|---------|
| Backend .env | `backend/.env` | DB, API keys |
| Frontend .env | `frontend/.env` | API URL |

### Database Models

| App | File | Models |
|-----|------|--------|
| users | `backend/apps/users/models.py` | User, Profile |
| courses | `backend/apps/courses/models.py` | Course, Lesson, etc. |
| exercises | `backend/apps/exercises/models.py` | Exercise, Submission |
| forum | `backend/apps/forum/models.py` | Post, Comment |
| ai_assistant | `backend/apps/ai_assistant/models.py` | ChatSession |
| analytics | `backend/apps/analytics/models.py` | Analytics, Achievement |

---

## 🔐 Default Credentials

### Development

Create using: `python manage.py createsuperuser`

Example:
- Email: `admin@example.com`
- Username: `admin`
- Password: `admin123456`

---

## 🎨 Tailwind Classes

### Common Patterns

```jsx
// Button
<button className="btn btn-primary">Click</button>

// Card
<div className="card">Content</div>

// Input
<input className="input" />

// Custom button
<button className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
  Button
</button>
```

### Colors

- Primary: `primary-50` to `primary-900`
- Secondary: `secondary-50` to `secondary-900`
- Gray: `gray-50` to `gray-900`

---

## 🔌 API Endpoints

### Authentication

```
POST   /api/auth/register/
POST   /api/auth/login/
POST   /api/auth/logout/
GET    /api/auth/users/me/
PUT    /api/auth/users/update_profile/
```

### Courses

```
GET    /api/courses/
GET    /api/courses/{id}/
POST   /api/courses/{id}/enroll/
GET    /api/courses/{id}/progress/
POST   /api/courses/lessons/{id}/complete/
```

### AI Assistant

```
POST   /api/ai/chat/send_message/
POST   /api/ai/chat/explain_code/
POST   /api/ai/chat/get_hint/
GET    /api/ai/chat/
GET    /api/ai/chat/{id}/
```

### Forum

```
GET    /api/forum/posts/
POST   /api/forum/posts/
GET    /api/forum/posts/{id}/
POST   /api/forum/posts/{id}/like/
POST   /api/forum/posts/{id}/mark_solved/
GET    /api/forum/comments/
POST   /api/forum/comments/
```

---

## 🧪 Testing

### Backend Tests

```bash
cd backend

# All tests
pytest

# Specific app
pytest apps/users/tests.py

# Specific test
pytest apps/users/tests.py::TestUserAPI::test_login

# With coverage
pytest --cov=apps

# Verbose
pytest -v
```

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Watch mode
npm test -- --watch

# Coverage
npm test -- --coverage
```

---

## 🐛 Debugging

### Backend Debug

```python
# Add to code
import pdb; pdb.set_trace()

# Or use print
print(f"Debug: {variable}")

# Django shell
python manage.py shell

# Check SQL queries
from django.db import connection
print(connection.queries)
```

### Frontend Debug

```javascript
// Console log
console.log('Debug:', data)

// React DevTools
// Install browser extension

// Check API calls
// Open Network tab in DevTools
```

---

## 📊 Database

### PostgreSQL Commands

```bash
# Connect to database
psql -U postgres -d intaaneto_db

# Inside psql:
\dt              # List tables
\d users_user    # Describe table
\q               # Quit

# Django shell
python manage.py dbshell
```

### Common Queries

```python
# In Django shell
from apps.users.models import User

# Get all users
User.objects.all()

# Filter
User.objects.filter(role='student')

# Get one
user = User.objects.get(email='test@example.com')

# Create
user = User.objects.create_user(
    email='new@example.com',
    username='newuser',
    full_name='New User',
    password='pass123'
)

# Update
user.full_name = 'Updated Name'
user.save()

# Delete
user.delete()
```

---

## 🔑 Environment Variables

### Backend (.env)

```env
# Required
SECRET_KEY=your-secret-key
DEBUG=True
DB_NAME=intaaneto_db
DB_USER=postgres
DB_PASSWORD=your-password
OPENAI_API_KEY=sk-your-key

# Optional
DB_HOST=localhost
DB_PORT=5432
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

### Frontend (.env)

```env
VITE_API_URL=http://localhost:8000/api
```

---

## 🚨 Common Errors & Fixes

### "No module named 'xxx'"
```bash
cd backend
venv\Scripts\activate
pip install -r requirements.txt
```

### "Connection refused" (Database)
```bash
# Check PostgreSQL is running
# Windows: Services -> PostgreSQL
# Or use Docker:
docker run -p 5432:5432 -e POSTGRES_PASSWORD=postgres -d postgres:15
```

### "CORS error"
```bash
# Check CORS_ALLOWED_ORIGINS in backend/.env
# Restart backend server
```

### "npm ERR!"
```bash
cd frontend
rmdir /s node_modules
npm install
```

### Port already in use
```bash
# Kill process on port
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

## 📚 Resources

### Documentation
- [Django Docs](https://docs.djangoproject.com/)
- [DRF Docs](https://www.django-rest-framework.org/)
- [React Docs](https://react.dev/)
- [Tailwind Docs](https://tailwindcss.com/)

### Learning
- [Django Tutorial](https://www.djangoproject.com/start/)
- [React Tutorial](https://react.dev/learn)
- [REST API Design](https://restfulapi.net/)

### Tools
- [Postman](https://www.postman.com/) - API testing
- [DBeaver](https://dbeaver.io/) - Database GUI
- [React DevTools](https://react.dev/learn/react-developer-tools)

---

## 💡 Tips & Tricks

### Backend

1. **Use Django shell for quick tests**
```bash
python manage.py shell_plus  # If django-extensions installed
```

2. **Debug SQL queries**
```python
from django.db import connection
print(len(connection.queries))  # After ORM operations
```

3. **Reset database**
```bash
python manage.py flush
```

### Frontend

1. **Quick component testing**
```javascript
// Add console.log to see renders
console.log('Component rendered:', props)
```

2. **React Query DevTools**
```javascript
// Add to main.jsx for debugging
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
```

3. **Tailwind JIT mode**
```javascript
// Already enabled in config
// Just use any Tailwind class
```

---

## 🎯 Next Steps Checklist

- [ ] Setup project (`setup.bat`)
- [ ] Edit `.env` files
- [ ] Run migrations
- [ ] Create superuser
- [ ] Start servers (`start.bat`)
- [ ] Test login/register
- [ ] Create sample course in admin
- [ ] Test AI chat (with OpenAI key)
- [ ] Start building features!

---

**Need Help?**
- Check [SETUP.md](SETUP.md)
- Check [README.md](README.md)
- Check [docs/](docs/)
- Email: n23dcpt054@student.ptithcm.edu.vn
