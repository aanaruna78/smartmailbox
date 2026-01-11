@echo off
TITLE Smart Mailbox - Database Setup
echo ===================================================
echo   Initializing Database (Migrations & Seed)
echo ===================================================

echo [1/3] Waiting for API service to be ready...
timeout /t 5 /nobreak >nul

echo.
echo [2/3] Applying Database Migrations...
docker-compose exec -T api alembic upgrade head
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Migration Failed!
    pause
    exit /b
)

echo.
echo [3/3] Seeding Admin User...
docker-compose exec -T api python /app/infra/scripts/seed_data.py
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Seeding Failed!
    pause
    exit /b
)

echo.
echo ===================================================
echo   Database Setup Complete!
echo ===================================================
echo   Admin User: admin@smartmailbox.com
echo   Password:   admin123
echo ===================================================
echo.
pause
