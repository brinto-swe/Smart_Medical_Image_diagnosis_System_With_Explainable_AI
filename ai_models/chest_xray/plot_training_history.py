import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt


def load_history(history_path):
    with open(history_path, "r", encoding="utf-8") as f:
        return json.load(f)


def plot_curve(x, y1, y2, title, ylabel, output_path, label1, label2):
    plt.figure(figsize=(10, 6))
    plt.plot(x, y1, linewidth=3, label=label1)
    plt.plot(x, y2, linewidth=3, label=label2)
    plt.title(title, fontsize=18, weight="bold")
    plt.xlabel("Epoch", fontsize=14)
    plt.ylabel(ylabel, fontsize=14)
    plt.legend()
    plt.grid(True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def plot_single_curve(x, y, title, ylabel, output_path, label):
    plt.figure(figsize=(10, 6))
    plt.plot(x, y, linewidth=3, label=label)
    plt.title(title, fontsize=18, weight="bold")
    plt.xlabel("Epoch", fontsize=14)
    plt.ylabel(ylabel, fontsize=14)
    plt.legend()
    plt.grid(True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()


def main(args):
    history_path = Path(args.history_path)
    output_dir = Path(args.output_dir) if args.output_dir else history_path.parent / "report_graphs"
    output_dir.mkdir(parents=True, exist_ok=True)

    history = load_history(history_path)
    epochs = history["epoch"]

    plot_curve(
        epochs,
        history["train_acc"],
        history["val_acc"],
        "Training vs Validation Accuracy",
        "Accuracy",
        output_dir / "accuracy_curve.png",
        "Training Accuracy",
        "Validation Accuracy",
    )

    plot_curve(
        epochs,
        history["train_loss"],
        history["val_loss"],
        "Training vs Validation Loss",
        "Loss",
        output_dir / "loss_curve.png",
        "Training Loss",
        "Validation Loss",
    )

    plot_single_curve(
        epochs,
        history["val_f1"],
        "Validation F1 Score Across Epochs",
        "F1 Score",
        output_dir / "f1_score_curve.png",
        "Validation F1 Score",
    )

    plot_single_curve(
        epochs,
        history["val_precision"],
        "Validation Precision Across Epochs",
        "Precision",
        output_dir / "precision_curve.png",
        "Validation Precision",
    )

    plot_single_curve(
        epochs,
        history["val_recall"],
        "Validation Recall Across Epochs",
        "Recall",
        output_dir / "recall_curve.png",
        "Validation Recall",
    )

    print("Training history graphs generated successfully.")
    print(f"Saved in: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--history_path", required=True)
    parser.add_argument("--output_dir", default=None)
    main(parser.parse_args())
