"""well://transport/loop — The 5-stage reaction loop contract.

Every reflection WELL emits has been processed through this loop.
The loop is the chemistry's reaction sequence. It is NOT AGI.

Authority: OPERATIONAL_CANON.
"""

from __future__ import annotations

from typing import Any, List

TRANSPORT_LOOP_META = """
---well_meta
uri: well://transport/loop
resource_class: transport_loop_contract
authority_level: OPERATIONAL_CANON
owner: WELL_OPERATOR
loop_stage: 000_INIT (canonical reference) — invoked at 111–999
blast_radius: FEDERATION_WIDE
mutation_allowed: false
requires_actor_verified: false
staleness_policy: cache
constitutional_floors: [F1, F2, F4, F6, F11]
truth_level: 2
schema_ref: well_resource_transport_loop_v1
companion_modules: [well_mcp.transport.{ingress,encode,metabolize,
                                          judge,egress}]
forged_at: 2026-06-27
---end_well_meta
"""

TRANSPORT_LOOP_TEXT = """\
# WELL × 5-Stage Transport Loop

## §1. WHY A LOOP

Every signal that enters WELL must be processed through the same
reaction sequence. Without the loop, the chemistry is inconsistent
and the sovereign cannot trust the mirror.

The loop is NOT a workflow. The loop is the reaction mechanism.
The reaction produces a stamped reflection. The sovereign decides
whether to act on the reflection.

## §2. THE 5 STAGES (the chemistry sequence)

  ┌────────────────────────────────────────────────────────────┐
  │                                                            │
  │  1. INGEST   ← external signal lands                      │
  │                freshness stamped                           │
  │                source recorded                             │
  │                signal_id generated                         │
  │                                                            │
  │  2. ENCODE   ← substrate canon resolved                   │
  │                dignity floor applied FIRST                 │
  │                freshness decay computed                    │
  │                decision class mapped (C1–C5 / M1–M5)      │
  │                handoff candidates identified               │
  │                                                            │
  │  3. METABOLIZE ← fluxes computed                          │
  │                   machine_entropy (4 components)           │
  │                   cognitive_entropy_rate (human)          │
  │                   metabolic_flux weighted + sigmoid       │
  │                   coupling_state assessed                  │
  │                   readiness verdict proposed               │
  │                                                            │
  │  4. JUDGE   ← yielded to arifOS for F1–F13 floors         │
  │                floor_status computed per floor            │
  │                if CRITICAL → escalate to 888_JUDGE         │
  │                if HOLD → return SABAR                      │
  │                if SEAL → proceed                           │
  │                if VOID → refuse + return reason            │
  │                                                            │
  │  5. EGRESS  ← stamped reflection emitted                  │
  │                { signal_id, value, freshness,              │
  │                  floor_status, source, hand_off,          │
  │                  coupling_state, readiness_verdict }      │
  │                sovereign observes                          │
  │                sovereign decides next                      │
  │                                                            │
  └────────────────────────────────────────────────────────────┘

## §3. STAGE 1 — INGEST (witness)

  Module:    well_mcp.transport.ingress
  Function:  stamp_ingress(payload) -> WellStamp.partial
  Cost:      < 5 ms typical, < 50 ms under load
  Authority: REFLECT_ONLY, never mutates state

What it does:
  - receives a payload (signal, tool call, federation message)
  - generates signal_id (uuid4)
  - records source (organ_id, tool_name, actor_id)
  - stamps timestamp (now, UTC)
  - records freshness_raw (how stale was the underlying signal)
  - returns partial stamp

## §4. STAGE 2 — ENCODE (classify)

  Module:    well_mcp.transport.encode
  Function:  stamp_encode(WellStamp.partial, canon) -> WellStamp.encoded
  Cost:      < 10 ms typical
  Authority: REFLECT_ONLY, applies dignity floor FIRST

What it does:
  - applies dignity floor (consent_verified, coercion_signals,
    reductionism_risk, dignity_preservation >= 0.70)
  - resolves substrate canon (H / M / G)
  - maps task to decision class (C1–C5 or M1–M5)
  - computes freshness_decayed from freshness_raw + age
  - identifies handoff candidates (WEALTH, GEOX, HEART, arifOS)
  - returns encoded stamp

## §5. STAGE 3 — METABOLIZE (reflect)

  Module:    well_mcp.transport.metabolize
  Function:  stamp_metabolize(WellStamp.encoded) -> WellStamp.metabolized
  Cost:      20–200 ms typical, 500 ms ceiling
  Authority: REFLECT_ONLY, READ-ONLY substrate slice

What it does:
  - reads machine_entropy (E1–E4 components) from well_assess_machine_substrate
  - reads cognitive_entropy_rate from well_assess_homeostasis
  - computes metabolic_flux = 0.55·human + 0.45·machine
  - computes coupling_state (σ(human × machine × governance))
  - proposes readiness_verdict (READY / DEGRADED / CRITICAL / STABLE / OPTIMAL)
  - returns metabolized stamp

## §6. STAGE 4 — JUDGE (attest)

  Module:    well_mcp.transport.judge
  Function:  stamp_judge(WellStamp.metabolized) -> WellStamp.judged
  Cost:      arifOS call (variable, 50–500 ms typical)
  Authority: YIELDS to arifOS. WELL NEVER adjudicates F1–F13.

What it does:
  - computes floor_status per F1–F13 (PASS / HOLD / VOID)
  - calls arif_judge with all evidence
  - receives verdict (SEAL / SABAR / HOLD / VOID)
  - if CRITICAL → escalate to 888_JUDGE
  - if HOLD → return SABAR + reason
  - if VOID → refuse + return reason
  - if SEAL → proceed
  - returns judged stamp

## §7. STAGE 5 — EGRESS (yield)

  Module:    well_mcp.transport.egress
  Function:  stamp_egress(WellStamp.judged) -> WellStamp.final
  Cost:      < 5 ms
  Authority: REFLECT_ONLY, sovereign observes output

What it does:
  - assembles final stamp with all stages' outputs
  - emits reflection to caller (well_* tool output, resource read, prompt invocation)
  - includes signal_id, value, freshness, floor_status, source, hand_off
  - does NOT log to vault (vault is arifOS responsibility)
  - does NOT trigger downstream actions (handoff is informational only)
  - returns final stamp to sovereign

## §8. THE WELL STAMP (the artifact)

  Every well_mcp reflection produces a WellStamp with shape:

  {
    "signal_id": uuid4,
    "value": <substrate-dependent scalar/dict>,
    "freshness": {
      "raw_hours": float,
      "decayed_hours": float,
      "confidence": "HIGH" | "MEDIUM" | "LOW" | "STALE" | "VOID"
    },
    "floor_status": {
      "F1_amanah": "PASS" | "HOLD" | "VOID",
      "F2_truth": "PASS" | "HOLD" | "VOID",
      "F4_clarity": "PASS" | "HOLD" | "VOID",
      "F6_maruah": "PASS" | "HOLD" | "VOID",
      "F8_law": "PASS" | "HOLD" | "VOID",
      "F11_audit": "PASS" | "HOLD" | "VOID",
      "F13_sovereign": "PASS" | "HOLD" | "VOID"
    },
    "decision_class": "C1" | ... | "C5" | "M1" | ... | "M5",
    "readiness_verdict": "READY" | "DEGRADED" | "CRITICAL" | "STABLE" | "OPTIMAL",
    "machine_entropy": float,
    "cognitive_entropy_rate": float,
    "metabolic_flux": float,
    "coupling_state": float,
    "source": {
      "organ": str, "tool": str, "actor": str, "ts": iso8601
    },
    "hand_off": [organs_with_signals_to_act_on],
    "loop_trace": [list_of_stages_executed]
  }

## §9. ERRORS (what to return when chemistry breaks)

  Any stage may fail. When it does:
  - INGRESS_FAIL  → return WellStamp.error with stage="ingress"
  - ENCODE_FAIL   → return WellStamp.error with stage="encode"
  - METABOLIZE_FAIL → return WellStamp.error with stage="metabolize"
  - JUDGE_FAIL    → return WellStamp.error with stage="judge", escalate 888
  - EGRESS_FAIL   → return WellStamp.error with stage="egress"

Errors are REFLECT_ONLY failures. They NEVER mutate state.
They NEVER execute forge cycles. They NEVER seal the vault.
They report the failure to the sovereign and wait.

## §10. POSITION STATEMENT

> "The loop is not the intelligence.
>  The loop is the reaction sequence.
>  Intelligence emerges when the sovereign observes
>  the loop's reflections and decides.
>  Without the sovereign, the loop is just chemistry.
>  With the sovereign, the chemistry yields."

DITEMPA BUKAN DIBERI — Reaction sequence, not agency.
"""


def register(mcp: Any) -> List[str]:
    """Register the transport loop resource with FastMCP."""

    @mcp.resource("well://transport/loop")
    def transport_loop() -> str:
        """The 5-stage reaction loop contract."""
        return TRANSPORT_LOOP_TEXT + TRANSPORT_LOOP_META

    return ["well://transport/loop"]
