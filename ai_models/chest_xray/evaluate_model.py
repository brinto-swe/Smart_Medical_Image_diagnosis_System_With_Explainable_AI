import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import torch
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
)
from torch.utils.data import DataLoader
from torchvision import datasets, transforms

from model import MSAHCNN


DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def build_val_loader(data_dir, batch_size, num_workers):
    transform = transforms.Compose([
        transforms.Grayscale(num_output_channels=3),
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            [0.485, 0.456, 0.406],
            [0.229, 0.224, 0.225],
        ),
    ])

    val_dataset = datasets.ImageFolder(
        root=str(Path(data_dir) / "val"),
        transform=transform,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
    )

    return val_dataset, val_loader


def save_json(data, output_path):
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def main(args):
    print(f"Device: {DEVICE}")

    checkpoint_path = Path(args.checkpoint)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    model = MSAHCNN(num_classes=2)
    model.load_state_dict(torch.load(checkpoint_path, map_location=DEVICE))
    model.to(DEVICE)
    model.eval()

    print(f"Model loaded from: {checkpoint_path}")

    val_dataset, val_loader = build_val_loader(args.data_dir, args.batch_size, args.num_workers)
    print(f"Validation samples: {len(val_dataset)}")

    all_labels = []
    all_preds = []
    all_probs = []

    with torch.no_grad():
        for images, labels in val_loader:
            images = images.to(DEVICE)
            outputs = model(images)
            probs = torch.softmax(outputs, dim=1)
            preds = torch.argmax(probs, dim=1)

            all_labels.extend(labels.numpy().tolist())
            all_preds.extend(preds.cpu().numpy().tolist())
            all_probs.extend(probs[:, 1].cpu().numpy().tolist())

    all_labels = np.array(all_labels)
    all_preds = np.array(all_preds)
    all_probs = np.array(all_probs)

    accuracy = accuracy_score(all_labels, all_preds)
    precision = precision_score(all_labels, all_preds, average="weighted", zero_division=0)
    recall = recall_score(all_labels, all_preds, average="weighted", zero_division=0)
    f1 = f1_score(all_labels, all_preds, average="weighted", zero_division=0)

    metrics_summary = {
        "accuracy": round(float(accuracy), 6),
        "precision": round(float(precision), 6),
        "recall": round(float(recall), 6),
        "f1_score": round(float(f1), 6),
        "total_samples": int(len(val_dataset)),
        "class_names": val_dataset.classes,
        "class_support": {
            class_name: int((all_labels == idx).sum())
            for idx, class_name in enumerate(val_dataset.classes)
        },
        "checkpoint": str(checkpoint_path),
    }
    save_json(metrics_summary, output_dir / "metrics_summary.json")

    cm = confusion_matrix(all_labels, all_preds)
    save_json({"confusion_matrix": cm.tolist()}, output_dir / "confusion_matrix.json")

    plt.figure(figsize=(6, 5))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=val_dataset.classes,
        yticklabels=val_dataset.classes,
    )
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title("Confusion Matrix")
    plt.savefig(output_dir / "confusion_matrix.png", dpi=300, bbox_inches="tight")
    plt.close()

    precision_curve, recall_curve, _ = precision_recall_curve(all_labels, all_probs)
    plt.figure(figsize=(7, 5))
    plt.plot(recall_curve, precision_curve, linewidth=2.5)
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision-Recall Curve")
    plt.grid(True)
    plt.savefig(output_dir / "precision_recall_curve.png", dpi=300, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(4, 5))
    plt.bar(["F1 Score"], [f1], color="#2563EB")
    plt.ylim(0, 1)
    plt.title("F1 Score")
    plt.savefig(output_dir / "f1_score.png", dpi=300, bbox_inches="tight")
    plt.close()

    report_text = classification_report(
        all_labels,
        all_preds,
        target_names=val_dataset.classes,
        digits=4,
        zero_division=0,
    )
    with open(output_dir / "classification_report.txt", "w", encoding="utf-8") as f:
        f.write(report_text)

    report_dict = classification_report(
        all_labels,
        all_preds,
        target_names=val_dataset.classes,
        output_dict=True,
        zero_division=0,
    )
    save_json(report_dict, output_dir / "classification_report.json")

    print("\nClassification Report:\n")
    print(report_text)
    print("Evaluation artifacts generated successfully.")
    print(f"Saved in: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--num_workers", type=int, default=2)
    parser.add_argument("--output_dir", default=None)
    args = parser.parse_args()

    if args.output_dir is None:
        checkpoint_dir = Path(args.checkpoint).resolve().parent
        args.output_dir = str(checkpoint_dir.parent / "evaluation_graphs")

    main(args)
