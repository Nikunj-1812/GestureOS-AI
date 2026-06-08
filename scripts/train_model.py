"""
GestureOS AI — Model Training Script
Trains the GestureClassifier on collected landmark CSV data.

FIX BUG-010: Initialise `ckpt` to None before the training loop.
After the loop, guard the ONNX export block: if no checkpoint was
ever saved (all epochs had val_acc == 0 and dataset may be empty),
emit a clear error instead of crashing with UnboundLocalError.

Usage:
    python scripts/train_model.py --data data/processed/landmarks_dataset.csv
"""

import argparse
import sys
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
from loguru import logger

from data.dataset_loader import LandmarkDataset
from models.gesture_classifier import GestureClassifier


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the gesture classifier.")
    parser.add_argument("--data", default="data/processed/landmarks_dataset.csv")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--output_dir", default="models/weights")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Training on device: {device}")

    dataset = LandmarkDataset(args.data)
    num_classes = len(dataset.classes)
    logger.info(f"Classes ({num_classes}): {dataset.classes}")

    val_size = max(1, int(len(dataset) * 0.15))
    train_size = len(dataset) - val_size
    train_ds, val_ds = random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size)

    model = GestureClassifier(num_classes=num_classes).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    criterion = nn.CrossEntropyLoss()
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    # FIX BUG-010: Initialise ckpt before the loop so it is always bound.
    # If no epoch improves the baseline, ckpt remains None and we abort
    # the ONNX export with a descriptive error rather than a NameError.
    best_val_acc = 0.0
    ckpt: Path | None = None
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, args.epochs + 1):
        model.train()
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            loss = criterion(model(x), y)
            loss.backward()
            optimizer.step()
        scheduler.step()

        # Validation
        model.eval()
        correct = total = 0
        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                preds = model(x).argmax(dim=1)
                correct += (preds == y).sum().item()
                total += len(y)

        val_acc = correct / total if total > 0 else 0.0
        logger.info(f"Epoch {epoch}/{args.epochs}  val_acc={val_acc:.3f}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            ckpt = out / "gesture_classifier_best.pt"
            torch.save(model.state_dict(), ckpt)
            logger.info(f"New best model saved → {ckpt}")

    logger.info(f"Training complete. Best val_acc={best_val_acc:.3f}")

    # Guard: if ckpt is still None, no improvement was ever recorded.
    if ckpt is None:
        logger.error(
            "No checkpoint was saved during training "
            "(val_acc never exceeded 0.0). "
            "Check your dataset or reduce --epochs."
        )
        sys.exit(1)

    # Export best model to ONNX
    best_model = GestureClassifier.from_checkpoint(str(ckpt), num_classes)
    onnx_path = str(out / "gesture_classifier_v1.onnx")
    best_model.export_onnx(onnx_path)
    LandmarkDataset.save_label_map(dataset.label_map, onnx_path.replace(".onnx", ".txt"))
    logger.info(f"ONNX model exported to {onnx_path}")


if __name__ == "__main__":
    main()
