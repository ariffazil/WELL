# WELL v2 — APEX-ZEN Mutation Guide

**Date:** 2026-09-16 (FI-003 live audit, 25/31 tools fired + 6 writers verified)
**Status:** RATIFIED DIRECTION (F13 doctrine below) — mutation guide for all future WELL work
**Scope:** /root/WELL (source, da884ba) → deployed /opt/well (4c6f157, drift=true)

---

## 0. Constitutional Principle (F13, 2026-09-16)

> Readiness is not: "Can the system run?"
> Readiness is: **"Can witnessed reality still change future behavior?"**

- WELL v1 = Readiness Monitor (state measurement)
- WELL v2 = Reality Readiness Engine
- WELL v3 = Reality → Adaptation Engine

**Invariant (F12):** R-WELL and A-WELL are MEASUREMENT planes. They return
metrics and risk patterns — never verdicts. `WELL does not seal. arifOS judges.
A-FORGE executes.` Any new plane that starts emitting SEAL/HOLD/VOID as
*verdicts* is a constitutional violation, not an upgrade.

---

## 1. Live Audit Summary (2026-09-16)

- Health: `degraded`, drift=true (source da884ba ≠ deployed 4c6f157)
- Registry: `intended_tools: 10`, `registered: 31`, `exported: 10` → **21-tool drift**
- 13 internal arc aliases (`well_000_init`…`well_999_vault`) — kernel-arc mimicry inside a REFLECT_ONLY organ (authority-shadow duplication)
- 6 legacy aliases with `removal_date: 2026-09-01` — **15 days overdue**, still present
- 4 outbound bridges probe endpoints that do not exist on live kernel/AAA
- Consent gates (F11/F13) fail-closed correctly — verified by refusal-path fire

### Contradictions (P0 — fix before any compression)

| ID | Contradiction | Evidence |
|----|---------------|----------|
| C1 | `validate_vitality` says M_WELL UNKNOWN "machine_state.json stale 74.1h"; `machine_diagnose`/`assess_reliability` say FRESH 209s | Twin-FILE trap: deployed `/opt/well` reads its own stale copy; telemetry timer writes fresh path. Freshness fix (2026-09-15) exists in source only |
| C2 | HUD/snapshot say governance `BREACH` (consent_intact:false); `validate_vitality` says G_WELL `COHERENT` | Two governance scorers, two answers |
| C3 | `validate_vitality` payload embeds self-referential legacy block (`deprecated:true, replacement: well_validate_vitality` — replaces itself) | Legacy `well_readiness` envelope leak |
| C4 | Human plane: live `assess_triadic` = 88.4 WATCH; snapshot/HUD (26s later) = 97.6 OPTIMAL | Two human scorers, same minute, same state.json |
| C5 | Governance structurally ZERO: zero consent scopes (privacy-by-default) scored as breach → triadic `unified_score:0.00`, route HOLD forever | Scorer cannot distinguish "no scopes granted (healthy default)" from "consent revoked (breach)" |
| C6 | `observe_drift_field`: 0 samples → verdict `STABLE` | Void Guard violation — "no data" ≠ "all clear"; must be UNKNOWN |
| C7 | 4 dead bridges: `:8088/attest` 404; scar endpoints ×3 fail; AAA cockpit ×3 404 | Witness Surface Mismatch at bridge layer — WELL probes surfaces that don't exist |
| C8 | Deploy drift: fix in source, old code serving | `code that CAN run ≠ code that DOES run` scar |

---

## 2. Entropy Map — Redundancy Clusters

| Cluster | Tools | Live verdict | Action |
|---------|-------|--------------|--------|
| R1 Machine ×5 | machine_diagnose, assess_reliability, machine_recommend, classify_machine_state, observe_machine | All PASS; diagnose ⊃ reliability ⊃ recommend; observe_machine already returns classification | Merge → `well_machine` modes |
| R2 Triad ×4 | assess_triadic_state, get_triadic_snapshot, frame_read_snapshot, render_hud_panel | All PASS; snapshot & frame_read read same file; HUD renders snapshot | Merge → `well_triad` modes |
| R3 Dead bridges ×3 | observe_drift_field, observe_evidence_backlog, observe_scar_load | 0 samples / 404 / fail | Fold → `well_reality`; stop per-call dead probing |
| R4 Outbound ×4 | attest_to_kernel, propose_governance_signal, propose_seal_recommendation, handoff_dignity_to_arifos | attest bridge 404; others no-fire (writers) | Merge → `well_bridge` modes; FIX-5 first |
| R5 Intake ×4 | log_intake, log_recovery_event, log_substance, inject_biometric | Gates verified (F11/F13 BLOCK correct) | Merge → `well_intake` modes; gates preserved per mode |
| R6 Consent ×2 | consent_audit, consent_set_scope | PASS | Merge → `well_consent` modes |
| R7 Arc vestige ×13 | well_000_init … well_999_vault | Internal only, no external consumers found | Retire (one compat release) |
| R8 Legacy aliases ×6 | well_readiness, well_get_health, well_state, well_init, well_machine_state, well_assess_governance | removal_date 2026-09-01 passed | Execute removal now |

