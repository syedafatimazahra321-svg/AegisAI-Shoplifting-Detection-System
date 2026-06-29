import os
import numpy as np
import cv2
from tqdm import tqdm
from dual_stream_extractor import DualStreamExtractor

WINDOW_SIZE = 16
STRIDE = 8  # overlap between windows
DATA_ROOT = r"C:\JOB\AegisAI\data"
OUT_DIR = r"C:\JOB\AegisAI\data\processed"

# Ensure output directory exists
os.makedirs(OUT_DIR, exist_ok=True)

extractor = DualStreamExtractor()

def extract_windows(video_path, label):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Cannot open: {video_path}")
        return [], []
    
    frames_buffer = []
    all_features = []
    all_labels = []
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames_buffer.append(frame)
        
        # When we have WINDOW_SIZE frames, extract features
        if len(frames_buffer) == WINDOW_SIZE:
            feats = extractor.extract(frames_buffer)  # [16, 1152]
            all_features.append(feats.numpy())
            all_labels.append(label)
            # Slide by STRIDE
            frames_buffer = frames_buffer[STRIDE:]
            
    cap.release()
    return all_features, all_labels

all_X, all_y = [], []

# Match your specific folder names exactly: (label, folder_name)
for label, folder in [(1, "Shoplifting_Class"), (0, "Normal_Class")]:
    folder_path = os.path.join(DATA_ROOT, folder)
    if not os.path.exists(folder_path):
        print(f"Warning: Directory missing, skipping: {folder_path}")
        continue
        
    video_files = [f for f in os.listdir(folder_path) 
                   if f.endswith(('.mp4', '.avi', '.mkv'))]
    print(f"\nProcessing {len(video_files)} videos from {folder}...")
    
    for vf in tqdm(video_files):
        vpath = os.path.join(folder_path, vf)
        feats, labs = extract_windows(vpath, label)
        all_X.extend(feats)
        all_y.extend(labs)

if len(all_X) == 0:
    print("\nError: No windows extracted. Check your video formats or file directory.")
else:
    X = np.array(all_X, dtype=np.float32)  # [N, 16, 1152]
    y = np.array(all_y, dtype=np.float32)  # [N]
    
    print(f"\nTotal windows extracted: {len(X)}")
    print(f"Shoplifting windows: {y.sum():.0f}")
    print(f"Normal windows: {len(y) - y.sum():.0f}")
    
    np.save(os.path.join(OUT_DIR, "X.npy"), X)
    np.save(os.path.join(OUT_DIR, "y.npy"), y)
    print(f"Saved successfully to {OUT_DIR}/X.npy and y.npy")