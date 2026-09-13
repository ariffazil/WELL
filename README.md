<!-- SOT-MANIFEST
owner: Muhammad Arif bin Fazil (F13 SOVEREIGN)
federation_release: v2026.09.13
last_verified: 2026-09-13T06:32:00Z
live_commit: 4e4e04c
live_health: degraded (OBS 2026-09-13) — REFLECT_ONLY, no autonomy escalation
tools_live: 31 (canonical, live-witnessed via :18083/health)
authority_ceiling: REFLECT_ONLY
apex_zen: A2A delegates ⊥ MCP equips ⊥ ACT mutates ⊥ arifOS governs ⊥ F13 decides
honesty: H-WELL is SELF_REPORT/AGED until biometric inject; M-WELL machine_state.json is separate
mesh: thermal observes KVM8 organs + KVM4 LiteLLM/OpenClaw + KVM2 witness fork — not extra judges
truth_rule: live :18083/health + tools/list beat any static count in prose
holds: biometric telemetry never on public or extended A2A cards
-->

# WELL — Biometric Monitoring & Vitality Engine

## AI-powered readiness intelligence for humans, machines, and institutions.

WELL makes invisible readiness visible before decisions become consequences. It monitors biometric state, machine health, governance coherence, and coupled risk — surfacing degradation signals before they become failures.

**The mirror never commands. The sovereign decides.**

Licensed under **AGPL-3.0**.

---

## The Problem

Most failures happen long before the failure event:
- **Operator fatigue** hides as overconfidence
- **System degradation** hides as "mostly working"
- **Governance decay** hides as "process compliance"
- **Burnout** hides as discipline

Traditional monitoring tools track uptime and metrics. They miss the human element, the coupling risk, and the slow drift that precedes every major incident.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    WELL Readiness Engine                       │
│  Port :18083  ·  MCP Interface  ·  31 Tools                  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐ │
│  │  H-WELL      │  │  M-WELL      │  │  G-WELL            │ │
│  │  Human       │  │  Machine     │  │  Governance        │ │
│  │  Readiness   │  │  Diagnostics │  │  Coherence         │ │
│  └──────┬───────┘  └──────┬───────┘  └─────────┬──────────┘ │
│         │                 │                     │           │
│  ┌──────▼─────────────────▼─────────────────────▼──────────┐│
│  │              WELL Fusion Layer                           ││
│  │  C-WELL (Coupled Risk) · U-WELL (Substrate Classify)    ││
│  └──────────────────────────┬──────────────────────────────┘│
│                             │                               │
│  ┌──────────────┐  ┌───────▼───────┐  ┌──────────────────┐ │
│  │  Biometric   │  │ Vitality      │  │  Homeostasis     │ │
│  │  Ingestion   │  │ Gate          │  │  Monitor         │ │
│  └──────────────┘  └───────────────┘  └──────────────────┘ │
│                                                              │
└──────────────────────────┬───────────────────────────────────┘
                           │ MCP
                    ┌──────▼──────┐
                    │  arifOS      │
                    │  :8088 MCP   │
                    └─────────────┘
```

---

## Quick Start

### Docker

```bash
git clone https://github.com/arif-fazil/WELL.git
cd WELL
docker compose up -d

