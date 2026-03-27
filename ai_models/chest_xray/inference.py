import torch
import torch.nn.functional as F
from PIL import Image
import os

from ai_models.chest_xray.model import ChestXrayCNN
from ai_models.chest_xray.transforms import test_transforms

# Device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Model path
MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "chest_xray_model.pt"
)

# Load model
model = ChestXrayCNN(num_classes=2)
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
model.to(device)
model.eval()

CLASS_NAMES = ["NORMAL", "PNEUMONIA"]

def predict_image(image_path):
    image = Image.open(image_path)

    image = test_transforms(image)
    image = image.unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(image)
        probabilities = F.softmax(outputs, dim=1)
        confidence, predicted = torch.max(probabilities, 1)

    predicted_class = CLASS_NAMES[predicted.item()]
    confidence_score = confidence.item()

    # Simple risk logic
    if predicted_class == "PNEUMONIA":
        risk = "High" if confidence_score > 0.8 else "Medium"
    else:
        risk = "Low"

    return {
        "prediction": predicted_class,
        "confidence": round(confidence_score * 100, 2),
        "risk_level": risk
    }


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(__file__)
    sample_image = os.path.abspath(
        os.path.join(BASE_DIR,
        "../../datasets/chest_xray/test/PNEUMONIA",
        os.listdir(
            os.path.join(BASE_DIR,
            "../../datasets/chest_xray/test/PNEUMONIA")
        )[0])
    )

    result = predict_image(sample_image)
    print("Inference Result:\n", result)
