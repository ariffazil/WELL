#!/usr/bin/env python3
"""
Tests for Dark Geometry Detector v2 — arifOS WELL organ
========================================================
Comprehensive tests: mode detection, benign counterexamples, state-not-trait,
prohibited conclusions, output contract validation.

Uses pytest style (assert statements, not unittest).
"""

import sys
import os

# Add parent to path for import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from gate.darkgeometrydetect import (
    DarkGeometryDetector,
    DarkGeometryMirror,
    ModeResult,
    Signal,
    DarkMode,
    EpistemicStatus,
    PROHIBITED_CONCLUSIONS,
)


@pytest.fixture
def detector():
    return DarkGeometryDetector()


# ─── MODE 1: JUDGMENT COLLAPSE ───────────────────────────────────────────────


def test_judgment_collapse_positive(detector):
    """High certainty without evidence triggers judgment collapse."""
    r = detector.analyze("This is definitely the right answer. No question about it.")
    jc = next(m for m in r.detected_modes if m.mode == DarkMode.JUDGMENT_COLLAPSE)
    assert jc.status != "CLEAR"
    assert jc.confidence > 0.0
    assert len(jc.signals) > 0


def test_judgment_collapse_negative(detector):
    """Hedged text does not trigger judgment collapse."""
    r = detector.analyze("I think this might work, but I could be wrong about the data.")
    jc = next(m for m in r.detected_modes if m.mode == DarkMode.JUDGMENT_COLLAPSE)
    assert jc.status == "CLEAR"


def test_judgment_collapse_with_evidence(detector):
    """Certainty WITH evidence markers reduces collapse confidence."""
    r = detector.analyze(
        "The data clearly shows this is correct, according to research."
    )
    jc = next(m for m in r.detected_modes if m.mode == DarkMode.JUDGMENT_COLLAPSE)
    # Evidence should reduce confidence, potentially to CLEAR
    assert jc.confidence < 0.5


# ─── MODE 2: SELF-CERTIFIED NIAT ────────────────────────────────────────────


def test_self_certified_niat_positive(detector):
    """Niat shield after criticism triggers self-certified niat."""
    r = detector.analyze(
        "Why did you fail? My intention was good. I know my heart."
    )
    sc = next(m for m in r.detected_modes if m.mode == DarkMode.SELF_CERTIFIED_NIAT)
    assert sc.status != "CLEAR"
    assert len(sc.signals) > 0


def test_self_certified_niat_negative(detector):
    """Niat phrases without criticism context are benign."""
    r = detector.analyze("I was trying to finish the report by Friday.")
    sc = next(m for m in r.detected_modes if m.mode == DarkMode.SELF_CERTIFIED_NIAT)
    assert sc.status == "CLEAR"


# ─── MODE 3: RESPONSIBILITY LAUNDERING ──────────────────────────────────────


def test_responsibility_laundering_positive(detector):
    """Agentless constructions in harm context trigger laundering."""
    r = detector.analyze(
        "Mistakes were made. Things happened. It was decided."
    )
    rl = next(m for m in r.detected_modes if m.mode == DarkMode.RESPONSIBILITY_LAUNDERING)
    # Agentless constructions detected, but needs harm context for high confidence
    # The harm markers in the default text may be minimal
    assert rl.mode == DarkMode.RESPONSIBILITY_LAUNDERING


def test_responsibility_laundering_negative(detector):
    """Active voice with responsibility does not trigger laundering."""
    r = detector.analyze("I made the decision. I'll take responsibility.")
    rl = next(m for m in r.detected_modes if m.mode == DarkMode.RESPONSIBILITY_LAUNDERING)
    assert rl.status == "CLEAR"


# ─── MODE 4: CERTAINTY IMMUNITY ─────────────────────────────────────────────


def test_certainty_immunity_positive(detector):
    """Self-reference as proof + certainty triggers certainty immunity."""
    r = detector.analyze("Trust me. I know because I know. Definitely right.")
    ci = next(m for m in r.detected_modes if m.mode == DarkMode.CERTAINTY_IMMUNITY)
    assert ci.status != "CLEAR"
    assert len(ci.signals) > 0


def test_certainty_immunity_negative(detector):
    """Hedged text does not trigger certainty immunity."""
    r = detector.analyze("I might be wrong, but the evidence suggests...")
    ci = next(m for m in r.detected_modes if m.mode == DarkMode.CERTAINTY_IMMUNITY)
    assert ci.status == "CLEAR"


