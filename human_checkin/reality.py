"""WELL::HUMAN_REALITY::v1 — passive session-reality observer (P3).

SYSTEM_OBSERVED, metadata-only. F13 directive 2026-11-19 ("focus on the
reality signals of the session") = explicit consent from the subject himself,
scoped: metadata only, local processing, 30-day retention, revocation stops
ingestion. Consent-default OFF — every collection call FAILS CLOSED without
an active consent receipt.

Captured (and only this): event timestamps, counts, active spans, local hour
bands, context switches (distinct sessions), per local day.
NEVER captured: message content, sentiment, tone, inferred emotion,
typing content, relationship analysis.

Allowed statements: "continuous activity in a late-night window",
"session span long vs available baseline".
Forbidden statements: "Arif is tired / anxious / burning out / needs sleep".

Observe-only for v1: written to its OWN event stream, never mixed into the
self-report attention envelope, never rendered as fatigue or burnout claims.
"""

from __future__ import annotations

import datetime as _dt
import fcntl
import json
import os
import sqlite3
from typing import Any

from .intake import SUBJECT_ID

DB_PATH = "/root/.hermes/state.db"
CONSENT_PATH = "/var/lib/well/human_consent.json"
REALITY_LOG = "/var/lib/well/human_reality.jsonl"
EVENT_TYPE = "human_reality_v1"
SOURCE = "hermes_state_db"

LOCAL_TZ = _dt.timezone(_dt.timedelta(hours=8))  # Asia/Kuala_Lumpur
RETENTION_DAYS = 30
ARIF_DM_CHAT_ID = "267378578"

HOUR_BANDS = (
    ((0, 5), "late_night"),
    ((5, 11), "morning"),
    ((11, 15), "midday"),
    ((15, 19), "afternoon"),
    ((19, 24), "evening"),
)


# --- consent (fail-closed) ----------------------------------------------------


def grant_consent(consent_path: str = CONSENT_PATH,
                  directive: str = "",
                  granted_by: str = "F13 subject in-lane") -> dict[str, Any]:
    """Record an explicit consent receipt. Metadata-only scope, revocable."""
    receipt = {
        "schema": "human_reality_consent_v1",
        "subject_id": SUBJECT_ID,
        "active": True,
        "scope": "metadata_only",
        "fields": [
            "event_timestamps", "event_counts", "active_span_minutes",
            "local_hour_band", "context_switches",
        ],
        "excluded": [
            "message_content", "sentiment", "tone", "inferred_emotion",
            "typing_content", "relationship_analysis",
        ],
        "retention_days": RETENTION_DAYS,
        "processing": "local_only",
        "directive": directive,
        "granted_by": granted_by,
        "granted_at_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "revocable": True,
    }
    os.makedirs(os.path.dirname(consent_path), exist_ok=True)
    tmp = f"{consent_path}.tmp.{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(receipt, fh, ensure_ascii=False, indent=1)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, consent_path)
    return receipt


def revoke_consent(consent_path: str = CONSENT_PATH) -> None:
    """Revocation stops all NEW ingestion. Retained events age out on schedule."""
    if os.path.exists(consent_path):
        with open(consent_path, "r", encoding="utf-8") as fh:
            receipt = json.load(fh)
        receipt["active"] = False
        receipt["revoked_at_utc"] = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
        tmp = f"{consent_path}.tmp.{os.getpid()}"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(receipt, fh, ensure_ascii=False, indent=1)
        os.replace(tmp, consent_path)


def consent_active(consent_path: str = CONSENT_PATH) -> bool:
    if not os.path.exists(consent_path):
        return False
    try:
        with open(consent_path, "r", encoding="utf-8") as fh:
            return bool(json.load(fh).get("active"))
    except (json.JSONDecodeError, OSError):
        return False  # unreadable consent = no consent


# --- observation ----------------------------------------------------------------


def local_hour_band(dt: _dt.datetime) -> str:
    h = dt.hour
    for (lo, hi), band in HOUR_BANDS:
        if lo <= h < hi:
            return band
    return "evening"


