
@echo off
setlocal
title WILDFIRE INTELLIGENCE - BUILD AND RUN

cd /d "%~dp0"

echo ==========================================
echo       WILDFIRE INTELLIGENCE
echo          BUILD AND RUN
echo ==========================================
echo.

echo [1/2] BUILDING APPLICATION...
call build_winforms.bat

if errorlevel 1 (
    echo BUILD FAILED!
    pause
    exit /b 1
)

echo.
echo [2/2] STARTING APPLICATION...
call run_winforms.bat

exit /b 0
