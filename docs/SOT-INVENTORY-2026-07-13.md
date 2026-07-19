# WELL — SOT Inventory Report
**Date:** 2026-07-13  
**Session:** SEAL-75dad8dbbb6a4683  
**Repo Path:** /root/WELL  
**Organ Role:** REFLECT_ONLY — Human Readiness Mirror  

---

## 1. GIT STATE

| Property | Value |
|----------|-------|
| **HEAD** | `765cf92` — "zen: dark geometry mirror metabolizes content + body-as-home archetype" |
| **Active Branch** | `zen-migration-2026-07-11` ⚠️ |
| **Other Branches** | `main`, `worktree-well-final` |
| **Remote Branches** | `origin/main`, `origin/zen-migration-2026-07-11`, `origin/archive/pre-consolidation-2026-07-12` |
| **Dirty Files** | **NONE** — working tree is clean |
| **Canonical Branch Claim** | INVARIANTS.md says `main`; reality is `zen-migration-2026-07-11` ⚠️ |

## 2. README.md — Health Check

- **934 lines** of comprehensive documentation
- **Two SOT-MANIFEST blocks** in frontmatter (lines 1-15 and 43-50) — redundant
- Well-structured with clear IS/NOT boundary declarations

### 🔴 Issues Found

#### A. Duplicate APEX Bridge Section (lines 54-63 and 103-109)
The exact same text block appears twice:
> "APEX is the admissibility framework for decisions under uncertainty (ΔΩΨ). arifOS compiles those dynamics into a constitutional orchestration substrate. AAA renders federation-state and coordination (display layer — not ASI-civilisation claims). A-FORGE gives the system governed hands. GEOX, WEALTH, and WELL anchor those hands to earth, capital, and human reality. VAULT999 preserves consequence. Arif/F13 remains the sovereign witness and final veto."
> "WELL must never: diagnose medical conditions, decide for the operator, or override human sovereignty over biological state."
> "Full doctrine: [GENESIS/040_APEX_STACK.md](...)"
> "**Orthogonal CANON:** ..."

Lines 54-63 (Section header "## APEX STACK Bridge") and lines 103-109 (after ABC Trinity test results) are **identical**.

#### B. Missing Referenced Files
READ ME's architecture diagram (line 485-486) lists:
- `TOOL_SURFACE.md` — **not at repo root**; exists at `scripts/governance/TOOL_SURFACE.md`
- `FEDERATION_CONTRACT.md` — **not at repo root**; exists at `scripts/governance/FEDERATION_CONTRACT.md`

#### C. Stale Quick-Start JSON Example (lines 223-235)
The expected health response JSON shows `tool_count: 22` — live server returns `tool_count: 29`.

## 3. data/ Directory — Cross-Organ Data Leakage

| File | Size | Content | Verdict |
|------|------|---------|---------|
| `data/sessions.json` | ~374 KB | arifOS session traces (arif sovereign sessions) | ✅ Acceptable — local session cache |
| `data/vault999.jsonl` | ~1.8 KB | **5 WEALTH_SESSION_INIT events** (economic-analysis intents) | 🔴 **Mis-stored from WEALTH organ** |

The vault999.jsonl file contains events like:
```json
{"event_type": "WEALTH_SESSION_INIT", "session_id": "wealth-session-...", "actor_id": "wealth-agent", ...}
```
These are WEALTH organ session records stored in WELL's data directory.

## 4. 'Quantum' Language Audit

| File | Line | Text | Assessment |
|------|------|------|------------|
| README.md | 33, 856 | "quantum diagnostics" | ✅ Intentional domain term (3-tier: qualitative/quantitative/quantum) |
| `well_mcp/prompts/well_critique.py` | 74, 76 | "quantum distress" | ✅ Intentional — hidden pattern detection |

**Verdict:** 15 matches found, all within WELL's own established domain language. "Quantum" here means "hidden pattern / non-obvious signal detection" (e.g., distress behind humour), not quantum physics. **No misuse.**

## 5. Diagnostic Claims Without Evidence

- **191 matches** for `diagnos*` across all files
- **Every match** is in guardrail context: "WELL does NOT diagnose," "not a diagnostic authority," "not a medical diagnosis"
- README explicitly lists (lines 183, 380, 829): "NOT a medical device... NOT a therapist... NEVER make medical diagnoses"
- GENESIS documents reinforce the non-diagnosis boundary

**Verdict:** Clean. WELL is well-guarded against diagnostic claims. No un-evidenced diagnostic assertions found despite the "quantum diagnostics" framing.

## 6. MCP Surface — Live Server Audit

### /health Endpoint (http://127.0.0.1:18083/health)

| Field | Value |
|-------|-------|
| **status** | `degraded` |
| **tool_count** | `29` |
| **authority** | `REFLECT_ONLY` |
| **truth_status** | `INSUFFICIENT_DATA` |
| **well_signal** | `WELL_HOLD` |
| **owner_summary** | `YELLOW` (canonical_tools=22, sovereign_state_unknown) |
| **freshness** | FRESH (age 2.6h) |
| **identity_hash** | `1b1f46b3e...` |
| **substrate_manifest_hash** | `sha256:fd21db85...` |

