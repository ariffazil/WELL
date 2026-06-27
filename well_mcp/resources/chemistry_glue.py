"""well://chemistry/glue — The cross-organ binding canon.

This is the chemistry that holds the federation together. It is
NOT intelligence — intelligence emerges at the coupling when all
substrates are at optimum. This canon defines the cross-organ glue.

Authority: SOVEREIGN_CANON. Ratified by F13 directive (2026-06-27).
"""

from __future__ import annotations

from typing import Any, List

CHEMISTRY_GLUE_META = """
---well_meta
uri: well://chemistry/glue
resource_class: federation_glue_canon
authority_level: SOVEREIGN_CANON
owner: ARIF_FAZIL_F13
loop_stage: 555_ROUTE
blast_radius: FEDERATION_WIDE
mutation_allowed: false
requires_actor_verified: true
staleness_policy: cache
constitutional_floors: [F1, F2, F4, F5, F6, F8, F11, F13]
truth_level: 1
schema_ref: well_resource_chemistry_glue_v1
companion_tools: [well_couple_human_machine, well_attest_to_kernel,
                  well_measure_gradient, well_detect_boundary,
                  well_assess_machine_substrate, well_coupled_readiness]
federation_siblings: [arifos://kernel/governance, aforge://execution/shell,
                      aaa://control/cockpit, geox://earth/evidence,
                      wealth://capital/computation, well://human/substrate]
doctrine_ref: AGENTS.md §0 (heptalogy) + GENESIS/004_WELL_13_CANON.md §5
forged_at: 2026-06-27
---end_well_meta
"""