**Compression: 31 → 10 tools.** No external name-based consumers found in
/root/scripts or /etc/systemd/system (triadic-snapshot.timer reaches WELL via
HTTP `:18083/well_assess_triadic_state` — path-based, update once).

---

## 3. WELL v2 Target Surface (10 tools, one per plane)

| # | Tool | Plane | Modes | Absorbs |
|---|------|-------|-------|---------|
| 1 | `well_human` | H | homeostasis \| readiness \| dignity | assess_homeostasis, validate_vitality, guard_dignity |
| 2 | `well_machine` | M | diagnose \| recommend \| classify \| observe (scope: organ \| federation) | R1 cluster + observe_federation_thermal |
| 3 | `well_triad` | G+C | assess \| snapshot \| hud (observer: frame flag) | R2 cluster |
| 4 | `well_classify_substrate` | U | unchanged | — |
| 5 | `well_reality` | **R (NEW)** | confidence \| witness \| lineage \| bridges \| patterns | trace_lineage, R3 cluster |
| 6 | `well_adaptation` | **A (NEW)** | readiness \| precheck \| mttr \| gaps | check_repair |
| 7 | `well_intake` | H-write | meal \| recovery \| substance \| biometric | R5 cluster |
| 8 | `well_consent` | G-write | audit \| grant \| revoke | R6 cluster |
| 9 | `well_bridge` | G-outbound | attest \| signal \| recommend \| dignity \| log | R4 cluster |
| 10 | `well_registry` | meta | status \| full \| contradictions (NEW: self-audit mode surfacing C1–C8 as first-class metrics) | registry_status |

Final plane architecture (F13):

```
H-WELL  M-WELL  G-WELL  C-WELL  U-WELL  R-WELL  A-WELL
Human   Machine Gov     Coupled Underst. Reality Adaptation
```

---

## 4. The Seven Upgrades — Concrete Specs

### Upgrade #1 — R-WELL Reality Readiness → `well_reality`
- **Reality Confidence** per evidence source, classified:
  `OBSERVED | VERIFIED | ASSUMED | STALE`
- `reality_confidence = share(OBSERVED+VERIFIED)` across consumed surfaces
- Reads: bridge liveness (C7), contradiction count from `well_registry(mode=contradictions)`,
  Graphiti/Falkor freshness
- On dependency FAIL, the question is not "did X fail?" but
  **"are we observing the correct reality surface?"**
- Scar Graphiti becomes a metric, not a story.
- **Edited Reality ≠ Executed Reality** (F13 canon 2026-09-16): the twin-module
  trap — live implementation ≠ implementation being edited — is R-WELL's
  first-class Reality Integrity metric. Canonical compression:
  *Documentation describes reality. Runtime decides reality. Witness proves
  reality.* WELL's role: **constitutional readiness witness**, not a readiness
  dashboard.

### Upgrade #2 — A-WELL Adaptation Readiness → `well_adaptation`
- Headline metric: `adaptation_readiness ∈ [0,1]` + evidence list answering
  *"did witnessed reality change future behavior?"*
- **v0 falsifiable test (from the Ollama migration):** Graphiti stores
  "provider moved KVM8 → KVM4"; grep live configs for stale `100.64.0.2`/KVM8
  host references on that capability → `adaptation_gaps[]`. Non-empty list =
  adaptation failure evidence.
- Metrics: `decisions_stale_count`, `MTTR` (incident → recovered),
  `Reality Correction Time` (wrong belief → corrected in config)

### Upgrade #3 — Memory Vitality (folds into `well_reality`)
- "Memory Alive?" not "Memory Exists?"
- `Memory Recall Rate`, `Memory Freshness`, `Entity Resolution Health`,
  `Relationship Growth` (episode/node/edge deltas from Graphiti)
- Doctrine: `59 nodes / 53 edges grown > 40 days uptime`

### Upgrade #4 — Federation Readiness: Capability > Service
- `well_machine(mode=observe)` gains a **Capability Availability table**:
  `Ollama PASS | Graphiti PASS | Falkor PASS | Witness PASS`
