import os
from PIL import Image
import matplotlib.pyplot as plt

DATASET_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../datasets/chest_xray"
)

splits = ["train", "val", "test"]
classes = ["NORMAL", "PNEUMONIA"]

print("Chest X-ray Dataset Overview\n")

for split in splits:
    print(f"--- {split.upper()} ---")
    for cls in classes:
        folder = os.path.join(DATASET_PATH, split, cls)
        count = len(os.listdir(folder))
        print(f"{cls}: {count} images")
    print()

# Show one sample image
sample_image_path = os.path.join(
    DATASET_PATH, "train", "PNEUMONIA", os.listdir(
        os.path.join(DATASET_PATH, "train", "PNEUMONIA")
    )[0]
)

img = Image.open(sample_image_path)

plt.imshow(img, cmap="gray")
plt.title("Sample Chest X-ray (Pneumonia)")
plt.axis("off")
plt.show()
