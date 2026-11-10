
@echo off
setlocal
title WILDFIRE INTELLIGENCE

cd /d "%~dp0"

echo ==========================================
echo       WILDFIRE INTELLIGENCE
echo ==========================================
echo.

if not exist "checkpoints\best_model.pth" (
    echo ERROR: AI model not found!
    echo Please check checkpoints folder.
    pause
    exit /b 1
)

if exist "bin\Release\net48\WildfireIntelligence.exe" (
    set "APP=bin\Release\net48\WildfireIntelligence.exe"
) else if exist "bin\Release\WildfireIntelligence.exe" (
    set "APP=bin\Release\WildfireIntelligence.exe"
) else (
    echo ERROR: Application not found!
    echo Please run build_winforms.bat first.
    pause
    exit /b 1
)

echo Starting Wildfire Intelligence...
echo.

start "" "%APP%"

exit /b 0
