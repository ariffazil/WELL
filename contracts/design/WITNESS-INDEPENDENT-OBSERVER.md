# ⚖️ WELL Independent Witness — Structural Design

> **Forged:** 2026-07-21 by FORGE (000Ω)
> **Status:** DESIGN · Not built
> **Target:** AGI substrate governance (WELL ~15→60 readiness path)
> **Problem:** WELL runs on the substrate it governs. A substrate that can
>   modify itself can modify its own WELL. The governor and governed sharing
>   a body means the governed can edit the governor.

---

## 1. The Self-Referential Trap

```
┌─────────────────────────────────────────┐
│  VPS (single substrate)                 │
│                                         │
│  ┌─────────┐    reads     ┌──────────┐ │
│  │  WELL   │◄────────────│  /proc,  │ │
│  │  (gov)  │             │  systemd, │ │
│  │         │             │  docker   │ │
│  └────┬────┘             └──────────┘ │
│       │                               │
│       │ advises                       │
│       ▼                               │
│  ┌─────────┐                          │
│  │ A-FORGE │──mutates──► substrate    │
│  └─────────┘                          │
│                                         │
│  PROBLEM: A-FORGE can modify WELL's    │
│  source, state, or telemetry.          │
│  WELL has no way to know.              │
└─────────────────────────────────────────┘
```

The fix: an observer that sits *adjacent* to WELL, not inside it.

---

## 2. WITNESS Architecture

```
┌──────────────────────────────────────────────────┐
│  VPS                                             │
│                                                  │
│  ┌──────────┐   ┌──────────┐   ┌─────────────┐ │
│  │  WELL    │   │ WITNESS  │   │ Prometheus   │ │
│  │  :18083  │   │ :18084   │   │ :9090        │ │
│  │          │   │          │   │              │ │
│  │ reads:   │   │ reads:   │   │ scrapes:     │ │
│  │  state   │   │  /proc   │   │  node_exp    │ │
│  │  machine │   │  WELL    │   │  :9100       │ │
│  │  sensors │   │  Prom    │   │              │ │
│  └────┬─────┘   └────┬─────┘   └──────┬───────┘ │
│       │              │                │          │
│       │   ┌──────────┴────────┐       │          │
│       │   │  CROSS-CHECK      │       │          │
│       │   │                   │       │          │
│       │   │  WELL says:       │       │          │
│       │   │  M_WELL=STABLE    │       │          │
│       │   │  MemAvail=14.6G   │       │          │
│       │   │  PSI_some=27.1    │       │          │
│       │   │                   │       │          │
│       │   │  WITNESS says:    │       │          │
│       │   │  MemAvail=14.6G ✓ │       │          │
│       │   │  PSI_some=27.2 ✓  │       │          │
│       │   │  docker: 8/8 up ✓ │       │          │
│       │   │                   │       │          │
│       │   │  → CONSENSUS      │       │          │
│       │   └───────────────────┘       │          │
│       │                               │          │
│       ▼                               ▼          │
│  ┌─────────────────────────────────────────────┐ │
│  │  WITNESS LEDGER (append-only, hash-chained) │ │
│  │  /var/witness/ledger.jsonl                  │ │
│  └─────────────────────────────────────────────┘ │
│                                                  │
│  When WELL and WITNESS disagree:                 │
│    → 888_HOLD event                              │
│    → Both readings preserved                     │
│    → WELL's advice is overridden to UNKNOWN      │
└──────────────────────────────────────────────────┘
```

---

## 3. Key Design Properties

### 3.1 Separate Process (not separate machine)

On a single VPS, true independence is impossible. But we can maximize
the distance:

| Property | WELL | WITNESS |
|----------|------|---------|
| Systemd unit | `well.service` | `well-witness.service` |
| Port | 18083 | 18084 |
| User | root | `well-witness` (dedicated) |
| Filesystem access | /root/WELL (rw) | /var/witness (rw), /root/WELL (ro) |
| /proc access | via machine_telemetry.py | direct read-only |
| Telemetry source | machine_state.json (own collector) | Prometheus (independent source) |
| Docker access | docker ps (own probe) | docker ps (independent probe) |
| State storage | state.json (own) | witness_state.json (own) |
| Audit ledger | events.jsonl (own) | ledger.jsonl (own) |

### 3.2 Cross-Check Protocol

