---
id: well-machine-diagnose
name: M-WELL Machine Diagnostics
version: 1.0.0
description: M-WELL VPS diagnostics lane — canonical machine health. USE WHEN: 'VPS health', 'CPU/RAM/disk pressure', 'PSI', 'zombies', 'swap issue', 'service degradation'. Covers: well_machine_diagnose (reads machine_state.json cron telemetry — CPU, RAM, swap, disk, PSI, services, Docker, zombies with per-issue RECOMMENDATIONS) → well_machine_recommend (maps issue_type → concrete shell commands with risk assessment, ADVISORY_ONLY) → well_assess_reliability. Iron rules: use well_machine_diagnose NOT well_assess_reliability for VPS optimization workflows (canonical); WELL recommends, A-FORGE executes via forge_shell; never run recommended commands without authority band check.
owner: 333-AGI
risk_tier: low
floor_scope: [F1, F2, F7, F11]
autonomy_tier: T1
organ_domain: well
forged: 2026-09-04
---

# M-WELL Machine Diagnostics

M-WELL VPS diagnostics lane — canonical machine health. USE WHEN: 'VPS health', 'CPU/RAM/disk pressure', 'PSI', 'zombies', 'swap issue', 'service degradation'. Covers: well_machine_diagnose (reads machine_state.json cron telemetry — CPU, RAM, swap, disk, PSI, services, Docker, zombies with per-issue RECOMMENDATIONS) → well_machine_recommend (maps issue_type → concrete shell commands with risk assessment, ADVISORY_ONLY) → well_assess_reliability. Iron rules: use well_machine_diagnose NOT well_assess_reliability for VPS optimization workflows (canonical); WELL recommends, A-FORGE executes via forge_shell; never run recommended commands without authority band check.

## Provenance

Forged 2026-09-04 by 333-AGI (session SEAL-83defc585b5a4296) from live organ tool surfaces + FEDERATION_SKILL_PROFILE gap analysis. Source of truth: the organ MCP surface itself — when skill and tool surface disagree, the tool surface wins and this skill must be revised.
