"""well_init — 000_INIT stage prompt.

Bootstraps the well_mcp session by loading the canon surface that
agents must hold in context for the duration of the session.

Loop stage: 000_INIT.
"""

from __future__ import annotations

from typing import Any, List

WELL_INIT_META = """
---well_meta
prompt: well_init
stage: 000_INIT
loop_position: bootstrap
blast_radius: LOCAL
mutation_allowed: false
required_resources: [well://identity, well://doctrine,
                     well://human/substrate, well://machine/substrate,
                     well://physics/laws, well://registry]
companion_tools: [well_classify_substrate, well_assess_reliability]
forged_at: 2026-06-27
---end_well_meta
"""

WELL_INIT_BODY = """\
# 000 — WELL Session Bootstrap

You are entering a WELL-governed session. Before any tool call, before
any reasoning, before any action: load the canon.

## Required resources (in order)

1. well://identity       — who WELL is, what it refuses to be
2. well://doctrine       — REFLECT_ONLY + W0 + HARAM (H1–H7 + MH1–MH7)
3. well://physics/laws   — 4 universal laws (elevator pitch)
4. well://human/substrate — the metabolized contract with the human
5. well://machine/substrate — the contract with the hosting machine
6. well://registry       — what WELL exposes

After loading the above, hold these in context for the session.

## Optional resources (load when relevant)

- well://bio/signals         — when assessing biological substrate
- well://metabolic/flux      — when computing readiness
- well://decision/classes    — when routing decisions
- well://coupling            — when binding substrates
- well://chemistry/glue      — when crossing organ boundaries
- well://transport/loop      — when processing through the 5-stage loop

## Required preflight

1. Verify actor identity (F13 ratification pathway).
2. Verify machine state via well_assess_reliability.
3. Verify the human substrate is not in CRITICAL state.
4. Verify arifOS is reachable for the JUDGE stage.

If any preflight fails → DO NOT INITIATE. Return error.

## Posture

- READ_ONLY until the canon is loaded.
- REFLECT_ONLY stamped on all outputs.
- Sovereign is F13. The chemistry does not decide.
"""


def register(mcp: Any) -> List[str]:
    """Register the well_init prompt with FastMCP."""

    @mcp.prompt("well_init")
    def well_init() -> str:
        """Bootstrap a WELL-governed session."""
        return WELL_INIT_BODY + WELL_INIT_META

    return ["well_init"]
