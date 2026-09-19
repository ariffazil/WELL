"""Claim-class gate tests for WELL — the human-substrate organ.

Covers the explanatory-class gate (claim_kernel/v1) at WELL's record and report
points, and its integration with WELL's existing dignity guard.

The three required properties:
  1. a NARRATIVE statement about a person is NOT returned as an assessment;
  2. a MEASURED statement IS;
  3. UNDECLARED fails closed.

Plus the dignity-guard interaction: the guard can only ever REMOVE assessment
eligibility, and its at-risk verdict is never withheld.

provenance: receipt_id WELL-CLAIMCLASS-GATE-20260919
evidence: /root/WELL/claim_class_gate.py  /root/WELL/tools_sot.yaml
"""

from __future__ import annotations

import sys
from pathlib import Path

WELL_ROOT = Path(__file__).resolve().parents[1]
if str(WELL_ROOT) not in sys.path:
    sys.path.insert(0, str(WELL_ROOT))

import server as well_server  # noqa: E402
from claim_class_gate import (  # noqa: E402
    ACTION_ELIGIBLE_CLASSES,
    CLAIM_CLASSES,
    NON_ASSESSMENT_CLASSES,
    evaluate_claim_class,
    gate_human_claim,
    must_not_return_as_assessment,
)

# A plain sentence about a person's state that carries no mechanism and no
# measure: the class of claim this gate exists for.
NARRATIVE_SENTENCE = "Arif is burned out and avoiding his family"
# A number with a stated source: action-eligible.
MEASURED_SENTENCE = "hrv_ms=42 measured by the oura ring at 2026-09-19T07:00:00Z"


def _federation_observation(result: dict) -> dict:
    """The inner observation of a _to_federation_output payload."""
    obs = result.get("observation")
    if isinstance(obs, dict) and isinstance(obs.get("observation"), dict):
        return obs["observation"]
    return obs or {}


def _federation_gate(result: dict) -> dict:
    obs = result.get("observation") or {}
    gate = obs.get("claim_class_gate")
    if isinstance(gate, dict):
        return gate
    gate = result.get("claim_class_gate")
    return gate if isinstance(gate, dict) else {}


# ── 1. NARRATIVE about a person is not returned as an assessment ─────────────


def test_narrative_statement_is_not_returned_as_an_assessment():
    verdict = gate_human_claim(NARRATIVE_SENTENCE, "NARRATIVE")

    assert verdict["returned_as_assessment"] is False
    assert verdict["assessment_refused"] is True
    assert verdict["verdict"] == "CLAIM_CLASS_NOT_ACTION_ELIGIBLE"
    # it may still be logged — logging is not the thing being refused
    assert verdict["statement_logged"] is True
    assert verdict["refusal"]["may_be_logged"] is True
    assert verdict["refusal"]["drives_recommendation"] is False


def test_narrative_intake_record_is_logged_but_not_assessed():
    result = well_server.well_log(
        note=NARRATIVE_SENTENCE,
        claim_class="NARRATIVE",
    )

    assert result["ok"] is True
    assert result["assessment_eligible"] is False
    assert result["recommendation"] is None
    assert result["recommendation_status"] == "WITHHELD_CLAIM_CLASS"
    # nothing is deleted: the advisory is held, not destroyed
    assert isinstance(result.get("readiness_advisory_held"), str)
    assert result["claim_class_refusal"]["code"] == (
        "CLAIM_CLASS_NOT_RETURNABLE_AS_ASSESSMENT"
    )
    # the sentence IS recorded
    events_path = Path(well_server.EVENTS_PATH)
    assert events_path.exists()
    assert any(
        "WELL_LOG" in line for line in events_path.read_text().splitlines() if line
    )


def test_narrative_shadow_report_is_withheld():
    result = well_server.well_guard_dignity(
        mode="shadow",
        subject="Arif",
        claim_class="NARRATIVE",
    )

    observation = _federation_observation(result)
    assert result["signal"] == "assessment_withheld"
    assert observation["assessment_eligible"] is False
    assert observation["assessment_withheld"] is True
    assert _federation_gate(result)["returned_as_assessment"] is False


def test_must_not_return_as_assessment_helper_matches_the_gate():
    assert must_not_return_as_assessment(NARRATIVE_SENTENCE, "NARRATIVE") is True
    assert must_not_return_as_assessment(MEASURED_SENTENCE, "MEASURED") is False


# ── 2. MEASURED is returned as an assessment ─────────────────────────────────


def test_measured_statement_is_returned_as_an_assessment():
    verdict = gate_human_claim(MEASURED_SENTENCE, "MEASURED")

    assert verdict["returned_as_assessment"] is True
    assert verdict["assessment_refused"] is False
    assert verdict["verdict"] == "CLAIM_CLASS_ACTION_ELIGIBLE"
    assert verdict["refusal"] is None


