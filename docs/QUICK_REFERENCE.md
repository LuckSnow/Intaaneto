# Intaaneto quick reference

## Docker (khuyến nghị)

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f backend frontend
docker compose exec backend python manage.py createsuperuser
docker compose down
```

Nếu container cũ mất bind mount sau khi restart Docker Desktop/WSL:

```bash
docker compose up -d --build --force-recreate db backend frontend
```

## Chạy trực tiếp

```bash
# Linux/macOS/WSL
./setup.sh
./start.sh

# Windows Command Prompt
setup.bat
start.bat
```

## URL

| Thành phần | URL |
|---|---|
| Frontend | http://localhost:5173 |
| API | http://localhost:8000/api/ |
| Admin | http://localhost:8000/admin/ |
| Swagger | http://localhost:8000/api/docs/ |
| ReDoc | http://localhost:8000/api/redoc/ |
| Adminer | http://localhost:8888 |

## Backend

```bash
cd backend
source venv/bin/activate       # Linux/macOS/WSL
# venv\Scripts\activate        # Windows Command Prompt
python manage.py migrate
python manage.py check
python manage.py makemigrations --check --dry-run
pytest
```

Chỉ chạy `python manage.py makemigrations` khi đã sửa model và muốn tạo migration
mới. Không tạo migration tự động mỗi lần setup.

## Frontend

```bash
cd frontend
npm ci
npm run dev
npm run lint
npm run build
```

Project hiện chưa khai báo script `npm test`.

## Environment

- `backend/.env`: database, server settings và khóa provider AI.
- `frontend/.env`: chỉ cấu hình công khai như `VITE_API_URL`.
- Không commit `.env`; không đặt secret trong biến `VITE_*`.

## RAG/AI hiện tại

Chat lesson nhận scope `lesson_id` do backend kiểm tra và trả contract gồm
`answer`, `citations`, `grounded`. Lesson text/PDF được version, chunk và embed
local vào PostgreSQL/pgvector; retrieval exact cosine chỉ chạy trong active source
đã authorize. Evidence yếu hoặc lesson chưa index trả fallback không gọi model;
citation được ứng dụng tạo từ selected chunk.

Hai corpus Markdown có thể nhập thành 2 course/15 lesson draft; command riêng tạo
3 assessment draft/27 câu tách khỏi RAG. Xem `docs/SETUP.md`. Grounded-answer
live baseline V1 đã có nhưng chưa thay thế multi-lesson/human evaluation.
