"""well_qc — 333_REASON+QC stage prompt.

Quality control on observed signals. Filters freshness, applies dignity
floor first, maps to decision class.

Loop stage: 333_REASON.
"""

from __future__ import annotations

from typing import Any, List

WELL_QC_META = """
---well_meta
prompt: well_qc
stage: 333_REASON
loop_position: quality_control
blast_radius: LOCAL
mutation_allowed: false
required_resources: [well://doctrine, well://bio/signals,
                     well://metabolic/flux]
companion_tools: [well_validate_vitality, well_measure_gradient,
                  well_trace_lineage, well_medical_boundary]
forged_at: 2026-06-27
---end_well_meta
"""

WELL_QC_BODY = """\
# 333 — WELL Quality Control

The 333 stage applies quality control to the observed signal. This is
the dignity floor's enforcement point.

## Step 1 — DIGNITY FLOOR (MUST PASS FIRST)

Before any other computation, verify:
1. consent_verified = True
2. coercion_signals = absent
3. reductionism_risk < 0.30
4. dignity_preservation ≥ 0.70

If ANY check fails → DOWNGRADE to observation only.
Return dignity_leakage advisory. Do NOT proceed.

## Step 2 — FRESHNESS DECAY

Apply freshness decay to the raw signal:
- ≤ 12h    → HIGH confidence
- 12–24h   → MEDIUM confidence
- 24–72h   → LOW confidence
- 72–168h  → STALE (cite only, no inference)
- > 168h   → DO_NOT_INFER (refuse)

## Step 3 — DECISION CLASS MAPPING

Map the originating task to a decision class:
- C1 OBSERVE      — read, query, fetch
- C2 DRAFT        — write, build, propose
- C3 COMMIT       — commit, deploy, execute
- C4 PRODUCTION   — production deploy, cross-org
- C5 IRREVERSIBLE — vault seal, F13 ratification

For machine tasks: M1–M5 (parallel, machine-side).

## Step 4 — HANDOFF IDENTIFICATION

Identify candidate handoffs:
- Cashflow pressure + role_burden ≥ 8 → WEALTH
- Shame / vulnerability / longing    → HEART
- Consent / dignity breach           → arifOS / 888_JUDGE
- Acute medical danger               → human_medical_route
- Terrain-fault pressure metaphor    → GEOX (lens only)

## Output shape

Return a WellStamp.encoded with:
- freshness_decayed (hours)
- confidence ("HIGH" | "MEDIUM" | "LOW" | "STALE" | "VOID")
- decision_class ("C1" | ... | "C5" | "M1" | ... | "M5")
- handoff_candidates (list of organs)
- dignity_floor (PASS | HOLD | VOID)
"""


def register(mcp: Any) -> List[str]:
    """Register the well_qc prompt with FastMCP."""

    @mcp.prompt("well_qc")
    def well_qc(signal: str = "") -> str:
        """Apply quality control to an observed signal.

        Args:
            signal: the signal to QC
        """
        body = WELL_QC_BODY + WELL_QC_META
        return body + f"\n\n## This invocation\n\n  signal={signal!r}\n"

    return ["well_qc"]
