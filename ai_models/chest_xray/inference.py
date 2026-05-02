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

# 🔥 Lazy loading
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


# ✅ FIXED: Risk based on pneumonia probability (NOT confidence)
def get_risk(pneumonia_prob):
    if pneumonia_prob < 0.3:
        return "LOW"
    elif pneumonia_prob < 0.7:
        return "MEDIUM"
    else:
        return "HIGH"


def predict(image_path):
    model, gradcam = load_model()

    image = Image.open(image_path).convert("RGB")
    input_tensor = transform(image).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        output = model(input_tensor)
        probs = torch.softmax(output, dim=1)

    pred_class = torch.argmax(probs, dim=1).item()
    confidence = probs[0][pred_class].item()

    # 🔥 KEY FIX
    pneumonia_prob = probs[0][1].item()
    risk = get_risk(pneumonia_prob)

    cam = gradcam.generate(input_tensor, pred_class)
    overlay = overlay_heatmap(image_path, cam)

    label = "PNEUMONIA" if pred_class == 1 else "NORMAL"

    return {
        "prediction": label,
        "confidence": round(confidence, 4),
        "pneumonia_probability": round(pneumonia_prob, 4),
        "risk_level": risk,
        "heatmap": overlay
    }


# 🔥 Standalone test
if __name__ == "__main__":
    img_path = "test_image.jpeg"

    result = predict(img_path)

    cv2.imwrite("result.jpg", result["heatmap"])

    print("Prediction:", result["prediction"])
    print("Confidence:", result["confidence"])
    print("Pneumonia Probability:", result["pneumonia_probability"])
    print("Risk Level:", result["risk_level"])