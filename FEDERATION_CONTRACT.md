# FEDERATION CONTRACT — WELL (Human Readiness)

> **This organ operates under the arifOS Constitutional Federation.**
> **Canonical contract:** [ariffazil/arifos/FEDERATION_CONTRACT.md](https://github.com/ariffazil/arifos/blob/main/FEDERATION_CONTRACT.md)
> **Kernel canon:** [ariffazil/arifos/GENESIS/000_KERNEL_CANON.md](https://github.com/ariffazil/arifos/blob/main/GENESIS/000_KERNEL_CANON.md)
> **WELL-specific hooks:** [`FEDERATION_HOOKS.md`](./FEDERATION_HOOKS.md)
> **Schema migration path:** [`SCHEMA_MIGRATION.md`](./SCHEMA_MIGRATION.md)

## Organ Identity

| Field | Value |
|-------|-------|
| **Organ** | WELL — Human Readiness |
| **Repo** | `ariffazil/well` |
| **Port** | 18083 |
| **Role** | Reflect-only human vitality mirror |
| **Floors enforced** | F5 PEACE², F6 EMPATHY, F7 HUMILITY, F9 ANTIHANTU |
| **APEX** | Legacy 888 JUDGE health probe (port 3002); deliberation moved to AAA a2a |
| **License** | AGPL-3.0 |

## Boundaries

**OWNS:** Sleep, fatigue, stress, cognitive clarity, dignity metrics, metabolic flux.
**NEVER:** Make medical diagnoses, judge fitness for duty, adjudicate constitutional verdicts.

## Federation Hooks (canonical entry: `FEDERATION_HOOKS.md`)

WELL participates in the federation through three explicit hooks, all
**fail-open** and **REFLECT_ONLY**:

| # | Hook | Direction | Peer organ | Purpose |
|---|------|-----------|-----------|---------|
| **S12** | `well_handoff_dignity_to_arifos()` | WELL → arifOS | arifOS 888_JUDGE | Dignity breach signal escalation (constitutional deliberation) |
| **S13** | `well_handoff_livelihood_to_wealth()` | WELL → WEALTH | WEALTH | Capital/cashflow evidence pull for S13 livelihood signal |
| **ATTEST** | `well_attest_to_kernel()` | WELL → arifOS | arifOS kernel | Active organ attestation (record state in kernel registry) |
| **GENERAL** | `well_get_packet(target="arifos")` | WELL → arifOS | arifOS | Generic biological readiness handoff (pre-existing) |
| **GATEWAY** | `well_get_health(mode="status")` (gateway) | WELL ↔ federation | All peers | Status / connect / handoff / manifest |
| **HEARTBEAT** | external `organ_heartbeat_daemon` polls `/health` | → WELL | arifOS | One-way health probe (read-only) |

**Authority contract:** WELL only emits `signal` (per GENESIS/004 §2.1).
WELL never emits `verdict` (SEAL/HOLD/VOID/SABAR/PASS/FAIL) — those belong
to arifOS 888_JUDGE alone.

**Fail-open contract:** If the peer organ is unreachable, the hook returns
`fail_mode: "federation_unavailable"` with the packet preserved for later
retry.  The hook never raises, never blocks the caller, never escalates
to 888_HOLD automatically — the operator decides.

## Contract Compliance

- [x] Points to kernel SoT from README
- [x] Has GENESIS/ (004-012)
- [x] Surfaces organ identity in /health
- [x] Routes irreversible actions through arifOS 888 JUDGE
- [x] Maintains AGENTS.md with federation boot sequence
- [x] **NEW 2026-06-17:** Explicit S12 handoff to arifOS (dignity)
- [x] **NEW 2026-06-17:** Explicit S13 handoff to WEALTH (livelihood)
- [x] **NEW 2026-06-17:** Active organ_attest to arifOS kernel
- [x] **NEW 2026-06-17:** Dual-schema state.json migration path documented

**DITEMPA BUKAN DIBERI — 999 SEAL ALIVE**