def collect_day(day: _dt.datetime | None = None,
                consent_path: str = CONSENT_PATH,
                db_path: str = DB_PATH,
                chat_id: str = ARIF_DM_CHAT_ID,
                subject_id: str = SUBJECT_ID) -> dict[str, Any]:
    """Collect ONE local day of metadata for the subject's DM lane.
    Metadata only — the SQL selects timestamps, never message bodies.
    Refuses without active consent (fail-closed). Idempotent per day."""
    if not consent_active(consent_path):
        return {
            "status": "refused",
            "reason": "consent_off",
            "note": "Tiada consent aktif — tiada kutipan.",
        }

    day = day or _dt.datetime.now(LOCAL_TZ)
    day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + _dt.timedelta(days=1)
    start_ts, end_ts = day_start.timestamp(), day_end.timestamp()

    if not os.path.exists(db_path):
        rows: list = []  # absent source = honest zero, never a crash
    else:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        try:
            rows = conn.execute(
                "SELECT m.timestamp, m.session_id FROM messages m "
                "JOIN sessions s ON s.id = m.session_id "
                "WHERE s.chat_id = ? AND m.timestamp >= ? AND m.timestamp < ? "
                "ORDER BY m.timestamp",
                (chat_id, start_ts, end_ts),
            ).fetchall()
        finally:
            conn.close()

    event = {
        "type": EVENT_TYPE,
        "schema": EVENT_TYPE,
        "subject_id": subject_id,
        "source": SOURCE,
        "provenance": "system_observed",
        "local_day": day_start.strftime("%Y-%m-%d"),
        "tz_offset_hours": 8,
        "metadata": {
            "event_count": len(rows),
            "first_event_at": _dt.datetime.fromtimestamp(rows[0][0], LOCAL_TZ).isoformat(timespec="seconds") if rows else None,
            "last_event_at": _dt.datetime.fromtimestamp(rows[-1][0], LOCAL_TZ).isoformat(timespec="seconds") if rows else None,
            "active_span_minutes": round((rows[-1][0] - rows[0][0]) / 60.0, 1) if len(rows) > 1 else 0.0,
            "local_hour_band": local_hour_band(_dt.datetime.fromtimestamp(rows[0][0], LOCAL_TZ)) if rows else None,
            "context_switches": len({r[1] for r in rows}),
        },
        "recorded_at_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
    }
    return event


def append_observation(event: dict[str, Any], log_path: str = REALITY_LOG) -> dict[str, Any]:
    """Idempotent per (subject, source, local_day). Atomic flock append."""
    if not os.path.exists(log_path):
        prior = None
    else:
        prior = None
        with open(log_path, "r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if (ev.get("subject_id") == event["subject_id"]
                        and ev.get("source") == event["source"]
                        and ev.get("local_day") == event["local_day"]):
                    prior = ev
                    break
    if prior is not None:
        return {"status": "duplicate", "local_day": event["local_day"],
                "note": "Metadata hari ni dah tercatat."}

    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            fh.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    return {"status": "accepted", "local_day": event["local_day"]}


def prune_expired(log_path: str = REALITY_LOG,
                  now: _dt.datetime | None = None) -> int:
    """Retention: drop events older than RETENTION_DAYS from the log."""
    if not os.path.exists(log_path):
        return 0
    now = now or _dt.datetime.now(_dt.timezone.utc)
    cutoff = now - _dt.timedelta(days=RETENTION_DAYS)
    kept: list[str] = []
    dropped = 0
    with open(log_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
                t = _dt.datetime.fromisoformat(ev["recorded_at_utc"].replace("Z", "+00:00"))
                if t.tzinfo is None:
                    t = t.replace(tzinfo=_dt.timezone.utc)
            except (json.JSONDecodeError, KeyError, ValueError):
                kept.append(line)  # unreadable: keep, never destroy evidence blindly
                continue
            if t >= cutoff:
                kept.append(line)
            else:
                dropped += 1
    tmp = f"{log_path}.tmp.{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write("\n".join(kept) + ("\n" if kept else ""))
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, log_path)
    return dropped


def observe(log_path: str = REALITY_LOG, **kwargs: Any) -> dict[str, Any]:
    """collect today + append + prune. Returns the day's metadata for reporting."""
    event = collect_day(**kwargs)
    if event.get("status") == "refused":
        return event
    stored = append_observation(event, log_path)
    pruned = prune_expired(log_path)
    return {**stored, "metadata": event["metadata"], "pruned_expired_events": pruned}


def allowed_summary(metadata: dict[str, Any]) -> str:
    """Honest, bounded wording. Metadata observations ONLY — never fatigue."""
    if metadata.get("event_count", 0) == 0:
        return "Tiada aktiviti sesi direkod hari ini (metadata)."
    lines = [f"Acara sesi: {metadata['event_count']} | rentakan aktif: {metadata['active_span_minutes']} min"]
    first, last = metadata.get("first_event_at"), metadata.get("last_event_at")
    if first and last:
        try:
            f = _dt.datetime.fromisoformat(first).strftime("%H:%M")
            l = _dt.datetime.fromisoformat(last).strftime("%H:%M")
            lines.append(f"Window: {f} → {l} (band {metadata['local_hour_band']})")
        except ValueError:
            pass
    lines.append(f"Tukar konteks (sesi berbeza): {metadata.get('context_switches', 0)}")
    span = metadata.get("active_span_minutes", 0)
    if metadata.get("local_hour_band") == "late_night" and span >= 60:
        lines.append("Aktiviti berterusan dalam window lewat malam.")
    elif span >= 180:
        lines.append("Sesi ini panjang berbanding baseline tersedia.")
    lines.append("Provenance: SYSTEM_OBSERVED, metadata sahaja. Bukan penilaian keadaan manusia.")
    return "\n".join(lines)
