# WELL Evidence Sources Pack
**manifest_id:** WELL-EVIDENCE-SOURCES-v1.0
**epoch:** 2026-05-03
**status:** SEALED
**classification:** reference_witness_pack
**seal_statement:** "WELL uses these sources as scientific witnesses for readiness, cognitive load, adaptive automation, and trigger design. They inform audits; they do not command action. Human remains sovereign."

---

## Seal statement

> These sources are **reference witnesses**, not sovereign authorities.
> Computer may retrieve, compare, and cite them during WELL audits, but must not treat them as automatic truth or final judgment.
> Human sovereignty (F13) and arifOS JUDGE final authority are never overridden by external references.

---

## WELL Evidence Sources

### 1. NRC RIL 2020-05 — Adaptive Automation

| Field | Value |
|---|---|
| **ID** | `NRC-RIL-2020-05` |
| **Name** | NRC RIL 2020-05 — Adaptive Automation |
| **URL** | https://www.nrc.gov/docs/ML2017/ML20176A199.pdf |
| **Publisher** | U.S. Nuclear Regulatory Commission |
| **Year** | 2020 |
| **Role** | Primary adaptive automation authority |
| **Floor mapping** | W-Floor trigger logic, throttle etiquette (gradual, rationale-first), 6-category sensor taxonomy, hybrid multimodal trigger rationale, human-factors safety boundaries |
| **Authority level** | `external_reference_witness` |
| **Not authority over** | Human sovereign (F13), arifOS JUDGE final judgment, W0 Sovereignty Invariant |
| **How to use** | Cite when auditing W-Floor trigger thresholds, throttle etiquette rules, or sensor taxonomy decisions. Compare proposed changes against NRC guidance. Do not treat as final override. |

### 2. Grzeszczuk et al. 2025 — Trustworthy Cognitive Monitoring

| Field | Value |
|---|---|
| **ID** | `ARXIV-2506.22066` |
| **Name** | Grzeszczuk 2025 — Trustworthy Cognitive Monitoring for Safety-Critical Human Tasks |
| **URL** | https://arxiv.org/abs/2506.22066 |
| **Publisher** | arXiv |
| **Year** | 2025 |
| **Role** | Cognitive state classifier witness |
| **Floor mapping** | W5 Cognitive Entropy (OFS classifier design), Phase 2-3 unsupervised OFS classification, fatigue/stress/workload monitoring methodology, phased cognitive monitoring approach |
| **Authority level** | `external_reference_witness` |
| **Not authority over** | Human sovereign (F13), arifOS JUDGE final judgment, W0 Sovereignty Invariant |
| **How to use** | Cite when designing or auditing W5 Cognitive Entropy floor, OFS classifier phases, or cognitive load thresholds. Compare against Grzeszczuk methodology. Do not treat as final override. |

### 3. Idaho National Lab — Initiators and Triggering Conditions

| Field | Value |
|---|---|
| **ID** | `INL-STI-STI-6250170` |
| **Name** | Idaho National Lab — Initiators and Triggering Conditions for Adaptive Automation |
| **URL** | https://inldigitallibrary.inl.gov/sites/sti/sti/6250170.pdf |
| **Publisher** | Idaho National Laboratory |
| **Year** | 2014 |
| **Authors** | Katya Le Blanc, Johanna Oxstrand |
| **Role** | Multi-domain trigger taxonomy witness |
| **Floor mapping** | W6 Incentive Decoupling (trigger taxonomy), loop detection logic, Metabolic Pause enforcement pattern, cross-domain adaptive automation trigger design (aviation, nuclear, military) |
| **Authority level** | `external_reference_witness` |
| **Not authority over** | Human sovereign (F13), arifOS JUDGE final judgment, W0 Sovereignty Invariant |
| **How to use** | Cite when designing or auditing W6 trigger conditions, loop detection thresholds, or pause/escalation rules. Use INL cross-domain taxonomy as broad validation. Do not treat as final override. |

---

## Complete 7-source evidence stack for WELL

### 4 Identity / constitutional sources

| ID | Name | Role |
|---|---|---|
| `GIST-CONSTITUTION` | APEX Constitution gist | Federation blueprint, F1-F13 authority |
| `GITHUB-WELL` | github.com/ariffazil/well | WELL canonical repo |
| `ARIF-FAZIL-COM` | arif-fazil.com | Public identity surface |
| `WIKI-ARIF-FAZIL-COM` | wiki.arif-fazil.com | Knowledge mesh, institutional memory |

### 3 Scientific / operational sources

| ID | Name | Role |
|---|---|---|
| `NRC-RIL-2020-05` | NRC Adaptive Automation | Trigger logic, throttle etiquette, sensor taxonomy |
| `ARXIV-2506.22066` | Grzeszczuk 2025 | W5 Cognitive Entropy, OFS classifier |
| `INL-STI-STI-6250170` | INL Initiators/Triggers | W6 trigger taxonomy, loop detection |

---

## Version history

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-05-03 | Initial seal — 3 scientific sources + 4 identity sources |

---

*DITEMPA BUKAN DIBERI — Evidence is gathered, not commanded.*
