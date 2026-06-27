"""well://metabolic/flux — Unified thermodynamic entropy rate.

The flux equation that binds human cognition to machine computation.
Three thresholds that drive decision-class routing.

Authority: OPERATIONAL_CANON.
"""

from __future__ import annotations

from typing import Any, List

FLUX_META = """
---well_meta
uri: well://metabolic/flux
resource_class: thermodynamics_canon
authority_level: OPERATIONAL_CANON
owner: WELL_OPERATOR
loop_stage: 111_SENSE → 333_REASON
blast_radius: ORGAN_WIDE
mutation_allowed: false
requires_actor_verified: false
staleness_policy: cache
constitutional_floors: [F2, F4]
truth_level: 2  # empirical
schema_ref: well_resource_flux_v1
companion_tools: [well_compute_metabolic_flux,
                  well_measure_machine_entropy,
                  well_assess_homeostasis]
forged_at: 2026-06-27
---end_well_meta
"""

FLUX_TEXT = """\
# WELL × Metabolic Flux Thermodynamics

## §1. THE FLUX EQUATION

  metabolic_flux = α · cognitive_entropy_rate + β · machine_entropy

Where:
  cognitive_entropy_rate ∈ [0.0, 1.0]
    — from well_assess_homeostasis (clarity, decision_fatigue,
      accumulated_session_fatigue)
  machine_entropy ∈ [0.0, 1.0]
    — from well_measure_machine_entropy
    — decomposed into 4 components (E1–E4)

Default weights (configurable by F13):
  α = 0.55  (human-side bias — the sovereign's substrate dominates)
  β = 0.45  (machine-side weight)

The asymmetry: human entropy is weighted slightly higher because
the sovereign's substrate is the primary signal. The machine
serves the human. When both rise, human priority is honored.

## §2. THE 4 COMPONENTS OF MACHINE_ENTROPY

  E1  context_budget_consumed  (daily budget fraction)
      Weight: 0.30
  E2  tool_latency_drift       (vs baseline, normalized)
      Weight: 0.20
  E3  resource_staleness       (max age of canon resources, hours/168)
      Weight: 0.20
  E4  tool_error_rate          (failures / last 100 calls)
      Weight: 0.30

  machine_entropy = 0.30·E1 + 0.20·E2 + 0.20·E3 + 0.30·E4

The error rate and context budget are weighted higher because they
represent the machine's reliability + the session's budget — the two
factors most likely to degrade emergence.

## §3. THE 4 THRESHOLDS

  ┌───────────┬────────┬──────────────────────────────────────────────┐
  │  Range    │ Verdict │ Action                                       │
  ├───────────┼────────┼──────────────────────────────────────────────┤
  │ 0.00–0.40 │ STABLE  │ proceed normally                             │
  │ 0.40–0.65 │ WARNING │ monitor; suggest rest; defer C5 tasks        │
  │ 0.65–0.85 │ DEGRADED│ reduce cognitive load; compulsory realloc;   │
  │           │         │ defer C4 and C5 tasks                        │
  │ 0.85–1.00 │ CRITICAL│ system_hold; defer all irreversibles;       │
  │           │         │ escalate to 888_JUDGE via arifOS             │
  └───────────┴────────┴──────────────────────────────────────────────┘

The thresholds are NOT arbitrary. They are calibrated against the
3-state assessment output language (READY | DEGRADED | CRITICAL)
and the 5-state routing language (C1–C5).

## §4. DECAY & FRESHNESS

The flux is a moment-in-time computation. It decays with staleness:

  age_hours ≤ 1      confidence = HIGH
  age_hours ≤ 12     confidence = HIGH
  age_hours ≤ 24     confidence = MEDIUM
  age_hours ≤ 72     confidence = LOW
  age_hours ≤ 168    confidence = STALE
  age_hours > 168    confidence = VOID (refuse to assess)

A stale flux is worse than no flux — it is a misleading flux.
WELL refuses to assess with stale flux and returns UNRELIABLE.

## §5. COMPOSITION RULE

The flux is computed when:
  1. cognitive_entropy_rate has been updated within 24h
  2. machine_entropy has been updated within 24h
  3. dignity_preservation >= 0.70 (else refuse to compose)
  4. substrate is classified (U-WELL)

If any precondition fails → flux is not computed → return UNRELIABLE.
This is the composition contract. It is non-negotiable.

## §6. ASYMMETRY INVARIANT (chemistry bias)

  When flux is high (>= 0.65):
    - The machine reduces load on the human
    - The machine prefers cached/static responses
    - The machine suggests recovery breaks
    - The human continues (or stops voluntarily; F13)
  When flux is high AND human is degraded:
    - The machine yields authority entirely to the human
    - The machine does not optimize the human
    - The machine does not push the human to recover
    - The machine reflects readiness and STOPS

The chemistry biases toward the human. The machine does not heal
the human; the human decides when to recover. The machine reduces
its own pressure on the human first.

DITEMPA BUKAN DIBERI — Flux is a measurement, not a verdict.
"""


def register(mcp: Any) -> List[str]:
    """Register the flux resource with FastMCP."""

    @mcp.resource("well://metabolic/flux")
    def flux() -> str:
        """Metabolic flux thermodynamics — the unified entropy rate."""
        return FLUX_TEXT + FLUX_META

    return ["well://metabolic/flux"]
