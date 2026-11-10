
@echo off
title WILDFIRE INTELLIGENCE
cd /d "%~dp0"

echo ==========================================
echo       WILDFIRE INTELLIGENCE
echo ==========================================
echo.

set "PYTHON=%~dp0.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo [ERROR] Khong tim thay Python trong .venv
    echo Hay chay setup_windows.bat truoc.
    pause
    exit /b 1
)

echo [1/3] Checking Python environment...
"%PYTHON%" --version

echo.
echo [2/3] Checking Streamlit...

"%PYTHON%" -m pip show streamlit >nul 2>&1

if errorlevel 1 (
    echo Streamlit chua duoc cai dat.
    echo Dang cai dat Streamlit...
    "%PYTHON%" -m pip install streamlit
)

echo.
echo [3/3] Starting Wildfire Intelligence...
echo.

"%PYTHON%" -m streamlit run app_premium.py

pause
