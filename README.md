# Wildfire Detection - Training & Analysis Bundle

## What is included
- ResNet50 training source (`train.py`) with explanatory comments.
- Per-mini-batch progress in the terminal and `checkpoints/logs/training.log`.
- `checkpoints/history.csv`: one row per epoch (Excel-compatible).
- `checkpoints/accuracy_curve.png`: train/test accuracy by epoch.
- `checkpoints/loss_curve.png`: train/test loss by epoch.
- `checkpoints/confusion_matrix.png`: test-set confusion matrix.
- `checkpoints/classification_report.txt`: precision, recall, F1 and support.
- `checkpoints/best_model.pth`: best model checkpoint.
- Synthetic demo dataset (Fire / Neutral / Smoke).

## Important dataset warning
The included images are procedurally generated synthetic illustrations, not real wildfire photographs. This dataset is only for verifying installation, data loading, model training, chart export, checkpoint saving and the demo UI. Accuracy measured on it is NOT real-world wildfire detection accuracy. Do not use this model for emergency alerts or safety decisions. Replace it with a properly licensed, diverse real-world dataset before research or deployment.

## Windows setup
1. Install Python 3.11 x64: https://www.python.org/downloads/release/python-3119/
2. Extract the ZIP.
3. Double-click `setup_windows.bat`.
4. Double-click `run_train.bat`.
5. After training, inspect the `checkpoints` folder.
6. Double-click `run_app.bat` to open the Streamlit interface.

PowerShell activation policy is not an issue when using the `.bat` launchers: they activate with `activate.bat`.

## Observe training
The terminal shows a progress bar for every epoch and logs each mini-batch's running loss and accuracy. A permanent text log is saved to:
`checkpoints/logs/training.log`

## Exported analysis
After each epoch:
- `history.csv` is updated.
- `accuracy_curve.png` is updated.
- `loss_curve.png` is updated.

After training completes:
- `confusion_matrix.png`
- `classification_report.txt`

Open PNG files directly or insert them into a report. Open `history.csv` in Excel.

## Change number of epochs
Open `run_train.bat` in Notepad and edit `--epochs 3` to a larger number, e.g. `--epochs 20`. The included synthetic dataset is tiny, so more epochs do not make its results representative of real-world performance.

## Manual command
```powershell
.venv\Scripts\python.exe train.py --data_dir Wildfire-smoke --epochs 3 --batch_size 4 --workers 0
```

## Project structure
```text
Wildfire-Detection-Training-Analysis/
  train.py
  predict.py
  app.py
  requirements.txt
  setup_windows.bat
  run_train.bat
  run_app.bat
  Wildfire-smoke/
    Train/Fire, Neutral, Smoke/
    Test/Fire, Neutral, Smoke/
  checkpoints/             # created automatically during training
```


## Jupyter Notebook and code map (new)
- `train.py` — MAIN training source code. This is the file to inspect/edit for the full training loop, batch logging, evaluation and chart export.
- `notebooks/Wildfire_Detection_ResNet50_Training_Lab.ipynb` — guided Jupyter Notebook with environment checks, dataset exploration, ResNet50 setup, training execution, charts and inference.
- `predict.py` — loads `best_model.pth` and predicts one image.
- `app.py` — Streamlit image-upload interface.
- `requirements.txt` — Python dependencies, including JupyterLab and ipykernel.
- `run_notebook.bat` — launches JupyterLab directly into the training notebook.
- `run_train.bat` — launches training from Windows CMD.

### Start Jupyter Notebook
1. Run `setup_windows.bat` once (it now installs JupyterLab).
2. Run `run_notebook.bat`.
3. In the browser, execute notebook cells from top to bottom using **Run**.
4. In section 6, the notebook runs `train.py`; batch progress is visible in the notebook output.
5. Open section 7 and 8 to view accuracy/loss curves and confusion matrix.

### Where is the training code?
Open `train.py` in VS Code for the complete Python source. Open the `.ipynb` file in JupyterLab for a step-by-step, interactive explanation and execution. The notebook calls the same `train.py`, so both use the same training implementation.

## Bản ZIP cài package tự động (bổ sung)
- Notebook có cell **0A. Cài thư viện tự động cho Kernel đang chọn**: cài toàn bộ `requirements.txt` vào đúng Python interpreter của kernel.
- `setup_windows.bat`: tạo `.venv` bằng Python 3.11, cài package, đăng ký Jupyter kernel và kiểm tra import.
- `wildfire_train.py`: file Python training độc lập, không cần mở notebook.
- `run_python_train.bat`: chạy `wildfire_train.py` bằng môi trường `.venv`.
- `run_notebook.bat`: khởi chạy JupyterLab bằng đúng Python trong `.venv`.

**Lưu ý:** ZIP không chứa sẵn thư mục `.venv` hay các wheel PyTorch. Môi trường Python phụ thuộc Windows, phiên bản Python và CPU/GPU của máy, nên script sẽ tải/cài package trên máy lần đầu. Cần kết nối Internet. Không thể đảm bảo có sẵn CUDA nếu máy không có GPU NVIDIA và driver phù hợp.
