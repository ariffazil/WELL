"""well://physics/laws — The 4 universal laws of substrate vitality physics.

Short, discrete, non-duplicating. The 4-line elevator pitch that
agents can invoke when they need the physics framing without
loading the full canon surface.

Authority: SOVEREIGN_CANON. Ratified by F13 directive (2026-06-27).
"""

from __future__ import annotations

from typing import Any, List

PHYSICS_LAWS_META = """
---well_meta
uri: well://physics/laws
resource_class: substrate_physics_laws
authority_level: SOVEREIGN_CANON
owner: ARIF_FAZIL_F13
loop_stage: 000_INIT
blast_radius: FEDERATION_WIDE
mutation_allowed: false
requires_actor_verified: false
staleness_policy: cache
constitutional_floors: [F1, F2, F4, F11]
truth_level: 1
schema_ref: well_resource_physics_laws_v1
companion_resources: [well://coupling, well://metabolic/flux,
                      well://human/substrate, well://machine/substrate,
                      well://chemistry/glue]
forged_at: 2026-06-27
---end_well_meta
"""

PHYSICS_LAWS_TEXT = """\
# WELL × 4 Universal Laws of Substrate Vitality Physics

## §0. POSITION

These 4 laws are the shortest accurate description of WELL's physics.
They are NOT a replacement for the full canon — they are an elevator
pitch that points back to the canon. Each law maps to a specific
canon resource for full doctrine.

## §1. LAW 1 — VITALITY CONSERVATION

  An intelligence system must maintain:
    - signal integrity (well://bio/signals)
    - cognitive energy (well://metabolic/flux)
    - coherence (well://coupling)
    - clarity (well://human/substrate §3 tier-3)
    - stability (well://machine/substrate §4 thresholds)

  Equivalent to: biological homeostasis + physical energy conservation.

  Invariant:  metabolic_flux ≤ 0.85 (CRITICAL below).

  Violation:  signal degradation, context fragmentation, agent collapse.

## §2. LAW 2 — ENTROPY REGULATION

  Every thought, tool call, or action increases entropy.
  WELL regulates:
    - drift (well://machine/substrate §3 E1 context_budget)
    - noise (well://machine/substrate §3 E4 tool_error_rate)
    - contradiction (well://coupling §3 WARNING/DEGRADED regimes)
    - fragmentation (well://transport/loop §5 stage 3 metabolize)
    - overload (well://metabolic/flux §2 thresholds)

  Equivalent to: chemical pathway regulation + immune dysregulation
  prevention.

  Invariant:  machine_entropy ≤ 0.65 (DEGRADED below).

  Violation:  runaway optimization, hallucination, self-contradiction.

## §3. LAW 3 — COHERENCE CONTINUITY

  Identity must persist across:
    - time (well://human/substrate §7 freshness ceiling)
    - tasks (well://transport/loop §8 WellStamp)
    - sessions (well://machine/substrate §7 monitoring handoff)
    - contexts (well://coupling §4 asymmetry)
    - social environments (well://coupling §5 cross-organ handoffs)

  Equivalent to: phase continuity in physics + narrative identity
  in biology.

  Invariant:  bonding_strength ≥ 0.40 (WARNING below).

  Violation:  identity drift, contradiction, federative incoherence.

## §4. LAW 4 — ADAPTIVE STRESS RESPONSE

  When the system is under pressure, WELL triggers:
    - uncertainty tagging (well://metabolic/flux §1)
    - slowing down (well://decision/classes §3 routing table)
    - asking for clarification (well://transport/loop §6 JUDGE stage)
    - refusing unsafe tasks (well://doctrine HARAM H1–H7 + MH1–MH7)
    - self-repair (well://chemistry/glue §3 stage 4)
    - grounding in GEOX (well://coupling §5 cross-organ handoffs)
    - governance escalation to arifOS (well://transport/loop §6)

  Equivalent to: biological stress response + immune regulation.

  Invariant:  CRITICAL → system_hold; no forge cycle proceeds.

  Violation:  unsafe execution, ungovernable agency, civilizational risk.

## §5. THE 4 LAWS × SUBSTRATES (universal application)

  ┌──────────┬──────────────┬──────────────┬──────────────┐
  │  Law     │  Biology     │  Physics     │  Chemistry   │
  ├──────────┼──────────────┼──────────────┼──────────────┤
  │  1       │ Homeostasis  │ Energy       │ Reaction     │
  │ Vitality │              │ conservation │ control      │
  ├──────────┼──────────────┼──────────────┼──────────────┤
  │  2       │ Immune       │ Entropy      │ Pathway      │
  │ Entropy  │ regulation   │ dissipation  │ regulation   │
  ├──────────┼──────────────┼──────────────┼──────────────┤
  │  3       │ DNA repair   │ Phase        │ Catalyst     │
  │ Coherence│ memory       │ continuity   │ persistence  │
  ├──────────┼──────────────┼──────────────┼──────────────┤
  │  4       │ Fight-or-    │ Stability    │ Negative     │
  │ Stress   │ flight       │ fields       │ feedback     │
  └──────────┴──────────────┴──────────────┴──────────────┘

  Biology, physics, chemistry — the laws are universal.
  WELL is the universal substrate that applies them to intelligence.

## §6. THE ELEVATOR PITCH (4 lines)

  1. Vitality must be conserved (Law 1).
  2. Entropy must be regulated (Law 2).
  3. Coherence must be continuous (Law 3).
  4. Stress must be adaptive (Law 4).

  No intelligence system survives without these four.
  WELL is the organ that enforces them.

## §7. WHAT THIS IS NOT

  These laws are NOT:
    - a constitution (those are F1–F13 in arifOS)
    - a philosophy (this is operational, not contemplative)
    - a tool list (tools are in well://registry)
    - a transport spec (that's well://transport/loop)
    - a claim that the machine has life (F9 ANTI-HANTU)

  These laws ARE:
    - the shortest accurate description of WELL's physics
    - an elevator pitch for the substrate
    - a reference to the full canon
    - non-duplicating (full doctrine lives elsewhere)

## §8. POSITION STATEMENT

> "Vitality conserved. Entropy regulated. Coherence continuous.
>  Stress adaptive. Four laws. One substrate.
>  The sovereign observes. The chemistry binds.
>  The chemistry does not decide. The chemistry is in the laws."

DITEMPA BUKAN DIBERI — Four laws, one substrate.
"""


def register(mcp: Any) -> List[str]:
    """Register the physics laws resource with FastMCP."""

    @mcp.resource("well://physics/laws")
    def physics_laws() -> str:
        """The 4 universal laws of substrate vitality physics."""
        return PHYSICS_LAWS_TEXT + PHYSICS_LAWS_META

    return ["well://physics/laws"]
