from torchvision import transforms

IMAGE_SIZE = 224

# Training data transformations
train_transforms = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),  # 🔴 IMPORTANT
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.RandomRotation(10),
    transforms.RandomHorizontalFlip(),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5], std=[0.5])
])

# Validation / Test transformations
test_transforms = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),  # 🔴 IMPORTANT
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5], std=[0.5])
])
