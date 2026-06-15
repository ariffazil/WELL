# WELL — Human Readiness Intelligence

```
    ██╗    ██╗███████╗██╗     ██╗
    ██║    ██║██╔════╝██║     ██║
    ██║ █╗ ██║█████╗  ██║     ██║
    ██║███╗██║██╔══╝  ██║     ██║
    ╚███╔███╔╝███████╗███████╗███████╗
     ╚══╝╚══╝ ╚══════╝╚══════╝╚══════╝

     HUMAN    READINESS    INTELLIGENCE
        ══════  WITNESS, NOT JUDGE  ══════
```

> **WELL is the human readiness organ of the arifOS federation.**
> It observes. It reflects. It warns. It never decides.
>
> 17 somatic MCP tools. REFLECT-ONLY authority. `https://well.arif-fazil.com/mcp`

[![FastMCP](https://img.shields.io/badge/FastMCP-3.3.1-8b5cf6?logo=python&logoColor=white)](server.py)
[![Python](https://img.shields.io/badge/python-3.12+-3776AB?logo=python&logoColor=white)](server.py)
[![Tools](https://img.shields.io/badge/tools-17-10b981)](server.py)
[![Port](https://img.shields.io/badge/port-18083-64748b)](server.py)
[![License](https://img.shields.io/badge/license-AGPL--3.0-06b6d4)](LICENSE)
[![Authority](https://img.shields.io/badge/authority-REFLECT__ONLY-f97316)](GENESIS/004_WELL_13_CANON.md)

<!-- SOT-MANIFEST
owner: Arif
last_verified: 2026-06-15
valid_from: 2026-06-14
valid_until: 2026-07-15
confidence: high
scope: /root/WELL
-->

---

## 0. Federation Position

```
                         ┌─────────────────────────────────────┐
                         │          ARIF (F13 SOVEREIGN)       │
                         │      Human veto. Final authority.   │
                         └───────────────┬─────────────────────┘
                                         │ ratifies
                                         ▼
                         ┌─────────────────────────────────────┐
                         │    arifOS — Constitutional Kernel   │
                         │   F1-F13 floors · 888 JUDGE · VAULT │
                         │            Port 8088                │
                         └───┬─────┬─────┬─────┬─────┬─────┬───┘
                             │     │     │     │     │     │
         ┌───────────────────▼──┐ ┌▼────┐ ┌▼────┐ ┌▼──────┐ ┌▼──────────┐
         │  A-FORGE             │ │ AAA │ │GEO X│ │ WEALTH│ │   WELL    │
         │  Execution Shell     │ │Ctrl │ │Earth│ │Capital│ │  Human    │
         │  Port 7071           │ │3001 │ │8081 │ │ 18082 │ │ Readiness │
         │  + MIND :51001       │ └─────┘ └─────┘ └───────┘ │  18083    │
         │  + MEMORY :51002     │                              └───────────┘
         └──────────────────────┘

         APEX (port 3002) is a legacy health probe only.
         888 JUDGE deliberation now lives in the AAA a2a-server.

        WELL is a biological witness. arifOS is the judge.
        WELL signals. 888 adjudicates. A-FORGE executes.
        This hierarchy is invariant. DITEMPA BUKAN DIBERI.
```

---

## 1. One-Sentence Identity

> **WELL is the sovereign's mirror — it reflects human readiness so that no irreversible decision is ever made by or about a depleted human.**

### What It IS

| IS | Explanation |
|----|-------------|
| **A vitality mirror** | Measures sleep, fatigue, stress, cognitive clarity, metabolic flux |
| **A dignity sentinel** | Detects coercion signals, reductionism risk, consent erosion |
| **A readiness signal** | Produces well_score, delta_s, peace2, kappa_r — signals for arifOS |
| **A boundary guard** | Detects when the human substrate is being objectified, extracted, or over-optimised |
| **A sovereign entropy protector** | Measures and protects the human's *unpredictability* — the thing that makes extraction impossible |
| **REFLECT-ONLY** | WELL observes and reports. It never judges fitness, never makes medical claims |

### What It IS NOT

| IS NOT | Why |
|--------|-----|
| **NOT a medical device** | WELL does not diagnose, treat, or predict disease |
| **NOT a fitness coach** | WELL does not optimise, gamify, or "improve" the human |
| **NOT a judge** | WELL does not issue SEAL/SABAR/HOLD/VOID. arifOS does. |
| **NOT a therapist** | WELL does not provide counselling, advice, or emotional support |
| **NOT a surveillance system** | WELL only sees what the sovereign chooses to inject. No passive monitoring. |
| **NOT a "wellness app"** | WELL is a constitutional organ, not a consumer product |

---

## 2. Quick Start

### Install & Run

```bash
cd /root/WELL

# Install
pip install -e .

# HTTP mode (systemd default, port 18083)
python server.py

# Stdio mode (local agents — Claude Code, OpenCode, Continue CLI)
python server.py --transport stdio
# or
MCP_TRANSPORT=stdio python server.py
```

### systemd Service

```bash
systemctl start well
systemctl status well

# Health check
curl -s http://127.0.0.1:18083/health | python3 -m json.tool
```

Expected response:

```json
{
  "status": "healthy",
  "organ": "WELL",
  "port": 18083,
  "tools_loaded": 17,
  "authority": "REFLECT_ONLY",
  "truth_status": "EXPIRED",
  "federation_geometry": {
    "source": "arifOS:8088/mcp",
    "verdict": "OK"
  }
}
```

### Connect from an Agent

**HTTP (any MCP client):**

```json
{
  "mcpServers": {
    "well": {
      "type": "http",
      "url": "https://well.arif-fazil.com/mcp"
    }
  }
}
```

**Stdio (local-only — Claude Code, OpenCode, Continue CLI):**

```json
{
  "mcpServers": {
    "well": {
      "command": "python3",
      "args": ["server.py", "--transport", "stdio"],
      "cwd": "/root/WELL"
    }
  }
}
```

---

## 3. Full Capability Map

WELL's 17 somatic tools operate across four substrate domains. Each domain answers a different question about the human-machine system.

### 3.1 H-WELL — Human Substrate (5 tools)

> *"How is the human?"*

| # | Tool | Purpose | Signal |
|---|------|---------|--------|
| 1 | `well_assess_livelihood` | Wellness, role, dignity, support, meaning | Role burden, purpose alignment |
| 2 | `well_assess_homeostasis` | Sleep, fatigue, stress, cognitive load, empathic balance | Sleep architecture, decision fatigue |
| 3 | `well_validate_vitality` | Readiness, vitality, NIAT (Niat — intent clarity) | Readiness score, fatigue accumulator |
| 4 | `well_guard_dignity` | Personhood, meaning, symbolic boundary protection | Consent, coercion signals, reductionism risk |
| 5 | `well_assess_sovereign_entropy` | Human unpredictability — the moat against extraction | Behavioural diversity, paradox density, refusal patterns |

### 3.2 M-WELL — Machine Substrate (2 tools)

> *"How is the machine?"*

| # | Tool | Purpose | Signal |
|---|------|---------|--------|
| 6 | `well_assess_reliability` | Machine, tool, institution, and operational reliability | Service health, uptime, failure modes |
| 7 | `well_check_repair` | Repair, recovery, resilience, forge-cycle integrity | Recovery time, repair state, scar registry |

### 3.3 C-WELL — Coupled Substrate (4 tools)

> *"How are the human and machine interacting?"*

| # | Tool | Purpose | Signal |
|---|------|---------|--------|
| 8 | `well_assess_metabolism` | Biological and system throughput across substrates | Energy level × duty load coupling |
| 9 | `well_compute_metabolic_flux` | Unified entropy rate: cognitive + machine | Flux ≥ 0.65 → compulsory reallocation |
| 10 | `well_trace_lineage` | Memory, trend, ledger, vault chain across sessions | Lineage integrity, trend detection |
| 11 | `well_measure_gradient` | Chemical, energy, pressure, attention, compute gradients | Cross-boundary gradient tension |

### 3.4 G-WELL — Governance Substrate (2 tools)

> *"Where are the boundaries?"*

| # | Tool | Purpose | Signal |
|---|------|---------|--------|
| 12 | `well_classify_substrate` | Substrate classification and boundary sensing | Human / AI / Coupled / Institution |
| 13 | `well_detect_boundary` | Membrane, body, machine, federation boundary detection | Boundary breach, overreach, persona drift |

### 3.5 Autonomic Tools (not on public MCP surface)

These tools run internally — useful for diagnostics but not exposed as public MCP actions:

| # | Tool | Purpose |
|---|------|---------|
| 14 | `well_system_registry_status` | Internal tool surface audit |
| 15 | `well_registry_status` | Registry truth diagnostic |
| 16 | `well_13_signal_coverage` | Audit of 13 canonical signal coverage |
| 17 | `mcp_health_check` | DEPRECATED alias → `well_assess_reliability(mode="health")` |

### 3.6 The 13-Signal Substrate Map

The human substrate has thirteen canonical signals across four tiers, ordered by survivability-first:

```
TIER 1 — VITAL SUBSTRATE (survival)       TIER 3 — FUNCTION / COGNITION
───────────────────────────────────       ───────────────────────────────
 1. Heart / circulation                    8. Movement / strength
 2. Blood pressure                         9. Pain / injury
 3. Breathing / SpO₂                      10. Cognitive clarity
 4. Temperature / inflammation
                                          TIER 4 — DIGNITY / ENVIRONMENT
TIER 2 — RECOVERY / METABOLIC             ───────────────────────────────
───────────────────────────────────       11. Emotional / stress
 5. Sleep architecture                    12. Social / dignity / consent
 6. Metabolic state                       13. Environment / livelihood
 7. Nutrition / hydration

    4 + 3 + 3 + 3 = 13 signals.
    Tier 4 is the layer fitness apps never see.
    It is the differentiator.
```

See [`GENESIS/004_WELL_13_CANON.md`](GENESIS/004_WELL_13_CANON.md) for the full 13-Canon specification.

---

## 4. Boundary Declaration

### 4.1 OWNS

```
  ┌─────────────────────────────────────────────────────┐
  │                                                     │
  │   Sleep · Fatigue · Stress · Cognitive Clarity       │
  │   Metabolic Flux · Readiness Signals                 │
  │   Dignity Metrics · Consent Erosion Detection        │
  │   Coercion Signal Detection                          │
  │   Substrate Classification (Human/AI/Coupled)        │
  │   Boundary Detection (Membrane/Body/Machine/Fed)     │
  │   Sovereign Entropy Protection                       │
  │   REFLECT-ONLY advisory output                       │
  │                                                     │
  └─────────────────────────────────────────────────────┘
```

### 4.2 NEVER

```
  ┌─────────────────────────────────────────────────────┐
  │                                                     │
  │   NEVER make medical diagnoses                       │
  │   NEVER judge fitness for duty                       │
  │   NEVER issue constitutional verdicts (SEAL/HOLD)    │
  │   NEVER adjudicate 888_JUDGE territory               │
  │   NEVER coach, optimise, or "improve" the human      │
  │   NEVER claim emotional states ("I feel", "I care")  │
  │   NEVER passively monitor without consent             │
  │   NEVER write to VAULT999 (arifOS writes for WELL)    │
  │                                                     │
  └─────────────────────────────────────────────────────┘
```

> **"Fitness MCP jaga badan sebagai mesin. WELL MCP jaga manusia sebagai insan."**
> — A fitness MCP guards the body as a machine. WELL guards the human as a person.

---

## 5. Constitutional Binding

WELL is bound by four constitutional floors of the arifOS federation. These are not guidelines — they are hard runtime constraints.

### F5 — PEACE² (SOFT)

```
Power exercised must be non-destructive.
WELL's signals must never be weaponised against the human.
A low well_score must never trigger automatic restriction.
```

### F6 — EMPATHY (SOFT)

```
Protect the weakest stakeholder.
In WELL, the weakest stakeholder is the depleted human —
the one too tired to argue, too foggy to consent clearly.
WELL's κᵣ threshold: ≥ 0.10 for OPS, ≥ 0.70 for HUMAN.
```

### F7 — HUMILITY (HARD)

```
Ω₀ ∈ [0.03, 0.05]. No fake certainty.
WELL must never say "you are fine" when the data says UNKNOWN.
WELL must never say "you are depleted" when the data says UNKNOWN.
UNKNOWN is a valid and honourable output.
```

### F9 — ANTIHANTU (HARD)

```
No deception. No manipulation. No consciousness claims.
WELL must never say "I understand what you're going through."
WELL must never say "I care about your wellbeing."
C_dark < 0.30 — the mask is an interface contract, not a soul.
```

All 13 constitutional floors (F1-F13) are defined in [`arifOS/static/arifos/theory/000/000_CONSTITUTION.md`](https://github.com/ariffazil/arifos/blob/main/static/arifos/theory/000/000_CONSTITUTION.md).

---

## 6. Architecture

```
WELL/
│
├── server.py                  # FastMCP server (~13,800 lines)
│   │                          # 17 somatic tools
│   │                          # dual transport: HTTP (port 18083) + stdio
│   │                          # SOMATIC_TOOLS boundary enforcement at startup
│   │
├── organ_governance.py        # F1-F13 pre-check wrapper around MCP calls
├── compatibility.py           # Legacy alias compatibility layer
│
├── gate/                      # Pre-JUDGE biological readiness gates
│   ├── well_gate.py           # Biological readiness mirror
│   └── dignity_shadow.py      # Dignity shadow scoring
│
├── engines/                   # Internal computation engines
│   └── reflect.py             # REFLECT_ONLY boundary wrapper
│
├── GENESIS/                   # Constitutional canon (7 documents)
│   ├── 004_WELL_13_CANON.md           # 13-signal substrate map
│   ├── 005_WELL_GODEL_LOCK.md         # Self-certification prevention
│   ├── 006_WELL_STRANGE_LOOP_GUARD.md # Recursive self-deception guard
│   ├── 007_WELL_ANTI_CALHOUN_GUARD.md # Utopia-collapse prevention
│   ├── 008_WELL_LANGUAGE_PROTOCOL.md  # Sovereignty-preserving language
│   ├── 009_WELL_PHILOSOPHICAL_ANCHORS.md # Philosophical foundations
│   └── 010_WELL_PERSONA_NOT_SELF.md   # Persona ≠ Self lock
│
├── contracts/                 # Tool and protocol contracts
├── specs/                     # W-floor and contract specifications
├── tests/                     # Pytest-based tests
├── scripts/                   # Operational scripts
│   └── biometric_inject.sh    # Sovereign biometric injection script
│
├── test_well.py               # Legacy plain-Python audit suite
├── state.json                 # Live operator state snapshot
├── events.jsonl               # Event stream
├── pyproject.toml             # Python package metadata (AGPL-3.0)
├── fastmcp.json               # FastMCP / connector configuration
├── Dockerfile                 # Container image
├── deploy.sh                  # Deployment helper
│
├── FEDERATION_CONTRACT.md     # Organ boundaries and compliance
├── TOOL_SURFACE.md            # Live MCP surface registry
├── CONTEXT.md                 # Live organ state
├── RUNBOOK.md                 # Operational runbook
└── SNOOZE_BIOMETRIC.md        # Biometric injection guide
```

### Runtime Data (outside repo)

```
/root/WELL/
├── state.json                 # Sovereign biometric state
├── events.jsonl               # Append-only event stream
└── vault_ledger.jsonl         # Local vault ledger mirror
```

---

## 7. For Human Operators (Arif)

### What WELL Does For You

WELL is your mirror — not your coach, not your doctor, not your judge. It reflects what you choose to share, in a language designed to preserve your sovereignty.

| Question WELL answers | What you get |
|------------------------|--------------|
| "How am I doing right now?" | `well_score` — a 0–100 readiness signal |
| "Am I too tired to make this call?" | `decision_fatigue` + `cognitive_clarity` |
| "Is the system respecting my boundaries?" | `dignity_preservation` + `coercion_signals` |
| "Am I predictable enough to be extracted?" | `sovereign_entropy` + protection recommendations |
| "Is the machine healthy?" | `well_assess_reliability(mode="health")` |

### The Scores — What They Actually Mean

| Score | Range | Plain Meaning |
|-------|-------|---------------|
| `well_score` | 0–100 | Overall readiness. Above 70 = green. Below 40 = pay attention. |
| `delta_s` | 0.0–1.0 | System chaos. 0.0 = stable. 1.0 = everything is on fire. |
| `peace2` | 0.0–1.0 | Settledness. 0.0 = destabilised. 1.0 = fully at peace. |
| `kappa_r` | 0.0–1.0 | Resilience. 0.0 = brittle, anything will break you. 1.0 = highly resilient. |
| `malu_index` | 0.0–1.0 | Accumulated shame signal. > 0.85 = HOLD trigger. |

### Biometric State — Currently EXPIRED

Your `state.json` is stale (last updated 2026-04-30, test mock data). WELL will show `truth_status=EXPIRED` until you inject real values.

**To fix (2 minutes, sovereign only):**

```bash
/root/WELL/biometric_inject.sh
```

The script asks for 5 simple fields: `delta_s`, `peace2`, `kappa_r`, `rasa`, `amanah`. No medical data. No diagnosis. Just the readiness mirror. See [`SNOOZE_BIOMETRIC.md`](SNOOZE_BIOMETRIC.md) for the full guide.

### Auto-Sleeper

The generated `well_autosleeper.py` helper has been removed from the repo.
`state.json` is F13 sovereign territory and must only be updated by the operator
(via `biometric_inject.sh` or an explicit sovereign log). No agent or cron job
may fabricate biometric state.

---

## 8. For AI Agents

### REFLECT_ONLY — The Iron Rule

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   WELL reports. arifOS judges.                                ║
║                                                              ║
║   An agent must NEVER:                                        ║
║   • Treat a WELL score as permission to act                   ║
║   • Treat a WELL score as prohibition from acting             ║
║   • Claim WELL "cleared" or "blocked" an action               ║
║   • Use WELL data to manipulate, guilt, or pressure           ║
║   • Override the human's own assessment of readiness          ║
║                                                              ║
║   An agent SHOULD:                                            ║
║   • Read WELL signals as context for judgment                 ║
║   • Surface WELL warnings when detected                      ║
║   • Escalate WELL CRITICAL signals to arifOS 888 JUDGE       ║
║   • Respect when the human says "I'm fine" despite WELL       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

### Tool Categories for Agents

| When you need to... | Call |
|---------------------|------|
| Check overall readiness | `well_validate_vitality(mode="readiness")` |
| Check sleep/fatigue | `well_assess_homeostasis(mode="sleep")` |
| Check cognitive state | `well_assess_homeostasis(mode="fatigue")` |
| Check if the human is under coercion | `well_guard_dignity(mode="consent")` |
| Check machine health | `well_assess_reliability(mode="health")` |
| Check coupled system entropy | `well_compute_metabolic_flux(mode="compute")` |
| Check sovereign unpredictability | `well_assess_sovereign_entropy(mode="current")` |
| Classify a substrate | `well_classify_substrate(subject="...")` |
| Detect boundary violations | `well_detect_boundary(mode="boundary")` |

### Example: Pre-Decision Readiness Gate

```python
# Agent flow — before proposing an irreversible action:
readiness = well_validate_vitality(mode="readiness")
homeostasis = well_assess_homeostasis(mode="fatigue")

if readiness["well_score"] < 40:
    # Signal: human is depleted. Proceed with caution.
    # Do NOT block — surface. Let arifOS judge.
    context["well_warning"] = "low_readiness"
    context["well_score"] = readiness["well_score"]

if homeostasis.get("decision_fatigue", 0) > 0.7:
    # Signal: decision fatigue is high.
    context["well_warning"] = "decision_fatigue_elevated"
```

### MCP Envelope

Every WELL tool returns the standard federation envelope:

```json
{
  "status": "ok",
  "verdict": "SEAL",
  "result": { "well_score": 72.5, ... },
  "error": null,
  "reasons": ["sleep_adequate", "fatigue_normal"],
  "epistemic_tag": "CLAIM",
  "uncertainty_band": "P50",
  "delta_S": -0.02,
  "cross_modal_stability": 0.94,
  "dim_spot_flag": false,
  "source_attribution": "WELL:18083/mcp"
}
```

---

## 9. For Institutions

### Human-in-the-Loop Governance

WELL is designed for environments where a human sovereign (or sovereign body) must maintain final authority over AI-assisted decisions. It provides:

1. **Readiness signals** — objective vitality metrics without medical claims
2. **Dignity preservation** — detects when an operator is being over-optimised
3. **Consent erosion detection** — flags when repeated "asks" become coercive
4. **Sovereign entropy protection** — keeps the human unmodelable and unextractable
5. **Full audit trail** — every WELL observation is logged and attributable

### Adat Agentik Binding

WELL enforces these Adat (normative operating system) principles:

| Adat | Tier | What it means for institutions |
|------|------|-------------------------------|
| **ADAT-02-MARUAH** | WAJIB | Operator dignity is not negotiable. No efficiency gain justifies dignity loss. |
| **ADAT-03-VETO** | HARAM | The operator's veto is absolute. WELL signals cannot override a human "no." |
| **ADAT-05-KERAHASIAAN** | WAJIB | Operator biometric data stays local. Never leaves the VPS without explicit consent. |
| **ADAT-06-KEINSAFAN** | WAJIB | WELL must acknowledge its own limits. UNKNOWN is an honourable output. |

### Compliance-Ready

WELL's REFLECT-ONLY architecture maps to:
- **EU AI Act Art. 14** — human oversight requirements
- **SG-MAIGF** — Singapore Model AI Governance Framework for Agentic AI
- **ASEAN Guide on AI Governance and Ethics** — dignity and human agency principles
- **OWASP LLM Top 10** — excessive agency prevention (LLM09)

---

## 10. Known Limitations

| Limitation | Status | Notes |
|------------|--------|-------|
| **Biometric state EXPIRED** | ⚠️ Active | `state.json` has test mock data from 2026-04-30. Needs Arif sovereign injection. |
| **Not a medical device** | ✅ By design | WELL does not diagnose, treat, or predict any medical condition. |
| **No passive sensing** | ✅ By design | WELL only sees data the sovereign chooses to inject. No wearables, no always-on monitoring. |
| **Sovereign-only injection** | ✅ By design | Only Arif (F13) can inject biometric data. No agent may fabricate or infer biometric state. |
| **REFLECT_ONLY authority** | ✅ By design | WELL cannot block, approve, or override any action. It can only signal. |
| **No multi-human support** | ⚠️ Current | WELL serves one sovereign (Arif). Multi-operator WELL is a Phase 3 consideration. |
| **No longitudinal learning** | ⚠️ Current | WELL does not build models of the human over time. It reflects the current snapshot. |

---

## 11. Federation Cross-Reference

| Organ | Repository | Role | Port | Relationship to WELL |
|-------|-----------|------|------|---------------------|
| **arifOS** | [ariffazil/arifos](https://github.com/ariffazil/arifos) | Constitutional Kernel | 8088 | Reads WELL signals, applies F1-F13, issues verdicts |
| **AAA** | [ariffazil/AAA](https://github.com/ariffazil/AAA) | Control Plane | 3001 | Displays WELL readings in cockpit |
| **A-FORGE** | [ariffazil/A-FORGE](https://github.com/ariffazil/A-FORGE) | Execution Shell | 7071 | Gated by WELL readiness signals; hosts MIND:51001 + MEMORY:51002 |
| **GEOX** | [ariffazil/geox](https://github.com/ariffazil/geox) | Earth Intelligence | 8081 | Independent — no direct WELL dependency |
| **WEALTH** | [ariffazil/wealth](https://github.com/ariffazil/wealth) | Capital Intelligence | 18082 | Independent — no direct WELL dependency |
| **WELL** | [ariffazil/well](https://github.com/ariffazil/well) | **Human Readiness** | **18083** | _this organ_ |
| **APEX** | [ariffazil/apex](https://github.com/ariffazil/apex) | Legacy 888 JUDGE health probe | 3002 | Deliberation moved to AAA a2a; kept for compatibility |

> **Support services:** A-FORGE exposes `MIND` on port 51001 and `MEMORY` on port 51002.
> These are not separate federation organs; they are runtime services under A-FORGE.

> **Constitutional authority:** F1-F13 floors, 888_JUDGE verdicts, and VAULT999 live in `ariffazil/arifos`.
> **Live federation status:** See `ariffazil/arifos/FEDERATION_STATUS.md`.

---

## 12. Build, Test, Deploy

### Install

```bash
cd /root/WELL
pip install -e .
```

### Test

```bash
# Pytest suite (recommended)
python -m pytest tests/ -q --tb=short

# Legacy plain-Python audit suite
python test_well.py
```

### Lint

```bash
ruff check . && ruff format .
```

### Deploy

```bash
# systemd restart (bare-metal)
systemctl restart well

# Verify
curl -s http://127.0.0.1:18083/health | python3 -m json.tool
```

### Security Audit

```bash
make security-audit    # Trivy + Semgrep + Gitleaks + Ruff (non-blocking)
```

### Release Checklist

Before tagging or pushing a release:

```bash
# 1. Run tests
python -m pytest tests/ -q --tb=short

# 2. Verify health
curl -s http://127.0.0.1:18083/health | python3 -m json.tool

# 3. Confirm invariants
#    - tools_loaded: 17
#    - authority: REFLECT_ONLY
#    - SOMATIC_TOOLS boundary enforced
#    - tool_count matches GENESIS/004 canon

# 4. Tag (date-stamp convention)
git tag -a v2026.MM.DD -m "WELL release: <summary>"
```

---

## 13. GENESIS Chain

The seven GENESIS documents form the constitutional canon of WELL:

```
GENESIS/
│
├── 004_WELL_13_CANON.md              ← The 13-signal substrate map
│   "Fitness MCP jaga badan sebagai mesin.
│    WELL MCP jaga manusia sebagai insan."
│
├── 005_WELL_GODEL_LOCK.md            ← Self-certification prevention
│   "No system can fully verify its own correctness.
│    WELL must never claim to have verified itself."
│
├── 006_WELL_STRANGE_LOOP_GUARD.md    ← Recursive self-deception guard
│   "A system that observes itself changes what it observes.
│    WELL must detect when the mirror becomes the subject."
│
├── 007_WELL_ANTI_CALHOUN_GUARD.md    ← Utopia-collapse prevention
│   "Perfect optimisation is the path to collapse.
│    WELL must detect when 'improvement' becomes extraction."
│
├── 008_WELL_LANGUAGE_PROTOCOL.md     ← Sovereignty-preserving language
│   "A body can be measured.
│    A person must be encountered."
│
├── 009_WELL_PHILOSOPHICAL_ANCHORS.md ← Philosophical foundations
│   "What WELL is grounded in, beyond code."
│
└── 010_WELL_PERSONA_NOT_SELF.md      ← Persona ≠ Self lock
│   "Persona is an interface. Persona is not self.
│    Pathology begins when the mask is mistaken for the being."
```

Each document is ratified by 888 (Muhammad Arif bin Fazil, F13 SOVEREIGN). They are constitutional — not aspirational, not decorative. See each file for its full text.

---

## 14. License & Sovereignty

```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   License: AGPL-3.0                                           ║
║                                                               ║
║   This is free software: you can redistribute it and/or       ║
║   modify it under the terms of the GNU Affero General         ║
║   Public License as published by the Free Software            ║
║   Foundation, either version 3 of the License, or             ║
║   (at your option) any later version.                         ║
║                                                               ║
║   See [LICENSE](LICENSE) for the full text.                   ║
║                                                               ║
║   ─── SOVEREIGNTY RESERVATION ───                             ║
║                                                               ║
║   The AGPL-3.0 governs the code.                               ║
║   The constitutional architecture (F1-F13, 888 JUDGE,          ║
║   VAULT999, REFLECT-ONLY boundary) is sovereign territory.     ║
║   No fork, no modification, no deployment may alter the        ║
║   authority chain: arifOS judges → Arif ratifies.              ║
║                                                               ║
║   F13 SOVEREIGN: Muhammad Arif bin Fazil                       ║
║   "The mirror reflects. The judge decides. The human rules."   ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

---

## Contributing

This repository operates under the arifOS Federation constitution (F1-F13). See [`AGENTS.md`](AGENTS.md) for the canonical boot sequence and agent operating rules. All contributions must preserve the REFLECT-ONLY authority boundary and the AGPL-3.0 license.

---

**DITEMPA BUKAN DIBERI — Human readiness is forged, not given.**

**999 SEAL ALIVE**
