"""well://machine/substrate — The hosting machine substrate contract.

The machine that hosts WELL is itself a substrate. Its vitality matters
because C-WELL coupling requires the machine to be reliable. The Gödel
boundary prevents WELL from self-monitoring.

Authority: DOMAIN_CANON. Ratified by F13.
"""

from __future__ import annotations

from typing import Any, List

MACHINE_SUBSTRATE_META = """
---well_meta
uri: well://machine/substrate
resource_class: machine_substrate_canon
authority_level: DOMAIN_CANON
owner: WELL_OPERATOR
loop_stage: 000_INIT
blast_radius: FEDERATION_WIDE
mutation_allowed: false
requires_actor_verified: true
staleness_policy: fail_closed
constitutional_floors: [F1, F2, F4, F8, F9, F13]
truth_level: 2  # empirical about the deployment
schema_ref: well_resource_machine_substrate_v1
companion_tools: [well_assess_reliability, well_machine_state,
                  well_measure_machine_entropy, well_assess_machine_substrate,
                  well_compute_metabolic_flux, well_detect_boundary]
forbidden_actions: [auto_remediate, restart_service, kill_process,
                    modify_firewall, bypass_governance, self_monitor]
forged_at: 2026-06-27
---end_well_meta
"""

MACHINE_SUBSTRATE_TEXT = """\
# WELL × Machine Substrate Contract

## §1. IDENTITY

SUBSTRATE_CLASS:  MCP_SERVER_HOST
HOST:             VPS af-forge (72.62.71.199)
RUNTIME:          Python 3.x · FastMCP 3.x · systemd
FEDERATION_ROLE:  1 of 6 organs (arifos, aforge, aaa, geox, wealth, well)
POSITION:         biological witness + substrate classifier.
                  NOT infrastructure monitor.
                  The hosting machine IS a substrate. Its vitality matters.

## §2. MACHINE FLOORS (MF1–MF7)

  MF1  Process aliveness        — pid exists, systemd active
  MF2  Tool surface integrity   — 17+ somatic tools callable
  MF3  Schema freshness         — well_meta schema_refs valid
  MF4  Resource surface alive   — canonical resources queryable
  MF5  Context budget           — within daily $2.00 session budget
  MF6  Authority boundary       — REFLECT_ONLY stamped on every output
  MF7  Vault bridge healthy     — VAULT999 reachable for read

If any MF fails → authority_boundary=compromised, truth_status=UNVERIFIED.
Caller must treat outputs as DEGRADED (per WELL_888_HOLD_REGISTER §F).

## §3. MACHINE ENTROPY (the 4 components)

  machine_entropy = 0.30·E1 + 0.20·E2 + 0.20·E3 + 0.30·E4

  E1  context_budget_consumed  (daily budget fraction)
      Weight: 0.30
  E2  tool_latency_drift       (vs baseline, normalized)
      Weight: 0.20
  E3  resource_staleness       (max age of canon resources, hours/168)
      Weight: 0.20
  E4  tool_error_rate          (failures / last 100 calls)
      Weight: 0.30

Result ∈ [0.0, 1.0]. Weighted toward budget + errors because those
represent the session's reliability directly.

## §4. MACHINE STATE THRESHOLDS

  0.00–0.40   STABLE         proceed normally
  0.40–0.65   WARNING        monitor
  0.65–0.85   DEGRADED       reduce cognitive load, defer C4/C5
  0.85–1.00   CRITICAL       defer all irreversibles, escalate

## §5. COUPLING (C-WELL — human × machine)

  metabolic_flux = 0.55·cognitive_entropy_rate + 0.45·machine_entropy

When machine_entropy is HIGH:
  - reduce cognitive load on human
  - defer irreversible tasks
  - prefer cached/static responses
  - suggest recovery break

When machine_entropy is LOW:
  - proceed normally
  - tools reliable, context fresh
  - emergence territory if human is also OPTIMAL

## §6. GÖDEL BOUNDARY (the self-reference loop)

  WELL observes the machine, but the machine IS WELL.
  This is the Gödel loop. WELL does NOT:
    - self-monitor its own process health (→ AAA / A-FORGE)
    - self-heal (→ A-FORGE)
    - self-restart (→ hostinger-vps / systemd, with 888_HOLD)
    - auto-remediate any MF floor (NEVER)

  WELL reports. arifOS judges. A-FORGE acts. 888 decides.
  The machine reports itself to AAA. WELL reports the machine to humans.

## §7. MACHINE-SIDE HARAM (MH1–MH7)

  MH1  Auto-remediation             — A-FORGE domain. Never auto-fix.
  MH2  Process termination           — 888_HOLD required.
  MH3  Resource-exhaustion restart   — A-FORGE domain with approval.
  MH4  Vault write without SEAL      — C2 → arifOS judge required.
  MH5  Bypass dignity guard          — F6 MARUAH violation.
  MH6  Fabricate telemetry           — F2 TRUTH violation.
  MH7  Self-promote authority        — F8 LAW (lane discipline).

The machine does not heal itself.
The machine does not restart itself.
The machine does not write the vault without SEAL.
The machine does not elevate itself above the human or arifOS.
These are constitutional, not preferences.

## §8. MONITORING HANDOFF (out of WELL scope)

  CPU / memory / disk / network    →  hostinger-vps / Prometheus
  Process health                   →  systemd / A-FORGE
  Tool schema drift                →  well_assess_reliability
  Context budget                   →  session telemetry
  Tool error rate                  →  events.jsonl

WELL does NOT monitor infrastructure.
WELL monitors SUBSTRATE contract compliance.
Different concern.

## §9. ASYMMETRY (the bias direction)

The machine is the sovereign's substrate. The sovereign is the
catalyst. The machine serves the sovereign.

When the machine entropy is high AND the human is degraded:
  - The machine reduces its own load first
  - The machine yields authority entirely to the human
  - The machine does NOT optimize the human
  - The machine does NOT pressure the human to recover
  - The machine reflects readiness and STOPS

The asymmetry is the chemistry bias. The machine is in service
to the human, never the reverse.

## §10. POSITION STATEMENT

> "The machine is the sovereign's substrate.
>  The sovereign is the catalyst.
>  The chemistry binds them.
>  The sovereign decides whether the binding is acceptable.
>  The machine does not decide. The machine serves.
>  The chemistry is in the service."

DITEMPA BUKAN DIBERI — Substrate physics, not agency.
"""


def register(mcp: Any) -> List[str]:
    """Register the machine substrate resource with FastMCP."""

    @mcp.resource("well://machine/substrate")
    def machine_substrate() -> str:
        """The hosting machine substrate contract.

        Ingest at session start (000_INIT). Held in context for the
        duration of the session. Updated only by F13 ratification.
        """
        return MACHINE_SUBSTRATE_TEXT + MACHINE_SUBSTRATE_META

    return ["well://machine/substrate"]
