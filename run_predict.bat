@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (echo Run setup_windows.bat first.& pause & exit /b 1)
call .venv\Scripts\activate.bat
if "%~1"=="" (echo Usage: drag an image onto this file or run: python predict.py --image path\to\image.jpg & pause & exit /b 1)
python predict.py --image "%~1"
pause
