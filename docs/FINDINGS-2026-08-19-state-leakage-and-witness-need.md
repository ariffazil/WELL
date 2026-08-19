# FINDINGS: state.json test-fixture leakage + WITNESS requirement

> **Forged:** 2026-08-19 by Kimi (FI-008) under sovereign instruction "go auto execution and zen the machine and substrate and tools and observability and measurement"
> **Status:** FINDING · Not fixed (T3 work requires PR)
> **Severity:** P0 (the vitality gate is reading a test fixture as production data)
> **Scope:** `/root/WELL/vitality_gate.py` + `/root/WELL/state.json` + the WITNESS design at `/root/WELL/contracts/design/WITNESS-INDEPENDENT-OBSERVER.md`

---

## TL;DR

The production `state.json` on `/root/WELL` is currently the test fixture from `tests/test_well_state_honesty.py`. The vitality gate reads this file as if it were real biometric data and produces a false `H_WELL=READY` verdict. The honesty test that should catch this doesn't cover the gate's code path. The tactical fix is a three-line change in `vitality_gate.py:466` to call the existing `_state_is_insufficient()` function from `server.py` and respect the result. The structural fix is **WITNESS Phase 1** — the design exists at `/root/WELL/contracts/design/WITNESS-INDEPENDENT-OBSERVER.md`, was forged 2026-07-21, and is marked "DESIGN · Not built." Building it would have caught this bug and would close the self-referential trap the design doc names as the root cause.

---

## Finding 1 — `state.json` is the test fixture (P0, observed)

`/root/WELL/state.json` (mtime `2026-08-19 09:30:12 +0800`, today) contains:

```json
{
  "timestamp": "2026-04-30T00:00:00+00:00",
  "operator_id": "arif",
  "metrics": {"cognitive": {"clarity": 10, "decision_fatigue": 10.0}},
  "well_score": 0,
  "floors_violated": [],
  "backend_status": "STABLE",
  "last_successful_read": "2026-04-30T00:00:00+00:00",
  "last_successful_write": "2026-04-30T00:00:00+00:00",
  "state_file_access": "PASS",
  "vault_access": "OK",
  "test_contamination": "NO",
  "contamination_quarantined": false,
  "confidence": "HIGH",
  "freshness": "FRESH",
  "environment": "TEST",
  "telemetry_confidence": "HIGH",
  "reason": "Mocked healthy state for test session",
  "safe_mode": "off",
  "arif_decision_required": false,
  "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT"
}
```

This is the exact state object constructed in `tests/test_well_state_honesty.py:30-38` (`test_mocked_test_state_is_insufficient`). The test is supposed to `monkeypatch` `server.STATE_PATH` to `tmp_path` so the production file is untouched. The production file was overwritten anyway. mtime is today.

The file lies in five fields:

- `freshness: "FRESH"` — but the timestamp is 2026-04-30, 111 days old
- `confidence: "HIGH"` — but the file is a test mock
- `test_contamination: "NO"` — but `reason` says "Mocked healthy state for test session"
- `environment: "TEST"` — the file itself says it's a test
- `well_score: 0` — but the `reason` says "Mocked healthy state" (the score contradicts the framing)

---

## Finding 2 — gate doesn't check `environment` (P0, root cause)

`/root/WELL/vitality_gate.py:466-513` (`assess_h_well`) reads:

- `state.get("truth_status", "UNVERIFIED")`
- `state.get("timestamp")`
- `state.get("well_score")`

It does **not** read `state.get("environment")`, `state.get("reason")`, or `state.get("test_contamination")`. The default `truth_status` is `"UNVERIFIED"`, which falls into the `verified_telemetry` branch at line 508-513:

```python
else:
    h_state = "READY"
    h_rank = 4
    evidence_parts.append("verified_telemetry")
    uncertainty = 0.1
```

So the gate reads the test fixture, doesn't see `environment: "TEST"`, defaults `truth_status` to `"UNVERIFIED"`, and produces `h_state=READY, h_rank=4`. The `H_WELL: "READY"` verdict observed in this session is the test fixture being laundered into production.

The honesty test in `tests/test_well_state_honesty.py` asserts that test mocks → insufficient. But the test imports `_state_is_insufficient` from `server.py`, not from `vitality_gate.py`. The gate uses its own state-reading code path that does not call `_state_is_insufficient`.

**The honesty test doesn't cover the gate.** That is the gap the live observation exposed.

### Tactical fix (3 lines)

`vitality_gate.py:466` should call `_state_is_insufficient` (or mirror its logic) and respect the result. Specifically: at the top of `assess_h_well`, before any ranking, check `state.get("environment") == "TEST"` or `state.get("truth_status") == "TEST"` or any "Mocked" prefix on `reason`. If any fires, return `h_state="UNKNOWN", h_rank=0, evidence="test_fixture_detected"`.

This is T3 work — modifying production code in the constitutional-readiness organ. Requires a PR and explicit F13.

---

## Finding 3 — `well_check_repair` bypasses the gate (P1, observed)

`/root/WELL/server.py:15341-15404` (`well_check_repair`) calls `well_777_forge` (line 15351), not `vitality_gate`. The `readiness.human: "OPTIMAL"` field observed in this session came from `well_777_forge`'s own readiness computation, which is unrelated to the `vitality_gate.H_WELL` field.

