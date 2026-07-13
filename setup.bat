@echo off
setlocal
cd /d "%~dp0"

echo ================================
echo   INTAANETO - First Time Setup
echo ================================

where python >nul 2>nul || goto :missing_python
where npm >nul 2>nul || goto :missing_node

echo [1/5] Creating backend virtual environment...
if not exist backend\venv\Scripts\python.exe python -m venv backend\venv
if errorlevel 1 goto :error

call backend\venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
if errorlevel 1 goto :error

echo [2/5] Preparing environment files...
if not exist backend\.env copy backend\.env.example backend\.env >nul
if not exist frontend\.env copy frontend\.env.example frontend\.env >nul
echo.
echo Edit backend\.env now and verify PostgreSQL credentials.
echo OPENAI_API_KEY may remain empty until AI chat is tested.
pause

echo [3/5] Installing frontend dependencies from package-lock.json...
pushd frontend
call npm ci
if errorlevel 1 (popd & goto :error)
popd

echo [4/5] Checking database and applying committed migrations...
pushd backend
python manage.py migrate
if errorlevel 1 (popd & goto :database_error)

echo [5/5] Creating an administrator...
python manage.py createsuperuser
if errorlevel 1 (popd & goto :error)
popd

echo.
echo Setup complete. Run start.bat for local development,
echo or use: docker compose up -d --build
exit /b 0

:missing_python
echo ERROR: Python was not found in PATH.
exit /b 1

:missing_node
echo ERROR: npm was not found in PATH. Install Node.js 20 or newer.
exit /b 1

:database_error
echo ERROR: Cannot migrate the database. Start PostgreSQL and check backend\.env.
exit /b 1

:error
echo ERROR: Setup stopped because a command failed.
exit /b 1
