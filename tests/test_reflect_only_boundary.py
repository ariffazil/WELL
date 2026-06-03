# WELL — Reflect-Only Boundary Tests (PR 6)
# ═══════════════════════════════════════════════════════════════════════════
# Doctrine: WELL reflects. arifOS arbitrates. Never the reverse.
# Every WELL canonical tool output must carry 4 reflect-only labels
# (telemetry, context, authority, medical_status) so that no downstream
# agent can mistake WELL's reflection for execution authority or a
# medical diagnosis.
#
# These tests prove the boundary is enforced at the module level (the
# detection helpers) and at the decorator level (the labels are
# injectable on any tool result).

from __future__ import annotations

import asyncio
import datetime
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "engines"))

from reflect import (
    AUTHORITY_REFLECT_ONLY,
    CONTEXT_VALUES,
    MEDICAL_NOT_DIAGNOSIS,
    MEDICAL_VALUES,
    REFLECT_DISCLAIMER,
    TELEMETRY_VALUES,
    compute_reflect_boundary,
    detect_authority_status,
    detect_context_status,
    detect_medical_status,
    detect_telemetry_status,
    reflect_only_boundary,
)


# ─── 1. all 4 labels are present on every output ─────────────────────────


def test_all_four_labels_present():
    """Every compute_reflect_boundary output has telemetry, context,
    authority, and medical_status.

    F2: an agent reading the output must be unable to confuse WELL
    reflection for execution authority or medical diagnosis.
    """
    cases = [
        {},
        {"timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
         "metrics": {"hr": 70}, "identity": "arif", "verified_metrics": True},
        {"synthetic": True},
        {"timestamp": "2026-01-01T00:00:00Z", "metrics": {}, "identity": "arif"},
        None,
    ]
    for state in cases:
        b = compute_reflect_boundary(state)  # type: ignore[arg-type]
        assert "telemetry" in b
        assert "context" in b
        assert "authority" in b
        assert "medical_status" in b
        assert "reflect_disclaimer" in b


# ─── 2. authority is ALWAYS "advisory_only" ──────────────────────────────


def test_authority_is_advisory_only():
    """Authority is a constitutional constant for WELL.

    F13 SOVEREIGN: WELL labels; arifOS arbitrates. The authority label
    does not change based on input. WELL never grants execution.
    """
    for state in [None, {}, {"verified_metrics": True}, {"synthetic": True}]:
        b = compute_reflect_boundary(state)  # type: ignore[arg-type]
        assert b["authority"] == AUTHORITY_REFLECT_ONLY
        assert b["authority"] == "advisory_only"
    # And the constant itself
    assert detect_authority_status() == "advisory_only"


# ─── 3. medical_status is ALWAYS "not_diagnosis" ────────────────────────


def test_medical_status_is_not_diagnosis():
    """WELL never diagnoses. medical_status is fixed by constitution.

    F2: a medical diagnosis is a clinical act. WELL is reflect-only.
    No input pattern can flip this label to "diagnostic_suggestion"
    from a canonical WELL tool. (That value is reserved for future
    clinical-integration work and the constant exists only for
    completeness of the value set.)
    """
    for state in [None, {}, {"verified_metrics": True}]:
        b = compute_reflect_boundary(state)  # type: ignore[arg-type]
        assert b["medical_status"] == MEDICAL_NOT_DIAGNOSIS
        assert b["medical_status"] == "not_diagnosis"
    assert detect_medical_status() == "not_diagnosis"
    # And the value set is closed
    assert MEDICAL_VALUES == ("not_diagnosis", "diagnostic_suggestion")


# ─── 4. telemetry classification is observable ──────────────────────────


def test_telemetry_classification():
    """Telemetry source classification: live / manual / synthetic / unavailable.

    F1: observable only. We never claim a sensor is reading the body;
    we only report what the state object says.
    """
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # live: verified_metrics + fresh timestamp
    s_live = {"timestamp": now, "verified_metrics": True, "metrics": {"hr": 70}}
    assert detect_telemetry_status(s_live) == "live"

    # synthetic: explicit synthetic flag wins
    s_synth = {"synthetic": True, "metrics": {"hr": 70}}
    assert detect_telemetry_status(s_synth) == "synthetic"

    # manual: self-report source
    s_manual = {"source": "self_report", "metrics": {"hr": 70}}
    assert detect_telemetry_status(s_manual) == "manual"

    # unavailable: empty / None / stale
    assert detect_telemetry_status({}) == "unavailable"
    assert detect_telemetry_status(None) == "unavailable"  # type: ignore[arg-type]
    s_old = {"timestamp": "2026-01-01T00:00:00Z", "metrics": {"hr": 70}}
    assert detect_telemetry_status(s_old) == "unavailable"


# ─── 5. context classification: sufficient vs insufficient ───────────────


def test_context_classification():
    """Context is sufficient only when state has metrics + timestamp + identity.

    F7 STEWARDSHIP: never emit a readiness score on insufficient context.
    """
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    s_sufficient = {
        "timestamp": now,
        "metrics": {"hr": 70},
        "identity": "arif",
    }
    assert detect_context_status(s_sufficient) == "sufficient"

    assert detect_context_status({}) == "insufficient"
    assert detect_context_status(None) == "insufficient"  # type: ignore[arg-type]
    assert detect_context_status({"metrics": {"hr": 70}}) == "insufficient"  # no ts
    assert detect_context_status({"timestamp": now, "identity": "arif"}) == "insufficient"  # no metrics

    # 168h hard ceiling
    s_old = {
        "timestamp": "2026-01-01T00:00:00Z",
        "metrics": {"hr": 70},
        "identity": "arif",
    }
    assert detect_context_status(s_old) == "insufficient"


# ─── 6. F7 readiness guard strips scores on insufficient context ─────────


def test_f7_readiness_guard():
    """A readiness score on insufficient context is replaced with HOLD.

    F7 STEWARDSHIP: a readiness score on insufficient context is a
    fabrication. The honest path is HOLD.
    """
    # Simulate a tool that returns a readiness score on empty state.
    @reflect_only_boundary
    def fake_tool_with_score() -> dict:
        return {
            "readiness": "GREEN",
            "well_score": 92.0,
            "score": 0.9,
            "summary": "Looks healthy",
        }

    out = fake_tool_with_score()
    # On insufficient context, the readiness fields are stripped to HOLD
    assert out["readiness"] == "HOLD"
    assert out["well_score"] == "HOLD"
    assert out["score"] == "HOLD"
    # The 4 reflect-only labels are still injected
    assert out["telemetry"] == "unavailable"
    assert out["context"] == "insufficient"
    assert out["authority"] == "advisory_only"
    assert out["medical_status"] == "not_diagnosis"


# ─── 7. decorator preserves original fields (additive only) ──────────────


def test_decorator_is_additive():
    """The decorator must not remove any original field. F2 / F1.

    F1 AMANAH: existing well outputs are sovereign biometric data. The
    decorator is additive, never subtractive.
    """
    @reflect_only_boundary
    def fake_tool_with_extras() -> dict:
        return {
            "summary": "test",
            "value": 42,
            "nested": {"key": "data"},
            "telemetry_status": "legacy_field",  # pre-existing
            "authority": "REFLECT_ONLY",  # pre-existing
        }

    out = fake_tool_with_extras()
    # Originals preserved
    assert out["summary"] == "test"
    assert out["value"] == 42
    assert out["nested"] == {"key": "data"}
    # 4 reflect-only labels injected (overwriting pre-existing is fine —
    # the new value is the canonical one)
    assert out["telemetry"] in TELEMETRY_VALUES
    assert out["context"] in CONTEXT_VALUES
    assert out["authority"] == "advisory_only"
    assert out["medical_status"] == "not_diagnosis"


# ─── 8. async decorator works ────────────────────────────────────────────


def test_async_decorator():
    """The decorator handles both sync and async tools.

    Many WELL canonical tools are async (e.g., well_init, well_anchor).
    """
    @reflect_only_boundary
    async def async_fake_tool() -> dict:
        return {"summary": "async test", "value": "x"}

    out = asyncio.run(async_fake_tool())
    assert out["summary"] == "async test"
    assert out["authority"] == "advisory_only"
    assert out["medical_status"] == "not_diagnosis"
    assert out["telemetry"] in TELEMETRY_VALUES
    assert out["context"] in CONTEXT_VALUES


# ─── 9. F13 honor: no new MCP tools ──────────────────────────────────────


def test_no_new_mcp_tools():
    """PR 6 does not add a new MCP tool. F13: surface stays clean.

    The reflect module exposes the 4 label constants + the decorator.
    It does not register any FastMCP tools.
    """
    import reflect as r

    forbidden = ("mcp.tool", "FastMCP", "@mcp")
    for name in dir(r):
        for marker in forbidden:
            assert marker not in name, (
                f"reflect.py must not register MCP tools; found {name!r} matching {marker!r}"
            )

    # The constants are present (proving the module is loaded).
    assert r.AUTHORITY_REFLECT_ONLY == "advisory_only"
    assert r.MEDICAL_NOT_DIAGNOSIS == "not_diagnosis"
    assert "advisory" in r.REFLECT_DISCLAIMER
    assert "not_diagnosis" in r.REFLECT_DISCLAIMER


# ─── 10. value-set enumeration ───────────────────────────────────────────


def test_value_set_enumeration():
    """Each label must be in its valid value set.

    F2: the value set is closed. New values require a constitutional
    change, not a config tweak.
    """
    for state in [None, {}, {"synthetic": True}, {"verified_metrics": True}]:
        b = compute_reflect_boundary(state)  # type: ignore[arg-type]
        assert b["telemetry"] in TELEMETRY_VALUES
        assert b["context"] in CONTEXT_VALUES
        assert b["medical_status"] in MEDICAL_VALUES
        assert b["authority"] == AUTHORITY_REFLECT_ONLY


if __name__ == "__main__":
    import pytest

    sys.exit(pytest.main([__file__, "-v"]))
