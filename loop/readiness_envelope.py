"""Standard readiness evidence envelope — never silent human←machine substitution."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


def _now() -> datetime:
    return datetime.now(timezone.utc)


def build_readiness_envelope(
    *,
    color: str,
    score: float | None,
    confidence: float,
    action: str,
    reason: str,
    human: dict[str, Any],
    machine: dict[str, Any],
    interaction: dict[str, Any] | None = None,
    governance: dict[str, Any] | None = None,
    missing_evidence: list[str] | None = None,
    measured_at: str | None = None,
    ttl_hours: float | None = None,
    vitality_gate: dict[str, Any] | None = None,
    decision_class: str | None = None,
    evidence_quality: float | None = None,
    energy: dict[str, Any] | None = None,
    shadow: dict[str, Any] | None = None,
    intelligence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Canonical readiness schema (Priority 3).

    substrates.*.evidence_type: none | self_report | telemetry | inferred | sensor
    recommendation: PROCEED | SIMPLIFY | HOLD | EVIDENCE_NEEDED | INJECT_NEEDED
    """
    now = _now()
    measured = measured_at or now.isoformat()
    expires = None
    if ttl_hours is not None and ttl_hours < 900:
        try:
            base = datetime.fromisoformat(str(measured).replace("Z", "+00:00"))
            # expires = when data becomes stale (48h policy) from measure time
            expires = (base + timedelta(hours=48)).isoformat()
        except Exception:
            expires = (
                now + timedelta(hours=max(0.0, 48 - float(ttl_hours)))
            ).isoformat()

    rec = action
    if rec == "INJECT_NEEDED":
        rec = "EVIDENCE_NEEDED"
    if color == "STALE" and rec not in ("HOLD", "EVIDENCE_NEEDED"):
        rec = "EVIDENCE_NEEDED"

    missing = list(missing_evidence or [])
    if human.get("state") == "UNKNOWN" or human.get("evidence_type") in ("none", None):
        if "human_state" not in missing:
            missing.append("human_state")

    env = {
        "schema": "well_readiness_envelope.v1",
        "readiness": {
            "state": color
            if color in ("GREEN", "YELLOW", "RED", "STALE", "UNKNOWN")
            else "UNKNOWN",
            "score": score,
            "confidence": round(float(confidence), 3),
            "measured_at": measured,
            "expires_at": expires,
            "ttl_hours": ttl_hours,
            "substrates": {
                "human": {
                    "state": human.get("state", "UNKNOWN"),
                    "evidence_type": human.get("evidence_type", "none"),
                    "source": human.get("source"),
                    "note": human.get("note"),
                },
                "machine": {
                    "state": machine.get("state", "UNKNOWN"),
                    "evidence_type": machine.get("evidence_type", "none"),
                    "source": machine.get("source"),
                },
                "interaction": (
                    interaction or {"state": "UNKNOWN", "evidence_type": "none"}
                ),
                "governance": (
                    governance or {"state": "UNKNOWN", "evidence_type": "none"}
                ),
            },
            "missing_evidence": missing,
            "recommendation": rec,
            "reason": reason,
            "decision_class": decision_class,
            "evidence_quality": evidence_quality
            if evidence_quality is not None
            else round(float(confidence), 3),
            "boundaries": {
                "diagnostic": False,
                "authority": "advisory_only",
                "final_judge": "ARIF",
                "medical_boundary": "NON_DIAGNOSTIC",
            },
            "vitality_gate": vitality_gate,
            "thermodynamic": {
                "energy": energy or {"state": "UNKNOWN", "evidence_type": "none"},
                "shadow": shadow or {"state": "UNKNOWN", "evidence_type": "none"},
                "intelligence": intelligence
                or {"state": "UNKNOWN", "evidence_type": "none"},
            },
        },
        "canonical_tool": "well_validate_vitality",
        "legacy_alias": "well_readiness",
        "w0": "OPERATOR_VETO_INTACT",
    }
    return env


def map_gate_to_substrates(
    gate: dict[str, Any],
    state: dict[str, Any],
    energy: dict[str, Any] | None = None,
    shadow: dict[str, Any] | None = None,
    intelligence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build human/machine/interaction/governance substrate blocks from vitality_gate.

    Optionally accepts thermodynamic-APEX signals (energy, shadow, intelligence)
    from well_measure_gradient, well_dark_geometry_mirror, well_reflect_intelligence, etc.
    These are passed through to the readiness envelope as the thermodynamic block.
    """
    h = gate.get("H_WELL") or {}
    m = gate.get("M_WELL") or {}
    c = gate.get("C_WELL") or {}
    g = gate.get("G_WELL") or {}
    truth = str(state.get("truth_status", "")).upper()

    if h.get("state") == "UNKNOWN":
        h_type, h_state = "none", "UNKNOWN"
    elif (
        "OPERATOR" in truth
        or "SELF" in truth
        or "self_report" in str(h.get("note", "")).lower()
    ):
        h_type, h_state = "self_report", h.get("state", "UNKNOWN")
    else:
        h_type, h_state = "inferred", h.get("state", "UNKNOWN")

    m_type = "telemetry" if m.get("rank", 0) > 0 else "none"
    return {
        "human": {
            "state": h_state,
            "evidence_type": h_type,
            "source": h.get("source"),
            "note": h.get("note") or h.get("evidence"),
        },
        "machine": {
            "state": m.get("state", "UNKNOWN"),
            "evidence_type": m_type,
            "source": m.get("source"),
        },
        "interaction": {
            "state": c.get("state", "UNKNOWN"),
            "evidence_type": "inferred",
            "source": c.get("source"),
        },
        "governance": {
            "state": g.get("state", "UNKNOWN"),
            "evidence_type": "observed",
            "source": g.get("source"),
        },
        "thermodynamic": {
            "energy": energy or {"state": "UNKNOWN", "evidence_type": "none"},
            "shadow": shadow or {"state": "UNKNOWN", "evidence_type": "none"},
            "intelligence": intelligence
            or {"state": "UNKNOWN", "evidence_type": "none"},
        },
    }
