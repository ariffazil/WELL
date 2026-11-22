"""PR-0a — cross-substrate inheritance guard (M→H leak cut).

Forged 2026-11-22 under sovereign GO (scope: PR-0a only).
Defect: machine load could decrement the composite ``well_score`` that
``vitality_gate`` then read as a human state, with an evidence label claiming
``self_report_score`` while the actual self-report field was absent.

Invariants enforced (Claude critique WELL-H1/H2 + WELL AGENTS.md Invariant #4):
  - A composite score may inform C_WELL; it may not instantiate H_WELL
    without a human-source observation.
  - No ``self_report`` label may be attached to a machine-derived or
    composite value when ``self_report_score`` is None.
  - Machine carbon inference degrades evidence, never state, when no
    human observation exists.

Every test here must FAIL on pre-patch code and PASS post-patch (spec §8).
Fixtures are generic (operator-001 / generic-subject) — no real person data.
"""

from __future__ import annotations

import json
import sys
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import vitality_gate as vg
from vitality_gate import assess_h_well, vitality_gate

ARIFOS_RUNTIME = Path("/root/arifOS/arifosmcp/runtime")


def _fresh_iso(hours_ago: float = 1.0) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()


def _machine_strain_sensor() -> dict:
    """Generic high machine-pressure carbon inference (no person data)."""
    return {
        "readiness_score": 0.1,
        "fatigue": {"level": "HIGH"},
        "sessions": {"human": 6, "agent": 40},
        "circadian": {"phase": "LATE_NIGHT"},
        "sleep": {"sleeping": False},
    }


def _operator_reported_state(**over) -> dict:
    """State as the defect leaves it: operator truth, composite 0, no observation."""
    base = {
        "operator_id": "operator-001",
        "environment": "PROD",
        "timestamp": _fresh_iso(),
        "metrics": {},
        "well_score": 0,
        "self_report_score": None,
        "truth_status": "OPERATOR_REPORTED",
    }
    base.update(over)
    return base


# ── Test A — high machine pressure + no human observation ────────────────────
def test_machine_pressure_without_human_observation_is_not_critical():
    """A: machine strain may not produce a human CRITICAL label."""
    result = assess_h_well(
        _operator_reported_state(), substrate_data=_machine_strain_sensor()
    )
    assert result["state"] == "UNKNOWN", (
        f"expected UNKNOWN, got {result['state']} — machine pressure "
        f"instantiated H. Evidence: {result.get('evidence', '')}"
    )
    assert result["rank"] == 0, f"expected rank 0, got {result['rank']}"
    assert result["state"] != "CRITICAL"


# ── Test B — evidence label honesty ──────────────────────────────────────────
def test_no_self_report_label_without_a_self_report():
    """B: self_report_score=None must never be labelled self_report."""
    result = assess_h_well(_operator_reported_state(), substrate_data=None)
    blob = json.dumps(result, default=str).lower()
    assert "self_report" not in blob, (
        f"evidence claims self_report while self_report_score is None: {blob}"
    )


# ── Test C — machine evidence survives, H does not ───────────────────────────
def test_machine_degradation_flows_to_coupled_not_human(
    monkeypatch: pytest.MonkeyPatch,
):
    """C: M may degrade and inform C_WELL; H stays UNKNOWN."""

    def _degraded_m():
        return {
            "state": "DEGRADED",
            "rank": 1,
            "evidence": "machine-pressure-high",
            "uncertainty": 0.3,
            "source": "machine_state.json",
        }

    monkeypatch.setattr(vg, "assess_m_well", _degraded_m)
    gate = vitality_gate(
        state=_operator_reported_state(), sensor_data=_machine_strain_sensor()
    )
    assert gate["H_WELL"]["state"] == "UNKNOWN", (
        f"H_WELL={gate['H_WELL']['state']} — machine evidence leaked into H"
    )
    assert gate["M_WELL"]["state"] == "DEGRADED", "machine evidence was removed"
    assert gate["C_WELL"]["state"] in ("HIGH_RISK", "MEDIUM_RISK"), (
        f"C_WELL should carry the coupled risk, got {gate['C_WELL']['state']}"
    )
    assert "M=DEGRADED" in gate["C_WELL"]["evidence"]


# ── Test D — genuine scoped self-report with value 0 ─────────────────────────
def test_scoped_self_report_zero_is_not_critical():
    """D: a real self-report of 0 is an observation, not a CRITICAL verdict.

    The gate has no semantic-scale binding yet (PR-1 scope), so a bare
    number cannot authorize a state label — the observation is preserved
    under SELF_REPORTED provenance instead of being read as CRITICAL.
    """
    state = _operator_reported_state(
        well_score=0,
        self_report_score=0,
        # declared scale travels with the observation (generic fixture):
        self_report_metric="fatigue",
        self_report_scale={
            "min": 0,
            "max": 10,
            "direction": "higher_means_more_fatigue",
        },
        self_report_source="SELF_REPORTED",
    )
    result = assess_h_well(state, substrate_data=None)
    assert result["state"] != "CRITICAL", (
        f"self-report of 0 on a declared scale was read as {result['state']}"
    )
    assert "self_report_score=0" in result["evidence"], (
        f"observation not preserved in evidence: {result.get('evidence', '')}"
    )
    assert "SELF_REPORTED" in result["evidence"]


# ── Test E — unknown/composite writer defense (consumer guard) ───────────────
def test_composite_zero_without_provenance_is_unknown():
    """E: well_score=0 from an unknown writer cannot instantiate H."""
    state = _operator_reported_state(
        well_score=0, self_report_score=None, source="unknown"
    )
    result = assess_h_well(state, substrate_data=None)
    assert result["state"] == "UNKNOWN", (
        f"composite well_score=0 with no human provenance gave "
        f"{result['state']} — consumer guard failed"
    )
    assert result["rank"] == 0


# ── Test F — source guard: bridge may not write the human score ──────────────
def test_machine_load_delta_never_writes_well_score(tmp_path, monkeypatch):
    """Source repair: signal_cognitive_pressure must not modify well_score.

    Machine pressure stays recorded under machine/coupled provenance
    (cognitive metrics + W6 floor); it may not decrement the composite
    consumed as H-WELL. Skipped when the arifOS tree is absent.
    """
    if not ARIFOS_RUNTIME.exists():
        pytest.skip("arifOS tree not present on this host")
    sys.path.insert(0, str(ARIFOS_RUNTIME))
    try:
        import httpx  # noqa: F401
    except ImportError:
        sys.modules["httpx"] = types.ModuleType("httpx")
    try:
        import well_bridge
    except Exception as exc:  # pragma: no cover - environment-dependent
        pytest.skip(f"well_bridge not importable: {exc}")

    state_file = tmp_path / "well-state.json"
    state_file.write_text(
        json.dumps({"well_score": 62, "metrics": {}, "floors_violated": []})
    )
    monkeypatch.setattr(well_bridge, "WELL_STATE_PATH", state_file)

    ok = well_bridge.signal_cognitive_pressure(load_delta=9.0, source="forge")
    assert ok is True, "bridge failed to record machine pressure at all"

    after = json.loads(state_file.read_text())
    assert after["well_score"] == 62, (
        f"machine load_delta wrote well_score={after['well_score']} "
        "(M→H inheritance still open)"
    )
    # machine evidence itself must survive under machine provenance
    assert after["metrics"]["cognitive"]["decision_fatigue"] == 9.0
    assert "W6_METABOLIC_PAUSE" in after["floors_violated"]
