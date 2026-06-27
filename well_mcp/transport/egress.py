"""well_mcp.transport.egress — Stage 5 of the 5-stage reaction loop.

EGRESS: assemble final WellStamp, emit to caller. NEVER write vault
(vault is arifOS responsibility). NEVER trigger downstream actions
(handoff is informational only).

Authority: REFLECT_ONLY.
"""

from __future__ import annotations

from typing import Any, Dict


def stamp_egress(judged_stamp: Dict[str, Any]) -> Dict[str, Any]:
    """Stage 5 — EGRESS.

    Args:
        judged_stamp: output of stamp_judge()

    Returns:
        WellStamp.final with all stages' outputs assembled, ready
        for sovereign observation.

    Cost: < 5 ms.
    """
    final = dict(judged_stamp)
    final.update(
        {
            "stage": "egress",
            "stage_status": "PASS",
            "loop_trace": ["ingress", "encode", "metabolize", "judge", "egress"],
        }
    )

    # Surface ready_to_observe flag (always true — sovereignty is invariant).
    final["ready_to_observe"] = True

    # Surface loop_complete flag.
    final["loop_complete"] = True

    # Note: WELL NEVER writes vault, NEVER triggers downstream.
    # These are constitutional boundaries enforced by absence.

    return final
