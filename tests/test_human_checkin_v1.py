"""Tests — WELL::HUMAN_CHECKIN::v1 (F13 acceptance, 2026-11-19).

Covers: honesty, privacy, reliability, idempotency, per-signal freshness,
bounded attention interpretation, no-restart invariant.
All fixtures use tmp paths — the production event log is never touched.
"""

from __future__ import annotations

import datetime as _dt
import json
import pathlib
import sys

sys.path.insert(0, "/root/WELL")

from human_checkin import intake as I
from human_checkin import projection as P

UTC = _dt.timezone.utc


def _log(tmp: pathlib.Path) -> str:
    return str(tmp / "human_checkins.jsonl")


def _age_iso(seconds: int) -> str:
    return (
        (_dt.datetime.now(UTC) - _dt.timedelta(seconds=seconds))
        .astimezone()
        .isoformat(timespec="seconds")
    )


# --- parsing / validation ------------------------------------------------------


def test_parse_basic():
    assert I.parse_checkin_text("6.5,5,8") == {
        "sleep_hours": 6.5,
        "energy": 5.0,
        "load": 8.0,
    }


def test_parse_partial_two_fields():
    v = I.parse_checkin_text("6.5,5")
    assert v == {"sleep_hours": 6.5, "energy": 5.0}
    assert "load" not in v  # partial stays partial


def test_reject_out_of_range_with_reason():
    r = I.ingest("25,5,8", event_log=_log(pathlib.Path("/tmp/hc_t1")))
    assert r["status"] == "rejected"
    assert "out_of_range" in r["reason"]


def test_reject_energy_zero():
    r = I.ingest("6.5,0,8", event_log="/tmp/hc_t2/x.jsonl")
    assert r["status"] == "rejected"


def test_reject_non_numeric():
    r = I.ingest("abc,5,8", event_log="/tmp/hc_t3/x.jsonl")
    assert r["status"] == "rejected"
    assert "invalid_number" in r["reason"]


def test_no_fourth_field_clarity():
    r = I.ingest("6.5,5,8,7", event_log="/tmp/hc_t4/x.jsonl")
    assert r["status"] == "rejected"
    assert "too_many_fields" in r["reason"]


def test_subject_binding_allowlist(tmp_path):
    """Subject binding (F13 P0 acceptance): only the bound subject may check in."""
    r = I.ingest("6.5,5,8", event_log=_log(tmp_path), subject_id="not_arif")
    assert r["status"] == "rejected"
    assert "unknown_subject" in r["reason"]
    assert P.load_events(_log(tmp_path)) == []  # nothing written


# --- honesty invariants ----------------------------------------------------------


def test_ingest_never_flips_verified_telemetry(tmp_path):
    r = I.ingest("6.5,5,8", event_log=_log(tmp_path))
    assert r["status"] == "accepted"
    assert r["has_verified_telemetry"] is False
    assert r["evidence_class"] == "SELF_REPORT"


def test_missing_sleep_never_zero(tmp_path):
    log = _log(tmp_path)
    I.ingest("6.5,5", event_log=log)
    proj = P.build_projection(P.load_events(log))
    sig = proj["signals"]["load"]
    assert sig["freshness"] == "MISSING"
    assert sig["missing_reason"] == "not_provided"
    assert "value" not in sig  # no fabricated zero


def test_no_score_synthesis(tmp_path):
    log = _log(tmp_path)
    I.ingest("6.5,5,8", event_log=log)
    proj = P.build_projection(P.load_events(log))
    dumped = json.dumps(proj)
    assert "well_score" not in dumped
    assert "peace2" not in dumped and "kappa" not in dumped and "amanah" not in dumped


def test_per_signal_freshness_isolation(tmp_path):
    """A NEW energy observation must NOT refresh an OLD sleep observation."""
    log = _log(tmp_path)
    I.ingest(
        "6.5,5,8", event_log=log, observed_at=_age_iso(12 * 3600)
    )  # 12h old -> STALE band
    I.ingest(
        {"energy": 6.0, "load": 4.0}, event_log=log
    )  # fresh energy+load, sleep untouched
    proj = P.build_projection(P.load_events(log))
    assert proj["signals"]["sleep_hours"]["freshness"] in ("STALE", "EXPIRED")
    assert proj["signals"]["energy"]["freshness"] == "FRESH"
    assert proj["signals"]["load"]["freshness"] == "FRESH"


