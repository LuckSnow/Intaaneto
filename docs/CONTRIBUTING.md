# Contributing to Intaaneto

## 🎉 Cảm ơn bạn đã quan tâm đến dự án!

Hướng dẫn này sẽ giúp bạn contribute vào dự án một cách hiệu quả.

## 📋 Quy trình Contribute

### 1. Fork & Clone

```bash
# Fork repo trên GitHub
# Clone về máy
git clone https://github.com/YOUR_USERNAME/intaaneto.git
cd intaaneto

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_REPO/intaaneto.git
```

### 2. Create Branch

```bash
# Sync với main branch
git checkout main
git pull upstream main

# Tạo branch mới
git checkout -b feature/your-feature-name
# hoặc
git checkout -b fix/your-bug-fix
```

### 3. Make Changes

- Viết code theo coding standards
- Test kỹ trước khi commit
- Viết commit message rõ ràng

### 4. Commit

```bash
# Stage changes
git add .

# Commit with meaningful message
git commit -m "feat: Add AI chat interface"
```

### 5. Push & Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name

# Tạo Pull Request trên GitHub
# Mô tả chi tiết những gì bạn đã làm
```

---

## 📝 Commit Message Convention

Sử dụng [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types:
- `feat`: Thêm tính năng mới
- `fix`: Sửa bug
- `docs`: Cập nhật documentation
- `style`: Format code (không ảnh hưởng logic)
- `refactor`: Refactor code
- `test`: Thêm/sửa tests
- `chore`: Maintenance tasks

### Examples:

```bash
feat(auth): Add password reset functionality
fix(courses): Fix enrollment bug for new users
docs(readme): Update installation instructions
style(frontend): Format components with Prettier
refactor(api): Simplify authentication middleware
test(users): Add unit tests for user model
chore(deps): Update Django to 5.0.2
```

---

## 🎨 Coding Standards

### Backend (Python/Django)

```python
# Follow PEP 8
# Use Black for formatting
# Max line length: 120 characters

# Good
class Course(models.Model):
    """Course model with proper docstring"""
    
    title = models.CharField(max_length=255)
    
    def get_enrolled_students(self):
        """Return list of enrolled students"""
        return self.enrollments.filter(is_active=True)

# Bad
class course(models.Model):
    title=models.CharField(max_length=255)
    def get_enrolled_students(self):return self.enrollments.filter(is_active=True)
```

### Frontend (React/JavaScript)

```javascript
// Use functional components with hooks
// Use meaningful names
// Add PropTypes or TypeScript

// Good ✅
export default function CourseCard({ course, onEnroll }) {
  const [isLoading, setIsLoading] = useState(false)
  
  const handleEnroll = async () => {
    setIsLoading(true)
    await onEnroll(course.id)
    setIsLoading(false)
  }
  
  return (
    <div className="card">
      <h3>{course.title}</h3>
      <button onClick={handleEnroll} disabled={isLoading}>
        {isLoading ? 'Đang xử lý...' : 'Đăng ký'}
      </button>
    </div>
  )
}

// Bad ❌
export default function c({ x, y }) {
  const [a, setA] = useState(false)
  return <div onClick={() => y(x.id)}>{x.title}</div>
}
```

---

## ✅ Code Review Checklist

Trước khi submit PR, check:

### General
- [ ] Code chạy được không lỗi
- [ ] Đã test manually
- [ ] Không có console.log/print debug statements
- [ ] No hardcoded values (dùng env variables)

### Backend
- [ ] Models có proper indexes
- [ ] Serializers complete và validated
- [ ] API có proper permissions
- [ ] Migrations generated và tested
- [ ] Tests pass (`pytest`)

### Frontend
- [ ] Components reusable
- [ ] Proper error handling
- [ ] Loading states
- [ ] Responsive design
- [ ] No eslint errors

---

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest

# Specific test
pytest apps/users/tests.py::TestUserAPI::test_login

# With coverage
pytest --cov=apps
```

### Frontend Tests

```bash
cd frontend
npm test

# Coverage
npm test -- --coverage
```

---

## 🐛 Bug Reports

Khi report bug, include:

1. **Mô tả bug**: Gì đã xảy ra?
2. **Steps to reproduce**: Làm thế nào để tái hiện?
3. **Expected behavior**: Đáng ra phải như thế nào?
4. **Screenshots**: Nếu có
5. **Environment**:
   - OS: Windows/Mac/Linux
   - Browser: Chrome/Firefox/Safari
   - Python version
   - Node version

**Template:**

```markdown
## Bug Description
Brief description

## Steps to Reproduce
1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

## Expected Behavior
What should happen

## Screenshots
Add screenshots if applicable

## Environment
- OS: Windows 11
- Browser: Chrome 120
- Python: 3.11
- Node: 20.0
```

---

## 💡 Feature Requests

Khi request feature:

1. **Mô tả feature**: Feature là gì?
2. **Use case**: Ai sẽ dùng? Khi nào?
3. **Why needed**: Tại sao cần?
4. **Proposed solution**: Đề xuất cách implement (optional)

---

## 📁 Project Structure Guidelines

### Backend Structure

```
apps/
├── users/           # User management
├── courses/         # Courses & Lessons
├── exercises/       # Exercises & Submissions
├── ai_assistant/    # AI features
├── forum/           # Forum
└── analytics/       # Analytics
```

Mỗi app nên có:
- `models.py` - Database models
- `serializers.py` - DRF serializers
- `views.py` - API views
- `urls.py` - URL routing
- `admin.py` - Django admin
- `tests.py` - Tests

### Frontend Structure

```
src/
├── components/     # Reusable components
├── pages/          # Page components
├── services/       # API services
├── store/          # State management
├── hooks/          # Custom hooks
└── utils/          # Utilities
```

---

## 🚀 Development Workflow

### Daily Workflow

```bash
# 1. Sync với main
git checkout main
git pull upstream main

# 2. Update branch
git checkout your-branch
git rebase main

# 3. Make changes & test
# ... code code code ...
npm run dev    # Frontend
python manage.py runserver  # Backend

# 4. Commit
git add .
git commit -m "feat: your changes"

# 5. Push
git push origin your-branch

# 6. Create PR if ready
```

### Code Review Process

1. **Author**: Submit PR với mô tả chi tiết
2. **Reviewer**: Review code, comment feedback
3. **Author**: Address feedback, update PR
4. **Reviewer**: Approve if OK
5. **Maintainer**: Merge to main

---

## 🎯 Priority Labels

PRs/Issues được tag với:

- `priority: high` - Critical bugs, security issues
- `priority: medium` - Important features
- `priority: low` - Nice to have
- `good first issue` - Dễ cho người mới
- `help wanted` - Cần giúp đỡ
- `documentation` - Liên quan docs
- `bug` - Bug fixes
- `enhancement` - New features

---

## 🤝 Code of Conduct

- Tôn trọng mọi người
- Constructive feedback
- Không discrimination
- Help người khác
- Professional communication

---

## 📞 Get Help

- **Issues**: [GitHub Issues](https://github.com/repo/issues)
- **Discord**: [Join our Discord](#)
- **Email**: n23dcpt054@student.ptithcm.edu.vn

---

## 🙏 Thank You!

Mỗi contribution, dù lớn hay nhỏ, đều có giá trị!

Happy Coding! 🚀
