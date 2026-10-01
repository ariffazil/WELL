"""WELL v2.1 Surface Integrity Release Invariants.
F13 Sovereign Ratification (2026-10-01).

Guarantees:
  Declared = Listed = Exported = Callable = Routed
"""

from __future__ import annotations

import pytest
import server


def test_public_tools_exactly_ten():
    """Canonical target surface is exactly 10 tools."""
    assert len(server.SOMATIC_TOOLS) == 10, (
        f"Expected exactly 10 somatic tools, got {len(server.SOMATIC_TOOLS)}: {sorted(server.SOMATIC_TOOLS)}"
    )
    expected = {
        "well_classify_substrate",
        "well_trace_lineage",
        "well_assess_homeostasis",
        "well_check_repair",
        "well_validate_vitality",
        "well_assess_reliability",
        "well_guard_dignity",
        "well_registry_status",
        "well_machine_diagnose",
        "well_machine_recommend",
    }
    assert set(server.SOMATIC_TOOLS) == expected


def test_registry_truth_pass_and_zero_phantoms():
    """well_registry_status must report REGISTRY_PASS with zero phantoms."""
    reg = server.well_registry_status()
    assert reg["verdict"] == "REGISTRY_PASS", f"Verdict was {reg.get('verdict')}"
    assert reg["phantom_tools_count"] == 0
    assert reg["unexpected_public_tools_count"] == 0
    assert reg["missing_public_tools_count"] == 0
    assert reg["intended_tools"] == 10
    assert reg["registered_tools"] == 10


def test_no_self_deprecation_loop_in_vitality():
    """well_validate_vitality must never claim to be deprecated or replace itself."""
    res = server.well_validate_vitality()
    assert "deprecated" not in res, "Self-deprecation loop detected in well_validate_vitality"
    assert "replacement" not in res, "Replacement pointer found in canonical tool"
    assert res.get("authority") == "ADVISORY_ONLY"
    assert res.get("readiness") in ("READY", "DEGRADED", "NOT_READY", "UNKNOWN")


def test_no_constitutional_verdict_leakage_from_well():
    """WELL outputs must never emit constitutional verdict words (HOLD, SEAL, VOID)."""
    res = server.well_validate_vitality()
    assert res.get("action") not in ("HOLD", "BLOCKED", "ALLOW", "DENY"), (
        f"Constitutional action word leaked: {res.get('action')}"
    )
    assert res.get("verdict") not in ("HOLD", "SEAL", "VOID"), (
        f"Constitutional verdict word leaked: {res.get('verdict')}"
    )


def test_dead_names_not_in_somatic():
    """Dead names like well_detect_boundary or well_system_registry_status must not be in SOMATIC_TOOLS."""
    for dead in ("well_detect_boundary", "well_system_registry_status", "well_state", "well_get_health"):
        assert dead not in server.SOMATIC_TOOLS, f"Dead tool {dead} leaked into public SOMATIC_TOOLS"
