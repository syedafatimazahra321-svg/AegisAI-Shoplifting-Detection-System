import mediapipe as mp
import cv2
import numpy as np

mp_pose = mp.solutions.pose

class BehaviourTagger:
    """
    Rule-based behavior analysis using MediaPipe pose keypoints.
    Runs AFTER the LSTM flags a window as suspicious.
    Returns a list of behavior tags explaining the detection.
    """
    def __init__(self):
        self.pose = mp_pose.Pose(
            static_image_mode=False,
            model_complexity=0,        # fastest configuration
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

    def analyze(self, frames):
        """
        frames: list of BGR frames (the 16 suspicious frames)
        returns: dict with tags and their confidence counts
        """
        concealment_count = 0
        loitering_count   = 0
        erratic_count     = 0
        exit_hover_count  = 0
        
        prev_cx, prev_cy = None, None
        velocities = []

        for frame in frames:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self.pose.process(rgb)
            if not result.pose_landmarks:
                continue
                
            lm = result.pose_landmarks.landmark
            h, w = frame.shape[:2]

            # --- Concealment: wrists near torso (jacket stuffing motion) ---
            left_wrist  = lm[mp_pose.PoseLandmark.LEFT_WRIST]
            right_wrist = lm[mp_pose.PoseLandmark.RIGHT_WRIST]
            left_hip    = lm[mp_pose.PoseLandmark.LEFT_HIP]
            right_hip   = lm[mp_pose.PoseLandmark.RIGHT_HIP]
            left_shoulder  = lm[mp_pose.PoseLandmark.LEFT_SHOULDER]
            right_shoulder = lm[mp_pose.PoseLandmark.RIGHT_SHOULDER]
            
            torso_center_y = (left_shoulder.y + right_shoulder.y + 
                              left_hip.y + right_hip.y) / 4
            wrist_avg_y = (left_wrist.y + right_wrist.y) / 2

            # Wrists near torso vertically = concealment gesture
            if abs(wrist_avg_y - torso_center_y) < 0.15:
                concealment_count += 1

            # --- Loitering: person moving slowly or staying still ---
            cx = (left_hip.x + right_hip.x) / 2 * w
            cy = (left_hip.y + right_hip.y) / 2 * h
            
            if prev_cx is not None:
                velocity = np.sqrt((cx-prev_cx)**2 + (cy-prev_cy)**2)
                velocities.append(velocity)
            prev_cx, prev_cy = cx, cy

            # --- Erratic: arm raised rapidly (stuffing motion) ---
            left_elbow  = lm[mp_pose.PoseLandmark.LEFT_ELBOW]
            right_elbow = lm[mp_pose.PoseLandmark.RIGHT_ELBOW]
            
            if (left_shoulder.y - left_elbow.y > 0.1 or 
                right_shoulder.y - right_elbow.y > 0.1):
                erratic_count += 1

        # --- Loitering check: consistently low velocity ---
        if velocities and np.mean(velocities) < 5:
            loitering_count = len(frames) // 2

        # --- Erratic check: high velocity variance ---
        if velocities and np.std(velocities) > 15:
            erratic_count = max(erratic_count, len(frames) // 3)

        # --- Build tags list ---
        tags = []
        threshold = len(frames) * 0.4  # 40% of frames must show behaviour
        
        if concealment_count >= threshold:
            tags.append(f"CONCEALMENT ({concealment_count}/{len(frames)} frames)")
        if loitering_count >= threshold:
            tags.append(f"LOITERING (avg speed: {np.mean(velocities):.1f}px/frame)")
        if erratic_count >= threshold:
            tags.append("ERRATIC MOVEMENT (rapid arm motion)")
            
        if not tags:
            tags.append("SUSPICIOUS POSTURE")

        return {
            "tags": tags,
            "concealment_score": concealment_count / len(frames),
            "loitering_score":   loitering_count  / len(frames),
            "erratic_score":     erratic_count    / len(frames),
        }

    def close(self):
        self.pose.close()

# Test Block
if __name__ == "__main__":
    import numpy as np
    tagger = BehaviorTagger()
    dummy_frames = [np.random.randint(0, 255, (480, 640, 3), 
                    dtype=np.uint8) for _ in range(16)]
    result = tagger.analyze(dummy_frames)
    print("Tags:", result["tags"])
    print("Behavior Tagger OK!")
    tagger.close()