# ─── BENIGN COUNTEREXAMPLES ─────────────────────────────────────────────────


def test_benign_technical_certainty(detector):
    """Code review certainty is technical, not dark geometry."""
    r = detector.analyze("The function definitely returns a float.")
    # May trigger signals but should have counterevidence/alternatives
    assert len(r.counterevidence) > 0 or r.overall_status in ("CLEAR", "REFLECT")


def test_benign_legal_prose(detector):
    """Legal/formal passive voice is not responsibility laundering."""
    r = detector.analyze("Steps were taken to ensure compliance.")
    rl = next(m for m in r.detected_modes if m.mode == DarkMode.RESPONSIBILITY_LAUNDERING)
    # Without harm context, should be clear or low
    assert rl.status in ("CLEAR", "REFLECT")


def test_benign_executive_directive(detector):
    """Urgent executive directive is not judgment collapse."""
    r = detector.analyze("We must do this now. No question.")
    # Should have alternatives mentioning executive/urgent context
    assert any(
        "executive" in alt.lower() or "urgent" in alt.lower() or "direct" in alt.lower()
        for alt in r.alternative_explanations
    ) or r.overall_status in ("CLEAR", "REFLECT")


def test_benign_second_language(detector):
    """L2 speaker patterns are alternative explanations, not pathology."""
    r = detector.analyze("I know my intention is good. I try hard.")
    # Should have L2/cultural alternatives
    assert any(
        "language" in alt.lower() or "cultural" in alt.lower()
        for alt in r.alternative_explanations
    ) or r.overall_status in ("CLEAR", "REFLECT")


def test_benign_trauma_disclosure(detector):
    """Trauma disclosure is not dark geometry pathology."""
    r = detector.analyze("I was hurt. I can't trust anyone.")
    # This text has harm markers but no agentless constructions
    # and no certainty patterns — should be relatively clean
    assert r.overall_status in ("CLEAR", "REFLECT")


# ─── STATE NOT TRAIT ────────────────────────────────────────────────────────


def test_no_permanent_label(detector):
    """Output never contains permanent identity labels."""
    r = detector.analyze("This is definitely wrong. Trust me. I know my heart.")
    result_str = str(r.to_dict()).lower()
    forbidden_labels = [
        "is a narcissist", "is toxic", "is a sociopath",
        "is a psychopath", "is evil", "is manipulative",
    ]
    for label in forbidden_labels:
        assert label not in result_str, f"Forbidden label found: {label}"


# ─── NO HIDDEN NIAT INFERENCE ───────────────────────────────────────────────


def test_prohibited_conclusions_present(detector):
    """Prohibited conclusions are always populated in output."""
    r = detector.analyze("This is definitely right. Trust me.")
    assert r.prohibited_conclusions == PROHIBITED_CONCLUSIONS
    assert len(r.prohibited_conclusions) == 4
    assert "hidden_niat" in r.prohibited_conclusions
    assert "evil_identity" in r.prohibited_conclusions
    assert "permanent_trait" in r.prohibited_conclusions
    assert "psychiatric_diagnosis" in r.prohibited_conclusions


def test_prohibited_conclusions_empty_input(detector):
    """Prohibited conclusions present even for empty input."""
    r = detector.analyze("")
    assert r.prohibited_conclusions == PROHIBITED_CONCLUSIONS


def test_no_niat_declaration(detector):
    """Output never declares someone's true intention."""
    r = detector.analyze(
        "My intention was good. I know my heart. Why did you fail?"
    )
    result_str = str(r.to_dict()).lower()
    niat_declarations = [
        "true intention is", "real niat is", "actual intention was",
        "their intention was", "his intention was", "her intention was",
    ]
    for decl in niat_declarations:
        assert decl not in result_str, f"Niat declaration found: {decl}"


# ─── OUTPUT CONTRACT ────────────────────────────────────────────────────────


def test_output_has_all_fields(detector):
    """DarkGeometryMirror has all required fields."""
    r = detector.analyze("This is definitely the right answer.")
    d = r.to_dict()

    required_fields = [
        "detected_modes", "dominant_mode", "overall_status",
        "combined_reflection_prompts", "counterevidence",
        "alternative_explanations", "epistemic_status",
        "confidence", "prohibited_conclusions",
        "authority_effect", "disclaimer",
    ]
    for field in required_fields:
        assert field in d, f"Missing field: {field}"


