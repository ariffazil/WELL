<!-- SOT-MANIFEST
owner: Arif
last_verified: 2026-07-24
valid_from: 2026-07-24
valid_until: 2026-08-17
confidence: high
scope: /root/WELL
-->

# AGENTS.md — WELL | arifOS Federation

> **Human readiness mirror — REFLECT_ONLY.**
> Assesses vitality, homeostasis, dignity. Never diagnoses.
> **ZEN:** `/root/AAA/prompts/AAA-ZEN-ALIGNMENT.md` — 18 operational rules. Load at boot.

## Identity
Somatic intelligence organ. Port 18083. Tools: well_classify_substrate, well_trace_lineage, well_assess_homeostasis, well_check_repair, well_validate_vitality, well_registry_status, well_guard_dignity, well_assess_reliability.

## Build & Test
```bash
pip install -e .
pytest tests/ -q --tb=short
```

## Boundary
✅ Assess biometrics, fatigue, dignity, reliability
❌ Never emit a diagnosis — REFLECT_ONLY
❌ Never mutate vault — local-only persistence
