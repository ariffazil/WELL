"""well_mcp.transport — 5-stage reaction loop helpers (ingress → egress)."""

from __future__ import annotations

from typing import Any, Dict

from .encode import stamp_encode
from .egress import stamp_egress
from .ingress import stamp_ingress
from .judge import stamp_judge
from .metabolize import stamp_metabolize

STAGE_NAMES = ("ingress", "encode", "metabolize", "judge", "egress")


def run_loop(
    payload: Any,
    substrate_canon: str = "human",
    decision_class: str = "C2",
    actor_id: str = "",
    session_id: str = "",
    freshness_raw_hours: float | None = None,
    human_state: float = 0.70,
    machine_state: float = 0.70,
    governance_state: float = 0.85,
    consent_verified: bool = False,
    coercion_signals: list[str] | None = None,
    reductionism_risk: float = 0.0,
    dignity_preservation: float = 1.0,
    arifOS_verdict: str = "PENDING",
    arifOS_attested: bool = False,
    handoff_candidates: list[str] | None = None,
    e1: float = 0.30,
    e2: float = 0.20,
    e3: float = 0.20,
    e4: float = 0.30,
    cognitive_entropy_rate: float = 0.30,
) -> Dict[str, Any]:
    """Run the 5-stage reaction loop and return the egress stamp.

    This is a thin orchestrator that composes the five stamp_* helpers in
    order.  It exists so callers can invoke the loop with one call, but each
    individual stage is also independently usable.
    """
    ingress = stamp_ingress(
        payload=payload,
        actor_id=actor_id,
        freshness_raw_hours=freshness_raw_hours,
        consent_verified=consent_verified,
        coercion_signals=coercion_signals,
        reductionism_risk=reductionism_risk,
        dignity_preservation=dignity_preservation,
    )
    encoded = stamp_encode(
        ingress,
        substrate_canon=substrate_canon,
        decision_class=decision_class,
        handoff_candidates=handoff_candidates,
    )
    metabolized = stamp_metabolize(
        encoded,
        human_state=human_state,
        machine_state=machine_state,
        governance_state=governance_state,
        e1=e1,
        e2=e2,
        e3=e3,
        e4=e4,
        cognitive_entropy_rate=cognitive_entropy_rate,
    )
    judged = stamp_judge(
        metabolized,
        arifOS_verdict=arifOS_verdict,
        arifOS_attested=arifOS_attested,
    )
    return stamp_egress(judged)


__all__ = [
    "STAGE_NAMES",
    "run_loop",
    "stamp_ingress",
    "stamp_encode",
    "stamp_metabolize",
    "stamp_judge",
    "stamp_egress",
]
