# WELL ↔ arifOS Cross-Repo Contract (v2)

> **SOT-MANIFEST**
> owner: Arif
> last_verified: 2026-09-16 (FI-003 live alignment audit)
> valid_from: 2026-09-16
> valid_until: 2026-12-16
> confidence: high (all consumers live-probed)
> scope: /root/WELL, /root/arifOS, /root/A-FORGE, /root/AAA
> supersedes: v1 (2026-05-08/26) — expired 2026-07-14; documented the historical WELL
> seal: DITEMPA BUKAN DIBERI

## 1. Purpose

Canonical contract between **WELL** (substrate vitality mirror, REFLECT_ONLY)
and the federation. v1 documented tools and consumers that no longer exist
(`well_assess_metabolism`, `well_assess_livelihood`, `well_evidence`,
`well_arifos_packet` as tool; consumer `_222_witness.py`). This v2 is written
against **live-verified surfaces only** (2026-09-16 audit).

**Golden rule (unchanged):** WELL reflects. arifOS judges. The operator decides.

## 2. Responsibility Matrix (live surface)

| Concern | WELL (owner) | Federation (consumer) |
|---------|--------------|----------------------|
| Human readiness | `well_validate_vitality`, `well_assess_homeostasis` | arifOS, A-FORGE |
| Machine reliability | `well_machine_diagnose`, `well_assess_reliability` | A-FORGE, arifOS probes |
| Triadic composition | `well_assess_triadic_state` + `/state/triadic_snapshot.json` | HUD, AAA cockpit, FRAME |
| Substrate classification | `well_classify_substrate` | any |
| Health heartbeat | `GET /health` (:18083) | **A-FORGE `wellReadiness.ts`**, arifOS probe scripts |
| Witness/attest lane | **DEAD** (§5) | — |

## 3. Canonical Handoff: `GET /health` (frozen shape, add-only)

A-FORGE `src/domain/governance/wellReadiness.ts` reads
`WELL_HEALTH_URL ?? http://127.0.0.1:18083/health`. The localhost response is a
**frozen cross-organ contract**: fields may be ADDED, never renamed or removed.
Key fields consumed today: `status`, `well_score`, `floors_violated`,
`freshness`, `machine_substrate`, `authority_ceiling`, `drift`.

### 3.1 Public vs Private (F4, 2026-09-16 FIX-13)

Requests carrying `X-Forwarded-For` (i.e. proxied via Caddy from
`well.arif-fazil.com`) receive the **public subset only**:

```json
{"status": "healthy", "organ": "WELL", "version": "v2026.07.24"}
```

Human cognitive aggregates (`clarity`, `decision_fatigue`, sleep, stress)
are **localhost-only**. Direct 127.0.0.1 consumers (A-FORGE, arifOS scripts)
are unaffected — they do not send XFF.

## 4. Live Consumers (verified 2026-09-16)

| Consumer | Repo | Surface used |
|----------|------|--------------|
| A-FORGE execution-intensity adaptation | A-FORGE `wellReadiness.ts` | `/health` (full, localhost) |
| A-FORGE surface guards | `mcp-surface-guard.ts`, `deployedReality.ts` | MCP + `/health` |
| arifOS probes | `scripts/drift_check_live.py`, `observatory_emit.py`, `audit_connector_schemas.py`, `federation_reality_probe.py`, `build_public_state.py` | :18083 |
| AAA organ registry | `state/federation_state.json`, `nodes.json`; registered via `register_with_aaa.py` (ExecStartPost) | registration |
| HUD / cockpit | `/state/triadic_snapshot.json` (written by `triadic-snapshot.timer` → HTTP `:18083/well_assess_triadic_state`) | snapshot |
| Public site | `well.arif-fazil.com` (Caddy → :18083) | `/health` public subset |

## 5. Witness / Attest Lane — DEAD (F13 Option B, 2026-09-16)

The arifOS bridge lane (`:18081` `/attest`, `/recommendation/inbox`,
`/signal/inbox`, `/dignity/handoff`) was **never deployed**; WELL's attempts
returned 404 (root cause of the 2026-09-16 "4 dead bridges" finding C7).

**Ruling:** lane DEAD. Rationale: async witness is already proven via
Graphiti-era receipts + arifFlow; the lane carries no authority, witness, or
adaptation capability that receipts do not. *Lane exists ≠ lane needed;
observed capability = lane justified.*

**Witness routing:** WELL attestations and governance proposals route via
**arifFlow :7073 `flow_ingest`** (wired as `well_bridge` in WELL v2 Phase 1 —
see `docs/WELL_V2_APEX_ZEN_MUTATION_GUIDE.md`). Until then, attestations are
recorded locally (`events.jsonl`) with `bridge.status = DEAD` declared
honestly in the tool response.

## 6. Pre-Consequential-Action Gate (PHOENIX-73F, unchanged)

Before C3+ consequential output, orchestrators call
`well_assess_homeostasis(mode="fatigue", decision_class=...)` →
`route_verdict: PROCEED | DEFER | ADVISORY_BLOCKED` (advisory only; arifOS
adjudicates). Decision-class table C1–C5 as in v1 §9.

## 7. Naming & Versioning

- WELL tools: `well_<verb>_<noun>` (v1 convention). Live exceptions
  (`machine_diagnose`, `machine_recommend`, `registry_status`,
  `classify_machine_state`) are resolved by the v2 mode-merge
  (`well_machine(mode=...)` etc.).
- Version: `schema_version` inside payloads; contract version = this file's
  `last_verified`.
- Compatibility: consumers must parse both unified and legacy shapes for 2
  epochs after breaking change (unchanged).

## 8. Canonical Files

| File | Role |
|------|------|
| `WELL_ARIFOS_CONTRACT.md` (this file) | provider-side contract v2 |
| `docs/WELL_V2_APEX_ZEN_MUTATION_GUIDE.md` | v2 mutation SOT (7 upgrades, 31→10) |
| `tools_sot.yaml` | tool surface SOT |
| `server.py` | live implementation (deployed via /opt/well until state-migration Phase 1) |

## 9. Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-05-08 | v1.0 — unified substrate packet | Arif |
| 2026-05-26 | v1.1 — PHOENIX-73F routing protocol | PHOENIX-73F |
| 2026-09-16 | **v2.0** — rewritten against live surfaces; expired-v1 retired; `/health` frozen + public/private split (FIX-13); attest lane DEAD → arifFlow routing (FIX-12 Option B) | FI-003 under F13 |

**DITEMPA BUKAN DIBERI.**
