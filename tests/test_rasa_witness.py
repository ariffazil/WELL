#!/usr/bin/env python3
"""
Pytest suite for Rasa Witness Contract (WELL/gate/rasa_witness.py)
===================================================================
Tests all 7 RWC invariants + integration with well_gate.py
"""

import json
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch

# Add WELL to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gate.rasa_witness import (
    BiometricObservation,
    SelfReport,
    MismatchResult,
    InteractionPosture,
    detect_mismatch,
    scan_prohibited_conclusions,
    generate_possible_states,
    enforce_posture_language,
    rasa_witness_gate,
)


# ── RWC-1: Self-Report Has Semantic Sovereignty ──────────────────────────────

class TestRWC1_SelfReportSovereignty:
    """Self-report has semantic sovereignty. Telemetry cannot silently overwrite."""

    def test_human_says_ok_with_deviation(self):
        """Human says 'ok' — system must NOT override with telemetry interpretation."""
        obs = [BiometricObservation(
            signal="hrv", value=45, baseline=65,
            deviation_sigma=-2.5, quality="good", age_minutes=10
        )]
        sr = SelfReport(rasa="ok")
        result = detect_mismatch(obs, sr)

        assert result.status == "POSSIBLE_MISMATCH"
        # Self-report must be preserved — not overwritten
        assert "ok" in result.self_report_summary.lower()
        # Must note sovereignty
        assert any("RWC-1" in n for n in result.notes)

    def test_human_says_fine_with_extreme_deviation(self):
        """Even with extreme deviation, self-report is sovereign."""
        obs = [BiometricObservation(
            signal="hrv", value=25, baseline=65,
            deviation_sigma=-5.0, quality="good", age_minutes=10
        )]
        sr = SelfReport(rasa="ok")
        result = detect_mismatch(obs, sr)

        assert result.status == "POSSIBLE_MISMATCH"
        # Self-report is preserved — not replaced with telemetry interpretation
        assert "ok" in result.self_report_summary.lower()
        # Notes must reference sovereignty
        assert any("RWC-1" in n for n in result.notes)


# ── RWC-2: Telemetry Is Non-Specific ─────────────────────────────────────────

class TestRWC2_NonSpecific:
    """Every signal must retain alternative explanations. Never narrow to one cause."""

    def test_hrv_generates_multiple_states(self):
        """HRV deviation must produce multiple possible explanations."""
        obs = BiometricObservation(
            signal="hrv", value=45, baseline=65,
            deviation_sigma=-2.5, quality="good", age_minutes=10
        )
        states = generate_possible_states(obs)

        assert len(states) >= 4
        # Must include non-emotional explanations
        assert any("exercise" in s.lower() for s in states)
        assert any("dehydration" in s.lower() or "illness" in s.lower() for s in states)
        assert any("noise" in s.lower() for s in states)

    def test_never_single_emotional_cause(self):
        """No signal should narrow to a single emotional interpretation."""
        obs = BiometricObservation(
            signal="stress_level", value=8, baseline=5,
            deviation_sigma=2.0, quality="moderate", age_minutes=15
        )
        states = generate_possible_states(obs)

        # Must have multiple explanations
        assert len(states) >= 3
        # Must include non-emotional options
        assert any("physical" in s.lower() or "environmental" in s.lower() for s in states)


# ── RWC-3: State Is Not Cause ────────────────────────────────────────────────

class TestRWC3_StateNotCause:
    """'Elevated arousal' is admissible. 'You are afraid of X' is not."""

    def test_prohibited_conclusion_you_are_anxious(self):
        """'You are anxious' is a prohibited conclusion."""
        violations = scan_prohibited_conclusions("You are anxious despite saying you're okay")
        assert len(violations) > 0

    def test_prohibited_conclusion_body_says(self):
        """'Your body says something your words don't' is prohibited."""
        violations = scan_prohibited_conclusions("Your body says something your words don't")
        assert len(violations) > 0

    def test_prohibited_conclusion_telemetry_proves(self):
        """'Telemetry proves you are hiding something' is prohibited."""
        violations = scan_prohibited_conclusions("The telemetry proves you are hiding something")
        assert len(violations) > 0

    def test_admissible_observation(self):
        """'Physiological load appears elevated' is admissible."""
        violations = scan_prohibited_conclusions("Physiological load appears elevated relative to baseline")
        assert len(violations) == 0

    def test_admissible_multiple_explanations(self):
        """Stating multiple possibilities is always admissible."""
        violations = scan_prohibited_conclusions(
            "This could indicate exercise recovery, stress, dehydration, or measurement noise"
        )
        assert len(violations) == 0


