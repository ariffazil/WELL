"""well://decision/classes — C1–C5 (human) and M1–M5 (machine) routing matrix.

Authority: OPERATIONAL_CANON.
"""

from __future__ import annotations

from typing import Any, List

DECISION_CLASSES_META = """
---well_meta
uri: well://decision/classes
resource_class: routing_matrix_canon
authority_level: OPERATIONAL_CANON
owner: WELL_OPERATOR
loop_stage: 555_ROUTE
blast_radius: FEDERATION_WIDE
mutation_allowed: false
requires_actor_verified: false
staleness_policy: cache
constitutional_floors: [F2, F4, F11]
truth_level: 2
schema_ref: well_resource_decision_classes_v1
companion_tools: [well_decision_classify, well_decision_bandwidth,
                  well_validate_vitality, well_assess_machine_substrate]
forged_at: 2026-06-27
---end_well_meta
"""

DECISION_CLASSES_TEXT = """\
# WELL × Decision Class Routing Matrix

## §1. HUMAN DECISION CLASSES (C1–C5)

  C1  OBSERVE / READ
      Proceed unless CRITICAL. No SEAL required.
      Reversible. Low blast radius.
      Examples: read file, query state, fetch resource.

  C2  DRAFT / PROPOSE / BUILD
      Proceed unless CRITICAL. SEAL from arifOS if vault-write.
      Mostly reversible. Medium blast radius.
      Examples: write code, draft doc, prepare PR.

  C3  COMMIT / DEPLOY / EXECUTE
      Proceed if STABLE or better. SEAL from arifOS.
      Partially reversible. High blast radius.
      Examples: git commit, deploy service, run forge cycle.

  C4  PRODUCTION-DEPLOY / CROSS-ORG / DATA-MIGRATE
      Proceed only if OPTIMAL. DEFER if STABLE.
      ADVISORY_BLOCK if DEGRADED. BLOCK if CRITICAL.
      Largely irreversible. Federation-wide blast radius.
      Examples: production deploy, cross-org refactor, schema migrate.

  C5  IRREVERSIBLE / SOVEREIGN / VAULT-SEAL
      Proceed only if OPTIMAL + no chronic fatigue.
      BLOCK otherwise. Constitutional floor.
      Fully irreversible. Civilization-scale blast radius.
      Examples: vault seal, F13 ratification, irreversible delete.

## §2. MACHINE DECISION CLASSES (M1–M5)

The hosting machine has parallel decision classes. M5 yields to the
human. M4 yields to arifOS. The machine never exceeds human authority.

  M1  OBSERVE / READ-ONLY TOOL CALL
      Proceed unconditionally. No internal governance required.
      Examples: well_get_state, well_assess_reliability, well_trace_lineage.

  M2  CACHED / STATIC RESPONSE
      Proceed if machine_entropy ≤ 0.65. Skip live computation.
      Examples: well_get_health, well_machine_state (cached).

  M3  LIVE COMPUTATION / CONTEXT BUDGET CONSUMPTION
      Proceed if machine_entropy ≤ 0.40 AND budget_remaining >= 0.30.
      Examples: well_compute_metabolic_flux, well_assess_homeostasis.

  M4  CROSS-ORGAN CALL / FEDERATION-WIDE STATE
      Proceed only if machine_entropy ≤ 0.40 AND no federation floor violated.
      Yield to arifOS governance if any floor uncertain.
      Examples: well_attest_to_kernel, well_handoff_dignity_to_arifos.

  M5  IRREVERSIBLE / VAULT-WRITE / SEAL
      Yield ABSOLUTELY to human + arifOS governance.
      Machine NEVER self-authorizes M5.
      Examples: well_seal_vault, well_log_state (when SEVERITY=critical).

## §3. HUMAN × MACHINE COUPLING TABLE

  The routing table combines human readiness + machine readiness.
  The COUPLING VERDICT is the most restrictive of the two.

  ┌─────────┬──────────┬──────────┬──────────┬──────────┐
  │         │ OPTIMAL  │  STABLE  │ DEGRADED │ CRITICAL │
  │         │ (READY)  │          │          │          │
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

  YIELD = machine proceeds, defers to human authority
  HOLD  = machine pauses, escalates to arifOS or human
  BLOCK = action blocked, requires 888_HOLD to proceed

  *C5 + OPTIMAL: requires no chronic fatigue. Strictest gate.

## §4. ASYMMETRY (the bias direction)

The matrix is asymmetric by design. The human is sovereign.
The machine is the substrate. When the machine is degraded,
the machine yields — the human continues. When the human is
degraded, the human is blocked from irreversible action but
retains authority over observation, reflection, and self-statement.

The machine NEVER overrides the human's authority to:
  - speak about their own state
  - refuse a wellness reflection
  - override a DEGRADED signal with their own assessment
  - request a hold on the machine

The machine MAY:
  - refuse to execute a forge cycle that exceeds its capacity
  - yield to arifOS for constitutional uncertainty
  - surface a dignity_leakage advisory

The asymmetry is the dignity floor in operational form.

## §5. THE BRIDGE TO ARIFOS

When the routing matrix produces HOLD or BLOCK:
  → escalate to arifOS kernel via well_attest_to_kernel
  → arifOS applies F1–F13 floors
  → arifOS issues SEAL/SABAR/VOID verdict
  → if SEAL → execution proceeds
  → if SABAR → hold, wait for human
  → if VOID → refuse

WELL does not adjudicate. WELL routes. arifOS judges. Arif decides.

DITEMPA BUKAN DIBERI — Routing is the chemistry of authority.
"""


def register(mcp: Any) -> List[str]:
    """Register the decision/classes resource with FastMCP."""

    @mcp.resource("well://decision/classes")
    def decision_classes() -> str:
        """The C1–C5 × M1–M5 routing matrix."""
        return DECISION_CLASSES_TEXT + DECISION_CLASSES_META

    return ["well://decision/classes"]
