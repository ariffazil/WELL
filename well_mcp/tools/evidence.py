"""
WELL Evidence Baseline — P0 Truth Enforcement.

When a tool has no real telemetry, sensor data, or external evidence,
it MUST return UNKNOWN, not STABLE / READY / LIVE / 0.85.

This module provides the canonical baseline for all WELL tools.
DITEMPA BUKAN DIBERI — Forged, Not Given.

P1 CONFORMANCE (2026-07-26): Every response now carries ClaimState,
WitnessType, and OrganType — the three semantic anchors that make
WELL the reference organ for metabolic conformance. Other organs
(WEALTH, GEOX) inherit this pattern.

Sovereign: Muhammad Arif bin Fazil (F13)
Date: 2026-07-21 / Conformance: 2026-07-26
License: AGPL-3.0
"""

from typing import Any

from ..types import ClaimState, OrganType, WitnessType

# ── Canonical UNKNOWN baseline ──────────────────────────────────────────────
# Every field that was previously hardcoded is now explicitly UNKNOWN.
# Tools MAY override individual fields when they have real evidence.
# Tools MUST NOT override the baseline to claim confidence without evidence.

UNKNOWN_BASELINE: dict[str, Any] = {
    "verdict": "UNKNOWN",
    "confidence": None,  # None = no evidence at all; 0.0 = evidence says "no signal"
    "truth_class": "STALE",  # STALE = no live telemetry; LIVE = real-time sensor data flowing
    "evidence_label": "NONE",  # NONE = no evidence; OBS/DER/INT when evidence exists
    "missing_evidence": [
        "no_telemetry",
        "no_sensor_data",
        "no_self_report",
        "no_external_verification",
    ],
    "evidence_age_hours": None,
    "friction_score": None,
    "cost_estimate": None,
    "reversibility_class": "UNKNOWN",
    "novelty_tags": [],
    # P1 conformance anchors
    "_well_conformance": {
        "claim_state": ClaimState.HOLD.value,
        "witness_type": WitnessType.UNKNOWN.value,
        "organ_type": OrganType.H_WELL.value,
    },
}


def build_unknown_result(
    tool_name: str,
    overrides: dict[str, Any] | None = None,
    missing: list[str] | None = None,
    note: str | None = None,
    claim_state: ClaimState = ClaimState.HOLD,
    witness_type: WitnessType = WitnessType.UNKNOWN,
    organ_type: OrganType | None = None,
) -> dict[str, Any]:
    """Build a WELL result dict from the UNKNOWN baseline.

    Args:
        tool_name: Name of the calling tool (for provenance)
        overrides: Fields to override on the baseline (e.g., when some evidence exists)
        missing: Specific evidence gaps for this tool call
        note: Human-readable note explaining why UNKNOWN
        claim_state: Epistemic state (default HOLD — no evidence)
        witness_type: Evidence source (default UNKNOWN)
        organ_type: Organ classification (auto-detected from tool_name if None)

    Returns:
        A dict safe to return from any WELL tool, with P1 conformance.
    """
    result = dict(UNKNOWN_BASELINE)  # shallow copy
    result["tool"] = tool_name

    # P1 conformance — override baseline defaults
    ot = organ_type or _infer_organ_type(tool_name)
    result["_well_conformance"] = {
        "claim_state": claim_state.value,
        "witness_type": witness_type.value,
        "organ_type": ot.value,
    }

    if missing:
        result["missing_evidence"] = missing
    if note:
        result["note"] = note
    if overrides:
        result.update(overrides)
    return result


def _infer_organ_type(tool_name: str) -> OrganType:
    """Infer organ type from tool name prefix."""
    if (
        tool_name.startswith("well_assess_homeostasis")
        or tool_name.startswith("well_validate_vitality")
        or tool_name.startswith("well_guard_dignity")
        or tool_name.startswith("well_assess_livelihood")
        or tool_name.startswith("well_assess_sovereign_entropy")
        or tool_name.startswith("well_medical_boundary")
        or tool_name.startswith("well_classify_state")
        or tool_name.startswith("well_dark_geometry")
        or tool_name.startswith("well_sabar")
        or tool_name.startswith("well_trust")
        or tool_name.startswith("well_niat")
        or tool_name.startswith("well_correction")
    ):
        return OrganType.H_WELL
    if tool_name.startswith("well_assess_reliability") or tool_name.startswith(
        "well_check_repair"
    ):
        return OrganType.M_WELL
    if (
        tool_name.startswith("well_assess_metabolism")
        or tool_name.startswith("well_compute_metabolic")
        or tool_name.startswith("well_trace_lineage")
        or tool_name.startswith("well_measure_gradient")
    ):
        return OrganType.C_WELL
    if tool_name.startswith("well_classify_substrate") or tool_name.startswith(
        "well_detect_boundary"
    ):
        return OrganType.G_WELL
    if (
        tool_name.startswith("well_attest")
        or tool_name.startswith("well_handoff")
        or tool_name.startswith("well_registry")
        or tool_name.startswith("well_signal")
        or tool_name.startswith("well_system")
    ):
        return OrganType.FEDERATION
    return OrganType.H_WELL  # default
