"""
Cross-Modal Fusion Engine — DeepShield Core

Combines all module scores into a Joint Trust Score using configurable
weighted fusion. The score is computed from actual module outputs only.
No hardcoded final scores.

Default weights:
  Face Authenticity       25%
  Lip-Speech Sync         20%
  Audio Authenticity      15%
  Liveness                15%
  Temporal Consistency    15%
  Behavioral Signals      10%
"""
from config import settings, PROTOTYPE_NOTE

MODULE_KEYS = ["face", "lipsync", "audio", "liveness", "temporal", "behavior"]

MODULE_LABELS = {
    "face": "Face Authenticity",
    "audio": "Audio Authenticity",
    "lipsync": "Lip-Speech Consistency",
    "temporal": "Temporal Consistency",
    "liveness": "Liveness",
    "behavior": "Behavioral Signals",
}


def fuse_results(module_results: dict) -> dict:
    """
    Compute Joint Trust Score from individual module results.
    
    Args:
        module_results: dict mapping module key → standard result dict
    
    Returns:
        Fused result with trust_score, risk_level, module_scores, evidence, timeline
    """
    weights = settings.fusion_weights
    
    weighted_sum = 0.0
    total_weight = 0.0
    module_scores = {}
    all_evidence = []
    all_timestamps = []
    
    for key in MODULE_KEYS:
        result = module_results.get(key, {})
        if not result:
            continue
        
        score = float(result.get("score", 50.0))
        confidence = float(result.get("confidence", 0.5))
        weight = weights.get(key, 0.0)
        
        # Confidence-adjusted weight: low-confidence modules contribute less
        adj_weight = weight * confidence
        weighted_sum += score * adj_weight
        total_weight += adj_weight
        
        module_scores[key] = {
            "label": MODULE_LABELS.get(key, key.title()),
            "score": round(score, 1),
            "confidence": round(confidence, 2),
            "risk": result.get("risk", "medium"),
            "evidence": result.get("evidence", []),
            "timestamps": result.get("timestamps", []),
            "weight": round(weight * 100),
            "detail": result.get("detail", {}),
        }
        
        # Collect evidence from modules with notable findings
        for ev in result.get("evidence", []):
            if result.get("risk") in ("medium", "high"):
                all_evidence.append({"module": MODULE_LABELS.get(key, key), "text": ev})
        
        # Collect timeline events
        for ts in result.get("timestamps", []):
            all_timestamps.append({
                "time": round(ts, 2),
                "module": MODULE_LABELS.get(key, key),
                "risk": result.get("risk", "medium"),
            })
    
    # Compute final trust score
    if total_weight > 0:
        raw_score = weighted_sum / total_weight
    else:
        raw_score = 50.0
    
    trust_score = round(max(0, min(100, raw_score)), 1)
    
    # Classify risk
    if trust_score >= settings.low_risk_threshold:
        risk_level = "low"
    elif trust_score >= settings.suspicious_threshold:
        risk_level = "suspicious"
    else:
        risk_level = "high"
    
    # Sort timeline by time
    all_timestamps.sort(key=lambda x: x["time"])
    
    return {
        "trust_score": trust_score,
        "risk_level": risk_level,
        "module_scores": module_scores,
        "evidence": all_evidence,
        "timeline": all_timestamps,
        "weights_used": {k: round(v*100) for k, v in weights.items()},
        "note": PROTOTYPE_NOTE,
    }


def classify_risk(score: float) -> str:
    """Classify a raw score into a risk level."""
    if score >= settings.low_risk_threshold:
        return "low"
    elif score >= settings.suspicious_threshold:
        return "suspicious"
    return "high"
