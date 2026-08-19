"""
Vitality Gate Environment Safety Tests
═══════════════════════════════════════

The vitality_gate must refuse to produce a verdict for a state file that
is itself a test fixture. These tests assert the property:

    Given state with environment=TEST, or truth_status=TEST, or
    reason starting with "Mocked", or well_score=0 with reason
    claiming health, the gate must return h_state=UNKNOWN, h_rank=0,
    regardless of timestamp, well_score, or truth_status.

Background: see docs/FINDINGS-2026-08-19-state-leakage-and-witness-need.md

Run: pytest tests/test_vitality_gate_environment_safety.py -v --tb=short

These tests are expected to FAIL on the current code — they document the
expected behavior. Fixing vitality_gate.py:466 to call
_state_is_insufficient (from server.py) is the three-line change that
makes them pass.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from vitality_gate import assess_h_well


def test_gate_rejects_test_environment():
    """environment=TEST must produce h_state=UNKNOWN, h_rank=0."""
    state = {
        "timestamp": "2026-04-30T00:00:00+00:00",
        "operator_id": "arif",
        "metrics": {"cognitive": {"clarity": 10}},
        "well_score": 92.2,
        "truth_status": "VERIFIED",
        "environment": "TEST",
        "reason": "Mocked healthy state for test session",
    }
    result = assess_h_well(state, substrate_data=None)
    assert result["state"] == "UNKNOWN", (
        f"got state={result['state']} for environment=TEST; expected UNKNOWN. "
        f"Evidence: {result.get('evidence', '')}"
    )
    assert result["rank"] == 0, (
        f"got rank={result['rank']} for environment=TEST; expected 0"
    )


def test_gate_rejects_mismatched_truth_status():
    """truth_status=VERIFIED with empty metrics is a category error.

    Same coercion as biometric_inject.sh VERIFIED → OPERATOR_REPORTED,
    applied to the gate's reading path. The gate must not produce READY
    when the state file claims VERIFIED with no biometric data.
    """
    state = {
        "timestamp": "2026-08-19T09:30:12+00:00",
        "operator_id": "arif",
        "metrics": {},
        "well_score": None,
        "truth_status": "VERIFIED",
        "environment": "PROD",
    }
    result = assess_h_well(state, substrate_data=None)
    assert result["state"] != "READY", (
        f"got state={result['state']} for empty-metrics VERIFIED claim; "
        f"expected not READY. Evidence: {result.get('evidence', '')}"
    )
    assert result["rank"] < 4, (
        f"got rank={result['rank']} for empty-metrics VERIFIED; expected < 4"
    )


def test_h_well_unmeasured_when_no_biometrics():
    """Honest empty PROD state must abstain, not READY."""
    state = {
        "truth_status": "INSUFFICIENT_DATA",
        "environment": "PROD",
        "well_score": None,
        "reason": "no production state yet",
    }
    result = assess_h_well(state, substrate_data=None)
    assert result["state"] == "UNMEASURED"
    assert result["rank"] is None


def test_gate_determinism_with_frozen_inputs():
    """Two calls with identical inputs must return byte-identical outputs.

    This is the #4 property from the upgrade plan: the gate must be a
    function of its inputs. The substrate sensor is time-dependent (live
    data), so this test freezes the substrate as well.
    """
    state = {
        "timestamp": "2026-08-19T09:30:12+00:00",
        "operator_id": "arif",
        "metrics": {"cognitive": {"clarity": 8}},
        "well_score": 80.0,
        "truth_status": "OPERATOR_REPORTED",
        "environment": "PROD",
    }
    sensor = {
        "readiness_score": 0.85,
        "fatigue": {"level": "LOW"},
        "sessions": {"human": 1, "agent": 2},
        "circadian": {"phase": "MORNING_PEAK"},
        "sleep": {"sleeping": False},
    }
    result1 = assess_h_well(state, substrate_data=sensor)
    result2 = assess_h_well(state, substrate_data=sensor)
    assert result1 == result2, (
        f"non-deterministic gate output for identical inputs: "
        f"{result1} != {result2}"
    )


def test_gate_substrate_only_path_requires_caution():
    """When state.json is stale (>48h) and substrate is the only signal,
    the gate must NOT produce a confident READY. The current code path
    produces READY (rank 4) on substrate-only. The fix is the UNMEASURED
    state proposed in the upgrade plan: substrate-only with stale
    self-report abstains from the H_WELL vote rather than overriding it.

    This test asserts what the gate SHOULD do.
    """
    state = {
        "timestamp": "2026-04-30T00:00:00+00:00",  # 111 days old
        "operator_id": "arif",
        "metrics": {},
        "well_score": None,
        "truth_status": "UNVERIFIED",
        "environment": "PROD",
    }
    sensor = {
        "readiness_score": 0.95,  # high substrate score
        "fatigue": {"level": "LOW"},
        "sessions": {"human": 0, "agent": 3},
        "circadian": {"phase": "MORNING_PEAK"},
        "sleep": {"sleeping": False},
    }
    result = assess_h_well(state, substrate_data=sensor)
    assert result["state"] != "READY", (
        f"substrate-only path produced READY for 111-day-stale self-report: "
        f"this is the absence-laundering bug. State was {result['state']}, "
        f"rank was {result['rank']}."
    )
    assert result["uncertainty"] >= 0.5, (
        f"uncertainty {result['uncertainty']} is too low for substrate-only "
        f"path with stale self-report; expected >= 0.5"
    )
