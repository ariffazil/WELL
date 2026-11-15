"""Public-path regression and semantic verification suite for WELL check_repair.

Verifies:
1. Machine task with operator telemetry present.
2. Machine task with operator telemetry absent.
3. Fresh flag with missing pressure/condition fields.
4. Unknown telemetry status.
5. None/string/negative/>100/NaN/infinite measurements.
6. Provider-consumer field mismatch.
7. Consequential operation without approval.
8. Missing evidence despite human approval.
9. Ambiguous text and unknown structured operation.
10. Schema compatibility and legacy consumer behavior.
11. Public-path reproduction of baseline defect.
"""

import math
import pytest
from unittest.mock import patch

import server as well_server
from server import (
    well_check_repair,
    _validate_machine_telemetry,
    _classify_machine_operation,
    _evaluate_machine_task_readiness,
)


def _valid_telemetry_fixture():
    return {
        "m_well_verdict": "HEALTHY",
        "m_well_score": 90,
        "has_telemetry": True,
        "telemetry_source": "prometheus://node-exporter+vitality_gate",
        "telemetry_status": "FULL",
        "telemetry_age_seconds": 15.0,
        "risk_level": "GREEN",
        "memory_psi_some_avg10": 1.2,
        "memory_psi_full_avg10": 0.4,
        "iowait_pct": 2.1,
        "mem_available_pct": 45.0,
        "swap_used_pct": 82.0,
    }


# ── Test 1: Machine task with operator telemetry present ────────────────────
def test_machine_task_with_operator_telemetry_present(monkeypatch, tmp_path):
    """Machine evidence evaluation must not depend on absence of body telemetry.
    If operator is tired, a machine task still evaluates against machine telemetry."""
    # Write state WITH operator body telemetry
    state_file = tmp_path / "well-state.json"
    state_file.write_text(
        '{"truth_status":"MEASURED","environment":"PROD",'
        '"operator_id":"arif","metrics":{"cognitive":{"decision_fatigue":8}},'
        '"well_score":65.0,"reason":"operator tired"}'
    )
    monkeypatch.setattr(well_server, "STATE_PATH", state_file)
    monkeypatch.setattr(well_server, "_build_machine_enrichment", _valid_telemetry_fixture)

    res = well_check_repair(mode="precheck", task_description="check disk space on VPS")
    obs = res.get("observation", {})
    exec_block = obs.get("execution", {})

    assert obs.get("machine_readiness") == "HEALTHY"
    assert obs.get("status") == "PASS"
    assert exec_block.get("human_confirmation_required") is False


# ── Test 2: Machine task with operator telemetry absent ─────────────────────
def test_machine_task_with_operator_telemetry_absent(monkeypatch, tmp_path):
    """When operator telemetry is absent, human_readiness is UNMEASURED,
    while machine readiness evaluates against machine telemetry."""
    state_file = tmp_path / "well-state.json"
    state_file.write_text(
        '{"truth_status":"INSUFFICIENT_DATA","environment":"PROD",'
        '"operator_id":"arif","metrics":{},"well_score":null}'
    )
    monkeypatch.setattr(well_server, "STATE_PATH", state_file)
    monkeypatch.setattr(well_server, "_build_machine_enrichment", _valid_telemetry_fixture)

    res = well_check_repair(mode="precheck", task_description="check disk space on VPS")
    obs = res.get("observation", {})

    assert obs.get("machine_readiness") == "HEALTHY"
    assert obs.get("human_readiness") == "UNMEASURED"
    assert obs.get("status") == "PASS"


# ── Test 3: Fresh flag with missing pressure/condition fields ───────────────
def test_fresh_flag_with_missing_pressure_fields():
    """Telemetry marked FULL and fresh, but missing required memory_psi_full_avg10
    must be rejected and yield readiness UNKNOWN."""
    tel = _valid_telemetry_fixture()
    del tel["memory_psi_full_avg10"]

    is_valid, reason, _ = _validate_machine_telemetry(tel)
    assert is_valid is False
    assert "memory_psi_full_avg10 missing" in reason

    eval_res = _evaluate_machine_task_readiness("check disk", "read", tel)
    assert eval_res["status"] == "HOLD"
    assert eval_res["machine_readiness"] == "UNKNOWN"
    assert eval_res["human_confirmation_required"] is True


# ── Test 4: Unknown telemetry status ────────────────────────────────────────
def test_unknown_telemetry_status():
    """Telemetry status UNKNOWN or PARTIAL must not be accepted as live evidence."""
    tel = _valid_telemetry_fixture()
    tel["telemetry_status"] = "UNKNOWN"

    is_valid, reason, _ = _validate_machine_telemetry(tel)
    assert is_valid is False
    assert "not FULL" in reason

    eval_res = _evaluate_machine_task_readiness("check disk", "read", tel)
    assert eval_res["status"] == "HOLD"
    assert eval_res["machine_readiness"] == "UNKNOWN"


