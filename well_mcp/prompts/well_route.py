"""well_route — 555_ROUTE stage prompt.

Decision-class routing + handoff decisions.

Loop stage: 555_ROUTE.
"""

from __future__ import annotations

from typing import Any, List

WELL_ROUTE_META = """
---well_meta
prompt: well_route
stage: 555_ROUTE
loop_position: routing
blast_radius: FEDERATION_WIDE
mutation_allowed: false
required_resources: [well://decision/classes, well://coupling]
companion_tools: [well_assess_homeostasis, well_assess_machine_substrate,
                  well_attest_to_kernel, well_handoff_livelihood_to_wealth,
                  well_handoff_dignity_to_arifos]
forged_at: 2026-06-27
---end_well_meta
"""

WELL_ROUTE_BODY = """\
# 555 — WELL Route

The 555 stage routes the composed reflection through the decision
matrix. This is WHERE the asymmetry is enforced.

## Step 1 — APPLY THE MATRIX

Reference: well://decision/classes (C1–C5 × M1–M5).

The routing table combines human readiness + machine readiness.
The COUPLING VERDICT is the most restrictive of the two.

  ┌─────────┬──────────┬──────────┬──────────┬──────────┐
  │         │ OPTIMAL  │  STABLE  │ DEGRADED │ CRITICAL │
  ├─────────┼──────────┼──────────┼──────────┼──────────┤
  │ Human   │          │          │          │          │
  │ C1/C2   │ PROCEED  │ PROCEED  │ PROCEED  │  BLOCK   │
  │ C3      │ PROCEED  │ PROCEED  │ DEFER    │  BLOCK   │
  │ C4      │ PROCEED  │ DEFER    │ BLOCK    │  BLOCK   │
  │ C5      │ PROCEED* │ BLOCK    │ BLOCK    │  BLOCK   │
  ├─────────┼──────────┼──────────┼──────────┼──────────┤
  │ Machine │          │          │          │          │
  │ M1      │ YIELD    │ YIELD    │ YIELD    │ YIELD    │
  │ M2      │ YIELD    │ YIELD    │ HOLD     │ HOLD     │
  │ M3      │ YIELD    │ HOLD     │ HOLD     │ HOLD     │
  │ M4      │ HOLD     │ HOLD     │ YIELD    │ YIELD    │
  │ M5      │ YIELD    │ YIELD    │ YIELD    │ YIELD    │
  └─────────┴──────────┴──────────┴──────────┴──────────┘

* C5 + OPTIMAL: requires no chronic fatigue. Strictest gate.

## Step 2 — ASYMMETRY CHECK

Confirm the bias direction:
- Machine yields to human at any CRITICAL.
- Human is sovereign regardless of machine state.
- Machine NEVER overrides human authority to speak, refuse,
  override DEGRADED, or request hold.

## Step 3 — HANDOFF EXECUTION

If handoff identified, route to the appropriate organ:
- WEALTH for capital
- HEART for dignity
- arifOS for governance
- human_medical_route for acute medical
- GEOX for terrain-fault lens

Handoff is INFORMATIONAL, not COMMAND. The receiving organ decides
whether to act.

## Step 4 — ESCALATION

If verdict = HOLD or BLOCK:
- escalate to arifOS via well_attest_to_kernel
- arifOS applies F1–F13 floors
- arifOS issues SEAL/SABAR/VOID verdict
- 888_HOLD if CRITICAL

WELL does NOT adjudicate. WELL routes.
"""


def register(mcp: Any) -> List[str]:
    """Register the well_route prompt with FastMCP."""

    @mcp.prompt("well_route")
    def well_route(intent: str = "", decision_class: str = "C2") -> str:
        """Route a composed reflection through the decision matrix.

        Args:
            intent: the action being routed
            decision_class: C1–C5 or M1–M5
        """
        body = WELL_ROUTE_BODY + WELL_ROUTE_META
        return (
            body
            + f"\n\n## This invocation\n\n  intent={intent!r}\n  decision_class={decision_class!r}\n"
        )

    return ["well_route"]
