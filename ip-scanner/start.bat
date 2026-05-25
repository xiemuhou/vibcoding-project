@echo off
chcp 65001 >nul
title 设备IP采集程序 v1.0.0

cd /d "%~dp0"

:: 检查虚拟环境
if exist ".venv\Scripts\python.exe" (
    set PYTHON=.venv\Scripts\python.exe
    echo [*] 使用虚拟环境
) else (
    set PYTHON=python
    echo [*] 使用系统 Python
)

:: 检查依赖
%PYTHON% -c "import flask, ping3, rich" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 正在安装依赖...
    %PYTHON% -m pip install -r requirements.txt -q
    if %errorlevel% neq 0 (
        echo [X] 依赖安装失败，请手动执行: pip install -r requirements.txt
        pause
        exit /b 1
    )
    echo [✓] 依赖安装完成
)

:: 启动 Web 服务
echo.
echo ============================================
echo   设备IP采集程序 Web 服务 v1.0.0
echo   访问地址: http://localhost:3000
echo   按 Ctrl+C 停止服务
echo ============================================
echo.

start "" http://localhost:3000
%PYTHON% web_server.py

pause
