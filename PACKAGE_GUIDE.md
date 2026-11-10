# Package guide

The project dependencies are declared in `requirements.txt` and installed by `setup_windows.bat` or notebook cell 0A.

| Package | Purpose |
|---|---|
| torch | Neural network, autograd, optimizers |
| torchvision | ResNet50, image transforms, ImageFolder |
| numpy | Numeric operations and confusion matrix |
| Pillow | Image loading |
| matplotlib | Accuracy/Loss and confusion matrix charts |
| tqdm | Live batch progress bar |
| streamlit | Image prediction web UI |
| jupyterlab | Notebook interface |
| ipykernel | Python kernel integration for VS Code/Jupyter |

Install command:
```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

PyTorch GPU/CUDA builds vary by machine. The default requirements install the standard pip build; check `torch.cuda.is_available()` after installation.
