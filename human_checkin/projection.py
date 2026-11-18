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
import fcntl
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


UNTOUCHED_STATE_KEYS = (
    "well_score",
    "biometric",
    "signals_meta",
    "metrics",
    "signals",
    "has_verified_telemetry",
    "environment",
)
PRESENCE_TRUTH = "OPERATOR_REPORTED"


def apply_to_state(
    proj: dict[str, Any], state_path: str, note: str | None = None
) -> dict[str, Any]:
    """G1-lite presence merge (F13 2026-11-19): project a FRESH self-report
    onto state.json presence fields so /health and the kernel F6 producer see
    honest presence (OPERATOR_REPORTED, fresh observation clock). Closes the
    EXPIRED hole WITHOUT creating a VERIFIED illusion.

    Allowlist ONLY: truth_status, source_type, evidence_class, confidence,
    reason, timestamp, last_successful_read, last_successful_write, and the
    additive 'human_checkin' namespace. The 13-signal schema, biometric,
    well_score, signals_meta, has_verified_telemetry and environment are
    captured before write and asserted byte-identical after (RuntimeError on
    any diff). No FRESH signal -> no presence assertion, file untouched.
    Never restarts anything."""
    signals = proj.get("signals", {})
    fresh = {
        m: signals[m]
        for m in CHECKIN_FIELDS
        if isinstance(signals.get(m), dict) and signals[m].get("freshness") == FRESH
    }
    now_iso = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
    if not fresh:
        return {
            "applied": False,
            "state_path": state_path,
            "reason": "no_fresh_signal presence not asserted",
        }
    os.makedirs(os.path.dirname(state_path) or ".", exist_ok=True)
    lock_path = state_path + ".lock"
    with open(lock_path, "w", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            created = False
            if os.path.exists(state_path):
                with open(state_path, "r", encoding="utf-8") as fh:
                    state = json.load(fh)
            else:
                created = True
                state = {
                    "schema": "well_state_v2",
                    "environment": "PROD",
                    "well_score": None,
                    "has_verified_telemetry": False,
                }
            untouched = {k: state.get(k) for k in UNTOUCHED_STATE_KEYS}
            latest_obs = None
            for s in fresh.values():
                t = parse_observed_at(s.get("observed_at", ""))
                if latest_obs is None or t > latest_obs:
                    latest_obs = t
            attention = proj.get("attention_readiness", {})
            reason = "human_checkin_v1 SELF_REPORT attention " + str(
                attention.get("state", "UNKNOWN")
            )
            if note:
                reason += " note " + str(note)[:120]
            state["truth_status"] = PRESENCE_TRUTH
            state["source_type"] = PRESENCE_TRUTH
            state["evidence_class"] = "SELF_REPORT"
            state["confidence"] = 0.5
            state["reason"] = reason
            # gate keys on record write time (repo convention, server.py:1147)
            state["timestamp"] = now_iso
            state["last_successful_read"] = (
                latest_obs.isoformat(timespec="seconds") if latest_obs else now_iso
            )
            state["last_successful_write"] = now_iso
            state["human_checkin"] = {
                "schema": "human_checkin_presence_v1",
                "signals": {
                    m: {
                        k: s[k]
                        for k in (
                            "value",
                            "unit",
                            "observed_at",
                            "source",
                            "provenance",
                            "freshness",
                        )
                        if k in s
                    }
                    for m, s in signals.items()
                },
                "attention_state": attention.get("state", "UNKNOWN"),
                "attention_confidence": attention.get("confidence", "NONE"),
                "evidence_class": proj.get("human_evidence", {}).get(
                    "class", "PARTIAL_SELF_REPORT"
                ),
                "projected_at_utc": proj.get("generated_at_utc", now_iso),
            }
            tmp = f"{state_path}.tmp.{os.getpid()}"
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(state, fh, ensure_ascii=False, indent=1, sort_keys=True)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, state_path)
            with open(state_path, "r", encoding="utf-8") as fh:
                reread = json.load(fh)
            for k, v in untouched.items():
                if reread.get(k) != v:
                    raise RuntimeError(f"state merge touched forbidden key {k}")
            return {
                "applied": True,
                "created": created,
                "state_path": state_path,
                "fresh_signals": sorted(fresh),
                "attention_state": attention.get("state", "UNKNOWN"),
                "untouched_verified": True,
            }
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


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