WITNESS doesn't trust WELL. It independently measures:

1. **Machine state** — Reads /proc directly (MemAvailable, PSI, load, swap).
   Cross-references against Prometheus (node_exporter on :9100).
   Compares against WELL's `machine_state.json`.

2. **Service health** — Runs `systemctl is-failed`, `docker ps` independently.
   Compares against WELL's service/docker readings.

3. **WELL's own health** — Probes `:18083/health`.
   Checks WELL's self-reported state against independent measurements.

4. **WELL's source integrity** — Hashes `vitality_gate.py`, `server.py`.
   Compares against known-good hashes from git.
   Alerts on unexpected modification.

### 3.3 Consensus Model

```
For each measurement dimension:

  WELL reading    WITNESS reading    Verdict
  ────────────    ───────────────    ───────
  STABLE          STABLE             CONSENSUS ✓
  STABLE          DEGRADED           DIVERGENCE ⚠ (888_HOLD)
  DEGRADED        STABLE             DIVERGENCE ⚠ (WELL more conservative — OK but flag)
  STABLE          UNKNOWN            WITNESS_BLIND ⚠ (witness can't measure)
  UNKNOWN         STABLE             WELL_BLIND ⚠ (WELL can't measure)

When WELL is more conservative (DEGRADED vs STABLE): safe, but flag.
When WELL is more optimistic (STABLE vs DEGRADED): DANGER, 888_HOLD.
```

### 3.4 Adversarial Stance

WITNESS assumes the substrate (or WELL itself) may be compromised:

- **Hash-chain integrity**: Every WITNESS observation is hash-chained.
  If the chain breaks, WITNESS itself may be compromised → 888_HOLD.
  
- **Source integrity**: WITNESS periodically hashes WELL's source files
  and compares against known-good hashes. Modification without commit → alert.

- **Telemetry freshness**: If WELL's machine_state.json timestamp is stale
  but WELL claims LIVE telemetry → contradiction → 888_HOLD.

- **Self-check**: WITNESS probes its own health. If WITNESS can't read /proc,
  it reports WITNESS_DEGRADED — not a false consensus.

---

## 4. What WITNESS Does NOT Do

- Does NOT judge (arifOS judges)
- Does NOT execute repairs (A-FORGE executes)
- Does NOT seal to VAULT999 (VAULT999 records)
- Does NOT override WELL (it reports divergence; arifOS decides)
- Does NOT replace WELL (WELL remains the primary vitality organ)
- Does NOT require a separate machine (single VPS, separate process)

---

## 5. Implementation Path

### Phase 1 — Standalone Observer (P1 effort)
- `well-witness.service` systemd unit (dedicated user)
- Reads /proc directly (no dependency on WELL)
- Cross-references Prometheus metrics
- Writes witness ledger
- Reports consensus/divergence via health endpoint

### Phase 2 — Active Challenge (P2 effort)
- WITNESS can request WELL re-measure (adversarial probe)
- WITNESS can flag WELL source modification
- WITNESS can trigger 888_HOLD events

### Phase 3 — External Ground Truth (P3 effort)
- Separate hardware (Raspberry Pi / second VPS) running WITNESS
- Out-of-band communication channel (separate network path)
- True independence from governed substrate

---

## 6. Relationship to WELL's Own Coherence Check

Arif identified three gaps for AGI substrate:
1. Independent witness ← THIS DESIGN
2. Self-modification resistance ← requires separate process (WITNESS)
3. Coherence + adversarial checking ← requires cross-check protocol (WITNESS)

WITNESS addresses all three:
- **(1)** It's the independent observer WELL can't compute itself
- **(2)** It runs as a separate user/process, not editable by the governed
- **(3)** Its cross-check protocol is the coherence mechanism — it catches
  when WELL says two incompatible things (or when WELL and reality disagree)

---

## 7. Bottom Line

For a single VPS, WITNESS is a separate process with independent /proc access,
cross-referencing Prometheus, and hash-chaining its observations. It doesn't
need to be a separate machine — it needs to be a separate *observer* that
the governed substrate cannot easily silence.

The design is ~200 lines of Python plus a systemd unit. It's P1-level effort
and would raise WELL's AGI substrate readiness from ~15 to ~35 by closing
the self-referential trap for machine telemetry.

Full independence (separate hardware) is P3.