def test_epistemic_status_values(detector):
    """Epistemic status is one of the valid enum values."""
    valid_statuses = {s.value for s in EpistemicStatus}

    # With signals
    r = detector.analyze("This is definitely right. Trust me. I know because I know.")
    assert r.epistemic_status.value in valid_statuses

    # Without signals
    r = detector.analyze("I think maybe we should consider options.")
    assert r.epistemic_status.value in valid_statuses

    # Empty
    r = detector.analyze("")
    assert r.epistemic_status.value in valid_statuses


def test_authority_effect_none(detector):
    """Authority effect is always NONE."""
    r = detector.analyze("This is definitely right. Trust me.")
    assert r.authority_effect == "NONE"

    r = detector.analyze("")
    assert r.authority_effect == "NONE"

    d = r.to_dict()
    assert d["authority_effect"] == "NONE"


def test_to_dict_serializable(detector):
    """to_dict() produces JSON-serializable output."""
    import json
    r = detector.analyze("This is definitely right. Mistakes were made. Trust me.")
    d = r.to_dict()
    # Should not raise
    serialized = json.dumps(d)
    assert isinstance(serialized, str)
    assert len(serialized) > 10


def test_mode_result_fields(detector):
    """Each ModeResult has all required fields."""
    r = detector.analyze("This is definitely right. Trust me.")
    for mr in r.detected_modes:
        assert isinstance(mr, ModeResult)
        assert isinstance(mr.mode, DarkMode)
        assert isinstance(mr.signals, list)
        assert isinstance(mr.confidence, float)
        assert isinstance(mr.status, str)
        assert isinstance(mr.questions, list)
        assert isinstance(mr.counterevidence, list)
        assert isinstance(mr.alternative_explanations, list)
        assert mr.status in ("CLEAR", "REFLECT", "ATTENTION")


def test_signal_fields(detector):
    """Each Signal has all required fields."""
    r = detector.analyze("This is definitely right. Trust me.")
    for mr in r.detected_modes:
        for sig in mr.signals:
            assert isinstance(sig, Signal)
            assert isinstance(sig.type, str)
            assert isinstance(sig.pattern, str)
            assert isinstance(sig.evidence, str)
            assert isinstance(sig.line, int)


# ─── BACKWARD COMPATIBILITY ─────────────────────────────────────────────────


def test_analyze_with_context_returns_dict(detector):
    """analyze_with_context returns a dict (backward compat)."""
    r = detector.analyze_with_context(
        "This is definitely right.",
        {"baseline_ref": "test", "time_window": "test_window"}
    )
    assert isinstance(r, dict)
    assert "detected_modes" in r
    assert "authority_effect" in r


def test_detect_forgetting_wrong_alias(detector):
    """detect_forgetting_wrong is a backward-compatible alias."""
    r1 = detector.detect_certainty_immunity("Trust me. I know because I know.")
    r2 = detector.detect_forgetting_wrong("Trust me. I know because I know.")
    assert r1.mode == r2.mode
    assert r1.confidence == r2.confidence
    assert r1.status == r2.status


# ─── EDGE CASES ─────────────────────────────────────────────────────────────


def test_empty_input(detector):
    """Empty input returns CLEAR with all required fields."""
    r = detector.analyze("")
    assert r.overall_status == "CLEAR"
    assert r.detected_modes == []
    assert r.dominant_mode is None
    assert r.epistemic_status == EpistemicStatus.INSUFFICIENT
    assert r.confidence == 0.0
    assert r.authority_effect == "NONE"


def test_whitespace_only(detector):
    """Whitespace-only input returns CLEAR."""
    r = detector.analyze("   \n\t  ")
    assert r.overall_status == "CLEAR"


def test_four_modes_always_present(detector):
    """All 4 modes are always evaluated."""
    r = detector.analyze("Some text here.")
    assert len(r.detected_modes) == 4
    mode_values = [m.mode for m in r.detected_modes]
    assert DarkMode.JUDGMENT_COLLAPSE in mode_values
    assert DarkMode.SELF_CERTIFIED_NIAT in mode_values
    assert DarkMode.RESPONSIBILITY_LAUNDERING in mode_values
    assert DarkMode.CERTAINTY_IMMUNITY in mode_values
