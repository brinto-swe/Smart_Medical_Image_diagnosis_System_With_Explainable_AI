# ai_models/chest_xray/inference.py

import torch
from PIL import Image
from torchvision import transforms
import cv2
import os

from ai_models.chest_xray.model import MSAHCNN
from ai_models.chest_xray.explainability import GradCAM, overlay_heatmap

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "checkpoints", "best_model.pt")

# 🔥 Lazy model loading (IMPORTANT)
model = None
gradcam = None


def load_model():
    global model, gradcam

    if model is None:
        model = MSAHCNN(num_classes=2)
        model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
        model.to(DEVICE)
        model.eval()

        target_layer = model.branch1.features[-1]
        gradcam = GradCAM(model, target_layer)

    return model, gradcam


# 🔥 Transform
transform = transforms.Compose([
    transforms.Grayscale(num_output_channels=3),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225])
])


def get_risk(conf):
    if conf < 0.6:
        return "LOW"
    elif conf < 0.8:
        return "MEDIUM"
    else:
        return "HIGH"


def predict(image_path):
    model, gradcam = load_model()

    image = Image.open(image_path).convert("RGB")
    input_tensor = transform(image).unsqueeze(0).to(DEVICE)

    output = model(input_tensor)
    probs = torch.softmax(output, dim=1)

    pred_class = torch.argmax(probs, dim=1).item()
    confidence = probs[0][pred_class].item()

    cam = gradcam.generate(input_tensor, pred_class)
    overlay = overlay_heatmap(image_path, cam)

    label = "PNEUMONIA" if pred_class == 1 else "NORMAL"
    risk = get_risk(confidence)

    return {
        "prediction": label,
        "confidence": round(confidence, 4),
        "risk_level": risk,
        "heatmap": overlay
    }


# 🔥 Standalone testing only
if __name__ == "__main__":
    img_path = "test_image.jpeg"

    result = predict(img_path)

    cv2.imwrite("result.jpg", result["heatmap"])

    print("Prediction:", result["prediction"])
    print("Confidence:", result["confidence"])
    print("Risk Level:", result["risk_level"])