def test_attention_unknown_is_valid(tmp_path):
    proj = P.build_projection([])
    assert proj["attention_readiness"]["state"] == "UNKNOWN"


def test_stale_only_signals_give_unknown(tmp_path):
    log = _log(tmp_path)
    I.ingest("6.5,5,8", event_log=log, observed_at=_age_iso(30 * 3600))
    proj = P.build_projection(P.load_events(log))
    assert proj["attention_readiness"]["state"] == "UNKNOWN"


# --- bounded interpretation vector -----------------------------------------------


def test_saturated_on_high_load(tmp_path):
    log = _log(tmp_path)
    I.ingest("7.0,5,9", event_log=log)
    proj = P.build_projection(P.load_events(log))
    assert proj["attention_readiness"]["state"] == "SATURATED"
    assert proj["attention_readiness"]["confidence"] == "PARTIAL"


def test_constrained_on_short_sleep(tmp_path):
    log = _log(tmp_path)
    I.ingest("5.0,6,4", event_log=log)
    assert (
        P.build_projection(P.load_events(log))["attention_readiness"]["state"]
        == "CONSTRAINED"
    )


def test_available_when_no_constraining_signal(tmp_path):
    log = _log(tmp_path)
    I.ingest("8.0,7,3", event_log=log)
    assert (
        P.build_projection(P.load_events(log))["attention_readiness"]["state"]
        == "AVAILABLE"
    )


# --- reliability: idempotency, rebuild, atomicity --------------------------------


def test_duplicate_idempotent(tmp_path):
    log = _log(tmp_path)
    r1 = I.ingest("6.5,5,8", event_log=log)
    r2 = I.ingest("6.5,5,8", event_log=log)
    assert r1["status"] == "accepted"
    assert r2["status"] == "duplicate"
    events = P.load_events(log)
    assert len(events) == 1  # no second event written


def test_same_values_after_window_not_duplicate(tmp_path):
    log = _log(tmp_path)
    old = (_dt.datetime.now(UTC) - _dt.timedelta(hours=2)).isoformat(timespec="seconds")
    I.ingest("6.5,5,8", event_log=log, recorded_at_utc=old)
    r2 = I.ingest("6.5,5,8", event_log=log)
    assert r2["status"] == "accepted"
    assert len(P.load_events(log)) == 2  # genuine second check-in, same values


def test_duplicate_collapse_uses_arrival_time(tmp_path):
    log = _log(tmp_path)
    r1 = I.ingest("6.5,5,8", event_log=log)
    r2 = I.ingest("6.5,5,8", event_log=log, observed_at=_age_iso(2 * 3600))
    # same arrival minute, different observed_at = Telegram retry, still duplicate
    assert r2["status"] == "duplicate"


def test_projection_rebuildable_from_event_log(tmp_path):
    log = _log(tmp_path)
    I.ingest("6.5,5,8", event_log=log)
    a = P.build_projection(P.load_events(log))
    b = P.build_projection(P.load_events(log))
    assert a["signals"] == b["signals"]  # deterministic from events alone


def test_corrupted_lines_skipped_not_fatal(tmp_path):
    log = _log(tmp_path)
    I.ingest("6.5,5,8", event_log=log)
    with open(log, "a", encoding="utf-8") as fh:
        fh.write("{corrupted json\n")
    events = P.load_events(log)
    assert len(events) == 1


def test_projection_write_atomic(tmp_path):
    path = str(tmp_path / "human_state.json")
    proj = P.build_projection([])
    out = P.write_projection(proj, path)
    assert pathlib.Path(out).exists()
    assert not list(tmp_path.glob("*.tmp.*"))  # tmp cleaned by os.replace


def test_evidence_separation(tmp_path):
    log = _log(tmp_path)
    I.ingest("6.5,5,8", event_log=log)
    proj = P.build_projection(P.load_events(log))
    assert proj["evidence_summary"] == {
        "self_reported": 3,
        "system_observed": 0,
        "sensor_measured": 0,
    }
    assert proj["human_evidence"]["class"] == "PARTIAL_SELF_REPORT"
    assert proj["human_evidence"]["has_verified_telemetry"] is False


def test_no_restart_touch(tmp_path):
    """Intake path must never invoke systemctl / service restart."""
    import inspect

    src = inspect.getsource(I) + inspect.getsource(P)
    for forbidden in ("systemctl", "subprocess", "os.system"):
        assert forbidden not in src