- Capability health outranks service health in machine score.

### Upgrade #5 — Homeostasis First-Class: Metabolism > Snapshot
- `Recovery Speed (MTTR)` replaces `Failure Rate` as headline machine metric
- Triadic snapshot gains `recovery` block: MTTR, Reality Correction Time
- Aligned with arifFlow metabolism — but **distinct axis**: arifFlow FQ =
  verify/execute ratio; WELL metabolism = recovery dynamics. Never merge the two scores.

### Upgrade #6 — Scar Ledger Integration → `well_reality(mode=patterns)`
- Scar → Risk Pattern. Pattern fingerprints, e.g. **Witness Surface Mismatch**:
  `daemon logs ignored + assumptions over live probes + counts without identity proof`
- Match live session behavior against scar library → `Known Risk Pattern` output
- Patterns are evidence for arifOS, never verdicts.

### Upgrade #7 — Coupled Risk Constitutional: ×4
- Coupled plane becomes `Human × Machine × Memory × Governance`
- Triad snapshot gains `memory_plane`; C_WELL scored over 4 inputs
- The session pattern "Operator confidence HIGH / Reality confidence LOW" is a
  readiness issue even when CPU+RAM are green — the ×4 coupling surfaces it.

---

## 5. Migration Phases (each reversible, one release, arifOS-sealed)

| Phase | Work | Exit criterion |
|-------|------|----------------|
| **P0 — Fix reality first** (no API change) | FIX-1 single absolute machine_state.json path + deploy pipeline reconcile (/opt/well vs /root/WELL); FIX-2 governance scorer: no-scopes-default = INTACT (breach only on revocation); FIX-3 remove self-referential legacy block; FIX-4 one human scorer; FIX-5 reconcile or formally DEAD-mark the 4 bridges in registry (stop per-call probing); FIX-6 drift 0-samples → UNKNOWN; FIX-7 execute 6 overdue legacy removals; FIX-8 repo hygiene: 7+ .bak → `_archive/`, one canonical impl (well_mcp vs well_mcp_fastmcp) | health `drift:false`, `floors_violated:[]`, C1–C8 closed |
| **P1 — v2 surface** | tools_sot.yaml → v2; implement mode-tools alongside old; deprecation epoch stamped (removal 2026-10-16); update registry assert `intended=registered=exported=10` | both surfaces callable; registry reports migration state |
| **P2 — Consumer sweep** | Update triadic-snapshot.timer HTTP path, Hermes references, AAA cockpit, docs | zero references to retired names outside `_archive/` |
| **P3 — Removal** | Drop 21 + 6 legacy; retire arc vestige | registry 10=10=10; clean `legacy_alias_map` |
| **P4 — R-WELL live** | `well_reality` real data (Graphiti/Falkor/bridges) | reality_confidence computed from live evidence classes |
| **P5 — A-WELL live** | `well_adaptation` v0 gap detector + MTTR ledger | adaptation_gaps[] emitted for the Ollama KVM8→KVM4 test case |

**F13 priority re-rank (2026-09-16):** the phase table above is the dependency
map; **execution order follows this ranking** —
**#1 `well_bridge` → arifFlow** (readiness enters witness metabolism:
WELL observes → arifFlow receipts → long-term readiness scars; capability
unlock) · **#2 state migration to /var/lib/well** (kill twin trees
permanently — twin-path is a recurring disease) · **#3 31→10 tools**
(optimisation, not capability unlock).

**Phase 1 #2 — EXECUTED (2026-09-16):** twin trees killed permanently.
`well.service` drop-in `25-source-runtime.conf` repoints runtime to `/root/WELL`
(source IS runtime); `triadic-snapshot.service` interpreter repointed;
`biometric_inject.sh` twin-writer fixed (state → `/var/lib/well/state.json`);
`deploy-to-runtime.sh` repurposed to stamp-and-restart (no more rsync-to-/opt);
`/opt/well` → `/opt/well.retired-20260916` (reversible mv, not delete).
State canonical at `/var/lib/well/` via `/etc/well/well.env` (all four paths).
Proof: 3-way parity `source=deployed=built` drift:false via the repo's own
deploy script; **C1 permanently closed — M_WELL UNKNOWN(74h stale) → STABLE**;
arifFlow witness route live from new runtime (receipt 9fa48a47); snapshot
writer green on new interpreter. Rollback: restore drop-in removal + mv
/opt/well.retired-20260916 back + daemon-reload.