# Verify
curl http://localhost:18083/health
curl http://localhost:18083/tools/list
```

### Local Development

```bash
cd WELL
pip install -e .
python -m well.server --port 18083
```

---

## The Five Readiness Axes

| Axis | What It Monitors | Key Signals |
|------|------------------|-------------|
| **H-WELL** (Human) | Vitality, fatigue, dignity, consent | Energy levels, sleep quality, stress markers |
| **M-WELL** (Machine) | System health, tool integrity, compute limits | CPU, RAM, disk, PSI, zombie processes, Docker |
| **G-WELL** (Governance) | Autonomic coherence, constitutional floor compliance | Floor pass rates, seal chain integrity |
| **C-WELL** (Coupled) | Human state × Machine state coupling risk | Elevated risk when tired operator + degraded system |
| **U-WELL** (Understanding) | Substrate classification, vitality assessment | Machine state classification, phase analysis |

---

## Capabilities

### Biometric Ingestion
- Consent-scoped biometric data intake
- Substance and recovery event logging
- Multi-source biometric fusion
- Privacy-preserving data handling

### Triadic State Assessment
- 5-phase wellness pipeline (Sense → Classify → Recommend → Propose → Seal)
- Human vitality scoring with explicit confidence levels
- Machine health diagnostics (CPU, RAM, swap, disk, PSI, services, Docker)
- Governance coherence scoring against constitutional floors

### Homeostasis Monitoring
- Drift detection across all readiness axes
- Trend deterioration alerts
- Baseline comparison and deviation tracking
- Dignity governance — respects human autonomy

### Machine Diagnostics
- Real-time system pressure monitoring
- Zombie process detection and alerting
- Service degradation analysis
- Swap and memory pressure tracking

### Vitality Gate
- Constitutional fusion layer combining all readiness signals
- Weakest substrate determines overall assessment
- Four mirrors → one gate pattern (same as ART → Kernel → ACT)
- Outputs: `ready`, `caution`, `degraded`, `unsafe`

---

## Honesty by Design

WELL prefers **honest degradation over fabricated certainty**. When biometric data is mock/test (no live sensor feeds), WELL reports degraded status with reduced confidence. This is not a bug — it is a feature that prevents false confidence.

```json
{
  "status": "degraded",
  "reason": "biometric source is mock/test data, not live sensor feeds",
  "confidence": "reduced",
  "final_authority": "HUMAN"
}
```

---

## Use Cases

| Domain | Application | Value |
|--------|-------------|-------|
| Corporate Wellness | Operator readiness monitoring | Prevent burnout, improve sustainability |
| DevOps/SRE | Machine + human coupled risk | Avoid incidents caused by tired operators |
| Healthcare | Personal vitality tracking | Early warning of health deterioration |
| AI Safety | Agent readiness before action | Distinguish unable/unavailable/unsafe/unready |
| Clinical Support | Biometric trend analysis | Long-term health monitoring with governance |

---

## MCP Interface

WELL exposes 31 canonical tools via MCP (Model Context Protocol):

`well_assess_*` · `well_check_*` · `well_classify_*` · `well_consent_*` · `well_frame_*` · `well_get_*` · `well_guard_*` · `well_inject_biometric` · `well_log_*` · `well_machine_*` · `well_observe_*` · `well_propose_*` · `well_render_hud_panel` · `well_seal_*` · `well_trace_lineage` · `well_validate_vitality`

Full tool list: `curl http://localhost:18083/tools/list`

---

## Federation Role

WELL is the readiness monitor in the arifOS federation. It holds a mirror — it never commands, diagnoses with authority, or judges.

**GEOX** = truth about reality · **WEALTH** = truth about consequences · **WELL** = truth about readiness

**ARIF vetoes. arifOS judges. AAA routes. A-FORGE executes.**

**Sister Repos:**
- [arifOS](https://github.com/arif-fazil/arifOS) — Constitutional kernel
- [AAA](https://github.com/arif-fazil/AAA) — Intelligence routing
- [A-FORGE](https://github.com/arif-fazil/A-FORGE) — Execution engine
- [GEOX](https://github.com/arif-fazil/GEOX) — Earth sciences
- [WEALTH](https://github.com/arif-fazil/WEALTH) — Capital management
- [arifFlow](https://github.com/arif-fazil/arifFlow) — Workflow orchestration

---

## Documentation

- [Full Technical README](docs/README-FULL.md)
- [Governance](docs/GOVERNANCE.md)
- [Schema Migration](docs/SCHEMA_MIGRATION.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Changelog](CHANGELOG.md)
- [Security Policy](SECURITY.md)
- [Contributing](CONTRIBUTING.md)

---

## License

**GNU Affero General Public License v3.0 (AGPL-3.0)**

This program is free software: you can redistribute it and/or modify it under the terms of the GNU AGPL v3.0. See [LICENSE](LICENSE) for the full text.

---

**DITEMPA BUKAN DIBERI** — Forged, Not Given.

Built by Muhammad Arif bin Fazil.
