"""
Explainability Engine — DeepShield

Generates human-readable explanations from actual analysis results.
Never generates explanations for signals that were not actually detected.
All explanations reference real computed values.
"""
from config import PROTOTYPE_NOTE


RISK_INTRO = {
    "low": "DeepShield's multi-layer analysis found no significant indicators of media manipulation.",
    "suspicious": "DeepShield detected moderate anomalies across one or more verification channels.",
    "high": "DeepShield detected significant anomalies that may indicate media manipulation or deepfake generation.",
}

RISK_SUMMARY = {
    "low": "The video passed all prototype verification layers with no critical findings. This is a positive indicator, though not a guarantee of authenticity.",
    "suspicious": "Some verification channels raised concerns. Manual review is recommended.",
    "high": "Multiple independent channels raised high-risk flags. This video warrants careful scrutiny.",
}


def generate_explanation(fusion_result: dict) -> dict:
    """
    Generate structured explanations from fused analysis results.
    Only references findings that were actually detected.
    """
    risk_level = fusion_result.get("risk_level", "suspicious")
    trust_score = fusion_result.get("trust_score", 50)
    module_scores = fusion_result.get("module_scores", {})
    evidence = fusion_result.get("evidence", [])
    timeline = fusion_result.get("timeline", [])
    
    # Introduction sentence
    intro = RISK_INTRO.get(risk_level, RISK_INTRO["suspicious"])
    
    # Build finding bullets from real evidence
    findings = []
    for ev in evidence:
        module = ev.get("module", "Analysis")
        text = ev.get("text", "")
        if text and len(text) > 10:
            findings.append(f"{module}: {text}")
    
    # Highlight passing modules
    passing = []
    for key, ms in module_scores.items():
        if ms.get("risk") == "low" and ms.get("score", 0) >= 70:
            passing.append(ms.get("label", key))
    
    # Build timeline narrative
    timeline_narrative = []
    for event in timeline[:5]:
        t = event.get("time", 0)
        minutes = int(t // 60)
        seconds = t % 60
        ts_str = f"{minutes:02d}:{seconds:05.2f}"
        module = event.get("module", "Analysis")
        timeline_narrative.append(f"At {ts_str} — {module} flagged an anomaly.")
    
    # Summary
    summary = RISK_SUMMARY.get(risk_level, RISK_SUMMARY["suspicious"])
    
    # Limitation disclaimer
    limitations = [
        "DeepShield uses prototype heuristic analysis, not a trained deepfake detection model.",
        "Thresholds are experimental and have not been validated on a labeled deepfake dataset.",
        "A low risk score does not guarantee media authenticity; a high risk score does not prove manipulation.",
        "This system should be used as a screening aid only — not as definitive evidence.",
    ]
    
    return {
        "intro": intro,
        "findings": findings,
        "passing_modules": passing,
        "timeline_narrative": timeline_narrative,
        "summary": summary,
        "limitations": limitations,
        "note": PROTOTYPE_NOTE,
    }
