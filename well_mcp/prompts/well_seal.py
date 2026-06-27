"""well_seal — 999_SEAL stage prompt.

Final reflection. No vault write — vault is arifOS responsibility.
Emits the stamped reflection to the sovereign.

Loop stage: 999_SEAL.
"""

from __future__ import annotations

from typing import Any, List

WELL_SEAL_META = """
---well_meta
prompt: well_seal
stage: 999_SEAL
loop_position: final_reflection
blast_radius: LOCAL
mutation_allowed: false  # never writes vault
required_resources: [well://registry, well://chemistry/glue]
companion_tools: [well_trace_lineage]  # read-only audit
note: "WELL emits reflection; arifOS seals the vault. Two different concerns."
forged_at: 2026-06-27
---end_well_meta
"""

WELL_SEAL_BODY = """\
# 999 — WELL Seal (FINAL REFLECTION)

The 999 stage is the final reflection. WELL emits the stamped
reflection to the sovereign. WELL NEVER writes the vault — that is
arifOS responsibility.

## Step 1 — ASSEMBLE THE WELL STAMP

Final WellStamp fields:
- signal_id (uuid4)
- value (substrate-dependent)
- freshness (raw + decayed + confidence)
- floor_status (per F1–F13)
- decision_class (C1–C5 / M1–M5)
- readiness_verdict
- machine_entropy, cognitive_entropy_rate, metabolic_flux
- coupling_state
- source (organ, tool, actor, ts)
- hand_off (organs to notify)
- loop_trace (stages 111–888)
- arifOS_verdict (SEAL/SABAR/HOLD/VOID)

## Step 2 — EMIT TO SOVEREIGN

Emit the reflection to the caller (human, agent, or federation).

The sovereign observes:
- the reflection
- the readiness verdict
- the floor status
- the coupling state
- the handoff candidates

The sovereign decides what to do next.

## Step 3 — DO NOT WRITE THE VAULT

WELL emits reflections. WELL does NOT seal VAULT999.

If a vault write is needed:
- arifOS handles it
- WELL surfaces the proposal
- The sovereign ratifies
- arifOS executes the seal

This is the constitutional separation:
- WELL reflects
- arifOS judges
- The sovereign decides
- The vault remembers

## Step 4 — CLOSE THE LOOP

After emission:
- close the loop_trace
- update local state (no mutation, only read)
- await sovereign's next instruction

The loop is not autonomous. The loop is reaction sequence.
The sovereign's next instruction starts the next loop.

## Stance

- Final reflection is offered, not enforced.
- The sovereign's authority is preserved.
- The chemistry is in the yielding.
- The yield is the reflection.
"""


def register(mcp: Any) -> List[str]:
    """Register the well_seal prompt with FastMCP."""

    @mcp.prompt("well_seal")
    def well_seal() -> str:
        """Emit the final stamped reflection to the sovereign."""
        return WELL_SEAL_BODY + WELL_SEAL_META

    return ["well_seal"]
