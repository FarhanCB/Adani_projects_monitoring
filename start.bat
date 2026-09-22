@echo off
title Ping Tester

echo ========================================
echo        Starting Ping Tester
echo ========================================

echo.
echo [1/4] Creating virtual environment...
python -m venv .venv

echo.
echo [2/4] Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo [3/4] Installing requirements...
python -m pip install -r requirements.txt

echo.
echo [4/4] Starting application...
python app.py

pause