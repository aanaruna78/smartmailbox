@echo off
TITLE Smart Mailbox - Dev Environment
echo ===================================================
echo   Starting Smart Mailbox Stack (Docker)
echo ===================================================

echo Checking if Docker is running...
docker info >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker is NOT running. Please start Docker Desktop and try again.
    pause
    exit /b
)

echo.
echo [1/2] Building and Starting Containers...
docker-compose up -d --build

echo.
echo [2/2] Checking Status...
docker-compose ps

echo.
echo ===================================================
echo   Startup Complete!
echo ===================================================
echo   Web UI:    http://localhost:3000
echo   API Docs:  http://localhost:8000/docs
echo   Mailhog:   http://localhost:8025 (if enabled)
echo ===================================================
echo.
echo To view logs, run: docker-compose logs -f
echo.
pause
