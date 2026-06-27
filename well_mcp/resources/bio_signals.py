"""well://bio/signals — The 13 canonical human substrate signals.

Full signal map from WELL_13_SIGNAL_MAP.json (363 LOC, ratified 2026-06-06).
4 tiers: vital_substrate → recovery_metabolic → function_cognition → dignity_environment.

Authority: DOMAIN_CANON.
"""

from __future__ import annotations

from typing import Any, List

BIO_SIGNALS_META = """
---well_meta
uri: well://bio/signals
resource_class: signal_architecture_canon
authority_level: DOMAIN_CANON
owner: WELL_OPERATOR
loop_stage: 000_INIT
blast_radius: FEDERATION_WIDE
mutation_allowed: false
requires_actor_verified: false
staleness_policy: fail_closed
constitutional_floors: [F2, F6, F9, F13]
truth_level: 2  # empirical, requires verification per assessment
schema_ref: well_resource_bio_signals_v1
source_doc: WELL_13_SIGNAL_MAP.json
doctrine_ref: GENESIS/004_WELL_13_CANON.md
forged_at: 2026-06-27
---end_well_meta
"""

BIO_SIGNALS_TEXT = """\
# WELL × 13 Canonical Biological Signals

## §1. STRUCTURE (4 tiers × 13 signals)

  ┌─────────────────────────────────────────────────────────────────┐
  │  TIER 1 — VITAL SUBSTRATE (S01–S04)                              │
  │  Principle: Without these, no higher layer is meaningful.       │
  │  Authority: reflect_only                                        │
  ├─────────────────────────────────────────────────────────────────┤
  │  S01  heart_circulation                                          │
  │        hrv_status, resting_heart_rate                            │
  │        Tool: well_assess_metabolism                              │
  │        Status: partial (self-report only; wearable HARUS)        │
  │        Escalation: acute_hold when hrv_status=low + chronic      │
  │                                                                  │
  │  S02  blood_pressure                                             │
  │        systolic_bp, diastolic_bp                                 │
  │        Tool: well_assess_metabolism                              │
  │        Status: partial (self-report only)                        │
  │        Escalation: medical_escalation when systolic>180 OR       │
  │                    diastolic>120                                  │
  │                                                                  │
  │  S03  breathing_oxygenation                                      │
  │        respiratory_rate, spo2                                    │
  │        Tool: well_assess_metabolism                              │
  │        Status: partial (self-report only)                        │
  │        Escalation: medical_escalation when spo2<92 OR sob_severe │
  │                                                                  │
  │  S04  temperature_inflammation                                   │
  │        body_temperature, inflammation_markers                    │
  │        Tool: well_assess_metabolism                              │
  │        Status: partial (self-report only)                        │
  │        Escalation: medical_escalation when temp>=39 OR <=35      │
  ├─────────────────────────────────────────────────────────────────┤
  │  TIER 2 — RECOVERY / METABOLIC (S05–S07)                         │
  │  Principle: Recovery precedes function.                          │
  │  Authority: reflect_only                                        │
  ├─────────────────────────────────────────────────────────────────┤
  │  S05  sleep_architecture                                         │
  │        sleep_hours, sleep_quality, sleep_debt_days, awakenings,  │
  │        circadian_alignment                                       │
  │        Tool: well_assess_homeostasis (mode='sleep')               │
  │        Status: active                                             │
  │        Escalation: acute_hold when sleep_debt_days>=3 +          │
  │                    cognitive_clarity<=4                           │
  │                                                                  │
  │  S06  metabolic_state                                            │
  │        fasting_hours, metabolic_stability, glucose, energy       │
  │        Tool: well_assess_metabolism                              │
  │        Status: active                                             │
  │        Escalation: medical_escalation when glucose<3 OR >25      │
  │                                                                  │
  │  S07  nutrition_hydration                                        │
  │        nutrition_quality, hydration, appetite, elimination       │
  │        Tool: well_assess_metabolism                              │
  │        Status: partial (self-report only)                        │
  │        Escalation: medical_escalation when dehydration_severe    │
  │                    OR eating_disorder_signal                     │
  ├─────────────────────────────────────────────────────────────────┤
  │  TIER 3 — FUNCTION / COGNITION (S08–S10)                         │
  │  Principle: What the body can do under current load.             │
  │  Authority: reflect_only                                        │
  ├─────────────────────────────────────────────────────────────────┤
  │  S08  movement_strength                                          │
  │        movement_count, gait, grip_strength, mobility_score       │
  │        Tool: well_assess_metabolism                              │
  │        Status: partial (wearable not yet wired)                  │
  │        Note: MAKRUH to use as coaching nudge; ALLOWED as          │
  │              substrate signal only.                              │
  │        Escalation: acute_hold when mobility_score<=2 +           │
  │                    decision_class>=C4                             │
  │                                                                  │
  │  S09  pain_injury                                                │
  │        pain_sites, pain_level, chronic_tension                   │
  │        Tool: well_assess_metabolism                              │
  │        Status: partial (self-report; pain is qualitative)        │
  │        Escalation: medical_escalation when pain_severe OR         │
  │                    new_injury                                     │
  │                                                                  │
  │  S10  cognitive_clarity                                          │
  │        clarity, decision_fatigue, focus_durability, reaction_time │
  │        Tool: well_assess_homeostasis (mode='cognitive')           │
  │        Status: active                                             │
  │        Escalation: decision_class downgrade when clarity<=4 +     │
  │                    decision_fatigue>=7                           │
  ├─────────────────────────────────────────────────────────────────┤
  │  TIER 4 — DIGNITY / ENVIRONMENT (S11–S13)  ← THE DIFFERENTIATOR │
  │  Principle: The layer fitness apps never see.                   │
  │  Authority: reflect_only                                        │
  ├─────────────────────────────────────────────────────────────────┤
  │  S11  emotional_stress                                           │
  │        stress_load, restlessness, emotional_state, perceived_ctrl │
  │        Tool: well_assess_homeostasis (mode='stress')             │
  │        Status: active                                             │
  │        Escalation: acute_hold when emotional_state=irritable +   │
  │                    stress_load>=8                                 │
  │                                                                  │
  │  S12  social_dignity_consent  ← PRIMARY DIFFERENTIATOR          │
  │        dignity_preservation, coercion_signals,                   │
  │        reductionism_risk, boundary_violated                      │
  │        Tool: well_guard_dignity                                  │
  │        Status: active                                             │
  │        Note: PRIMARY surface for body/person boundary +          │
  │              reductionism detection. NEVER diagnose — only signal.│
  │        Escalation: arifOS/JUDGE when boundary_violated=true      │
  │                                                                  │
  │  S13  environment_livelihood                                     │
  │        energy_level, duty_load, role_burden, purpose_alignment,  │
  │        cashflow_status, internal_consistency                     │
  │        Tool: well_assess_livelihood                              │
  │        Status: active                                             │
  │        Escalation: WEALTH handoff when cashflow=stress +          │
  │                    role_burden>=8                                 │
  │        Cross-organ handoff: WELL→WEALTH for cashflow pressure;   │
  │                             WELL→HEART for shame/vulnerability. │
  └─────────────────────────────────────────────────────────────────┘

## §2. FEDERATION RULE

  "Wearables may feed WELL. Wearables must not define WELL."

WELL is not a fitness app. Biometrics are substrate, not metrics
to optimize. The 13 signals are the vocabulary; the doctrine is
the grammar.

## §3. COVERAGE GAPS (KNOWN, DOCUMENTED)

  Tier 1 vital_substrate:        0 active, 4 partial (self-report only)
  Tier 2 recovery_metabolic:     2 active, 1 partial (nutrition)
  Tier 3 function_cognition:     1 active, 2 partial (movement, pain)
  Tier 4 dignity_environment:    3 active, 0 partial

Coverage gaps are intentional until wearable integration matures.
Gaps do not block canon ratification. Coverage is audited via
well_13_signal_coverage tool.

## §4. CROSS-ORGAN HANDOFFS

  Cashflow pressure + role burden >= 8   →  WEALTH
  Shame / vulnerability / longing        →  HEART
  Consent / dignity breach               →  arifOS / 888_JUDGE
  Acute medical danger                   →  human_medical_route
  Terrain-fault pressure metaphor        →  GEOX (lens only)

WELL signals; other organs act. WELL never acts alone on irreversible.

DITEMPA BUKAN DIBERI — Substrate signals, not metric optimization.
"""


def register(mcp: Any) -> List[str]:
    """Register the bio/signals resource with FastMCP."""

    @mcp.resource("well://bio/signals")
    def bio_signals() -> str:
        """The 13 canonical biological signals — full signal map."""
        return BIO_SIGNALS_TEXT + BIO_SIGNALS_META

    return ["well://bio/signals"]
