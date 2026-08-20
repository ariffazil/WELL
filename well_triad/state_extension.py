"""
well_triad.state_extension — Idempotent state.json extension helpers.

Forged 2026-08-20.
Wraps server._load_state / _save_state with additive defaults for the
new metrics keys Phase 1 introduces.
"""

from __future__ import annotations

from typing import Any, Optional


def ensure_metric_keys(state: dict[str, Any]) -> None:
    """Idempotently ensure all Phase 1 metric keys exist."""
    metrics = state.setdefault("metrics", {})
    metrics.setdefault("daily_intake", {})
    metrics.setdefault("hydration_24h_ml", 0.0)
    metrics.setdefault("thermal_sessions", [])
    subs = metrics.setdefault("substances", {})
    subs.setdefault("rolling_24h", {})
    subs.setdefault("alcohol_timeline", [])
    metrics.setdefault("biometrics", {}).setdefault("last", {})
    metrics["biometrics"].setdefault("history", [])


def accumulate_intake(
    state: dict[str, Any],
    *,
    kcal: float,
    protein_g: Optional[float] = None,
    carb_g: Optional[float] = None,
    fat_g: Optional[float] = None,
    hydration_ml: Optional[float] = None,
    caffeine_mg: Optional[float] = None,
    sugar_g: Optional[float] = None,
    fiber_g: Optional[float] = None,
) -> None:
    """Add intake values to rolling 24h counters."""
    metrics = state.setdefault("metrics", {})
    daily = metrics.setdefault("daily_intake", {})
    daily["kcal"] = daily.get("kcal", 0.0) + float(kcal)
    if protein_g is not None:
        daily["protein_g"] = daily.get("protein_g", 0.0) + float(protein_g)
    if carb_g is not None:
        daily["carb_g"] = daily.get("carb_g", 0.0) + float(carb_g)
    if fat_g is not None:
        daily["fat_g"] = daily.get("fat_g", 0.0) + float(fat_g)
    if sugar_g is not None:
        daily["sugar_g"] = daily.get("sugar_g", 0.0) + float(sugar_g)
    if fiber_g is not None:
        daily["fiber_g"] = daily.get("fiber_g", 0.0) + float(fiber_g)
    if hydration_ml is not None:
        metrics["hydration_24h_ml"] = (
            metrics.get("hydration_24h_ml", 0.0) + hydration_ml
        )
    if caffeine_mg is not None:
        subs = metrics.setdefault("substances", {}).setdefault("rolling_24h", {})
        subs["caffeine_mg"] = subs.get("caffeine_mg", 0.0) + caffeine_mg


def append_thermal_session(
    state: dict[str, Any],
    *,
    ts_iso: str,
    duration_min: Optional[float],
    intensity: Optional[float],
    source: str,
) -> None:
    """Append to thermal_sessions, capped at 20."""
    metrics = state.setdefault("metrics", {})
    thermal = metrics.setdefault("thermal_sessions", [])
    thermal.append({
        "ts": ts_iso,
        "duration_min": duration_min,
        "intensity": intensity,
        "source": source,
    })
    if len(thermal) > 20:
        metrics["thermal_sessions"] = thermal[-20:]


def update_fasting_window(state: dict[str, Any], hours: float) -> None:
    """Update metabolic.fasting_window_hours."""
    meta = state.setdefault("metrics", {}).setdefault("metabolic", {})
    meta["fasting_window_hours"] = hours


