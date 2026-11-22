"""WELL receipt streams — the honest age of HUMAN REALITY in the substrate.

Why this module exists (2026-11-23, F13 GO A+B — WELL side):

The F6 MARUAH instrument derived `consequence_flow` from the age of the newest
structured receipt in ``/var/log/well/intake.log``. That file is the
``well_ingest`` CRON'S STDOUT, and the cron writes a line every 30 minutes
whether or not anything arrived::

    {"tool":"well_ingest","ts":"...","status":"NO_INTAKE","state_written":false,
     "note":"intake queue empty - heartbeat; live state timestamp NOT advanced"}

Measured 2026-11-23 on the live box: **3206 NO_INTAKE lines and ZERO real
receipts in the entire log history.** So the flow leg was covered by CRON
LIVENESS, never by reality entering the substrate — and a self-report
check-in (the human lane) never touched that log at all.

This module computes the honest age:

* **heartbeat lines are LIVENESS, not MEASUREMENT** — excluded (D1, the same
  rule ``well_auto_keepalive.py`` already respects: a heartbeat may write its
  own liveness fields and nothing else);
* the **self-report lane** (``human_checkins.jsonl``) IS a real receipt stream
  — the human's own reported reality entering the substrate;
* the **SYSTEM_OBSERVED lane** (``human_reality.jsonl``) is EXCLUDED on
  purpose: a machine-observed signal must not refresh the floor (F13 MARUAH
  canon 2026-10-23 — the machine never self-certifies the human in order to
  unlock itself). That is decision C, not this module;
* the **SENSOR lane** is excluded until a device actually lands.

It lives in its own module so the production server can serve the EVIDENCE
without referencing the F6 instrument module — the A4 scar guard
(``test_cutover_guard_production_server_must_not_reference``) forbids the
production monolith from gaining a reference to ``well_measure_floor_f6``,
because that would create a dual surface with byte-identity drift. One
computation, two consumers, no dual surface.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence

# ── receipt streams ─────────────────────────────────────────────────────────

INTAKE_LOG_DEFAULT = "/var/log/well/intake.log"
SELF_REPORT_LOG_DEFAULT = "/var/lib/well/human_checkins.jsonl"

#: The Freshness Law ceiling — >24h without a real receipt = STALE_MIRROR.
FLOW_BAND_SECONDS = 24 * 3600

#: Statuses the intake cron writes when NOTHING arrived. Liveness, not receipt.
HEARTBEAT_STATUSES = frozenset({"NO_INTAKE"})

#: The dignity surface is the canonical Ω-WELL-12 guard in the production
#: server. The check is static and structural — no HTTP, no runtime probe.
DIGNITY_GUARD_SYMBOL = "well_guard_dignity"
DIGNITY_GUARD_LABEL = "Ω-WELL-12 well_guard_dignity (canonical server.py)"


def _receipt_ts(rec: dict[str, Any]) -> Optional[datetime]:
    """Newest observation timestamp carried by one receipt record.

    Handles the three shapes the lanes actually write:
      * intake log / cron stdout  -> {"ts": ...}
      * self-report event          -> {"recorded_at_utc": ..., "observations": [...]}
      * anything else              -> no timestamp (honest None)
    """
    raw = rec.get("ts") or rec.get("recorded_at_utc")
    candidates: list[datetime] = []
    if raw:
        try:
            dt = datetime.fromisoformat(str(raw))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            candidates.append(dt)
        except ValueError:
            pass
    obs = rec.get("observations")
    if isinstance(obs, list):
        for o in obs:
            if isinstance(o, dict) and o.get("observed_at"):
                try:
                    dt = datetime.fromisoformat(str(o["observed_at"]))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    candidates.append(dt)
                except ValueError:
                    continue
    if not candidates:
        return None
    return max(candidates)


def _is_real_receipt(rec: dict[str, Any]) -> bool:
    """Does this record carry human reality into the substrate?

    A heartbeat (status NO_INTAKE) proves the CRON is alive. It does not prove
    the human was measured. Counting it would make the flow leg permanently
    covered with zero human input — a painted number, which this organ's
    instrument docstring forbids outright.
    """
    status = str(rec.get("status") or "").upper()
    if status in HEARTBEAT_STATUSES:
        return False
    if not status and rec.get("state_written") is False:
        # heartbeat shape without the status key — same exclusion
        return False
    return True


def newest_real_receipt_age_s(
    log_paths: Optional[Sequence[str]] = None,
    now: Optional[float] = None,
) -> Optional[float]:
    """Age (seconds) of the newest REAL receipt across the given streams.

    Returns None when no stream carries a real receipt (honest None — never a
    fabricated age).
    """
    now = now if now is not None else time.time()
    newest: Optional[datetime] = None
    for path in log_paths or ():
        p = Path(path)
        try:
            lines = p.read_text(errors="replace").strip().splitlines()
        except Exception:
            continue
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            if not isinstance(rec, dict) or not _is_real_receipt(rec):
                continue
            dt = _receipt_ts(rec)
            if dt is None:
                continue
            if newest is None or dt > newest:
                newest = dt
            break  # newest usable record in this stream
    if newest is None:
        return None
    return max(0.0, now - newest.timestamp())


def default_receipt_logs(
    intake_log: Optional[str] = None,
    self_report_log: Optional[str] = None,
) -> list[str]:
    """The receipt streams the flow leg reads by default.

    The SYSTEM_OBSERVED and SENSOR lanes are deliberately absent — see the
    module docstring.
    """
    return [
        intake_log or INTAKE_LOG_DEFAULT,
        self_report_log or SELF_REPORT_LOG_DEFAULT,
    ]


def consequence_flow_view(
    intake_log: Optional[str] = None,
    self_report_log: Optional[str] = None,
    now: Optional[float] = None,
    band_seconds: int = FLOW_BAND_SECONDS,
) -> dict[str, Any]:
    """The consequence_flow leg, as the served /health surface should carry it.

    Evidence only — no verdict. The kernel recomputes covered/factor from the
    age it is given; it never trusts a verdict it cannot recompute.
    """
    logs = default_receipt_logs(intake_log, self_report_log)
    age = newest_real_receipt_age_s(logs, now=now)
    covered = age is not None and age <= band_seconds
    factor = max(0.0, 1.0 - (age / band_seconds)) if covered else 0.0
    return {
        "covered": covered,
        "last_receipt_age_s": None if age is None else round(age, 1),
        "band_seconds": band_seconds,
        "flow_factor": round(factor, 6),
        "streams": logs,
        "excluded_streams": {
            "system_observed": "/var/lib/well/human_reality.jsonl",
            "sensor": "/var/lib/well/sensor_events.jsonl",
        },
        "note": (
            "Age of the newest REAL receipt (human reality entering the substrate). "
            "Cron heartbeats (NO_INTAKE) are liveness, not receipt, and are excluded."
        ),
    }


def dignity_surface_view(server_py: Optional[str] = None) -> dict[str, Any]:
    """The dignity_surface leg: is the canonical Ω-WELL-12 guard present?

    Static structural check, no HTTP — the same check the F6 instrument uses,
    so both readings agree.
    """
    if server_py:
        p = Path(server_py)
    else:
        p = Path(__file__).resolve().parents[1] / "server.py"
    try:
        present = DIGNITY_GUARD_SYMBOL in p.read_text(errors="replace")
    except Exception:
        present = False
    return {
        "covered": bool(present),
        "guard": DIGNITY_GUARD_LABEL,
        "source": str(p),
        "note": "Static presence check of the canonical dignity guard. No verdict.",
    }
