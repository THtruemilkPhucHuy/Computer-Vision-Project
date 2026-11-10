@echo off
cd /d "%~dp0"
title Wildfire Detection - Standalone Python Training
if not exist .venv\Scripts\python.exe (
  echo Run setup_windows.bat first.
  pause
  exit /b 1
)
.venv\Scripts\python.exe wildfire_train.py --data_dir Wildfire-smoke --epochs 3 --batch_size 4 --workers 0 --output_dir checkpoints
pause
