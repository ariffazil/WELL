"""well_mcp.transport.encode — Stage 2 of the 5-stage reaction loop.

ENCODE: apply dignity floor first, map to substrate canon, compute
freshness decay, map to decision class, identify handoffs.

Authority: REFLECT_ONLY.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# Freshness decay thresholds (hours).
FRESHNESS_BANDS = [
    (12, "HIGH"),
    (24, "MEDIUM"),
    (72, "LOW"),
    (168, "STALE"),
]
FRESHNESS_VOID_HOURS = 168


def _confidence_for_age(age_hours: Optional[float]) -> str:
    if age_hours is None:
        return "MEDIUM"  # unknown → conservative
    if age_hours < 0:
        return "VOID"
    if age_hours > FRESHNESS_VOID_HOURS:
        return "VOID"
    for cap, label in FRESHNESS_BANDS:
        if age_hours <= cap:
            return label
    return "VOID"


def _dignity_floor_check(stamp: Dict[str, Any]) -> Dict[str, Any]:
    """Check the dignity floor. Returns a dict with status and reason."""
    consent = stamp.get("consent_verified", False)
    coercion = stamp.get("coercion_signals", [])
    reductionism = stamp.get("reductionism_risk", 0.0)
    dignity = stamp.get("dignity_preservation", 0.0)

    if not consent:
        return {"status": "VOID", "reason": "consent_verified is False"}
    if coercion:
        return {"status": "VOID", "reason": f"coercion_signals present: {coercion}"}
    if reductionism >= 0.30:
        return {
            "status": "HOLD",
            "reason": f"reductionism_risk >= 0.30 ({reductionism})",
        }
    if dignity < 0.70:
        return {"status": "HOLD", "reason": f"dignity_preservation < 0.70 ({dignity})"}
    return {"status": "PASS", "reason": "dignity floor satisfied"}


def stamp_encode(
    partial_stamp: Dict[str, Any],
    substrate_canon: str = "human",
    decision_class: str = "C1",
    handoff_candidates: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Stage 2 — ENCODE.

    Args:
        partial_stamp: output of stamp_ingress()
        substrate_canon: which canon applies ("human", "machine",
                         "governance")
        decision_class: C1–C5 (human) or M1–M5 (machine)
        handoff_candidates: list of organs to hand off to

    Returns:
        WellStamp.encoded dict with substrate_canon, freshness_decayed,
        confidence, decision_class, handoff_candidates, dignity_floor.

    Cost: < 10 ms typical.
    """
    # 1. Apply dignity floor FIRST (most important gate).
    dignity_floor = _dignity_floor_check(partial_stamp)

    # 2. Compute freshness decay.
    raw = partial_stamp.get("freshness_raw")
    confidence = _confidence_for_age(raw)

    # 3. Validate decision_class.
    valid_classes = {"C1", "C2", "C3", "C4", "C5", "M1", "M2", "M3", "M4", "M5"}
    if decision_class not in valid_classes:
        dignity_floor = {
            "status": "VOID",
            "reason": f"invalid decision_class: {decision_class}",
        }
        decision_class = "C1"  # default to safest

    encoded = dict(partial_stamp)
    encoded.update(
        {
            "stage": "encode",
            "stage_status": dignity_floor["status"],
            "substrate_canon": substrate_canon,
            "freshness_decayed": raw,
            "confidence": confidence,
            "decision_class": decision_class,
            "handoff_candidates": handoff_candidates or [],
            "dignity_floor": dignity_floor,
        }
    )

    # If dignity floor fails → downgrade to observation only.
    if dignity_floor["status"] != "PASS":
        encoded["decision_class"] = "C1"
        encoded["stage_status"] = dignity_floor["status"]
        encoded["dignity_leakage_advisory"] = dignity_floor["reason"]

    return encoded
