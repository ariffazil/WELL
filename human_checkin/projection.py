"""WELL::HUMAN_CHECKIN::v1 — projection (P1).

Reads the append-only event log and projects per-signal human state.
Rules (F13 2026-11-19):
  - Per-signal freshness: one new observation NEVER refreshes another.
  - Missing sleep is never replaced with zero.
  - Attention readiness is a BOUNDED vector interpretation
    (AVAILABLE/CONSTRAINED/SATURATED/RECOVERY/UNKNOWN), confidence PARTIAL
    at best, provenance SELF_REPORT — never a diagnosis, never a score.
  - Projection NEVER touches state.json's 13-signal schema and NEVER
    sets has_verified_telemetry=true.
  - Rebuild is always possible from the event log alone.
Atomic write: tmp file + os.replace in the same directory.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
from typing import Any

from .intake import (
    CHECKIN_FIELDS,
    DEFAULT_EVENT_LOG,
    EVENT_TYPE,
    FRESHNESS_MAX_AGE_S,
    SUBJECT_ID,
    parse_observed_at,
)

DEFAULT_PROJECTION = "/var/lib/well/human_state.json"

FRESH = "FRESH"
STALE = "STALE"
EXPIRED = "EXPIRED"
STALE_AFTER_S = 0.5  # fraction of max age after which a signal reads STALE


def load_events(event_log: str = DEFAULT_EVENT_LOG) -> list[dict[str, Any]]:
    """Read all valid check-in events. Corrupted lines are skipped, never fatal."""
    if not os.path.exists(event_log):
        return []
    out = []
    with open(event_log, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("type") == EVENT_TYPE:
                out.append(ev)
    return out


def _freshness(observed_at: str, now: _dt.datetime, max_age_s: int) -> str:
    try:
        t = parse_observed_at(observed_at)
    except (ValueError, TypeError):
        return EXPIRED
    age = (now - t).total_seconds()
    if age < 0:
        return EXPIRED  # future-dated: treat as unusable, not fresh
    if age <= max_age_s * STALE_AFTER_S:
        return FRESH
    if age <= max_age_s:
        return STALE
    return EXPIRED


def latest_per_signal(events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Latest valid observation per measurement. Absence = explicit missing,
    never zero. Per-signal freshness: each carries its own observed_at."""
    latest: dict[str, dict[str, Any]] = {}
    for ev in events:
        for obs in ev.get("observations", []):
            m = obs.get("measurement")
            if m not in CHECKIN_FIELDS:
                continue
            prev = latest.get(m)
            if prev is None:
                latest[m] = obs
                continue
            # D1 fix (555-ASI 2026-11-19): compare by parsed instant, never by
            # string — ISO offsets sort lexicographically, not chronologically.
            try:
                obs_t = parse_observed_at(obs.get("observed_at", ""))
                prev_t = parse_observed_at(prev.get("observed_at", ""))
            except (ValueError, TypeError):
                continue  # unparseable timestamp = unusable observation
            if obs_t > prev_t:
                latest[m] = obs
    return latest


def interpret_attention(
    latest: dict[str, dict[str, Any]], now: _dt.datetime
) -> dict[str, Any]:
    """Bounded AttentionEnvelope interpretation. Rule-based, provenance-tagged.
    UNKNOWN is a valid first-class state, not a failure."""
    fresh: dict[str, float] = {}
    reasons: list[str] = []
    for m in CHECKIN_FIELDS:
        obs = latest.get(m)
        if obs is None:
            reasons.append(f"{m}:missing")
            continue
        band = _freshness(obs["observed_at"], now, FRESHNESS_MAX_AGE_S[m])
        if band == FRESH:
            fresh[m] = float(obs["value"])
        else:
            reasons.append(f"{m}:{band.lower()}")

    if not fresh:
        return {
            "state": "UNKNOWN",
            "confidence": "NONE",
            "reasons": reasons,
            "note": "Tiada isyarat segar. UNKNOWN sah — jangan infer.",
        }

    if "energy" in fresh and fresh["energy"] <= 2:
        state = "SATURATED"
        reasons.append("self_reported_energy<=2")
    elif "load" in fresh and fresh["load"] >= 8:
        state = "SATURATED"
        reasons.append("high_self_reported_load")
    elif (
        "energy" in fresh
        and fresh["energy"] <= 3
        and "load" in fresh
        and fresh["load"] <= 4
    ):
        # D2 fix (555-ASI 2026-11-19): RECOVERY needs load known-and-low.
        # No phantom defaults — missing load never enters decision logic.
        state = "RECOVERY"
        reasons.append("low_energy_low_load")
    elif ("load" in fresh and fresh["load"] >= 6) or (
        "energy" in fresh and fresh["energy"] <= 5
    ):
        state = "CONSTRAINED"
        if "load" in fresh and fresh["load"] >= 6:
            reasons.append("high_self_reported_load")
        if "energy" in fresh and fresh["energy"] <= 5:
            reasons.append("low_self_reported_energy")
    elif "sleep_hours" in fresh and fresh["sleep_hours"] < 6.5:
        state = "CONSTRAINED"
        reasons.append("short_sleep")
    else:
        state = "AVAILABLE"
        reasons.append("no_constraining_signal")

    return {
        "state": state,
        "confidence": "PARTIAL",
        "reasons": reasons,
        "note": "Interpretasi bounded daripada SELF_REPORT sahaja. "
        "Bukan diagnosis, bukan skor manusia. Arif kekal penentu.",
    }


