from torchvision import transforms

train_transforms = transforms.Compose([
    transforms.Grayscale(num_output_channels=3),   # 🔥 FIX
    transforms.Resize((256, 256)),
    transforms.RandomCrop(224),
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(),
    transforms.RandomRotation(15),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225]),
])

test_transforms = transforms.Compose([
    transforms.Grayscale(num_output_channels=3),   # 🔥 FIX
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225]),
])