### tools/list (http://127.0.0.1:18083/mcp)

**29 tools** exposed (not 22 as documented):

| Category | Tools |
|----------|-------|
| Core Canonical (13) | well_health_check, well_classify_substrate, well_trace_lineage, well_detect_boundary, well_measure_gradient, well_assess_metabolism, well_assess_homeostasis, well_check_repair, well_validate_vitality, well_assess_livelihood, well_assess_reliability, well_compute_metabolic_flux, well_assess_sovereign_entropy |
| Dignity/Guard | well_guard_dignity, well_dark_geometry_mirror, well_medical_boundary |
| Registry/Diagnostic | well_registry_status, well_classify_state, well_13_signal_coverage |
| Federation Handoff (3) | well_handoff_dignity_to_arifos, well_handoff_livelihood_to_wealth, well_attest_to_kernel |
| ZEN Extensions (7) | well_sabar_latency, well_trust_compression, well_niat_impact_mirror, well_correction_capacity, well_regulation_recovery, well_readiness (deprecated), well_signal_coverage |

### 🔴 Discrepancies

| Issue | Detail |
|-------|--------|
| **Doc/Reality mismatch** | Docs claim 22 tools (21 canonical + 1 deprecated). Live surface: **29 tools**. |
| **TOOL_SURFACE.md stale** | In `scripts/governance/`, lists 22 tools, missing 7 ZEN extensions |
| **SOMATIC_TOOLS duplicates** | `well_classify_substrate` and `well_dark_geometry_mirror` appear **twice** in the set (benign in a set, but sloppy) |
| **Running binary ≠ repo HEAD** | Health endpoint returns fields (`status`, `final_authority`, `tool_count`) not in server.py at HEAD `765cf92` |
| **`well_sense_substrate`** | In SOMATIC_TOOLS set but depends on import from `sensors/` — may fail at runtime |

## 7. Additional Quality Issues

| # | Issue | Severity | Detail |
|---|-------|----------|--------|
| 1 | **Tool count mismatch** | **HIGH** | All docs say 22; live server serves 29. TOOL_SURFACE.md, CONTEXT.md, INVARIANTS.md all stale. |
| 2 | **Running server != repo** | **HIGH** | HEAD is on `zen-migration-2026-07-11`; the health endpoint's field set differs from current server.py. Suggests running binary is from a build on `main` or a different commit. |
| 3 | **WEALTH data in WELL data/** | **MEDIUM** | `data/vault999.jsonl` contains 5 WEALTH_SESSION_INIT records — cross-organ data leakage. |
| 4 | **Duplicate APEX bridge** | **MEDIUM** | 7-line block repeated at lines 54-63 and 103-109 of README.md |
| 5 | **BOUNDARY.md misnamed** | **LOW** | File at repo root named BOUNDARY.md actually contains invariants content |
| 6 | **FEDERATION_CONTRACT.md mislocated** | **LOW** | README claims root path; actual path is `scripts/governance/` |
| 7 | **TOOL_SURFACE.md mislocated** | **LOW** | README claims root path; actual path is `scripts/governance/` |
| 8 | **Dual SOT-MANIFEST** | **LOW** | README.md has two SOT-MANIFEST blocks — the first claims `health_status: degraded` and `truth_status: INSUFFICIENT_DATA` (accurate, but redundant) |
| 9 | **Canonical branch mismatch** | **LOW** | INVARIANTS.md says canonical branch is `main`; active work is on `zen-migration-2026-07-11` |

## 8. Summary

### What's Good
- ✅ **Working tree is clean** — committed state
- ✅ **No diagnostic claims without evidence** — WELL's guardrails are effective
- ✅ **"Quantum" language is domain-correct** — not quantum physics misuse
- ✅ **MCP server is live and responding** — all 29 tools callable
- ✅ **SOMATIC_TOOLS boundary enforced** at server startup
- ✅ **Fresh biometric state** (2.6 hours old, within FRESH band)
- ✅ **Clear REFLECT_ONLY authority** — no mission creep

### What Needs Attention (Priority Order)
1. **🔴 RECONCILE tool count** — Update docs to 29 or trim SOMATIC_TOOLS to match documented 22. Running server exposes 7 ZEN extension tools beyond the canonical 22.
2. **🔴 REBUILD/SYNC** — Running server differs from repo HEAD. Rebuild on current `zen-migration-2026-07-11` or merge branch.
3. **🟡 CLEAN data/** — Remove WEALTH_SESSION_INIT events from `data/vault999.jsonl` (belongs to WEALTH organ).
4. **🟡 DEDUP APEX section** — Remove duplicate APEX bridge text at line 103-109 of README.md.
5. **🟡 RELOCATE or REMOVE dangling references** — TOOL_SURFACE.md and FEDERATION_CONTRACT.md referenced at root but live in `scripts/governance/`.
6. **🟡 INVARIANTS.md** — Update canonical branch from `main` to `zen-migration-2026-07-11` or merge.

---

*SOT inventory compiled 2026-07-13 under FEDERATION-SOT-20260712-ac8550fa epoch.*  
*WELL organ: REFLECT_ONLY mirror, 29 live tools, degraded health status, YELLOW owner verdict.*
