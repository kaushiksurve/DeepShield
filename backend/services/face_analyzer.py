"""
Face Authenticity Analyzer — Prototype

Uses MediaPipe FaceMesh to detect face landmarks and analyze:
- Face detection consistency across frames
- Landmark drift (frame-to-frame instability)
- Facial boundary anomalies

This is a prototype using geometric heuristics.
A trained CNN/ViT deepfake detection model would replace this for production.
"""
import numpy as np
from config import settings, PROTOTYPE_NOTE
from utils.video_utils import extract_frames, get_video_metadata, frame_to_timestamp

try:
    import mediapipe as mp
    _mp_face_mesh = mp.solutions.face_mesh
    MEDIAPIPE_AVAILABLE = True
except Exception:
    MEDIAPIPE_AVAILABLE = False

# Key landmark indices for face region
FACE_OVAL_IDX = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
LIP_IDX = [61, 185, 40, 39, 37, 0, 267, 269, 270, 409, 291, 146, 91, 181, 84, 17, 314, 405, 321, 375]


def _landmarks_to_array(landmarks, frame_w: int, frame_h: int) -> np.ndarray:
    return np.array([[lm.x * frame_w, lm.y * frame_h] for lm in landmarks.landmark])


def _landmark_drift(prev: np.ndarray, curr: np.ndarray) -> float:
    """Mean Euclidean distance between corresponding landmarks."""
    return float(np.mean(np.linalg.norm(curr - prev, axis=1)))


def analyze_face(video_path: str) -> dict:
    """
    Prototype face authenticity analysis.
    Returns standard analysis schema.
    """
    meta = get_video_metadata(video_path)
    fps = meta.get("fps", 25.0)
    frames = extract_frames(video_path)
    
    if not frames:
        return {
            "score": 50.0, "confidence": 0.1, "risk": "medium",
            "evidence": ["Could not extract frames from video."],
            "timestamps": [], "note": PROTOTYPE_NOTE
        }
    
    if not MEDIAPIPE_AVAILABLE:
        return _fallback_face_analysis(frames, fps)
    
    face_mesh = _mp_face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    
    detection_results = []
    drift_values = []
    prev_landmarks = None
    suspicious_timestamps = []
    
    try:
        for i, frame in enumerate(frames):
            rgb = frame[:, :, ::-1]  # BGR to RGB
            h, w = frame.shape[:2]
            results = face_mesh.process(rgb)
            
            detected = results.multi_face_landmarks is not None
            detection_results.append(detected)
            
            if detected:
                lm_arr = _landmarks_to_array(results.multi_face_landmarks[0], w, h)
                if prev_landmarks is not None:
                    drift = _landmark_drift(prev_landmarks, lm_arr)
                    normalized_drift = drift / max(w, h)  # normalize by frame size
                    drift_values.append(normalized_drift)
                    
                    # Flag high-drift frames as suspicious
                    if normalized_drift > 0.03:  # prototype threshold
                        ts = frame_to_timestamp(i, fps)
                        if not suspicious_timestamps or abs(ts - suspicious_timestamps[-1]) > 1.0:
                            suspicious_timestamps.append(ts)
                
                prev_landmarks = lm_arr
    finally:
        face_mesh.close()
    
    # Compute sub-scores
    total_frames = len(detection_results)
    detected_frames = sum(detection_results)
    detection_ratio = detected_frames / total_frames if total_frames > 0 else 0
    
    evidence = []
    
    # Score 1: face detection consistency
    detection_score = detection_ratio * 100
    if detection_ratio < 0.5:
        evidence.append(f"Face detected in only {detection_ratio*100:.0f}% of sampled frames — low consistency.")
    elif detection_ratio < 0.8:
        evidence.append(f"Face not continuously visible (detected in {detection_ratio*100:.0f}% of frames).")
    
    # Score 2: landmark stability
    if drift_values:
        mean_drift = float(np.mean(drift_values))
        drift_std = float(np.std(drift_values))
        high_drift_ratio = sum(d > 0.03 for d in drift_values) / len(drift_values)
        
        # Higher drift = lower score
        drift_score = max(0, 100 - high_drift_ratio * 200)
        
        if high_drift_ratio > 0.3:
            evidence.append(f"High facial landmark instability detected in {high_drift_ratio*100:.0f}% of frame transitions.")
        if drift_std > 0.02:
            evidence.append("Irregular variance in facial landmark drift — possible editing artifact.")
        
        if suspicious_timestamps:
            evidence.append(f"Significant facial inconsistencies at {len(suspicious_timestamps)} timestamp(s).")
    else:
        drift_score = 50.0
        if detected_frames == 0:
            evidence.append("No face detected in video.")
    
    # Combined face score
    if detected_frames == 0:
        final_score = 30.0
        confidence = 0.4
    else:
        final_score = 0.5 * detection_score + 0.5 * drift_score
        confidence = min(0.9, 0.4 + detection_ratio * 0.5)
    
    if not evidence:
        evidence.append("Face detection consistent across sampled frames. Landmark drift within normal range. [Prototype]")
    
    risk = "low" if final_score >= 70 else ("medium" if final_score >= 40 else "high")
    
    return {
        "score": round(final_score, 1),
        "confidence": round(confidence, 2),
        "risk": risk,
        "evidence": evidence,
        "timestamps": suspicious_timestamps[:5],
        "note": PROTOTYPE_NOTE,
        "detail": {
            "detection_ratio": round(detection_ratio, 2),
            "frames_analyzed": total_frames,
            "mean_drift": round(float(np.mean(drift_values)) if drift_values else 0, 4),
        }
    }


def _fallback_face_analysis(frames: list, fps: float) -> dict:
    """Simple pixel-variance fallback when MediaPipe is unavailable."""
    from utils.video_utils import frame_to_timestamp
    gray_frames = [np.mean(f, axis=2) for f in frames]
    if len(gray_frames) < 2:
        return {"score": 50.0, "confidence": 0.1, "risk": "medium",
                "evidence": ["Insufficient frames for analysis."], "timestamps": [], "note": PROTOTYPE_NOTE}
    
    diffs = [np.mean(np.abs(gray_frames[i+1] - gray_frames[i])) for i in range(len(gray_frames)-1)]
    mean_diff = float(np.mean(diffs))
    diff_std = float(np.std(diffs))
    
    suspicious = [frame_to_timestamp(i+1, fps) for i, d in enumerate(diffs) if d > mean_diff + 2*diff_std]
    score = max(30.0, 80.0 - min(50.0, diff_std * 500))
    
    return {
        "score": round(score, 1), "confidence": 0.4, "risk": "low" if score >= 70 else "medium",
        "evidence": ["Prototype pixel-variance analysis (MediaPipe unavailable). Frame variation analyzed."],
        "timestamps": suspicious[:5], "note": PROTOTYPE_NOTE
    }
