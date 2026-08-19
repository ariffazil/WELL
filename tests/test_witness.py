"""WITNESS Phase 1 — divergence detection tests.

The two cases that would have caught the live 2026-08-19 state.json
leakage if WITNESS had been live:

  1. state.json with environment=TEST → DIVERGENCE
  2. well_check_repair.H_WELL ≠ well_validate_vitality.H_WELL → DIVERGENCE

Plus a positive case to prove the OK path is wired.

Background: docs/FINDINGS-2026-08-19.

Run: pytest tests/test_witness.py -v --tb=short
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "well_witness"))

from well_witness import cross_check  # noqa: E402


# ── 1. state.json with environment=TEST → DIVERGENCE ──────────────────────


def test_state_with_environment_test_returns_divergence():
    """The exact live bug: state.json left as a test fixture in production.

    The April 30 fixture had environment=TEST, truth_status=TEST (implicit),
    reason='Mocked healthy state for test session', and a 3.5-month-stale
    timestamp that still claimed FRESH. The WITNESS must catch this.
    """
    state = {
        "timestamp": "2026-04-30T00:00:00+00:00",
        "operator_id": "arif",
        "well_score": 0,
        "environment": "TEST",
        "truth_status": "TEST",
        "reason": "Mocked healthy state for test session",
        "freshness": "FRESH",
    }
    result = cross_check.check_state_honesty(state=state)
    assert result["verdict"] == "DIVERGENCE", (
        f"WITNESS missed the test fixture: {result}"
    )
    assert result["reason"] == "test_fixture_detected"
    assert "env=TEST" in result["evidence"]
    assert "remediation" in result, "DIVERGENCE must include a remediation hint"


def test_state_with_mocked_reason_only_returns_divergence():
    """The reason field alone — even with environment=PROD — is enough.

    Belt-and-braces: an attacker who flips environment to PROD but forgets
    to change the reason still gets caught.
    """
    state = {
        "timestamp": "2026-08-19T00:00:00+00:00",
        "environment": "PROD",
        "truth_status": "INSUFFICIENT_DATA",
        "reason": "Mocked state for CI",
    }
    result = cross_check.check_state_honesty(state=state)
    assert result["verdict"] == "DIVERGENCE"
    assert result["reason"] == "test_fixture_detected"


def test_state_honest_returns_ok():
    """The positive case: a 4-field honest empty must pass."""
    state = {
        "truth_status": "INSUFFICIENT_DATA",
        "environment": "PROD",
        "well_score": None,
        "reason": "no production state yet",
    }
    result = cross_check.check_state_honesty(state=state)
    assert result["verdict"] == "OK"
    assert result["reason"] == "state_honest"


def test_state_missing_file_returns_ok():
    """No state.json at all is honest empty, not a violation."""
    result = cross_check.check_state_honesty(
        state_path=Path("/nonexistent/path/state.json")
    )
    assert result["verdict"] == "OK"
    assert result["reason"] == "no_state_file"


# ── 2. well_check_repair.H_WELL ≠ well_validate_vitality.H_WELL → DIVERGENCE


def test_repair_leaks_readiness_returns_divergence():
    """If well_check_repair leaks a fabricated readiness field, DIVERGENCE.

    The T3 fix should prevent this in production. If the fix regresses,
    the WITNESS is the structural catch.
    """
    def mock_repair(mode=None, **kwargs):
        return {
            "ok": True,
            "observation": {
                "readiness": {"human": "OPTIMAL", "machine": "HEALTHY"},
                "status": "HOLD",
            },
        }

    def mock_vitality(mode=None, **kwargs):
        return {"H_WELL": "UNKNOWN", "ok": True}

    result = cross_check.check_h_well_divergence(
        well_check_repair_fn=mock_repair,
        well_validate_vitality_fn=mock_vitality,
    )
    assert result["verdict"] == "DIVERGENCE", (
        f"WITNESS missed the readiness leak: {result}"
    )
    assert "leaks_readiness" in result["reason"]
    assert "remediation" in result


def test_repair_top_level_readiness_returns_divergence():
    """Even at the top level (not inside observation), a leaked readiness
    field on well_check_repair is a DIVERGENCE.
    """
    def mock_repair(mode=None, **kwargs):
        return {"ok": True, "readiness": "OPTIMAL"}

    def mock_vitality(mode=None, **kwargs):
        return {"H_WELL": "READY"}

    result = cross_check.check_h_well_divergence(
        well_check_repair_fn=mock_repair,
        well_validate_vitality_fn=mock_vitality,
    )
    assert result["verdict"] == "DIVERGENCE"


def test_vitality_missing_h_well_returns_divergence():
    """If well_validate_vitality returns no H_WELL at all, DIVERGENCE.

    The two paths cannot agree on what they don't both report.
    """
    def mock_repair(mode=None, **kwargs):
        return {"ok": True, "observation": {}}

    def mock_vitality(mode=None, **kwargs):
        return {"ok": True, "M_WELL": "HEALTHY"}  # no H_WELL

    result = cross_check.check_h_well_divergence(
        well_check_repair_fn=mock_repair,
        well_validate_vitality_fn=mock_vitality,
    )
    assert result["verdict"] == "DIVERGENCE"
    assert "missing_h_well" in result["reason"]


def test_consistent_paths_return_ok():
    """The positive case: repair has no readiness, vitality reports H_WELL.

    T3 fix in place + well_validate_vitality working = OK.
    """
    def mock_repair(mode=None, **kwargs):
        return {"ok": True, "observation": {"status": "HOLD"}}

    def mock_vitality(mode=None, **kwargs):
        return {"ok": True, "H_WELL": "UNKNOWN"}

    result = cross_check.check_h_well_divergence(
        well_check_repair_fn=mock_repair,
        well_validate_vitality_fn=mock_vitality,
    )
    assert result["verdict"] == "OK"
    assert "consistent" in result["reason"]


# ── 3. run_all_checks aggregates both findings ─────────────────────────────


def test_run_all_checks_returns_both_findings():
    """Smoke test: run_all_checks returns a list with both checks present."""
    findings = cross_check.run_all_checks()
    assert isinstance(findings, list)
    assert len(findings) == 2
    check_names = {f["check"] for f in findings}
    assert "state_honesty" in check_names
    assert "h_well_divergence" in check_names