def accumulate_substance(
    state: dict[str, Any],
    *,
    substance: str,
    dose_mg: Optional[float],
    dose_count: Optional[float],
    occurred_at_iso: str,
    subclass: Optional[str],
    source: str,
) -> None:
    """Update substances.rolling_24h and alcohol_timeline as appropriate."""
    metrics = state.setdefault("metrics", {})
    subs = metrics.setdefault("substances", {})
    rolling_24h = subs.setdefault("rolling_24h", {})

    if substance == "caffeine" and dose_mg is not None:
        rolling_24h["caffeine_mg"] = rolling_24h.get("caffeine_mg", 0.0) + dose_mg
    elif substance == "alcohol":
        if dose_count is not None:
            rolling_24h["alcohol_units"] = (
                rolling_24h.get("alcohol_units", 0.0) + dose_count
            )
        elif dose_mg is not None:
            rolling_24h["alcohol_units"] = (
                rolling_24h.get("alcohol_units", 0.0) + dose_mg / 14_000.0
            )
        timeline = subs.setdefault("alcohol_timeline", [])
        timeline.append({
            "ts": occurred_at_iso,
            "units": dose_count if dose_count is not None
            else (dose_mg / 14_000.0 if dose_mg is not None else None),
            "subclass": subclass,
            "source": source,
        })
        if len(timeline) > 200:
            subs["alcohol_timeline"] = timeline[-200:]
    elif substance == "nicotine" and dose_mg is not None:
        rolling_24h["nicotine_mg"] = (
            rolling_24h.get("nicotine_mg", 0.0) + dose_mg
        )
    else:
        rolling_24h["supplement_count"] = (
            rolling_24h.get("supplement_count", 0) + 1
        )


def set_biometric_last(
    state: dict[str, Any],
    *,
    ts_iso: str,
    source: str,
    device_id: Optional[str],
    readings: dict[str, float],
) -> None:
    """Set biometrics.last and append to biometrics.history (capped 90d)."""
    import datetime as _dt
    metrics = state.setdefault("metrics", {})
    bio = metrics.setdefault("biometrics", {})
    bio["last"] = {
        "ts": ts_iso,
        "source": source,
        "device_id": device_id,
        "readings": readings,
    }
    history = bio.setdefault("history", [])
    history.append({
        "ts": ts_iso,
        "source": source,
        "device_id": device_id,
        "readings": readings,
    })
    cutoff = (
        _dt.datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
        - _dt.timedelta(days=90)
    ).isoformat()
    bio["history"] = [h for h in history if h.get("ts", "") >= cutoff][-2000:]


def truth_status_for(source: str) -> str:
    """Compute truth_status from source provenance."""
    return "VERIFIED_DEVICE" if source != "manual" else "OPERATOR_REPORTED"


def rolling_24h(state: dict[str, Any]) -> dict[str, float]:
    """Read rolling_24h intake counters from state."""
    return dict(state.get("metrics", {}).get("daily_intake", {}))


def rolling_7d_mean(state: dict[str, Any]) -> dict[str, float]:
    """7d mean = rolling_24h × 1/7 placeholder. Real impl: walk events.jsonl.

    Draft returns rolling_24h values as-is for hermetic correctness;
    production wires events.jsonl walker.
    """
    return dict(state.get("metrics", {}).get("daily_intake", {}))


def recovery_7d_counts(state: dict[str, Any]) -> dict[str, int]:
    """Count recovery events by type. Draft returns empty dict."""
    return {}


def alcohol_units_7d(state: dict[str, Any], now_iso: str) -> float:
    """Sum alcohol_units within last 7 days from timeline."""
    import datetime as _dt
    metrics = state.get("metrics", {})
    timeline = metrics.get("substances", {}).get("alcohol_timeline", [])
    now = _dt.datetime.fromisoformat(now_iso.replace("Z", "+00:00"))
    cutoff = (now - _dt.timedelta(days=7)).isoformat()
    total = 0.0
    for entry in timeline:
        if entry.get("ts", "") >= cutoff:
            u = entry.get("units")
            if isinstance(u, (int, float)):
                total += float(u)
    return round(total, 2)


def is_late_caffeine(occurred_at: "_dt.datetime") -> bool:
    """True if caffeine was logged at >= 14:00 local time."""
    return occurred_at.astimezone().hour >= 14