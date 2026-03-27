import os
from torchvision import datasets
from torch.utils.data import DataLoader
from transforms import train_transforms, test_transforms

# Get absolute path to dataset directory
BASE_DIR = os.path.dirname(__file__)
DATASET_DIR = os.path.abspath(
    os.path.join(BASE_DIR, "../../datasets/chest_xray")
)

def get_dataloaders(batch_size=16):
    train_dataset = datasets.ImageFolder(
        root=os.path.join(DATASET_DIR, "train"),
        transform=train_transforms
    )

    val_dataset = datasets.ImageFolder(
        root=os.path.join(DATASET_DIR, "val"),
        transform=test_transforms
    )

    test_dataset = datasets.ImageFolder(
        root=os.path.join(DATASET_DIR, "test"),
        transform=test_transforms
    )

    train_loader = DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True
    )

    val_loader = DataLoader(
        val_dataset, batch_size=batch_size, shuffle=False
    )

    test_loader = DataLoader(
        test_dataset, batch_size=batch_size, shuffle=False
    )

    return train_loader, val_loader, test_loader
