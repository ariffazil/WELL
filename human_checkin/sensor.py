"""WELL::HUMAN_SENSOR::v1 — route-agnostic SENSOR_MEASURED intake (P0).

F13 sovereign directive 2026-11-19 (autonomous mode): accept measured events
from ANY route — Health Connect agent, Zepp open API, Gadgetbridge export —
without rework, without manual data provision, without biometric_inject.sh.

Design (mirrors the check-in v1 pattern, DIFFERENT stream):
  - append-only sensor_events.jsonl, flock + fsync atomic append
  - idempotent: subject|source|values|arrival-bucket key + 600s collapse window
  - per-signal freshness: a fresh sync NEVER refreshes another signal
  - provenance is FIXED to sensor_measured — callers cannot forge it
  - registry-gated measurements: unknown signals rejected, no garbage
  - NO score synthesis, NO attention interpretation (P4 couples later),
    NO state.json write, NO restart, NO network code
Evidence class: SENSOR_MEASURED — never merged with SELF_REPORT.
"""

from __future__ import annotations

import datetime as _dt
import fcntl
import hashlib
import json
import os
import uuid
from dataclasses import dataclass, field
from typing import Any

from .intake import SUBJECT_ID, parse_observed_at

# --- constants -------------------------------------------------------------

SENSOR_EVENT_TYPE = "sensor_observation_v1"
PROVENANCE = "sensor_measured"  # fixed by this module; not a caller parameter

DEFAULT_SENSOR_LOG = "/var/lib/well/sensor_events.jsonl"
DEFAULT_SENSOR_PROJECTION = "/var/lib/well/human_sensor_state.json"

# Registry (granite v1): measurement -> (unit, lo, hi, max_age_seconds).
# Per-signal max age: a heart-rate reading dies in an hour; nightly sleep
# stays meaningful for a day+. Route-agnostic — any lane maps into these.
REGISTRY: dict[str, tuple[str, float, float, int]] = {
    "sleep_hours": ("hours", 0.0, 24.0, 26 * 3600),
    "heart_rate_bpm": ("bpm", 20.0, 250.0, 1 * 3600),
    "resting_heart_rate_bpm": ("bpm", 20.0, 250.0, 26 * 3600),
    "hrv_ms": ("ms", 0.0, 500.0, 26 * 3600),
    "spo2_pct": ("pct", 50.0, 100.0, 26 * 3600),
    "steps_count": ("steps", 0.0, 200000.0, 26 * 3600),
    "body_temperature_c": ("c", 30.0, 45.0, 8 * 3600),
    "weight_kg": ("kg", 20.0, 300.0, 8 * 24 * 3600),
}

DEDUPE_WINDOW_S = 600


# --- dataclasses -------------------------------------------------------------


@dataclass
class SensorObservation:
    measurement: str
    value: float
    unit: str
    observed_at: str
    source: str
    subject_id: str = SUBJECT_ID
    provenance: str = PROVENANCE
    quality: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "measurement": self.measurement,
            "value": self.value,
            "unit": self.unit,
            "observed_at": self.observed_at,
            "source": self.source,
            "subject_id": self.subject_id,
            "provenance": self.provenance,
            "quality": self.quality,
        }


# --- intake (append-only, idempotent) -------------------------------------------


def _idempotency_key(
    subject: str,
    source: str,
    values: dict[str, float],
    recorded_at: _dt.datetime | None = None,
    bucket_s: int = 300,
) -> str:
    vals = "|".join(f"{k}={values[k]:g}" for k in sorted(values))
    ts = recorded_at or _dt.datetime.now(_dt.timezone.utc)
    bucket = int(ts.timestamp()) // bucket_s
    raw = f"{subject}|{source}|{vals}|bucket={bucket}"
    return hashlib.sha256(raw.encode()).hexdigest()


