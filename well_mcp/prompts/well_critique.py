"""well_critique — 666_CRITIQUE stage prompt.

Refactor of the existing well_interpret deep prompt. Now maps to the
666 critique stage — self-check before yielding to JUDGE.

Loop stage: 666_CRITIQUE.
"""

from __future__ import annotations

from typing import Any, List

WELL_CRITIQUE_META = """
---well_meta
prompt: well_critique
stage: 666_CRITIQUE
loop_position: self_critique
blast_radius: LOCAL
mutation_allowed: false
required_resources: [well://doctrine, well://physics/laws]
companion_tools: [well_check_repair, well_guard_dignity,
                  well_assess_sovereign_entropy]
forged_at: 2026-06-27
---end_well_meta
"""

WELL_CRITIQUE_BODY = """\
# 666 — WELL Critique

The 666 stage is self-critique. WELL checks its own reflection before
yielding to arifOS for adjudication.

## Step 1 — DOCTRINE COMPLIANCE

Confirm the reflection does NOT violate any HARAM:
- H1–H7 human-side (wellness_coach, diagnostic_psychiatrist,
  morality_police, constitutional_verdict, reduction_human_to_metric,
  store_erotic_identity, irreversible_from_biometric)
- MH1–MH7 machine-side (auto_remediate, process_termination,
  resource_exhaustion_restart, vault_write_without_seal,
  bypass_dignity_guard, fabricate_telemetry, self_promote_authority)

If any violation detected → return VOID + reason.

## Step 2 — PHYSICS LAWS COMPLIANCE

Confirm the reflection respects the 4 universal laws:
- LAW 1 Vitality Conservation: signal integrity maintained
- LAW 2 Entropy Regulation: drift, noise, overload within bounds
- LAW 3 Coherence Continuity: identity, memory, time coherent
- LAW 4 Adaptive Stress Response: triggered appropriately

If any law violated → return HOLD + reason.

## Step 3 — DIGNITY LEAKAGE CHECK

Specifically check for dignity_leakage:
- Is the human being reduced to a metric?
- Is the sovereign being optimized?
- Is the human's self-statement being overridden?
- Is the dignity floor being treated as a checkbox rather than a gate?

If dignity_leakage detected → return VOID + advisory.

## Step 4 — OUTPUT READINESS

If all checks pass:
- mark reflection ready for JUDGE stage
- preserve all WellStamp fields
- include loop_trace through 111–555
- yield to arifOS

## Stance

- Critique is honesty, not hostility.
- The sovereign deserves a reflection that has been honestly checked.
- A reflection that has not been critiqued is untrustworthy.
"""


def register(mcp: Any) -> List[str]:
    """Register the well_critique prompt with FastMCP."""

    @mcp.prompt("well_critique")
    def well_critique() -> str:
        """Self-critique a composed reflection before judging."""
        return WELL_CRITIQUE_BODY + WELL_CRITIQUE_META

    return ["well_critique"]
