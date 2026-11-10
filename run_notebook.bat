@echo off
cd /d "%~dp0"
title Wildfire Detection - JupyterLab
if not exist .venv\Scripts\python.exe (
  echo Run setup_windows.bat first.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m jupyter lab notebooks\Wildfire_Detection_ResNet50_Training_Lab.ipynb
pause
