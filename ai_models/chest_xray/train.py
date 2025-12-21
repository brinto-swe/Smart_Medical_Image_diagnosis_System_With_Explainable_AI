import torch
import torch.nn as nn
import torch.optim as optim

from model import ChestXrayCNN
from dataset import get_dataloaders

# Device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# Hyperparameters (temporary)
BATCH_SIZE = 16
LEARNING_RATE = 0.001
EPOCHS = 1  # ONLY 1 for sanity check

# Load data
train_loader, val_loader, test_loader = get_dataloaders(
    batch_size=BATCH_SIZE
)

# Model
model = ChestXrayCNN(num_classes=2).to(device)

# Loss & Optimizer
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

print("Starting training...")

for epoch in range(EPOCHS):
    model.train()
    running_loss = 0.0

    for images, labels in train_loader:
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item()

    avg_loss = running_loss / len(train_loader)
    print(f"Epoch [{epoch+1}/{EPOCHS}], Loss: {avg_loss:.4f}")

print("Training sanity check completed.")
