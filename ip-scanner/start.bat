@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
title IP Scanner Web v1.0.0

cd /d "%~dp0"

echo.
echo ============================================
echo   IP Scanner Web Service v1.0.0
echo ============================================
echo.

set "BOOT_PYTHON="

for %%V in (3.13 3.12 3.11 3.10) do (
    py -%%V -c "import sys" >nul 2>&1
    if !errorlevel! equ 0 (
        set "BOOT_PYTHON=py -%%V"
        goto :python_found
    )
)

python -c "import sys; raise SystemExit(sys.version_info.major < 3 or sys.version_info.minor < 10)" >nul 2>&1
if %errorlevel% equ 0 (
    set "BOOT_PYTHON=python"
    goto :python_found
)

echo [ERROR] Python 3.10 or newer was not found.
echo Please install Python 3.10/3.11/3.12/3.13 and enable "Add python.exe to PATH".
echo Download: https://www.python.org/downloads/windows/
pause
exit /b 1

:python_found
echo [INFO] Using Python launcher: %BOOT_PYTHON%

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import sys; print(sys.executable)" >nul 2>&1
    if errorlevel 1 (
        echo [WARN] Existing .venv is invalid or copied from another computer.
        echo [INFO] Recreating .venv ...
        rmdir /s /q ".venv"
    )
)

if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Creating virtual environment .venv ...
    %BOOT_PYTHON% -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        echo Try reinstalling Python, then run this script again.
        pause
        exit /b 1
    )
)

set "PYTHON=.venv\Scripts\python.exe"

echo [INFO] Checking pip ...
"%PYTHON%" -m ensurepip --upgrade >nul 2>&1
"%PYTHON%" -m pip install --disable-pip-version-check --upgrade pip setuptools wheel
if errorlevel 1 (
    echo [WARN] pip upgrade failed. Continuing with dependency install ...
)

echo [INFO] Checking required packages ...
"%PYTHON%" -c "import flask, ping3, rich, openpyxl" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing required packages ...
    "%PYTHON%" -m pip install --disable-pip-version-check -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install required packages.
        echo Common causes:
        echo 1. Network cannot access PyPI
        echo 2. Corporate proxy or antivirus blocked pip
        echo 3. Python installation is incomplete
        echo.
        echo Manual retry:
        echo "%PYTHON%" -m pip install -r requirements.txt -i https://pypi.org/simple
        echo.
        pause
        exit /b 1
    )
)

echo [OK] Dependencies are ready.
echo.
echo URL: http://localhost:3000
echo Press Ctrl+C to stop the service.
echo.

start "" http://localhost:3000
"%PYTHON%" web_server.py

pause