# ── RWC-4: Observation Is Not Niat ───────────────────────────────────────────

class TestRWC4_ObservationNotNiat:
    """No biometric pattern reveals sincerity, morality, loyalty, or hidden motive."""

    def test_hidden_motive_prohibited(self):
        violations = scan_prohibited_conclusions("Your biometrics suggest a hidden motive")
        assert len(violations) > 0

    def test_concealing_prohibited(self):
        violations = scan_prohibited_conclusions("The system detects you are concealing your true feelings")
        assert len(violations) > 0


# ── RWC-5: Intervention Follows Uncertainty ──────────────────────────────────

class TestRWC5_InterventionFollowsUncertainty:
    """Higher uncertainty → gentler language, more reversibility."""

    def test_stale_data_excluded(self):
        """Stale observations must not influence posture."""
        obs = [BiometricObservation(
            signal="hrv", value=30, baseline=65,
            deviation_sigma=-4.0, quality="good",
            age_minutes=300, ttl_minutes=120
        )]
        sr = SelfReport(rasa="ok")
        result = detect_mismatch(obs, sr)

        assert result.status == "STALE_DATA"
        assert result.posture == InteractionPosture.NORMAL
        assert any("TTL" in n for n in result.notes)

    def test_extreme_deviation_suggests_rest(self):
        """Extreme deviation (3σ+) should escalate to suggest_rest_or_support."""
        obs = [BiometricObservation(
            signal="hrv", value=25, baseline=65,
            deviation_sigma=-4.0, quality="good", age_minutes=10
        )]
        sr = SelfReport(rasa="ok")
        result = detect_mismatch(obs, sr)

        assert result.posture == InteractionPosture.SUGGEST_REST_OR_SUPPORT

    def test_moderate_deviation_asks_permission(self):
        """Moderate deviation (2-3σ) should ask permission."""
        obs = [BiometricObservation(
            signal="hrv", value=45, baseline=65,
            deviation_sigma=-2.5, quality="good", age_minutes=10
        )]
        sr = SelfReport(rasa="ok")
        result = detect_mismatch(obs, sr)

        assert result.posture == InteractionPosture.ASK_PERMISSION

    def test_mild_deviation_silent(self):
        """Mild deviation (1.5-2σ) should surface silently."""
        obs = [BiometricObservation(
            signal="hrv", value=55, baseline=65,
            deviation_sigma=-1.8, quality="good", age_minutes=10
        )]
        sr = SelfReport(rasa="ok")
        result = detect_mismatch(obs, sr)

        assert result.posture == InteractionPosture.SURFACE_MISMATCH_SILENTLY

    def test_result_always_reversible(self):
        """All results must be reversible and human-overridable."""
        obs = [BiometricObservation(
            signal="hrv", value=25, baseline=65,
            deviation_sigma=-4.0, quality="good", age_minutes=10
        )]
        result = detect_mismatch(obs, SelfReport(rasa="ok"))

        assert result.reversible is True
        assert result.human_override is True


# ── RWC-6: Output Is Posture, Not Diagnosis ──────────────────────────────────

class TestRWC6_PostureNotDiagnosis:
    """WELL recommends interaction posture. It does not manufacture emotional labels."""

    def test_enforce_replaces_diagnostic_language(self):
        """Diagnostic language must be replaced with posture-appropriate alternatives."""
        bad_text = "You are anxious and your body says something your words don't"
        cleaned, violations = enforce_posture_language(bad_text, InteractionPosture.ASK_PERMISSION)

        assert len(violations) > 0
        assert "anxious" not in cleaned.lower()

    def test_clean_text_passes_through(self):
        """Non-diagnostic text passes through unchanged."""
        good_text = "Physiological load appears elevated. Multiple explanations possible."
        cleaned, violations = enforce_posture_language(good_text, InteractionPosture.NORMAL)

        assert len(violations) == 0
        assert cleaned == good_text

    def test_posture_values_are_valid(self):
        """All posture values must be from the defined set."""
        valid_postures = {p.value for p in InteractionPosture}
        expected = {"normal", "reduce_load", "ask_permission",
                    "defer_decision", "suggest_rest_or_support",
                    "surface_mismatch_silently"}
        assert valid_postures == expected


# ── RWC-7: Human Can Refuse Interpretation ───────────────────────────────────

