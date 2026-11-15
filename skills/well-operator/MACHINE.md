# MACHINE — WELL machine stewardship rules (M-WELL lane)
<!-- Sources: arifos-machine-wellness (AAA), well-machine-diagnose, live probes 2026-11-15.
     Bounded-scan discipline applies to everything in this file. -->

## 1. Signal, not verdict
WELL is a mirror. Branch on `signal` (`stable_signal | recovery_needed | readiness_low | unsafe_to_interpret | insufficient_context`), never on legacy `verdict`, never on `status` alone.
`telemetry_status != FULL` ⇒ treat output as provisional (`calm_state=assumed|unknown`).

## 2. Diagnose is the primary machine read
- VPS health question → `well_machine_diagnose`, then `well_machine_recommend` for the fix surface.
- `well_assess_reliability` historically over-alarms (it once called 2% PSI-full "all tasks stalled" and 50% zram swap DEGRADED). Those specific false alarms were fixed 2026-11-15, but the rule stands: **cross-check reliability claims against diagnose numbers** before acting.

## 3. Severity semantics (what the numbers mean)
- PSI `full_avgNN` = % of the window tasks stalled, not a live stall count. Tiers: ≥25 CRITICAL · ≥5 DEGRADED · >1 note.
- Swap % is not pressure. Gate on **disk-swap share** + memory PSI; zram occupancy with low PSI is healthy.
- Disk % alone is not a diagnosis: read the reconcile block (root cause + measured evidence) and only trust `expected_recovery_gb` on top-level targets (nested targets are zeroed).
- `severity` is machine-lane only. It never converts into a constitutional verdict.

## 4. Repair gate behaviour
- `well_check_repair` HOLD/`unsafe_to_interpret` = **"unverified"**, not "broken". It means machine evidence or policy didn't clear the bar yet.
- Machine evidence now falls back to the durable cron-fed `machine_state.json` (5-min cadence) when the live Prometheus adapter is unavailable (2026-11-15). A telemetry HOLD after that fix is a genuine anomaly → report, don't paper over.

## 5. Never flush swap
`swapoff` under pressure = OOM risk. WELL voids the swap-flush command by design (`SWAP_FLUSH_HAZARD`). The sanctioned levers, least→most disruptive: drop page cache (only when memory pressure is the true axis), kill confirmed-idle duplicates, restart a stuck process, kill confirmed orphans.

## 6. drop_caches is not "LOW risk" under pressure
It forces re-reads and spikes I/O; treat as MEDIUM when any service is latency-sensitive. Gate before any cache drop: memory PSI (not load), reclaimable cache is the actual shortfall, workload identified, authorization present.

## 7. No destructive action without approval honoured
Every recommendation with `requires_approval=true` routes to **888_HOLD** first. WELL never authorises; A-FORGE executes; Arif decides T3.

## 8. Backups on the same disk are not backups
`/root/backups/restic-repo` sits on the same filesystem it protects. Offsite copy lane = A1 (`/root/scripts/a1-offsite-restic.sh`, 888 verdict `ses_e2529006`: COPY only, verify before any local delete, A2 delete = separate 888 gate). Fallback lane = `a1-gws-upload-fallback.sh` (gws upload; rclone lane is blocked by secret-scrub design — do not work around it).
Restore test: `RESTIC_PASSWORD` is required; the repo currently opens with the password recorded in the ops receipt (not stored in this skill).

## 9. Identify the live kernel by PORT, never by PID age
`ss -tlnp | grep :8088` decides who owns the kernel. Everything else with the same cmdline and PPID=1 is a candidate orphan. Kill ONLY with all five tells (PPID=1, older than unit start, no owned port, bare cmdline, not on the avoid list). **UNKNOWN → SKIP, never kill.**

## 10. Bounded scans only
Under pressure (disk >85%, CPU PSI >25, load > cores): one scan at a time, `-maxdepth` + `-prune` on `node_modules/.venv/.git/__pycache__/caches`. No full-disk `du`/`find`, no parallel agents.

## 11. Evidence shape
Every machine claim: `[OBS]` probe output · `[DER]` derived · `[INT]` judgment. A number without an instrument does not ship.

## 12. Current machine constraints (OBS 2026-11-15 11:00 MYT)
disk 91% used (35 GB free, ~0.5 GB/day burn) · load ~9.5/8 cores · CPU PSI some ~30% · RAM 42% free · swap ~50% (zram-dominated, low PSI) · zombies 7 (stable 2 weeks) · WELL human substrate EXPIRED since 2026-11-01 (correct honest RED).
Binding constraint: **disk**. Top measured consumers: /root/runtime/hermes 22G, /root/backups 19G (incl. restic 16G), /root/.cache 16G, /root/_quarantine 6.2G (5.4G of it = F13 EXPORT-ONLY agent-store export — deletion VETOED).