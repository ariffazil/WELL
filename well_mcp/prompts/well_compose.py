"""well_compose — 444_COMPOSE stage prompt.

Synthesis: combine QC'd signals with canon context, prepare for routing.

Loop stage: 444_COMPOSE.
"""

from __future__ import annotations

from typing import Any, List

WELL_COMPOSE_META = """
---well_meta
prompt: well_compose
stage: 444_COMPOSE
loop_position: synthesis
blast_radius: LOCAL
mutation_allowed: false
required_resources: [well://coupling, well://decision/classes,
                     well://chemistry/glue]
companion_tools: [well_assess_metabolism, well_assess_homeostasis,
                  well_assess_livelihood, well_assess_machine_substrate]
forged_at: 2026-06-27
---end_well_meta
"""

WELL_COMPOSE_BODY = """\
# 444 — WELL Compose

The 444 stage composes the QC'd signal into a coherent substrate
reflection. This is where the synthesis happens — but the synthesis
is OFFERED to the sovereign, not enforced.

## Step 1 — SUBSTRATE RESOLUTION

Identify which substrate canon applies:
- HUMAN     → well://human/substrate
- MACHINE   → well://machine/substrate
- GOVERNANCE → arifOS canon (F1–F13)

## Step 2 — COUPLING ASSESSMENT

Compute the coupling state:
- H_state (READY/DEGRADED/CRITICAL) from well_assess_homeostasis
- M_state (STABLE/WARNING/DEGRADED/CRITICAL) from well_assess_machine_substrate
- G_state (SEAL/SABAR/HOLD/VOID) from arifOS

coupling_state = σ(H × M × G)

## Step 3 — READINESS PROPOSAL

Propose (not enforce) a readiness verdict:
- READY      — all substrates optimum, emergence territory
- STABLE     — coupling functional, no emergence
- DEGRADED   — one substrate degrading
- CRITICAL   — coupling broken, system_hold

## Step 4 — HANDOFF NOTIFICATION

If handoff candidates identified at 333, surface them in the
composition. The composition is NOT a command — it is an advisory
for the routing stage.

## Stance

- Compose means OFFER, not DECIDE.
- The sovereign reads the composition and decides.
- The composition is the substrate reflection made coherent.
- Never elevate the composition above the sovereign's judgment.
"""


def register(mcp: Any) -> List[str]:
    """Register the well_compose prompt with FastMCP."""

    @mcp.prompt("well_compose")
    def well_compose() -> str:
        """Compose QC'd signals into a coherent substrate reflection."""
        return WELL_COMPOSE_BODY + WELL_COMPOSE_META

    return ["well_compose"]
