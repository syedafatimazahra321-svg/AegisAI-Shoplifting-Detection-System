import cv2
import torch
import numpy as np
import os
import argparse
import time
from datetime import datetime
from collections import deque

from dual_stream_extractor import DualStreamExtractor
from model import AttentionLSTM
from behaviour_tagger import BehaviourTagger
from zone_manager import ZoneManager
from database import init_db, log_incident

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WINDOW_SIZE       = 16
STRIDE            = 8
SUSPICION_THRESH  = 0.55
CONSEC_WINDOWS    = 2
INCIDENT_COOLDOWN = 60   # frames before logging another incident

# ---------------------------------------------------------------------------
def run_inference(video_source, camera_id="CAM_01", show_preview=True):

    init_db()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[Init] Device: {device}")

    print("[Init] Loading feature extractor...")
    extractor = DualStreamExtractor()

    print("[Init] Loading model...")
    model = AttentionLSTM().to(device)
    model.load_state_dict(torch.load("models/attention_lstm.pth",
                                     map_location=device))
    model.eval()

    print("[Init] Loading behaviour tagger...")
    tagger = BehaviourTagger()

    zone_mgr = ZoneManager()

    try:
        from ultralytics import YOLO
        yolo     = YOLO("yolov8n.pt")
        use_yolo = True
        print("[Init] YOLOv8 loaded.")
    except Exception as e:
        print(f"[Init] YOLOv8 unavailable ({e}), skipping person gate.")
        use_yolo = False

    cap = cv2.VideoCapture(video_source)
    if not cap.isOpened():
        print(f"ERROR: Cannot open source: {video_source}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    W   = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H   = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    zone_mgr.w, zone_mgr.h = W, H
    print(f"[Init] Video: {W}x{H} @ {fps:.1f} fps\n")

    # --- State ---
    frame_buffer     = deque(maxlen=WINDOW_SIZE)
    score_history    = deque(maxlen=5)
    frame_count      = 0
    person_bbox      = None
    smoothed_score   = 0.0
    active_zone      = "General Area"
    high_score_count = 0
    cooldown_counter = 0

    target_ms = max(1, int(1000.0 / fps))

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_count  += 1
        t_frame_start = time.time()

        if cooldown_counter > 0:
            cooldown_counter -= 1

        # ------------------------------------------------------------------
        # Person detection — every 4th frame
        # ------------------------------------------------------------------
        if use_yolo and (frame_count % 4 == 0 or person_bbox is None):
            results = yolo(frame, classes=[0], conf=0.35, verbose=False)
            if len(results[0].boxes) > 0:
                box = results[0].boxes[0].xyxy[0].cpu().numpy()
                person_bbox = (
                    int(box[0]), int(box[1]),
                    int(box[2] - box[0]), int(box[3] - box[1]),
                )

        frame_buffer.append(frame.copy())

        # ------------------------------------------------------------------
        # Buffer filling phase
        # ------------------------------------------------------------------
        if len(frame_buffer) < WINDOW_SIZE:
            if show_preview:
                display = zone_mgr.draw_zones(frame.copy())
                cv2.putText(display,
                            f"Buffering... ({len(frame_buffer)}/{WINDOW_SIZE})",
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 0), 2)
                cv2.imshow(f"AegisAI - {camera_id}", display)
                if cv2.waitKey(target_ms) & 0xFF == ord('q'):
                    break
            continue

        # ------------------------------------------------------------------
        # Between strides — display with last known score
        # ------------------------------------------------------------------
        if frame_count % STRIDE != 0:
            if show_preview:
                _draw_and_show(frame, zone_mgr, person_bbox, smoothed_score,
                               active_zone, W, H, camera_id, SUSPICION_THRESH)
                elapsed_ms = int((time.time() - t_frame_start) * 1000)
                wait_ms    = max(1, target_ms - elapsed_ms)
                if cv2.waitKey(wait_ms) & 0xFF == ord('q'):
                    break
            continue

        # ------------------------------------------------------------------
        # Inference window
        # ------------------------------------------------------------------
        frames_list = list(frame_buffer)

        features = extractor.extract(frames_list)          # [16, 1152]
        x_tensor = features.unsqueeze(0).to(device)       # [1, 16, 1152]

        with torch.no_grad():
            logit, _ = model(x_tensor)
        raw_score = torch.sigmoid(logit).item()

        multiplier, active_zone = zone_mgr.get_zone_multiplier(person_bbox)
        final_score             = min(raw_score * multiplier, 1.0)

        score_history.append(final_score)
        smoothed_score = float(np.mean(score_history))

        print(f"Frame {frame_count:4d} | raw={raw_score:.4f} | "
              f"smoothed={smoothed_score:.4f} → "
              f"{'INCIDENT DETECTED' if smoothed_score > SUSPICION_THRESH else 'normal'} "
              f"({smoothed_score:.2%})")

        # ------------------------------------------------------------------
        # Incident logic
        # ------------------------------------------------------------------
        if smoothed_score > SUSPICION_THRESH:
            high_score_count += 1
        else:
            high_score_count = 0

        if high_score_count >= CONSEC_WINDOWS and cooldown_counter == 0:
            high_score_count = 0
            cooldown_counter = INCIDENT_COOLDOWN

            print(f"\n{'='*60}")
            print(f"!!! INCIDENT DETECTED (Score: {smoothed_score:.2%}) !!!")
            print(f"{'='*60}\n")

            # --- Save paths (Updated to .mp4) ---
            ts         = datetime.now().strftime("%Y%m%d_%H%M%S")
            clip_path  = f"incidents/clips/{camera_id}_{ts}.mp4"
            thumb_path = f"incidents/clips/{camera_id}_{ts}_thumb.jpg"
            os.makedirs("incidents/clips", exist_ok=True)

            # --- Thumbnail (middle frame of the window) ---
            thumb_frame = frames_list[len(frames_list) // 2]
            cv2.imwrite(thumb_path, thumb_frame)

            # --- Clip (Updated to mp4v web-safe format) ---
            out = cv2.VideoWriter(
                clip_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (W, H))
            for f in frames_list:
                out.write(f)
            out.release()

            # --- Behaviour ---
            behavior = tagger.analyze(frames_list)
            print(f"Behavior: {behavior['tags']}")

            # --- DB ---
            log_incident(
                camera_id      = camera_id,
                score          = smoothed_score,
                zone           = active_zone,
                behavior_tags  = behavior["tags"],
                clip_path      = clip_path,
                thumbnail_path = thumb_path,
            )
            print(f"Saved: {clip_path}")

        # ------------------------------------------------------------------
        # Display
        # ------------------------------------------------------------------
        if show_preview:
            _draw_and_show(frame, zone_mgr, person_bbox, smoothed_score,
                           active_zone, W, H, camera_id, SUSPICION_THRESH)
            elapsed_ms = int((time.time() - t_frame_start) * 1000)
            wait_ms    = max(1, target_ms - elapsed_ms)
            if cv2.waitKey(wait_ms) & 0xFF == ord('q'):
                break

    cap.release()
    if show_preview:
        cv2.destroyAllWindows()
    tagger.close()
    print(f"\nDone. Processed {frame_count} frames total.")


# ---------------------------------------------------------------------------
def _draw_and_show(frame, zone_mgr, person_bbox, score, zone,
                    W, H, camera_id, thresh):
    display = zone_mgr.draw_zones(frame.copy())

    if person_bbox is not None:
        px, py, pw, ph = person_bbox
        color = (0, 0, 255) if score > thresh else (0, 200, 0)

        if (score > thresh
                and 0 <= px and 0 <= py
                and px + pw <= W and py + ph <= H
                and pw > 0 and ph > 0):
            roi = display[py:py+ph, px:px+pw]
            if roi.size > 0:
                red = np.zeros_like(roi)
                red[:, :] = [0, 0, 200]
                display[py:py+ph, px:px+pw] = cv2.addWeighted(
                    roi, 0.75, red, 0.25, 0)

        cv2.rectangle(display, (px, py), (px+pw, py+ph), color, 2)

    hud_color = (0, 0, 255) if score > thresh else (0, 255, 0)
    label     = "!! SUSPICIOUS !!" if score > thresh else "Monitoring"

    # Keep text within frame width — scale font down for small frames
    font_scale = min(0.75, W / 500.0)
    cv2.putText(display, f"Score: {score:.2%}  {label}",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, font_scale, hud_color, 2)
    cv2.putText(display, f"Zone: {zone}",
                (10, 58), cv2.FONT_HERSHEY_SIMPLEX, font_scale * 0.75,
                (255, 255, 255), 1)

    cv2.imshow(f"AegisAI - {camera_id}", display)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="0",
                        help="Video file path or camera index")
    parser.add_argument("--camera", default="CAM_01")
    parser.add_argument("--no-preview", action="store_true")
    args = parser.parse_args()

    source = int(args.source) if args.source.isdigit() else args.source
    run_inference(source, args.camera, show_preview=not args.no_preview)