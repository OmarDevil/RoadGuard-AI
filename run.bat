@echo off
setlocal

cd /d "%~dp0"

set "PYTHON_CMD=python"
set "VENV_PYTHON=.venv\Scripts\python.exe"
set "APP_URL=http://127.0.0.1:8000/frontend/index.html"

where %PYTHON_CMD% >nul 2>nul
if errorlevel 1 (
    echo [RoadGuard AI] Python was not found in PATH.
    echo Install Python 3.10+ and run this file again.
    pause
    exit /b 1
)

if not exist "%VENV_PYTHON%" (
    echo [RoadGuard AI] Creating virtual environment...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 (
        echo [RoadGuard AI] Failed to create virtual environment.
        pause
        exit /b 1
    )

    echo [RoadGuard AI] Installing dependencies. This may take a while on first run...
    "%VENV_PYTHON%" -m pip install --upgrade pip
    if errorlevel 1 (
        echo [RoadGuard AI] Failed to upgrade pip.
        pause
        exit /b 1
    )

    "%VENV_PYTHON%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [RoadGuard AI] Failed to install requirements.
        pause
        exit /b 1
    )
)

echo [RoadGuard AI] Initializing SQLite database...
"%VENV_PYTHON%" -c "from api.database import init_db; init_db()"
if errorlevel 1 (
    echo [RoadGuard AI] Database initialization failed.
    pause
    exit /b 1
)

echo [RoadGuard AI] Starting FastAPI server...
echo [RoadGuard AI] Dashboard will open at %APP_URL%
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 2; Start-Process '%APP_URL%'"
"%VENV_PYTHON%" -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload

pause
