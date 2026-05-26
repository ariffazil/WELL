# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v2026.05.26] - 2026-05-26
### Changed
- **PHOENIX-73F**: MCP surface collapse (1A+1B+1C) — 79 tools → 51 decorators → 45 live
  - Step 1A: 28 internal helpers hidden (decorator removed, functions intact)
  - Step 1B: 3 mode-bearing tools fail-closed (well_assess_livelihood, well_assess_metabolism, well_guard_dignity) — delegation chain bugs
  - Step 1C: 3 absorptions (well_contrast_report→well_state, well_fatigue_accumulator→homeostasis, mcp_health_check→reliability)
- **MCP Endpoint**: `https://well.arif-fazil.com/mcp` — Caddy route fixed (was 8083, now 18083)
- **Transport**: `streamable-http` (latest MCP protocol) — not SSE

### Known Issues
- 3 mode delegation chains blocked (888_HOLD): livelihood, metabolism, guard_dignity — require human approval to fix
- 13 stage aliases still exposed pending Step 2

## [v2026.05.17] - 2026-05-16
### Added
- **`well_contrast_report` tool**: W→P→C→M→G→J metabolic loop for anomalous biological contrast detection.
  - W: Load events.jsonl rolling window (14 days, test-filtered).
  - P: `_compute_baseline` — rolling mean/stdev per dimension (well_score, violations, urgency).
  - C: `_detect_contrast` — z-score anomaly detection (z ≥ 1.5 threshold).
  - M: `_infer_meaning` — pattern-match anomaly to biological hypotheses.
  - G: W-floor guard routing + severity tier.
  - J: Severity tier + recommended_action (advisory) + w_floor_flags.
- **Severity tiers**: NORMAL / WATCH / CONCERN / CRITICAL.
- **Test contamination guard**: Events with "test", "Test", or "mocked" in `note` are excluded from baseline.
- **Baseline requires stdev > 0**: z_violations only computed when violation counts have variance.
- **9 new contrast tests** in test_well.py (all pass).

### Fixed
- **`get_standard_envelope` claim_state bug**: Error branches pass `claim_state` as explicit kwarg to prevent INGESTED default from overriding NO_VALID_EVIDENCE.

### Security
- W0 authority invariant: all outputs HYPOTHESIS-tagged; advisory verbs only; recommended_action is non-binding.

## [v2026.05.01] - 2026-05-01
### Added
- **WELL Kanon**: Unified 13-tool surface (31 legacy tools → 13 canonical verbs).
- **Identity Invariant (W0)**: Immutable `identity: WELL`, `role: Body`, `authority: REFLECT_ONLY`.
- **Physically-Grounded Readiness**: No telemetry → UNKNOWN; cognitive entropy grounded in live scores.
- **Three-Layer Health Model**: Service liveness → Instrument validation → Domain truth verification.
- **W-Invariant**: Fatigue correctness fix; forge closeout now correctly increments biological load.
- **A-FORGE Compatibility**: 31 legacy wrappers maintained for backward compatibility.

---

⬡ DITEMPA BUKAN DIBERI — WELL BIOLOGICAL MIRROR ACTIVE ⬡
