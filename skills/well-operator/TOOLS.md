# TOOLS — the 10 live WELL tools, inputs, and what outputs MEAN
<!-- Validated live 2026-11-15 (well_registry_status mode=full → REGISTRY_PASS 10/10). -->

## Common envelope (all tools)

| Field | Meaning | Read it as |
|---|---|---|
| `signal` | Advisory signal: `stable_signal`, `recovery_needed`, `readiness_low`, `unsafe_to_interpret`, `insufficient_context` | **Use this for logic.** |
| `verdict` | Legacy compat (`PASS/HOLD/...`) | Do not branch on it. |
| `telemetry_status` | `FULL` / `PARTIAL` / `unknown` | `unknown` degrades signal to `insufficient_context` by design (false-calm guard). |
| `calm_state` | `observed` / `assumed` / `unknown` | `assumed` = telemetry stale; treat results as provisional. |
| `aaa.risk_tier` | `T0` stable · `T1` recovery_needed · `T3` readiness_low · `T5` unsafe | Downstream autonomy hint. |
| `constitution_hash` | Hash of WELL's constitutional surface (domain law + advisory boundary + sovereign authority) | Distinct from `substrate_manifest_hash` since 2026-11-15. |
| `substrate_manifest_hash` | Hash of the substrate manifest (identity anchor) | Identity, not behaviour. |

## 1. well_machine_diagnose
- Input: none. Runs bounded scans over machine_state.json (+ disk evidence).
- Outputs: `severity` (GREEN/AMBER/RED/CRITICAL), `signal`, `issues[]` (each a sentence with numbers), `recommendations[]` (`recommendation_id`, `target`, `expected_recovery_gb`, `risk`, `requires_approval`, `worth_it`, `nested_duplicate_of_parent`), `binding_constraint` semantics via reconcile block.
- **Meaning traps:**
  - PSI `full_avgNN` = fraction of the window that tasks stalled — NOT "tasks stalled now". ≥25 CRITICAL / ≥5 DEGRADED / >1 note (fixed 2026-11-15).
  - Swap % alone is not pressure: zram-dominated swap with low memory PSI is healthy (fixed 2026-11-15).
  - `expected_recovery_gb` on nested targets is 0 and `nested_duplicate_of_parent=true` — the parent already counts those bytes (fixed 2026-11-15).
  - `severity` is a machine-lane summary; do not promote it to a constitutional verdict.

## 2. well_machine_recommend
- Input: `issue_type` = `swap|memory|disk|service|docker|zombie|all`.
- Output: `signal` + `aaa.risk_tier` derived from the SAME data it read (disk ≥90% or PSI pressure ⇒ `RECOVER`/`recovery_needed`/T1 — fixed 2026-11-15), `data.binding_constraint`, per-command `risk` / `blast_radius` / `reversible` / `requires_approval`.
- Traps: `safe:false` blocks are intentional; swap-flush command is voided (hazard). `requires_approval` commands go to 888_HOLD first.

## 3. well_assess_reliability
- Input: `mode` (reliability views). M-lane assessment of machine/tool/institution reliability.
- Traps: historically over-alarms (claims, e.g., "all tasks stalled" on tiny PSI-full). Prefer `machine_diagnose` for VPS questions; use this for tool/institution reliability, checking the numbers it cites against diagnose.

## 4. well_classify_substrate
- Input: `mode` (substrate classes). Output: substrate class + boundary observations.
- Use before deciding *what kind of thing* a request touches (human vs machine vs institution).

## 5. well_validate_vitality
- Input: `mode` (`readiness|...`), intent/context/task_description.
- Output: readiness + risk_level + `recommended_mode` + `decision_ceiling` (authority: arifOS), `human_confirmation_required`.
- Trap: no state timestamp → `UNKNOWN`/`pause`; state age >168h → `DO_NOT_INFER`. This is CORRECT behaviour. Never inject numbers to green it.

## 6. well_assess_homeostasis
- Input: mode. Output: regulation/stability/empathic balance fields.
- Advisory; combine with vitality when answering readiness questions.

## 7. well_guard_dignity
- Input: mode (dignity contexts). Output: boundary/consent/dignity findings.
- Run before agent output that characterises a real person; it does not authorise publication.

## 8. well_check_repair
- Input: `mode=precheck|postcheck`, `task_description`, `decision_class`, `outcome`.
- Output: op_class (DIAGNOSTIC_READ / BUILD_COMPUTE / ...), pressure policy verdict, allowlist options, `action_note`.
- **Treat `unsafe_to_interpret` / HOLD as "not verified yet"** — not as proof something is broken. Machine evidence now falls back to the durable 5-min `machine_state.json` (2026-11-15), so a telemetry HOLD here is a real anomaly worth reporting.

## 9. well_trace_lineage
- Input: mode (lineage views). Output: provenance chain for a decision packet.
- Use for "where did this claim come from" questions.

## 10. well_registry_status
- Input: `mode=status|full`. Output: `intended/registered/exported/callable` counts, `phantom_tools_count`, `missing_public_tools_count`, `verdict=REGISTRY_PASS`.
- **The only authority for "what tools exist".** If a skill names a tool not in this list, the skill is stale, not the organ.

## Freshness semantics (state.json lane)
- `freshness.status` (`fresh`/`stale`/`expired`) keys on the record's timestamp; `freshness.age_seconds` + `human_substrate.age_hours` + `honesty_banner` are the ground truth trio.
- `well_score: null` + `INSUFFICIENT_DATA` + `honesty: INSUFFICIENT` = honest mirror with no sovereign data. NEVER "fix" it by injecting vitals.