"""
WELL MCP Resources — Canonical resource definitions.

Domain Law: SUBSTRATE_LAW
Authority: REFLECT_ONLY — mirror, never judge

Sovereign: Muhammad Arif bin Fazil (F13)
Date: 2026-07-16
License: AGPL-3.0

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

import json


# ============================================================
# IDENTITY RESOURCES
# ============================================================


def well_identity() -> str:
    """The five-well frame. Ingest at session start (000_INIT)."""
    return json.dumps(
        {
            "organ": "WELL",
            "domain_law": "SUBSTRATE_LAW",
            "authority": "REFLECT_ONLY",
            "w0": "OPERATOR_VETO_INTACT",
            "substates": ["H-WELL", "M-WELL", "G-WELL", "C-WELL"],
        }
    )


def well_doctrine() -> str:
    """The WELL doctrine canon."""
    return json.dumps(
        {
            "what_well_is": "biological witness",
            "what_well_refuses": "judge, block, diagnose, prescribe, seal",
            "what_well_never_becomes": "sovereign, executor, oracle",
        }
    )


# ============================================================
# SIGNAL RESOURCES
# ============================================================


def well_bio_signals() -> str:
    """The 13 canonical biological signals."""
    return json.dumps(
        {
            "tier_1_vital": ["heart_circulation", "blood_pressure", "breathing_spo2"],
            "tier_2_recovery": [
                "sleep_architecture",
                "metabolic_state",
                "nutrition_hydration",
            ],
            "tier_3_function": [
                "movement_strength",
                "pain_injury",
                "cognitive_clarity",
            ],
            "tier_4_dignity": [
                "emotional_stress",
                "social_dignity_consent",
                "environment_livelihood",
            ],
        }
    )


def well_flux() -> str:
    """Metabolic flux thermodynamics."""
    return json.dumps(
        {
            "formula": "unified_scalar = (cognitive_entropy + machine_entropy) / 2",
            "compulsory_reallocation_threshold": 0.65,
            "system_hold_threshold": 0.85,
        }
    )


def well_decision_classes() -> str:
    """The C1–C5 × M1–M5 routing matrix."""
    return json.dumps(
        {
            "C1": "proceed_unless_critical",
            "C2": "proceed_unless_critical",
            "C3": "proceed_if_stable",
            "C4": "proceed_only_if_optimal",
            "C5": "proceed_only_if_optimal_no_chronic",
        }
    )


def well_coupling() -> str:
    """The H × M × G coupling chemistry canon."""
    return json.dumps(
        {
            "formula": "coupling = H_well * M_well * G_well",
            "weakest_substrate_dominates": True,
        }
    )


def well_physics_laws() -> str:
    """The 4 universal laws of substrate vitality physics."""
    return json.dumps(
        {
            "law_1": "Conservation — vitality cannot be created or destroyed, only transformed",
            "law_2": "Entropy — ΔS ≤ 0 on every output",
            "law_3": "Floor dominance — weakest substrate determines response",
            "law_4": "Signal ≠ Verdict — WELL signals, arifOS judges",
        }
    )


# ============================================================
# CONTRACT RESOURCES
# ============================================================


def well_human_substrate() -> str:
    """Human substrate contract."""
    return json.dumps(
        {
            "substrate_class": "HUMAN",
            "states": ["READY", "BELOW_BASELINE", "DEGRADED", "CRITICAL", "UNKNOWN"],
            "authority": "REFLECT_ONLY",
            "medical_boundary": "NON_DIAGNOSTIC",
        }
    )


def well_machine_substrate() -> str:
    """Machine substrate contract."""
    return json.dumps(
        {
            "substrate_class": "MACHINE",
            "states": ["STABLE", "STRAINED", "DEGRADED", "CRITICAL"],
            "authority": "REFLECT_ONLY",
        }
    )


def well_interaction_substrate() -> str:
    """The third substrate — the live coupling zone."""
    return json.dumps(
        {
            "substrate_class": "COUPLED",
            "states": ["LOW_RISK", "MEDIUM_RISK", "HIGH_RISK", "RECOVERY"],
            "authority": "REFLECT_ONLY",
        }
    )


def well_info_asymmetry() -> str:
    """Asymmetry as substrate signal — declare, don't exploit."""
    return json.dumps(
        {
            "principle": "Asymmetry is a signal, not a tool",
            "action": "Declare, never exploit",
        }
    )


def well_consent_integrity() -> str:
    """Consent integrity signal — F13 protection layer."""
    return json.dumps(
        {
            "principle": "Consent is sovereign",
            "action": "Guard, never override",
        }
    )


# ============================================================
# TRANSPORT RESOURCES
# ============================================================