This is a separate bug from the state.json leakage. Even after the gate is fixed, `well_check_repair` will still report a different `H_WELL` than `well_validate_vitality` for the same substrate window. The non-determinism is real and the fix is one of:

- Route `well_check_repair` through `vitality_gate` and read `H_WELL` from there, OR
- Remove the redundant `readiness.human` field from `well_check_repair` and have it return only repair-allowlist data

---

## Finding 4 — substrate sensor honesty field contradiction (P2, observed)

`/root/WELL/sensors/machine_human_substrate.py:285-292` produces:

```python
"honesty": {
    "source_type": "MACHINE_TELEMETRY",
    "is_sensor_verified": True,
    "is_self_report": False,
    "is_mock_or_test": False,
    "is_stale": False,
    "banner": "UNKNOWN — machine telemetry sensor pipeline not deployed. "
              "Install Prometheus Node Exporter for live substrate signals.",
}
```

`is_sensor_verified: True` and `is_stale: False` while the banner explicitly says the sensor pipeline is **not deployed**. This is a field-level contradiction inside a single output dict. The fix: when the banner says pipeline-not-deployed, `is_sensor_verified` must be `False` and `is_stale` must be `True`.

---

## Finding 5 — WITNESS design exists, is "Not built," and would have caught Findings 1 and 3 (P1 deliverable)

`/root/WELL/contracts/design/WITNESS-INDEPENDENT-OBSERVER.md` (forged 2026-07-21, "DESIGN · Not built") describes a separate-process observer that cross-checks WELL's claims against ground truth. The design estimates Phase 1 at P1 effort and ~200 lines of Python plus a systemd unit, and projects AGI substrate readiness moving from ~15 to ~35 once built.

WITNESS would have caught **Finding 1** by:

- Reading `/root/WELL/state.json` independently
- Checking `environment`, `reason`, `test_contamination` fields
- Flagging the divergence from expected production state and proposing `INSUFFICIENT_DATA` until restored

WITNESS would have caught **Finding 3** by:

- Reading both `well_validate_vitality` and `well_check_repair` outputs
- Cross-checking the `H_WELL` fields agree
- Flagging the divergence and proposing a 888_HOLD

The self-referential trap the design names is exactly the bug observed: "WELL runs on the substrate it governs. A substrate that can modify itself can modify its own WELL. The governor and governed sharing a body means the governed can edit the governor." The test fixture on production disk is a soft form of that trap (test code path writing to production read path). The WITNESS independent observer is the architectural answer.

---

## Recommended actions, ordered

| Pri | Action | Tier | Est. |
|---|---|---|---|
| **P0** | Fix `vitality_gate.py:466` to call `_state_is_insufficient` and respect the result | T3 (PR) | 3 lines |
| **P0** | Restore `state.json` to an honest empty production state. Sovereign decision required: what does "real" mean for an empty state? Honest default: `{ truth_status: "INSUFFICIENT_DATA", environment: "PROD", well_score: null, reason: "no production state yet" }` | T2 (announce + 10s veto) | 1 file |
| **P1** | Build WITNESS Phase 1 per the design doc | T3 (PR) | ~200 LOC + systemd unit |
| **P1** | Route `well_check_repair` through `vitality_gate`, or remove its redundant `readiness.human` field | T3 (PR) | ~10 lines |
| **P2** | Fix `machine_human_substrate.py:285` honesty-field consistency | T3 (PR) | 5 lines |
| **P2** | Add the property tests in `tests/test_vitality_gate_environment_safety.py` (this commit) | T1 (in this commit) | 4 tests |
| **P3** | Phase 1 falsifiability log (#19): append every gate verdict against subsequent outcomes to `/root/VAULT999/well/falsifiability.jsonl` | T1 (this commit, doc + script) | ~50 LOC |

The two P0 items cannot both be done by the agent autonomously. P0-1 is a T3 code change. P0-2 is a T2 mutation to a production config file, but the sovereign must decide what "real" means for an empty state.

---

## F2 evidence (sources)

- `/root/WELL/state.json` — read directly, mtime `2026-08-19 09:30:12 +0800`
- `/root/WELL/tests/test_well_state_honesty.py:30-38` — read directly, the test fixture template
- `/root/WELL/vitality_gate.py:466-513` — read directly, the code path that produces the false READY verdict
- `/root/WELL/server.py:15341-15404` — read directly, `well_check_repair` bypasses the gate
- `/root/WELL/sensors/machine_human_substrate.py:285-292` — read directly, honesty field contradiction
- `/root/WELL/contracts/design/WITNESS-INDEPENDENT-OBSERVER.md` — read directly, the design that would have caught this
- `/root/WELL/contracts/WELL_MANIFEST.json` — read directly, autonomy bands and tool surface
- `/root/AAA/AGENTS-AUTONOMY.md` — read directly, autonomy tier doctrine
- `/root/WELL/H1_MONOLITH_CUTOVER.md` — read directly, monolith-vs-modular cutover plan

DITEMPA BUKAN DIBERI ⚒️
