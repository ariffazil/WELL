"""
WELL MCP Transport Objects — Typed schemas for constitutional organ.

Domain Law: SUBSTRATE_LAW
Authority: REFLECT_ONLY — mirror, never judge

Sovereign: Muhammad Arif bin Fazil (F13)
Date: 2026-07-16
License: AGPL-3.0

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime


class SubstrateState(BaseModel):
    """Typed substrate state object."""

    substrate_class: Literal["HUMAN", "MACHINE", "INSTITUTIONAL", "COUPLED"]
    state: Literal["READY", "BELOW_BASELINE", "DEGRADED", "CRITICAL", "UNKNOWN"]
    confidence: float = Field(ge=0.0, le=1.0)
    truth_class: Literal["LIVE", "CACHED", "INFERRED"]
    evidence_label: Literal["OBS", "DER", "INT", "SPEC"]
    timestamp: datetime
    source: str


class VitalityGateResult(BaseModel):
    """Typed vitality gate result."""

    verdict: Literal["PROCEED", "REDUCE_LOAD", "RECOVER", "HOLD", "INSUFFICIENT_DATA"]
    h_well: SubstrateState
    m_well: SubstrateState
    g_well: SubstrateState
    c_well: SubstrateState
    weakest_substrate: str
    friction_score: float = Field(ge=0.0, le=1.0)
    cost_estimate: float = Field(ge=0.0)
    reversibility_class: Literal["REVERSIBLE", "IRREVERSIBLE"]
    novelty_tags: list[str]


class MetabolicFlux(BaseModel):
    """Typed metabolic flux object."""

    cognitive_entropy_rate: float
    machine_entropy: float
    unified_scalar: float = Field(ge=0.0, le=1.0)
    compulsory_reallocation: bool
    system_hold: bool
    truth_class: Literal["LIVE", "CACHED", "INFERRED"]


class ReplayReceipt(BaseModel):
    """Typed replay receipt for audit trail — canonical claim-state format."""

    tool: str
    timestamp: datetime
    session_id: str
    actor_id: str
    inputs: dict
    outputs: dict
    # Canonical metabolic progression (WELL: never emits SEAL/HOLD — arifOS adjudicates)
    claim_state: Literal["OBSERVED", "HYPOTHESIS", "QUALIFIED", "VERIFIED"] = "OBSERVED"
    witness_type: Literal["SENSOR", "CROSS_WITNESS", "HUMAN", "AI", "EARTH"] = "SENSOR"
    organ_type: Literal["WELL"] = "WELL"
    # Legacy provenance fields (retained for backward compatibility)
    truth_class: Literal["LIVE", "CACHED", "INFERRED"] = "LIVE"
    evidence_label: Literal["OBS", "DER", "INT", "SPEC"] = "OBS"
    # Metadata
    friction_score: float = 0.0
    cost_estimate: float = 0.0
    reversibility_class: Literal["REVERSIBLE", "IRREVERSIBLE"] = "REVERSIBLE"
    novelty_tags: list[str] = []
