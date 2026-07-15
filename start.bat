@echo off
setlocal
cd /d "%~dp0"

if not exist backend\.env (
  echo ERROR: backend\.env is missing. Run setup.bat first.
  exit /b 1
)
if not exist backend\venv\Scripts\python.exe (
  echo ERROR: backend virtual environment is missing. Run setup.bat first.
  exit /b 1
)
if not exist frontend\node_modules (
  echo ERROR: frontend dependencies are missing. Run setup.bat first.
  exit /b 1
)

echo Checking migrations and database connection...
pushd backend
call venv\Scripts\activate
python manage.py migrate
if errorlevel 1 (
  popd
  echo ERROR: PostgreSQL is not available or backend\.env is incorrect.
  exit /b 1
)
popd

echo Starting backend and frontend...
start "Intaaneto Backend" cmd /k "cd /d ""%~dp0backend"" && venv\Scripts\activate && python manage.py runserver"
start "Intaaneto Frontend" cmd /k "cd /d ""%~dp0frontend"" && npm run dev"

timeout /t 5 /nobreak >nul
start http://localhost:5173

echo Frontend: http://localhost:5173
echo Backend:  http://localhost:8000
echo Admin:    http://localhost:8000/admin
echo API Docs: http://localhost:8000/api/docs/
exit /b 0