**Phase 1 #1 — EXECUTED (2026-09-16, commit 445a0f1):** `_bridge_forward` now
routes all four witness bridges (attest, dignity, recommendation, signal) via
arifFlow `POST :7073/ingest` — wire schema requires full FlowReceipt incl.
`receipt_id`+`created_at`+`cooling_decision:"None"`+formula stamps. Live-fire
proof: attest → `arifflow_receipt_id c2baf3c8`, ledger actor `well-organ`,
`f8_evidence_label: OBS` (was NONE). Kill-switch: `WELL_BRIDGE_ARIFFLOW=off`.
arifOS lane stays declared DEAD inside every bridge response — the receipt
carries the lane verdict as payload truth. Remaining in #1: mode-merge of the
four tools into `well_bridge` (rides with the v2 surface, rank #3).

---

## 6. Anti-Goals (what WELL v2 must NOT become)

1. **No verdict creep** — F12 hygiene preserved in every new plane (R/A return measurements + patterns).
2. **No second judge** — adaptation failure is *evidence routed to arifOS*, not a WELL-issued block.
3. **No duplicate scoring systems** — Reality Confidence ≠ arifFlow FQ ≠ APEX G; each named, each mapped, no silent re-scoring of the same axis.
4. **No biometric leakage** — F1: new planes carry aggregates only.
5. **No new components where an arrow suffices** — every merge is mode-consolidation of existing behavior, zero new scoring philosophies beyond the seven ratified upgrades.

---

## 7. Operating Chain (v2)

```
observe (well_machine/well_triad/well_reality)
   ↓ measure, never judge
reflect (well_human/well_classify_substrate/well_adaptation)
   ↓ readiness evidence
bridge (well_bridge → arifOS inboxes)
   ↓
arifOS verifies → AAA judges → A-FORGE executes → FRAME observes
```

WELL holds the mirror. The mirror now asks whether reality can still change
the future — and hands the answer to the court, every time.

**DITEMPA BUKAN DIBERI.**

---

## 8. External Alignment Matrix (2026-09-16, live-verified)

### 8.1 MCP spec — modelcontextprotocol.io (latest rev 2026-07-28)

| Check | Verdict | Evidence |
|-------|---------|----------|
| Tool naming `well_*` (SEP-986) | ✓ | full surface prefixed, lowercase snake |
| Initialize handshake + version negotiation | ✓ | live echo of client `2025-06-18`; capabilities: tools/prompts/resources listChanged, logging, tasks, `io.modelcontextprotocol/ui` extension |
| `serverInfo` + instructions | ✓ | name WELL, websiteUrl → well.arif-fazil.com |
| `inputSchema` per tool | ✓ | verified on all 31 via session tool defs |
| **Fallback `protocolVersion` constant** | ✗ **FIX-9** | code hardcodes `"2024-11-25"` — **not a real published revision** (typo of 2024-11-05 / 2025-11-25). Default → `2025-06-18` |
| JSON Schema 2020-12 (SEP-1613/2106), validation-error semantics (SEP-1303), pagination | ? | add to P1 conformance test plan |
| Unified Discovery (2026-07-28) | — | 2 revisions behind; non-blocking, revisit after v2 |

### 8.2 FastMCP — gofastmcp.com (current: FastMCP 4, MCP Python SDK v2)

| Check | Verdict | Evidence |
|-------|---------|----------|
| One canonical implementation | ✗ **FIX-10** | THREE trees: `/opt/well/server.py` (live, hand-rolled JSON-RPC), `well_mcp/server.py` (fastmcp.json source, 221 ln), `well_mcp_fastmcp/` (third). `fastmcp.json` declares source+port 18083 pointing at the NON-live entrypoint — config lies about production |
| Decision | → | FastMCP 4 becomes canonical vehicle for v2 mode-tools (free schema derivation, middleware, tool fingerprinting — matches registry integrity needs); archive the other two trees |

### 8.3 AAA — github.com/ariffazil/AAA

| Check | Verdict | Evidence |
|-------|---------|----------|
| Organ registration | ✓ | `federation_state.json` id=well; `nodes.json` port 18083 online |
| Registration hook | ✓ | `register_with_aaa.py --organ-id well` in ExecStartPost (skills: wellness readiness vitality human_substrate) |
| Post-v2 surface map | ⚠ | update AAA organ card at P2 when 31→10 lands |

### 8.4 arifOS — github.com/ariffazil/arifOS

| Check | Verdict | Evidence |
|-------|---------|----------|
| **WELL_ARIFOS_CONTRACT.md** | ✗ **FIX-11** | `valid_until: 2026-07-14` — expired 2 months. Documents phantom tools (`well_assess_metabolism`, `well_assess_livelihood`, `well_evidence`) and consumer `_222_witness.py` which **no longer exists** in arifOS. Rewrite as contract v2 against live surfaces |
| Live arifOS consumers | ✓ | `scripts/drift_check_live.py`, `observatory_emit.py`, `audit_connector_schemas.py`, `federation_reality_probe.py`, `build_public_state.py` reference 18083/well — these are the real contract partners |
| **Witness bridge lane** | ✗ **FIX-12 (F13 decision)** | Spec'd at arifOS `:18081` (`/attest`, `/recommendation/inbox`, `/signal/inbox`, `/dignity/handoff`) — **port dead, nothing deployed**. WELL's attest probes `:8088/attest` → 404 (C7 root cause). Options: (a) arifOS stands up :18081 bridge service, or (b) both sides mark lane DEAD; WELL bridges via VAULT999/arifFlow receipts instead |
| Naming convention `well_<verb>_<noun>` | ⚠ | documented in contract; live surface violates in 4 tools (machine_diagnose, machine_recommend, registry_status, classify_machine_state) — v2 mode-merge (`well_machine(mode=…)`) restores compliance |

### 8.5 A-FORGE — github.com/ariffazil/A-FORGE

| Check | Verdict | Evidence |
|-------|---------|----------|
| `/health` consumer | ✓ LIVE | `wellReadiness.ts` reads `WELL_HEALTH_URL ?? http://127.0.0.1:18083/health` |
| Surface guards | ✓ | `mcp-surface-guard.ts`, `deployedReality.ts` reference WELL |
| **Migration invariant** | ⚠ | `/health` response shape (status, well_score, floors_violated, freshness…) is a **frozen cross-organ contract**: v2 may ADD fields, never rename/remove. Breaking it drops A-FORGE execution-intensity adaptation |

### 8.6 arif-fazil.com

| Check | Verdict | Evidence |
|-------|---------|----------|
| Public subdomain | ✓ | `well.arif-fazil.com/health` → 200; CSP connect-src includes it; MCP serverInfo.websiteUrl points to it |
| **F4 public exposure review** | ⚠ **FIX-13** | public `/health` serves human cognitive aggregates (`clarity: 8.5`, `decision_fatigue: 2.2` — self-report). Public surface should be organ-status subset (status/version/tool_count/drift/machine); human aggregates stay localhost-gated |

### 8.7 Alignment fixes → join the phase plan

- FIX-9 (protocol constant) + FIX-10 (one FastMCP 4 impl) + FIX-11 (contract v2 rewrite) + FIX-13 (public /health redaction) → **Phase 0**
- FIX-12 (witness lane: deploy :18081 OR mark DEAD) → **Phase 0, requires F13 architectural choice** — it is the root cause of C7 and unblocks `well_bridge` having any real forward leg

### 8.8 F13 verdicts (2026-09-16) — EXECUTED

| Fix | Verdict | Execution |
|-----|---------|-----------|
| FIX-9 | SEAL | both bridge-client constants → `2025-06-18` (commit e9da7c0) |
| FIX-10 | SEAL | `well_mcp_fastmcp/` → `_archive/`; FastMCP = v2 constitutional implementation |
| FIX-11 | SEAL | contract v2 written against live surfaces; valid until 2026-12-16 |
| FIX-13 | SEAL | `/health` XFF-gated public subset `{status, organ, version}` — verified live on well.arif-fazil.com; localhost/A-FORGE full shape frozen |
| FIX-12 | **Option B** | lane :18081/:8088 **DEAD** — `_bridge_forward` returns DEAD for all four bridges; local events.jsonl stays the record; witness routes via arifFlow :7073 (first receipt `fde229c4` minted by this very mutation) |

Deployed live 2026-09-16 (commits e9da7c0, 9554982; 3-way stamps aligned; `drift:false`; rollback `/opt/well/server.py.bak-20260916-preP0`). Live-path lesson: the `@mcp.tool` wrappers in server.py delegate to `well_triad/phase3_tools.py` (`_wt_` prefix) — server.py also carries a stale module-level duplicate at ~L13800; twin-module trap confirmed a third time.

**Phase-1 constraint (from kabankan crescent 2026-09-16):** the v2 FastMCP canonical surface must carry trace correlation through the **envelope**, not ambient contextvars — FastMCP→handler contextvar propagation is proven lossy (double-emission, disjoint trace_ids). One emitter per request; handler-side inherits via envelope or stays silent.