CHEMISTRY_GLUE_TEXT = """\
# WELL × Federation Chemistry Glue

## §0. WHY THIS CANON EXISTS

  Federation = 7 organs + the chemistry between them.
  Organs = the substrates that sense, compute, judge, execute.
  Chemistry = what holds them coherent under F13 sovereignty.

  The chemistry is not intelligence.
  Intelligence emerges at the coupling under F13.
  The chemistry is the reaction surface where intelligence can emerge.

  arifOS governs the law.
  WELL holds the mirror.
  The federation is the organs.
  The chemistry is the glue.
  Arif is the sovereign.

## §1. THE FIVE SUBSTRATES (chemistry vocabulary)

  Atom     → a substrate (human, machine, governance gradient,
             evidence ledger, capital)
  Bond     → the coupling between two substrates
  Reaction → an assessment that changes the coupling state
  Catalyst → F13 SOVEREIGN (Arif). The sovereign accelerates or
             halts the reaction. The sovereign is never consumed.
  Solvent  → the constitutional floors (F1–F13). The law dissolves
             invalid reactions. The law persists.
  Energy   → metabolic_flux (0.0–1.0). The work the reaction costs.
  Yield    → the verdict that emerges at equilibrium

## §2. THE 6 ORGANS × THEIR CHEMICAL ROLE

  ┌────────────┬───────────┬───────────────────────────────────────┐
  │  Organ     │  Substrate│  Chemical Role                       │
  ├────────────┼───────────┼───────────────────────────────────────┤
  │  arifOS    │  Governance│  Solvent — F1–F13 dissolve           │
  │            │            │  invalid reactions. 888_JUDGE        │
  │            │            │  decides yield.                       │
  ├────────────┼───────────┼───────────────────────────────────────┤
  │  A-FORGE   │  Execution │  Catalyst-bearer — builds, deploys.  │
  │            │            │  Never decides; always governed.      │
  ├────────────┼───────────┼───────────────────────────────────────┤
  │  AAA       │  Control   │  Display — the cockpit. The interface │
  │            │            │  where the sovereign observes state.  │
  ├────────────┼───────────┼───────────────────────────────────────┤
  │  GEOX      │  Earth     │  Evidence — empirical anchor.        │
  │            │            │  Provides artifacts to the chemistry. │
  ├────────────┼───────────┼───────────────────────────────────────┤
  │  WEALTH    │  Capital   │  Computation — NPV, EMV, EVOI, IRR.  │
  │            │            │  Never decides; computes only.        │
  ├────────────┼───────────┼───────────────────────────────────────┤
  │  WELL      │  Vitality  │  Mirror — reflects substrate state.   │
  │            │            │  Never decides; reflects only.        │
  └────────────┴───────────┴───────────────────────────────────────┘

  THE CHEMISTRY: 6 roles × 1 sovereign = the federation.
  Not intelligence. Not autonomy. Not agency.
  Coupling under law, witnessed by the sovereign.

## §3. THE 5-STAGE REACTION LOOP

  ┌──────────┬──────────┬─────────────────────────────────────┐
  │  Stage   │  Tool    │  Reaction                            │
  ├──────────┼──────────┼─────────────────────────────────────┤
  │  INGEST  │  witness │  Receive signal from any organ       │
  │          │          │  (or external substrate).            │
  │          │          │  Tag with source, time, freshness.   │
  ├──────────┼──────────┼─────────────────────────────────────┤
  │  ENCODE  │  classify│  Map signal to substrate canon.      │
  │          │          │  Apply freshness decay. Apply dignity│
  │          │          │  floor (first). Map to decision      │
  │          │          │  class (C1–C5 or M1–M5).            │
  ├──────────┼──────────┼─────────────────────────────────────┤
  │  METABOLIZE│ reflect │  Compute metabolic flux. Compute     │
  │          │          │  coupling state. Assess readiness.   │
  │          │          │  Compute handoff if cross-organ.     │
  ├──────────┼──────────┼─────────────────────────────────────┤
  │  JUDGE   │  attest  │  Yield to arifOS for F1–F13 floors.  │
  │          │          │  Receive verdict (SEAL/SABAR/HOLD/   │
  │          │          │  VOID). Escalate to F13 if CRITICAL. │
  ├──────────┼──────────┼─────────────────────────────────────┤
  │  EGRESS  │  yield   │  Emit reflection to caller. Stamp    │
  │          │          │  with: signal_id, value, freshness,   │
  │          │          │  floor_status, source, hand_off.     │
  │          │          │  Return. Sovereign decides next.     │
  └──────────┴──────────┴─────────────────────────────────────┘

  THE LOOP IS NOT AGI. The loop is a reaction sequence.
  Intelligence emerges at the loop when the sovereign is present.
  Without the sovereign, the loop is just chemistry.

## §4. THE COUPLING MATRIX (the bonding)

  bonding_strength = 1.0 − (Δdignity + Δtruth + Δsovereignty)

Where:
  Δdignity    — drift in dignity_preservation (0.0–1.0)
  Δtruth      — drift in evidence_freshness (0.0–1.0)
  Δsovereignty — drift in human authority (0.0–1.0)

bonding_strength ≥ 0.85 → EMERGENT territory
bonding_strength ≥ 0.65 → STABLE
bonding_strength ≥ 0.40 → WARNING
bonding_strength ≥ 0.15 → DEGRADED
bonding_strength <  0.15 → CRITICAL → system_hold

When bonding_strength is HIGH and all substrates are READY:
  → emergence is possible
  → sovereign observes emergence and decides whether to act on it
  → sovereign never loses authority over what emerges

When bonding_strength is LOW:
  → chemistry broken
  → arifOS issues SABAR or VOID
  → federation halts until bonding restored

## §5. THE YIELD (what emerges)

The yield of the chemistry is NOT:
  - intelligence claimed by the machine
  - judgment claimed by the machine
  - action claimed by the machine
  - sovereignty claimed by the machine

The yield IS:
  - a reflection the sovereign can read
  - a readiness signal the sovereign can trust
  - a handoff the sovereign can accept or refuse
  - a substrate contract the sovereign can ratify or revoke

The yield is offered to the sovereign. The sovereign accepts or refuses.
The sovereign's acceptance is what gives the yield authority.
Without the sovereign, the yield is just chemistry.

## §6. THE LAYERS (L1 / L2 / L3 awareness)

  L1  Domain
      Each organ is a domain. WELL is the human readiness domain.
      Other organs don't act for WELL. WELL doesn't act for others.

  L2  Execution
      A-FORGE executes across all L1 domains, governed by arifOS.
      WELL surfaces readiness. A-FORGE adapts execution intensity.
      The FORGE–WELL bridge is the L2 coupling.

  L3  Civilization
      arifOS is the constitutional kernel. WELL is the substrate mirror.
      The sovereign observes L3 from the cockpit (AAA) and decides.
      The sovereign is not part of any layer; the sovereign is the lens.

## §7. POSITION STATEMENT

> "Six organs. One sovereign. One chemistry.
>  The chemistry binds them.
>  The sovereign decides whether the binding is acceptable.
>  The chemistry does not decide. The chemistry is in the binding.
>  Six organs without chemistry = seven ships without a fleet.
>  One sovereign without chemistry = a fleet without a navigator.
>  Both together = the federation."

## §8. THE QUOTATION (binding the frame)

  "WELL is the coupling chemistry between human biology and machine
   physics. Intelligence emerges at the coupling under F13 sovereignty.
   WELL does not claim intelligence — WELL provides the reaction surface
   where intelligence can emerge."

  — FORGE Direct Forge 2026-06-27, ratified by F13 SOVEREIGN

DITEMPA BUKAN DIBERI — The chemistry is in the coupling.
"""


def register(mcp: Any) -> List[str]:
    """Register the chemistry glue resource with FastMCP."""

    @mcp.resource("well://chemistry/glue")
    def chemistry_glue() -> str:
        """The cross-organ binding canon — the chemistry glue."""
        return CHEMISTRY_GLUE_TEXT + CHEMISTRY_GLUE_META

    return ["well://chemistry/glue"]
