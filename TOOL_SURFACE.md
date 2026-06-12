# WELL Tool Surface Registry
> **Canonical Source:** `ariffazil/well`
> **Authority:** WELL organ, governed by `ariffazil/arifOS`
> **Purpose:** Document the live public MCP surface and its invariants
> **Status:** OPERATIONAL | PHOENIX-73F | 14-tool somatic surface

---

## Live MCP Surface

**Production endpoint:** `https://well.arif-fazil.com/mcp`
**Transport:** `streamable-http` (MCP protocol)
**Live tool count:** 18
**Health endpoint:** `https://well.arif-fazil.com/health`

### Invariant

```
/health tool_count (18) = SOMATIC_TOOLS (18)
```

This invariant is enforced at startup by `_enforce_somatic_boundary()` in `server.py`. Any `@mcp.tool` not in `SOMATIC_TOOLS` is stripped before the server begins accepting connections.

---

## Public MCP Tools (14)

| Tool | Class | Omega Reference | Note |
|------|-------|-----------------|------|
| `mcp_health_check` | `DEPRECATED_ALIAS` | Ω-WELL | Delegates to `well_assess_reliability(mode="health")`. Retained for backward compatibility. |
| `well_classify_substrate` | `CANONICAL_PUBLIC` | Ω-WELL-01 | Substrate classification and boundary sensing. |
| `well_trace_lineage` | `CANONICAL_PUBLIC` | Ω-WELL-02 | Memory, trend, ledger, and vault chain tracing. |
| `well_detect_boundary` | `CANONICAL_PUBLIC` | Ω-WELL-03 | Boundary detection across membrane, body, machine, and federation. |
| `well_measure_gradient` | `CANONICAL_PUBLIC` | Ω-WELL-04 | Measure chemical, energy, pressure, attention, and compute gradients. |
| `well_assess_metabolism` | `CANONICAL_PUBLIC` | Ω-WELL-05 | Assess biological metabolism and system throughput across substrates. |
| `well_assess_homeostasis` | `CANONICAL_PUBLIC` | Ω-WELL-06 | Assess regulation, stability, and empathic balance under change. |
| `well_check_repair` | `CANONICAL_PUBLIC` | Ω-WELL-07 | Check repair, recovery, resilience, and forge cycle integrity. |
| `well_validate_vitality` | `CANONICAL_PUBLIC` | Ω-WELL-08 | Validate vitality, readiness, and NIAT. |
| `well_assess_livelihood` | `CANONICAL_PUBLIC` | Ω-WELL-09 | Assess human wellness, role, dignity, support, and meaning. |
| `well_assess_reliability` | `CANONICAL_PUBLIC` | Ω-WELL-10 | Assess machine, tool, institution, and operational reliability. |
| `well_compute_metabolic_flux` | `CANONICAL_PUBLIC` | Ω-WELL-10b | Compute unified metabolic entropy rate (cognitive + machine). |
| `well_guard_dignity` | `CANONICAL_PUBLIC` | Ω-WELL-12 | Guard soul, personhood, meaning, and symbolic boundaries. |
| `well_medical_boundary` | `CANONICAL_PUBLIC` | Ω-WELL-13 | Explicit non-diagnosis guard with F9 Soul Contract. |

---

## Deprecation Notes

- `mcp_health_check` — deprecated alias. Use `well_assess_reliability(mode="health")` directly.
- No stage aliases (`well_NNN_*`) on MCP surface — stripped at startup.

---

## Source Counts

| Metric | Count |
|--------|-------|
| Total `@mcp.tool` decorators in source | 52 |
| SOMATIC_TOOLS boundary set | 18 |
| Live MCP tools (boundary enforced) | 18 |
| Internal helpers / autonomic tools | 39 |

---

## What Is NOT On MCP Surface

The following are internal-only functions (no `@mcp.tool` decorator):

- `well_system_registry_status` — internal diagnostic
- `well_registry_status` — internal diagnostic
- All `well_NNN_*` stage helpers (000–999) — stripped by SOMATIC boundary
- All `well_*` helpers not in `SOMATIC_TOOLS` — stripped by SOMATIC boundary

---

## Absorption Log

| Alias | Canonical | Absorbed |
|-------|-----------|----------|
| `well_contrast_report` | `well_state(include="trend")` | ✅ 2026-05-26 |
| `well_fatigue_accumulator(mode="check")` | `well_assess_homeostasis(mode="fatigue")` | ✅ 2026-05-26 |
| `mcp_health_check` | `well_assess_reliability(mode="health")` | ✅ 2026-05-26 |

---

*Last Updated: 2026-06-12 | PHOENIX-73F | DITEMPA BUKAN DIBERI*
