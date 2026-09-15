"""
WELL MCP Replay Receipt Generator — Audit trail for constitutional organ.

Domain Law: SUBSTRATE_LAW
Authority: REFLECT_ONLY — mirror, never judge

Sovereign: Muhammad Arif bin Fazil (F13)
Date: 2026-07-16
License: AGPL-3.0

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from datetime import datetime
from typing import Any, Literal
import json

from ..transport.types import ReplayReceipt


def generate_replay_receipt(
    tool: str,
    session_id: str,
    actor_id: str,
    inputs: dict[str, Any],
    outputs: dict[str, Any],
    claim_state: Literal["OBSERVED", "HYPOTHESIS", "QUALIFIED", "VERIFIED"] = "OBSERVED",
    witness_type: Literal["SENSOR", "CROSS_WITNESS", "HUMAN", "AI", "EARTH"] = "SENSOR",
    organ_type: Literal["WELL"] = "WELL",
    truth_class: Literal["LIVE", "CACHED", "INFERRED"] = "LIVE",
    evidence_label: Literal["OBS", "DER", "INT", "SPEC"] = "OBS",
    friction_score: float = 0.0,
    cost_estimate: float = 0.0,
    reversibility_class: Literal["REVERSIBLE", "IRREVERSIBLE"] = "REVERSIBLE",
    novelty_tags: list[str] | None = None,
) -> ReplayReceipt:
    """Generate a typed replay receipt for audit trail."""
    return ReplayReceipt(
        tool=tool,
        timestamp=datetime.utcnow(),
        session_id=session_id,
        actor_id=actor_id,
        inputs=inputs,
        outputs=outputs,
        claim_state=claim_state,
        witness_type=witness_type,
        organ_type=organ_type,
        truth_class=truth_class,
        evidence_label=evidence_label,
        friction_score=friction_score,
        cost_estimate=cost_estimate,
        reversibility_class=reversibility_class,
        novelty_tags=novelty_tags or [],
    )


def receipt_to_json(receipt: ReplayReceipt) -> str:
    """Convert replay receipt to JSON string."""
    return receipt.model_dump_json(indent=2)


def receipt_to_dict(receipt: ReplayReceipt) -> dict[str, Any]:
    """Convert replay receipt to dictionary."""
    return receipt.model_dump()
