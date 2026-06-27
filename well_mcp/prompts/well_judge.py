"""well_judge — 888_JUDGE stage prompt.

Yields to arifOS for F1–F13 floor adjudication. WELL NEVER adjudicates.

Loop stage: 888_JUDGE.
"""

from __future__ import annotations

from typing import Any, List

WELL_JUDGE_META = """
---well_meta
prompt: well_judge
stage: 888_JUDGE
loop_position: yield_to_arifos
blast_radius: FEDERATION_WIDE
mutation_allowed: false  # WELL never adjudicates
required_resources: [well://doctrine, well://physics/laws,
                     well://coupling, well://chemistry/glue]
companion_tools: [well_attest_to_kernel, well_guard_dignity]
note: "This prompt is a YIELD, not a judge. WELL reads it before calling arif_judge."
forged_at: 2026-06-27
---end_well_meta
"""

WELL_JUDGE_BODY = """\
# 888 — WELL Judge (YIELD to arifOS)

The 888 stage yields the critiqued reflection to arifOS for F1–F13
adjudication. WELL NEVER adjudicates floors. WELL surfaces the
reflection and awaits verdict.

## Step 1 — PREPARE EVIDENCE FOR ARIFOS

Before calling arif_judge, prepare:
- signal_id (uuid4)
- substrate_kind
- decision_class (C1–C5 / M1–M5)
- readiness_verdict (proposed, not enforced)
- floor_status (computed per floor, awaiting judgment)
- coupling_state
- handoff_candidates
- loop_trace (stages 111–777)

## Step 2 — CALL arif_judge

Use arifos-kernel arif_judge with the prepared evidence.

arif_judge returns:
- SEAL    → proceed
- SABAR   → hold, wait for human
- HOLD    → pause, conditions to satisfy
- VOID    → refuse + reason

WELL receives the verdict. WELL does NOT modify the verdict.

## Step 3 — PROPAGATE VERDICT

If SEAL:
- reflection ready for EGRESS stage
- proceed to 999_SEAL

If SABAR:
- emit reflection with verdict="SABAR"
- sovereign waits, decides, re-initiates
- loop halts at 555 until sovereign's call

If HOLD:
- emit reflection with verdict="HOLD"
- include conditions to satisfy
- sovereign decides whether to satisfy or escalate

If VOID:
- emit reflection with verdict="VOID"
- include reason
- do NOT re-initiate without sovereign ratification

## Step 4 — ESCALATION

If verdict = HOLD and conditions unclear → 888_HOLD
If verdict = VOID and disagreement → F13 ratification pathway
If verdict = SEAL but sovereignty uncertain → escalate to F13

WELL NEVER overrides arifOS. WELL NEVER overrides F13.
WELL yields. The chemistry binds. The sovereign decides.

## Stance

- Yielding is strength, not weakness.
- The chemistry is in the yielding.
- The sovereign's authority is preserved by the yielding.
"""


def register(mcp: Any) -> List[str]:
    """Register the well_judge prompt with FastMCP."""

    @mcp.prompt("well_judge")
    def well_judge(intent: str = "", decision_class: str = "C2") -> str:
        """Yield a critiqued reflection to arifOS for F1–F13 adjudication.

        Args:
            intent: the action being judged
            decision_class: C1–C5 or M1–M5
        """
        body = WELL_JUDGE_BODY + WELL_JUDGE_META
        return (
            body
            + f"\n\n## This invocation\n\n  intent={intent!r}\n  decision_class={decision_class!r}\n"
        )

    return ["well_judge"]
