import os
import pydicom
import numpy as np
import cv2
from tqdm import tqdm

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "datasets", "processed_rsna")

def convert_folder(folder):
    for root, _, files in os.walk(folder):
        for file in tqdm(files):
            if file.endswith(".dcm"):
                dcm_path = os.path.join(root, file)

                ds = pydicom.dcmread(dcm_path)
                img = ds.pixel_array.astype(float)

                # Normalize
                img = (img - np.min(img)) / (np.max(img) - np.min(img))
                img = (img * 255).astype(np.uint8)

                png_path = dcm_path.replace(".dcm", ".png")

                cv2.imwrite(png_path, img)

                # Remove original .dcm
                os.remove(dcm_path)

print("Converting TRAIN...")
convert_folder(os.path.join(DATA_DIR, "train"))

print("Converting VAL...")
convert_folder(os.path.join(DATA_DIR, "val"))

print("\n✅ Conversion COMPLETE!")