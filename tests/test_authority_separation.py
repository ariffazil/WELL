"""
Authority separation in the human-state plane.

Falsification tests for the F13 order of 2026-09-28 ("fix is_well and stop decision
ceiling"). The defect being closed: is_well() conflated organ-identity integrity with the
operator's self-report, so _ensure_well_identity had to inject *passing* boilerplate
(peace2=1.0, kappa_r=0.95, rasa=True, amanah="LOCK") at top level to keep the organ
serving -- while the operator's real report sat unread in state["biometric"]. Consequence
measured live on 2026-09-28: is_well()==True on a file containing nobody's data, and
is_well()==False if the gate had ever read the actual datum.

These tests assert the two properties that were missing:
  * absence of a report is reported as absence, never as wellness;
  * a human's substrate state cannot cap the sovereign's decision class.
"""

import importlib.util
import os
import tempfile
from pathlib import Path

import pytest

well_dir = Path(__file__).parent.parent
_test_dir = Path(tempfile.mkdtemp(prefix="well-authority-"))
os.environ["WELL_STATE_PATH"] = str(_test_dir / "state.json")
os.environ["WELL_EVENTS_PATH"] = str(_test_dir / "events.jsonl")
os.environ["WELL_VAULT_PATH"] = str(_test_dir / "vault_ledger.jsonl")

_spec = importlib.util.spec_from_file_location(
    "well_authority_server", well_dir / "server.py"
)
assert _spec and _spec.loader
server = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(server)


def _identity(**over):
    """A state that is genuinely, structurally the WELL organ."""
    s = {
        "identity": "WELL",
        "role": "Body / Human Intelligence",
        "authority": "REFLECT_ONLY",
        "operator_id": "arif",
        "metrics": {},
        "well_score": None,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }
    s.update(over)
    return s


# ── is_well() is an identity check, nothing else ──────────────────────────────

def test_is_well_true_with_zero_operator_data():
    """No report at all must not make the organ unhealthy. It was this inverted
    pressure that forced the boilerplate injection in the first place."""
    assert server.is_well(_identity()) is True


def test_is_well_indifferent_to_operator_mood():
    """A tired, low-peace operator does not corrupt the organ. Before the fix the
    first of these returned False and would have emitted LOW_CAPACITY + a C1 ceiling."""
    low = _identity(delta_s=0.9, peace2=0.1, kappa_r=0.0, rasa="raw", amanah=0.1)
    high = _identity(delta_s=0.0, peace2=1.0, kappa_r=1.0, rasa=True, amanah="LOCK")
    assert server.is_well(low) is server.is_well(high) is True


def test_is_well_still_detects_impersonation():
    """Stripping the human fields must not have disarmed the identity check itself."""
    assert server.is_well(_identity(authority="MUTATE")) is False
    assert server.is_well(_identity(identity="NOT-WELL")) is False
    assert server.is_well(_identity(role="Execution Engine")) is False
    assert server.is_well({"metrics": {}}) is False  # needs migration, not corrupt


# ── the operator's own state, with provenance ─────────────────────────────────

def test_injected_defaults_are_reported_as_absence_not_wellness():
    s = _identity(
        delta_s=0.0, peace2=1.0, kappa_r=0.95, rasa=True, amanah="LOCK",
        _identity_defaults_injected=["delta_s", "peace2", "kappa_r", "rasa", "amanah"],
    )
    d = server._human_datum(s)
    assert d["operator_datum_present"] is False
    assert d["provenance"] == "NO_OPERATOR_DATUM"
    assert set(d["absent_fields"]) == {
        "delta_s", "peace2", "kappa_r", "rasa", "amanah"
    }
    assert d["observed"] == {}
    assert d["authority"] == "REFLECT_ONLY"


def test_real_report_is_read_from_biometric_block():
    s = _identity(biometric={"peace2": 0.9, "kappa_r": 0.85, "rasa": "ready",
                             "amanah": 0.95, "delta_s": 0.1},
                  truth_status="OPERATOR_REPORTED")
    d = server._human_datum(s)
    assert d["operator_datum_present"] is True
    assert d["provenance"] == "OPERATOR_SELF_REPORT"
    assert d["sensor_verified"] is False
    assert d["observed"]["peace2"] == 0.9
    assert d["absent_fields"] == []


