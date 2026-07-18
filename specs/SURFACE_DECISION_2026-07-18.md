# WELL Surface Decision — Thermodynamic-APEX Promotion

> **Date:** 2026-07-18
> **Authority:** Pending arif_judge SEAL
> **Tier:** T2 ANNOUNCE (surface visibility change, not capability change)

---

## Current State

WELL has 13 canonical tools in `tool_authority_manifest.yaml` but only 8 on the
public MCP surface (tools/list). The 5 missing from public:

| Tool | Ω | Canonical Since | Why It's Not Public |
|------|---|----------------|-------------------|
| `well_detect_boundary` | 03 | 2026-05-12 | Historical — never promoted after manifest creation |
| `well_measure_gradient` | 04 | 2026-05-12 | Historical — never promoted |
| `well_assess_metabolism` | 05 | 2026-05-12 | Historical — never promoted |
| `well_assess_livelihood` | 09 | 2026-05-12 | Historical — never promoted |
| `well_compute_metabolic_flux` | 10b | 2026-05-12 | Historical — never promoted |

## Recommendation

Promote 4 of 5 to the SOMATIC_TOOLS set in `server.py`:

| Tool | Promotion Rationale |
|------|-------------------|
| `well_measure_gradient` | **Energy vertex** of constraint-energy-intelligence triangle. Required for thermodynamic-APEX framework. |
| `well_assess_metabolism` | **Energy throughput** measurement. Complements gradient with flow rate. |
| `well_detect_boundary` | **Shadow vertex** — boundary detection is the structural shadow detector. |
| `well_assess_livelihood` | **Livelihood energy** — connects biology to capital (WEALTH bridge). |

**Deferred:**
| Tool | Deferral Rationale |
|------|-------------------|
| `well_compute_metabolic_flux` | Internal compute helper. Exposed through `well_assess_metabolism`. No independent agent need. |

## What Changes

1. `server.py`: Add 4 tool names to `SOMATIC_TOOLS` set
2. `server.py`: Ensure 4 functions have `@mcp.tool()` decorator (verify — they may already)
3. No schema changes. No new code logic. Visibility only.

## What Does NOT Change

- Existing 8 public tools remain unchanged
- No new tools created
- No parameters added to existing tools
- No breaking changes to MCP surface

## Verification

After promotion, tools/list should return 12 tools (8 existing + 4 promoted).

## Gate

This is a document only. Code changes require arif_judge SEAL.

---

*DITEMPA BUKAN DIBERI — Surface is forged through evidence, not given through assumption.*
