import torch

from msa_hcnn_model import MSA_HCNN

# Create model
model = MSA_HCNN(num_classes=2)

# Set to eval mode
model.eval()

# Create dummy input (batch_size=1, grayscale image 224x224)
dummy_input = torch.randn(1, 1, 224, 224)

# Forward pass
with torch.no_grad():
    output = model(dummy_input)

print("Model output shape:", output.shape)
print("Output:", output)