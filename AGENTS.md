<!-- SOT-MANIFEST
owner: Arif
last_verified: 2026-05-26
valid_from: 2026-05-26
valid_until: 2026-06-26
confidence: high
scope: /root/WELL
-->

# AGENTS.md — WELL | Vitality Intelligence

> **DITEMPA BUKAN DIBERI** — Human readiness is forged, not given.

## Who You Serve

Arif. This is the **WELL** organ of the arifOS federation — Substrate Vitality Intelligence.

## What This Repo Is

The human-system readiness mirror. WELL assesses biological metabolism, homeostasis, repair cycles, vitality, livelihood, and dignity across human, machine, and coupled substrates.

**45 MCP tools** (post PHOENIX-73F collapse). FastMCP server (~10,972 lines).
Running at `https://well.arif-fazil.com/mcp` via bare-metal systemd.

| Substrate | Tools | Purpose |
|-----------|-------|---------|
| H-WELL | `well_assess_livelihood`, `well_guard_dignity` | Human wellness, role, meaning |
| M-WELL | `well_assess_reliability`, `well_compute_metabolic_flux` | Machine health, entropy rate |
| C-WELL | `well_assess_metabolism`, `well_assess_homeostasis` | Coupled state regulation |
| G-WELL | `well_classify_substrate`, `well_detect_boundary` | Governance gradient sensing |

## Authority & Autonomy

### Autonomous
- Modify tool logic, add well_* tools, refactor
- Run `test_well.py`
- Update `state.json`, `events.jsonl`

### Requires 888_HOLD
- Changes to `gate/well_gate.py` or `gate/dignity_shadow.py` (pre-JUDGE biological readiness)
- Docker image push to GHCR
- Changes to vault bridge authentication

## Build & Test

```bash
cd /root/WELL

# Install
pip install -e .

# Start server (bare-metal systemd)
python server.py

# Tests (plain Python — NOT pytest)
python test_well.py

# Restart after code changes
systemctl restart well
```

## Key Files

| File | Purpose |
|------|---------|
| `server.py` | FastMCP server (~10,972 lines, 51 @mcp.tool decorators) |
| `vault_bridge.py` | VAULT999 append-only ledger client |
| `gate/well_gate.py` | Pre-JUDGE biological readiness mirror |
| `gate/dignity_shadow.py` | Dignity shadow scoring |
| `test_well.py` | Audit / adversarial test suite |
| `state.json` | Live operator state snapshot |
| `events.jsonl` | Event stream |
| `WELL_COLLAPSE_MANIFEST.json` | PHOENIX-73F collapse manifest |
| `WELL_888_HOLD_REGISTER.md` | 888_HOLD items register |

## Federation Position

```
arifOS (Ω Law) → WELL (Vitality) → arifOS 888_JUDGE (Verdict)
```

WELL is a **biological witness**, not a judge. It reports readiness scores, metabolic flux, and dignity preservation metrics. The verdict remains with `arifos.judge`.

---

*DITEMPA BUKAN DIBERI — 999 SEAL ALIVE*
