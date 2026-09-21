"""
DeepShield Backend Tests
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from database import init_db
from services.fusion_engine import fuse_results, classify_risk
from services.explanation_engine import generate_explanation
from config import settings


@pytest.fixture(scope="session", autouse=True)
def initialize_db():
    """Initialize DB tables before any tests (startup event doesn't fire in TestClient)."""
    asyncio.get_event_loop().run_until_complete(init_db())


client = TestClient(app)


# ── Health ──────────────────────────────────────

def test_health_endpoint():
    r = client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "version" in data


# ── Demo mode ────────────────────────────────────

def test_demo_genuine():
    r = client.get("/api/demo/genuine")
    assert r.status_code == 200
    data = r.json()
    assert data["is_demo"] is True
    assert data["trust_score"] >= 70
    assert data["risk_level"] == "low"

def test_demo_suspicious():
    r = client.get("/api/demo/suspicious")
    assert r.status_code == 200
    data = r.json()
    assert data["is_demo"] is True
    assert 40 <= data["trust_score"] < 70
    assert data["risk_level"] == "suspicious"

def test_demo_high_risk():
    r = client.get("/api/demo/high_risk")
    assert r.status_code == 200
    data = r.json()
    assert data["is_demo"] is True
    assert data["trust_score"] < 40
    assert data["risk_level"] == "high"

def test_demo_invalid_scenario():
    r = client.get("/api/demo/fake_scenario")
    assert r.status_code == 404


# ── File validation ──────────────────────────────

def test_upload_no_file():
    r = client.post("/api/analyze")
    assert r.status_code == 422

def test_upload_invalid_extension(tmp_path):
    fake_file = tmp_path / "test.txt"
    fake_file.write_bytes(b"not a video")
    with open(fake_file, "rb") as f:
        r = client.post("/api/analyze", files={"file": ("test.txt", f, "text/plain")})
    assert r.status_code == 400


# ── Fusion engine ────────────────────────────────

def _make_module_result(score: float, confidence: float = 0.8) -> dict:
    risk = "low" if score >= 70 else ("medium" if score >= 40 else "high")
    return {"score": score, "confidence": confidence, "risk": risk, "evidence": [], "timestamps": []}

def test_fusion_all_low_risk():
    results = {k: _make_module_result(85.0) for k in ["face", "audio", "lipsync", "temporal", "liveness", "behavior"]}
    fused = fuse_results(results)
    assert fused["trust_score"] >= 70
    assert fused["risk_level"] == "low"

def test_fusion_all_high_risk():
    results = {k: _make_module_result(20.0) for k in ["face", "audio", "lipsync", "temporal", "liveness", "behavior"]}
    fused = fuse_results(results)
    assert fused["trust_score"] < 40
    assert fused["risk_level"] == "high"

def test_fusion_mixed():
    results = {
        "face": _make_module_result(80.0),
        "audio": _make_module_result(30.0),
        "lipsync": _make_module_result(45.0),
        "temporal": _make_module_result(75.0),
        "liveness": _make_module_result(60.0),
        "behavior": _make_module_result(70.0),
    }
    fused = fuse_results(results)
    assert 0 <= fused["trust_score"] <= 100
    assert fused["risk_level"] in ("low", "suspicious", "high")

def test_fusion_empty_results():
    fused = fuse_results({})
    assert fused["trust_score"] == 50.0


# ── Risk classification ──────────────────────────

def test_classify_risk_low():
    assert classify_risk(85) == "low"
    assert classify_risk(70) == "low"

def test_classify_risk_suspicious():
    assert classify_risk(69) == "suspicious"
    assert classify_risk(40) == "suspicious"

def test_classify_risk_high():
    assert classify_risk(39) == "high"
    assert classify_risk(0) == "high"


# ── Explainability ───────────────────────────────

def test_explanation_generated():
    fusion = {
        "trust_score": 55.0,
        "risk_level": "suspicious",
        "module_scores": {
            "face": {"label": "Face Authenticity", "score": 60.0, "risk": "medium"}
        },
        "evidence": [{"module": "Face Authenticity", "text": "Some anomaly detected."}],
        "timeline": [],
    }
    explanation = generate_explanation(fusion)
    assert "intro" in explanation
    assert len(explanation["findings"]) > 0
    assert "limitations" in explanation

def test_explanation_no_false_findings():
    """Explanations must not invent findings for clean analyses."""
    fusion = {
        "trust_score": 88.0,
        "risk_level": "low",
        "module_scores": {},
        "evidence": [],
        "timeline": [],
    }
    explanation = generate_explanation(fusion)
    assert explanation["findings"] == []
