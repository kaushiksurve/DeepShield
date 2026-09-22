"""
Lip-Speech Synchronization Analyzer — Prototype

Compares:
  - Mouth aperture time series (from MediaPipe FaceMesh)
  - Audio RMS energy time series

Using cross-correlation to measure temporal synchronization.
Adapted from the existing SyncShield scoring.py algorithm.

This is a prototype. It does not perform full phoneme-level lip reading.
"""
import numpy as np
from config import PROTOTYPE_NOTE

try:
    import mediapipe as mp
    import cv2
    _mp_face_mesh = mp.solutions.face_mesh
    MEDIAPIPE_AVAILABLE = True
except Exception:
    MEDIAPIPE_AVAILABLE = False

try:
    import librosa
    LIBROSA_AVAILABLE = True
except Exception:
    LIBROSA_AVAILABLE = False

# Upper/lower lip landmark indices for mouth aperture
UPPER_LIP = 13
LOWER_LIP = 14


def _smooth(x, k=3):
    return np.convolve(x, np.ones(k) / k, mode="same")

def _norm01(x):
    lo, hi = np.percentile(x, 5), np.percentile(x, 95)
    return np.clip((x - lo) / (hi - lo + 1e-9), 0, 1)

def _xcorr(a, b, max_lag):
    best = (-1.0, 0)
    for lag in range(-max_lag, max_lag + 1):
        if lag >= 0:
            x, y = a[:len(a)-lag] if lag > 0 else a, b[lag:] if lag > 0 else b
        else:
            x, y = a[-lag:], b[:len(b)+lag]
        if len(x) < 5 or x.std() < 1e-9 or y.std() < 1e-9:
            continue
        c = float(np.corrcoef(x, y)[0, 1])
        if c > best[0]:
            best = (c, lag)
    return best


def _extract_mouth_aperture(video_path: str, fps: float, sample_rate: int = 5) -> list[float]:
    """Extract per-frame mouth aperture from video (capped at 200 samples)."""
    if not MEDIAPIPE_AVAILABLE:
        return []

    import cv2
    cap = cv2.VideoCapture(video_path)
    face_mesh = _mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1,
                                        min_detection_confidence=0.5)
    apertures = []
    frame_idx = 0
    MAX_SAMPLES = 200
    try:
        while len(apertures) < MAX_SAMPLES:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % sample_rate == 0:
                rgb = frame[:, :, ::-1]
                h, w = frame.shape[:2]
                results = face_mesh.process(rgb)
                if results.multi_face_landmarks:
                    lm = results.multi_face_landmarks[0].landmark
                    upper_y = lm[13].y * h
                    lower_y = lm[14].y * h
                    face_height = abs(lm[10].y - lm[152].y) * h
                    aperture = abs(lower_y - upper_y) / (face_height + 1e-6)
                    apertures.append(aperture)
                else:
                    apertures.append(0.0)
            frame_idx += 1
    finally:
        cap.release()
        face_mesh.close()

    return apertures


