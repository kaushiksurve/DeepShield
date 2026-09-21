"""
Behavioral Signal Analyzer — Prototype

Analyzes:
- Head pose (yaw/pitch proxy from nose position)
- Face position consistency
- Sudden behavioral changes
- Movement naturalness

Lightweight prototype using MediaPipe face landmarks.
"""
import numpy as np
from config import PROTOTYPE_NOTE
from utils.video_utils import extract_frames, get_video_metadata, frame_to_timestamp

try:
    import mediapipe as mp
    _mp_face_mesh = mp.solutions.face_mesh
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False

# Landmark indices for pose estimation proxy
NOSE_TIP = 1
CHIN = 152
LEFT_EYE_INNER = 133
RIGHT_EYE_INNER = 362
LEFT_MOUTH = 61
RIGHT_MOUTH = 291


def _head_pose_proxy(lm, w: int, h: int) -> tuple[float, float]:
    """Estimate rough yaw/pitch from landmark positions."""
    # Yaw: horizontal asymmetry between left/right eye corners and nose
    left_x = lm[LEFT_EYE_INNER].x * w
    right_x = lm[RIGHT_EYE_INNER].x * w
    nose_x = lm[NOSE_TIP].x * w
    eye_center_x = (left_x + right_x) / 2
    yaw_proxy = (nose_x - eye_center_x) / max(abs(right_x - left_x), 1)
    
    # Pitch: vertical position of nose relative to eyes-chin span
    eye_y = (lm[LEFT_EYE_INNER].y + lm[RIGHT_EYE_INNER].y) / 2 * h
    chin_y = lm[CHIN].y * h
    nose_y = lm[NOSE_TIP].y * h
    vertical_span = max(chin_y - eye_y, 1)
    pitch_proxy = (nose_y - eye_y) / vertical_span
    
    return float(yaw_proxy), float(pitch_proxy)


def analyze_behavior(video_path: str) -> dict:
    """
    Prototype behavioral signal analysis.
    Returns standard analysis schema.
    """
    meta = get_video_metadata(video_path)
    fps = meta.get("fps", 25.0)
    frames = extract_frames(video_path)
    
    if not frames:
        return {
            "score": 50.0, "confidence": 0.1, "risk": "medium",
            "evidence": ["No frames for behavioral analysis."],
            "timestamps": [], "note": PROTOTYPE_NOTE
        }
    
    if not MEDIAPIPE_AVAILABLE:
        return {"score": 50.0, "confidence": 0.2, "risk": "medium",
                "evidence": ["MediaPipe unavailable — behavioral analysis skipped."],
                "timestamps": [], "note": PROTOTYPE_NOTE}
    
    face_mesh = _mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1,
                                        min_detection_confidence=0.5)
    
    yaw_series = []
    pitch_series = []
    face_x_series = []
    face_y_series = []
    detected = 0
    
    try:
        for frame in frames:
            rgb = frame[:, :, ::-1]
            h, w = frame.shape[:2]
            results = face_mesh.process(rgb)
            if results.multi_face_landmarks:
                detected += 1
                lm = results.multi_face_landmarks[0].landmark
                yaw, pitch = _head_pose_proxy(lm, w, h)
                yaw_series.append(yaw)
                pitch_series.append(pitch)
                face_x_series.append(lm[NOSE_TIP].x)
                face_y_series.append(lm[NOSE_TIP].y)
    finally:
        face_mesh.close()
    
    if not yaw_series:
        return {"score": 40.0, "confidence": 0.2, "risk": "medium",
                "evidence": ["No face detected for behavioral analysis."],
                "timestamps": [], "note": PROTOTYPE_NOTE}
    
    yaw = np.array(yaw_series)
    pitch = np.array(pitch_series)
    face_x = np.array(face_x_series)
    face_y = np.array(face_y_series)
    
    # Detect sudden jumps in head pose
    yaw_diff = np.abs(np.diff(yaw))
    pitch_diff = np.abs(np.diff(pitch))
    
    yaw_threshold = float(np.mean(yaw_diff)) + 2 * float(np.std(yaw_diff))
    pitch_threshold = float(np.mean(pitch_diff)) + 2 * float(np.std(pitch_diff))
    
    jump_frames = np.where((yaw_diff > yaw_threshold) | (pitch_diff > pitch_threshold))[0]
    jump_ratio = len(jump_frames) / len(yaw_diff) if len(yaw_diff) > 0 else 0
    
    suspicious_timestamps = []
    for idx in jump_frames[:5]:
        ts = frame_to_timestamp(idx + 1, fps)
        if not suspicious_timestamps or abs(ts - suspicious_timestamps[-1]) > 1.0:
            suspicious_timestamps.append(ts)
    
    evidence = []
    
    # Position stability analysis
    pos_range_x = float(np.max(face_x) - np.min(face_x))
    pos_range_y = float(np.max(face_y) - np.min(face_y))
    
    if pos_range_x < 0.01 and pos_range_y < 0.01 and len(frames) > 5:
        evidence.append("Face position appears unnaturally fixed — very little natural movement.")
    
    if jump_ratio > 0.2:
        evidence.append(f"Sudden head pose changes in {jump_ratio*100:.0f}% of frame transitions — possible editing.")
    elif jump_ratio > 0.1:
        evidence.append(f"Moderate head pose instability ({jump_ratio*100:.0f}% of transitions).")
    
    if suspicious_timestamps:
        ts_str = ", ".join(f"{t:.1f}s" for t in suspicious_timestamps[:3])
        evidence.append(f"Abrupt pose changes at: {ts_str}.")
    
    score = max(20.0, 100 - jump_ratio * 300)
    confidence = min(0.75, 0.3 + detected / len(frames) * 0.45)
    
    if not evidence:
        evidence.append(f"Head pose and behavioral signals appear natural across {len(frames)} frames. [Prototype]")
    
    risk = "low" if score >= 70 else ("medium" if score >= 40 else "high")
    
    return {
        "score": round(score, 1),
        "confidence": round(confidence, 2),
        "risk": risk,
        "evidence": evidence,
        "timestamps": suspicious_timestamps[:5],
        "note": PROTOTYPE_NOTE,
        "detail": {"yaw_range": round(float(np.max(yaw)-np.min(yaw)), 3),
                   "pitch_range": round(float(np.max(pitch)-np.min(pitch)), 3),
                   "jump_ratio": round(jump_ratio, 3)}
    }
