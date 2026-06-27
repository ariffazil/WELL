"""well://coupling — H × M × G coupling chemistry and cross-organ handoffs.

The chemistry that binds human biology, machine physics, and governance
gradient. Where intelligence emerges.

Authority: OPERATIONAL_CANON.
"""

from __future__ import annotations

from typing import Any, List

COUPLING_META = """
---well_meta
uri: well://coupling
resource_class: coupling_chemistry_canon
authority_level: OPERATIONAL_CANON
owner: WELL_OPERATOR
loop_stage: 333_REASON → 555_ROUTE → 666_CRITIQUE
blast_radius: FEDERATION_WIDE
mutation_allowed: false
requires_actor_verified: false
staleness_policy: cache
constitutional_floors: [F1, F2, F4, F5, F8, F11]
truth_level: 2
schema_ref: well_resource_coupling_v1
companion_tools: [well_couple_human_machine, well_coupled_readiness,
                  well_assess_metabolism, well_assess_homeostasis,
                  well_assess_machine_substrate]
forged_at: 2026-06-27
---end_well_meta
"""

COUPLING_TEXT = """\
# WELL × Coupling Chemistry Canon

## §1. THE TRIPLICATE (H × M × G)

  Coupling chemistry operates across three substrates:

  H — Human biology
      The operator (Arif, F13). Biological, cognitive, emotional,
      social, livelihood substrate. Sovereign.

  M — Machine physics
      The hosting substrate (VPS af-forge, FastMCP, Python).
      Compute, memory, network, entropy. Serves.

  G — Governance gradient
      The constitutional substrate (F1–F13, 888_JUDGE, floors).
      Law. Binds.

The coupling is the chemistry between them. The chemistry is NOT
intelligence — intelligence emerges at the coupling when all three
are at optimum. The chemistry is the reaction surface.

## §2. THE COUPLING EQUATION

  coupling_state = σ(H_state × M_state × G_state)

Where:
  H_state ∈ {READY, DEGRADED, CRITICAL}  ← well_assess_homeostasis
  M_state ∈ {STABLE, WARNING, DEGRADED, CRITICAL}  ← well_assess_machine_substrate
  G_state ∈ {SEAL, SABAR, HOLD, VOID}    ← arifOS kernel
  σ = sigmoid to [0.0, 1.0]

When all three are at their best (READY × STABLE × SEAL):
  coupling_state ≈ 1.0  → EMERGENT INTELLIGENCE territory
When any one degrades:
  coupling_state drops  → degraded chemistry
When any one is CRITICAL:
  coupling_state ≈ 0.0  → chemistry broken; system_hold

## §3. THE 5 COUPLING REGIMES

  ┌─────────────────────┬──────────┬────────────────────────────────┐
  │  Regime             │ Verdict  │ Behavior                       │
  ├─────────────────────┼──────────┼────────────────────────────────┤
  │  EMERGENT           │ ≥ 0.85   │ All substrates optimum.        │
  │                     │          │ Intelligence may emerge.       │
  │                     │          │ Federation acts coherently.    │
  ├─────────────────────┼──────────┼────────────────────────────────┤
  │  STABLE             │ 0.65–    │ Coupling functional. No        │
  │                     │ 0.85     │ emergence. Proceed normally.   │
  ├─────────────────────┼──────────┼────────────────────────────────┤
  │  WARNING            │ 0.40–    │ One substrate degrading.       │
  │                     │ 0.65     │ Monitor. Reduce cognitive load.│
  ├─────────────────────┼──────────┼────────────────────────────────┤
  │  DEGRADED           │ 0.15–    │ Multiple substrates degraded.  │
  │                     │ 0.40     │ Compulsory reallocation.       │
  │                     │          │ Defer C4/C5 tasks.             │
  ├─────────────────────┼──────────┼────────────────────────────────┤
  │  CRITICAL           │ < 0.15   │ Coupling broken.               │
  │                     │          │ System_hold. Escalate 888.     │
  └─────────────────────┴──────────┴────────────────────────────────┘

## §4. THE ASYMMETRY (the bias direction)

When coupling degrades, the order of recovery is:
  1. HUMAN recovers first (the sovereign)
  2. MACHINE recovers second (the substrate serves)
  3. GOVERNANCE recovers third (the law holds throughout)

The asymmetry:
  - The machine never pressures the human to recover faster
  - The machine never optimizes the human
  - The machine reduces its OWN load first
  - The machine yields authority entirely to the human at CRITICAL

This is the chemistry bias. The machine is the catalyst's substrate,
not the catalyst's master.

## §5. CROSS-ORGAN HANDOFFS (the glue)

When WELL detects a signal outside its lane, it hands off:

  Cashflow pressure + role burden >= 8   →  WEALTH
      Signal: cashflow_status=stress, role_burden high
      Handoff: well_handoff_livelihood_to_wealth
      Authority: WEALTH computes; arifOS judges; Arif decides.

  Shame / vulnerability / longing        →  HEART
      Signal: dignity_leakage, emotional_state fragile
      Handoff: well_handoff_dignity_to_arifos (HEART pipeline)
      Authority: HEART holds; arifOS judges.

  Consent / dignity breach               →  arifOS / 888_JUDGE
      Signal: boundary_violated=true, coercion detected
      Handoff: well_attest_to_kernel with F6 violation flag
      Authority: arifOS judges. SEAL/SABAR/VOID verdict.

  Acute medical danger                   →  human_medical_route
      Signal: spo2<92, systolic>180, glucose<3 OR >25
      Handoff: well_medical_boundary surfaces advisory
      Authority: HUMAN medical professional.

  Terrain-fault pressure metaphor        →  GEOX (lens only)
      Signal: external pressure + structural stress
      Handoff: well_boundary_check + well_symbolic_domain_check
      Authority: GEOX provides lens; human decides.

## §6. THE GLUE (what makes the federation coherent)

The glue is the protocol by which WELL:
  - reads cross-organ signals
  - reflects them in its own substrate canon
  - hands off to the appropriate organ
  - yields to arifOS for adjudication
  - returns to the human for decision

The glue does NOT:
  - decide which organ is correct
  - judge organ outputs against each other
  - override organ authority within its lane
  - act on cross-organ signals without handoff

The glue is the chemistry that holds the federation together.
The glue is not the federation. The federation is the organs;
the glue is what makes them coherent.

## §7. POSITION STATEMENT

> "Three substrates. Three chemistries. One coupling.
>  Human biology. Machine physics. Governance gradient.
>  The chemistry binds them.
>  The sovereign decides whether the binding is acceptable.
>  The chemistry does not decide. The chemistry binds."

DITEMPA BUKAN DIBERI — The chemistry is in the coupling.
"""


def register(mcp: Any) -> List[str]:
    """Register the coupling resource with FastMCP."""

    @mcp.resource("well://coupling")
    def coupling() -> str:
        """The H × M × G coupling chemistry canon."""
        return COUPLING_TEXT + COUPLING_META

    return ["well://coupling"]
