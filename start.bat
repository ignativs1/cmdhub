@echo off
chcp 65001 >nul
title CmdHub - Command & Telemetry Hub
cd /d "%~dp0"

echo ========================================================
echo  CmdHub - Cross-Device Command Dispatch ^& Telemetry Hub
echo ========================================================

python -c "import fastapi" 2>nul
if %errorlevel% neq 0 (
    echo [INFO] Installing required dependencies...
    pip install -r requirements.txt
)

set CMDHUB_PORT=8080
set CMDHUB_HOST=0.0.0.0

python app.py
pause
