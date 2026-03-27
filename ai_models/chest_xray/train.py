import argparse
import os
import time
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, WeightedRandomSampler
from torchvision import datasets, transforms
from model import MSAHCNN


def get_transforms():
    train_tf = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(),
        transforms.ColorJitter(0.2, 0.2, 0.1),
        transforms.RandomRotation(15),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406],
                             [0.229, 0.224, 0.225]),
    ])

    val_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406],
                             [0.229, 0.224, 0.225]),
    ])

    return train_tf, val_tf


def make_weighted_sampler(dataset):
    class_counts = torch.zeros(len(dataset.classes))
    for _, label in dataset.samples:
        class_counts[label] += 1

    weights = 1.0 / class_counts
    sample_weights = [weights[label] for _, label in dataset.samples]

    return WeightedRandomSampler(sample_weights, len(sample_weights))


def train_one_epoch(model, loader, criterion, optimizer, device):
    model.train()
    total_loss, correct, total = 0.0, 0, 0

    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)

        optimizer.zero_grad()
        logits = model(images)
        loss = criterion(logits, labels)

        loss.backward()
        optimizer.step()

        total_loss += loss.item() * images.size(0)
        correct += (logits.argmax(1) == labels).sum().item()
        total += images.size(0)

    return total_loss / total, correct / total


@torch.no_grad()
def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss, correct, total = 0.0, 0, 0

    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)

        logits = model(images)
        loss = criterion(logits, labels)

        total_loss += loss.item() * images.size(0)
        correct += (logits.argmax(1) == labels).sum().item()
        total += images.size(0)

    return total_loss / total, correct / total


def main(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    train_tf, val_tf = get_transforms()

    train_ds = datasets.ImageFolder(
        os.path.join(args.data_dir, "train"), train_tf)
    val_ds = datasets.ImageFolder(os.path.join(args.data_dir, "val"),   val_tf)

    print(f"Classes: {train_ds.classes}")
    print(f"Train: {len(train_ds)} | Val: {len(val_ds)}")
    print("Class mapping:", train_ds.class_to_idx)

    sampler = make_weighted_sampler(train_ds)

    train_dl = DataLoader(
        train_ds,
        batch_size=args.batch_size,
        sampler=sampler,
        num_workers=2,
        pin_memory=True,
        drop_last=True   # ✅ ADD THIS
    )

    val_dl = DataLoader(
        val_ds,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=2,
        pin_memory=True,
        drop_last=True   # ✅ ADD THIS
    )

    model = MSAHCNN(num_classes=len(train_ds.classes),
                    freeze_layers=args.freeze_layers).to(device)

    print(f"Params: {sum(p.numel() for p in model.parameters()):,}")

    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)

    backbone_params = list(model.branch1.parameters())
    new_params = (
        list(model.branch2.parameters()) +
        list(model.fusion.parameters()) +
        list(model.classifier.parameters())
    )

    optimizer = optim.AdamW([
        {"params": backbone_params, "lr": args.lr * 0.1},
        {"params": new_params, "lr": args.lr},
    ], weight_decay=1e-4)

    scheduler = optim.lr_scheduler.OneCycleLR(
        optimizer,
        max_lr=args.lr,
        steps_per_epoch=len(train_dl),
        epochs=args.epochs
    )

    os.makedirs(args.output_dir, exist_ok=True)
    best_val_acc = 0.0

    for epoch in range(args.epochs):
        t0 = time.time()

        tr_loss, tr_acc = train_one_epoch(
            model, train_dl, criterion, optimizer, device)
        va_loss, va_acc = evaluate(model, val_dl, criterion, device)

        scheduler.step()

        print(
            f"Epoch {epoch+1}/{args.epochs} | "
            f"train_loss={tr_loss:.4f} train_acc={tr_acc:.3f} | "
            f"val_loss={va_loss:.4f} val_acc={va_acc:.3f} | "
            f"time={time.time()-t0:.1f}s"
        )

        if va_acc > best_val_acc:
            best_val_acc = va_acc
            torch.save(model.state_dict(),
                       os.path.join(args.output_dir, "best_model.pt"))

    torch.save(model.state_dict(),
               os.path.join(args.output_dir, "final_model.pt"))

    print(f"\nTraining complete | best_val_acc={best_val_acc:.3f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--data_dir", required=True)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--freeze_layers", type=int, default=4)
    parser.add_argument("--output_dir", default="./checkpoints")

    args = parser.parse_args()
    main(args)

# load checkpoint if exists
checkpoint_path = os.path.join(args.output_dir, "best_model.pt")

if os.path.exists(checkpoint_path):
    print("Loading previous checkpoint...")
    model.load_state_dict(torch.load(checkpoint_path))