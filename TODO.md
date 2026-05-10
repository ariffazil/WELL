# TODO — WELL Biological Substrate

> **Roadmap:** ARIFOS_NEXT_HORIZON_2026  
> **Execution Status:** HOLD until contracts frozen  
> **Last Updated:** 2026-05-10  
> **Seal:** DITEMPA BUKAN DIBERI

---

## ✅ Embodiment Attestation (Completed Earlier Today)

- [x] arifOS embodiment contracts deployed
- [x] Model registry fix

---

## 🔴 P0 — Horizon 0: Canon Lock (Days 0–14)

**Gate: No new features until contracts are frozen.**

### Authority Freeze
- [ ] **Create `REPO_AUTHORITY_MATRIX.md`** — what WELL may own / must not own
- [ ] **Tool inventory** — 60 tools (13 Ω-WELL + aliases), verify boundaries
- [ ] **Schema inventory** — map all substrate schemas
- [ ] **Version string fix** — health endpoint shows `2026.05.10`, not `2026.05.08`

---

## 🟠 P1 — Horizon 1: Security + Session Spine (Days 15–45)

**Gate: Operator state feeds arifOS escalation thresholds.**

### Substrate Evidence Schema
- [ ] **Create `/schemas/substrate_evidence.schema.json`** — structured substrate vitality object
- [ ] **Export `cognitive_load` metric** — via health endpoint or MCP tool
- [ ] **Export `clarity` metric** — operator readiness score

### arifOS Integration
- [ ] **arifOS consumes WELL state** — adjust allowed risk tier based on operator clarity
- [ ] **Threshold enforcement:**
  - `clarity > 0.7` → all tiers allowed
  - `clarity 0.4–0.7` → SOVEREIGN blocked, CRITICAL allowed
  - `clarity < 0.4` → HOLD on all non-query tools

### HRV / Biological Hardening
- [ ] **Validate HRV input** — reject impossible values (HR > 300)
- [ ] **Sensor fallback** — infer from self-reported state if device offline
- [ ] **Privacy boundary** — biological data never leaves WELL container unencrypted

---

## 🟡 P2 — Horizon 2: Deterministic Judge (Days 46–90)

**Gate: WELL evidence is machine-checkable and judge-ready.**

- [ ] **Multi-operator aggregation** — average readiness across panel members
- [ ] **Unavailability handling** — operator offline > 30 min → escalate to next panel member
- [ ] **Readiness history** — 7-day rolling window for trend detection
- [ ] **WELL ↔ arifOS loop** — `gate/well_gate.py` pre-JUDGE biological readiness mirror

---

## 🟢 P3 — Horizon 3: Semantic Federation (Days 91–135)

**Gate: WELL state affects causal decision intelligence.**

### Causal Intelligence
- [ ] **Causal template:** WELL/AAA → arifOS operator state affects escalation threshold
- [ ] **Required causal output:**
  ```json
  {
    "claim": "...",
    "causal_graph_id": "...",
    "intervention_tested": "...",
    "counterfactual": "...",
    "uncertainty": "...",
    "evidence_refs": [],
    "recommended_verdict": "HOLD"
  }
  ```
- [ ] **Predictive operator state** — ML model predicts cognitive load 30 min ahead

---

## 🔵 P4 — Horizon 4: Self-Healing + Release (Days 136–180)

**Gate: WELL informs recovery decisions, never authorizes them.**

- [ ] **Recovery readiness check** — WELL assesses operator fitness before recovery
- [ ] **Intervention suggestions** — recommend break, hydration, sleep before critical decisions
- [ ] **Cross-operator learning** — anonymized readiness patterns (differential privacy)
- [ ] **Public docs cleanup**
- [ ] **Release tag `vNext-Horizon-0`**

---

**DITEMPA BUKAN DIBERI — Biological sovereignty is forged, not given.**
