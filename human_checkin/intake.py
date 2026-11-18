"""WELL::HUMAN_CHECKIN::v1 — schema + intake (P0).

Three-field sovereign presence intake. Append-only, idempotent,
no restart, no score synthesis. Conforms to observation_contract.py
(subject / measurement / unit / observed_at / source / provenance).
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

# --- constants -------------------------------------------------------------

SUBJECT_ID = "arif"
SOURCE = "telegram_checkin"
EVENT_TYPE = "human_checkin_v1"
PROVENANCE = "self_reported"  # matches observation_contract.VALID_PROVENANCE

DEFAULT_EVENT_LOG = "/var/lib/well/human_checkins.jsonl"

# Per-signal freshness max age (seconds). Sleep stays meaningful far longer
# than momentary states. These are per-SIGNAL — never a global timestamp.
FRESHNESS_MAX_AGE_S = {
    "sleep_hours": 20 * 3600,
    "energy": 6 * 3600,
    "load": 6 * 3600,
}

VALID_RANGES = {
    "sleep_hours": (0.0, 24.0),
    "energy": (1.0, 10.0),
    "load": (1.0, 10.0),
}

# Fields accepted in a check-in. Clarity is deliberately ABSENT — it stays
# UNKNOWN until the subject states it, and is never derived from these.
CHECKIN_FIELDS = ("sleep_hours", "energy", "load")

# Duplicate collapse window: same values + same subject + same source within
# this window = one submission (Telegram retries), idempotent no-append.
DEDUPE_WINDOW_S = 600


# --- dataclasses -------------------------------------------------------------


@dataclass
class FieldObservation:
    measurement: str
    value: float
    unit: str
    observed_at: str  # ISO-8601 with offset
    source: str = SOURCE
    provenance: str = PROVENANCE
    quality: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "measurement": self.measurement,
            "value": self.value,
            "unit": self.unit,
            "observed_at": self.observed_at,
            "source": self.source,
            "provenance": self.provenance,
            "quality": self.quality,
        }


@dataclass
class CheckinEvent:
    event_id: str
    idempotency_key: str
    subject_id: str
    source: str
    recorded_at_utc: str
    observations: list[FieldObservation] = field(default_factory=list)
    missing: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "idempotency_key": self.idempotency_key,
            "type": EVENT_TYPE,
            "schema": EVENT_TYPE,
            "subject_id": self.subject_id,
            "source": self.source,
            "recorded_at_utc": self.recorded_at_utc,
            "observations": [o.to_dict() for o in self.observations],
            "missing": self.missing,
        }


# --- helpers ------------------------------------------------------------------


def _now_utc_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def parse_observed_at(raw: str | None) -> _dt.datetime:
    """Parse an ISO timestamp; naive values are read as UTC."""
    if not raw:
        return _dt.datetime.now(_dt.timezone.utc)
    ts = _dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=_dt.timezone.utc)
    return ts


def _idempotency_key(
    subject: str,
    source: str,
    values: dict[str, float],
    recorded_at: _dt.datetime | None = None,
    bucket_s: int = 300,
) -> str:
    """subject + source + values + 5-minute ARRIVAL bucket (event's own
    recorded time, not wall clock — a retry collapses, a later genuine
    check-in with identical values does not)."""
    vals = "|".join(f"{k}={values[k]:g}" for k in CHECKIN_FIELDS if k in values)
    ts = recorded_at or _dt.datetime.now(_dt.timezone.utc)
    bucket = int(ts.timestamp()) // bucket_s
    raw = f"{subject}|{source}|{vals}|bucket={bucket}"
    return hashlib.sha256(raw.encode()).hexdigest()


# --- parsing -------------------------------------------------------------------


def parse_checkin_text(text: str) -> dict[str, float]:
    """Parse '6.5,5,8' (sleep, energy, load). Returns {field: value}.
    Raises ValueError with a human-readable reason on bad input."""
    parts = [p.strip() for p in text.replace(";", ",").split(",") if p.strip()]
    if not parts:
        raise ValueError("empty_input")
    if len(parts) > 3:
        raise ValueError("too_many_fields: maksimum 3 medan (tidur,tenaga,beban)")
    names = CHECKIN_FIELDS[: len(parts)]
    out: dict[str, float] = {}
    for name, raw in zip(names, parts):
        try:
            val = float(raw)
        except ValueError:
            raise ValueError(f"invalid_number:{name}='{raw}'")
        lo, hi = VALID_RANGES[name]
        if not (lo <= val <= hi):
            raise ValueError(f"out_of_range:{name}={val:g} (sah {lo:g}-{hi:g})")
        out[name] = val
    return out


def build_event(
    values: dict[str, float],
    subject_id: str = SUBJECT_ID,
    source: str = SOURCE,
    observed_at: str | None = None,
    recorded_at_utc: str | None = None,
) -> CheckinEvent:
    """Build a typed event from validated values. Missing fields get an
    explicit missing_reason — never zero, never derived."""
    now_iso = observed_at or _dt.datetime.now(_dt.timezone.utc).astimezone().isoformat(
        timespec="seconds"
    )
    # per-field observed_at = the check-in moment, stored per field
    observations: list[FieldObservation] = []
    units = {"sleep_hours": "hours", "energy": "score_1_10", "load": "score_1_10"}
    for name in CHECKIN_FIELDS:
        if name in values:
            observations.append(
                FieldObservation(
                    measurement=name,
                    value=values[name],
                    unit=units[name],
                    observed_at=now_iso,
                    source=source,
                )
            )
    missing = [
        {"measurement": name, "missing_reason": "not_provided"}
        for name in CHECKIN_FIELDS
        if name not in values
    ]
    ref_ts = parse_observed_at(recorded_at_utc) if recorded_at_utc else None
    idem = _idempotency_key(subject_id, source, values, recorded_at=ref_ts)
    return CheckinEvent(
        event_id=str(uuid.uuid4()),
        idempotency_key=idem,
        subject_id=subject_id,
        source=source,
        recorded_at_utc=recorded_at_utc or _now_utc_iso(),
        observations=observations,
        missing=missing,
    )


# --- intake (append-only, idempotent) -------------------------------------------


def find_duplicate(
    event_log: str, event: CheckinEvent, window_s: int = DEDUPE_WINDOW_S
) -> dict[str, Any] | None:
    """Return the prior event dict if an identical submission exists:
    same idempotency_key, OR same subject+source+values inside window_s."""
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
                continue  # corrupted line: skip, never crash intake
            if prior.get("idempotency_key") == event.idempotency_key:
                return prior
            if (
                prior.get("subject_id") != event.subject_id
                or prior.get("source") != event.source
            ):
                continue
            prior_vals = {
                o["measurement"]: round(float(o["value"]), 6)
                for o in prior.get("observations", [])
            }
            new_vals = {o.measurement: round(o.value, 6) for o in event.observations}
            if prior_vals != new_vals or not prior_vals:
                continue
            try:
                t_prior = parse_observed_at(prior.get("recorded_at_utc"))
            except ValueError:
                continue
            if (now - t_prior).total_seconds() <= window_s:
                return prior
    return None


def append_event(event_log: str, event: CheckinEvent) -> None:
    """Atomic append under an exclusive flock; fsync before release."""
    os.makedirs(os.path.dirname(event_log), exist_ok=True)
    line = json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True)
    with open(event_log, "a", encoding="utf-8") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            fh.write(line + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def ingest(
    text_or_values: str | dict[str, float],
    event_log: str = DEFAULT_EVENT_LOG,
    subject_id: str = SUBJECT_ID,
    source: str = SOURCE,
    observed_at: str | None = None,
    recorded_at_utc: str | None = None,
) -> dict[str, Any]:
    """Full intake path: parse → validate → dedupe → append → receipt.
    NEVER restarts any service. NEVER touches state.json.
    recorded_at_utc: override for backfill/tests (dedupe compares arrival time).
    Returns a receipt dict (accepted | duplicate | rejected)."""
    if subject_id != SUBJECT_ID:
        return {
            "status": "rejected",
            "reason": f"unknown_subject:{subject_id} (subject binding: {SUBJECT_ID})",
            "evidence_class": "SELF_REPORT",
            "note": "Subject tidak terikat. Tiada apa-apa disimpan.",
        }
    try:
        if isinstance(text_or_values, str):
            values = parse_checkin_text(text_or_values)
        else:
            values = {k: float(v) for k, v in text_or_values.items()}
            for name, val in values.items():
                if name not in VALID_RANGES:
                    raise ValueError(f"unknown_field:{name}")
                lo, hi = VALID_RANGES[name]
                if not (lo <= val <= hi):
                    raise ValueError(f"out_of_range:{name}={val:g} (sah {lo:g}-{hi:g})")
    except ValueError as exc:
        return {
            "status": "rejected",
            "reason": str(exc),
            "evidence_class": "SELF_REPORT",
            "note": "Tiada apa-apa disimpan. Betulkan format: tidur,tenaga,beban (cth 6.5,5,8).",
        }

    event = build_event(
        values,
        subject_id=subject_id,
        source=source,
        observed_at=observed_at,
        recorded_at_utc=recorded_at_utc,
    )
    dup = find_duplicate(event_log, event)
    if dup is not None:
        return {
            "status": "duplicate",
            "receipt_id": dup.get("event_id"),
            "subject_id": event.subject_id,
            "evidence_class": "SELF_REPORT",
            "stored_at": dup.get("recorded_at_utc"),
            "note": "Check-in sama dah tercatat. Tiada entri baru.",
        }

    append_event(event_log, event)
    return {
        "status": "accepted",
        "receipt_id": event.event_id,
        "idempotency_key": event.idempotency_key,
        "subject_id": event.subject_id,
        "source": event.source,
        "recorded_at_utc": event.recorded_at_utc,
        "observations": [o.to_dict() for o in event.observations],
        "missing": event.missing,
        "evidence_class": "SELF_REPORT",
        "has_verified_telemetry": False,  # invariant: check-in never flips this
        "note": "Disimpan sebagai SELF_REPORT. Tiada diagnosis, tiada wearable claim.",
    }
