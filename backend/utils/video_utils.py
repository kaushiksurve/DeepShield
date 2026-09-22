import cv2
import numpy as np
import subprocess
import os
import tempfile
from pathlib import Path
from config import settings

def extract_frames(video_path: str, sample_rate: int = None) -> list[np.ndarray]:
    """
    Extract frames from video at given sample rate, capped at max_frames.
    Resizes frames to max 640px wide to reduce CPU load.
    Returns list of BGR numpy arrays.
    """
    if sample_rate is None:
        sample_rate = settings.frame_sample_rate

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    frames = []
    frame_idx = 0
    max_frames = getattr(settings, 'max_frames', 40)
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % sample_rate == 0:
                # Resize to max 640px wide to reduce MediaPipe CPU load
                h, w = frame.shape[:2]
                if w > 640:
                    scale = 640 / w
                    frame = cv2.resize(frame, (640, int(h * scale)))
                frames.append(frame)
                if len(frames) >= max_frames:
                    break
            frame_idx += 1
    finally:
        cap.release()

    return frames


def get_video_metadata(video_path: str) -> dict:
    """Extract video metadata: fps, frame count, duration, width, height."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {"error": "Cannot open video"}
    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        return {
            "fps": fps,
            "frame_count": frame_count,
            "duration": round(duration, 2),
            "width": width,
            "height": height,
        }
    finally:
        cap.release()

def extract_audio(video_path: str) -> str | None:
    """
    Extract audio from video to a temporary WAV file.
    Returns path to WAV file, or None if no audio.
    Tries ffmpeg first, falls back to opencv-based check.
    """
    wav_path = video_path.replace(Path(video_path).suffix, "_audio.wav")
    try:
        result = subprocess.run(
            [
                "ffmpeg", "-y", "-i", video_path,
                "-vn", "-acodec", "pcm_s16le",
                "-ar", "22050", "-ac", "1",
                wav_path
            ],
            capture_output=True, timeout=60
        )
        if result.returncode == 0 and os.path.exists(wav_path) and os.path.getsize(wav_path) > 1000:
            return wav_path
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        # ffmpeg not available
        return None

def frame_to_timestamp(frame_idx: int, fps: float, sample_rate: int = None) -> float:
    """Convert sampled frame index to real video timestamp in seconds."""
    if sample_rate is None:
        sample_rate = settings.frame_sample_rate
    return round(frame_idx * sample_rate / fps, 2)
