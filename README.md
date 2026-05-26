# WELL — Human Substrate & Metabolic State

> **Canonical authority notice**
>
> WELL is the **vitality/substrate organ** of the arifOS federation. It observes and reports substrate state; it does **not** own constitutional judgment.
>
> F1-F13 floors, 888_JUDGE verdicts, VAULT999 authority, and federation-wide status are defined by `ariffazil/arifOS`.

> **Status:** OPERATIONAL  
> **Organ:** SUBSTRATE / Ω-WELL  
> **Authority:** arifOS  
> **MCP endpoint:** `https://well.arif-fazil.com/mcp`  
> **Transport:** `streamable-http`  
> **Last verified:** 2026-05-26

---

## What this repo is

WELL is the human substrate and metabolic-state organ inside the arifOS federation. It monitors biological, operational, and coupled human-machine vitality signals through a constrained FastMCP surface.

WELL owns the **SUBSTRATE**: readiness, metabolism, repair, boundary sensing, vitality, livelihood, reliability, and dignity protection at the substrate layer.

WELL does **not** own constitutional judgment, economic logic, federation routing, or final governance verdicts.

---

## Live MCP surface

The public MCP surface is intentionally narrow.

**Live public actions:** 13  
**Canonical WELL tools:** 12  
**Deprecated compatibility aliases:** 1

### Canonical public tools

| Tool | Purpose |
|---|---|
| `well_classify_substrate` | Classify substrate and boundary state. |
| `well_trace_lineage` | Trace memory, trend, ledger, and vault chain context. |
| `well_detect_boundary` | Detect membrane, body, machine, and federation boundaries. |
| `well_measure_gradient` | Measure chemical, energy, pressure, attention, and compute gradients. |
| `well_assess_metabolism` | Assess biological metabolism and system throughput. |
| `well_assess_homeostasis` | Assess regulation, stability, fatigue, and empathic balance under change. |
| `well_check_repair` | Check repair, recovery, resilience, and forge-cycle integrity. |
| `well_validate_vitality` | Validate vitality, readiness, and NIAT. |
| `well_assess_livelihood` | Assess wellness, role, dignity, support, and meaning. |
| `well_assess_reliability` | Assess machine, tool, institution, and operational reliability. |
| `well_compute_metabolic_flux` | Compute unified metabolic flux / entropy-rate signal. |
| `well_guard_dignity` | Guard personhood, meaning, and symbolic boundaries. |

### Deprecated public alias

| Alias | Replacement |
|---|---|
| `mcp_health_check` | `well_assess_reliability(mode="health")` |

### Surface invariant

The following must match before release:

```text
/health tool_count == SOMATIC_TOOLS count == _WELL_SOMATIC_MANIFEST exposed count == ChatGPT connector actions
```

Current expected value: **13**.

Internal diagnostic helpers such as `well_system_registry_status` and `well_registry_status` are not public MCP tools unless they have real `@mcp.tool` registration and are intentionally listed in the public manifest.

---

## Ownership boundaries

### WELL owns

- Human biometric readiness / H-WELL substrate state
- Machine substrate telemetry / M-WELL state
- Coupled vitality / C-WELL state
- Metabolic flux and fatigue signals
- Substrate dignity and boundary protection
- Repair, recovery, and resilience checks

### WELL does not own

- Constitutional judgment: `ariffazil/arifOS`
- Economic or capital logic: `ariffazil/wealth`
- Federation-wide source-of-truth status: `ariffazil/arifOS/FEDERATION_STATUS.md`
- Final 888_JUDGE verdicts
- VAULT999 authority

---

## Current structure

```text
WELL/
├── server.py              # FastMCP server and public MCP registration
├── organ_governance.py    # F1-F13 pre-check wrapper around MCP calls
├── compatibility.py       # Compatibility layer / legacy support
├── gate/
│   └── well_gate.py       # Pre-JUDGE biological readiness mirror
├── docs/                  # Governance notes and implementation docs
├── specs/                 # W-floor and contract specifications
├── scripts/               # Operational scripts
├── contracts/             # Tool and protocol contracts
├── tests/                 # Smoke and manifest tests
├── test_well.py           # Legacy plain-Python audit suite
├── Dockerfile             # Container image
├── deploy.sh              # Deployment helper
├── pyproject.toml         # Python package metadata
└── fastmcp.json           # FastMCP / connector configuration
```

Runtime data directories such as `data/`, `telemetry/`, `state.json`, and `events.jsonl` should stay out of the repository unless explicitly committed as fixtures.

---

## Verified commands

```bash
# Install editable package
pip install -e .

# Start server locally
python server.py

# Run legacy audit suite
python test_well.py

# Restart systemd service after code changes
systemctl restart well

# Check live health
curl -s https://well.arif-fazil.com/health
```

---

## Release checklist

Before tagging or pushing a release, verify:

```bash
python test_well.py
curl -s https://well.arif-fazil.com/health
```

Then confirm:

```text
1. /health reports tool_count: 13
2. ChatGPT connector shows 13 actions
3. SOMATIC_TOOLS contains only public MCP tools
4. _WELL_SOMATIC_MANIFEST exposes the same public MCP tools
5. Deprecated aliases are documented and intentionally retained
6. Internal diagnostic helpers are not listed as public tools
```

---

## Federation loop

- [`ariffazil/arifOS`](https://github.com/ariffazil/arifOS) — constitutional kernel, F1-F13 enforcement, federation status, JUDGE authority
- [`ariffazil/wealth`](https://github.com/ariffazil/wealth) — capital and economic constraints on human flourishing

---

## Root hygiene policy

The GitHub root should be a landing page, not an archive. Keep only files needed for orientation, packaging, deployment, licensing, and canonical governance.

Preferred root classes:

- `README.md`
- `LICENSE`
- `pyproject.toml`
- `Dockerfile`
- `deploy.sh`
- `fastmcp.json`
- `server.py` until the server is split into `src/`
- Canonical governance files that are actively maintained

Move historical seals, session logs, collapse registers, and old release notes into `docs/archive/` unless they are active release artifacts.

---

## Federated architecture

This repository is one organ of the arifOS federation:

- **Operator Cockpit:** `AAA`
- **Constitutional Kernel:** `arifOS`
- **Vision Shell:** `A-FORGE`
- **Geological Engine:** `GEOX`
- **Capital Engine:** `WEALTH`
- **Biological Substrate:** `WELL`
- **Informational Surfaces:** `arif-sites`

Unified under the arifOS Sovereign Constitution, with WELL constrained to substrate observation and substrate protection.