def well_transport_loop() -> str:
    """The 5-stage reaction loop contract."""
    return json.dumps(
        {
            "stages": [
                "HOMEOSTASIS",
                "METABOLISM",
                "GRADIENT",
                "LIVELIHOOD",
                "SYNTHESIS",
            ],
            "assessment_language": ["OBSERVED", "DEGRADED", "UNRELIABLE"],
        }
    )



def well_chemistry_glue() -> str:
    """The cross-organ binding canon — the chemistry glue."""
    return json.dumps(
        {
            "principle": "Organs bind through shared substrate signals",
            "bridges": ["arifos", "wealth", "geox", "aaa", "aforge"],
        }
    )


# ============================================================
# BRIDGE RESOURCES
# ============================================================


def well_bridge_wealth() -> str:
    """The WELL→WEALTH federation bridge contract."""
    return json.dumps(
        {
            "source": "well",
            "target": "wealth",
            "tool": "well_handoff_livelihood_to_wealth",
            "signal": "S13_environment_livelihood",
        }
    )


def well_bridge_geox() -> str:
    """The WELL to GEOX federation bridge contract."""
    return json.dumps(
        {
            "source": "well",
            "target": "geox",
            "tool": "well_handoff_livelihood_to_wealth",
            "signal": "S13_environment_livelihood",
        }
    )


def well_bridge_arifos_kernel() -> str:
    """The WELL to arifOS constitutional escalation bridge."""
    return json.dumps(
        {
            "source": "well",
            "target": "arifos",
            "tool": "well_handoff_dignity_to_arifos",
            "signal": "S12_social_dignity_consent",
        }
    )


# ============================================================
# STATE RESOURCES
# ============================================================


def well_registry() -> str:
    """The well_mcp surface registry — auto-discovery."""
    return json.dumps(
        {
            "tools": 27,
            "resources": 29,
            "prompts": 3,
            "phantom": 0,
            "unknown": 0,
        }
    )


def well_afwell_schema() -> str:
    """AFWELL State JSON Schema — canonical substrate state contract."""
    return json.dumps(
        {
            "type": "object",
            "properties": {
                "h_well": {"type": "object"},
                "m_well": {"type": "object"},
                "g_well": {"type": "object"},
                "c_well": {"type": "object"},
                "verdict": {"type": "string"},
                "confidence": {"type": "number"},
            },
        }
    )


def well_afwell_state_arif() -> str:
    """Live operator state snapshot for Arif."""
    return json.dumps(
        {
            "operator": "Arif",
            "state": "unknown",
            "confidence": 0.0,
            "truth_class": "INFERRED",
        }
    )


def well_afwell_events_recent() -> str:
    """Last 20 events from the append-only event ledger."""
    return json.dumps(
        {
            "events": [],
            "total": 0,
        }
    )


def well_afwell_floors() -> str:
    """W-Series floor definitions and current status."""
    return json.dumps(
        {
            "W0": "OPERATOR_VETO_INTACT",
            "W1": "REFLECT_ONLY",
            "W2": "DOMAIN_LAW",
            "W3": "SIGNAL_NOT_VERDICT",
            "W4": "MEDICAL_BOUNDARY",
            "W5": "PERSONA_NOT_SELF",
            "W6": "FLOOR_DOMINANCE",
        }
    )


def well_afwell_vitals_arif() -> str:
    """Readiness vitals — triage color, score, violations."""
    return json.dumps(
        {
            "triage_color": "unknown",
            "score": 0.0,
            "violations": [],
        }
    )


def well_afwell_substrate_registry() -> str:
    """U-WELL Universal Substrate Class Registry."""
    return json.dumps(
        {
            "classes": ["HUMAN", "MACHINE", "INSTITUTIONAL", "COUPLED"],
            "authority": "REFLECT_ONLY",
        }
    )


def well_afwell_telemetry() -> str:
    """Live behavioral telemetry snapshot for Arif."""
    return json.dumps(
        {
            "telemetry": {},
            "confidence": 0.0,
            "truth_class": "INFERRED",
        }
    )


def well_afwell_readiness() -> str:
    """Decision readiness verdict for Arif."""
    return json.dumps(
        {
            "verdict": "UNKNOWN",
            "confidence": 0.0,
            "truth_class": "INFERRED",
        }
    )


def well_afwell_sovereign_entropy() -> str:
    """Live psi_SE (sovereign entropy) metric with component breakdown."""
    return json.dumps(
        {
            "psi_se": 0.0,
            "components": {},
            "confidence": 0.0,
        }
    )


def well_afwell_causal_dag() -> str:
    """WELL causal readiness DAG specification."""
    return json.dumps(
        {
            "nodes": [],
            "edges": [],
            "confidence": 0.0,
        }
    )