def build_projection(
    events: list[dict[str, Any]], now: _dt.datetime | None = None
) -> dict[str, Any]:
    """Full projection: human_state + attention envelope + evidence summary."""
    now = now or _dt.datetime.now(_dt.timezone.utc)
    latest = latest_per_signal(events)

    # explicit missing_reasons carried by the events themselves
    missing_reasons: dict[str, str] = {}
    for ev in events:
        for miss in ev.get("missing", []):
            m = miss.get("measurement")
            if m in CHECKIN_FIELDS and m not in latest:
                missing_reasons[m] = miss.get("missing_reason", "not_provided")

    signals: dict[str, Any] = {}
    counts: dict[str, int] = {"FRESH": 0, "STALE": 0, "EXPIRED": 0, "MISSING": 0}
    for m in CHECKIN_FIELDS:
        obs = latest.get(m)
        if obs is None:
            counts["MISSING"] += 1
            signals[m] = {
                "freshness": "MISSING",
                "missing_reason": missing_reasons.get(m, "no_observation_yet"),
                "provenance": "self_reported",
            }
            continue
        band = _freshness(obs["observed_at"], now, FRESHNESS_MAX_AGE_S[m])
        counts[band] = counts.get(band, 0) + 1
        signals[m] = {
            "value": float(obs["value"]),
            "unit": obs.get("unit"),
            "observed_at": obs.get("observed_at"),
            "source": obs.get("source"),
            "provenance": "self_reported",
            "freshness": band,
        }

    attention = interpret_attention(latest, now)
    return {
        "schema": "human_state_v1",
        "subject_id": SUBJECT_ID,
        "generated_at_utc": now.isoformat(timespec="seconds"),
        "signals": signals,
        "attention_readiness": attention,
        "evidence_summary": {
            "self_reported": sum(
                1
                for s in signals.values()
                if s.get("provenance") == "self_reported"
                and s.get("freshness") != "MISSING"
            ),
            "system_observed": 0,
            "sensor_measured": 0,
        },
        "human_evidence": {
            "class": "PARTIAL_SELF_REPORT",
            "has_verified_telemetry": False,  # invariant: never flipped by check-in
        },
        "event_count": len(events),
        "freshness_counts": counts,
    }


def write_projection(projection: dict[str, Any], path: str = DEFAULT_PROJECTION) -> str:
    """Atomic write: tmp in same dir + os.replace."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.tmp.{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(projection, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)
    return path


def refresh(
    event_log: str = DEFAULT_EVENT_LOG, path: str = DEFAULT_PROJECTION
) -> dict[str, Any]:
    """Rebuild projection from the event log and write it atomically."""
    proj = build_projection(load_events(event_log))
    write_projection(proj, path)
    return proj


def project(proj: dict[str, Any]) -> str:
    """Compact one-line summary for Telegram receipts (BM)."""
    a = proj["attention_readiness"]
    sig = proj["signals"]
    parts = []
    for m, label in (("sleep_hours", "Tidur"), ("energy", "Tenaga"), ("load", "Beban")):
        s = sig.get(m, {})
        if s.get("freshness") == "MISSING":
            parts.append(f"{label}: —")
        else:
            val = s["value"]
            parts.append(
                f"{label}: {val:g}{'j' if m == 'sleep_hours' else '/10'} [{s['freshness']}]"
            )
    return (
        "Disimpan sebagai SELF_REPORT.\n"
        + "\n".join(parts)
        + f"\nAttention readiness: {a['state']} ({a['confidence']})"
        + "\nTiada diagnosis. Tiada wearable claim."
    )
