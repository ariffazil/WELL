"""WELL::READINESS_SCIENCE::v1 — Evidence-based readiness & attention primitives.

Forged 2026-10-15 (AUTHORITY: ARIF) as an ADDITIVE module: no existing verdict
path changes. Consumers: well_assess_homeostasis(mode="readiness") and any
caller wanting pure-Python readiness math.

Authority ceiling: REFLECT_ONLY / ADVISORY. Not medical advice. Research-grade.

Evidence tags used throughout:
  STRONG  = replicated controlled-human evidence (two-process model, KSS,
            caffeine pharmacokinetics, sleep-debt dose-response).
  POPULAR = widely-cited but weak/limited evidence (90-min ultradian cycles,
            HRV single-day readiness).

Design: pure functions, no I/O, no state.json dependency. Every composite
carries per-component provenance so the caller can show WHY.
"""

from __future__ import annotations

import math
from typing import Any


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


# ── 1. Process S — homeostatic sleep pressure ────────────────────────────────
# STRONG: Borbély 1982; reappraisal Borbély et al., J Sleep Res 2016.
# Behavioural anchor: after ~17h continuous wakefulness, psychomotor
# performance degrades to ~0.05% BAC equivalence (Dawson & Reid, Nature 1997);
# after 24h, ~0.10%. Sigmoid centred at 16.5h awake captures that knee.

def sleep_pressure(hours_awake: float, prior_sleep_hours: float | None = None) -> dict[str, Any]:
    """Sigmoid proxy of Process S. Returns 0..1 pressure + provenance."""
    h = _clamp(float(hours_awake), 0.0, 40.0)
    p = 1.0 / (1.0 + math.exp(-(h - 16.5) / 2.5))
    # Prior night's short sleep (<6h) adds residual pressure even after waking.
    residual = 0.0
    if prior_sleep_hours is not None:
        short = _clamp((6.0 - float(prior_sleep_hours)) / 6.0)  # 0 at >=6h, 1 at 0h
        residual = 0.15 * short
    total = _clamp(p + residual)
    return {
        "value": round(total, 3),
        "evidence": "STRONG",
        "anchors": {
            "hours_awake": h,
            "knee_hours": 16.5,
            "bac_equivalence": (
                "≈0.05% at 17h, ≈0.10% at 24h awake (Dawson & Reid 1997)"
                if h >= 17
                else None
            ),
        },
    }


# ── 2. Process C — circadian alertness curve ─────────────────────────────────
# STRONG: two-harmonic fits of subjective alertness + performance (main nadir
# ~04:00-06:00, secondary post-lunch dip ~13:00-16:00, peak early evening).

def circadian_alertness(local_hour: float, chronotype_shift_h: float = 0.0) -> dict[str, Any]:
    """Two-harmonic alertness curve, 0..1. chronotype_shift_h>0 = night owl."""
    t = (float(local_hour) - float(chronotype_shift_h)) % 24.0
    rad = 2.0 * math.pi * t / 24.0
    # Base: peak ~18:00, nadir ~05:00. Second harmonic: post-lunch dip.
    base = 0.5 + 0.34 * math.cos(rad - 2.0 * math.pi * (18.0 / 24.0))
    dip = 0.06 * math.cos(2 * rad - 2.0 * math.pi * (14.5 / 12.0))
    v = _clamp(base + dip)
    phase = "nadir" if 3.0 <= t < 6.5 else "post_lunch_dip" if 13.0 <= t < 16.5 else "normal"
    return {
        "value": round(v, 3),
        "phase": phase,
        "evidence": "STRONG",
        "note": "Two-harmonic fit; main nadir 04:00-06:00, secondary dip 13:00-16:00",
    }


# ── 3. Caffeine pharmacokinetics ──────────────────────────────────────────────
# STRONG: elimination half-life in adults 3-7h (typical ~5h). First-order decay.

def caffeine_load(events: list[dict[str, float]] | None,
                  half_life_h: float = 5.0) -> dict[str, Any]:
    """events = [{'mg': 100, 'hours_ago': 3}, ...]. Active mg right now."""
    if not events:
        return {"active_mg": 0.0, "evidence": "STRONG",
                "note": "no events provided; 0 active"}
    mg = 0.0
    for e in events or []:
        dose = float(e.get("mg", 0))
        ago = float(e.get("hours_ago", 0))
        if dose > 0 and ago >= 0:
            mg += dose * math.pow(0.5, ago / half_life_h)
    return {
        "active_mg": round(mg, 1),
        "half_life_h": half_life_h,
        "evidence": "STRONG",
        "cutoff_guidance": (
            "Common evidence-backed guidance: last dose ≥6-8h before bed "
            "(≈1-1.5 half-lives)."
        ),
    }


# ── 4. Weekly sleep debt ─────────────────────────────────────────────────────
# STRONG: cumulative debt shows dose-response deficits; recovery is slow
# (Van Dongen et al. 2003 — 6h/night for 2 weeks ≈ 1 night total deprivation).

def weekly_sleep_debt(sleep_hours_by_night: list[float],
                      target_per_night: float = 7.0) -> dict[str, Any]:
    nights = [float(x) for x in (sleep_hours_by_night or [])][-7:]
    if not nights:
        return {"debt_hours": None, "evidence": "STRONG", "note": "no nights provided"}
    debt = max(0.0, target_per_night * len(nights) - sum(nights))
    return {
        "debt_hours": round(debt, 1),
        "nights_counted": len(nights),
        "target_per_night": target_per_night,
        "evidence": "STRONG",
        "recovery_note": (
            "Recovery is imperfect: long-term debt is not fully repaid by extra "
            "weekend sleep; metabolic/performance deficits persist partially."
        ),
    }


