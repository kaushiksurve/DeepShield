from pydantic_settings import BaseSettings
from typing import Dict

PROTOTYPE_NOTE = (
    "DeepShield prototype — thresholds are heuristic, not trained on a labeled deepfake dataset. "
    "Results are indicative only and should not be treated as definitive proof of media authenticity."
)

DEMO_NOTE = "DEMO / SIMULATED RESULT — This result is pre-computed for demonstration purposes and is NOT a real AI prediction."

class Settings(BaseSettings):
    max_upload_mb: int = 100
    allowed_extensions: list = [".mp4", ".mov", ".webm", ".avi"]
    allowed_mimetypes: list = ["video/mp4", "video/quicktime", "video/webm", "video/x-msvideo", "video/avi"]
    frame_sample_rate: int = 10  # process every Nth frame
    temp_dir: str = "temp_uploads"
    db_path: str = "deepshield.db"
    cors_origins: list = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]
    
    # Fusion weights (must sum to 1.0)
    fusion_weights: Dict[str, float] = {
        "face": 0.25,
        "audio": 0.15,
        "lipsync": 0.20,
        "liveness": 0.15,
        "temporal": 0.15,
        "behavior": 0.10,
    }
    
    # Risk thresholds
    low_risk_threshold: int = 70
    suspicious_threshold: int = 40
    
    class Config:
        env_file = ".env"

settings = Settings()
