"""
DeepShield — FastAPI Backend
Multi-Layer Deepfake & Identity Verification System
Hackathon Prototype — Team AI Warriors
"""
import asyncio
import os
import time
import uuid
from pathlib import Path

import aiofiles
from fastapi import FastAPI, File, HTTPException, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings, PROTOTYPE_NOTE, DEMO_NOTE
from database import init_db, create_analysis, update_analysis, get_analysis, list_analyses
from utils.security import sanitize_filename, validate_video_file, cleanup_file
from utils.video_utils import get_video_metadata, extract_audio
from services.face_analyzer import analyze_face
from services.audio_analyzer import analyze_audio
from services.lipsync_analyzer import analyze_lipsync
from services.temporal_analyzer import analyze_temporal
from services.liveness_analyzer import analyze_liveness
from services.behavior_analyzer import analyze_behavior
from services.fusion_engine import fuse_results
from services.explanation_engine import generate_explanation

app = FastAPI(
    title="DeepShield API",
    description="Multi-Layer Deepfake & Identity Verification — Hackathon Prototype",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure temp directory exists
os.makedirs(settings.temp_dir, exist_ok=True)


@app.on_event("startup")
async def startup():
    await init_db()


# ─────────────────────────────────────────────
# Health
# ─────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "DeepShield Analysis Engine",
        "version": "1.0.0",
        "note": PROTOTYPE_NOTE,
    }


# ─────────────────────────────────────────────
# Analysis
# ─────────────────────────────────────────────

async def _run_analysis(analysis_id: str, video_path: str, filename: str):
    """Run the full analysis pipeline in background."""
    audio_path = None
    try:
        start_time = time.time()
        
        # Get video metadata
        meta = get_video_metadata(video_path)
        
        # Extract audio
        audio_path = extract_audio(video_path)
        
        # Run all modules
        face_result = analyze_face(video_path)
        audio_result = analyze_audio(audio_path, meta.get("duration", 0))
        lipsync_result = analyze_lipsync(video_path, audio_path, meta.get("fps", 25.0))
        temporal_result = analyze_temporal(video_path)
        liveness_result = analyze_liveness(video_path)
        behavior_result = analyze_behavior(video_path)
        
        module_results = {
            "face": face_result,
            "audio": audio_result,
            "lipsync": lipsync_result,
            "temporal": temporal_result,
            "liveness": liveness_result,
            "behavior": behavior_result,
        }
        
        # Fuse results
        fusion = fuse_results(module_results)
        
        # Generate explanation
        explanation = generate_explanation(fusion)
        
        elapsed = round(time.time() - start_time, 2)
        
        result = {
            "analysis_id": analysis_id,
            "filename": filename,
            "video_metadata": meta,
            "processing_time_s": elapsed,
            **fusion,
            "explanation": explanation,
            "is_demo": False,
        }
        
        await update_analysis(analysis_id, "complete", result)
    
    except Exception as e:
        error_result = {
            "analysis_id": analysis_id,
            "error": str(e)[:200],
            "trust_score": None,
            "risk_level": "error",
        }
        await update_analysis(analysis_id, "error", error_result)
    
    finally:
        cleanup_file(video_path)
        if audio_path:
            cleanup_file(audio_path)


