import argparse
import json
import os
import time
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.metrics import f1_score, precision_score, recall_score

from dataset import get_dataloaders
from model import MSAHCNN


def train_one_epoch(model, loader, criterion, optimizer, scheduler, device):
    model.train()
    total_loss, correct, total = 0.0, 0, 0

    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)

        optimizer.zero_grad()
        logits = model(images)
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()
        scheduler.step()

        total_loss += loss.item() * images.size(0)
        correct += (logits.argmax(1) == labels).sum().item()
        total += images.size(0)

    return total_loss / total, correct / total


@torch.no_grad()
def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss, correct, total = 0.0, 0, 0
    all_labels = []
    all_preds = []

    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)

        logits = model(images)
        loss = criterion(logits, labels)
        preds = logits.argmax(1)

        total_loss += loss.item() * images.size(0)
        correct += (preds == labels).sum().item()
        total += images.size(0)

        all_labels.extend(labels.cpu().numpy().tolist())
        all_preds.extend(preds.cpu().numpy().tolist())

    precision = precision_score(all_labels, all_preds, average="weighted", zero_division=0)
    recall = recall_score(all_labels, all_preds, average="weighted", zero_division=0)
    f1 = f1_score(all_labels, all_preds, average="weighted", zero_division=0)

    return {
        "loss": total_loss / total,
        "accuracy": correct / total,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def save_json(data, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def main(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    train_loader, val_loader = get_dataloaders(
        data_dir=args.data_dir,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
    )

    model = MSAHCNN(
        num_classes=2,
        freeze_layers=args.freeze_layers,
    ).to(device)

    print(f"Params: {sum(p.numel() for p in model.parameters()):,}")

    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.OneCycleLR(
        optimizer,
        max_lr=args.lr,
        steps_per_epoch=len(train_loader),
        epochs=args.epochs,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    history = {
        "epoch": [],
        "train_loss": [],
        "train_acc": [],
        "val_loss": [],
        "val_acc": [],
        "val_precision": [],
        "val_recall": [],
        "val_f1": [],
        "lr": [],
    }

    best_val_acc = 0.0
    best_epoch = -1

    for epoch in range(args.epochs):
        t0 = time.time()

        tr_loss, tr_acc = train_one_epoch(
            model, train_loader, criterion, optimizer, scheduler, device
        )
        val_metrics = evaluate(model, val_loader, criterion, device)
        current_lr = optimizer.param_groups[0]["lr"]

        history["epoch"].append(epoch + 1)
        history["train_loss"].append(round(tr_loss, 6))
        history["train_acc"].append(round(tr_acc, 6))
        history["val_loss"].append(round(val_metrics["loss"], 6))
        history["val_acc"].append(round(val_metrics["accuracy"], 6))
        history["val_precision"].append(round(val_metrics["precision"], 6))
        history["val_recall"].append(round(val_metrics["recall"], 6))
        history["val_f1"].append(round(val_metrics["f1"], 6))
        history["lr"].append(round(current_lr, 10))

        print(
            f"Epoch {epoch+1}/{args.epochs} | "
            f"train_loss={tr_loss:.4f} train_acc={tr_acc:.4f} | "
            f"val_loss={val_metrics['loss']:.4f} val_acc={val_metrics['accuracy']:.4f} "
            f"val_f1={val_metrics['f1']:.4f} | "
            f"lr={current_lr:.8f} | time={time.time() - t0:.1f}s"
        )

        save_json(history, output_dir / "training_history.json")

        if val_metrics["accuracy"] > best_val_acc:
            best_val_acc = val_metrics["accuracy"]
            best_epoch = epoch + 1
            torch.save(model.state_dict(), output_dir / "best_model.pt")
            save_json(
                {
                    "best_epoch": best_epoch,
                    "best_val_acc": round(best_val_acc, 6),
                    "best_val_loss": round(val_metrics["loss"], 6),
                    "best_val_precision": round(val_metrics["precision"], 6),
                    "best_val_recall": round(val_metrics["recall"], 6),
                    "best_val_f1": round(val_metrics["f1"], 6),
                },
                output_dir / "best_metrics.json",
            )

    torch.save(model.state_dict(), output_dir / "final_model.pt")
    save_json(
        {
            "best_epoch": best_epoch,
            "best_val_acc": round(best_val_acc, 6),
            "final_epoch": args.epochs,
            "final_train_loss": history["train_loss"][-1],
            "final_train_acc": history["train_acc"][-1],
            "final_val_loss": history["val_loss"][-1],
            "final_val_acc": history["val_acc"][-1],
            "final_val_precision": history["val_precision"][-1],
            "final_val_recall": history["val_recall"][-1],
            "final_val_f1": history["val_f1"][-1],
        },
        output_dir / "final_metrics.json",
    )

    print(f"\nTraining complete | best_epoch={best_epoch} | best_val_acc={best_val_acc:.4f}")
    print(f"Artifacts saved in: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", required=True)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--freeze_layers", type=int, default=4)
    parser.add_argument("--num_workers", type=int, default=2)
    parser.add_argument("--output_dir", default="/kaggle/working/checkpoints")

    main(parser.parse_args())
