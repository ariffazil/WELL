# WELL State Schema Migration — Old ↔ New

> **Forged:** 2026-06-17 by FORGE (000Ω)
> **Scope:** `state.json` at `/root/WELL/state.json` (or
> `/var/lib/arifosmcp/WELL/state.json` when running under systemd)
> **Authority:** Sovereign biometric data — Arif only.

---

## 0. Why this file exists

`state.json` has lived in **two formats** since the AFWELL State Schema
was bumped to **v2026.05.12**.  The legacy format was never migrated.
This file is the canonical map between them, plus the migration recipe.

---

## 1. The Two Schemas

### Old schema (legacy, pre-2026.05.12)

```json
{
  "timestamp": "2026-04-30T00:00:00+00:00",
  "operator_id": "arif",
  "metrics": {
    "cognitive": {
      "clarity": 10,
      "decision_fatigue": 4.1
    }
  },
  "well_score": 91.8,
  "floors_violated": [],
  "environment": "TEST",
  "reason": "Mocked healthy state for test session",
  "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT"
}
```

**Markers:**
- `environment: "TEST"` (production state should be `"PROD"`)
- `reason: "Mocked healthy state for test session"` (synthetic)
- No `biometric` block
- No `delta_s` / `peace2` / `kappa_r` / `rasa` / `amanah` fields

### New schema (AFWELL v2026.05.12, current)

```json
{
  "schema": "AFWELL State Schema v2026.05.12",
  "timestamp": "<ISO 8601 UTC>",
  "operator_id": "arif",
  "biometric": {
    "delta_s": 0.2,
    "peace2": 0.7,
    "kappa_r": 0.6,
    "rasa": "clear",
    "amanah": 0.9
  },
  "metrics": {
    "cognitive": {
      "clarity": 7.5,
      "decision_fatigue": 2.0
    }
  },
  "well_score": 85.0,
  "floors_violated": [],
  "backend_status": "STABLE",
  "last_successful_read": "<ISO 8601 UTC>",
  "last_successful_write": "<ISO 8601 UTC>",
  "state_file_access": "PASS",
  "vault_access": "OK",
  "test_contamination": "NO",
  "contamination_quarantined": false,
  "confidence": "HIGH",
  "freshness": "FRESH",
  "truth_status": "VERIFIED",
  "environment": "PROD",
  "telemetry_confidence": "HIGH",
  "reason": "Sovereign biometric injection (biometric_inject.sh)",
  "safe_mode": "off",
  "arif_decision_required": false,
  "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT"
}
```

**Markers:**
- `environment: "PROD"`
- `schema: "AFWELL State Schema v2026.05.12"`
- Has `biometric` block with the 5 readiness fields
- `truth_status: "VERIFIED"`
- `freshness: "FRESH"`

---

## 2. How WELL Handles Both Formats

`/root/WELL/server.py` reads both schemas.  The /health endpoint reports
`freshness_band: "VOID"` and `owner_summary.color: "RED"` whenever the
state.json is in the OLD format with `environment: "TEST"`.  This is by
design — it forces the operator to inject a real PROD state.

When a real (new-schema) state.json is present, the /health endpoint
returns:
- `freshness.status: "fresh" | "stale" | "expired"` (computed from age)
- `owner_summary.color: "GREEN" | "AMBER" | "RED"` (computed from score + age)

---

## 3. The Migration Recipe

**This is the only path to turn WELL from RED to GREEN.**  It is
operator-only — no agent can run it on Arif's behalf.

### Option A — Interactive (recommended first time)

```bash
/root/WELL/biometric_inject.sh
```

The script will:
1. Show the current (stale) state.
2. Ask for each of the 5 readiness fields one at a time, in plain
   language.
3. Compute `well_score` transparently.
4. Show exactly what it's about to write.
5. Wait for `yes` to commit.
6. Write atomically (with .bak).
7. Restart `well.service`.
8. Verify `/health` turned green.

### Option B — Non-interactive (script-friendly)

```bash
/root/WELL/biometric_inject.sh --non-interactive \
  --delta-s 0.2 --peace2 0.7 --kappa-r 0.6 \
  --rasa "clear" --amanah 0.9
```

### Option C — Per-signal self-report (NEW 2026-06-17)

For the 13-signal coverage gaps (S05–S11), you can inject per-signal
values directly:

```bash
/root/WELL/biometric_inject.sh --signals \
  --signal-s05-sleep '{"hours": 7.5, "quality": 8, "debt_days": 0}' \
  --signal-s06-metabolic '{"glucose_stable": true, "energy_level": 7}' \
  --signal-s07-nutrition '{"water_ml": 1800, "meals": 2}' \
  --signal-s08-movement '{"steps": 4200, "strength_sessions": 0}' \
  --signal-s09-pain '{"level": 1, "sites": []}' \
  --signal-s11-stress '{"subjective_load": 3, "anxiety": 2}'
```

This populates a `signals` block in `state.json` so the 13-signal
coverage can advance from "missing" to "active" for each injected
signal.

### Option D — Dry-run (preview only)

```bash
/root/WELL/biometric_inject.sh --dry-run
```

Shows what would be written, writes nothing, doesn't restart.

---

## 4. Reversibility

- `state.json` is overwritten with `state.json.bak` kept for 24h.
- Restoring: `cp /root/WELL/state.json.bak /root/WELL/state.json && systemctl restart well`
- The script never touches anything outside `state.json`, `state.json.bak`,
  and the `well.service` restart.
- All operations are atomic (write to `.tmp` then `os.replace`).

---

## 5. What does NOT migrate

- Old-format `state.json` files older than 7 days should be archived, not
  migrated — the data is no longer reflective of the operator's state.
- Test-environment state.json (`environment: "TEST"`) should be replaced
  with a real PROD injection, not migrated.
- Cloud mirror (Supabase) state is authoritative; local state.json is
  the witness copy.  Migrations are local-first, then cloud sync.

---

## 6. Files that reference this migration

| File | What it does |
|------|--------------|
| `/root/WELL/biometric_inject.sh` | The migration script |
| `/root/WELL/SNOOZE_BIOMETRIC.md` | User-facing guide |
| `/root/WELL/snooze_check.sh` | Cron entry that nudges if state is stale |
| `/root/WELL/state.json` | The state file (current or stale) |
| `/root/WELL/state.json.bak` | Most recent backup (24h window) |
| `/root/WELL/server.py` | The FastMCP server that reads state.json |
| `/var/lib/arifosmcp/WELL/state.json` | Canonical path when run under systemd |

---

**DITEMPA BUKAN DIBERI — Readiness is forged, not assumed.**
