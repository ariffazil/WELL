"""
WELL Metabolic Contract Enricher — Phase 3 Adoption
═══════════════════════════════════════════════════════════════════════════════════

Wraps WELL tool outputs with MetabolicOutput envelope.
WELL is advisory-only (biological_substrate) — all outputs are recommendation_only.

Source: arifOS commit eb53b316.
adoption_status: PHASE_3

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any


# ── Contract metadata ──────────────────────────────────────────────────────────

SCHEMA_NAME = "MetabolicOutput"
SCHEMA_VERSION = "1.0.0"
SOURCE_COMMIT = "eb53b316"
ADOPTION_STATUS = "PHASE_3"

# Well-known contract hash — computed from canonical schema at schema creation
CONTRACT_HASH = ""  # Empty until computed at first import


def _compute_contract_hash() -> str:
    """Compute SHA256 of the source metabolic schema for audit trail."""
    try:
        from pathlib import Path

        schema_path = Path(__file__).parent / "schemas" / "metabolic.py"
        content = schema_path.read_text()
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    except Exception:
        return ""


CONTRACT_HASH = _compute_contract_hash()


# ── Verdict → ClaimState mapping ──────────────────────────────────────────────
# WELL verdicts: SEAL, PASS, PROVISIONAL, HOLD, WARN, VOID, UNKNOWN

_VERDICT_CLAIM_STATE_MAP = {
    "SEAL": "VERIFIED",
    "PASS": "VERIFIED",
    "PROVISIONAL": "QUALIFIED",
    "HOLD": "HOLD",
    "WARN": "HYPOTHESIS",
    "VOID": "HOLD",
    "UNKNOWN": "HYPOTHESIS",
}


def _verdict_to_claim_state(verdict: str | None) -> str:
    """Map WELL internal verdict to MetabolicOutput ClaimState."""
    if verdict is None:
        return "HYPOTHESIS"
    return _VERDICT_CLAIM_STATE_MAP.get(verdict.upper(), "HYPOTHESIS")


# ── Uncertainty from verdict ───────────────────────────────────────────────────

_UNCERTAINTY_MAP = {
    "SEAL": 0.05,
    "PASS": 0.05,
    "PROVISIONAL": 0.25,
    "HOLD": 0.50,
    "WARN": 0.75,
    "VOID": 0.90,
    "UNKNOWN": 0.50,
}


def _verdict_to_uncertainty(verdict: str | None) -> float:
    """Get omega_0 uncertainty from WELL verdict."""
    if verdict is None:
        return 0.50
    return _UNCERTAINTY_MAP.get(verdict.upper(), 0.50)


# ── Witness type per tool ──────────────────────────────────────────────────────

_WITNESS_TYPE_MAP = {
    "well_validate_vitality": "sensor",
    "well_assess_reliability": "sensor",
    "well_reflect_intelligence": "testimony",
}

# ── Model target per tool ──────────────────────────────────────────────────────

_MODEL_TARGET_MAP = {
    "well_validate_vitality": "Body",
    "well_assess_reliability": "System",
    "well_reflect_intelligence": "System",
}

# ── High-stakes escalation ─────────────────────────────────────────────────────
# WELL always requires_888_judge for:
#   - vitality validation (biological readiness)
#   - intelligence routing (lane/stage selection)
#   - coupled readiness (human-machine pair)


def _requires_888_judge(tool_name: str, verdict: str | None) -> bool:
    """Determine if this tool output requires 888_JUDGE escalation.

    WELL is advisory-only. High-stakes outputs must route to arifOS.
    """
    if tool_name == "well_validate_vitality":
        return True  # biological readiness always needs judgment
    if tool_name == "well_reflect_intelligence":
        return True  # lane/stage routing always needs judgment
    if tool_name == "well_assess_reliability":
        # Only escalate on HOLD or VOID verdicts
        return verdict in ("HOLD", "VOID", "UNKNOWN")
    return False


# ── Main builder ───────────────────────────────────────────────────────────────


def build_metabolic_output(
    tool_name: str,
    internal_result: dict[str, Any],
    session_id: str | None = None,
    constitution_hash: str = "",  # DEPRECATED — kept for backward compat
    domain_law: str = "SUBSTRATE_LAW",
    substrate_manifest_hash: str = "",
) -> dict[str, Any]:
    """
    Wrap a WELL tool output with MetabolicOutput envelope.

    Parameters
    ----------
    tool_name: Which WELL MCP tool generated this output.
    internal_result: Raw result from the internal well_* function
                     (before _to_federation_output wrapping).
    session_id: Governed session ID for audit binding.
    constitution_hash: DEPRECATED — use substrate_manifest_hash instead.
    domain_law: Domain law type (SUBSTRATE_LAW for WELL).
    substrate_manifest_hash: SHA-256 of WELL Substrate Manifest (identity anchor).

    Returns
    -------
    dict with top-level ``metabolic`` key containing MetabolicOutput fields,
    plus the federation ``observation``, ``uncertainty``, ``constraints``,
    and ``boundary_notice`` at the top level for backward compatibility.
    """
    # Import here to avoid circular import at runtime
    import importlib

    _to_federation_output = getattr(
        importlib.import_module("server"), "_to_federation_output"
    )

    # Wrap internal result in federation format
    federation_output: dict[str, Any] = _to_federation_output(
        internal_result, tool_name=tool_name
    )

    # Extract verdict from internal result BEFORE _to_federation_output strips Ω.
    # _omega_well_output structure: {ok, Ω: {verdict, stage, lane, mode}, data, ...}
    verdict = None
    if isinstance(internal_result, dict):
        omega = internal_result.get("Ω", {})
        if isinstance(omega, dict):
            verdict = omega.get("verdict")
        if verdict is None:
            verdict = internal_result.get("verdict")
    if verdict is None:
        verdict = federation_output.get("verdict", "UNKNOWN")

    # Compute claim_state
    claim_state = _verdict_to_claim_state(verdict)
    uncertainty = _verdict_to_uncertainty(verdict)
    witness_type = _WITNESS_TYPE_MAP.get(tool_name, "sensor")
    model_target = _MODEL_TARGET_MAP.get(tool_name, "Body")
    requires_888 = _requires_888_judge(tool_name, verdict)

    # Extract observation data
    observation = federation_output.get("observation", {})
    if isinstance(observation, dict):
        observation_data = {
            k: v
            for k, v in observation.items()
            if k not in ("ok", "Ω", "arifos", "aaa", "w0", "verdict", "error")
        }
    else:
        observation_data = {"raw": observation}

    # Timestamp
    timestamp_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Build MetabolicOutput fields
    metabolic = {
        # Identity
        "organ": "WELL",
        "tool_name": tool_name,
        "session_id": session_id,
        # Witness layer
        "witness_type": witness_type,
        "witness_status": "RAW",
        # Meaning layer
        "candidate_meanings": [],
        # Uncertainty
        "uncertainty": {
            "omega_0": uncertainty,
            "uncertainty_range": (
                max(0.0, uncertainty - 0.1),
                min(1.0, uncertainty + 0.1),
            ),
            "major_unknowns": [],
            "key_missing_evidence": [],
            "claim_too_certain_flag": False,
        },
        # Claim state
        "claim_state": claim_state,
        # Confidence
        "confidence_level": (
            "VERIFIED"
            if claim_state == "VERIFIED"
            else "HIGH"
            if claim_state == "QUALIFIED" and uncertainty < 0.3
            else "MODERATE"
            if claim_state == "QUALIFIED"
            else "LOW"
            if claim_state == "HYPOTHESIS"
            else "UNKNOWN"
        ),
        # Model
        "model_target": model_target,
        # Sovereignty boundary — WELL is always advisory
        "recommendation_only": True,
        "execution_authorized": False,
        "human_final_authority": "Arif",
        "requires_888_judge": requires_888,
        # Provenance
        "timestamp_utc": timestamp_utc,
        "constitution_hash": constitution_hash,  # DEPRECATED — backward compat
        "domain_law": domain_law,
        "substrate_manifest_hash": substrate_manifest_hash,
        # Contract metadata
        "schema_name": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "source_commit": SOURCE_COMMIT,
        "contract_hash": CONTRACT_HASH,
        "adoption_status": ADOPTION_STATUS,
    }

    # Cross-organ handoff
    if tool_name == "well_validate_vitality":
        metabolic["cross_organ_handoff"] = {
            "next_best_organ": "arifOS",
            "handoff_reason": "Biological readiness assessment requires arifOS 888_JUDGE for action",
            "handoff_payload": observation_data,
            "blocked_organs": [],
            "blocked_reason": "",
            "confidence_at_handoff": "MODERATE",
        }
    elif tool_name == "well_reflect_intelligence":
        metabolic["cross_organ_handoff"] = {
            "next_best_organ": "arifOS",
            "handoff_reason": "Lane/stage routing requires arifOS kernel for final dispatch",
            "handoff_payload": observation_data,
            "blocked_organs": [],
            "blocked_reason": "",
            "confidence_at_handoff": "MODERATE",
        }
    elif tool_name == "well_assess_reliability":
        metabolic["cross_organ_handoff"] = {
            "next_best_organ": "A-FORGE",
            "handoff_reason": "Machine/institution reliability assessment routes to A-FORGE for operational action",
            "handoff_payload": observation_data,
            "blocked_organs": [],
            "blocked_reason": "",
            "confidence_at_handoff": "MODERATE",
        }

    # Return: metabolic envelope + federation fields at top level
    return {
        "metabolic": metabolic,
        # Federation standard fields for backward compat
        "observation": observation_data,
        "uncertainty": uncertainty,
        "constraints": federation_output.get("constraints", []),
        "recommended_next_organ": federation_output.get("recommended_next_organ"),
        "boundary_notice": federation_output.get(
            "boundary_notice",
            "WELL is advisory-only. Non-medical. Not a substitute for professional care.",
        ),
    }
