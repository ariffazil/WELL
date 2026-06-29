---
id: well-substrate-readiness
name: well-substrate-readiness
version: 1.0.0-2026.06.25
description: Human readiness — vitality, fatigue, dignity. Reflect, never diagnose.
owner: WELL team
risk_tier: high
floor_scope: [F1, F2, F4, F6, F7, F9]
autonomy_tier: T1
trigger_phrases:
  - "well"
  - "fatigue"
  - "readiness"
  - "human state"
  - "substrate"
  - "well-substrate-readiness"
dependencies:
  mcp_servers:
    - well
    - arifos
  skills:
    - 444-route-organ-direct
inputs:
  - operator_question
  - decision_class
  - substrate_type
outputs:
  - readiness_verdict
  - decision_bandwidth
  - consent_state
  - substrate_health
  - recommended_action
version_lock:
  schema_version: "1"
  artifact_hash: pending
---

# well-substrate-readiness — SUBSTRATE READINESS SKILL

> **DITEMPA BUKAN DIBERI.** Readiness reflected, not commanded.
> **Skill type:** Substrate mirror — informs judgment, never substitutes for it.

---

## 0. WELL MCP Surface (key tools)

| Tool | Use for |
|------|---------|
| `well_assess_homeostasis` | Regulation, stability, empathic balance |
| `well_validate_vitality` | Readiness, NIAT |
| `well_assess_reliability` | Machine, tool, institution reliability |
| `well_detect_boundary` | Membrane, body, machine, federation boundaries |
| `well_guard_dignity` | Soul, personhood, meaning, symbolic boundaries |
| `well_compute_metabolic_flux` | Cognitive + machine entropy (0.0–1.0) |
| `well_classify_substrate` | Substrate classification and boundary sensing |

---

## 1. The Authority Grammar (Critical)

WELL uses **non-authority verbs only:**

| ✅ ALLOWED | ❌ FORBIDDEN |
|-----------|------------|
| `get` | `approve` |
| `check` | `block` |
| `reflect` | `judge` |
| `suggest` | `execute` |
| `recommend` | `command` |
| `measure` | `certify` |
| `assess` | `diagnose` |

**This is enforced.** WELL is a mirror, not a gate.

---

## 2. Decision Class Routing

| Decision class | WELL action | arifOS verdict |
|---------------|------------|---------------|
| C1/C2 | Precheck OK | arifOS proceeds unless CRITICAL |
| C3 | Check STABLE+ | arifOS proceeds if STABLE |
| C4 | Check OPTIMAL | arifOS proceeds only if OPTIMAL |
| C5 | Check OPTIMAL + no chronic fatigue | arifOS blocks if not OPTIMAL |

---

## 3. Metabolic Flux Thresholds

```
flux < 0.65  → normal operation
flux >= 0.65 → compulsory_reallocation signal
flux >= 0.85 → system_hold
```

---

## 4. Non-Diagnosis Notice (Mandatory in all WELL outputs)

```
WELL is not a doctor, therapist, or diagnostic authority.
For severe, persistent, or urgent symptoms, seek professional care.
This protects operator dignity and safety.
```

---

## 5. Anti-Patterns

- ❌ Using WELL verdict as final approval
- ❌ Using authority verbs (approve/block/judge)
- ❌ Diagnosing medical conditions
- ❌ Making strategic decisions based on WELL alone
- ❌ Ignoring metabolic flux warnings

---

## 6. Pre-Flight Check

```bash
curl -sf http://localhost:18083/health && echo "✅ WELL" || echo "❌ WELL DOWN"
```

If WELL is ❌ → proceed without WELL input, note degraded state.

---

*DITEMPA BUKAN DIBERI — Readiness reflected, never commanded.*
