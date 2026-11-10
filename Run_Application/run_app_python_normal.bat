
@echo off
title WILDFIRE DETECTION - AI APPLICATION

cd /d "%~dp0"

echo ==========================================
echo       WILDFIRE DETECTION SYSTEM
echo ==========================================

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Python virtual environment not found.
    echo Please run setup_windows.bat first.
    pause
    exit /b 1
)

echo.
echo Checking Streamlit...

.venv\Scripts\python.exe -m pip show streamlit >nul 2>&1

if errorlevel 1 (
    echo Installing Streamlit...
    .venv\Scripts\python.exe -m pip install streamlit
)

echo.
echo Starting Wildfire Detection App...
echo.

.venv\Scripts\python.exe -m streamlit run app.py

pause
