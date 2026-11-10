@echo off
setlocal
cd /d "%~dp0"
title Wildfire Detection - Full Environment Setup

echo ================================================
echo  WILDFIRE DETECTION - PYTHON 3.11 ENVIRONMENT
echo ================================================

if not exist .venv\Scripts\python.exe (
    py -3.11 -m venv .venv
    if errorlevel 1 (
        echo Cannot create Python 3.11 venv.
        echo Install Python 3.11 x64 and enable "Add Python to PATH".
        pause
        exit /b 1
    )
)

.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto install_error

echo.
echo Installing PyTorch, TorchVision, JupyterLab and project packages...
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto install_error

echo.
echo Registering Jupyter kernel...
.venv\Scripts\python.exe -m ipykernel install --user --name wildfire-detection --display-name "Python 3.11 - Wildfire Detection"
if errorlevel 1 goto install_error

echo.
echo Checking imports...
.venv\Scripts\python.exe -c "import torch, torchvision, numpy, matplotlib, PIL, tqdm; print('PyTorch:',torch.__version__); print('TorchVision:',torchvision.__version__); print('CUDA:',torch.cuda.is_available())"
if errorlevel 1 goto install_error

echo.
echo SETUP COMPLETE.
echo Next: run_notebook.bat for Jupyter, run_train.bat for CMD training,
echo or run_python_train.bat for the standalone Python training script.
pause
exit /b 0

:install_error
echo.
echo SETUP FAILED. Check Internet connection and the error above.
echo For GPU-specific PyTorch installation, see https://pytorch.org/get-started/locally/
pause
exit /b 1