# ── Test 5: None/string/negative/>100/NaN/infinite measurements ──────────────
@pytest.mark.parametrize("bad_val", [None, "20%", -1.0, 105.0, float("nan"), float("inf"), float("-inf")])
def test_invalid_telemetry_numeric_measurements(bad_val):
    """Numeric measurements must be strictly finite numbers in [0, 100]."""
    tel = _valid_telemetry_fixture()
    tel["memory_psi_full_avg10"] = bad_val

    is_valid, reason, _ = _validate_machine_telemetry(tel)
    assert is_valid is False
    assert "memory_psi_full_avg10" in reason


# ── Test 6: Provider-consumer field mismatch ────────────────────────────────
def test_provider_consumer_field_mismatch():
    """If provider emits completely unexpected payload structure,
    it must fail closed without raising uncaught exceptions."""
    mismatched_payload = {"unexpected_blob": 12345, "status": "ok"}
    is_valid, reason, _ = _validate_machine_telemetry(mismatched_payload)
    assert is_valid is False

    eval_res = _evaluate_machine_task_readiness("clean disk", "destructive", mismatched_payload)
    assert eval_res["status"] == "HOLD"
    assert eval_res["machine_readiness"] == "UNKNOWN"


# ── Test 7: Consequential operation without approval ────────────────────────
def test_consequential_operation_without_approval(monkeypatch):
    """Healthy machine condition + consequential deletion request must NOT authorize
    execution; status must remain HOLD and human_confirmation_required=True."""
    monkeypatch.setattr(well_server, "_build_machine_enrichment", _valid_telemetry_fixture)

    res = well_check_repair(mode="precheck", task_description="clean disk on VPS")
    obs = res.get("observation", {})
    exec_block = obs.get("execution", {})

    assert obs.get("status") == "HOLD"
    assert exec_block.get("human_confirmation_required") is True
    assert "requires explicit human approval" in exec_block.get("next_safe_action", "").lower()


# ── Test 8: Missing evidence despite human approval ─────────────────────────
def test_missing_evidence_despite_human_approval():
    """Human approval does NOT substitute for missing or invalid machine evidence."""
    bad_tel = {"has_telemetry": False}
    eval_res = _evaluate_machine_task_readiness(
        task_description="clean disk",
        decision_class="destructive",
        telemetry=bad_tel,
        operator_approved=True,
    )
    assert eval_res["status"] == "HOLD"
    assert eval_res["task_readiness"] == "UNKNOWN"
    assert eval_res["human_confirmation_required"] is True
    assert "cannot substitute for missing" in eval_res["action_note"]


# ── Test 9: Ambiguous text and unknown structured operation ─────────────────
def test_ambiguous_text_fails_closed_as_consequential():
    """Ambiguous or unknown task text fails closed to UNKNOWN_OPERATION requiring approval."""
    op_class, is_consequential = _classify_machine_operation("run something obscure on machine", None)
    assert op_class == "UNKNOWN_OPERATION"
    assert is_consequential is True

    eval_res = _evaluate_machine_task_readiness(
        task_description="run something obscure on machine",
        decision_class=None,
        telemetry=_valid_telemetry_fixture(),
    )
    assert eval_res["operation_class"] == "UNKNOWN_OPERATION"
    assert eval_res["human_confirmation_required"] is True
    assert eval_res["status"] == "HOLD"


# ── Test 10: Schema compatibility and legacy consumer behavior ──────────────
def test_schema_compatibility_preserved(monkeypatch):
    """Existing callers receive canonical envelope and observation fields."""
    monkeypatch.setattr(well_server, "_build_machine_enrichment", _valid_telemetry_fixture)

    res = well_check_repair(mode="precheck", task_description="check disk space on VPS")
    for key in ("ok", "status", "observation", "signal", "decision_support", "constraints"):
        assert key in res, f"Missing canonical top-level key: {key}"

    obs = res["observation"]
    for key in ("status", "domain_verdict", "risk_level", "execution", "machine_readiness"):
        assert key in obs, f"Missing canonical observation key: {key}"

    assert "human_confirmation_required" in obs["execution"]


# ── Test 11: High swap occupancy alone does not trigger CRITICAL ────────────
def test_high_swap_occupancy_alone_not_critical():
    """High swap occupancy (e.g. 85%) with low PSI pressure must not trigger CRITICAL."""
    tel = _valid_telemetry_fixture()
    tel["swap_used_pct"] = 85.0
    tel["memory_psi_full_avg10"] = 0.2
    tel["m_well_verdict"] = "FUNCTIONAL"
    tel["risk_level"] = "AMBER"

    eval_res = _evaluate_machine_task_readiness("check status", "read", tel)
    assert eval_res["observed_condition"] != "CRITICAL"
    assert eval_res["risk_level"] != "CRITICAL"
