@echo off
:: Force use CMD and UTF-8 encoding (fix garbled code)
chcp 65001 >nul 2>&1

:: Define root directory (script location)
set "ROOT_DIR=%~dp0"
:: Remove trailing backslash to avoid path error
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"

:: Define CMD path (avoid PowerShell parsing)
if "%PROCESSOR_ARCHITECTURE%"=="AMD64" (
    set "CMD_EXE=%SystemRoot%\System32\cmd.exe"
) else (
    set "CMD_EXE=%SystemRoot%\SysWOW64\cmd.exe"
)

echo ==============================================
echo Starting AI Vision Platform Dev Env...
echo Root Directory: %ROOT_DIR%
echo ==============================================


:: 3. Start Video Processing Engine
echo Starting Video Processing Engine...
start "AI Vision Engine" "%CMD_EXE%" /k "cd /d ""%ROOT_DIR%\backend"" && python -m engine.main"

echo ==============================================
echo All services started in separate windows:
echo 1. Frontend Dev Server (frontend)
echo 2. Backend FastAPI (backend, port 8000)
echo 3. Video Processing Engine (backend/engine)
echo Close the windows to stop services.
echo ==============================================
pause >nul