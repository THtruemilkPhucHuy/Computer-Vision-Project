
@echo off
title WILDFIRE INTELLIGENCE DESKTOP

echo ==========================================
echo       WILDFIRE INTELLIGENCE
echo       C# WINDOWS DESKTOP APPLICATION
echo ==========================================
echo.

cd /d "%~dp0"

echo [1/3] Checking project...

if not exist "WildfireIntelligence.csproj" (
    echo ERROR: Cannot find csproj file!
    pause
    exit /b 1
)

echo [2/3] Building application...

dotnet build "WildfireIntelligence.csproj" -c Release

if errorlevel 1 (
    echo.
    echo BUILD FAILED!
    pause
    exit /b 1
)

echo.
echo [3/3] Launching application...

start "" "%~dp0bin\Release\WildfireIntelligence.exe"

echo Application launched!
exit /b 0
