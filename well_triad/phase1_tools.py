"""
well_triad.phase1_tools — Canonical Phase 1 tool implementations.

Forged 2026-08-20. F13 SEALED. Production.

Exports 4 tool functions to be registered with FastMCP in server.py:
  well_log_intake
  well_log_recovery_event
  well_log_substance
  well_inject_biometric

All 4 follow the existing well_log (server.py:3172) pattern: extend
state.json metrics, append typed event to events.jsonl, return typed dict.

Authority ceiling: WRITE_OWN_STATE (per-tool). F13 floor envelope enforced.
"""

from __future__ import annotations

import datetime as _dt
import os
import sys
import time as _time
from typing import Any, Literal, Optional

from fastmcp import Context

from well_triad import consent_scopes, events, sanitize, state_extension as sx


HERMES_HERMETIC_TOKEN_ENV = "HERMES_HERMETIC_TOKEN"

ALLOWED_BIOMETRIC_KEYS: frozenset[str] = frozenset({
    "hrv_ms",
    "resting_hr_bpm",
    "spo2_pct",
    "skin_temp_c",
    "weight_kg",
    "body_fat_pct",
    "lean_mass_kg",
    "vo2_max",
    "sleep_hours",
    "sleep_rem_pct",
    "sleep_deep_pct",
    "steps",
    "active_energy_kcal",
    "respiratory_rate",
})


# ── Server bindings (lazy, captured at install time) ────────────────────────
# server.py calls install_bindings(_load_state, _save_state) at module load
# to wire its helpers into this module without re-importing server (which
# would re-trigger the arifOS import chain).
_load_state_fn = None
_save_state_fn = None


def install_bindings(load_state_fn, save_state_fn):
    """Called by server.py at module load to wire its helpers."""
    global _load_state_fn, _save_state_fn
    _load_state_fn = load_state_fn
    _save_state_fn = save_state_fn


def _load_state() -> dict[str, Any]:
    if _load_state_fn is None:
        raise RuntimeError(
            "well_triad.phase1_tools.install_bindings() not called"
        )
    return _load_state_fn()


def _save_state(state: dict[str, Any]) -> None:
    if _save_state_fn is None:
        raise RuntimeError(
            "well_triad.phase1_tools.install_bindings() not called"
        )
    _save_state_fn(state)


# ── Per-tool floor envelope helpers ─────────────────────────────────────────

def _floor_block(floor: str, detail: str, **extras: Any) -> dict[str, Any]:
    out = {
        "ok": False,
        "error": f"{floor}_BLOCK",
        "floor": floor,
        "detail": detail,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        "f13_sovereign": "OPERATOR_VETO_INTACT",
    }
    out.update(extras)
    return out


def _clamp(v: Optional[float], lo: float, hi: float) -> Optional[float]:
    if v is None:
        return None
    if not (lo <= v <= hi):
        raise ValueError(f"value {v} out of range [{lo}, {hi}]")
    return float(v)


def _hermes_token() -> Optional[str]:
    return os.environ.get(HERMES_HERMETIC_TOKEN_ENV)


# ── Tool 1: well_log_intake ─────────────────────────────────────────────────

INTAKE_SOURCES = ("manual", "photo", "estimate", "barcode")