def test_live_file_regression_boilerplate_cannot_mask_the_human():
    """Exactly the shape observed in /var/lib/well/state.json on 2026-09-28:
    injected peace2=1.0 at top level, the real 0.9 one dict deeper. The gate must
    report the human, not the boilerplate."""
    s = _identity(
        peace2=1.0, kappa_r=0.95, rasa=True, amanah="LOCK", delta_s=0.0,
        _identity_defaults_injected=["delta_s", "peace2", "kappa_r", "rasa", "amanah"],
        biometric={"delta_s": 0.1, "peace2": 0.9, "kappa_r": 0.85,
                   "rasa": "ready", "amanah": 0.95},
        truth_status="OPERATOR_REPORTED",
    )
    d = server._human_datum(s)
    assert d["observed"]["peace2"] == 0.9, "boilerplate leaked into the reported human"
    assert d["observed"]["rasa"] == "ready", "bool default overwrote a real string"
    assert d["provenance"] == "OPERATOR_SELF_REPORT"
    # Nothing had to be stripped: every field came from a genuine report.
    assert d["injected_defaults_stripped"] == []
    assert d["absent_fields"] == []


def test_boilerplate_only_state_is_stripped_and_listed():
    """When the ONLY values are injected defaults, they are stripped and named."""
    s = _identity(
        peace2=1.0, kappa_r=0.95, rasa=True, amanah="LOCK", delta_s=0.0,
        _identity_defaults_injected=["delta_s", "peace2", "kappa_r", "rasa", "amanah"],
    )
    d = server._human_datum(s)
    assert d["injected_defaults_stripped"] == [
        "amanah", "delta_s", "kappa_r", "peace2", "rasa"
    ]
    assert d["provenance"] == "NO_OPERATOR_DATUM"
    assert d["observed"] == {}


def test_partial_biometric_strips_only_what_it_must():
    s = _identity(
        peace2=1.0, amanah="LOCK",
        _identity_defaults_injected=["peace2", "amanah"],
        biometric={"peace2": 0.4},
        truth_status="OPERATOR_REPORTED",
    )
    d = server._human_datum(s)
    assert d["observed"]["peace2"] == 0.4
    assert d["injected_defaults_stripped"] == ["amanah"]
    assert d["absent_fields"] == ["amanah", "delta_s", "kappa_r", "rasa"]
    assert d["provenance"] == "PARTIAL_DEFAULTS_STRIPPED"


# ── decision ceiling: WELL does not cap the sovereign ─────────────────────────

def _telemetry_state(**over):
    """A state that genuinely counts as verified body telemetry, so that
    _compute_decision_ceiling walks its full mapping instead of returning early."""
    s = _identity(
        truth_status="VERIFIED",
        metrics={"sleep": {"sleep_hours": 4, "sleep_debt_days": 9},
                 "stress": {"subjective_load": 10},
                 "cognitive": {"clarity": 0, "decision_fatigue": 10},
                 "structural": {"pain_level": 10, "sedentary_hours_continuous": 12}},
    )
    s.update(over)
    return s


@pytest.mark.parametrize("state", [
    _identity(),                                                   # no telemetry
    _identity(floors_violated=["F1", "F2", "F3", "F4"]),           # many violations
    _identity(metrics={"sleep": {"sleep_debt_days": 9},
                       "stress": {"subjective_load": 10},
                       "cognitive": {"clarity": 0, "decision_fatigue": 10},
                       "structural": {"pain_level": 10,
                                      "sedentary_hours_continuous": 12}}),  # worst case
    _telemetry_state(),                                            # worst + verified
    _telemetry_state(floors_violated=["F1"] * 9),                   # worst + breaches
])
def test_no_state_of_the_operator_yields_a_decision_ceiling(state):
    r = server._compute_decision_ceiling(state)
    assert r["decision_ceiling"] is None
    assert "arifOS" in r["ceiling_authority"]


def test_verified_worst_case_still_reflects_without_capping():
    """This is the case the old code answered with decision_ceiling="C0" -- no
    decision class open to the sovereign. It must now report the substrate and
    leave the class alone."""
    r = server._compute_decision_ceiling(_telemetry_state())
    assert r["ground_state"] in ("DEGRADED", "UNSAFE"), r
    assert r["decision_ceiling"] is None
    assert "arifOS" in r["ceiling_authority"]


def test_resolve_readiness_emits_no_c_class_cap():
    r = server._resolve_readiness(_telemetry_state(floors_violated=["F1"] * 9))
    assert r.get("decision_ceiling") is None, r.get("decision_ceiling")


def test_stale_data_refuses_inference_without_revoking_authority():
    """The 168h hard boundary must say 'I cannot know', not 'you may not decide'."""
    r = server._check_human_readiness_168h_ceiling(
        _identity(timestamp="2020-01-01T00:00:00+00:00")
    )
    assert r is not None
    assert r["ceiling_168h"] == "BREACHED"
    assert r["readiness"] in ("UNKNOWN", "DO_NOT_INFER")
    assert r["decision_ceiling"] is None
    assert "cannot infer" in r["reason"].lower()
