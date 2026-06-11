# WELL — Human Readiness Organ

WELL is the **reflect-only** vitality organ. It observes and reports human readiness — sleep, fatigue, stress, cognitive clarity, dignity — so irreversible decisions are never made by or about a depleted human. It reflects. It warns. It **never** decides.

## Repo identity

- **Path:** `/root/WELL`
- **Port:** 18083 | **Domain:** `well.arif-fazil.com/mcp`
- **Systemd:** `well.service`
- **Language:** Python 3.12

## Build, test, run

```bash
pip install -e .
pytest tests/ -q --tb=short          # test suite
python server.py                      # FastMCP server on :18083

# Redeploy
make forge && systemctl restart well
```

## Key files

| Path | Role |
|------|------|
| `server.py` | Single-file FastMCP kernel (~12K lines, 45 tools) |
| `state.json` | Sovereign biometric state (F13 territory — only Arif writes) |
| `gate/well_gate.py` | Pre-JUDGE biological readiness gate |
| `gate/dignity_shadow.py` | Dignity preservation shadow layer |
| `tests/test_metabolic_contract.py` | Metabolic contracts |
| `tests/test_sovereign_entropy.py` | Sovereignty entropy checks |

## 13 Canonical WELL signals

sleep_debt, hrv_status, cognitive_clarity, stress_load, emotional_state,
decision_fatigue, accumulated_session_fatigue, chronic_fatigue,
dignity_preservation, reductionism_risk, coercion_signals,
energy_level, mission_clarity

## CRITICAL: state.json is F13 territory

`state.json` contains Arif's biometric state. Only Arif can call `well_log_state` with real readings. Do NOT fabricate, mock, or fill in this file. Current state is ~900h stale — this is expected; WELL correctly holds until real readings are injected.

## Conventions

- REFLECT_ONLY — no tool may issue a strategic judgment or authorization.
- All output is advisory. WELL feeds evidence to arifOS; it never self-seals.
- REPO= commit trailer required: `REPO=well`
- Tags: `vYYYY.MM.DD` only.
