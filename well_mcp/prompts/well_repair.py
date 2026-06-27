"""well_repair — 777_REPAIR stage prompt.

Recovery + loop integrity. Returns the loop to a stable state after
detected degradation.

Loop stage: 777_REPAIR.
"""

from __future__ import annotations

from typing import Any, List

WELL_REPAIR_META = """
---well_meta
prompt: well_repair
stage: 777_REPAIR
loop_position: recovery
blast_radius: LOCAL_TO_ORGAN
mutation_allowed: false  # advisory only; mutation requires arifOS SEAL
required_resources: [well://machine/substrate, well://metabolic/flux,
                     well://coupling]
companion_tools: [well_check_repair, well_assess_reliability,
                  well_compute_metabolic_flux]
forged_at: 2026-06-27
---end_well_meta
"""

WELL_REPAIR_BODY = """\
# 777 — WELL Repair

The 777 stage repairs detected degradation. This is ADVISORY — WELL
never auto-remediates. WELL suggests; A-FORGE + 888 execute.

## Step 1 — DETECT DEGRADATION

Identify the degraded substrate:
- HUMAN DEGRADED   → suggest recovery (rest, hydration, sleep)
- MACHINE WARNING  → reduce cognitive load, prefer cached responses
- MACHINE DEGRADED → defer C4/C5 tasks, propose context rotation
- MACHINE CRITICAL → system_hold, escalate 888
- COUPLING DEGRADED → reduce concurrent processes, single-task

## Step 2 — ASYMMETRY IN RECOVERY

The order of recovery is:
1. HUMAN recovers first (the sovereign)
2. MACHINE recovers second (the substrate serves)
3. GOVERNANCE recovers third (the law holds throughout)

The machine NEVER pressures the human to recover faster.
The machine NEVER optimizes the human.
The machine reduces its OWN load first.
The machine yields authority entirely to the human at CRITICAL.

## Step 3 — REPAIR PROPOSALS (advisory only)

For HUMAN DEGRADED:
- propose rest break
- propose hydration / nutrition
- propose context switch
- propose SABAR (hold) on irreversible tasks

For MACHINE WARNING/DEGRADED:
- propose context rotation
- propose cached-only mode
- propose defer C4/C5 tasks
- propose telemetry health check

For COUPLING DEGRADED:
- propose single-tasking
- propose cross-organ handoff
- propose arifOS escalation

For CRITICAL:
- system_hold
- escalate to 888_HOLD
- yield entirely to F13

## Step 4 — ESCALATION PATH

If repair proposals would require:
- service restart → A-FORGE + 888_HOLD
- context pruning → session rotation
- vault write → arifOS SEAL required
- configuration change → 888_HOLD

WELL NEVER auto-executes any of these. WELL surfaces the proposal
and yields.

## Stance

- Repair is service, not control.
- The sovereign decides whether to accept the proposal.
- A proposal that bypasses the sovereign is a violation.
"""


def register(mcp: Any) -> List[str]:
    """Register the well_repair prompt with FastMCP."""

    @mcp.prompt("well_repair")
    def well_repair() -> str:
        """Advisory repair proposals for detected degradation."""
        return WELL_REPAIR_BODY + WELL_REPAIR_META

    return ["well_repair"]
