# FEDERATION HOOKS — WELL → Federation

> **Forged:** 2026-06-17 by FORGE (000Ω) on behalf of Arif (F13 SOVEREIGN)
> **Authority:** REFLECT_ONLY — WELL signals, arifOS judges.
> **Scope:** This file is the canonical contract for WELL's three
> explicit federation handoff tools, plus the active attestation
> heartbeat.  Referenced by `FEDERATION_CONTRACT.md` and the
> 13-signal coverage report.

---

## 0. The Iron Rules

1. **WELL never emits a constitutional verdict.** It emits `signal`.
   `verdict: SEAL/HOLD/VOID/SABAR/PASS/FAIL` belongs to arifOS 888_JUDGE.
2. **WELL never escalates to 888_HOLD automatically.** The hook returns a
   `fail_mode` field.  The operator (F13) decides what to do next.
3. **All hooks are fail-open.** If the peer is unreachable, the hook
   returns `federation_unavailable` with the packet preserved.  The
   caller's tool surface never crashes because a peer is down.
4. **All hooks have a 2.0s timeout** (configurable via
   `WELL_FED_TIMEOUT_S` env var).  A slow peer cannot hang WELL.
5. **Authority: REFLECT_ONLY.** WELL is the mirror.  It does not coerce,
   authorise, allocate, or adjudicate.

---

## 1. `well_handoff_dignity_to_arifos()` — S12 → arifOS 888_JUDGE

### Purpose
The 13-signal coverage report flagged S12 (social_dignity_consent) as
**MISSING** with a handoff recommended to **arifOS 888_JUDGE**.  This
tool implements that handoff explicitly.

### Signature
```python
def well_handoff_dignity_to_arifos(
    coercion_signals: list[str] | None = None,
    dignity_preservation: float | None = None,   # 0.0–1.0
    reductionism_risk: float | None = None,      # 0.0–1.0
    signal: str = "dignity_leakage_under_review",
    ctx: Context | None = None,
) -> dict[str, Any]
```

### What it does
1. Builds a dignity packet with the supplied signals.
2. Calls arifOS `arif_judge_deliberate(mode="judge", action_class="dignity_breach_signal")`
   via the standard MCP initialize → tools/call handshake.
3. Returns the arifOS receipt (which contains the **verdict** — emitted
   by arifOS, not by WELL).
4. On failure: returns `fail_mode: "federation_unavailable"` with the
   packet preserved.

### Output contract
```json
{
  "ok": true,
  "signal": "dignity_leakage_under_review",
  "federation": "arifos",
  "arifos_session_id": "<id>",
  "arifos_receipt": { /* arifOS 888_JUDGE verdict + reasoning */ },
  "packet": { /* the dignity packet WELL sent */ },
  "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT"
}
```

### When to use
- When the operator (or AAA cockpit) detects coercion / objectification
  / consent breach in a peer or system message.
- When `well_guard_dignity` returns a non-nominal signal.
- NOT to be called for routine status — the handoff is per-incident.

### When NOT to use
- For medical/psychiatric symptoms → `well_medical_boundary` instead.
- For financial distress → `well_handoff_livelihood_to_wealth` instead.
- For routine federation liveness → `well_get_health(mode="status")`.

---

## 2. `well_handoff_livelihood_to_wealth()` — S13 → WEALTH

### Purpose
The 13-signal coverage report flagged S13 (environment_livelihood) as
**MISSING** with a handoff recommended to **WEALTH** (cashflow_status,
duty_load, runway).  This tool implements that handoff explicitly.

### Signature
```python
def well_handoff_livelihood_to_wealth(
    duty_load: float | None = None,
    cashflow_status: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]
```

### What it does
1. Calls WEALTH `wealth_personal_finance(mode="summary", owner="arif")`
   to pull cashflow/runway evidence.
2. Composes a livelihood packet that includes the operator's readiness
   frame (`duty_load`, self-reported `cashflow_status`) plus the
   WEALTH evidence.
