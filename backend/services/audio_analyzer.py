"""
Audio Authenticity Analyzer — Prototype

Analyzes audio track for:
- Audio presence and duration consistency
- Spectral feature regularity (MFCC variance)
- Energy distribution anomalies
- Unusual silence/noise patterns

Uses librosa for audio feature extraction.
This is a prototype heuristic — not a trained voice spoofing detector.
"""
import numpy as np
from config import PROTOTYPE_NOTE

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False


def analyze_audio(audio_path: str | None, video_duration: float = 0) -> dict:
    """
    Prototype audio authenticity analysis.
    Returns standard analysis schema.
    """
    if not audio_path:
        return {
            "score": 50.0, "confidence": 0.3, "risk": "medium",
            "evidence": ["No audio track found in video. Cannot perform audio analysis."],
            "timestamps": [], "note": PROTOTYPE_NOTE
        }
    
    if not LIBROSA_AVAILABLE:
        return {
            "score": 50.0, "confidence": 0.2, "risk": "medium",
            "evidence": ["librosa not available — audio analysis skipped."],
            "timestamps": [], "note": PROTOTYPE_NOTE
        }
    
    try:
        y, sr = librosa.load(audio_path, sr=22050, mono=True)
    except Exception as e:
        return {
            "score": 45.0, "confidence": 0.2, "risk": "medium",
            "evidence": [f"Audio file could not be loaded: {str(e)[:80]}"],
            "timestamps": [], "note": PROTOTYPE_NOTE
        }
    
    if len(y) < sr * 0.5:  # less than 0.5 seconds
        return {
            "score": 50.0, "confidence": 0.2, "risk": "medium",
            "evidence": ["Audio track too short for reliable analysis."],
            "timestamps": [], "note": PROTOTYPE_NOTE
        }
    
    evidence = []
    suspicious_timestamps = []
    sub_scores = []
    
    # 1. MFCC variance analysis
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    mfcc_var = float(np.mean(np.var(mfcc, axis=1)))
    # Natural speech has moderate MFCC variance; too low = synthetic/repetitive, too high = noise
    mfcc_score = 100 - min(100, max(0, abs(mfcc_var - 80) * 0.8))
    sub_scores.append(mfcc_score)
    if mfcc_var < 20:
        evidence.append(f"Very low MFCC variance ({mfcc_var:.1f}) — audio may be repetitive or synthetic.")
    elif mfcc_var > 200:
        evidence.append(f"Unusually high MFCC variance ({mfcc_var:.1f}) — possible audio splicing.")
    
    # 2. RMS energy analysis — detect abnormal silence pockets
    frame_length = 2048
    hop_length = 512
    rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
    rms_mean = float(np.mean(rms))
    rms_std = float(np.std(rms))
    
    if rms_mean < 0.001:
        evidence.append("Audio is nearly silent — possible missing or muted audio track.")
        energy_score = 20.0
    else:
        # Find anomalous energy drops within speech
        threshold = rms_mean - 2.5 * rms_std
        anomaly_frames = np.where(rms < threshold)[0]
        anomaly_ratio = len(anomaly_frames) / len(rms)
        energy_score = max(30.0, 100 - anomaly_ratio * 300)
        
        if anomaly_ratio > 0.15:
            evidence.append(f"Abnormal energy drops detected in {anomaly_ratio*100:.0f}% of audio frames.")
            # Convert anomaly frame indices to timestamps
            for f_idx in anomaly_frames[::max(1, len(anomaly_frames)//3)][:3]:
                ts = round(float(f_idx * hop_length / sr), 2)
                if not suspicious_timestamps or abs(ts - suspicious_timestamps[-1]) > 1.0:
                    suspicious_timestamps.append(ts)
    
    sub_scores.append(energy_score)
    
    # 3. Spectral centroid consistency
    spec_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    centroid_std = float(np.std(spec_centroid))
    centroid_score = max(30.0, 100 - centroid_std / 50)
    sub_scores.append(centroid_score)
    if centroid_std > 2000:
        evidence.append("High spectral centroid variance — possible audio discontinuity.")
    
    # 4. Audio duration vs video duration check
    audio_duration = len(y) / sr
    if video_duration > 0:
        duration_delta = abs(audio_duration - video_duration)
        if duration_delta > 2.0:
            evidence.append(f"Audio duration ({audio_duration:.1f}s) differs from video duration ({video_duration:.1f}s) by {duration_delta:.1f}s.")
            sub_scores.append(40.0)
        else:
            sub_scores.append(90.0)
    
    final_score = float(np.mean(sub_scores))
    confidence = 0.6 if LIBROSA_AVAILABLE else 0.2
    
    if not evidence:
        evidence.append("Audio spectral features and energy distribution appear within normal range. [Prototype]")
    
    risk = "low" if final_score >= 70 else ("medium" if final_score >= 40 else "high")
    
    return {
        "score": round(final_score, 1),
        "confidence": round(confidence, 2),
        "risk": risk,
        "evidence": evidence,
        "timestamps": suspicious_timestamps[:5],
        "note": PROTOTYPE_NOTE,
        "detail": {
            "audio_duration": round(audio_duration, 2),
            "rms_mean": round(rms_mean, 5),
            "mfcc_variance": round(mfcc_var, 2),
        }
    }
