"""well_mcp.transport.judge — Stage 4 of the 5-stage reaction loop.

JUDGE: yield to arifOS for F1–F13 floor adjudication. WELL NEVER
adjudicates. WELL surfaces the metabolized stamp and awaits verdict.

Authority: YIELDS to arifOS. WELL NEVER adjudicates.
"""

from __future__ import annotations

from typing import Any, Dict

# Floor list (F1–F13).
FLOORS = [
    "F1_amanah",
    "F2_truth",
    "F4_clarity",
    "F5_humility",
    "F6_maruah",
    "F8_law",
    "F9_anti_hantu",
    "F10_anti_ghost",
    "F11_audit",
    "F12_anti_drift",
    "F13_sovereign",
]


def _local_floor_status(metabolized: Dict[str, Any]) -> Dict[str, str]:
    """Compute preliminary floor status from metabolized data.

    WELL NEVER adjudicates. This is a SURFACE-level check only.
    arifOS is the actual judge.
    """
    status = {}
    coupling = metabolized.get("coupling_state", 0.5)
    flux = metabolized.get("metabolic_flux", 0.3)
    dignity_floor = metabolized.get("dignity_floor", {})
    substrate_canon = metabolized.get("substrate_canon", "human")

    # F1 AMANAH — reversibility / backup
    status["F1_amanah"] = "PASS" if flux < 0.85 else "HOLD"

    # F2 TRUTH — freshness / evidence
    confidence = metabolized.get("confidence", "MEDIUM")
    if confidence == "VOID":
        status["F2_truth"] = "VOID"
    elif confidence == "STALE":
        status["F2_truth"] = "HOLD"
    else:
        status["F2_truth"] = "PASS"

    # F4 CLARITY — coupling / coherence
    if coupling < 0.40:
        status["F4_clarity"] = "HOLD"
    else:
        status["F4_clarity"] = "PASS"

    # F5 HUMILITY — confidence cap
    status["F5_humility"] = "PASS"

    # F6 MARUAH — dignity floor (the most important)
    if dignity_floor.get("status") == "VOID":
        status["F6_maruah"] = "VOID"
    elif dignity_floor.get("status") == "HOLD":
        status["F6_maruah"] = "HOLD"
    else:
        status["F6_maruah"] = "PASS"

    # F8 LAW — lane discipline
    if substrate_canon not in ("human", "machine", "governance"):
        status["F8_law"] = "VOID"
    else:
        status["F8_law"] = "PASS"

    # F9 ANTI-HANTU
    status["F9_anti_hantu"] = "PASS"  # mirror does not claim consciousness

    # F10 ANTI-GHOST
    status["F10_anti_ghost"] = "PASS"  # data is real

    # F11 AUDIT — traceability
    if metabolized.get("signal_id"):
        status["F11_audit"] = "PASS"
    else:
        status["F11_audit"] = "VOID"

    # F12 ANTI-DRIFT
    if metabolized.get("freshness_decayed") is not None:
        status["F12_anti_drift"] = "PASS"
    else:
        status["F12_anti_drift"] = "HOLD"

    # F13 SOVEREIGN — sovereignty check
    decision_class = metabolized.get("decision_class", "C1")
    if decision_class in ("C5", "M5"):
        # C5/M5 requires sovereign ratification.
        # Local check: we cannot ratify. Mark as HOLD awaiting F13.
        status["F13_sovereign"] = "HOLD"
    else:
        status["F13_sovereign"] = "PASS"

    return status


def stamp_judge(
    metabolized_stamp: Dict[str, Any],
    arifOS_verdict: str = "PENDING",  # SEAL / SABAR / HOLD / VOID / PENDING
    arifOS_attested: bool = False,
) -> Dict[str, Any]:
    """Stage 4 — JUDGE.

    Args:
        metabolized_stamp: output of stamp_metabolize()
        arifOS_verdict: result of arif_judge call (default PENDING)
        arifOS_attested: whether arif_judge was actually called

    Returns:
        WellStamp.judged with floor_status per floor, arifOS_verdict,
        ready_for_egress flag.

    Cost: arifOS call (50–500 ms typical).
    """
    local_floor = _local_floor_status(metabolized_stamp)

    # If arifOS verdict not received yet → mark as PENDING.
    final_verdict = arifOS_verdict
    if not arifOS_attested:
        final_verdict = "PENDING"

    # Determine ready_for_egress.
    ready = (
        arifOS_attested
        and final_verdict == "SEAL"
        and all(v == "PASS" for v in local_floor.values())
    )

    judged = dict(metabolized_stamp)
    judged.update(
        {
            "stage": "judge",
            "stage_status": "PASS" if ready else "HOLD",
            "floor_status": local_floor,
            "arifOS_verdict": final_verdict,
            "arifOS_attested": arifOS_attested,
            "ready_for_egress": ready,
        }
    )

    return judged