def well_log_intake(
    meal_label: str,
    kcal: float,
    protein_g: Optional[float] = None,
    carb_g: Optional[float] = None,
    fat_g: Optional[float] = None,
    hydration_ml: Optional[float] = None,
    caffeine_mg: Optional[float] = None,
    sugar_g: Optional[float] = None,
    fiber_g: Optional[float] = None,
    location_label: Optional[str] = None,
    eaten_at_utc: Optional[_dt.datetime] = None,
    source: Literal["manual", "photo", "estimate", "barcode"] = "manual",
    confidence: float = 0.6,
    consent_scope: str = "intake.basic",
    note: Optional[str] = None,
    ctx: Optional[Context] = None,
) -> dict[str, Any]:
    """Log a meal/snack/intake event with kcal + macro breakdown."""


    # ── F2: provenance ──────────────────────────────────────────────────────
    if source not in INTAKE_SOURCES:
        return _floor_block(
            "F2_amanah_provenance",
            f"source cannot be '{source}'; choose one of: {', '.join(INTAKE_SOURCES)}",
        )

    # ── F4: PII scan ────────────────────────────────────────────────────────
    for field_name, field_value in (
        ("meal_label", meal_label),
        ("location_label", location_label),
        ("note", note),
    ):
        pii = sanitize.scan_pii(field_value)
        if pii:
            return _floor_block(
                "F4_privacy",
                f"field '{field_name}' contains PII pattern: {pii}",
                redacted_field=field_name,
            )

    # ── F11: consent gate ───────────────────────────────────────────────────
    required_scope = consent_scope
    if location_label is not None and consent_scope == "intake.basic":
        required_scope = "intake.location"
    state_for_consent = _load_state()
    active, revoked_at = consent_scopes.consent_active(state_for_consent, required_scope)
    # Persist scope registration (consent_active mutates state.consent.scopes)
    _save_state(state_for_consent)
    if not active:
        return _floor_block(
            "F11_consent",
            f"scope '{required_scope}' not granted or revoked at {revoked_at}",
            scope_required=required_scope,
            scope_status="REVOKED" if revoked_at else "NOT_GRANTED",
        )

    # ── Validate numeric ranges ────────────────────────────────────────────
    try:
        kcal = _clamp(kcal, 0.0, 10_000.0) or 0.0
        protein_g = _clamp(protein_g, 0.0, 500.0)
        carb_g = _clamp(carb_g, 0.0, 1000.0)
        fat_g = _clamp(fat_g, 0.0, 500.0)
        hydration_ml = _clamp(hydration_ml, 0.0, 10_000.0)
        caffeine_mg = _clamp(caffeine_mg, 0.0, 2000.0)
        sugar_g = _clamp(sugar_g, 0.0, 500.0)
        fiber_g = _clamp(fiber_g, 0.0, 200.0)
        confidence = _clamp(confidence, 0.0, 1.0) or 0.6
    except ValueError as e:
        return _floor_block("F2_amanah_provenance", f"Invalid input: {e}")

    note = sanitize.sanitize_note(note)
    eaten_at = eaten_at_utc or _dt.datetime.now(_dt.timezone.utc)

    # ── Update state.json ───────────────────────────────────────────────────
    state = _load_state()
    sx.ensure_metric_keys(state)
    sx.accumulate_intake(
        state,
        kcal=kcal,
        protein_g=protein_g,
        carb_g=carb_g,
        fat_g=fat_g,
        hydration_ml=hydration_ml,
        caffeine_mg=caffeine_mg,
        sugar_g=sugar_g,
        fiber_g=fiber_g,
    )
    state["truth_status"] = "OPERATOR_REPORTED"
    _save_state(state)

    # ── Append typed event ──────────────────────────────────────────────────
    truth_class = "OBS" if source == "barcode" else "INT"
    event_id = events.append_typed_event(
        event="WELL_TRIAD_1_INTAKE",
        phase=1,
        tool="well_log_intake",
        plane="human",
        inputs={
            "meal_label": meal_label,
            "kcal": kcal,
            "protein_g": protein_g,
            "carb_g": carb_g,
            "fat_g": fat_g,
            "hydration_ml": hydration_ml,
            "caffeine_mg": caffeine_mg,
            "sugar_g": sugar_g,
            "fiber_g": fiber_g,
            "location_label": location_label,
            "source": source,
            "confidence": confidence,
        },
        consent_scope=required_scope,
        source=source,
        truth_class=truth_class,
        evidence_label=truth_class,
        note=note,
        timestamp_utc=eaten_at.isoformat(),
    )

    return {
        "ok": True,
        "event_id": event_id,
        "received": {
            "kcal": kcal,
            "protein_g": protein_g,
            "carb_g": carb_g,
            "fat_g": fat_g,
            "hydration_ml": hydration_ml,
            "caffeine_mg": caffeine_mg,
            "sugar_g": sugar_g,
            "fiber_g": fiber_g,
        },
        "rolling_24h": sx.rolling_24h(state),
        "rolling_7d_mean": sx.rolling_7d_mean(state),
        "consent_scope": required_scope,
        "f2_provenance": source,
        "f4_privacy": "leaves_host:false",
        "f11_consent": required_scope,
        "f13_sovereign": "OPERATOR_VETO_INTACT",
        "truth_status": "OPERATOR_REPORTED",
        "truth_class": truth_class,
        "evidence_label": truth_class,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


# ── Tool 2: well_log_recovery_event ──────────────────────────────────────────

RECOVERY_SOURCES = ("manual", "watch", "ring", "app")
RECOVERY_TYPES = (
    "sauna", "cold_exposure", "nap", "meditation",
    "walk", "stretching", "fasting_start", "fasting_end",
    "breathwork", "massage", "sleep_block",
)


def well_log_recovery_event(
    event_type: Literal[
        "sauna", "cold_exposure", "nap", "meditation",
        "walk", "stretching", "fasting_start", "fasting_end",
        "breathwork", "massage", "sleep_block",
    ],
    duration_min: Optional[float] = None,
    intensity: Optional[float] = None,
    fasting_window_hours: Optional[float] = None,
    occurred_at_utc: Optional[_dt.datetime] = None,
    source: Literal["manual", "watch", "ring", "app"] = "manual",
    confidence: float = 0.6,
    consent_scope: str = "recovery.basic",
    note: Optional[str] = None,
    ctx: Optional[Context] = None,
) -> dict[str, Any]:
    """Log a recovery/restorative event."""


    # ── F2 ──────────────────────────────────────────────────────────────────
    if source not in RECOVERY_SOURCES:
        return _floor_block(
            "F2_amanah_provenance",
            f"source cannot be '{source}'; choose one of: {', '.join(RECOVERY_SOURCES)}",
        )

    # ── F4 ──────────────────────────────────────────────────────────────────
    pii = sanitize.scan_pii(note)
    if pii:
        return _floor_block(
            "F4_privacy",
            f"field 'note' contains PII pattern: {pii}",
            redacted_field="note",
        )

    # ── F11 ─────────────────────────────────────────────────────────────────
    state_for_consent = _load_state()
    active, revoked_at = consent_scopes.consent_active(state_for_consent, consent_scope)
    _save_state(state_for_consent)
    if not active:
        return _floor_block(
            "F11_consent",
            f"scope '{consent_scope}' not granted or revoked at {revoked_at}",
            scope_required=consent_scope,
            scope_status="REVOKED" if revoked_at else "NOT_GRANTED",
        )

    # ── Validate ────────────────────────────────────────────────────────────
    try:
        duration_min = _clamp(duration_min, 0.0, 1440.0)
        intensity = _clamp(intensity, 0.0, 10.0)
        fasting_window_hours = _clamp(fasting_window_hours, 0.0, 168.0)
        confidence = _clamp(confidence, 0.0, 1.0) or 0.6
    except ValueError as e:
        return _floor_block("F2_amanah_provenance", f"Invalid input: {e}")

    note = sanitize.sanitize_note(note)
    occurred_at = occurred_at_utc or _dt.datetime.now(_dt.timezone.utc)

    # ── Update state.json ───────────────────────────────────────────────────
    state = _load_state()
    sx.ensure_metric_keys(state)

    if event_type in ("fasting_start", "fasting_end") and fasting_window_hours is not None:
        sx.update_fasting_window(state, fasting_window_hours)

    if event_type == "sauna":
        sx.append_thermal_session(
            state,
            ts_iso=occurred_at.isoformat(),
            duration_min=duration_min,
            intensity=intensity,
            source=source,
        )

    state["truth_status"] = "OPERATOR_REPORTED"
    _save_state(state)

    # ── Append typed event ──────────────────────────────────────────────────
    truth_class = "OBS" if source in ("watch", "ring", "app") else "INT"
    event_id = events.append_typed_event(
        event="WELL_TRIAD_1_RECOVERY",
        phase=1,
        tool="well_log_recovery_event",
        plane="human",
        inputs={
            "event_type": event_type,
            "duration_min": duration_min,
            "intensity": intensity,
            "fasting_window_hours": fasting_window_hours,
            "source": source,
            "confidence": confidence,
        },
        consent_scope=consent_scope,
        source=source,
        truth_class=truth_class,
        evidence_label=truth_class,
        note=note,
        timestamp_utc=occurred_at.isoformat(),
    )

    return {
        "ok": True,
        "event_id": event_id,
        "received": {
            "event_type": event_type,
            "duration_min": duration_min,
            "intensity": intensity,
            "fasting_window_hours": fasting_window_hours,
        },
        "rolling_7d_count": sx.recovery_7d_counts(state),
        "consent_scope": consent_scope,
        "f2_provenance": source,
        "f4_privacy": "leaves_host:false",
        "f11_consent": consent_scope,
        "f13_sovereign": "OPERATOR_VETO_INTACT",
        "truth_status": "OPERATOR_REPORTED",
        "truth_class": truth_class,
        "evidence_label": truth_class,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


# ── Tool 3: well_log_substance ──────────────────────────────────────────────

SUBSTANCES = (
    "caffeine", "alcohol", "nicotine", "melatonin",
    "creatine", "magnesium", "modafinil", "other",
)
SUBSTANCE_SOURCES = ("manual", "watch", "ring", "app")


def well_log_substance(
    substance: Literal[
        "caffeine", "alcohol", "nicotine", "melatonin",
        "creatine", "magnesium", "modafinil", "other",
    ],
    subclass: Optional[str] = None,
    dose_mg: Optional[float] = None,
    dose_unit: Optional[Literal["mg", "g", "ml", "cup", "tablet", "drop"]] = None,
    dose_count: Optional[float] = None,
    occurred_at_utc: Optional[_dt.datetime] = None,
    source: Literal["manual", "watch", "ring", "app"] = "manual",
    confidence: float = 0.6,
    consent_scope: str = "substance.full",
    note: Optional[str] = None,
    ctx: Optional[Context] = None,
) -> dict[str, Any]:
    """Log a substance intake event."""


    # ── F2 ──────────────────────────────────────────────────────────────────
    if source not in SUBSTANCE_SOURCES:
        return _floor_block(
            "F2_amanah_provenance",
            f"source cannot be '{source}'; choose one of: {', '.join(SUBSTANCE_SOURCES)}",
        )

    # ── F4 ──────────────────────────────────────────────────────────────────
    for field_name, field_value in (("subclass", subclass), ("note", note)):
        pii = sanitize.scan_pii(field_value)
        if pii:
            return _floor_block(
                "F4_privacy",
                f"field '{field_name}' contains PII pattern: {pii}",
                redacted_field=field_name,
            )

    # ── F11: stricter scope ─────────────────────────────────────────────────
    state_for_consent = _load_state()
    active, revoked_at = consent_scopes.consent_active(state_for_consent, consent_scope)
    _save_state(state_for_consent)
    if not active:
        return _floor_block(
            "F11_consent",
            f"scope '{consent_scope}' not granted or revoked at {revoked_at}. "
            "Substance tracking requires explicit opt-in.",
            scope_required=consent_scope,
            scope_status="REVOKED" if revoked_at else "NOT_GRANTED",
        )

    # ── Validate ────────────────────────────────────────────────────────────
    try:
        dose_mg = _clamp(dose_mg, 0.0, 10_000.0)
        dose_count = _clamp(dose_count, 0.0, 100.0)
        confidence = _clamp(confidence, 0.0, 1.0) or 0.6
    except ValueError as e:
        return _floor_block("F2_amanah_provenance", f"Invalid input: {e}")

    note = sanitize.sanitize_note(note)
    occurred_at = occurred_at_utc or _dt.datetime.now(_dt.timezone.utc)

    # ── Update state.json ───────────────────────────────────────────────────
    state = _load_state()
    sx.ensure_metric_keys(state)
    sx.accumulate_substance(
        state,
        substance=substance,
        dose_mg=dose_mg,
        dose_count=dose_count,
        occurred_at_iso=occurred_at.isoformat(),
        subclass=subclass,
        source=source,
    )
    state["truth_status"] = "OPERATOR_REPORTED"
    _save_state(state)

    # ── Append typed event ──────────────────────────────────────────────────
    truth_class = "OBS" if source in ("watch", "ring", "app") else "INT"
    event_id = events.append_typed_event(
        event="WELL_TRIAD_1_SUBSTANCE",
        phase=1,
        tool="well_log_substance",
        plane="human",
        inputs={
            "substance": substance,
            "subclass": subclass,
            "dose_mg": dose_mg,
            "dose_unit": dose_unit,
            "dose_count": dose_count,
            "source": source,
            "confidence": confidence,
        },
        consent_scope=consent_scope,
        source=source,
        truth_class=truth_class,
        evidence_label=truth_class,
        note=note,
        timestamp_utc=occurred_at.isoformat(),
    )

    # ── Informational flags ─────────────────────────────────────────────────
    late_caffeine = (
        substance == "caffeine" and sx.is_late_caffeine(occurred_at)
    )
    alcohol_units_7d = sx.alcohol_units_7d(state, occurred_at.isoformat())
    rolling_24h = state.get("metrics", {}).get("substances", {}).get("rolling_24h", {})

    return {
        "ok": True,
        "event_id": event_id,
        "received": {
            "substance": substance,
            "subclass": subclass,
            "dose_mg": dose_mg,
            "dose_unit": dose_unit,
            "dose_count": dose_count,
        },
        "rolling_24h": rolling_24h,
        "late_caffeine": late_caffeine,
        "alcohol_units_7d": alcohol_units_7d,
        "consent_scope": consent_scope,
        "f2_provenance": source,
        "f4_privacy": "leaves_host:false",
        "f11_consent": consent_scope,
        "f13_sovereign": "OPERATOR_VETO_INTACT",
        "truth_status": "OPERATOR_REPORTED",
        "truth_class": truth_class,
        "evidence_label": truth_class,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        "_f8_disclaimer": (
            "late_caffeine is an informational timestamp heuristic, "
            "not a verdict on sleep impact."
        ),
    }


# ── Tool 4: well_inject_biometric (Hermes-only) ──────────────────────────────

BIOMETRIC_SOURCES = ("apple_health", "whoop", "oura", "withings", "garmin", "manual")


def well_inject_biometric(
    source: Literal[
        "apple_health", "whoop", "oura", "withings", "garmin", "manual",
    ],
    readings: dict[str, float],
    observed_at_utc: Optional[_dt.datetime] = None,
    consent_scope: str = "biometric.full",
    device_id: Optional[str] = None,
    actor_token: Optional[str] = None,
    ctx: Optional[Context] = None,
) -> dict[str, Any]:
    """Hermes-only biometric injection from external device."""


    # ── F13: Hermes-only ────────────────────────────────────────────────────
    expected = _hermes_token()
    if expected is None:
        return _floor_block(
            "F13_sovereign",
            f"server misconfigured: env {HERMES_HERMETIC_TOKEN_ENV} is unset",
        )
    if actor_token != expected:
        return _floor_block(
            "F13_sovereign",
            "tool requires Hermes actor_token",
        )

    # ── F2: provenance ──────────────────────────────────────────────────────
    if source not in BIOMETRIC_SOURCES:
        return _floor_block(
            "F2_amanah_provenance",
            f"source cannot be '{source}'",
        )
    if source != "manual" and not device_id:
        return _floor_block(
            "F2_amanah_provenance",
            f"source={source} requires device_id for F2 provenance",
        )

    # ── F11: strictest scope ────────────────────────────────────────────────
    state_for_consent = _load_state()
    active, revoked_at = consent_scopes.consent_active(state_for_consent, consent_scope)
    _save_state(state_for_consent)
    if not active:
        return _floor_block(
            "F11_consent",
            f"scope '{consent_scope}' not granted or revoked at {revoked_at}. "
            "Biometric injection requires Hermes-mediated opt-in.",
            scope_required=consent_scope,
            scope_status="REVOKED" if revoked_at else "NOT_GRANTED",
        )

    # ── Validate readings ───────────────────────────────────────────────────
    keys_logged: list[str] = []
    keys_rejected: list[str] = []
    sanitized: dict[str, float] = {}
    for k, v in readings.items():
        if k not in ALLOWED_BIOMETRIC_KEYS:
            keys_rejected.append(k)
            continue
        if not isinstance(v, (int, float)):
            keys_rejected.append(k)
            continue
        # physical plausibility bounds
        if k.endswith("_pct") and not (0 <= v <= 100):
            keys_rejected.append(k)
            continue
        if k == "hrv_ms" and not (0 <= v <= 300):
            keys_rejected.append(k)
            continue
        if k == "resting_hr_bpm" and not (20 <= v <= 200):
            keys_rejected.append(k)
            continue
        if k == "spo2_pct" and not (50 <= v <= 100):
            keys_rejected.append(k)
            continue
        if k == "skin_temp_c" and not (25 <= v <= 45):
            keys_rejected.append(k)
            continue
        if k == "weight_kg" and not (20 <= v <= 300):
            keys_rejected.append(k)
            continue
        if k == "vo2_max" and not (10 <= v <= 100):
            keys_rejected.append(k)
            continue
        if k == "sleep_hours" and not (0 <= v <= 24):
            keys_rejected.append(k)
            continue
        sanitized[k] = float(v)
        keys_logged.append(k)

    if not sanitized:
        return _floor_block(
            "F2_amanah_provenance",
            "no valid readings after validation",
            keys_rejected=keys_rejected,
        )

    observed_at = observed_at_utc or _dt.datetime.now(_dt.timezone.utc)

    # ── Update state.json ───────────────────────────────────────────────────
    state = _load_state()
    sx.ensure_metric_keys(state)
    sx.set_biometric_last(
        state,
        ts_iso=observed_at.isoformat(),
        source=source,
        device_id=device_id,
        readings=sanitized,
    )
    state["truth_status"] = sx.truth_status_for(source)
    _save_state(state)

    # ── Append typed event ──────────────────────────────────────────────────
    truth_class = "OBS" if source != "manual" else "INT"
    provenance = f"{source}:{device_id}" if device_id else source
    event_id = events.append_typed_event(
        event="WELL_TRIAD_1_BIOMETRIC_INJECT",
        phase=1,
        tool="well_inject_biometric",
        plane="human",
        actor_hermes=True,
        inputs={
            "source": source,
            "device_id": device_id,
            "readings": sanitized,
        },
        consent_scope=consent_scope,
        source=provenance,
        truth_class=truth_class,
        evidence_label=truth_class,
        timestamp_utc=observed_at.isoformat(),
    )

    return {
        "ok": True,
        "event_id": event_id,
        "received_count": len(sanitized),
        "keys_logged": keys_logged,
        "keys_rejected": keys_rejected,
        "consent_scope": consent_scope,
        "f2_provenance": provenance,
        "f4_privacy": "leaves_host:false",
        "f11_consent": consent_scope,
        "f13_sovereign": "OPERATOR_VETO_INTACT",
        "f13_hermes_enforced": True,
        "truth_status": state["truth_status"],
        "truth_class": truth_class,
        "evidence_label": truth_class,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }