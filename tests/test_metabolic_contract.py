"""
WELL Metabolic Contract — Conformance Tests
═══════════════════════════════════════════════════════════════════════════════════

Tests WELL Phase 3 adoption of the Universal Metabolic Contract.
Source: arifOS commit eb53b316.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

import sys
from pathlib import Path

# Ensure contracts package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from contracts.schemas.metabolic import (
    ClaimState,
    ConfidenceLevel,
    MetabolicOutput,
    OrganType,
    WitnessType,
)
from contracts.enrich_well import (
    ADOPTION_STATUS,
    SCHEMA_NAME,
    SCHEMA_VERSION,
    SOURCE_COMMIT,
    build_metabolic_output,
)


# ── Schema import ────────────────────────────────────────────────────────────────


def test_metabolic_schema_import():
    """Canonical schema imports cleanly."""
    assert MetabolicOutput is not None
    assert ClaimState is not None
    assert ConfidenceLevel is not None
    assert OrganType is not None
    assert WitnessType is not None


def test_claim_state_enum_values():
    """ClaimState enum has all required values."""
    values = {c.value for c in ClaimState}
    assert "OBSERVED" in values
    assert "HYPOTHESIS" in values
    assert "QUALIFIED" in values
    assert "VERIFIED" in values
    assert "SEALED" in values
    assert "HOLD" in values


def test_confidence_level_enum_values():
    """ConfidenceLevel enum has all required values."""
    values = {c.value for c in ConfidenceLevel}
    assert "UNKNOWN" in values
    assert "LOW" in values
    assert "MODERATE" in values
    assert "HIGH" in values
    assert "VERIFIED" in values
    assert "SEALED" in values


def test_organ_type_weird_wealth():
    """OrganType includes WELL."""
    assert OrganType.WELL.value == "WELL"


def test_witness_type_values():
    """WitnessType enum has expected values."""
    values = {c.value for c in WitnessType}
    assert "sensor" in values
    assert "testimony" in values


# ── Contract metadata ───────────────────────────────────────────────────────────


def test_schema_name():
    assert SCHEMA_NAME == "MetabolicOutput"


def test_schema_version():
    assert SCHEMA_VERSION == "1.0.0"


def test_source_commit():
    assert SOURCE_COMMIT == "eb53b316"


def test_adoption_status():
    assert ADOPTION_STATUS == "PHASE_3"


# ── build_metabolic_output helper ───────────────────────────────────────────────


def test_enrich_helper_import():
    """enrich_well helper imports cleanly."""
    from contracts.enrich_well import build_metabolic_output

    assert callable(build_metabolic_output)


def test_build_metabolic_output_basic():
    """build_metabolic_output returns dict with metabolic key."""
    # _omega_well_output return structure: ok at top, Ω at top, data inside
    internal = {
        "ok": True,
        "Ω": {
            "verdict": "SEAL",
            "stage": "888_JUDGE",
            "lane": "APEX",
            "mode": "readiness",
        },
        "data": {"status": "ADVISORY_READY"},
    }
    result = build_metabolic_output(
        tool_name="well_validate_vitality", internal_result=internal
    )
    assert "metabolic" in result
    assert result["metabolic"]["organ"] == "WELL"
    assert result["metabolic"]["tool_name"] == "well_validate_vitality"


# ── Verdict → ClaimState mapping ───────────────────────────────────────────────
# Fixtures match _omega_well_output return structure (Ω at top level, ok at top level)


def test_seal_yields_verified():
    """SEAL verdict maps to VERIFIED claim_state."""
    internal = {
        "ok": True,
        "Ω": {
            "verdict": "SEAL",
            "stage": "888_JUDGE",
            "lane": "APEX",
            "mode": "readiness",
        },
        "data": {},
    }
    result = build_metabolic_output(
        tool_name="well_validate_vitality", internal_result=internal
    )
    assert result["metabolic"]["claim_state"] == "VERIFIED"


def test_pass_yields_verified():
    """PASS verdict maps to VERIFIED claim_state."""
    internal = {
        "ok": True,
        "Ω": {"verdict": "PASS", "stage": "000_OPS", "lane": "AGI", "mode": "health"},
        "data": {},
    }
    result = build_metabolic_output(
        tool_name="well_assess_reliability", internal_result=internal
    )
    assert result["metabolic"]["claim_state"] == "VERIFIED"


def test_provisional_yields_qualified():
    """PROVISIONAL verdict maps to QUALIFIED claim_state."""
    internal = {
        "ok": True,
        "Ω": {
            "verdict": "PROVISIONAL",
            "stage": "444_KERNEL",
            "lane": "ASI",
            "mode": "route",
        },
        "data": {},
    }
    result = build_metabolic_output(
        tool_name="well_reflect_intelligence", internal_result=internal
    )
    assert result["metabolic"]["claim_state"] == "QUALIFIED"


def test_hold_yields_hold():
    """HOLD verdict maps to HOLD claim_state."""
    internal = {
        "ok": False,
        "Ω": {
            "verdict": "HOLD",
            "stage": "888_JUDGE",
            "lane": "APEX",
            "mode": "readiness",
        },
        "data": {},
    }
    result = build_metabolic_output(
        tool_name="well_validate_vitality", internal_result=internal
    )
    assert result["metabolic"]["claim_state"] == "HOLD"


def test_void_yields_hold():
    """VOID verdict maps to HOLD claim_state."""
    internal = {
        "ok": False,
        "Ω": {"verdict": "VOID", "stage": "000_OPS", "lane": "AGI", "mode": "health"},
        "data": {},
    }
    result = build_metabolic_output(
        tool_name="well_assess_reliability", internal_result=internal
    )
    assert result["metabolic"]["claim_state"] == "HOLD"


def test_warn_yields_hypothesis():
    """WARN verdict maps to HYPOTHESIS claim_state."""
    internal = {
        "ok": False,
        "Ω": {"verdict": "WARN", "stage": "000_OPS", "lane": "AGI", "mode": "health"},
        "data": {},
    }
    result = build_metabolic_output(
        tool_name="well_assess_reliability", internal_result=internal
    )
    assert result["metabolic"]["claim_state"] == "HYPOTHESIS"


# ── WELL sovereignty boundary ───────────────────────────────────────────────────


def test_well_always_recommendation_only():
    """WELL outputs are always recommendation_only=True."""
    for verdict in ["SEAL", "PASS", "PROVISIONAL", "HOLD", "WARN", "VOID"]:
        internal = {
            "ok": True,
            "Ω": {
                "verdict": verdict,
                "stage": "888_JUDGE",
                "lane": "APEX",
                "mode": "readiness",
            },
            "data": {},
        }
        result = build_metabolic_output(
            tool_name="well_validate_vitality", internal_result=internal
        )
        assert result["metabolic"]["recommendation_only"] is True, f"verdict={verdict}"
        assert result["metabolic"]["execution_authorized"] is False, (
            f"verdict={verdict}"
        )


def test_well_human_final_authority():
    """WELL outputs always cite Arif as final authority."""
    internal = {
        "ok": True,
        "Ω": {
            "verdict": "SEAL",
            "stage": "888_JUDGE",
            "lane": "APEX",
            "mode": "readiness",
        },
        "data": {},
    }
    result = build_metabolic_output(
        tool_name="well_validate_vitality", internal_result=internal
    )
    assert result["metabolic"]["human_final_authority"] == "Arif"


def test_vitality_requires_888():
    """well_validate_vitality always requires_888_judge=True."""
    internal = {
        "ok": True,
        "Ω": {
            "verdict": "SEAL",
            "stage": "888_JUDGE",
            "lane": "APEX",
            "mode": "readiness",
        },
        "data": {},
    }
    result = build_metabolic_output(
        tool_name="well_validate_vitality", internal_result=internal
    )
    assert result["metabolic"]["requires_888_judge"] is True


def test_reflect_intelligence_requires_888():
    """well_reflect_intelligence always requires_888_judge=True."""
    internal = {
        "ok": True,
        "Ω": {
            "verdict": "PROVISIONAL",
            "stage": "444_KERNEL",
            "lane": "ASI",
            "mode": "route",
        },
        "data": {},
    }
    result = build_metabolic_output(
        tool_name="well_reflect_intelligence", internal_result=internal
    )
    assert result["metabolic"]["requires_888_judge"] is True


def test_reliability_escalates_on_hold():
    """well_assess_reliability requires_888_judge only on HOLD/VOID."""
    # On SEAL - no escalation
    internal_seal = {
        "ok": True,
        "Ω": {"verdict": "SEAL", "stage": "000_OPS", "lane": "AGI", "mode": "health"},
        "data": {},
    }
    result = build_metabolic_output(
        tool_name="well_assess_reliability", internal_result=internal_seal
    )
    assert result["metabolic"]["requires_888_judge"] is False

    # On HOLD - escalation
    internal_hold = {
        "ok": False,
        "Ω": {"verdict": "HOLD", "stage": "000_OPS", "lane": "AGI", "mode": "health"},
        "data": {},
    }
    result = build_metabolic_output(
        tool_name="well_assess_reliability", internal_result=internal_hold
    )
    assert result["metabolic"]["requires_888_judge"] is True


# ── Uncertainty ─────────────────────────────────────────────────────────────────


def test_uncertainty_has_omega_0():
    """uncertainty band includes omega_0."""
    internal = {
        "ok": True,
        "Ω": {
            "verdict": "SEAL",
            "stage": "888_JUDGE",
            "lane": "APEX",
            "mode": "readiness",
        },
        "data": {},
    }
    result = build_metabolic_output(
        tool_name="well_validate_vitality", internal_result=internal
    )
    assert "uncertainty" in result["metabolic"]
    assert "omega_0" in result["metabolic"]["uncertainty"]
    assert isinstance(result["metabolic"]["uncertainty"]["omega_0"], float)


def test_seal_low_uncertainty():
    """SEAL verdict yields low uncertainty (0.05)."""
    internal = {
        "ok": True,
        "Ω": {
            "verdict": "SEAL",
            "stage": "888_JUDGE",
            "lane": "APEX",
            "mode": "readiness",
        },
        "data": {},
    }
    result = build_metabolic_output(
        tool_name="well_validate_vitality", internal_result=internal
    )
    assert result["metabolic"]["uncertainty"]["omega_0"] == 0.05


def test_void_high_uncertainty():
    """VOID verdict yields high uncertainty (0.90)."""
    internal = {
        "ok": False,
        "Ω": {"verdict": "VOID", "stage": "000_OPS", "lane": "AGI", "mode": "health"},
        "data": {},
    }
    result = build_metabolic_output(
        tool_name="well_assess_reliability", internal_result=internal
    )
    assert result["metabolic"]["uncertainty"]["omega_0"] == 0.90


# ── Cross-organ handoff ─────────────────────────────────────────────────────────


def test_cross_organ_handoff_present():
    """build_metabolic_output includes cross_organ_handoff."""
    internal = {
        "ok": True,
        "Ω": {
            "verdict": "SEAL",
            "stage": "888_JUDGE",
            "lane": "APEX",
            "mode": "readiness",
        },
        "data": {},
    }
    result = build_metabolic_output(
        tool_name="well_validate_vitality", internal_result=internal
    )
    assert "cross_organ_handoff" in result["metabolic"]
    assert result["metabolic"]["cross_organ_handoff"]["next_best_organ"] == "arifOS"


def test_vitality_handoff_to_arifOS():
    """well_validate_vitality hands off to arifOS."""
    internal = {
        "ok": True,
        "Ω": {
            "verdict": "SEAL",
            "stage": "888_JUDGE",
            "lane": "APEX",
            "mode": "readiness",
        },
        "data": {},
    }
    result = build_metabolic_output(
        tool_name="well_validate_vitality", internal_result=internal
    )
    assert result["metabolic"]["cross_organ_handoff"]["next_best_organ"] == "arifOS"


def test_reflect_handoff_to_arifOS():
    """well_reflect_intelligence hands off to arifOS."""
    internal = {
        "ok": True,
        "Ω": {
            "verdict": "PROVISIONAL",
            "stage": "444_KERNEL",
            "lane": "ASI",
            "mode": "route",
        },
        "data": {},
    }
    result = build_metabolic_output(
        tool_name="well_reflect_intelligence", internal_result=internal
    )
    assert result["metabolic"]["cross_organ_handoff"]["next_best_organ"] == "arifOS"


def test_reliability_handoff_to_a_forge():
    """well_assess_reliability hands off to A-FORGE."""
    internal = {
        "ok": True,
        "Ω": {"verdict": "SEAL", "stage": "000_OPS", "lane": "AGI", "mode": "health"},
        "data": {},
    }
    result = build_metabolic_output(
        tool_name="well_assess_reliability", internal_result=internal
    )
    assert result["metabolic"]["cross_organ_handoff"]["next_best_organ"] == "A-FORGE"


# ── Witness type per tool ───────────────────────────────────────────────────────


def test_vitality_witness_type_sensor():
    """well_validate_vitality uses sensor witness type."""
    internal = {
        "ok": True,
        "Ω": {
            "verdict": "SEAL",
            "stage": "888_JUDGE",
            "lane": "APEX",
            "mode": "readiness",
        },
        "data": {},
    }
    result = build_metabolic_output(
        tool_name="well_validate_vitality", internal_result=internal
    )
    assert result["metabolic"]["witness_type"] == "sensor"


def test_reflect_witness_type_testimony():
    """well_reflect_intelligence uses testimony witness type."""
    internal = {
        "ok": True,
        "Ω": {
            "verdict": "PROVISIONAL",
            "stage": "444_KERNEL",
            "lane": "ASI",
            "mode": "route",
        },
        "data": {},
    }
    result = build_metabolic_output(
        tool_name="well_reflect_intelligence", internal_result=internal
    )
    assert result["metabolic"]["witness_type"] == "testimony"


# ── Model target per tool ──────────────────────────────────────────────────────


def test_vitality_model_target_body():
    """well_validate_vitality targets Body model."""
    internal = {
        "ok": True,
        "Ω": {
            "verdict": "SEAL",
            "stage": "888_JUDGE",
            "lane": "APEX",
            "mode": "readiness",
        },
        "data": {},
    }
    result = build_metabolic_output(
        tool_name="well_validate_vitality", internal_result=internal
    )
    assert result["metabolic"]["model_target"] == "Body"


def test_reflect_model_target_system():
    """well_reflect_intelligence targets System model."""
    internal = {
        "ok": True,
        "Ω": {
            "verdict": "PROVISIONAL",
            "stage": "444_KERNEL",
            "lane": "ASI",
            "mode": "route",
        },
        "data": {},
    }
    result = build_metabolic_output(
        tool_name="well_reflect_intelligence", internal_result=internal
    )
    assert result["metabolic"]["model_target"] == "System"


# ── Backward compatibility ─────────────────────────────────────────────────────


def test_federation_fields_present():
    """Result includes federation standard fields at top level."""
    internal = {
        "ok": True,
        "Ω": {
            "verdict": "SEAL",
            "stage": "888_JUDGE",
            "lane": "APEX",
            "mode": "readiness",
        },
        "data": {},
    }
    result = build_metabolic_output(
        tool_name="well_validate_vitality", internal_result=internal
    )
    assert "observation" in result
    assert "uncertainty" in result
    assert "constraints" in result
    assert "boundary_notice" in result


def test_boundary_notice_present():
    """Result includes WELL boundary notice."""
    internal = {
        "ok": True,
        "Ω": {
            "verdict": "SEAL",
            "stage": "888_JUDGE",
            "lane": "APEX",
            "mode": "readiness",
        },
        "data": {},
    }
    result = build_metabolic_output(
        tool_name="well_validate_vitality", internal_result=internal
    )
    # WELL boundary notice: "Not diagnosis. Not therapy. Reflective readiness only. Arif remains final judge."
    assert "Arif" in result["boundary_notice"]
    assert (
        "diagnosis" in result["boundary_notice"].lower()
        or "reflective" in result["boundary_notice"].lower()
    )


if __name__ == "__main__":
    # Run all tests
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  PASS  {name}")
            except Exception as e:
                print(f"  FAIL  {name}: {e}")
    print(
        f"\n{sum(1 for n, f in globals().items() if n.startswith('test_') and callable(f))} tests total"
    )
