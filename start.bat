@echo off
echo ================================
echo   INTAANETO - Quick Start
echo ================================
echo.

echo [1/3] Starting Backend Server...
start cmd /k "cd backend && venv\Scripts\activate && python manage.py runserver"

timeout /t 5 /nobreak > nul

echo [2/3] Starting Frontend Server...
start cmd /k "cd frontend && npm run dev"

timeout /t 3 /nobreak > nul

echo [3/3] Opening Browser...
timeout /t 5 /nobreak > nul
start http://localhost:5173

echo.
echo ================================
echo   Servers are running!
echo ================================
echo   Frontend: http://localhost:5173
echo   Backend:  http://localhost:8000
echo   Admin:    http://localhost:8000/admin
echo   API Docs: http://localhost:8000/api/docs
echo ================================
echo.
pause
