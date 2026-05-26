@echo off
title IP Manager

echo ========================================
echo   IP Address Manager
echo ========================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

cd /d "%~dp0backend"

echo Checking dependencies...
pip install -r requirements.txt -q 2>nul
if %errorlevel% neq 0 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
)

echo.
echo ----------------------------------------
echo   URL:      http://127.0.0.1:5000
echo   Account:  admin / admin123
echo ----------------------------------------
echo   Press Ctrl+C to stop
echo ========================================
echo.

python app.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Server failed to start.
)

pause
