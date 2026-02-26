@echo off
REM Start Web App Server Batch File
REM Automatically uses the virtual environment

setlocal enabledelayedexpansion

cd /d "%~dp0"

echo.
echo ============================================================
echo 🌐 Shoulder Surfing Detection - Web App Server
echo ============================================================
echo.

REM Check if venv exists
if exist ".venv\Scripts\python.exe" (
    echo Using virtual environment Python...
    echo.
    echo 📍 Web App: http://localhost:5000
    echo 📍 API: http://localhost:5000/api/
    echo.
    echo ============================================================
    echo.
    
    ".venv\Scripts\python.exe" web_server.py
) else (
    echo ❌ Virtual environment not found
    echo Creating virtual environment...
    python -m venv .venv
    echo Installing dependencies...
    ".venv\Scripts\pip.exe" install -r requirements.txt > nul 2>&1
    echo.
    echo Starting server...
    echo 📍 Web App: http://localhost:5000
    echo.
    ".venv\Scripts\python.exe" web_server.py
)

pause
