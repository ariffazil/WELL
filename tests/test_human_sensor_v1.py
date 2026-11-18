"""Tests — WELL::HUMAN_SENSOR::v1 (route-agnostic SENSOR_MEASURED intake).

F13 directive 2026-11-19 (sovereign, autonomous mode): build the sensor intake
lane that accepts measured events from ANY route (Health Connect / Zepp API /
Gadgetbridge export) without rework, without manual data provision, without
biometric_inject.sh, without scores, without restarts.

Stream isolation is a hard invariant: sensor events NEVER touch
human_checkins.jsonl (SELF_REPORT) and never merge evidence classes.
"""

from __future__ import annotations

import datetime as _dt
import inspect
import json
import pathlib
import sys

sys.path.insert(0, "/root/WELL")

from human_checkin import intake as I
from human_checkin import sensor as S

UTC = _dt.timezone.utc


def _log(tmp: pathlib.Path) -> str:
    return str(tmp / "sensor_events.jsonl")


def _age_iso(seconds: int) -> str:
    return (
        (_dt.datetime.now(UTC) - _dt.timedelta(seconds=seconds))
        .astimezone()
        .isoformat(timespec="seconds")
    )


# --- validation -----------------------------------------------------------------


def test_sensor_accept_valid_event(tmp_path):
    r = S.ingest_sensor_event(
        {"heart_rate_bpm": 62}, source="health_connect", event_log=_log(tmp_path)
    )
    assert r["status"] == "accepted"
    assert r["provenance"] == "sensor_measured"
    assert r["source"] == "health_connect"
    obs = r["observations"][0]
    assert obs["unit"] == "bpm"
    assert obs["provenance"] == "sensor_measured"


def test_sensor_reject_unknown_measurement(tmp_path):
    r = S.ingest_sensor_event(
        {"mood_vibe": 5}, source="health_connect", event_log=_log(tmp_path)
    )
    assert r["status"] == "rejected"
    assert "unknown_measurement" in r["reason"]
    assert S.load_events(_log(tmp_path)) == []


def test_sensor_reject_out_of_range(tmp_path):
    r = S.ingest_sensor_event(
        {"heart_rate_bpm": 400}, source="zepp_api", event_log=_log(tmp_path)
    )
    assert r["status"] == "rejected"
    assert "out_of_range" in r["reason"]


def test_sensor_reject_empty_source(tmp_path):
    """Lane binding: a sensor event must name the route it arrived by."""
    r = S.ingest_sensor_event(
        {"heart_rate_bpm": 62}, source="", event_log=_log(tmp_path)
    )
    assert r["status"] == "rejected"
    assert "source_required" in r["reason"]


def test_sensor_reject_foreign_subject(tmp_path):
    r = S.ingest_sensor_event(
        {"heart_rate_bpm": 62},
        source="zepp_api",
        subject_id="not_arif",
        event_log=_log(tmp_path),
    )
    assert r["status"] == "rejected"
    assert "unknown_subject" in r["reason"]


def test_sensor_registry_covers_core_signals():
    for m in (
        "sleep_hours",
        "heart_rate_bpm",
        "resting_heart_rate_bpm",
        "hrv_ms",
        "spo2_pct",
        "steps_count",
    ):
        assert m in S.REGISTRY, m


# --- reliability -----------------------------------------------------------------


def test_sensor_duplicate_idempotent(tmp_path):
    log = _log(tmp_path)
    r1 = S.ingest_sensor_event(
        {"steps_count": 8123}, source="health_connect", event_log=log
    )
    r2 = S.ingest_sensor_event(
        {"steps_count": 8123}, source="health_connect", event_log=log
    )
    assert r1["status"] == "accepted"
    assert r2["status"] == "duplicate"
    assert len(S.load_events(log)) == 1


def test_sensor_same_values_later_accepted(tmp_path):
    log = _log(tmp_path)
    old = (_dt.datetime.now(UTC) - _dt.timedelta(hours=2)).isoformat(timespec="seconds")
    S.ingest_sensor_event(
        {"steps_count": 8123},
        source="health_connect",
        event_log=log,
        recorded_at_utc=old,
    )
    r2 = S.ingest_sensor_event(
        {"steps_count": 8123}, source="health_connect", event_log=log
    )
    assert r2["status"] == "accepted"
    assert len(S.load_events(log)) == 2


def test_sensor_per_signal_freshness_isolation(tmp_path):
    """A fresh steps sync must NOT refresh an old heart-rate reading."""
    log = _log(tmp_path)
    S.ingest_sensor_event(
        {"heart_rate_bpm": 62, "steps_count": 500},
        source="health_connect",
        event_log=log,
        observed_at=_age_iso(6 * 3600),
    )  # hr max age 1h -> EXPIRED
    S.ingest_sensor_event(
        {"steps_count": 8000}, source="health_connect", event_log=log
    )  # fresh steps only
    proj = S.build_sensor_projection(S.load_events(log))
    assert proj["signals"]["heart_rate_bpm"]["freshness"] in ("STALE", "EXPIRED")
    assert proj["signals"]["steps_count"]["freshness"] == "FRESH"


# --- honesty / evidence separation -------------------------------------------------


def test_sensor_projection_evidence_class(tmp_path):
    log = _log(tmp_path)
    S.ingest_sensor_event(
        {"heart_rate_bpm": 62, "sleep_hours": 7.0},
        source="gadgetbridge_export",
        event_log=log,
    )
    proj = S.build_sensor_projection(S.load_events(log))
    assert proj["evidence_summary"] == {
        "self_reported": 0,
        "system_observed": 0,
        "sensor_measured": 2,
    }
    assert proj["human_evidence"]["class"] == "SENSOR_MEASURED"
    assert proj["human_evidence"]["has_device_telemetry"] is True
    assert "well_score" not in json.dumps(proj)
    assert "attention_readiness" not in json.dumps(proj)  # P4 couples later, not here


def test_sensor_stream_isolated_from_checkin_stream(tmp_path):
    """Sensor ingest must never write the SELF_REPORT log, and the checkin
    projection loader must never see sensor events."""
    s_log = str(tmp_path / "sensor_events.jsonl")
    c_log = str(tmp_path / "human_checkins.jsonl")
    S.ingest_sensor_event(
        {"heart_rate_bpm": 62}, source="health_connect", event_log=s_log
    )
    I.ingest("6.5,5,8", event_log=c_log)
    from human_checkin import projection as P

    s_events = S.load_events(s_log)
    assert s_events
    assert s_events[0]["evidence_class"] == "SENSOR_MEASURED"
    assert s_events[0]["observations"][0]["provenance"] == "sensor_measured"
    # the checkin log loader must not see sensor events (type filter)
    assert len(P.load_events(c_log)) == 1
    with open(c_log, encoding="utf-8") as fh:
        assert "sensor_measured" not in fh.read()


# --- invariants ----------------------------------------------------------------------


def test_sensor_no_restart_no_state_write(tmp_path):
    src = inspect.getsource(S)
    for forbidden in ("systemctl", "subprocess", "os.system"):
        assert forbidden not in src
    # no write path to the 13-signal state.json in the module
    assert "/var/lib/well/state.json" not in src


def test_sensor_provenance_cannot_be_forged():
    """The module fixes provenance — a caller cannot label manual numbers as
    measured. There is no parameter to override it."""
    sig = inspect.signature(S.ingest_sensor_event)
    assert "provenance" not in sig.parameters
