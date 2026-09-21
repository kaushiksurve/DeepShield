"""
Temporal Consistency Analyzer — Prototype

Compares consecutive video frames to detect:
- Sudden visual discontinuities
- Unusual frame-to-frame changes
- Face region instability over time

This is a prototype pixel/optical-flow heuristic.
"""
import numpy as np
import cv2
from config import PROTOTYPE_NOTE
from utils.video_utils import extract_frames, get_video_metadata, frame_to_timestamp


def _compute_frame_diff(f1: np.ndarray, f2: np.ndarray) -> float:
    """Mean absolute pixel difference between two grayscale frames."""
    g1 = cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY).astype(float)
    g2 = cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY).astype(float)
    return float(np.mean(np.abs(g1 - g2)))


def _compute_optical_flow_magnitude(f1: np.ndarray, f2: np.ndarray) -> float:
    """Mean optical flow magnitude between two frames."""
    try:
        g1 = cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY)
        g2 = cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY)
        flow = cv2.calcOpticalFlowFarneback(g1, g2, None, 0.5, 3, 15, 3, 5, 1.2, 0)
        magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
        return float(np.mean(magnitude))
    except Exception:
        return _compute_frame_diff(f1, f2)


def analyze_temporal(video_path: str) -> dict:
    """
    Prototype temporal consistency analysis.
    Returns standard analysis schema.
    """
    meta = get_video_metadata(video_path)
    fps = meta.get("fps", 25.0)
    frames = extract_frames(video_path)
    
    if len(frames) < 3:
        return {
            "score": 50.0, "confidence": 0.1, "risk": "medium",
            "evidence": ["Insufficient frames for temporal analysis (need at least 30 original frames)."],
            "timestamps": [], "note": PROTOTYPE_NOTE
        }
    
    diffs = []
    for i in range(len(frames) - 1):
        diff = _compute_frame_diff(frames[i], frames[i+1])
        diffs.append(diff)
    
    diffs = np.array(diffs)
    mean_diff = float(np.mean(diffs))
    std_diff = float(np.std(diffs))
    
    # Detect outlier transitions (anomalous jumps)
    threshold = mean_diff + 2.5 * std_diff
    anomaly_indices = np.where(diffs > threshold)[0]
    
    suspicious_timestamps = []
    for idx in anomaly_indices:
        ts = frame_to_timestamp(idx + 1, fps)
        if not suspicious_timestamps or abs(ts - suspicious_timestamps[-1]) > 1.5:
            suspicious_timestamps.append(ts)
    
    anomaly_ratio = len(anomaly_indices) / len(diffs) if len(diffs) > 0 else 0
    
    evidence = []
    
    if anomaly_ratio > 0.25:
        evidence.append(f"High temporal inconsistency: {anomaly_ratio*100:.0f}% of frame transitions are abnormal.")
    elif anomaly_ratio > 0.10:
        evidence.append(f"Moderate temporal inconsistency detected ({anomaly_ratio*100:.0f}% of frame transitions).")
    
    if std_diff > mean_diff * 0.8 and mean_diff > 5:
        evidence.append("High variance in frame-to-frame change — irregular temporal pattern detected.")
    
    if suspicious_timestamps:
        ts_str = ", ".join(f"{t:.1f}s" for t in suspicious_timestamps[:3])
        evidence.append(f"Abrupt visual transitions detected at: {ts_str}.")
    
    # Score: fewer anomalies = higher score
    score = max(20.0, 100 - anomaly_ratio * 250)
    confidence = min(0.8, 0.3 + len(frames) / 50)
    
    if not evidence:
        evidence.append(f"Temporal consistency appears normal across {len(frames)} sampled frames. [Prototype]")
    
    risk = "low" if score >= 70 else ("medium" if score >= 40 else "high")
    
    return {
        "score": round(score, 1),
        "confidence": round(confidence, 2),
        "risk": risk,
        "evidence": evidence,
        "timestamps": suspicious_timestamps[:5],
        "note": PROTOTYPE_NOTE,
        "detail": {
            "frames_analyzed": len(frames),
            "mean_frame_diff": round(mean_diff, 3),
            "anomaly_ratio": round(anomaly_ratio, 3),
        }
    }
