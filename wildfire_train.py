"""
WILDFIRE DETECTION - RESNET50 TRAINING
------------------------------------------------------------
Training pipeline:
1) Load Train/Test folders using ImageFolder.
2) Build ResNet50.
3) Train one mini-batch at a time.
4) Print and save per-batch progress to logs/training.log.
5) Evaluate on Test after every epoch.
6) Export history.csv, accuracy/loss charts, confusion matrix,
   and classification_report.txt.

NOTE: Included demo images are synthetic illustrations. They only
verify that the software pipeline works; they do NOT measure real
wildfire detection performance.
"""
from pathlib import Path
import argparse, csv, json, random, logging, time

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models
from tqdm import tqdm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CLASSES = ["Fire", "Neutral", "Smoke"]

def setup_logger(output_dir: Path):
    """Write the same progress messages to terminal and logs/training.log."""
    log_dir = output_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("wildfire_training")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    file_handler = logging.FileHandler(log_dir / "training.log", encoding="utf-8")
    file_handler.setFormatter(fmt)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(fmt)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger

def seed_everything(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def build_model(num_classes):
    # weights=None means no internet download is required.
    return models.resnet50(weights=None, num_classes=num_classes)

def evaluate(model, loader, criterion, device):
    """Evaluate model on the held-out Test folder."""
    model.eval()
    total_loss, correct, total = 0.0, 0, 0
    all_true, all_pred = [], []
    with torch.inference_mode():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            logits = model(images)
            loss = criterion(logits, labels)
            predictions = logits.argmax(dim=1)
            total_loss += loss.item() * labels.size(0)
            correct += (predictions == labels).sum().item()
            total += labels.size(0)
            all_true.extend(labels.cpu().tolist())
            all_pred.extend(predictions.cpu().tolist())
    return total_loss / max(total, 1), correct / max(total, 1), all_true, all_pred

def save_history_csv(history, path):
    """Export one row per epoch so results can be opened in Excel."""
    if not history:
        return
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(history[0].keys()))
        writer.writeheader()
        writer.writerows(history)

def save_training_charts(history, output_dir):
    """Export accuracy and loss curves as PNG files."""
    epochs = [row["epoch"] for row in history]

    plt.figure(figsize=(9, 5))
    plt.plot(epochs, [r["train_accuracy"] for r in history],
             marker="o", label="Train accuracy")
    plt.plot(epochs, [r["test_accuracy"] for r in history],
             marker="s", label="Test accuracy")
    plt.title("ResNet50 - Accuracy by Epoch")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.ylim(0, 1.05)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "accuracy_curve.png", dpi=160)
    plt.close()

    plt.figure(figsize=(9, 5))
    plt.plot(epochs, [r["train_loss"] for r in history],
             marker="o", label="Train loss")
    plt.plot(epochs, [r["test_loss"] for r in history],
             marker="s", label="Test loss")
    plt.title("ResNet50 - Loss by Epoch")
    plt.xlabel("Epoch")
    plt.ylabel("Cross-entropy loss")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "loss_curve.png", dpi=160)
    plt.close()

def save_confusion_matrix(y_true, y_pred, class_names, output_dir):
    """Create a confusion matrix without requiring scikit-learn."""
    n = len(class_names)
    matrix = np.zeros((n, n), dtype=int)
    for actual, predicted in zip(y_true, y_pred):
        matrix[actual, predicted] += 1

    fig, ax = plt.subplots(figsize=(7, 6))
    image = ax.imshow(matrix, cmap="Blues")
    fig.colorbar(image, ax=ax)
    ax.set_xticks(range(n), class_names, rotation=25)
    ax.set_yticks(range(n), class_names)
    ax.set_xlabel("Predicted label")
    ax.set_ylabel("True label")
    ax.set_title("Confusion Matrix - Test Set")
    threshold = matrix.max() / 2 if matrix.size else 0
    for i in range(n):
        for j in range(n):
            ax.text(j, i, str(matrix[i, j]), ha="center", va="center",
                    color="white" if matrix[i, j] > threshold else "black")
    fig.tight_layout()
    fig.savefig(output_dir / "confusion_matrix.png", dpi=160)
    plt.close(fig)

    # Per-class precision/recall/F1 report, computed directly.
    lines = ["CLASSIFICATION REPORT (Test set)", "",
             f"{'Class':<12}{'Precision':>12}{'Recall':>12}{'F1-score':>12}{'Support':>10}"]
    for i, name in enumerate(class_names):
        tp = matrix[i, i]
        fp = matrix[:, i].sum() - tp
        fn = matrix[i, :].sum() - tp
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        support = matrix[i, :].sum()
        lines.append(f"{name:<12}{precision:>12.4f}{recall:>12.4f}{f1:>12.4f}{support:>10d}")
    (output_dir / "classification_report.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")

