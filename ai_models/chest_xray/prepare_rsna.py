import os
import shutil
import pandas as pd
from sklearn.model_selection import train_test_split
from tqdm import tqdm

# ================================
# PATHS (MODIFY IF NEEDED)
# ================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RAW_IMAGES = os.path.join(BASE_DIR, "datasets", "rsna", "stage_2_train_images")
CSV_PATH   = os.path.join(BASE_DIR, "datasets", "rsna", "stage_2_train_labels.csv")

OUTPUT_DIR = os.path.join(BASE_DIR, "datasets", "processed_rsna")

# ================================
# STEP 1: LOAD CSV
# ================================
df = pd.read_csv(CSV_PATH)

print("Total rows:", len(df))

# ================================
# STEP 2: CREATE IMAGE-LEVEL LABEL
# ================================
# If any row has Target=1 → pneumonia

image_labels = df.groupby("patientId")["Target"].max().reset_index()

print("Total unique images:", len(image_labels))

# ================================
# STEP 3: BALANCE DATA (OPTIONAL BUT IMPORTANT)
# ================================
pneumonia = image_labels[image_labels["Target"] == 1]
normal    = image_labels[image_labels["Target"] == 0]

print("Before balance:")
print("Pneumonia:", len(pneumonia))
print("Normal   :", len(normal))

# Balance dataset (same count)
min_count = min(len(pneumonia), len(normal))

pneumonia = pneumonia.sample(min_count, random_state=42)
normal    = normal.sample(min_count, random_state=42)

balanced_df = pd.concat([pneumonia, normal]).sample(frac=1).reset_index(drop=True)

print("After balance:", len(balanced_df))

# ================================
# STEP 4: TRAIN/VAL SPLIT
# ================================
train_df, val_df = train_test_split(
    balanced_df,
    test_size=0.15,
    stratify=balanced_df["Target"],
    random_state=42
)

print("Train:", len(train_df))
print("Val  :", len(val_df))

# ================================
# STEP 5: CREATE FOLDERS
# ================================
def create_dirs():
    for split in ["train", "val"]:
        for cls in ["NORMAL", "PNEUMONIA"]:
            os.makedirs(os.path.join(OUTPUT_DIR, split, cls), exist_ok=True)

create_dirs()

# ================================
# STEP 6: COPY IMAGES
# ================================
def copy_images(df, split):
    for _, row in tqdm(df.iterrows(), total=len(df)):
        img_id = row["patientId"]
        label  = "PNEUMONIA" if row["Target"] == 1 else "NORMAL"

        src = os.path.join(RAW_IMAGES, img_id + ".dcm")
        dst = os.path.join(OUTPUT_DIR, split, label, img_id + ".dcm")

        if os.path.exists(src):
            shutil.copy(src, dst)

copy_images(train_df, "train")
copy_images(val_df, "val")

print("\n✅ Dataset preparation COMPLETE!")