def load_events(event_log: str = DEFAULT_SENSOR_LOG) -> list[dict[str, Any]]:
    if not os.path.exists(event_log):
        return []
    out: list[dict[str, Any]] = []
    with open(event_log, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue  # corrupted line: skip, never crash
            if ev.get("type") == SENSOR_EVENT_TYPE:
                out.append(ev)
    return out


def find_duplicate(
    event_log: str,
    key: str,
    subject: str,
    source: str,
    values: dict[str, float],
    window_s: int = DEDUPE_WINDOW_S,
) -> dict[str, Any] | None:
    if not os.path.exists(event_log):
        return None
    now = _dt.datetime.now(_dt.timezone.utc)
    with open(event_log, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                prior = json.loads(line)
            except json.JSONDecodeError:
                continue
            if prior.get("idempotency_key") == key:
                return prior
            if prior.get("subject_id") != subject or prior.get("source") != source:
                continue
            prior_vals = {
                o["measurement"]: round(float(o["value"]), 6)
                for o in prior.get("observations", [])
            }
            if (
                prior_vals != {k: round(v, 6) for k, v in values.items()}
                or not prior_vals
            ):
                continue
            try:
                t_prior = parse_observed_at(prior.get("recorded_at_utc"))
            except (ValueError, TypeError):
                continue
            if (now - t_prior).total_seconds() <= window_s:
                return prior
    return None


def ingest_sensor_event(
    measurements: dict[str, float],
    source: str,
    observed_at: str | None = None,
    recorded_at_utc: str | None = None,
    subject_id: str = SUBJECT_ID,
    event_log: str = DEFAULT_SENSOR_LOG,
) -> dict[str, Any]:
    """Validate -> dedupe -> append -> receipt. NO restart, NO state.json,
    NO score. provenance is fixed sensor_measured (not a parameter)."""
    if subject_id != SUBJECT_ID:
        return {
            "status": "rejected",
            "reason": f"unknown_subject:{subject_id}",
            "note": "Subject tidak terikat. Tiada apa-apa disimpan.",
        }
    if not source or not str(source).strip():
        return {
            "status": "rejected",
            "reason": "source_required",
            "note": "Setiap event sensor mesti namakan laluannya (cth health_connect, zepp_api, gadgetbridge_export).",
        }
    if not measurements:
        return {
            "status": "rejected",
            "reason": "empty_measurements",
            "note": "Tiada pengukuran diberi.",
        }
    try:
        vals: dict[str, float] = {}
        for name, raw in measurements.items():
            if name not in REGISTRY:
                raise ValueError(
                    f"unknown_measurement:{name} (registry: {', '.join(sorted(REGISTRY))})"
                )
            v = float(raw)
            unit, lo, hi, _max_age = REGISTRY[name]
            if not (lo <= v <= hi):
                raise ValueError(
                    f"out_of_range:{name}={v:g} (sah {lo:g}-{hi:g} {unit})"
                )
            vals[name] = v
    except ValueError as exc:
        return {
            "status": "rejected",
            "reason": str(exc),
            "evidence_class": "SENSOR_MEASURED",
            "note": "Tiada apa-apa disimpan. Betulkan nilai atau daftar signal dalam REGISTRY.",
        }

    now_iso = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
    obs_iso = observed_at or now_iso
    ref_ts = parse_observed_at(recorded_at_utc) if recorded_at_utc else None
    key = _idempotency_key(subject_id, source, vals, recorded_at=ref_ts)
    dup = find_duplicate(event_log, key, subject_id, source, vals)
    if dup is not None:
        return {
            "status": "duplicate",
            "receipt_id": dup.get("event_id"),
            "source": source,
            "stored_at": dup.get("recorded_at_utc"),
            "note": "Event sensor sama dah tercatat. Tiada entri baru.",
        }

    observations = [
        SensorObservation(
            measurement=m,
            value=v,
            unit=REGISTRY[m][0],
            observed_at=obs_iso,
            source=source,
        ).to_dict()
        for m, v in sorted(vals.items())
    ]
    event = {
        "event_id": str(uuid.uuid4()),
        "idempotency_key": key,
        "type": SENSOR_EVENT_TYPE,
        "schema": SENSOR_EVENT_TYPE,
        "subject_id": subject_id,
        "source": source,
        "recorded_at_utc": recorded_at_utc or now_iso,
        "observations": observations,
        "evidence_class": "SENSOR_MEASURED",
    }
    os.makedirs(os.path.dirname(event_log), exist_ok=True)
    line = json.dumps(event, ensure_ascii=False, sort_keys=True)
    with open(event_log, "a", encoding="utf-8") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            fh.write(line + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    return {
        "status": "accepted",
        "receipt_id": event["event_id"],
        "idempotency_key": key,
        "subject_id": subject_id,
        "source": source,
        "observations": observations,
        "provenance": PROVENANCE,
        "evidence_class": "SENSOR_MEASURED",
        "note": "Disimpan sebagai SENSOR_MEASURED. Tiada skor, tiada inferens.",
    }


# --- projection ----------------------------------------------------------------


def latest_per_signal(events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for ev in events:
        for obs in ev.get("observations", []):
            m = obs.get("measurement")
            if m not in REGISTRY:
                continue
            prev = latest.get(m)
            if prev is None:
                latest[m] = obs
                continue
            try:
                obs_t = parse_observed_at(obs.get("observed_at", ""))
                prev_t = parse_observed_at(prev.get("observed_at", ""))
            except (ValueError, TypeError):
                continue
            if obs_t > prev_t:
                latest[m] = obs
    return latest


def _freshness(observed_at: str, now: _dt.datetime, max_age_s: int) -> str:
    try:
        t = parse_observed_at(observed_at)
    except (ValueError, TypeError):
        return "EXPIRED"
    age = (now - t).total_seconds()
    if age < 0:
        return "EXPIRED"
    if age <= max_age_s * 0.5:
        return "FRESH"
    if age <= max_age_s:
        return "STALE"
    return "EXPIRED"


def build_sensor_projection(
    events: list[dict[str, Any]], now: _dt.datetime | None = None
) -> dict[str, Any]:
    """Signals + freshness ONLY. No interpretation, no score, no attention
    state — coupling is P4 and every source stays separate until then."""
    now = now or _dt.datetime.now(_dt.timezone.utc)
    latest = latest_per_signal(events)
    signals: dict[str, Any] = {}
    n_measured = 0
    for m, (unit, _lo, _hi, max_age) in REGISTRY.items():
        obs = latest.get(m)
        if obs is None:
            continue
        band = _freshness(obs.get("observed_at", ""), now, max_age)
        n_measured += 1
        signals[m] = {
            "value": float(obs["value"]),
            "unit": obs.get("unit") or unit,
            "observed_at": obs.get("observed_at"),
            "source": obs.get("source"),
            "provenance": PROVENANCE,
            "freshness": band,
        }
    return {
        "schema": "human_sensor_state_v1",
        "subject_id": SUBJECT_ID,
        "generated_at_utc": now.isoformat(timespec="seconds"),
        "signals": signals,
        "evidence_summary": {
            "self_reported": 0,
            "system_observed": 0,
            "sensor_measured": n_measured,
        },
        "human_evidence": {
            "class": "SENSOR_MEASURED",
            "has_device_telemetry": n_measured > 0,  # scoped to THIS stream
        },
        "event_count": len(events),
        "note": (
            "Tiada skor, tiada inferens, tiada diagnosis. "
            "P4 couple kemudian — setiap sumber kekal berasingan."
        ),
    }


def refresh_sensor_projection(
    event_log: str = DEFAULT_SENSOR_LOG, path: str = DEFAULT_SENSOR_PROJECTION
) -> dict[str, Any]:
    from .projection import write_projection  # reuse the atomic writer

    proj = build_sensor_projection(load_events(event_log))
    write_projection(proj, path)
    return proj
