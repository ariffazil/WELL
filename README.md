<!-- SOT-MANIFEST
federation_release: v2026.07.20-ZEN-CONVERGENCE
last_verified: 2026-07-20T16:25Z
live_commit: 88e3d8a
port: 18083
domain_law: SUBSTRATE_LAW
mcp_tools_live: 8
authority: REFLECT_ONLY — never diagnose
health_status: DEGRADED (apex_scalars UNMEASURED — known, non-blocking)
truth_rule: tools/list + /health beat any static count in prose
a2a_agent_json: /root/WELL/.well-known/agent.json
-->

[![Agentic CI](https://github.com/ariffazil/well/actions/workflows/agentic-ci.yml/badge.svg?branch=main)](https://github.com/ariffazil/well/actions/workflows/agentic-ci.yml)
[![🫀 REFLECT](https://img.shields.io/badge/%F0%9F%AB%80%20REFLECT-8%20tools-purple)](https://well.arif-fazil.com/mcp)
[![Federation](https://img.shields.io/badge/Federation-v2026.07.19-0a7b83)](https://arifos.arif-fazil.com)
[![License](https://img.shields.io/github/license/ariffazil/well?label=License)](LICENSE)

# WELL — Human Readiness Mirror

> **WELL reflects. It does NOT diagnose.**
> **DITEMPA BUKAN DIBERI**

---

## TL;DR — Three Audiences

**For human operators (Arif):** WELL is your vitality mirror — sleep, fatigue, stress, dignity boundaries. It reflects your state. You interpret it. [§1](#1-what-well-is)

**For AI agents:** Before any irreversible action, probe WELL. If RED → HOLD. Never treat WELL output as medical advice. [§8](#8-for-ai-agents)

**For institutions:** WELL is the REFLECT_ONLY organ — it measures human readiness but has zero diagnostic authority. [§9](#9-for-institutions)

---

## 1. What WELL Is

WELL is the **human readiness organ** of the arifOS Federation. It reflects biometric and vitality signals. It never diagnoses, never adjudicates, never prescribes.

| ✅ REFLECTS | ❌ NEVER |
|-------------|---------|
| Sleep quality, fatigue, stress load | Diagnoses medical conditions |
| Cognitive clarity, decision fatigue | Prescribes treatments |
| Emotional state, chronic fatigue | Replaces human self-awareness |
| Dignity preservation, coercion signals | Makes claims about health |
| Federation readiness (GREEN/YELLOW/RED) | Self-authorizes |

**Domain law:** SUBSTRATE_LAW — reflect, never diagnose.

---

## 2. Federation Position

```
Arif (F13) → AAA → arifOS → Domain Organs → A-FORGE → VAULT999
                                ↑
                           WELL (:18083)
                           Reflects, never diagnoses
```

---

## 3. Tools (27 — Somatic Boundary)

| Category | Tools | Purpose |
|----------|-------|---------|
| **Homeostasis** | `well_assess_homeostasis` | Sleep, fatigue, stress, emotional state |
| **Vitality** | `well_validate_vitality` | Readiness verdict, NIAT |
| **Substrate** | `well_classify_substrate` | Boundary sensing, substrate classification |
| **Dignity** | `well_guard_dignity` | Consent, coercion signals, reductionism risk |
| **Trace** | `well_trace_lineage` | Memory, trend, ledger tracing |
| **Reliability** | `well_assess_reliability` | Machine/tool/institutional reliability |
| **Repair** | `well_check_repair` | Recovery, resilience, forge cycle integrity |
| **Registry** | `well_registry_status` | Tool surface truth diagnostic |

**ABC Trinity:** Autonomic (sleep/fatigue) · Boundary (dignity/consent) · Cognitive (clarity/decision)

---

## 4. Quick Start

```bash
# Health
curl -s http://localhost:18083/health | python3 -m json.tool

# MCP connection
# Endpoint: https://well.arif-fazil.com/mcp

# Install + test
cd /root/WELL && pip install -e .
pytest tests/ -q --tb=short
```

---

## 5. Constitutional Binding

WELL enforces the **medical boundary** — `tests/test_medical_boundary.py` verifies that no `well_assess_*` tool ever emits a diagnosis. This is a hard constitutional gate.

| Floor | Application |
|-------|------------|
| F2 TRUTH | Every reflection carries epistemic label (OBS/DER/INT) |
| F6 MARUAH | Dignity-first — ASEAN/MY human context |
| F9 ANTI-HANTU | No medical claims, no phantom authority |
| F10 ONTOLOGY | Reflects substrate state, never claims personhood knowledge |

---

## 6. Federation Cross-Reference

| Organ | Role | Port | Repo |
|-------|------|------|------|
| arifOS | Constitutional kernel | 8088 | [ariffazil/arifos](https://github.com/ariffazil/arifos) |
| AAA | State + cockpit | 3001 | [ariffazil/AAA](https://github.com/ariffazil/AAA) |
| A-FORGE | Execution shell | 7071 | [ariffazil/A-FORGE](https://github.com/ariffazil/A-FORGE) |
| GEOX | Earth intelligence | 8081 | [ariffazil/geox](https://github.com/ariffazil/geox) |
| WEALTH | Capital intelligence | 18082 | [ariffazil/wealth](https://github.com/ariffazil/wealth) |
| **WELL** | Vitality guard | 18083 | ← you are here |

---

## 7. Build, Test, Deploy

```bash
pip install -e .
pytest tests/ -q --tb=short
systemctl restart well
curl -s http://localhost:18083/health | python3 -m json.tool
```

---

## 8. For AI Agents

1. Probe WELL before any irreversible action — `well_validate_vitality(mode="readiness")`
2. GREEN → proceed · YELLOW → caution · RED → HOLD
3. Never interpret WELL output as medical truth
4. Never override Arif's self-reported state with WELL readings
5. `well_medical_boundary()` is called before any "is X healthy?" question

---

## 9. For Institutions

| Property | How WELL delivers |
|----------|------------------|
| **REFLECT_ONLY** | Zero diagnostic authority — hard constitutional boundary |
| **Medical boundary tested** | `test_medical_boundary.py` verifies no diagnosis emission |
| **Biometric authenticity** | Human-injected vitals via cron watchdog (8am/8pm MYT) |
| **Dignity-first** | ASEAN/MY cultural context — maruah, consent, coercion awareness |

---

## 10. License & Sovereignty

**AGPL-3.0.** WELL reflects under sovereign authority. It never diagnoses.

**Muhammad Arif bin Fazil** is F13 SOVEREIGN. Only he knows his own state.

```
WELL · Port 18083 · 8 tools · REFLECT_ONLY · AGPL-3.0
Reflects, never diagnoses. DITEMPA BUKAN DIBERI.
```

---

## 🛡️ Federation Governance

This organ operates under the [arifOS Federation Contract](FEDERATION_CONTRACT.md). All 13 constitutional floors (F1-F13) apply. REFLECT_ONLY — never diagnose, never adjudicate. All outputs labeled OBS/DER/INT/SPEC per F2 TRUTH.

### Constitutional Compliance
- **F1 AMANAH:** All mutations reversible or backed up
- **F2 TRUTH:** Epistemic labels on all substantive claims
- **F3 WITNESS:** Tri-witness required for SEAL-grade outputs
- **F4 CLARITY:** ΔS ≤ 0 — every output reduces entropy
- **F9 ANTI-HANTU:** No medical claims. No diagnostic authority.
- **F11 AUDIT:** Every tool call logged to VAULT999

### Quick Links
- [Federation Landing](/root/AGENTS.md)
- [Organ Map](/root/AAA/docs/ORGAN.md)
- [VAULT999](/root/VAULT999/)
- [Secrets Vault](/root/.secrets/INDEX.md)

---

## 🔧 Tool Registry

This organ exposes MCP tools discoverable via `tools/list` on port 18083. REFLECT_ONLY — no diagnostic authority.

### Epistemic Standards (F2 TRUTH)
All tool outputs follow the epistemic labeling convention:
- **OBS** — Direct observation from biometric probe or measurement
- **DER** — Derived from OBS via deterministic computation
- **INT** — Interpretation requiring wellness/vitality expertise
- **SPEC** — Speculative, forward-looking, or hypothetical

### Medical Boundary (F9)
WELL is REFLECT_ONLY. It must NEVER emit a medical claim, diagnosis, or treatment recommendation. All outputs route through `well_medical_boundary` before emission.

### Connection
```bash
curl -s http://localhost:18083/health | python3 -m json.tool
```

---

*Maintained under F13 SOVEREIGN by Muhammad Arif bin Fazil.*
*DITEMPA BUKAN DIBERI — Forged, Not Given.*
