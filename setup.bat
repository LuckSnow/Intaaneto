@echo off
echo ================================
echo   INTAANETO - First Time Setup
echo ================================
echo.

echo [1/5] Setting up Backend...
cd backend
python -m venv venv
call venv\Scripts\activate
pip install -r requirements.txt

echo.
echo [2/5] Setting up environment files...
if not exist .env copy .env.example .env
echo ⚠️  Don't forget to edit backend\.env with your database and OpenAI credentials!
echo.

cd ..
echo [3/5] Setting up Frontend...
cd frontend
call npm install
if not exist .env copy .env.example .env

cd ..
echo.
echo [4/5] Setting up database...
echo Please make sure PostgreSQL is running!
pause
cd backend
call venv\Scripts\activate
python manage.py migrate

echo.
echo [5/5] Creating superuser...
python manage.py createsuperuser

echo.
echo ================================
echo   Setup Complete! 🎉
echo ================================
echo.
echo Next steps:
echo   1. Edit backend\.env with your credentials
echo   2. Run start.bat to start the servers
echo   3. Visit http://localhost:5173
echo.
pause
