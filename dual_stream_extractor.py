import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
import cv2
import numpy as np

# Transforms
transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225])
])

flow_transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.5, 0.5, 0.5], [0.5, 0.5, 0.5])
])

# MobileNetV3 backbone (shared architecture, separate weights)
def make_mobilenet():
    m = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
    # Remove final classifier, keep feature extractor
    m.classifier = nn.Identity()
    m.eval()
    for p in m.parameters():
        p.requires_grad = False
    return m

class DualStreamExtractor(nn.Module):
    def __init__(self):
        super().__init__()
        self.rgb_net = make_mobilenet()
        self.flow_net = make_mobilenet()

    def extract_rgb(self, frames):
        """frames: list of BGR numpy arrays"""
        tensors = torch.stack([transform(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)) 
                               for f in frames])  # [N, 3, 224, 224]
        with torch.no_grad():
            feats = self.rgb_net(tensors)  # [N, 576]
        return feats  # one feature vector per frame

    def extract_flow(self, frames):
        """Compute optical flow between consecutive frames, extract features"""
        flow_frames = []
        gray_frames = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames]
        for i in range(len(gray_frames)):
            if i == 0:
                # First frame: zero flow
                flow_rgb = np.zeros((frames[0].shape[0], frames[0].shape[1], 3), 
                                    dtype=np.uint8)
            else:
                flow = cv2.calcOpticalFlowFarneback(
                    gray_frames[i-1], gray_frames[i], None,
                    pyr_scale=0.5, levels=3, winsize=15,
                    iterations=3, poly_n=5, poly_sigma=1.2, flags=0
                )
                # Convert flow to RGB for visualization and feature extraction
                mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
                hsv = np.zeros_like(frames[i])
                hsv[..., 1] = 255
                hsv[..., 0] = ang * 180 / np.pi / 2
                hsv[..., 2] = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX)
                flow_rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
            flow_frames.append(flow_rgb)
        tensors = torch.stack([flow_transform(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)) 
                               for f in flow_frames])
        with torch.no_grad():
            feats = self.flow_net(tensors)  # [N, 576]
        return feats

    def extract(self, frames):
        """Returns [N, 1152] tensor: RGB(576) + Flow(576) per frame"""
        rgb_feats  = self.extract_rgb(frames)   # [N, 576]
        flow_feats = self.extract_flow(frames)  # [N, 576]
        return torch.cat([rgb_feats, flow_feats], dim=1)  # [N, 1152]

# Quick test
if __name__ == "__main__":
    extractor = DualStreamExtractor()
    dummy_frames = [np.random.randint(0, 255, (480, 640, 3), 
                    dtype=np.uint8) for _ in range(16)]
    feats = extractor.extract(dummy_frames)
    print(f"Feature shape: {feats.shape}")  # Should be [16, 1152]
    print("Extractor OK!")