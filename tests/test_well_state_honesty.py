"""
WELL State Honesty Tests
════════════════════════

Verify that WELL never pretends to know the sovereign's biological state
when it is reading fixtures, test data, or missing telemetry.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from server import (
    _classify_well_state,
    _state_is_insufficient,
    _assert_sovereign_presence,
    _load_state,
)


# ── 1. Mocked/test state is classified as insufficient ────────────────────────


def test_mocked_test_state_is_insufficient():
    state = {
        "timestamp": "2026-04-30T00:00:00+00:00",
        "operator_id": "arif",
        "metrics": {"cognitive": {"clarity": 10}},
        "well_score": 92.2,
        "truth_status": "TEST",
        "environment": "TEST",
        "reason": "Mocked healthy state for test session",
    }
    insufficient, reasons = _state_is_insufficient(state)
    assert insufficient is True
    assert any("truth_status:TEST" in r for r in reasons)
    assert any("environment:TEST" in r for r in reasons)
    assert any("mocked_state" in r for r in reasons)


def test_missing_identity_is_insufficient():
    state = {
        "timestamp": "2026-06-15T12:00:00+00:00",
        "metrics": {"cognitive": {"clarity": 10}},
        "truth_status": "VERIFIED",
        "environment": "PROD",
    }
    insufficient, reasons = _state_is_insufficient(state)
    assert insufficient is True
    assert any("identity_invalid" in r for r in reasons)


def test_no_telemetry_is_insufficient():
    state = {
        "timestamp": "2026-06-15T12:00:00+00:00",
        "operator_id": "arif",
        "identity": "WELL",
        "role": "Body / Human Intelligence",
        "authority": "REFLECT_ONLY",
        "metrics": {},
        "truth_status": "UNVERIFIED",
        "environment": "PROD",
    }
    insufficient, reasons = _state_is_insufficient(state)
    assert insufficient is True
    assert any("no_verified_telemetry" in r for r in reasons)


# ── 2. Classification converts insufficient state to honest health payload ────


def test_classify_mocked_state_returns_insufficient_data():
    state = {
        "timestamp": "2026-04-30T00:00:00+00:00",
        "operator_id": "arif",
        "metrics": {"cognitive": {"clarity": 10}},
        "well_score": 92.2,
        "truth_status": "TEST",
        "environment": "TEST",
        "reason": "Mocked healthy state for test session",
    }
    classification = _classify_well_state(state)
    assert classification["truth_status"] == "INSUFFICIENT_DATA"
    assert classification["well_signal"] == "WELL_HOLD"
    assert classification["well_score"] is None
    assert classification["owner_summary"]["color"] == "RED"
    assert "sovereign_state_unknown" in classification["owner_summary"]["reasons"]
    assert classification["freshness_band"] == "STALE"
    assert classification["freshness"]["status"] == "expired"


def test_classify_operator_reported_state_is_not_insufficient():
    state = {
        "timestamp": "2026-06-15T12:00:00+00:00",
        "operator_id": "arif",
        "identity": "WELL",
        "role": "Body / Human Intelligence",
        "authority": "REFLECT_ONLY",
        "delta_s": 0.0,
        "peace2": 1.0,
        "kappa_r": 0.95,
        "rasa": True,
        "amanah": "LOCK",
        "metrics": {},
        "truth_status": "OPERATOR_REPORTED",
        "environment": "PROD",
        "reason": "Sovereign presence asserted manually via /ready",
    }
    classification = _classify_well_state(state)
    assert classification["insufficient"] is False
    assert classification["truth_status"] == "OPERATOR_REPORTED"
    assert classification["well_signal"] == "WELL_OPERATOR_PRESENT"
    assert classification["owner_summary"]["color"] == "YELLOW"


# ── 3. /ready assertion writes honest OPERATOR_REPORTED state ─────────────────


def test_assert_sovereign_presence_writes_operator_reported(monkeypatch, tmp_path):
    state_path = tmp_path / "state.json"
    events_path = tmp_path / "events.jsonl"

    monkeypatch.setattr("server.STATE_PATH", state_path)
    monkeypatch.setattr("server.EVENTS_PATH", events_path)

    result = _assert_sovereign_presence(operator_id="arif")
    assert result["ok"] is True
    assert result["truth_status"] == "OPERATOR_REPORTED"

    state = json.loads(state_path.read_text())
    assert state["truth_status"] == "OPERATOR_REPORTED"
    assert state["environment"] == "PROD"
    assert state["operator_id"] == "arif"
    assert state["reason"].startswith("Sovereign presence asserted")

    # Events should be appended
    events = events_path.read_text().strip().split("\n")
    assert len(events) == 1
    event = json.loads(events[0])
    assert event["event"] == "SOVEREIGN_PRESENCE_ASSERTED"


def test_autouse_fixture_preserves_production_state():
    """A write-capable call must use the per-test paths from conftest."""
    import server

    production_state_path = ROOT / "state.json"
    production_events_path = ROOT / "events.jsonl"
    state_before = production_state_path.read_bytes()
    state_mtime_before = production_state_path.stat().st_mtime_ns

    assert server.STATE_PATH != production_state_path
    assert server.EVENTS_PATH != production_events_path

    result = _assert_sovereign_presence(operator_id="arif")

    assert result["ok"] is True
    assert server.STATE_PATH.exists()
    assert server.EVENTS_PATH.exists()
    assert production_state_path.read_bytes() == state_before
    assert production_state_path.stat().st_mtime_ns == state_mtime_before


# ── 4. Default missing-state payload is honest, not a fabricated score ────────


def test_load_state_default_is_honest(monkeypatch, tmp_path):
    state_path = tmp_path / "nonexistent_state.json"
    monkeypatch.setattr("server.STATE_PATH", state_path)

    state = _load_state()
    assert state["truth_status"] == "INSUFFICIENT_DATA"
    assert state["well_score"] is None
    assert state["environment"] == "PROD"
    assert state["reason"] == "No state file found. Sovereign state unknown."


# ── 5. Inject-as-VERIFIED must coerce to OPERATOR_REPORTED (T2 F2 harden) ─────


def test_inject_verified_coerces_to_self_report():
    """biometric_inject.sh historically wrote VERIFIED — that is a category error."""
    from server import _normalize_truth_status

    state = {
        "timestamp": "2026-07-09T00:55:21+00:00",
        "operator_id": "arif",
        "identity": "WELL",
        "role": "Body / Human Intelligence",
        "authority": "REFLECT_ONLY",
        # is_well() thresholds: peace2>=1.0, kappa_r>=0.95, rasa True, amanah LOCK
        "delta_s": 0.1,
        "peace2": 1.0,
        "kappa_r": 0.95,
        "rasa": True,
        "amanah": "LOCK",
        "metrics": {"cognitive": {"clarity": 9.0}},
        "well_score": 90.4,
        "truth_status": "VERIFIED",
        "environment": "PROD",
        "reason": "Sovereign biometric injection (biometric_inject.sh)",
    }
    assert _normalize_truth_status(state) == "OPERATOR_REPORTED"
    classification = _classify_well_state(state)
    assert classification["truth_status"] == "OPERATOR_REPORTED"
    assert classification["well_signal"] == "WELL_OPERATOR_PRESENT"
    assert classification["owner_summary"]["color"] == "YELLOW"
    assert classification["honesty"]["is_self_report"] is True
    assert classification["honesty"]["cockpit_banner_required"] is True
    assert "SELF-REPORT" in classification["honesty_banner"]
    assert classification["has_telemetry"] is False


def test_honesty_block_stale_banner():
    from server import _honesty_block

    h = _honesty_block("VERIFIED", source_type="SENSOR", freshness_band="STALE")
    assert h["is_stale"] is True
    assert h["code"] == "STALE"
    assert "STALE" in h["banner"]
