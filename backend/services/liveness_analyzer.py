"""
Liveness Analyzer — Prototype

For pre-recorded video, analyzes proxy liveness indicators:
- Cumulative face movement (static face = suspicious)
- Natural variation in facial features
- Eye aspect ratio proxy (blink indicator)

IMPORTANT: This is NOT full biometric liveness verification.
It is a prototype heuristic. Label as: 'Prototype Liveness Analysis'.
"""
import numpy as np
from config import PROTOTYPE_NOTE
from utils.video_utils import extract_frames, get_video_metadata, frame_to_timestamp

try:
    import mediapipe as mp
    _mp_face_mesh = mp.solutions.face_mesh
    MEDIAPIPE_AVAILABLE = True
except Exception:
    MEDIAPIPE_AVAILABLE = False

# Eye landmarks for EAR (Eye Aspect Ratio) computation
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]


def _ear(eye_pts: np.ndarray) -> float:
    """Compute Eye Aspect Ratio."""
    v1 = np.linalg.norm(eye_pts[1] - eye_pts[5])
    v2 = np.linalg.norm(eye_pts[2] - eye_pts[4])
    h = np.linalg.norm(eye_pts[0] - eye_pts[3])
    return (v1 + v2) / (2.0 * h + 1e-6)


def analyze_liveness(video_path: str) -> dict:
    """
    Prototype liveness analysis for pre-recorded video.
    Returns standard analysis schema.
    """
    meta = get_video_metadata(video_path)
    fps = meta.get("fps", 25.0)
    frames = extract_frames(video_path, sample_rate=5)  # finer sampling for liveness
    
    if not frames:
        return {
            "score": 50.0, "confidence": 0.1, "risk": "medium",
            "evidence": ["No frames extracted for liveness analysis."],
            "timestamps": [], "note": PROTOTYPE_NOTE
        }
    
    if not MEDIAPIPE_AVAILABLE:
        return _fallback_liveness(frames, fps)
    
    face_mesh = _mp_face_mesh.FaceMesh(
        static_image_mode=False, max_num_faces=1,
        refine_landmarks=True, min_detection_confidence=0.5
    )
    
    ear_series = []
    face_positions = []
    detected_count = 0
    
    try:
        for frame in frames:
            rgb = frame[:, :, ::-1]
            h, w = frame.shape[:2]
            results = face_mesh.process(rgb)
            if results.multi_face_landmarks:
                detected_count += 1
                lm = results.multi_face_landmarks[0].landmark
                
                # EAR computation
                left_pts = np.array([[lm[i].x * w, lm[i].y * h] for i in LEFT_EYE])
                right_pts = np.array([[lm[i].x * w, lm[i].y * h] for i in RIGHT_EYE])
                avg_ear = (float(_ear(left_pts)) + float(_ear(right_pts))) / 2
                ear_series.append(avg_ear)
                
                # Face center position
                nose_x = lm[1].x
                nose_y = lm[1].y
                face_positions.append((nose_x, nose_y))
    finally:
        face_mesh.close()
    
    evidence = []
    suspicious_timestamps = []
    
    if not ear_series:
        return {
            "score": 40.0, "confidence": 0.3, "risk": "medium",
            "evidence": ["No face detected for liveness analysis."],
            "timestamps": [], "note": PROTOTYPE_NOTE
        }
    
    ear_arr = np.array(ear_series)
    ear_std = float(np.std(ear_arr))
    ear_mean = float(np.mean(ear_arr))
    
    # Blink detection: EAR drops below 70% of mean
    blink_threshold = ear_mean * 0.7
    blink_frames = np.where(ear_arr < blink_threshold)[0]
    blink_count = len(blink_frames)
    
    # Movement analysis
    if face_positions:
        positions = np.array(face_positions)
        pos_std = float(np.mean(np.std(positions, axis=0)))
        movement_score = min(100, pos_std * 2000)  # more movement = more liveness
    else:
        pos_std = 0
        movement_score = 0
    
    # Scoring
    # Natural variation: moderate EAR std is good
    variation_score = min(100, ear_std * 2000)
    
    # Blink bonus: at least 1 blink in typical 10-second video
    video_duration = meta.get("duration", 0)
    expected_blinks = max(1, video_duration / 5)  # ~1 blink per 5 seconds
    blink_score = min(100, (blink_count / expected_blinks) * 100) if expected_blinks > 0 else 50
    
    # Too-static face is suspicious
    static_penalty = 0
    if pos_std < 0.002 and video_duration > 3:
        evidence.append("Face appears unnaturally static — very little head movement detected.")
        static_penalty = 30
    
    if blink_count == 0 and video_duration > 5:
        evidence.append("No blink-like eye movement detected in video. [Prototype blink proxy]")
        static_penalty += 10
    
    final_score = max(10, (0.35 * variation_score + 0.35 * blink_score + 0.30 * movement_score) - static_penalty)
    final_score = min(95, final_score)  # cap — prototype cannot confirm liveness at 100%
    
    confidence = min(0.7, 0.3 + detected_count / len(frames) * 0.4)
    
    if not evidence:
        liveness_desc = "Adequate" if final_score >= 60 else "Limited"
        evidence.append(f"{liveness_desc} face movement and variation detected. Blinks detected: {blink_count}. [Prototype liveness proxy]")
    
    risk = "low" if final_score >= 70 else ("medium" if final_score >= 40 else "high")
    
    return {
        "score": round(final_score, 1),
        "confidence": round(confidence, 2),
        "risk": risk,
        "evidence": evidence,
        "timestamps": suspicious_timestamps[:5],
        "note": PROTOTYPE_NOTE,
        "detail": {
            "blinks_detected": blink_count,
            "head_movement_std": round(pos_std, 4),
            "ear_variance": round(ear_std, 4),
        }
    }


def _fallback_liveness(frames: list, fps: float) -> dict:
    """Fallback using pixel variance when MediaPipe unavailable."""
    grays = [np.mean(f, axis=2) for f in frames]
    stds = [float(np.std(g)) for g in grays]
    mean_std = float(np.mean(stds))
    score = min(80, mean_std * 2)
    return {
        "score": round(score, 1), "confidence": 0.3, "risk": "medium",
        "evidence": ["Prototype pixel-variance liveness proxy (MediaPipe unavailable)."],
        "timestamps": [], "note": PROTOTYPE_NOTE
    }
