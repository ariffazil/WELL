<!-- SOT-MANIFEST
owner: Arif
last_verified: 2026-07-04
valid_from: 2026-06-14
valid_until: 2026-08-03
confidence: high
scope: /root/WELL
epistemic_status: SOURCE_OF_TRUTH
-->

# INVARIANTS.md — WELL

> Human Substrate & Metabolic State — Immutable boundaries for the WELL organ.

## Canonical Branch

`main`

## Live Endpoints

| Endpoint | Port | Status |
|----------|------|--------|
| MCP | `http://127.0.0.1:18083/mcp` | ✅ LIVE — `well.service` active |
| Health (public) | `https://well.arif-fazil.com/health` | ✅ LIVE |
| Health (local) | `http://127.0.0.1:18083/health` | ✅ LIVE |

## Required Health Checks

- `curl http://localhost:18083/health` must return `200` with `tool_count: 22`
- `python -m pytest tests/ -q --tb=short` must pass before any deployment
- `python test_well.py` must pass (legacy audit suite)

## Change Coupling

These files must change together:

- `server.py` — canonical FastMCP server (~15,755 lines, 72 `@mcp.tool` decorated helpers)
- `gate/well_gate.py` — pre-JUDGE biological readiness mirror
- `gate/dignity_shadow.py` — dignity shadow scoring
- `test_well.py` — plain-Python audit suite

## Canonical Tool Surface

**22 somatic MCP tools** across 4 substrate types plus federation/ZEN/diagnostic helpers:

| Substrate | Tools | Purpose |
|-----------|-------|---------|
| H-WELL | `well_assess_livelihood`, `well_guard_dignity`, `well_medical_boundary`, `well_assess_sovereign_entropy`, `well_validate_vitality`, `well_assess_homeostasis` | Human wellness, role, meaning, dignity |
| M-WELL | `well_assess_reliability`, `well_check_repair`, `well_health_check` | Machine health, entropy rate, repair |
| C-WELL | `well_assess_metabolism`, `well_compute_metabolic_flux`, `well_trace_lineage`, `well_measure_gradient` | Coupled state regulation |
| G-WELL | `well_classify_substrate`, `well_detect_boundary` | Governance gradient sensing |
| F-Ω / ZEN / Diagnostic | `well_handoff_dignity_to_arifos`, `well_handoff_livelihood_to_wealth`, `well_attest_to_kernel`, `well_classify_state`, `well_readiness`, `well_13_signal_coverage`, `well_registry_status` | Federation handoff, ZEN verdict, diagnostics |

## Forbidden Stale Assumptions

- ❌ WELL is NOT "not deployed" — it is live on bare-metal systemd (port 18083)
- ❌ Port 8083 is a legacy/stale port — canonical WELL port is 18083
- ❌ Tool count is NOT 13 — it is 17 (INVARIANTS.md once said 13; corrected 2026-06-14)
- ❌ Line count is NOT 11,243 — server.py is ~15,755 lines
- ✅ `pytest tests/` is the primary test runner; `test_well.py` is a legacy plain-Python audit suite

## Verification

```bash
# Health check
curl http://localhost:18083/health | python3 -m json.tool

# MCP tool count
curl http://localhost:18083/health | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'tool_count: {d[\"tool_count\"]}')"

# Restart after changes
systemctl restart well

# Tests
python -m pytest tests/ -q --tb=short
python test_well.py
```
