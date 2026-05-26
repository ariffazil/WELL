# WELL Tool Surface Registry
> **Canonical Source:** `ariffazil/well`
> **Authority:** WELL organ, governed by `ariffazil/arifOS`
> **Purpose:** Classify every `@mcp.tool` decorator in `server.py`
> **Status:** PHOENIX-73F — collapse in progress

---

## Live MCP Surface (Post PHOENIX-73F Step 1A+1B+1C)

**Production endpoint:** `https://well.arif-fazil.com/mcp`
**Transport:** `streamable-http` (latest MCP protocol)
**Live tool count:** 45 (verified 2026-05-26 via JSON-RPC)

### Canonical Public Tools (9 + aliases)

| Tool | Class | Status |
|------|-------|--------|
| `well_state` | `CANONICAL_PUBLIC` | ✅ Live — biological telemetry snapshot |
| `well_log` | `CANONICAL_PUBLIC` | ✅ Live — event logging (only write tool) |
| `well_assess_homeostasis` | `CANONICAL_PUBLIC` | ✅ Live — mode-bearing, fatigue implemented (2026-05-26) |
| `well_assess_livelihood` | `CANONICAL_PUBLIC` | ✅ Live — mode-bearing, fail-closed on role/meaning/dignity (888_HOLD) |
| `well_assess_metabolism` | `CANONICAL_PUBLIC` | ✅ Live — mode-bearing, fail-closed on gradient/flux (888_HOLD) |
| `well_assess_reliability` | `CANONICAL_PUBLIC` | ✅ Live — machine health + machine/model/vitals modes |
| `well_guard_dignity` | `CANONICAL_PUBLIC` | ✅ Live — mode-bearing, fail-closed on consent/boundary/shadow (888_HOLD) |
| `well_check_repair` | `CANONICAL_PUBLIC` | ✅ Live — forge cycle integrity |
| `well_validate_vitality` | `CANONICAL_PUBLIC` | ✅ Live — vitality + NIAT validation |
| `well_readiness_gate` | `CANONICAL_PUBLIC` | ✅ Live (2026-05-26) — pre-consequential-action readiness gate; PROCEED/DEFER/ADVISORY_BLOCKED for C1-C5 decisions; contrast scenario tested |
| `well_contrast_report` | `DEPRECATED_ALIAS` | ✅ Live — delegates to `well_state(include="trend")` |
| `well_fatigue_accumulator` | `DEPRECATED_ALIAS` | ✅ Live — `check` delegates to homeostasis(fatigue), log/rest/reset direct |
| `mcp_health_check` | `DEPRECATED_ALIAS` | ✅ Live — delegates to `well_assess_reliability(mode="health")` |

### Stage Aliases (13 — exposed, pending Step 2 decorator removal)

These are internal stage-numbered helpers still on MCP surface:

| Tool | Stage | Note |
|------|-------|------|
| `well_000_init` | 000 | Bootstrap |
| `well_111_sense` | 111 | Substrate sensing |
| `well_222_fetch` | 222 | Evidence fetching |
| `well_333_mind` | 333 | Vitality reasoning — delegate for livelihood/metabolism |
| `well_444_kernel` | 444 | Routing + lane selection |
| `well_444_gateway` | 444 | Federation gateway |
| `well_444_reply` | 444 | Packet composition |
| `well_555_memory` | 555 | Memory + trend |
| `well_666_heart` | 666 | Empathy + dignity — delegate for homeostasis |
| `well_777_forge` | 777 | Forge execution |
| `well_888_judge` | 888 | Readiness validation |
| `well_999_vault` | 999 | Vault operations |
| `well_000_ops` | 000 | Operations + health |

**Step 2 will hide all 13 stage aliases.** Expected post-Step 2 count: **~32 tools**.

### Internal Helpers (28 — hidden by Step 1A)

Decorators removed, function bodies preserved for future alias removal (Step 2):

```
well_log_state, well_get_readiness, well_check_floor, well_list_log,
well_seal_vault, well_trend_analysis, well_bandwidth_recommendation,
well_recovery_protocol, well_niat_check, well_decision_classify,
well_consent_status, well_medical_boundary, well_pressure_ledger,
well_daily_brief, well_machine_log, well_forge_precheck,
well_forge_pressure_update, well_forge_mode_recommend, well_forge_closeout,
well_get_health, well_get_state, well_check_invariant, well_log_signal,
well_list_events, well_circadian_phase, well_livelihood_dignity_check,
well_symbolic_domain_check
```

---

## Source vs Live Count

| Metric | Count | Note |
|--------|-------|------|
| Source `@mcp.tool` decorators | 52 | Git HEAD after Step 1A+1B+1C+1D |
| Live MCP tools (post-restart) | 46 | After `_enforce_somatic_boundary` filter |
| Internal helpers hidden (Step 1A) | 28 | Decorators removed |
| Stage aliases pending hide (Step 2) | 13 | All well_NNN_* |
| Target MCP surface | ~32 | After Step 2 |

---

## 888_HOLD Items (Mode Delegation Bugs)

| Tool | Issue | Resolution |
|------|-------|------------|
| `well_assess_livelihood` | Declares role/meaning/dignity; `well_333_mind` has human/machine/coupled — zero overlap | 888_HOLD pending |
| `well_assess_metabolism` | Declares gradient/flux; `well_333_mind` only has human/machine/coupled | 888_HOLD pending |
| `well_guard_dignity` | Declares consent/boundary/shadow; `well_666_heart` only has critique/empathize/dignity/redteam/maruah | 888_HOLD pending |

Full register: `WELL_888_HOLD_REGISTER.md`

---

## Absorption Log (Step 1C)

| Alias | Canonical | Absorbed |
|-------|-----------|----------|
| `well_contrast_report` | `well_state(include="trend")` | ✅ 2026-05-26 |
| `well_fatigue_accumulator(mode="check")` | `well_assess_homeostasis(mode="fatigue")` | ✅ 2026-05-26 |
| `mcp_health_check` | `well_assess_reliability(mode="health")` | ✅ 2026-05-26 |

---

## Next Steps

- [x] Step 1A: Hide 28 internal helpers ✅
- [x] Step 1B: Guard 3 mode-bearing tools with fail-closed ✅
- [x] Step 1C: Absorb 3 aliases ✅
- [ ] Step 2: Remove 13 stage alias decorators → target ~32 tools
- [ ] Deploy: Restart WELL systemd, verify tool count
- [ ] 888_HOLD: Fix 3 mode delegation chains
- [ ] SEAL: Emit final WELL_COLLAPSE_MANIFEST.json

---

*Last Updated: 2026-05-26 | PHOENIX-73F | DITEMPA BUKAN DIBERI*
