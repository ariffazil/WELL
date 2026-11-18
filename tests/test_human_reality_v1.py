"""Tests — WELL::HUMAN_REALITY::v1 (P3 passive observer).

Privacy, fail-closed consent, metadata-only, idempotency, retention.
All fixtures use tmp paths; the real consent file and reality log are
never touched by tests.
"""

from __future__ import annotations

import datetime as _dt
import json
import pathlib
import sys

sys.path.insert(0, "/root/WELL")

from human_checkin import reality as R

UTC = _dt.timezone.utc
LOCAL = R.LOCAL_TZ


def _paths(tmp: pathlib.Path):
    return str(tmp / "consent.json"), str(tmp / "reality.jsonl")


# --- consent fail-closed -------------------------------------------------------


def test_no_consent_means_refused(tmp_path):
    cp, lp = _paths(tmp_path)
    r = R.collect_day(consent_path=cp)
    assert r["status"] == "refused"
    assert r["reason"] == "consent_off"


def test_unreadable_consent_means_no_consent(tmp_path):
    cp, _ = _paths(tmp_path)
    cp_file = pathlib.Path(cp)
    cp_file.write_text("{broken", encoding="utf-8")
    assert R.consent_active(cp) is False


def test_revocation_stops_ingestion(tmp_path):
    cp, lp = _paths(tmp_path)
    R.grant_consent(consent_path=cp, directive="test")
    assert R.consent_active(cp)
    R.revoke_consent(cp)
    assert R.consent_active(cp) is False
    r = R.collect_day(consent_path=cp)
    assert r["status"] == "refused"


def test_consent_receipt_scope_is_metadata_only(tmp_path):
    cp, _ = _paths(tmp_path)
    rc = R.grant_consent(consent_path=cp, directive="test directive")
    assert rc["scope"] == "metadata_only"
    assert "message_content" in rc["excluded"]
    assert rc["processing"] == "local_only"
    assert rc["revocable"] is True


# --- metadata-only invariant -----------------------------------------------------


def test_event_carries_no_content_fields(tmp_path):
    cp, lp = _paths(tmp_path)
    R.grant_consent(consent_path=cp, directive="test")
    ev = R.collect_day(consent_path=cp, db_path=str(tmp_path / "absent.db"))
    dumped = json.dumps(ev)
    import re
    for forbidden in ("content", "text", "body", "sentiment", "tone", "emotion"):
        assert not re.search(rf"\b{forbidden}", dumped), forbidden
    assert ev["provenance"] == "system_observed"


def test_empty_day_is_zero_not_fabricated(tmp_path):
    cp, lp = _paths(tmp_path)
    R.grant_consent(consent_path=cp, directive="test")
    ev = R.collect_day(day=_dt.datetime(2026, 1, 1, 12, tzinfo=LOCAL),
                       consent_path=cp, db_path=str(tmp_path / "absent.db"))
    m = ev["metadata"]
    assert m["event_count"] == 0
    assert m["first_event_at"] is None
    assert m["local_hour_band"] is None


# --- hour bands ----------------------------------------------------------------


def test_hour_bands():
    assert R.local_hour_band(_dt.datetime(2026, 11, 19, 2, tzinfo=LOCAL)) == "late_night"
    assert R.local_hour_band(_dt.datetime(2026, 11, 19, 8, tzinfo=LOCAL)) == "morning"
    assert R.local_hour_band(_dt.datetime(2026, 11, 19, 13, tzinfo=LOCAL)) == "midday"
    assert R.local_hour_band(_dt.datetime(2026, 11, 19, 17, tzinfo=LOCAL)) == "afternoon"
    assert R.local_hour_band(_dt.datetime(2026, 11, 19, 22, tzinfo=LOCAL)) == "evening"


# --- idempotency + retention ------------------------------------------------------


def test_append_idempotent_per_day(tmp_path):
    cp, lp = _paths(tmp_path)
    R.grant_consent(consent_path=cp, directive="test")
    ev = R.collect_day(day=_dt.datetime(2026, 1, 1, 12, tzinfo=LOCAL),
                       consent_path=cp, db_path=str(tmp_path / "x.db"))
    r1 = R.append_observation(ev, lp)
    r2 = R.append_observation(ev, lp)
    assert r1["status"] == "accepted"
    assert r2["status"] == "duplicate"
    assert len(pathlib.Path(lp).read_text().strip().splitlines()) == 1


def test_prune_drops_expired_keeps_fresh(tmp_path):
    cp, lp = _paths(tmp_path)
    old = {
        "type": R.EVENT_TYPE, "subject_id": "arif", "source": R.SOURCE,
        "local_day": "2026-01-01",
        "recorded_at_utc": (_dt.datetime.now(UTC) - _dt.timedelta(days=45)).isoformat(timespec="seconds"),
        "metadata": {"event_count": 1},
    }
    fresh = dict(old, local_day="2026-11-19",
                 recorded_at_utc=_dt.datetime.now(UTC).isoformat(timespec="seconds"))
    pathlib.Path(lp).write_text(json.dumps(old) + "\n" + json.dumps(fresh) + "\n", encoding="utf-8")
    dropped = R.prune_expired(lp)
    assert dropped == 1
    remaining = pathlib.Path(lp).read_text().strip().splitlines()
    assert len(remaining) == 1
    assert json.loads(remaining[0])["local_day"] == "2026-11-19"


def test_corrupted_line_survives_prune(tmp_path):
    cp, lp = _paths(tmp_path)
    pathlib.Path(lp).write_text("{broken\n", encoding="utf-8")
    assert R.prune_expired(lp) == 0
    assert pathlib.Path(lp).read_text().strip() == "{broken"


# --- bounded summary wording -------------------------------------------------------


def test_summary_never_claims_fatigue(tmp_path):
    cp, lp = _paths(tmp_path)
    m = {"event_count": 40, "first_event_at": "2026-11-19T01:00:00+08:00",
         "last_event_at": "2026-11-19T03:30:00+08:00", "active_span_minutes": 150,
         "local_hour_band": "late_night", "context_switches": 3}
    s = R.allowed_summary(m)
    for forbidden in ("penat", "fatigue", "burnout", "anxious", "letih"):
        assert forbidden not in s
    assert "SYSTEM_OBSERVED" in s


def test_summary_empty_day(tmp_path):
    s = R.allowed_summary({"event_count": 0})
    assert "Tiada aktiviti" in s
