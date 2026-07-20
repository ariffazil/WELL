---
type: System
title: WELL Human Readiness
description: Human readiness organ — vitality assessment, fatigue detection, dignity guarding, substrate classification, and cognitive load awareness. REFLECT_ONLY — never diagnostic
resource: http://localhost:18083/health
tags: [federation, human-readiness, vitality, fatigue, dignity, well]
timestamp: 2026-07-20T08:00:00Z
links:
  - ../atlas333.md
  - ../skills/index.md
  - ../federation-map.md
---
# WELL (Human Readiness)

Doctrine: What is true about the human?

## What it does

WELL assesses **human readiness** — the factor most technical systems ignore. It asks:

- Is the human operator ready for this decision?
- Are fatigue, stress, or cognitive load degrading judgment?
- Is dignity preserved in the interaction?
- What is the substrate classification of a given system?

### Key Tools

- **classify_substrate** — Ω-WELL-01: Substrate classification and boundary sensing
- **assess_homeostasis** — Ω-WELL-06: Fatigue, sleep debt, cognitive clarity, stress load, HRV
- **validate_vitality** — Ω-WELL-08: Vitality and readiness assessment
- **guard_dignity** — Ω-WELL-12: Consent, personhood, symbolic boundary protection
- **check_repair** — Ω-WELL-07: Recovery and forge cycle integrity

### The C-Class Threshold Matrix

| Class | Behavior | When |
|-------|----------|------|
| C1/C2 | Proceed unless CRITICAL | Routine operations |
| C3 | Proceed if STABLE or better | Standard decision-making |
| C4 | Proceed only if OPTIMAL; DEFER if STABLE | High-stakes decisions |
| C5 | Proceed only if OPTIMAL + no chronic fatigue | Irreversible actions |

### REFLECT_ONLY Doctrine

WELL **never** issues diagnostic claims. It provides substrate reflection and validated evidence. arifOS judges. Arif decides.

## Port

`:18083` — Python FastMCP server

## Key Paths

- `/root/WELL/` — Source
- `/root/WELL/GENESIS/` — Human readiness canon (indexed)
- `/root/WELL/docs/` — Documentation (indexed)
- `/root/WELL/well_mcp/` — MCP server implementation

# Citations

[1] WELL documentation audit SEAL (seq 12) — /root/.local/share/arifos/vault999/seal_chain.jsonl
[2] WELL REFLECT_ONLY doctrine — https://github.com/ariffazil/WELL