@app.post("/api/analyze")
async def analyze_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload a video file and start analysis."""
    content = await file.read()
    
    # Validate
    validate_video_file(file, content)
    
    safe_name = sanitize_filename(file.filename or "video.mp4")
    ext = Path(safe_name).suffix
    unique_name = f"{uuid.uuid4().hex}{ext}"
    video_path = os.path.join(settings.temp_dir, unique_name)
    
    # Save file
    async with aiofiles.open(video_path, "wb") as f:
        await f.write(content)
    
    # Create DB record
    analysis_id = await create_analysis(safe_name, len(content))
    
    # Kick off background analysis
    background_tasks.add_task(_run_analysis, analysis_id, video_path, safe_name)
    
    return {
        "analysis_id": analysis_id,
        "status": "processing",
        "filename": safe_name,
        "file_size": len(content),
        "message": "Analysis started. Poll GET /api/analysis/{id} for results.",
    }


@app.get("/api/analysis/{analysis_id}")
async def get_analysis_result(analysis_id: str):
    """Get analysis result by ID."""
    record = await get_analysis(analysis_id)
    if not record:
        raise HTTPException(404, f"Analysis '{analysis_id}' not found")
    return record


@app.get("/api/analyses")
async def list_all_analyses(limit: int = 20):
    """List recent analyses."""
    return await list_analyses(limit)


# ─────────────────────────────────────────────
# Demo Mode
# ─────────────────────────────────────────────

DEMO_SCENARIOS = {
    "genuine": {
        "trust_score": 84.5,
        "risk_level": "low",
        "module_scores": {
            "face": {"label": "Face Authenticity", "score": 88.0, "confidence": 0.75, "risk": "low",
                     "evidence": ["Face detection consistent (96% of frames). Landmark drift within normal range."],
                     "timestamps": [], "weight": 25},
            "audio": {"label": "Audio Authenticity", "score": 82.0, "confidence": 0.65, "risk": "low",
                      "evidence": ["MFCC variance normal. Energy distribution consistent."],
                      "timestamps": [], "weight": 15},
            "lipsync": {"label": "Lip-Speech Consistency", "score": 79.0, "confidence": 0.70, "risk": "low",
                        "evidence": ["Lip-speech correlation 0.71. Timing offset within natural range."],
                        "timestamps": [], "weight": 20},
            "temporal": {"label": "Temporal Consistency", "score": 86.0, "confidence": 0.80, "risk": "low",
                         "evidence": ["No significant frame discontinuities detected."],
                         "timestamps": [], "weight": 15},
            "liveness": {"label": "Liveness", "score": 81.0, "confidence": 0.65, "risk": "low",
                         "evidence": ["Natural head movement. Blinks detected: 4. [Prototype liveness proxy]"],
                         "timestamps": [], "weight": 15},
            "behavior": {"label": "Behavioral Signals", "score": 85.0, "confidence": 0.60, "risk": "low",
                         "evidence": ["Head pose variation consistent with natural conversation."],
                         "timestamps": [], "weight": 10},
        },
        "evidence": [],
        "timeline": [],
        "explanation": {
            "intro": "DeepShield's multi-layer analysis found no significant indicators of media manipulation.",
            "findings": [],
            "passing_modules": ["Face Authenticity", "Audio Authenticity", "Lip-Speech Consistency",
                                 "Temporal Consistency", "Liveness", "Behavioral Signals"],
            "timeline_narrative": [],
            "summary": "The video passed all prototype verification layers with no critical findings.",
            "limitations": [
                "DeepShield uses prototype heuristic analysis, not a trained deepfake detection model.",
                "Results are indicative only."
            ],
        },
    },
    "suspicious": {
        "trust_score": 54.2,
        "risk_level": "suspicious",
        "module_scores": {
            "face": {"label": "Face Authenticity", "score": 65.0, "confidence": 0.70, "risk": "medium",
                     "evidence": ["Moderate facial landmark instability in 18% of transitions."],
                     "timestamps": [4.2, 8.1], "weight": 25},
            "audio": {"label": "Audio Authenticity", "score": 58.0, "confidence": 0.60, "risk": "medium",
                      "evidence": ["Audio energy drops detected in 22% of frames. Possible audio substitution."],
                      "timestamps": [13.5], "weight": 15},
            "lipsync": {"label": "Lip-Speech Consistency", "score": 41.0, "confidence": 0.65, "risk": "medium",
                        "evidence": ["Weak lip-speech correlation (r=0.38). Audio may not match this face.",
                                     "Audio-lip timing offset of +320ms exceeds natural sync range."],
                        "timestamps": [4.0, 11.0], "weight": 20},
            "temporal": {"label": "Temporal Consistency", "score": 63.0, "confidence": 0.75, "risk": "medium",
                         "evidence": ["Abrupt visual transitions at: 8.1s."],
                         "timestamps": [8.1], "weight": 15},
            "liveness": {"label": "Liveness", "score": 55.0, "confidence": 0.55, "risk": "medium",
                         "evidence": ["Limited head movement detected. Blinks detected: 1."],
                         "timestamps": [], "weight": 15},
            "behavior": {"label": "Behavioral Signals", "score": 48.0, "confidence": 0.50, "risk": "medium",
                         "evidence": ["Sudden head pose changes in 15% of transitions."],
                         "timestamps": [8.1], "weight": 10},
        },
        "evidence": [
            {"module": "Lip-Speech Consistency", "text": "Weak lip-speech correlation (r=0.38). Audio may not match this face."},
            {"module": "Audio Authenticity", "text": "Audio energy drops detected in 22% of frames."},
            {"module": "Temporal Consistency", "text": "Abrupt visual transitions at: 8.1s."},
        ],
        "timeline": [
            {"time": 4.0, "module": "Lip-Speech Consistency", "risk": "medium"},
            {"time": 8.1, "module": "Temporal Consistency", "risk": "medium"},
            {"time": 13.5, "module": "Audio Authenticity", "risk": "medium"},
        ],
        "explanation": {
            "intro": "DeepShield detected moderate anomalies across one or more verification channels.",
            "findings": [
                "Lip-Speech Consistency: Weak lip-speech correlation (r=0.38) — audio may not come from this face.",
                "Audio Authenticity: Audio energy drops detected in 22% of frames — possible audio substitution.",
                "Temporal Consistency: Abrupt visual transition detected at 8.1s.",
            ],
            "passing_modules": ["Face Authenticity"],
            "timeline_narrative": [
                "At 00:04.00 — Lip-Speech Consistency flagged an anomaly.",
                "At 00:08.10 — Temporal Consistency flagged an anomaly.",
                "At 00:13.50 — Audio Authenticity flagged an anomaly.",
            ],
            "summary": "Some verification channels raised concerns. Manual review is recommended.",
            "limitations": ["DeepShield uses prototype heuristic analysis, not a trained deepfake detection model."],
        },
    },
    "high_risk": {
        "trust_score": 22.8,
        "risk_level": "high",
        "module_scores": {
            "face": {"label": "Face Authenticity", "score": 28.0, "confidence": 0.80, "risk": "high",
                     "evidence": ["High facial landmark instability in 45% of transitions.",
                                  "Face detected in only 71% of sampled frames.",
                                  "Significant facial inconsistencies at 3 timestamps."],
                     "timestamps": [2.1, 5.8, 9.3], "weight": 25},
            "audio": {"label": "Audio Authenticity", "score": 22.0, "confidence": 0.75, "risk": "high",
                      "evidence": ["Very low MFCC variance (12.3) — audio may be synthetic or repetitive.",
                                   "Abnormal energy drops in 38% of audio frames."],
                      "timestamps": [3.5, 7.2, 11.8], "weight": 15},
            "lipsync": {"label": "Lip-Speech Consistency", "score": 18.0, "confidence": 0.75, "risk": "high",
                        "evidence": ["Very weak lip-speech correlation (r=0.11).",
                                     "Speech bursts do not align with mouth-open intervals — likely audio substitution.",
                                     "Audio-lip timing offset +580ms far outside natural range."],
                        "timestamps": [2.0, 5.5, 9.0, 12.5], "weight": 20},
            "temporal": {"label": "Temporal Consistency", "score": 25.0, "confidence": 0.85, "risk": "high",
                         "evidence": ["High temporal inconsistency: 38% of frame transitions are abnormal.",
                                      "Abrupt visual transitions at: 5.8s, 9.3s, 11.9s."],
                         "timestamps": [5.8, 9.3, 11.9], "weight": 15},
            "liveness": {"label": "Liveness", "score": 18.0, "confidence": 0.70, "risk": "high",
                         "evidence": ["Face appears unnaturally static.",
                                      "No blink-like eye movement detected. [Prototype blink proxy]"],
                         "timestamps": [], "weight": 15},
            "behavior": {"label": "Behavioral Signals", "score": 22.0, "confidence": 0.65, "risk": "high",
                         "evidence": ["Sudden head pose changes in 42% of transitions.",
                                      "Face position appears unnaturally fixed."],
                         "timestamps": [2.1, 5.8], "weight": 10},
        },
        "evidence": [
            {"module": "Face Authenticity", "text": "High facial landmark instability in 45% of transitions."},
            {"module": "Lip-Speech Consistency", "text": "Very weak lip-speech correlation (r=0.11)."},
            {"module": "Audio Authenticity", "text": "Very low MFCC variance — audio may be synthetic."},
            {"module": "Temporal Consistency", "text": "38% of frame transitions are abnormal."},
            {"module": "Liveness", "text": "Face appears unnaturally static. No blink detected."},
        ],
        "timeline": [
            {"time": 2.1, "module": "Face Authenticity", "risk": "high"},
            {"time": 3.5, "module": "Audio Authenticity", "risk": "high"},
            {"time": 5.8, "module": "Temporal Consistency", "risk": "high"},
            {"time": 9.0, "module": "Lip-Speech Consistency", "risk": "high"},
            {"time": 9.3, "module": "Face Authenticity", "risk": "high"},
            {"time": 11.8, "module": "Audio Authenticity", "risk": "high"},
        ],
        "explanation": {
            "intro": "DeepShield detected significant anomalies that may indicate media manipulation or deepfake generation.",
            "findings": [
                "Face Authenticity: High facial landmark instability in 45% of transitions.",
                "Lip-Speech Consistency: Very weak lip-speech correlation (r=0.11) — audio does not match lip movement.",
                "Audio Authenticity: Very low MFCC variance — audio may be synthetic.",
                "Temporal Consistency: 38% of frame transitions show abnormal changes.",
                "Liveness: Face appears unnaturally static with no detected blinks.",
            ],
            "passing_modules": [],
            "timeline_narrative": [
                "At 00:02.10 — Face Authenticity flagged an anomaly.",
                "At 00:03.50 — Audio Authenticity flagged an anomaly.",
                "At 00:05.80 — Temporal Consistency flagged an anomaly.",
                "At 00:09.00 — Lip-Speech Consistency flagged an anomaly.",
            ],
            "summary": "Multiple independent channels raised high-risk flags. This video warrants careful scrutiny.",
            "limitations": [
                "DeepShield uses prototype heuristic analysis, not a trained deepfake detection model.",
                "A high risk score does not prove manipulation — it is a prototype indicator only.",
            ],
        },
    },
}


@app.get("/api/demo/{scenario}")
async def demo_result(scenario: str):
    """Return a pre-computed demo result, clearly labeled as DEMO/SIMULATED."""
    if scenario not in DEMO_SCENARIOS:
        raise HTTPException(404, f"Demo scenario must be one of: {list(DEMO_SCENARIOS.keys())}")
    
    data = DEMO_SCENARIOS[scenario].copy()
    data["is_demo"] = True
    data["demo_note"] = DEMO_NOTE
    data["analysis_id"] = f"demo-{scenario}-{uuid.uuid4().hex[:6]}"
    data["filename"] = f"demo_{scenario}.mp4"
    data["video_metadata"] = {"fps": 25, "frame_count": 375, "duration": 15.0, "width": 1280, "height": 720}
    data["note"] = PROTOTYPE_NOTE
    
    # Store in DB for reference
    analysis_id = await create_analysis(data["filename"], 0, is_demo=True)
    await update_analysis(analysis_id, "complete", data)
    data["analysis_id"] = analysis_id
    
    return data
