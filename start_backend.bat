@echo off
echo [SHACON V2] Starting Backend Environment...
cd /d "%~dp0backend"

if not exist "venv" (
    echo [ERROR] Virtual environment not found in %CD%\venv
    echo Please run setup or ensure venv is present.
    pause
    exit /b
)

echo [SHACON V2] Activating Virtual Environment...
call venv\Scripts\activate

echo [SHACON V2] P-Core Affinity will be applied by hardware.py on startup.
echo [SHACON V2] Launching Uvicorn on http://localhost:8080...
python -m uvicorn main:app --port 8080 --reload

pause
