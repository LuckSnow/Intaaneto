#!/usr/bin/env sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$ROOT_DIR"

command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required."; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "Node.js/npm is required."; exit 1; }

test -x backend/venv/bin/python || python3 -m venv backend/venv
backend/venv/bin/python -m pip install --upgrade pip
backend/venv/bin/pip install -r backend/requirements.txt

test -f backend/.env || cp backend/.env.example backend/.env
test -f frontend/.env || cp frontend/.env.example frontend/.env

echo "Edit backend/.env and verify PostgreSQL credentials, then press Enter."
read -r _

(cd frontend && npm ci)
(cd backend && venv/bin/python manage.py migrate)

echo "Setup complete. Create an admin with:"
echo "  cd backend && venv/bin/python manage.py createsuperuser"
