@echo off
setlocal enabledelayedexpansion
title Ping Tester - Setup and Run

rem Always run from the folder this script lives in, regardless of where
rem it is double-clicked from.
cd /d "%~dp0"

echo ============================================
echo   Ping Tester - one-click setup and run
echo ============================================
echo.

rem --- 1. Find a Python interpreter (python, then the py launcher) ------
set "PYTHON="
where python >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON=python"
) else (
    where py >nul 2>nul
    if !errorlevel!==0 (
        set "PYTHON=py"
    )
)

if not defined PYTHON (
    echo [ERROR] Python was not found on this system.
    echo         Install Python 3.10+ from https://www.python.org/downloads/
    echo         and make sure "Add python.exe to PATH" is checked during install.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('%PYTHON% --version 2^>^&1') do set "PY_VERSION=%%v"
echo [OK] Found Python %PY_VERSION%
echo.

rem --- 2. Create the virtual environment if it doesn't exist yet --------
if not exist ".venv\Scripts\python.exe" (
    echo [SETUP] Creating virtual environment in .venv ...
    %PYTHON% -m venv .venv
    if not exist ".venv\Scripts\python.exe" (
        echo [ERROR] Failed to create the virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
) else (
    echo [OK] Virtual environment already exists.
)
echo.

set "VENV_PY=.venv\Scripts\python.exe"

rem --- 3. Install / update dependencies ----------------------------------
echo [SETUP] Installing dependencies from requirements.txt ...
"%VENV_PY%" -m pip install --upgrade pip --quiet
"%VENV_PY%" -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Dependency installation failed. See the messages above.
    pause
    exit /b 1
)
echo [OK] Dependencies installed.
echo.

rem --- 4. Optional .env for AI features -----------------------------------
if not exist ".env" (
    if exist ".env.example" (
        copy /y ".env.example" ".env" >nul
        echo [INFO] Created .env from .env.example.
        echo        AI features ^(Analyst / Helper chat^) are optional - add your
        echo        NVIDIA_API_KEY in .env, or set it later in Settings - AI Config.
    )
) else (
    echo [OK] .env already present.
)
echo.

rem --- 5. Launch the app and open the browser -----------------------------
echo [RUN] Starting Ping Tester on http://localhost:5050 ...
echo       Login: admin / admin123
echo       Press CTRL+C in this window to stop the server.
echo.

start "" "http://localhost:5050/dashboard"

"%VENV_PY%" app.py

echo.
echo [STOPPED] Ping Tester server has stopped.
pause
