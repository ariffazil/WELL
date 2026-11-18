"""WELL::CRAVING::v1 — one-word craving events (zero-input intake).

Lesson from the failed 3-field check-in (F13, 2026-11-19): an intake that
demands typed output during a craving window will not be used. So this lane
takes ONE WORD from the subject and does everything else itself.

Protocol (in-lane):
  Subject sends "20"  -> HERMES starts a 20-minute hold: deploys ONE
                         pre-prepared absorbing thing, starts a countdown,
                         stays present. Well logs a craving_event.
  Subject sends "ok"  -> craving survived. Well logs the survive mark.
  No numbers. No fields. The agent spends; the human only sends.

Events are append-only, provenance self_reported, provenance class
SELF_REPORT — a craving event never flips has_verified_telemetry.
Pattern use: time-of-day clustering feeds the reality observer, nothing else.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
from typing import Any

from .intake import SUBJECT_ID, parse_observed_at  # noqa: F401 (parse reuse)

CRAVING_LOG = "/var/lib/well/human_cravings.jsonl"
EVENT_TYPE = "craving_event_v1"
SOURCE = "telegram_oneword"

CODE_WORD = "20"      # craving now
SURVIVE_WORD = "ok"   # survived the hold

HOUR_BANDS = (
    ((0, 5), "late_night"),
    ((5, 11), "morning"),
    ((11, 15), "midday"),
    ((15, 19), "afternoon"),
    ((19, 24), "evening"),
)


def classify_word(text: str) -> str | None:
    t = text.strip().lower()
    if t == CODE_WORD:
        return "craving"
    if t == SURVIVE_WORD:
        return "survived"
    return None


def log_event(kind: str, text: str,
              log_path: str = CRAVING_LOG,
              subject_id: str = SUBJECT_ID,
              now: _dt.datetime | None = None) -> dict[str, Any]:
    """Append one one-word event. Atomic, append-only, no restart, no score."""
    now = now or _dt.datetime.now(_dt.timezone(_dt.timedelta(hours=8)))
    local_hour = now.hour
    band = "evening"
    for (lo, hi), b in HOUR_BANDS:
        if lo <= local_hour < hi:
            band = b
            break
    event = {
        "type": EVENT_TYPE,
        "subject_id": subject_id,
        "source": SOURCE,
        "provenance": "self_reported",
        "kind": kind,
        "local_hour": local_hour,
        "hour_band": band,
        "recorded_at_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "word": text.strip().lower(),
    }
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as fh:
        import fcntl
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            fh.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
    return event


def handle_word(text: str, log_path: str = CRAVING_LOG) -> dict[str, Any] | None:
    """Returns an action for HERMES to execute, or None if not a craving word.
    HERMES owns the hold behaviour; this only records and tells it what to do."""
    kind = classify_word(text)
    if kind is None:
        return None
    ev = log_event(kind, text, log_path=log_path)
    if kind == "craving":
        return {
            "action": "start_hold",
            "minutes": 20,
            "event": ev,
            "receipt": "Direkod. Tahan 20 minit bermula sekarang — aku kejar sesuatu untuk kau. Tiada soalan, tiada nombor.",
        }
    return {
        "action": "mark_survived",
        "event": ev,
        "receipt": "Survive direkod. Itu satu pusingan yang kau menang.",
    }


def pattern(log_path: str = CRAVING_LOG) -> dict[str, Any]:
    """Read-only pattern: counts by hour band. Pattern evidence only —
    never rendered as a diagnosis or a score."""
    if not os.path.exists(log_path):
        return {"events": 0, "by_band": {}, "survived": 0, "cravings": 0}
    cravings = survived = 0
    by_band: dict[str, int] = {}
    with open(log_path, "r", encoding="utf-8") as fh:
        for line in fh:
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("type") != EVENT_TYPE:
                continue
            if ev.get("kind") == "craving":
                cravings += 1
                b = ev.get("hour_band", "?")
                by_band[b] = by_band.get(b, 0) + 1
            elif ev.get("kind") == "survived":
                survived += 1
    return {"events": cravings + survived, "cravings": cravings,
            "survived": survived, "by_band": by_band}
