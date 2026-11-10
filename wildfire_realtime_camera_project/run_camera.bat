@echo off
title Wildfire Intelligence - Realtime Camera
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Creating virtual environment...
    py -3 -m venv .venv
)

echo [2/3] Activating environment...
call .venv\Scripts\activate

echo [3/3] Installing camera requirements...
python -m pip install --upgrade pip
pip install -r requirements-camera.txt

echo.
echo Make sure your existing project has:
echo   - predict.py
echo   - checkpoints\best_model.pth
echo   - the dependencies required by your model (especially PyTorch)
echo.
echo Starting Streamlit...
python -m streamlit run app_camera_realtime.py
pause
