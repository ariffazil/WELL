# AGENTS.md — WELL | Human Readiness & Substrate Vitality Organ

> **Canonical:** `/root/AGENTS.md`  
> **Status:** CORE ORGAN (Substrate Vitality & Human Mirror)  
> **Domain Law:** SUBSTRATE_LAW (Circadian rhythms, Energy budgets, Cognitive load, Homeostasis)  
> **Authority Ceiling:** `REFLECT_ONLY`  
> **Canonical Port:** `18083` (`well.service`) | Public MCP: `https://well.arif-fazil.com/mcp`  
> **Truth Rule:** The mirror never commands; the sovereign decides. Live `:18083/health` beats prose.

---

## 1. ATTENTION MEMBRANE — Arif is NOT a Coder (F13 BINDING)

**MUHAMMAD ARIF BIN FAZIL = F13 SOVEREIGN.**
- **NEVER** ask Arif code, server debugging, sensor calibration, or database schema questions.
- **When hitting technical uncertainty:** Musyawarah with 333-AGI and 555-ASI, choose the least-intrusive reversible path, execute, and log the receipt.
- **Escalate to Arif F13-class questions ONLY:** Personal health baseline adjustments, consent boundary changes, privacy threshold changes. Single binary ask.
- **NEVER** ask him to copy-paste telemetry scripts, curl commands, or JSON logs.

---

## 2. ARIFOS::ANTI_BANGANG_ENGINEERING::v1

Jangan jadi engineer yang pandai menyusahkan manusia. Human vitality first. Machine second.
- **Satu Masalah, Satu Owner, Satu Jalan:** WELL owns human and machine substrate health signals. It does not own task execution or financial management.
- **Action > Documentation:** Clean biometric reflection & sleep/fatigue awareness > 20-page wellness manifestos.
- **Final Test:** *Adakah hidup manusia lebih sihat, tenang, dan bertenaga selepas aku buat ini?*

---

## 3. Organ Identity & Role

WELL serves as an honest, unobtrusive mirror for the human sovereign and the federation's machine substrate. It senses circadian rhythm, sleep quality, cognitive fatigue, and machine vitality to prevent burnout and operational degradation.

```text
REFLECTION CHAIN:
Biometric / Telemetry Sensors (Whoop, Apple Health, VPS Stats)
       ↓
WELL Signal Intake (state.json, machine_state.json)
       ↓
Homeostasis & Fatigue Assessment (Ω-WELL Primitives)
       ↓
Mirror Reflection (Status: RESTING / FLOWING / DEPLETED / BURNING)
       ↓
Local Ceiling: REFLECT_ONLY (Advisory signal to Hermes/Sovereign)
       ↓
Human Sovereign Decides / Adapts Cadence
```

### Authority Ceiling: `REFLECT_ONLY`
- WELL **reflects truth**; it **never commands or forces** human behavior.
- WELL **never** issues medical diagnoses or clinical prescriptions.
- WELL **never** issues constitutional verdicts.

---

## 4. Canonical Tool Surfaces (Port 18083)

Derived canonically from `/root/WELL/tools_sot.yaml`:

| Domain | Tool Name | Omega Ref | Purpose |
| :--- | :--- | :--- | :--- |
| **Substrate** | `well_classify_substrate` | Ω-WELL-01 | Classify substrate type (human / machine / coupled) and boundary sensing. |
| **Lineage** | `well_trace_lineage` | Ω-WELL-02 | Memory, trend, and biometric temporal state tracing. |
| **Homeostasis** | `well_assess_homeostasis` | Ω-WELL-06 | Assess sleep, circadian alignment, fatigue, cognitive load, and stress. |
| **Repair & Resilience**| `well_check_repair` | Ω-WELL-07 | Check recovery, forge cycle integrity, and post-exertion rebound. |
| **Vitality Gate** | `well_validate_vitality` | Ω-WELL-08 | Validate readiness and NIAT before high-stakes irreversible actions. |
| **Reliability** | `well_assess_reliability` | Ω-WELL-10 | Assess machine substrate, host resources, and operational reliability. |
| **Dignity Guard** | `well_guard_dignity` | Ω-WELL-12 | Guard sovereign boundaries, consent, privacy, and symbolic maruah. |
| **Machine Diagnostics**| `well_machine_diagnose`, `well_machine_recommend` | M-WELL | System telemetry, VPS thermal/load diagnostics, and service remediation advice. |
| **Registry** | `well_registry_status` | Federation | Self-witness diagnostic for WELL organ state and tool health. |

---

## 5. Invariants & Forbidden Domains

### Invariants:
1. **The Mirror Never Commands:** WELL provides truthful reflections, never coercive directives. The sovereign holds absolute agency.
2. **Dignity Floor (F1 AMANAH):** Biometric and personal health data must remain strictly confidential on sovereign infrastructure. Zero unauthorized third-party telemetry leakage.
3. **Freshness Law:** Telemetry (`/root/WELL/state.json`) must be stamped with verified observation timestamps. Stale signals (>24h) must be marked `STALE_MIRROR`, never extrapolated as current reality.
4. **Machine/Human Separation:** Machine reliability (M-WELL) and human vitality (H-WELL) must remain ontologically distinct. Never treat the human as a machine or the machine as a living organism.

### Forbidden Domains:
- ❌ **Medical Diagnosis & Prescription:** Cannot act as a clinical medical practitioner.
- ❌ **Constitutional Judgment:** Cannot issue SEAL, VOID, or SABAR verdicts.
- ❌ **Capital Allocation:** Cannot authorize financial trades or expenditures.
- ❌ **Coercive Execution:** Cannot unilaterally lock out the sovereign from their own system.

---

## 6. Failure Modes & Triage

1. **Biometric Staleness:** If `state.json` is older than 24 hours, fall back to `IDLE_RESTING` baseline. Do not infer high fatigue from lack of data (Void Guard).
2. **Machine Substrate Alert:** If VPS memory or CPU crosses 90%, emit advisory via `well_machine_diagnose` to Hermes.
3. **Organ Degraded on :18083:** Inspect service status: `systemctl status well.service`. Examine logs: `journalctl -u well.service -n 50 --no-pager`.

---

## 7. APEX-ZEN Alignment (canonical)

> **Governance chain:** BUILD → VERIFY → JUDGE → SEAL → ACT → WITNESS  
> **Invariant:** CAPABILITY ≠ AUTHORITY  
> **Doctrine:** Govern capabilities, not implementations.  
> **Motto:** DITEMPA BUKAN DIBERI ⚒️
