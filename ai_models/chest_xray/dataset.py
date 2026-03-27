import os
from torchvision import datasets
from torch.utils.data import DataLoader
from transforms import train_transforms, test_transforms


def get_dataloaders(data_dir, batch_size=16, num_workers=2):
    train_dir = os.path.join(data_dir, "train")
    val_dir   = os.path.join(data_dir, "val")

    if not os.path.exists(train_dir):
        raise FileNotFoundError(f"Train folder not found: {train_dir}")
    if not os.path.exists(val_dir):
        raise FileNotFoundError(f"Val folder not found: {val_dir}")

    train_dataset = datasets.ImageFolder(
        root=train_dir,
        transform=train_transforms
    )

    val_dataset = datasets.ImageFolder(
        root=val_dir,
        transform=test_transforms
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True,
        drop_last=True
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True,
        drop_last=True
    )

    return train_loader, val_loader