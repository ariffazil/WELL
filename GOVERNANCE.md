# ⚖️ AFWELL Governance Framework

**Protocol:** Biological Substrate Gating (BSG) v1.0
**Axiom:** Intent integrity is a function of substrate capacity.

---

## 1. Decision Classes (C-Axis)

AFWELL classifies all operator actions into risk tiers to determine the required readiness score.

| Class | Type | Risk | Req. Score | Human Reconfirmation |
| :--- | :--- | :--- | :--- | :--- |
| **C0** | Reflection / Notes | Zero | 0.0 | No |
| **C1** | Drafting / Organizing | Low | 0.4 | No |
| **C2** | Coding / Testing | Med | 0.55 | Yes (if Amber) |
| **C3** | Public Posting / Replies | Med-High | 0.65 | Yes |
| **C4** | Financial / Legal / Architecture | High | 0.75 | Yes (Absolute) |
| **C5** | Irreversible / Schema Migration | Critical | 0.85 | Yes (Dual-Witness) |

---

## 2. Hard W-Floors

Breaching these floors triggers an automatic **RED** tier recommendation to the arifOS Judge.

### W1 — Sleep Integrity
- **Threshold:** `sleep_debt_days > 2` OR `last_night_hours < 4`.
- **Action:** Block C3–C5 actions. Suggest 24h cooldown.

### W5 — Cognitive Entropy
- **Threshold:** `clarity_score < 4/10` OR `decision_fatigue > 8/10`.
- **Action:** Downgrade all tasks to C1 (Draft-only).

### W6 — Metabolic Pause
- **Threshold:** High-frequency intent loops detected in 15min window.
- **Action:** Mandatory 15-minute forge lockout.

---

## 3. The Handshake Protocol

When `A-FORGE` initiates a forge, it MUST call `well_forge_precheck`.

1. **Pre-check:** `A-FORGE` provides `task_description` and `estimated_intensity`.
2. **Response:** `AFWELL` returns `forge_mode` (full|normal|draft_only|paused).
3. **Execution:** `A-FORGE` executes within the returned bandwidth.
4. **Pressure:** `A-FORGE` signals `well_forge_pressure_update` if complexity spikes.

---

**DITEMPA BUKAN DIBERI — SEALED v2026.04.28**
