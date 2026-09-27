"""H-WELL must age the READING, not the file (F13 order 2026-09-28).

The bug this pins: `_check_data_freshness()` computed staleness from
`state["timestamp"]`, which the `/ready` presence assertion and the keepalive path
rewrite. A 291-hour-old self-report therefore reported `freshness: FRESH`, and
`well_score 88.4` was consumed downstream as Arif's current readiness. The clock that
matters is when a human reading was last actually taken.

Also pinned: a liveness ping may assert *presence*, but it may not mint confidence,
freshness, or floor-compliance numbers.
"""

from __future__ import annotations

import datetime as dt
import json

import server

NOW = dt.datetime.now(dt.timezone.utc)


def _iso(hours_ago: float) -> str:
    return (NOW - dt.timedelta(hours=hours_ago)).isoformat()


def _state(file_age_h: float, read_age_h: float | None) -> dict:
    s = {"timestamp": _iso(file_age_h), "metrics": {}}
    if read_age_h is not None:
        s["last_successful_read"] = _iso(read_age_h)
    return s


# ── the regression itself ────────────────────────────────────────────────────
def test_recent_file_write_over_old_reading_is_not_fresh():
    """The exact shape of tonight's defect: file touched now, read taken 291h ago."""
    band = server._well_observation_band(_state(file_age_h=0.0, read_age_h=291.0))
    assert band["band"] == "EXPIRED", band
    assert band["counts_toward_readiness"] is False
    assert band["age_hours"] > 290


def test_check_data_freshness_labels_the_reading_expired():
    f = server._check_data_freshness(_state(file_age_h=0.0, read_age_h=291.0))
    assert f["freshness_label"] == "expired", f
    assert f["observation_band"] == "EXPIRED"
    assert f["counts_toward_readiness"] is False
    # existing keys preserved: consumers must not break
    for key in ("state_age_hours", "freshness_label", "has_telemetry", "truth_status"):
        assert key in f, key


def test_genuinely_recent_reading_is_fresh():
    f = server._check_data_freshness(_state(file_age_h=0.05, read_age_h=0.05))
    assert f["freshness_label"] == "fresh", f
    assert f["counts_toward_readiness"] is True


def test_aging_is_conservative_not_flattering():
    """2h old is not 'fresh'. AGING folds to stale; the fine band is still exposed."""
    f = server._check_data_freshness(_state(file_age_h=2.0, read_age_h=2.0))
    assert f["freshness_label"] == "stale", f
    assert f["observation_band"] == "AGING"


def test_no_timestamp_anywhere_is_unknown_not_zero():
    """Absence reports as UNKNOWN; it must not silently read as fresh or as 0h."""
    f = server._check_data_freshness({"metrics": {}})
    assert f["freshness_label"] == "unknown", f
    assert f["state_age_hours"] is None
    assert f["counts_toward_readiness"] is False


def test_heartbeat_clock_used_when_no_read_field():
    s = {"timestamp": _iso(0.0), "heartbeat_ts": _iso(100.0), "metrics": {}}
    band = server._well_observation_band(s)
    assert band["band"] == "EXPIRED", band


# ── presence must not fabricate epistemic status ────────────────────────────
def test_ready_presence_no_longer_mints_fresh_high():
    """Pins the source shape so the fabricated trio cannot return unnoticed."""
    src = open("/root/WELL/server.py").read()
    forbidden = '"confidence": "HIGH",\n            "freshness": "FRESH"'
    assert forbidden not in src, (
        "presence assertion is again minting HIGH-confidence FRESH state from a liveness ping"
    )
    assert '"presence_only": True' in src


def test_band_labels_stay_inside_existing_vocabulary():
    """Consumers branch on four labels; do not invent a fifth without a sweep."""
    allowed = {"fresh", "stale", "expired", "unknown"}
    for ages in ((0.0, 0.0), (0.5, 2.0), (0.5, 100.0), (0.5, None), (0.0, 0.0)):
        f = server._check_data_freshness(_state(*ages))
        assert f["freshness_label"] in allowed, f


# ── the stored claim can no longer outlive its measurement ──────────────────
def test_file_write_time_alone_cannot_produce_fresh():
    """Only an observation clock may say FRESH. A rewritten `timestamp` may not."""
    s = {"timestamp": _iso(0.0), "metrics": {}}          # touched right now, never read
    band = server._well_observation_band(s)
    assert band["clock"] == "file_write_only", band
    assert band["band"] == "STALE", band                  # capped, never FRESH
    assert server._check_data_freshness(s)["freshness_label"] == "stale"


def test_save_state_derives_freshness_and_never_stores_a_claim(tmp_path, monkeypatch):
    """_save_state is the single writer: what lands on disk is derived, not asserted."""
    target = tmp_path / "state.json"
    monkeypatch.setattr(server, "STATE_PATH", target)
    server._save_state({"metrics": {}, "operator_id": "arif"})
    saved = json.loads(target.read_text())
    assert saved["freshness"] in {"FRESH", "AGING", "STALE", "EXPIRED", "UNKNOWN"}
    assert saved["freshness"] != "FRESH", saved           # no observation -> cannot be fresh
    assert saved["freshness_clock"] == "file_write_only", saved


def test_no_writer_in_server_asserts_a_freshness_literal():
    src = open("/root/WELL/server.py").read()
    assert '"freshness": "FRESH"' not in src
    assert 'state["freshness"] = "FRESH"' not in src


def test_keepalive_may_only_report_its_own_liveness():
    """A cron heartbeat must not manufacture a human observation clock."""
    src = open("/root/WELL/scripts/well_auto_keepalive.py").read()
    for forbidden in ('data["freshness"]', 'data["last_successful_read"]',
                      'data["last_successful_write"]'):
        assert forbidden not in src, forbidden
    assert 'data["keepalive_ts"]' in src