def main():
    parser = argparse.ArgumentParser(description="Train ResNet50 wildfire classifier")
    parser.add_argument("--data_dir", default="Wildfire-smoke")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch_size", type=int, default=4)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--output_dir", default="checkpoints")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    seed_everything(args.seed)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = setup_logger(output_dir)

    data_root = Path(args.data_dir)
    train_dir, test_dir = data_root / "Train", data_root / "Test"
    if not train_dir.is_dir() or not test_dir.is_dir():
        raise SystemExit(
            f"Dataset not found. Expected {train_dir}/<class> and {test_dir}/<class>."
        )

    # Convert each image to a normalized 224x224 tensor for ResNet50.
    transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.5] * 3, [0.5] * 3),
    ])

    train_data = datasets.ImageFolder(str(train_dir), transform=transform)
    test_data = datasets.ImageFolder(str(test_dir), transform=transform)
    if train_data.classes != test_data.classes:
        raise SystemExit("Train and Test class folders must match.")
    if len(train_data.classes) != 3:
        raise SystemExit(f"Expected 3 classes; found {train_data.classes}.")

    synthetic = (data_root / "DATASET_NOTICE.txt").exists()
    dataset_type = "synthetic_demo" if synthetic else "external_dataset"
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Classes: %s", train_data.class_to_idx)
    logger.info("Train images: %d | Test images: %d", len(train_data), len(test_data))
    logger.info("Device: %s", device)
    if synthetic:
        logger.warning("SYNTHETIC DEMO DATA: metrics are not real-world performance.")

    train_loader = DataLoader(
        train_data, batch_size=args.batch_size, shuffle=True,
        num_workers=args.workers, pin_memory=(device.type == "cuda"))
    test_loader = DataLoader(
        test_data, batch_size=args.batch_size, shuffle=False,
        num_workers=args.workers, pin_memory=(device.type == "cuda"))

    model = build_model(len(train_data.classes)).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    scheduler = torch.optim.lr_scheduler.MultiStepLR(
        optimizer, milestones=[max(1, args.epochs // 2)], gamma=0.1)
    scaler = torch.amp.GradScaler("cuda", enabled=(device.type == "cuda"))

    history = []
    best_accuracy = -1.0
    best_true, best_pred = [], []

    for epoch in range(1, args.epochs + 1):
        epoch_start = time.time()
        model.train()
        running_loss, correct, total = 0.0, 0, 0
        progress = tqdm(
            enumerate(train_loader, start=1),
            total=len(train_loader),
            desc=f"Epoch {epoch}/{args.epochs} [TRAIN]",
            unit="batch"
        )

        for batch_index, (images, labels) in progress:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad(set_to_none=True)

            # Forward pass: compute model predictions and loss.
            with torch.autocast(
                device_type=device.type,
                dtype=torch.float16,
                enabled=(device.type == "cuda")
            ):
                logits = model(images)
                loss = criterion(logits, labels)

            # Backpropagation and optimizer update.
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            predictions = logits.argmax(dim=1)
            batch_count = labels.size(0)
            running_loss += loss.item() * batch_count
            correct += (predictions == labels).sum().item()
            total += batch_count

            batch_loss = running_loss / max(total, 1)
            batch_accuracy = correct / max(total, 1)
            progress.set_postfix(loss=f"{batch_loss:.4f}",
                                 accuracy=f"{batch_accuracy:.3f}")

            # Log every mini-batch so the learning process is visible.
            logger.info(
                "Epoch %d/%d | Batch %d/%d | running_loss=%.4f | running_accuracy=%.4f",
                epoch, args.epochs, batch_index, len(train_loader),
                batch_loss, batch_accuracy
            )

        train_loss = running_loss / max(total, 1)
        train_accuracy = correct / max(total, 1)
        test_loss, test_accuracy, y_true, y_pred = evaluate(
            model, test_loader, criterion, device)
        scheduler.step()

        row = {
            "epoch": epoch,
            "train_loss": round(train_loss, 6),
            "train_accuracy": round(train_accuracy, 6),
            "test_loss": round(test_loss, 6),
            "test_accuracy": round(test_accuracy, 6),
            "learning_rate": optimizer.param_groups[0]["lr"],
            "seconds": round(time.time() - epoch_start, 2),
        }
        history.append(row)
        save_history_csv(history, output_dir / "history.csv")
        save_training_charts(history, output_dir)

        logger.info(
            "EPOCH SUMMARY %d/%d | train_loss=%.4f | train_accuracy=%.4f | "
            "test_loss=%.4f | test_accuracy=%.4f | duration=%.1fs",
            epoch, args.epochs, train_loss, train_accuracy,
            test_loss, test_accuracy, row["seconds"]
        )

        if test_accuracy >= best_accuracy:
            best_accuracy = test_accuracy
            best_true, best_pred = y_true, y_pred
            torch.save({
                "model_state_dict": model.state_dict(),
                "classes": train_data.classes,
                "class_to_idx": train_data.class_to_idx,
                "image_size": 224,
                "mean": [0.5, 0.5, 0.5],
                "std": [0.5, 0.5, 0.5],
                "best_test_accuracy": best_accuracy,
                "dataset_type": dataset_type,
            }, output_dir / "best_model.pth")
            logger.info("Saved best checkpoint: %s", output_dir / "best_model.pth")

    save_confusion_matrix(best_true, best_pred, train_data.classes, output_dir)
    logger.info("Training complete. Best test accuracy: %.4f", best_accuracy)
    logger.info("Charts and metrics exported to: %s", output_dir.resolve())
    logger.info("Open accuracy_curve.png, loss_curve.png, confusion_matrix.png and history.csv.")

if __name__ == "__main__":
    main()
