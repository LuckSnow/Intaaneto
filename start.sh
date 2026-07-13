#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$ROOT_DIR"

test -f backend/.env || { echo "backend/.env is missing. Run ./setup.sh first."; exit 1; }
test -x backend/venv/bin/python || { echo "Backend venv is missing. Run ./setup.sh first."; exit 1; }
test -d frontend/node_modules || { echo "Frontend dependencies are missing. Run ./setup.sh first."; exit 1; }

(cd backend && venv/bin/python manage.py migrate)

cleanup() {
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

(cd backend && venv/bin/python manage.py runserver) &
BACKEND_PID=$!
(cd frontend && npm run dev) &
FRONTEND_PID=$!

echo "Frontend: http://localhost:5173"
echo "Backend:  http://localhost:8000"
wait
