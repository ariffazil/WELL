"""
well_mcp/types.py — Canonical WELL Response Types

ClaimState, WitnessType, OrganType — the three semantic anchors
that make WELL the reference organ for metabolic conformance.

Every WELL tool response MUST include these three fields.
Other organs (WEALTH, GEOX) will inherit this pattern.

Constitutional binding:
  F2 TRUTH:       claim_state declares epistemic status
  F3 TRI-WITNESS: witness_type declares evidence source
  F4 CLARITY:     organ_type prevents category errors

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from enum import Enum


class ClaimState(str, Enum):
    """Epistemic status of a WELL claim — F2 TRUTH bound.

    Every tool output must declare its state on this ladder:
      OBSERVED   → raw measurement, no interpretation
      HYPOTHESIS → testable claim, not yet verified
      QUALIFIED  → verified against evidence, uncertainties stated
      VERIFIED   → multi-witness confirmed, reproducible
      SEALED     → immutable, constitutionally anchored in VAULT999
      HOLD       → blocked — insufficient evidence, authority, or safety
    """

    OBSERVED = "OBSERVED"
    HYPOTHESIS = "HYPOTHESIS"
    QUALIFIED = "QUALIFIED"
    VERIFIED = "VERIFIED"
    SEALED = "SEALED"
    HOLD = "HOLD"


class WitnessType(str, Enum):
    """Evidence source for a claim — F3 TRI-WITNESS bound.

    Every tool output must declare which witness channels
    contributed to this claim:
      HUMAN       → sovereign/operator attestation
      AI          → model/computation-derived
      EARTH       → physical sensor/domain evidence
      HYBRID      → multiple channels combined
      UNKNOWN     → source cannot be determined
    """

    HUMAN = "HUMAN"
    AI = "AI"
    EARTH = "EARTH"
    HYBRID = "HYBRID"
    UNKNOWN = "UNKNOWN"


class OrganType(str, Enum):
    """Organ classification — F4 CLARITY bound.

    Every tool output must declare which organ domain it
    operates within, preventing category errors:
      H_WELL → human substrate / biological readiness
      M_WELL → machine reliability / tool health
      C_WELL → coupled human-machine risk
      G_WELL → governance coherence / boundary integrity
      FEDERATION → cross-organ bridge
    """

    H_WELL = "H_WELL"
    M_WELL = "M_WELL"
    C_WELL = "C_WELL"
    G_WELL = "G_WELL"
    FEDERATION = "FEDERATION"


# ── Conformance Wrapper ──────────────────────────────────────
def well_response(
    tool_name: str,
    organ_type: OrganType,
    claim_state: ClaimState,
    witness_type: WitnessType,
    data: dict,
    **extra,
) -> dict:
    """Wrap a WELL tool response with mandatory conformance fields.

    Returns a dict with guaranteed keys:
      _well_conformance: { claim_state, witness_type, organ_type }
      _tool: tool_name
      ...data
      ...extra

    Every WELL tool MUST use this wrapper or equivalent inline
    fields. No naked dict responses.
    """
    return {
        "_well_conformance": {
            "claim_state": claim_state.value,
            "witness_type": witness_type.value,
            "organ_type": organ_type.value,
        },
        "_tool": tool_name,
        **data,
        **extra,
    }
