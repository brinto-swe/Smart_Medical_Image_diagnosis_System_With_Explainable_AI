import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models


class ConvBlock(nn.Module):
    def __init__(self, in_ch, out_ch, kernel=3, stride=1, padding=1):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel, stride, padding, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.block(x)


class ResidualBlock(nn.Module):
    def __init__(self, in_ch, out_ch, stride=1):
        super().__init__()
        self.conv1 = nn.Conv2d(in_ch, out_ch, 3, stride, 1, bias=False)
        self.bn1   = nn.BatchNorm2d(out_ch)
        self.conv2 = nn.Conv2d(out_ch, out_ch, 3, 1, 1, bias=False)
        self.bn2   = nn.BatchNorm2d(out_ch)
        self.relu  = nn.ReLU(inplace=True)

        self.shortcut = nn.Identity()
        if in_ch != out_ch or stride != 1:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_ch, out_ch, 1, stride, bias=False),
                nn.BatchNorm2d(out_ch),
            )

    def forward(self, x):
        out = self.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        return self.relu(out + self.shortcut(x))


class MultiScaleFeatureBlock(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        branch_ch = out_ch // 4

        self.branch1 = nn.Sequential(
            nn.Conv2d(in_ch, branch_ch, 1, bias=False),
            nn.BatchNorm2d(branch_ch), nn.ReLU(inplace=True),
        )
        self.branch2 = nn.Sequential(
            nn.Conv2d(in_ch, branch_ch, 3, padding=1, dilation=1, bias=False),
            nn.BatchNorm2d(branch_ch), nn.ReLU(inplace=True),
        )
        self.branch3 = nn.Sequential(
            nn.Conv2d(in_ch, branch_ch, 3, padding=2, dilation=2, bias=False),
            nn.BatchNorm2d(branch_ch), nn.ReLU(inplace=True),
        )
        self.branch4 = nn.Sequential(
            nn.Conv2d(in_ch, branch_ch, 3, padding=4, dilation=4, bias=False),
            nn.BatchNorm2d(branch_ch), nn.ReLU(inplace=True),
        )

        self.fuse = nn.Sequential(
            nn.Conv2d(branch_ch * 4, out_ch, 1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        out = torch.cat([
            self.branch1(x),
            self.branch2(x),
            self.branch3(x),
            self.branch4(x)
        ], dim=1)
        return self.fuse(out)


class ChannelAttention(nn.Module):
    def __init__(self, in_ch, reduction=16):
        super().__init__()
        mid = max(in_ch // reduction, 8)

        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.max_pool = nn.AdaptiveMaxPool2d(1)

        self.fc = nn.Sequential(
            nn.Flatten(),
            nn.Linear(in_ch, mid, bias=False),
            nn.ReLU(inplace=True),
            nn.Linear(mid, in_ch, bias=False),
        )

        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        avg = self.fc(self.avg_pool(x))
        mx  = self.fc(self.max_pool(x))
        scale = self.sigmoid(avg + mx).unsqueeze(-1).unsqueeze(-1)
        return x * scale


class SpatialAttention(nn.Module):
    def __init__(self, kernel=7):
        super().__init__()
        self.conv = nn.Conv2d(2, 1, kernel, padding=kernel // 2, bias=False)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        avg = x.mean(dim=1, keepdim=True)
        mx, _ = x.max(dim=1, keepdim=True)
        attn = self.sigmoid(self.conv(torch.cat([avg, mx], dim=1)))
        return x * attn


class AttentionModule(nn.Module):
    def __init__(self, in_ch):
        super().__init__()
        self.channel = ChannelAttention(in_ch)
        self.spatial = SpatialAttention()

    def forward(self, x):
        return self.spatial(self.channel(x))


class Branch1_ResNet(nn.Module):
    def __init__(self, freeze_layers=6):
        super().__init__()
        base = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)

        self.features = nn.Sequential(*list(base.children())[:-2])
        self.pool = nn.AdaptiveAvgPool2d(1)

        for layer in list(self.features.children())[:freeze_layers]:
            for p in layer.parameters():
                p.requires_grad = False

        self.out_dim = 2048

    def forward(self, x):
        x = self.features(x)
        x = self.pool(x)
        return x.flatten(1)


class Branch2_CustomCNN(nn.Module):
    def __init__(self, in_channels=3):
        super().__init__()
        self.conv = ConvBlock(in_channels, 64, kernel=7, stride=2, padding=3)
        self.pool = nn.MaxPool2d(3, stride=2, padding=1)

        self.res1 = ResidualBlock(64, 128, stride=2)
        self.ms   = MultiScaleFeatureBlock(128, 256)
        self.attn = AttentionModule(256)
        self.res2 = ResidualBlock(256, 512, stride=2)

        self.pool_out = nn.AdaptiveAvgPool2d(1)
        self.out_dim = 512

    def forward(self, x):
        x = self.pool(self.conv(x))
        x = self.res1(x)
        x = self.ms(x)
        x = self.attn(x)
        x = self.res2(x)
        x = self.pool_out(x)
        return x.flatten(1)


class FusionLayer(nn.Module):
    def __init__(self, dim1, dim2, out_dim=512):
        super().__init__()
        self.fusion = nn.Sequential(
            nn.Linear(dim1 + dim2, out_dim),
            nn.BatchNorm1d(out_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(0.4),
        )
        self.out_dim = out_dim

    def forward(self, f1, f2):
        return self.fusion(torch.cat([f1, f2], dim=1))


class Classifier(nn.Module):
    def __init__(self, in_dim, num_classes):
        super().__init__()
        self.head = nn.Sequential(
            nn.Linear(in_dim, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes),
        )

    def forward(self, x):
        return self.head(x)


class MSAHCNN(nn.Module):
    def __init__(self, num_classes=2, in_channels=3, freeze_layers=6):
        super().__init__()
        self.branch1 = Branch1_ResNet(freeze_layers)
        self.branch2 = Branch2_CustomCNN(in_channels)

        self.fusion = FusionLayer(
            self.branch1.out_dim,
            self.branch2.out_dim
        )

        self.classifier = Classifier(self.fusion.out_dim, num_classes)

    def forward(self, x):
        f1 = self.branch1(x)
        f2 = self.branch2(x)
        fused = self.fusion(f1, f2)
        return self.classifier(fused)

    @torch.no_grad()
    def predict(self, x):
        self.eval()
        return F.softmax(self.forward(x), dim=1)