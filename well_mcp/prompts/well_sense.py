"""well_sense — 111_SENSE stage prompt.

Preserves the existing deep prompt structure (substrate observation).
Reframed under the chemistry loop.

Loop stage: 111_SENSE.
"""

from __future__ import annotations

from typing import Any, List

WELL_SENSE_META = """
---well_meta
prompt: well_sense
stage: 111_SENSE
loop_position: observe
blast_radius: LOCAL
mutation_allowed: false
required_resources: [well://bio/signals, well://machine/substrate]
companion_tools: [well_classify_substrate, well_detect_boundary,
                  well_assess_reliability, well_trace_lineage]
forged_at: 2026-06-27
---end_well_meta
"""

WELL_SENSE_BODY = """\
# 111 — WELL Substrate Sense

The 111 stage observes the substrate. It does NOT reason, route, or
act. It collects evidence.

## Observation targets

For human substrate:
- Tier 1 (vital):  hrv, blood_pressure, breathing, temperature
- Tier 2 (recovery): sleep, metabolic, nutrition
- Tier 3 (function): movement, pain, cognitive_clarity
- Tier 4 (dignity): emotional, social_consent, environment

For machine substrate:
- MF1 process aliveness
- MF2 tool surface integrity
- MF3 schema freshness
- MF4 resource surface alive
- MF5 context budget
- MF6 authority boundary
- MF7 vault bridge healthy

## Output shape

Return a WellStamp.partial with:
- signal_id (uuid4)
- source (organ, tool, actor, ts)
- freshness_raw (hours stale)
- substrate_kind ("human" | "machine" | "governance")
- raw_value (signal payload)

## Stance

- Observe only.
- Tag freshness precisely.
- Never infer from stale data (> 168h = VOID).
- Never fabricate telemetry.
- Yield to next stage (333 QC) for sanity checks.
"""


def register(mcp: Any) -> List[str]:
    """Register the well_sense prompt with FastMCP."""

    @mcp.prompt("well_sense")
    def well_sense(signal: str = "", substrate: str = "human") -> str:
        """Observe a substrate signal.

        Args:
            signal: which signal to observe (e.g., "fatigue", "drift")
            substrate: which substrate to sense ("human", "machine")
        """
        body = WELL_SENSE_BODY + WELL_SENSE_META
        return (
            body
            + f"\n\n## This invocation\n\n  signal={signal!r}\n  substrate={substrate!r}\n"
        )

    return ["well_sense"]