def _extract_audio_rms_series(audio_path: str, target_length: int) -> list[float]:
    """Extract RMS energy series resampled to target_length points."""
    if not LIBROSA_AVAILABLE or not audio_path:
        return []
    import librosa
    try:
        y, sr = librosa.load(audio_path, sr=22050, mono=True)
        hop = max(1, len(y) // target_length)
        rms = librosa.feature.rms(y=y, frame_length=hop*2, hop_length=hop)[0]
        # Resample to target_length
        indices = np.linspace(0, len(rms)-1, target_length).astype(int)
        return [float(rms[i]) for i in indices]
    except Exception:
        return []


def analyze_lipsync(video_path: str, audio_path: str | None, fps: float = 25.0) -> dict:
    """
    Prototype lip-speech synchronization analysis.
    Returns standard analysis schema.
    """
    if not MEDIAPIPE_AVAILABLE:
        return {
            "score": 50.0, "confidence": 0.2, "risk": "medium",
            "evidence": ["MediaPipe not available — lip-sync analysis skipped."],
            "timestamps": [], "note": PROTOTYPE_NOTE
        }
    
    sample_rate = 5  # every 5th frame for lipsync (more temporal resolution)
    lip_series = _extract_mouth_aperture(video_path, fps, sample_rate)
    
    if len(lip_series) < 10:
        return {
            "score": 50.0, "confidence": 0.2, "risk": "medium",
            "evidence": ["Insufficient lip landmark data for synchronization analysis."],
            "timestamps": [], "note": PROTOTYPE_NOTE
        }
    
    if not audio_path:
        return {
            "score": 50.0, "confidence": 0.2, "risk": "medium",
            "evidence": ["No audio available for lip-speech synchronization check."],
            "timestamps": [], "note": PROTOTYPE_NOTE
        }
    
    audio_series = _extract_audio_rms_series(audio_path, len(lip_series))
    
    if len(audio_series) < 10:
        return {
            "score": 50.0, "confidence": 0.2, "risk": "medium",
            "evidence": ["Could not extract audio time series for synchronization."],
            "timestamps": [], "note": PROTOTYPE_NOTE
        }
    
    lip = np.array(lip_series)
    audio = np.array(audio_series[:len(lip)])
    lip = _smooth(lip)
    audio = _smooth(audio)
    
    # Normalize
    lip_n = _norm01(lip)
    audio_n = _norm01(audio)
    
    # Cross-correlation
    fps_sampled = fps / sample_rate
    max_lag = int(fps_sampled * 0.5)  # max 0.5 second lag
    
    lip_z = (lip - lip.mean()) / (lip.std() + 1e-9)
    audio_z = (audio - audio.mean()) / (audio.std() + 1e-9)
    peak_corr, best_lag = _xcorr(lip_z, audio_z, max_lag)
    lag_ms = best_lag * 1000 / fps_sampled
    
    # Sub-scores
    corr_score = float(np.clip((peak_corr - 0.1) / 0.55, 0, 1))
    lag_score = float(np.clip(1 - (abs(lag_ms) - 120) / 280, 0, 1))
    
    # Activity overlap: do mouth-open and speech-active frames co-occur?
    speech_active = audio_n > 0.25
    mouth_open = lip_n > 0.35
    if mouth_open.sum() > 0 and speech_active.sum() > 0:
        speech_dilated = np.convolve(speech_active.astype(float), np.ones(3), mode="same") > 0
        mouth_dilated = np.convolve(mouth_open.astype(float), np.ones(3), mode="same") > 0
        p = float(speech_dilated[mouth_open].mean())
        r = float(mouth_dilated[speech_active].mean())
        act_score = (2 * p * r / (p + r)) if (p + r) > 0 else 0.0
    else:
        act_score = 0.5
    
    final_score = 100 * (0.40 * corr_score + 0.30 * lag_score + 0.30 * act_score)
    confidence = 0.65 if MEDIAPIPE_AVAILABLE and LIBROSA_AVAILABLE else 0.3
    
    evidence = []
    suspicious_timestamps = []
    
    if corr_score < 0.4:
        evidence.append(f"Weak lip-speech correlation (r={peak_corr:.2f}) — mouth movement may not match audio source.")
        # Find worst-corr segments
        segment_size = max(5, len(lip) // 8)
        for seg_start in range(0, len(lip) - segment_size, segment_size):
            seg_lip = lip_z[seg_start:seg_start+segment_size]
            seg_aud = audio_z[seg_start:seg_start+segment_size]
            if seg_lip.std() > 1e-9 and seg_aud.std() > 1e-9:
                local_corr = float(np.corrcoef(seg_lip, seg_aud)[0, 1])
                if local_corr < 0.1:
                    ts = round(seg_start * sample_rate / fps, 2)
                    suspicious_timestamps.append(ts)
    
    if lag_score < 0.4:
        evidence.append(f"Audio-lip timing offset of {lag_ms:+.0f}ms exceeds natural sync range (±120ms).")
    
    if act_score < 0.4:
        evidence.append("Speech bursts do not align with mouth-open intervals — possible audio substitution.")
    
    if not evidence:
        evidence.append(f"Lip-speech synchronization within acceptable range (correlation: {peak_corr:.2f}). [Prototype]")
    
    risk = "low" if final_score >= 70 else ("medium" if final_score >= 40 else "high")
    
    return {
        "score": round(final_score, 1),
        "confidence": round(confidence, 2),
        "risk": risk,
        "evidence": evidence,
        "timestamps": sorted(suspicious_timestamps)[:5],
        "note": PROTOTYPE_NOTE,
        "detail": {"correlation": round(peak_corr, 3), "lag_ms": round(lag_ms), "activity_overlap": round(act_score, 3)}
    }