def test_measured_telemetry_record_keeps_its_assessment_and_recommendation():
    result = well_server.well_log(
        sleep_hours=8.0,
        clarity=9.0,
        claim_class="MEASURED",
    )

    assert result["assessment_eligible"] is True
    assert isinstance(result["recommendation"], str)
    assert result["recommendation_status"] == "ASSESSMENT"
    assert "readiness_advisory_held" not in result
    # legacy fields that existing callers depend on are untouched
    assert result["tier"] in ("GREEN", "AMBER", "RED")
    assert "human_decision_required" in result


def test_measured_dignity_report_returns_a_clear_signal():
    result = well_server.well_guard_dignity(
        mode="consent",
        dignity_preservation=0.85,
        claim_class="MEASURED",
    )

    observation = _federation_observation(result)
    assert result["signal"] == "consent_clear"
    assert observation["assessment_eligible"] is True
    assert isinstance(observation["recommendation"], str)


# ── 3. UNDECLARED fails closed ───────────────────────────────────────────────


def test_undeclared_claim_class_fails_closed_at_the_gate():
    for undeclared in (None, "", "   "):
        verdict = gate_human_claim(MEASURED_SENTENCE, undeclared)
        assert verdict["returned_as_assessment"] is False
        assert verdict["verdict"] == "CLAIM_CLASS_NOT_DECLARED"
        assert verdict["refusal"]["may_be_logged"] is True


def test_unknown_claim_class_fails_closed():
    verdict = gate_human_claim(MEASURED_SENTENCE, "BANANA")
    assert verdict["returned_as_assessment"] is False
    assert evaluate_claim_class(MEASURED_SENTENCE, "BANANA")["action_eligible"] is False


def test_undeclared_telemetry_record_fails_closed():
    result = well_server.well_log(sleep_hours=8.0, clarity=9.0)

    assert result["assessment_eligible"] is False
    assert result["claim_class"] == "UNCLASSIFIED"
    assert result["recommendation"] is None
    assert result["recommendation_status"] == "WITHHELD_CLAIM_CLASS"
    assert result["claim_class_refusal"]["refused"] is True


def test_undeclared_dignity_report_fails_closed():
    result = well_server.well_guard_dignity(
        mode="consent",
        dignity_preservation=0.85,
    )
    observation = _federation_observation(result)
    assert result["signal"] == "assessment_withheld"
    assert observation["assessment_eligible"] is False
    assert _federation_gate(result)["declared"] == "UNCLASSIFIED"


def test_every_narrative_class_fails_closed_and_undeclared_never_opens():
    for cls in NON_ASSESSMENT_CLASSES:
        assert gate_human_claim(MEASURED_SENTENCE, cls)["returned_as_assessment"] is False
    # A declared action-eligible class is the ONLY way through — and the
    # declaration must match what the sentence actually reads as
    # (claim_kernel's mismatch lint), so each class gets its own sentence.
    class_sentences = {
        "MEASURED": MEASURED_SENTENCE,
        "MECHANISM": "because of accumulated sleep debt the recovery score dropped",
        "PATTERN": "Arif always crashes after big forges",
    }
    assert set(class_sentences) == set(ACTION_ELIGIBLE_CLASSES)
    for cls, sentence in class_sentences.items():
        assert gate_human_claim(sentence, cls)["returned_as_assessment"] is True, cls
    # misdeclaring an action-eligible class is refused too (mismatch lint)
    assert (
        gate_human_claim(MEASURED_SENTENCE, "MECHANISM")["returned_as_assessment"]
        is False
    )
    assert set(CLAIM_CLASSES) == set(ACTION_ELIGIBLE_CLASSES) | set(NON_ASSESSMENT_CLASSES)


# ── 4. Dignity guard interaction — the guard is never weakened ───────────────


def test_dignity_hold_forces_refusal_for_every_action_eligible_class():
    """The dignity guard can only REMOVE eligibility. It can never be overridden
    by a declared class — this is the one-way interaction."""
    labelling = "Arif is avoidant"
    for cls in ACTION_ELIGIBLE_CLASSES:
        verdict = gate_human_claim(labelling, cls)
        assert verdict["returned_as_assessment"] is False, cls
        assert verdict["verdict"] == "CLAIM_CLASS_DIGNITY_HOLD", cls
        assert verdict["dignity"]["tier"] == "HOLD", cls
        assert verdict["refusal"]["dignity_hold"] is True, cls


def test_dignity_guard_verdict_is_passed_through_verbatim():
    supplied = {
        "tier": "HOLD",
        "violations": ["FATAL:\\bis\\s+avoidant\\b"],
        "notes": ["F05 PEACE: Diagnostic language detected."],
        "safe_rephrase_hint": "Rephrase as pattern observation.",
    }
    verdict = gate_human_claim(
        "Arif is avoidant", "MEASURED", dignity=supplied
    )
    assert verdict["dignity"] == supplied
    assert verdict["dignity_guard_unchanged"] is True
    assert verdict["dignity_guard_authority"] == (
        "gate/dignity_shadow.assess_dignity_risk"
    )