# ── 5. Subjective anchors (no hardware needed) ───────────────────────────────
# STRONG: KSS (Åkerstedt & Gillberg 1990) correlates with PVT lapses and
# driving impairment. Stanford Sleepiness Scale similar, 7-point.

def kss_to_score(kss: float | None) -> dict[str, Any]:
    """Karolinska Sleepiness Scale 1..9 → readiness penalty 0..1."""
    if kss is None:
        return {"value": None, "evidence": "STRONG", "note": "not provided"}
    k = _clamp(float(kss), 1.0, 9.0)
    penalty = (k - 3.0) / 6.0  # KSS<=3 = alert → 0; KSS>=9 = fighting sleep → 1
    return {
        "value": round(_clamp(penalty), 3),
        "kss": k,
        "evidence": "STRONG",
        "flag": "sleep_attack_risk" if k >= 8 else None,
    }


# ── 6. Vigilance & nap science (recommendation layer) ─────────────────────────
# Vigilance decrement: STRONG (meta-analyses; onsets ~20-40 min on task).
# Nap timing: STRONG for 10-20min power naps (minimal sleep inertia);
# 90min full cycle POPULAR-to-moderate; 20-60min naps = inertia window.

def attention_advisories(minutes_on_task: float | None, nap_minutes: float | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"evidence": "STRONG"}
    if minutes_on_task is not None:
        m = float(minutes_on_task)
        if m >= 40:
            out["micro_break"] = "DUE — vigilance decrement reliably exceeds 20-40 min on task"
        elif m >= 20:
            out["micro_break"] = "SOON — decrement onset window (20-40 min)"
        else:
            out["micro_break"] = None
        out["minutes_on_task"] = m
    if nap_minutes is not None:
        n = float(nap_minutes)
        if n <= 20:
            out["nap_read"] = f"{n:g} min — power-nap range, minimal sleep inertia"
        elif n < 90:
            out["nap_read"] = f"{n:g} min — slow-wave inertia window; grogginess likely on wake"
        else:
            out["nap_read"] = f"{n:g} min — ~full cycle; wake at end of cycle reduces inertia (cycle length varies by person — POPULAR-to-moderate)"
    return out


# ── 7. Composite readiness ────────────────────────────────────────────────────

def composite_readiness(
    hours_awake: float | None = None,
    prior_sleep_hours: float | None = None,
    local_hour: float | None = None,
    chronotype_shift_h: float = 0.0,
    caffeine_events: list[dict[str, float]] | None = None,
    sleep_hours_by_night: list[float] | None = None,
    kss: float | None = None,
    hrv_status: str = "normal",
    minutes_on_task: float | None = None,
    nap_minutes: float | None = None,
) -> dict[str, Any]:
    """Advisory composite 0-100 with full provenance. Never a verdict."""
    comps: dict[str, Any] = {}
    weights: dict[str, float] = {}

    if hours_awake is not None:
        sp = sleep_pressure(hours_awake, prior_sleep_hours)
        comps["process_s"] = sp
        weights["process_s"] = 0.35
    if local_hour is not None:
        ca = circadian_alertness(local_hour, chronotype_shift_h)
        comps["process_c"] = ca
        weights["process_c"] = 0.25
    if sleep_hours_by_night is not None:
        sd = weekly_sleep_debt(sleep_hours_by_night)
        comps["sleep_debt"] = sd
        weights["sleep_debt"] = 0.20
    if kss is not None:
        ks = kss_to_score(kss)
        comps["kss"] = ks
        weights["kss"] = 0.20
    if caffeine_events:
        comps["caffeine"] = caffeine_load(caffeine_events)
        # caffeine is a modifier, not a weighted component
    if hrv_status != "normal":
        comps["hrv"] = {
            "status": hrv_status,
            "evidence": "POPULAR",
            "note": "single-day HRV readiness has weak validation vs multi-day baselines",
        }

    if not weights:
        return {
            "readiness_score": None,
            "status": "UNKNOWN",
            "reason": "No inputs provided. WELL cannot infer readiness from nothing.",
            "components": comps,
            "boundary_notice": "Not diagnosis. Not medical advice. Reflective readiness only. Arif remains final judge.",
        }

    # 0..1 readiness where each weighted component is 'good' = 1
    total = 0.0
    wsum = 0.0
    for name, w in weights.items():
        c = comps[name]
        if name == "process_s":
            good = 1.0 - c["value"]
        elif name == "process_c":
            good = c["value"]
        elif name == "sleep_debt":
            good = _clamp(1.0 - (c["debt_hours"] or 0.0) / 14.0)
        elif name == "kss":
            good = 1.0 - (c["value"] or 0.0)
        else:
            continue
        total += w * good
        wsum += w
    score = round(100.0 * total / wsum) if wsum else None

    # caffeine modifier: active load >150mg can mask fatigue — flag, don't boost
    caf = comps.get("caffeine", {}).get("active_mg")
    masked = bool(caf and caf > 150.0 and (comps.get("process_s", {}).get("value", 0) or 0) > 0.6)

    if score is None:
        status = "UNKNOWN"
    elif score >= 80:
        status = "OPTIMAL"
    elif score >= 60:
        status = "FUNCTIONAL"
    else:
        status = "LOW_CAPACITY"

    result: dict[str, Any] = {
        "readiness_score": score,
        "status": status,
        "components": comps,
        "weights": weights,
        "caffeine_masking_warning": (
            "Caffeine load masks elevated sleep pressure — score reflects chemistry, not recovered capacity."
            if masked else None
        ),
        "advisories": attention_advisories(minutes_on_task, nap_minutes),
        "boundary_notice": "Not diagnosis. Not medical advice. Reflective readiness only. Arif remains final judge.",
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }
    return result
