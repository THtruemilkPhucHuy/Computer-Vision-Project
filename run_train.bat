@echo off
cd /d "%~dp0"
title Wildfire Detection - Training and Analysis
if not exist .venv\Scripts\python.exe (
  echo Please run setup_windows.bat first.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
echo.
echo ================================================
echo  RESNET50 TRAINING - LIVE BATCH LOGGING
echo  Results: checkpoints\
echo ================================================
echo.
python train.py --data_dir Wildfire-smoke --epochs 3 --batch_size 4 --workers 0
echo.
echo Training ended. Open checkpoints\accuracy_curve.png
echo Also see checkpoints\loss_curve.png and checkpoints\confusion_matrix.png
pause
