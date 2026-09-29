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


# ── D1, trace_id HRFID-20260929: the band must BE the arithmetic it advertises ──
# Measured 2026-09-29 14:53Z on :18083/health — age_seconds 37803.6 against
# max_fresh_age_seconds 3600 / stale_after_seconds 14400, while the same payload said
# status "fresh", freshness_band "FRESH", honesty.is_stale false. The band came from a
# private 12h/24h/72h ladder over `state["timestamp"]` — a clock the keepalive and
# /ready paths rewrite — so the thresholds printed beside it were decoration.

def test_age_beyond_stale_after_is_never_fresh():
    """The exact shape of the 14:53Z payload: 37,803.6s old, thresholds 3600/14400."""
    age = 37803.6
    state = {
        "last_successful_read": _iso(age / 3600),
        "timestamp": _iso(0.0),           # file just rewritten
        "keepalive_ts": _iso(0.0),        # keepalive just ticked
        "metrics": {},
    }
    band = server._get_freshness_band(state)
    assert band != "FRESH", band
    assert band == "EXPIRED", band
    assert server._is_stale_band(band) is True


def test_band_ladder_is_the_configured_thresholds():
    assert server._freshness_band_from_age(0) == "FRESH"
    assert server._freshness_band_from_age(server.WELL_MAX_FRESH_AGE_SECONDS) == "FRESH"
    assert server._freshness_band_from_age(server.WELL_MAX_FRESH_AGE_SECONDS + 1) == "STALE"
    assert server._freshness_band_from_age(server.WELL_STALE_AFTER_SECONDS) == "STALE"
    assert server._freshness_band_from_age(server.WELL_STALE_AFTER_SECONDS + 1) == "EXPIRED"
    assert server._freshness_band_from_age(37803.6) == "EXPIRED"


def test_band_fails_closed_without_a_clock():
    """Absence, garbage, or a clock in the future may not read as fresh."""
    assert server._freshness_band_from_age(None) == "EXPIRED"
    assert server._freshness_band_from_age(-5) == "EXPIRED"
    assert server._get_freshness_band({}) == "EXPIRED"
    assert server._get_freshness_band({"timestamp": "not-a-date"}) == "EXPIRED"
    assert server._is_stale_band(None) is True          # a missing band is not freshness


def test_is_stale_follows_the_same_arithmetic_as_the_band():
    for band, expected in (
        ("FRESH", False), ("STALE", True), ("EXPIRED", True), ("AGED", True), (None, True),
    ):
        assert server._is_stale_band(band) is expected, band
        honesty = server._honesty_block("VERIFIED", source_type="SENSOR", freshness_band=band)
        assert honesty["is_stale"] is expected, (band, honesty)


def test_ticks_cannot_reach_the_health_payload():
    """The payload's own numbers must agree with each other, not only with the ladder."""
    state = {
        "identity": "WELL",
        "role": "Body / Human Intelligence",
        "authority": "REFLECT_ONLY",
        "operator_id": "arif",
        "metrics": {},
        "well_score": 88.4,
        "truth_status": "OPERATOR_REPORTED",
        "environment": "PROD",
        "last_successful_read": _iso(37803.6 / 3600),
        "timestamp": _iso(0.0),
        "keepalive_ts": _iso(0.0),
    }
    c = server._classify_well_state(state)
    f = c["freshness"]
    assert f["age_seconds"] > f["stale_after_seconds"], f
    assert f["status"] == "expired", f
    assert c["freshness_band"] == "EXPIRED", c
    assert c["honesty"]["is_stale"] is True
    # the thresholds advertised are the thresholds used — no decoration keys
    assert f["max_fresh_age_seconds"] == server.WELL_MAX_FRESH_AGE_SECONDS
    assert f["stale_after_seconds"] == server.WELL_STALE_AFTER_SECONDS
    assert f["expired_after_seconds"] == server.WELL_STALE_AFTER_SECONDS
    assert f["age_clock"] == "observation", f


def test_genuine_recent_observation_is_still_allowed_to_be_fresh():
    """The fix must not flatten honest data — a reading actually taken now is fresh."""
    state = {"last_successful_read": _iso(0.001), "timestamp": _iso(0.001), "metrics": {}}
    assert server._get_freshness_band(state) == "FRESH"
    assert server._is_stale_band(server._get_freshness_band(state)) is False


def test_stored_claim_and_health_band_share_one_clock():
    """The two ladders used to disagree about the same file. One clock now feeds both."""
    state = _state(file_age_h=0.0, read_age_h=291.0)
    assert server._well_observation_band(state)["band"] == "EXPIRED"
    assert server._get_freshness_band(state) == "EXPIRED"


def test_no_freshness_writer_keeps_a_private_threshold_ladder():
    """The human plane must not hold a second, undeclared freshness ladder.

    The 12h/24h/72h ladder that produced the 14:53Z lie is gone; the configured
    thresholds are the only human-band arithmetic. (The machine-substrate probe has
    its own ladder over machine_state.json — a different object, not human freshness,
    and deliberately out of scope here.)
    """
    src = open("/root/WELL/server.py").read()
    for stale in ("age_hours <= 12", "age_hours <= 24", "age_hours <= 72"):
        assert stale not in src, f"the undeclared human freshness ladder is back: {stale}"
