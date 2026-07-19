<!-- SOT-MANIFEST
owner: Arif
last_verified: 2026-07-15
valid_from: 2026-07-15
valid_until: 2026-08-15
confidence: high
scope: /root/WELL
domain_law: SUBSTRATE_LAW
authority: REFLECT_ONLY
mcp_tools_live: 27
license: AGPL-3.0
epistemic_status: SOURCE_OF_TRUTH
truth_rule: tools/list + /health beat any static count in this file
-->

# BOUNDARY.md — WELL

> Human Substrate & Metabolic State — Immutable boundaries for the WELL organ.  
> **REFLECT_ONLY.** License **AGPL-3.0**. Not medical. Not capital. Not earth.

## Canonical Branch

`main`

## Live Endpoints

| Endpoint | Port | Status |
|----------|------|--------|
| MCP | `http://127.0.0.1:18083/mcp` | LIVE — `well.service` |
| Health (public) | `https://well.arif-fazil.com/health` | LIVE |
| Health (local) | `http://127.0.0.1:18083/health` | LIVE · expect `tool_count: 27` |

## Required Health Checks

- `curl -s :18083/health` → `tool_count: **27**` (SOT: live tools/list — not 22, not 72)
- `python -m pytest tests/ -q --tb=short` before deploy
- Biometric inject required if `freshness` STALE/EXPIRED (operational RED ≠ code fail)

## Change Coupling

- `server.py` — FastMCP membrane (public **27** tools; internal helpers may exist)
- `well_mcp/tools/__init__.py` — name registry (must match tools/list)
- `gate/` — constitutional mirror (dignity, dark geometry, rasa)
- `engines/` · `sensors/` — compute / ingress
- `docs/WELL_TOOL_SURFACE.md` — agent intake catalog

## Canonical Tool Surface

**27 public MCP tools** — full list: `docs/WELL_TOOL_SURFACE.md` + `well_mcp/tools/__init__.py`.

| Substrate | Role |
|-----------|------|
| H-WELL | Human readiness, dignity, vitality |
| M-WELL | Machine reliability / repair |
| C-WELL | Coupled metabolism / flux |
| G-WELL | Boundary / substrate class |
| Federation | handoff_dignity · handoff_livelihood · attest_to_kernel · medical_boundary |

Do not invent tool counts from decorator totals.

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
