@echo off
setlocal enabledelayedexpansion

title Adani Website Monitoring & Uptime Analytics Platform

echo ===============================================================================
echo   ADANI WEBSITE MONITORING & UPTIME ANALYTICS - SETUP AND RUN
echo ===============================================================================
echo.

:: 1. Navigate to script directory
cd /d "%~dp0"

:: 2. Check Prerequisites
echo [Step 1/4] Checking prerequisites...
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not found in PATH.
    echo Please install Python 3.10+ and add it to your system PATH.
    pause
    exit /b 1
)

where npm >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Node.js / npm is not installed or not found in PATH.
    echo Please install Node.js and add npm to your system PATH.
    pause
    exit /b 1
)
echo Python and Node.js/npm detected successfully.
echo.

:: 3. Backend Setup
echo [Step 2/4] Setting up Python backend virtual environment and dependencies...

if not exist "backend\.env" (
    if exist ".env" (
        copy ".env" "backend\.env" >nul
        echo Created backend\.env from root .env.
    ) else if exist ".env.example" (
        copy ".env.example" "backend\.env" >nul
        echo Created backend\.env from .env.example.
    )
)

if not exist "backend\.venv\Scripts\python.exe" (
    echo Creating Python virtual environment in backend\.venv...
    python -m venv backend\.venv
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

echo Activating virtual environment and installing backend requirements...
call backend\.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install backend dependencies from requirements.txt.
    pause
    exit /b 1
)
echo Backend dependencies installed successfully.
echo.

:: 4. Frontend Setup & Build
echo [Step 3/4] Installing frontend dependencies and building production assets...
cd frontend
echo Running npm install...
call npm install
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Frontend npm install failed.
    cd ..
    pause
    exit /b 1
)

echo Building frontend production bundle...
call npm run build
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Frontend build failed.
    cd ..
    pause
    exit /b 1
)
cd ..
echo Frontend built successfully into frontend\dist.
echo.

:: 5. Launch Backend Server on Port 8008
echo [Step 4/4] Starting Adani Monitoring Server on port 8008...
echo.
echo ===============================================================================
echo   Platform is running!
echo   Web Application:   http://localhost:8008/dashboard/
echo   REST API Base:     http://localhost:8008/dashboard/api
echo   Swagger Docs:      http://localhost:8008/dashboard/docs
echo   Press Ctrl+C to stop the server.
echo ===============================================================================
echo.

python run_server.py

pause