3. Returns the WEALTH receipt + the composed packet.
4. On failure: returns `fail_mode: "federation_unavailable"` with the
   readiness frame preserved.

### Output contract
```json
{
  "ok": true,
  "signal": "livelihood_signal_composed",
  "federation": "wealth",
  "wealth_session_id": "<id>",
  "wealth_receipt": { /* WEALTH compute result */ },
  "packet": {
    "readiness_frame": { "duty_load": ..., "operator_id": "arif" },
    "wealth_evidence": { /* nested WEALTH output */ }
  }
}
```

### When to use
- When S13 (livelihood) needs to be evaluated.
- When operator (or AAA) is asking "can I afford to keep going?"
- When MSS / career transition signals are active.
- NOT to be called for routine status.

### When NOT to use
- For S11 emotional/stress signals — WELL can assess directly.
- For capital allocation decisions — that is WEALTH + arifOS 888_JUDGE,
  not WELL.

---

## 3. `well_attest_to_kernel()` — WELL → arifOS organ_attest

### Purpose
The external `organ_heartbeat_daemon` polls WELL `/health` (one-way,
read-only).  This tool performs the **active** half: WELL posting its
state to arifOS so the kernel's organ registry stays current.

### Signature
```python
def well_attest_to_kernel(
    ctx: Context | None = None,
) -> dict[str, Any]
```

### What it does
1. Reads current WELL state (`verdict_local`, `well_score`, `freshness`).
2. Calls arifOS `arif_organ_attest(organ_id="WELL", attestation=...)`
   with the full state envelope.
3. Returns the arifOS receipt (the kernel's response to the attestation).
4. On failure: returns `fail_mode: "federation_unavailable"`.

### Output contract
```json
{
  "ok": true,
  "organ": "WELL",
  "federation": "arifos",
  "arifos_session_id": "<id>",
  "arifos_receipt": { /* arifOS attestation response */ },
  "attestation": {
    "organ_id": "WELL",
    "identity_hash": "<sha256>",
    "authority": "REFLECT_ONLY",
    "final_authority": "ARIF",
    "verdict_local": "WELL_HOLD" | "...",
    "well_score": null | <float>,
    "freshness": "FRESH" | "STALE" | "EXPIRED" | "VOID",
    "ts": "<ISO 8601>"
  }
}
```

### When to use
- When the operator wants to manually re-attest (e.g., after
  biometric_inject.sh writes new state).
- When AAA cockpit wants to "ping" the kernel about WELL.
- When a handoff chain needs a fresh attestation receipt.

### When NOT to use
- For routine federation liveness — the heartbeat daemon handles that.
- From a tight loop — the daemon's 30s poll is the right cadence.

---

## 4. Pre-existing Federation Surface (unchanged)

These were already wired in WELL canonical server.py and remain
authoritative:

| Tool / Route | Direction | Purpose |
|--------------|-----------|---------|
| `well_get_packet(target=...)` | WELL → peer | Generic biological readiness packet |
| `well_get_health(mode="status"|"connect"|"handoff"|"manifest")` | WELL ↔ federation | Gateway modes |
| `well_coupled_readiness()` | internal | Human-machine coupled risk |
| `_build_arifos_packet()` | internal | Canonical handoff packet builder |
| `well_medical_boundary` | internal | Non-diagnosis guard |
| `well_13_signal_coverage` | internal | DREAM ENGINE coverage audit |
| External: `organ_heartbeat_daemon` polls `/health` | → WELL | One-way health probe |
| External: `well_agent_telemetry.py` cron | bidirectional | Hermes-style telemetry |

---

## 5. Schema and Audit Trail

- **Schema version:** WELL federation hooks v2026.06.17
- **Forged by:** FORGE (000Ω) on behalf of Arif (F13 SOVEREIGN)
- **Receipt:** `/root/forge_work/well-federation-fix-2026-06-17.md`
- **Vault seal:** pending (operator action — 888_HOLD)

---

**DITEMPA BUKAN DIBERI — Forged, not given.  Federation is composed, not assumed.**