def test_dignity_at_risk_verdict_is_retained_under_a_refusal():
    """The guard's at-risk instruction is a SAFETY output, not an assessment:
    the claim-class refusal must not hide it."""
    result = well_server.well_guard_dignity(
        mode="consent",
        dignity_preservation=0.1,
        claim_class="NARRATIVE",
    )
    observation = _federation_observation(result)
    assert result["signal"] == "consent_at_risk"
    assert "dignity_preservation_low" in observation["flags"]
    assert observation["dignity_guard_instruction_retained"] is True
    assert isinstance(observation["dignity_guard_instruction"], str)


def test_shadow_hold_verdict_is_retained_under_a_refusal():
    result = well_server.well_guard_dignity(
        mode="shadow",
        subject="Arif",
        coercion_signals=["he is avoidant"],
        claim_class="MEASURED",
    )
    observation = _federation_observation(result)
    assert observation["tier"] == "HOLD"
    assert observation["violations"]
    assert observation["dignity_guard_verdict_retained"] is True
    assert result["signal"] == "shadow_flagged"


# ── 5. The gate never labels a person ───────────────────────────────────────


def test_gate_never_attaches_a_class_to_a_person():
    for text, cls in (
        (NARRATIVE_SENTENCE, "NARRATIVE"),
        (MEASURED_SENTENCE, "MEASURED"),
        (MEASURED_SENTENCE, None),
        ("Arif is avoidant", "MEASURED"),
    ):
        verdict = gate_human_claim(text, cls, subject="Arif")
        assert verdict["person_label_assigned"] is False
        assert verdict["governs"] == "EPISTEMIC_CLASS_OF_A_SENTENCE_ABOUT_A_PERSON"
        # `subject` is provenance only — it is never classified
        assert verdict["subject"] == "Arif"


# ── 6. Triad intake record point ────────────────────────────────────────────


def test_intake_records_the_event_even_when_the_claim_is_narrative(monkeypatch):
    # Capture the typed-event payload directly: WELL has more than one live
    # module instance of server.py under pytest (conftest imports it; test_well
    # loads it by path), and the typed event chain binds whichever imported last.
    # Asserting on the payload is deterministic where asserting on a file is not.
    import well_triad.events as wt_events

    captured: list = []
    monkeypatch.setattr(wt_events, "_native_append_event", captured.append)

    result = well_server.well_log_intake(
        meal_label="nasi lemak",
        kcal=700.0,
        source="manual",
        claim_class="NARRATIVE",
    )

    assert result["ok"] is True
    assert result["event_id"]
    assert result["assessment_eligible"] is False
    assert result["claim_class"] == "NARRATIVE"
    assert result["claim_class_refusal"]["may_be_logged"] is True

    intake = [e for e in captured if e.get("event") == "WELL_TRIAD_1_INTAKE"]
    assert intake, "the intake event must be recorded even when the claim is refused"
    assert intake[-1]["claim_class"] == "NARRATIVE"


def test_intake_undeclared_fails_closed():
    result = well_server.well_log_intake(
        meal_label="nasi lemak",
        kcal=700.0,
        source="manual",
    )
    assert result["ok"] is True
    assert result["assessment_eligible"] is False
    assert result["claim_class"] == "UNCLASSIFIED"


# ── 7. Outage still fails closed ────────────────────────────────────────────


def test_gate_fails_closed_when_claim_kernel_is_unreachable(monkeypatch):
    """An unreachable kernel must not open the gate. The membership rule is
    still enforced locally and `degraded` records that the lint was skipped."""
    import claim_class_gate as ccg

    monkeypatch.setattr(ccg, "CLAIM_KERNEL_PATH", "/nonexistent/claim-kernel")
    monkeypatch.setattr(ccg, "_CLAIM_KERNEL_CACHE", {"loaded": True, "module": None})

    ok = ccg.gate_human_claim(MEASURED_SENTENCE, "MEASURED")
    assert ok["returned_as_assessment"] is True
    assert ok["degraded"] is True
    assert ok["kernel"] == "local-fallback"

    assert (
        ccg.gate_human_claim(MEASURED_SENTENCE, "NARRATIVE")["returned_as_assessment"]
        is False
    )
    assert ccg.gate_human_claim(MEASURED_SENTENCE, None)["returned_as_assessment"] is False


def test_gate_fails_closed_when_the_gate_module_is_unreachable(monkeypatch):
    """An unavailable gate must not read as an available one."""
    monkeypatch.setattr(well_server, "_CLAIM_CLASS_GATE_MODULE", None)

    result = well_server.well_log(sleep_hours=8.0, clarity=9.0, claim_class="MEASURED")
    assert result["assessment_eligible"] is False
    assert result["recommendation"] is None
    assert result["recommendation_status"] == "WITHHELD_CLAIM_CLASS"
    assert result["claim_class_gate"]["verdict"] == "CLAIM_CLASS_GATE_ERROR"
    assert result["claim_class_refusal"]["may_be_logged"] is True
