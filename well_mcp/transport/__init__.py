"""well_mcp.transport — 5-stage reaction loop registry.

Stages:
  1. ingress    → stamp_ingress()
  2. encode     → stamp_encode()
  3. metabolize → stamp_metabolize()
  4. judge      → stamp_judge()
  5. egress     → stamp_egress()

Each stage produces a partial WellStamp. The full stamp is assembled
at stage 5 (egress).

Authority: REFLECT_ONLY. Never writes vault. Never triggers downstream.
"""

from __future__ import annotations

from typing import Any, List

from . import ingress, encode, metabolize, judge, egress

# Re-export stage functions so callers can `from well_mcp.transport import stamp_ingress`.
stamp_ingress = ingress.stamp_ingress
stamp_encode = encode.stamp_encode
stamp_metabolize = metabolize.stamp_metabolize
stamp_judge = judge.stamp_judge
stamp_egress = egress.stamp_egress

STAGE_MODULES = [ingress, encode, metabolize, judge, egress]

STAGE_NAMES = ["ingress", "encode", "metabolize", "judge", "egress"]


def run_loop(
    payload: Any,
    *,
    substrate_canon: str = "human",
    decision_class: str = "C1",
    actor_id: str = "",
    source_organ: str = "well",
    source_tool: str = "",
    freshness_raw_hours: Any = None,
    human_state: float = 0.70,
    machine_state: float = 0.70,
    governance_state: float = 0.85,
    e1: float = 0.30,
    e2: float = 0.20,
    e3: float = 0.20,
    e4: float = 0.30,
    cognitive_entropy_rate: float = 0.30,
    arifOS_verdict: str = "PENDING",
    arifOS_attested: bool = False,
    handoff_candidates: Any = None,
    consent_verified: bool = False,
    coercion_signals: Any = None,
    reductionism_risk: float = 0.0,
    dignity_preservation: float = 1.0,
) -> Any:
    """Run the full 5-stage loop and return the final WellStamp.

    Convenience helper. Each stage is also exposed individually via
    `stage.<name>.stamp_<stage>(...)`.

    Authority: REFLECT_ONLY. Never mutates state.
    """
    # 1. INGEST
    s1 = ingress.stamp_ingress(
        payload=payload,
        source_organ=source_organ,
        source_tool=source_tool,
        actor_id=actor_id,
        freshness_raw_hours=freshness_raw_hours,
    )

    # Inject dignity-floor inputs (so encode can check them).
    s1["consent_verified"] = consent_verified
    s1["coercion_signals"] = coercion_signals or []
    s1["reductionism_risk"] = reductionism_risk
    s1["dignity_preservation"] = dignity_preservation

    # 2. ENCODE
    s2 = encode.stamp_encode(
        s1,
        substrate_canon=substrate_canon,
        decision_class=decision_class,
        handoff_candidates=handoff_candidates or [],
    )

    # 3. METABOLIZE
    s3 = metabolize.stamp_metabolize(
        s2,
        human_state=human_state,
        machine_state=machine_state,
        governance_state=governance_state,
        e1=e1,
        e2=e2,
        e3=e3,
        e4=e4,
        cognitive_entropy_rate=cognitive_entropy_rate,
    )

    # 4. JUDGE
    s4 = judge.stamp_judge(
        s3,
        arifOS_verdict=arifOS_verdict,
        arifOS_attested=arifOS_attested,
    )

    # 5. EGRESS
    s5 = egress.stamp_egress(s4)
    return s5


def register_transport(mcp: Any) -> List[str]:
    """Register transport stage helpers with FastMCP.

    Currently registers metadata as a single diagnostic resource.
    Each stage function is exposed as a Python function for direct
    invocation; MCP tool surface is reserved for canonical well_*
    tools in server.py.

    Returns list of URIs registered.
    """

    @mcp.resource("well://transport/stages")
    def transport_stages() -> str:
        """Canonical 5-stage loop, in human-readable form."""
        return (
            "well_mcp.transport — 5-stage reaction loop\n"
            "==========================================\n\n"
            "  1. ingress    stamp_ingress(payload)        → WellStamp.partial\n"
            "  2. encode     stamp_encode(partial, ...)    → WellStamp.encoded\n"
            "  3. metabolize stamp_metabolize(encoded, ...)→ WellStamp.metabolized\n"
            "  4. judge      stamp_judge(metabolized, ...) → WellStamp.judged\n"
            "  5. egress     stamp_egress(judged)          → WellStamp.final\n\n"
            "run_loop(payload, **kwargs) → runs all 5 stages.\n"
            "Each stage is independently importable for testing.\n"
            "Authority: REFLECT_ONLY. Never writes vault.\n"
        )

    return ["well://transport/stages"]


__all__ = [
    "register_transport",
    "STAGE_MODULES",
    "STAGE_NAMES",
    "run_loop",
    "ingress",
    "encode",
    "metabolize",
    "judge",
    "egress",
]
