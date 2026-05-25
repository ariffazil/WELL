# WELL Tool Surface Registry
> **Canonical Source:** `ariffazil/well`
> **Authority:** WELL organ, governed by `ariffazil/arifOS`
> **Purpose:** Classify every `@mcp.tool` decorator in `server.py`
> **Status:** PARTIAL — classification in progress (PHOENIX-73E)

---

## Classification Key

| Class | Meaning |
|-------|---------|
| `CANONICAL_PUBLIC` | Intentionally exposed to MCP clients; safe for agents |
| `INTERNAL_ALIAS` | Helper/wrapper that maps to a canonical tool |
| `DEPRECATED_ALIAS` | Old name, superseded by canonical name |
| `TEST_ONLY` | Only for testing, not for production use |
| `REMOVE_CANDIDATE` | Should be removed; causes agent confusion |
| `UNKNOWN` | Not yet classified; requires SME review |

---

## Known Canonical Public Tools (from WELL README)

WELL README claims: **15 tools** on public surface (including `mcp_health_check` + 14 Ω-WELL tools).

Public tools confirmed in code:
| Function | Class | Notes |
|---------|-------|-------|
| `mcp_health_check` | `CANONICAL_PUBLIC` | ✅ Health check |
| `well_state` | `CANONICAL_PUBLIC` | ✅ Core state |
| `well_readiness` | `CANONICAL_PUBLIC` | ✅ Readiness assessment |
| `well_log` | `CANONICAL_PUBLIC` | ✅ Event logging |
| `well_contrast_report` | `CANONICAL_PUBLIC` | ✅ Contrast analysis |
| `well_trend_analysis` | `CANONICAL_PUBLIC` | ✅ Trend analysis |
| `well_bandwidth_recommendation` | `CANONICAL_PUBLIC` | ✅ Bandwidth rec |
| `well_machine_state` | `CANONICAL_PUBLIC` | ✅ Machine substrate |
| `well_coupled_readiness` | `CANONICAL_PUBLIC` | ✅ Coupled readiness |
| `well_decision_bandwidth` | `CANONICAL_PUBLIC` | ✅ Decision bandwidth |
| `well_reflect_trend` | `CANONICAL_PUBLIC` | ✅ Reflection trend |
| `well_reflect_readiness` | `CANONICAL_PUBLIC` | ✅ Reflection readiness |

**Total confirmed public:** 12 tools. README says 15. 3 more public tools not yet identified.

---

## Internal Infrastructure (INTERNAL_ALIAS / TEST_ONLY)

| Function | Class | Notes |
|----------|-------|-------|
| `build_well_todo` | `INTERNAL_ALIAS` | Task builder; not MCP exposed |
| `is_well` | `INTERNAL_ALIAS` | State predicate; internal |
| `readiness_score` | `INTERNAL_ALIAS` | Computed internally; not direct MCP |
| `well_init` | `TEST_ONLY` | Initialization only |
| `well_anchor` | `TEST_ONLY` | Anchor session only |
| `well_check_floors` | `INTERNAL_ALIAS` | Floor check wrapper |
| `well_log_state` | `INTERNAL_ALIAS` | State logging helper |
| `well_get_readiness` | `INTERNAL_ALIAS` | Readiness getter (duplicate?) |
| `well_check_floor` | `INTERNAL_ALIAS` | Floor validator |
| `well_list_log` | `INTERNAL_ALIAS` | Log listing |
| `well_seal_vault` | `INTERNAL_ALIAS` | Vault sealing (internal) |
| `well_recovery_protocol` | `INTERNAL_ALIAS` | Recovery logic |
| `well_niat_check` | `INTERNAL_ALIAS` | NIAT boundary check |
| `well_decision_classify` | `INTERNAL_ALIAS` | Decision classification |
| `well_consent_status` | `INTERNAL_ALIAS` | Consent tracking |
| `well_medical_boundary` | `INTERNAL_ALIAS` | Medical boundary |
| `well_pressure_ledger` | `INTERNAL_ALIAS` | Pressure ledger |
| `well_daily_brief` | `INTERNAL_ALIAS` | Daily brief generator |
| `well_machine_log` | `INTERNAL_ALIAS` | Machine log helper |
| `well_forge_precheck` | `INTERNAL_ALIAS` | Forge precheck |
| `well_forge_pressure_update` | `INTERNAL_ALIAS` | Forge pressure update |
| `well_forge_mode_recommend` | `INTERNAL_ALIAS` | Forge mode recommendation |
| `well_forge_closeout` | `INTERNAL_ALIAS` | Forge closeout |
| `well_get_health` | `INTERNAL_ALIAS` | Health getter (duplicate of mcp_health_check?) |
| `well_get_state` | `INTERNAL_ALIAS` | State getter (duplicate of well_state?) |
| `well_check_invariant` | `INTERNAL_ALIAS` | Invariant checker |
| `well_log_signal` | `INTERNAL_ALIAS` | Signal logging |
| `well_list_events` | `INTERNAL_ALIAS` | Event listing |

---

## Unknown Classification (need SME review)

The following tools are not yet classified. They may be public, internal, or deprecated:

| Function | Line | Possible Class |
|----------|------|---------------|
| (all above listed functions) | — | See above |

---

## Next Steps

1. ✅ Created this registry (PHOENIX-73E)
2. ⬜ Identify 3 missing public tools from the 15 claimed in README
3. ⬜ Resolve duplicate tools (`well_state` vs `well_get_state`, `mcp_health_check` vs `well_get_health`)
4. ⬜ Classify all `UNKNOWN` entries with WELL SME review
5. ⬜ Update WELL README to match actual tool surface

---

## WELL README Claim vs Reality

| Claim | Value |
|-------|-------|
| Public MCP surface | 15 tools |
| Source `@mcp.tool` decorators | 81 |
| **Ratio** | ~15 public / 81 total |

Only 12 public tools confirmed so far. 3 unaccounted for.
