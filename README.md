# WELL — Human Substrate & Metabolic State

> ⚠️ **CANONICAL AUTHORITY NOTICE:**
> WELL is the **vitality/substrate organ**, not a constitutional authority.
> F1-F13 floors, 888_JUDGE verdicts, and VAULT999 are defined in `ariffazil/arifOS`.

> **Status:** OPERATIONAL | **Organ:** SUBSTRATE (Ω-WELL) | **Authority:** arifOS
> **Domain:** `well.arif-fazil.com`
>
> ⚠️ **For live/degraded/disabled status of ALL federation organs, see:**
> **`ariffazil/arifOS/FEDERATION_STATUS.md`** — canonical source of truth.

## 🏛️ What this repo is

The human bio-telemetry and metabolic state organ within the arifOS federation. WELL monitors the coupled human-machine system state through a FastMCP surface of ~60 tools spanning biometric readiness, machine substrate telemetry, and coupled vitality metrics. All WELL data passes through the F5 PEACE and F6 EMPATHY floors before being used in any governance decision.

**WELL owns the SUBSTRATE — the living layer that keeps the human in the loop.**

> **MCP Surface (live test 2026-05-17):** 15 tools — `mcp_health_check` + 14 Ω-WELL tools. Source has 81 `@mcp.tool` decorators; only 15 exposed on public surface. Internal aliases (well_state, well_log, well_readiness, etc.) are hidden from MCP surface.

## 📦 Ownership

- **Owns**: Human biometric readiness (H-WELL), machine substrate telemetry (M-WELL), coupled vitality state (C-WELL), governance telemetry (G-WELL).
- **Does NOT own**: Constitutional judgment (arifOS), economic logic (WEALTH).

## 🏗️ Current Structure

```
WELL/
├── server.py              # FastMCP server (~60 tools: 13 Ω-WELL + aliases)
├── vault_bridge.py        # VAULT999 append-only ledger client
├── gate/
│   └── well_gate.py      # Pre-JUDGE biological readiness mirror
├── test_well.py          # Audit / adversarial test suite (plain Python, NOT pytest)
├── state.json            # Live operator state snapshot
├── events.jsonl          # Event stream
├── Dockerfile            # Container image
├── deploy.sh             # Docker build & deploy script
├── docs/                # Governance specs and telemetry docs
├── specs/               # W-Floor specifications
└── scripts/             # Operational scripts
```

## 🚀 Verified Commands

```bash
# Install
pip install -e .

# Start server
python server.py

# Run tests (plain Python, NOT pytest)
python test_well.py

# Docker build & deploy
./deploy.sh [TAG]
```

## 🔗 Federation Loop

- [arifOS](https://github.com/ariffazil/arifOS) — Kernel (constitutional judgment, F5/F6 enforcement)
- [WEALTH](https://github.com/ariffazil/wealth) — Capital (economic constraints on human flourishing)

---

*Last Verified: 2026.05.16 | 999 SEAL ALIVE*


---

## 🏛️ Federated Architecture

This repository is a core organ of the **arifOS Federation**:
*   **Operator Cockpit (AAA):** `/root/AAA`
*   **Constitutional Kernel (arifOS):** `/root/arifOS`
*   **Vision Shell (A-FORGE):** `/root/A-FORGE`
*   **Geological Engine (GEOX):** `/root/geox`
*   **Capital Engine (WEALTH):** `/root/WEALTH`
*   **Biological Substrate (WELL):** `/root/WELL`
*   **Informational Surfaces (arif-sites):** `/root/arif-sites`

*Unified under the arifOS Sovereign Constitution (F1–F13).*
