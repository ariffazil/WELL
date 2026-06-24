<!-- SOT-MANIFEST
owner: Arif
last_verified: 2026-06-24
valid_from: 2026-06-24
valid_until: 2026-07-24
confidence: high
scope: /root/WELL
-->

# CONTEXT.md — WELL (Vitality Guard)

> **Organ:** WELL | **Port:** 18083 | **Repo:** `ariffazil/well`
> **Last Updated:** 2026-06-24

## Live State

- **Service:** `well.service` (systemd, HTTP mode)
- **Health:** `http://127.0.0.1:18083/health`
- **Public MCP:** `https://well.arif-fazil.com/mcp`
- **Runtime:** Python 3.12+ / FastMCP / Pydantic v2
- **Role:** Human readiness — reflect, never judge or diagnose
- **State file:** `/root/WELL/state.json`

## Key Features

- Metabolic flux computation (`well_compute_metabolic_flux`)
- Homeostasis assessment (`well_assess_homeostasis`)
- Sovereign entropy scoring (`well_assess_sovereign_entropy`)
- Dignity guard (`well_guard_dignity`)
- WELL → GEOX decision-class gate (`geox_well_decision_class`)

## Dependencies

- arifOS MCP kernel (8088) — constitutional judgment
- GEOX (8081) — receives decision-class gating
- AAA (3001) — cockpit display

## Known Issues

- Federation Governance Gate previously failed due to missing `FEDERATION_CONTRACT.md` and `CONTEXT.md` — **resolved 2026-06-24**

---

*DITEMPA BUKAN DIBERI — Human readiness is forged, not assumed.*