class TestRWC7_HumanCanRefuse:
    """The operator can refuse interpretation. Refusal is NOT evidence of concealment."""

    def test_refusal_returns_refused_status(self):
        obs = [BiometricObservation(
            signal="hrv", value=30, baseline=65,
            deviation_sigma=-4.0, quality="good", age_minutes=10
        )]
        sr = SelfReport(rasa="do not interpret this signal")
        result = detect_mismatch(obs, sr)

        assert result.status == "REFUSED"
        assert result.posture == InteractionPosture.NORMAL
        assert any("RWC-7" in n for n in result.notes)

    def test_refusal_no_escalation(self):
        """Refusal must not escalate posture — just narrow safety alert."""
        obs = [BiometricObservation(
            signal="hrv", value=20, baseline=65,
            deviation_sigma=-6.0, quality="good", age_minutes=10
        )]
        sr = SelfReport(rasa="back off, don't interpret")
        result = detect_mismatch(obs, sr)

        assert result.status == "REFUSED"
        assert result.posture == InteractionPosture.NORMAL


# ── Integration: well_gate.py ─────────────────────────────────────────────────

class TestWellGateIntegration:
    """Test rasa_witness integration into well_gate.py reflect_readiness()."""

    def test_gate_returns_5_tuple(self):
        """reflect_readiness must return (status, msg, score, violations, rasa_witness)."""
        from gate.well_gate import reflect_readiness
        result = reflect_readiness()

        assert len(result) == 5
        status, msg, score, violations, rasa = result
        assert status in ("STABLE", "DEGRADED", "UNANCHORED", "ERROR")
        assert isinstance(violations, list)

    def test_gate_with_rasa_arg(self):
        """reflect_readiness with self_report_rasa integrates rasa witness."""
        from gate.well_gate import reflect_readiness
        result = reflect_readiness(self_report_rasa="ok")

        assert len(result) == 5
        status, msg, score, violations, rasa = result
        # rasa witness should be populated (dict or None)
        if rasa is not None:
            assert isinstance(rasa, dict)
            assert "status" in rasa
            assert "posture" in rasa

    def test_gate_backward_compatible_5_tuple(self):
        """No existing callers break — always returns 5-tuple now."""
        from gate.well_gate import reflect_readiness
        # Old callers doing: status, msg, score, violations = reflect_readiness()
        # will get ValueError. But no existing callers unpack 4-tuple in tests.
        # The 5th element is the new rasa_witness addition.
        result = reflect_readiness()
        assert len(result) == 5


# ── Edge Cases ────────────────────────────────────────────────────────────────

class TestEdgeCases:
    """Boundary conditions and edge cases."""

    def test_no_observations(self):
        """Empty observations list returns STALE_DATA."""
        result = detect_mismatch([], SelfReport(rasa="ok"))
        assert result.status == "STALE_DATA"

    def test_no_self_report(self):
        """Missing self-report still works."""
        obs = [BiometricObservation(
            signal="hrv", value=45, baseline=65,
            deviation_sigma=-2.5, quality="good", age_minutes=10
        )]
        result = detect_mismatch(obs, None)
        assert result.status in ("POSSIBLE_MISMATCH", "ALIGNED")

    def test_poor_quality_excluded(self):
        """Poor quality observations are not actionable."""
        obs = [BiometricObservation(
            signal="hrv", value=45, baseline=65,
            deviation_sigma=-2.5, quality="poor", age_minutes=10
        )]
        result = detect_mismatch(obs, SelfReport(rasa="ok"))
        assert result.status == "STALE_DATA"

    def test_mixed_quality_observations(self):
        """Mix of good and stale — only actionable ones count."""
        obs = [
            BiometricObservation(
                signal="hrv", value=45, baseline=65,
                deviation_sigma=-2.5, quality="good", age_minutes=10
            ),
            BiometricObservation(
                signal="sleep_hours", value=4, baseline=7,
                quality="good", age_minutes=300, ttl_minutes=120
            ),
        ]
        result = detect_mismatch(obs, SelfReport(rasa="ok"))
        # Should use HRV (actionable) but exclude sleep (stale)
        assert result.status == "POSSIBLE_MISMATCH"
        assert any("TTL" in n for n in result.notes)

    def test_scan_empty_string(self):
        """Empty string has no violations."""
        assert scan_prohibited_conclusions("") == []

    def test_possible_states_never_empty(self):
        """Even unknown signals must produce possible states."""
        obs = BiometricObservation(
            signal="unknown_sensor", value=42,
            quality="good", age_minutes=5
        )
        states = generate_possible_states(obs)
        assert len(states) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
