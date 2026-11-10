
@echo off
setlocal
title WILDFIRE INTELLIGENCE - BUILD

cd /d "%~dp0"

echo ==========================================
echo       WILDFIRE INTELLIGENCE
echo          BUILD APPLICATION
echo ==========================================
echo.

if not exist "WildfireIntelligence.csproj" (
    echo ERROR: Cannot find project file!
    pause
    exit /b 1
)

echo [1/3] Restoring project...
dotnet restore "WildfireIntelligence.csproj"

if errorlevel 1 goto ERROR

echo.
echo [2/3] Building application...
dotnet build "WildfireIntelligence.csproj" -c Release --no-restore

if errorlevel 1 goto ERROR

echo.
echo [3/3] BUILD SUCCESSFUL!
echo.
echo Application is ready.
echo.

pause
exit /b 0

:ERROR
echo.
echo ==========================================
echo BUILD FAILED!
echo Check errors above.
echo ==========================================
pause
exit /b 1
