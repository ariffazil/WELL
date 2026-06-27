"""Tests for well_mcp — the WELL federation MCP canon surface.

Covers:
  1. Package imports
  2. 5-stage transport loop (happy path + 6 critical paths)
  3. Freshness decay + VOID ceiling
  4. Dignity floor (consent, coercion, reductionism, dignity_preservation)
  5. Decision class mapping + downgrade
  6. F1–F13 floor status computation
  7. C5 irreversible → F13 HOLD

Run: cd /root/WELL && python3 -m pytest tests/test_well_mcp.py -v
     or: python3 tests/test_well_mcp.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure /root/WELL on path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from well_mcp.transport import (
    run_loop,
    STAGE_NAMES,
    stamp_ingress,
    stamp_encode,
    stamp_metabolize,
    stamp_judge,
    stamp_egress,
)


# ============================================================================
# 1. PACKAGE IMPORTS
# ============================================================================


def test_package_imports():
    """well_mcp package + sub-packages import cleanly."""
    import well_mcp

    assert well_mcp.__name__ == "well_mcp"
    assert well_mcp.resources is not None
    assert well_mcp.prompts is not None
    assert well_mcp.transport is not None
    assert well_mcp.tools is not None
    assert len(well_mcp.resources.RESOURCE_MODULES) == 12
    assert len(well_mcp.prompts.PROMPT_MODULES) == 9
    assert len(STAGE_NAMES) == 5


# ============================================================================
# 2. STAGE 1 — INGRESS
# ============================================================================


def test_ingress_generates_signal_id():
    """Stage 1 generates a uuid4 signal_id."""
    s = stamp_ingress({"x": 1})
    assert "signal_id" in s
    assert len(s["signal_id"]) == 36  # uuid4 format
    assert s["stage"] == "ingress"
    assert s["source"]["organ"] == "well"


def test_ingress_records_source():
    """Stage 1 records source organ/tool/actor/timestamp."""
    s = stamp_ingress(
        payload={"x": 1},
        source_organ="geox",
        source_tool="geox_basin",
        actor_id="arif",
    )
    assert s["source"]["organ"] == "geox"
    assert s["source"]["tool"] == "geox_basin"
    assert s["source"]["actor"] == "arif"
    assert "ts" in s["source"]


def test_ingress_freshness_optional():
    """Stage 1 accepts None freshness."""
    s = stamp_ingress({"x": 1}, freshness_raw_hours=None)
    assert s["freshness_raw"] is None


# ============================================================================
# 3. STAGE 2 — ENCODE (freshness decay + dignity floor)
# ============================================================================


def test_encode_freshness_high():
    """age ≤ 12h → HIGH confidence."""
    s = stamp_ingress(
        {"x": 1},
        freshness_raw_hours=5.0,
        consent_verified=True,
        dignity_preservation=0.85,
    )
    e = stamp_encode(s)
    assert e["confidence"] == "HIGH"


def test_encode_freshness_stale_to_void():
    """age > 168h → VOID."""
    s = stamp_ingress(
        {"x": 1},
        freshness_raw_hours=200.0,
        consent_verified=True,
        dignity_preservation=0.85,
    )
    e = stamp_encode(s)
    assert e["confidence"] == "VOID"


def test_encode_freshness_decay_bands():
    """All freshness bands correctly mapped."""
    for age, expected in [
        (1.0, "HIGH"),
        (15.0, "MEDIUM"),
        (50.0, "LOW"),
        (100.0, "STALE"),
        (200.0, "VOID"),
    ]:
        s = stamp_ingress(
            {"x": 1},
            freshness_raw_hours=age,
            consent_verified=True,
            dignity_preservation=0.85,
        )
        e = stamp_encode(s)
        assert e["confidence"] == expected, f"age={age} expected {expected}"


def test_encode_dignity_floor_pass():
    """Dignity floor PASSes when all checks satisfied."""
    s = stamp_ingress({"x": 1}, consent_verified=True, dignity_preservation=0.85)
    e = stamp_encode(s, decision_class="C3")
    assert e["dignity_floor"]["status"] == "PASS"
    assert e["decision_class"] == "C3"


def test_encode_dignity_floor_void_when_consent_missing():
    """Dignity floor VOIDs when consent_verified is False."""
    s = stamp_ingress({"x": 1}, consent_verified=False, dignity_preservation=0.85)
    e = stamp_encode(s, decision_class="C3")
    assert e["dignity_floor"]["status"] == "VOID"
    assert e["decision_class"] == "C1"  # downgraded
    assert "dignity_leakage_advisory" in e


def test_encode_dignity_floor_hold_when_dignity_low():
    """Dignity floor HOLDs when dignity_preservation < 0.70."""
    s = stamp_ingress({"x": 1}, consent_verified=True, dignity_preservation=0.50)
    e = stamp_encode(s, decision_class="C3")
    assert e["dignity_floor"]["status"] == "HOLD"
    assert e["decision_class"] == "C1"  # downgraded


def test_encode_coercion_triggers_void():
    """Coercion signals present → dignity floor VOID."""
    s = stamp_ingress(
        {"x": 1},
        consent_verified=True,
        coercion_signals=["forced_oversight"],
        dignity_preservation=0.85,
    )
    e = stamp_encode(s, decision_class="C3")
    assert e["dignity_floor"]["status"] == "VOID"
    assert "coercion_signals present" in e["dignity_leakage_advisory"]


def test_encode_invalid_decision_class_defaults_to_C1():
    """Invalid decision_class → defaults to C1 (safest)."""
    s = stamp_ingress({"x": 1}, consent_verified=True, dignity_preservation=0.85)
    e = stamp_encode(s, decision_class="C9")
    assert e["decision_class"] == "C1"


# ============================================================================
# 4. STAGE 3 — METABOLIZE (flux + coupling)
# ============================================================================


def test_metabolize_happy_path():
    """Happy path: low flux, high coupling, OPTIMAL."""
    s = stamp_ingress({"x": 1}, consent_verified=True, dignity_preservation=0.85)
    e = stamp_encode(s, decision_class="C2")
    m = stamp_metabolize(
        e,
        human_state=0.85,
        machine_state=0.90,
        governance_state=0.95,
        e1=0.20,
        e2=0.15,
        e3=0.10,
        e4=0.10,
        cognitive_entropy_rate=0.20,
    )
    assert m["machine_entropy"] < 0.40
    assert m["metabolic_flux"] < 0.40
    assert m["coupling_state"] > 0.65
    assert m["readiness_verdict"] in ("STABLE", "OPTIMAL")


def test_metabolize_machine_critical():
    """Machine CRITICAL → low coupling, CRITICAL verdict."""
    s = stamp_ingress({"x": 1}, consent_verified=True, dignity_preservation=0.85)
    e = stamp_encode(s, decision_class="C2")
    m = stamp_metabolize(
        e,
        human_state=0.85,
        machine_state=0.05,  # CRITICAL
        governance_state=0.95,
    )
    assert m["coupling_state"] < 0.15
    assert m["readiness_verdict"] == "CRITICAL"


def test_metabolize_flux_weights_correct():
    """metabolic_flux = 0.55·human + 0.45·machine."""
    s = stamp_ingress({"x": 1}, consent_verified=True, dignity_preservation=0.85)
    e = stamp_encode(s, decision_class="C2")
    m = stamp_metabolize(
        e,
        human_state=0.50,
        machine_state=0.50,
        cognitive_entropy_rate=0.50,
        e1=0.50,
        e2=0.50,
        e3=0.50,
        e4=0.50,
    )
    # machine_entropy = 0.30·0.5 + 0.20·0.5 + 0.20·0.5 + 0.30·0.5 = 0.5
    # metabolic_flux = 0.55·0.5 + 0.45·0.5 = 0.5
    assert abs(m["machine_entropy"] - 0.5) < 0.01
    assert abs(m["metabolic_flux"] - 0.5) < 0.01


# ============================================================================
# 5. STAGE 4 — JUDGE (F1–F13 floors + arifOS verdict)
# ============================================================================


def test_judge_f13_hold_on_c5():
    """C5 irreversible → F13_sovereign=HOLD until F13 ratifies."""
    s = stamp_ingress({"x": 1}, consent_verified=True, dignity_preservation=0.85)
    e = stamp_encode(s, decision_class="C5")
    m = stamp_metabolize(e)
    j = stamp_judge(m, arifOS_verdict="SEAL", arifOS_attested=True)
    assert j["floor_status"]["F13_sovereign"] == "HOLD"
    assert j["ready_for_egress"] is False


def test_judge_f2_void_when_stale():
    """F2_truth=VOID when confidence=VOID."""
    s = stamp_ingress(
        {"x": 1},
        freshness_raw_hours=200.0,
        consent_verified=True,
        dignity_preservation=0.85,
    )
    e = stamp_encode(s, decision_class="C2")
    m = stamp_metabolize(e)
    j = stamp_judge(m, arifOS_verdict="SEAL", arifOS_attested=True)
    assert j["floor_status"]["F2_truth"] == "VOID"


def test_judge_f6_void_on_coercion():
    """F6_maruah=VOID when coercion present."""
    s = stamp_ingress(
        {"x": 1},
        consent_verified=True,
        coercion_signals=["forced_oversight"],
        dignity_preservation=0.85,
    )
    e = stamp_encode(s, decision_class="C2")
    m = stamp_metabolize(e)
    j = stamp_judge(m, arifOS_verdict="SEAL", arifOS_attested=True)
    assert j["floor_status"]["F6_maruah"] == "VOID"


def test_judge_ready_when_seal_and_all_pass():
    """Ready when SEAL + arifOS_attested + all floors PASS."""
    s = stamp_ingress(
        {"x": 1},
        freshness_raw_hours=2.0,
        consent_verified=True,
        dignity_preservation=0.85,
    )
    e = stamp_encode(s, decision_class="C2")
    m = stamp_metabolize(e, human_state=0.90, machine_state=0.90, governance_state=0.95)
    j = stamp_judge(m, arifOS_verdict="SEAL", arifOS_attested=True)
    assert j["ready_for_egress"] is True


def test_judge_pending_when_arifos_not_attested():
    """Verdict=PENDING when arifOS not yet called."""
    s = stamp_ingress({"x": 1}, consent_verified=True, dignity_preservation=0.85)
    e = stamp_encode(s, decision_class="C2")
    m = stamp_metabolize(e)
    j = stamp_judge(m, arifOS_attested=False)
    assert j["arifOS_verdict"] == "PENDING"
    assert j["ready_for_egress"] is False


# ============================================================================
# 6. STAGE 5 — EGRESS
# ============================================================================


def test_egress_assembles_loop_trace():
    """Egress includes the full 5-stage loop_trace."""
    s = stamp_ingress({"x": 1}, consent_verified=True, dignity_preservation=0.85)
    e = stamp_encode(s, decision_class="C2")
    m = stamp_metabolize(e)
    j = stamp_judge(m, arifOS_verdict="SEAL", arifOS_attested=True)
    out = stamp_egress(j)
    assert out["loop_trace"] == ["ingress", "encode", "metabolize", "judge", "egress"]
    assert out["stage"] == "egress"
    assert out["loop_complete"] is True
    assert out["ready_to_observe"] is True


def test_egress_never_writes_vault():
    """Egress output has no vault_write field (WELL never writes vault)."""
    s = stamp_ingress({"x": 1}, consent_verified=True, dignity_preservation=0.85)
    e = stamp_encode(s, decision_class="C2")
    m = stamp_metabolize(e)
    j = stamp_judge(m, arifOS_verdict="SEAL", arifOS_attested=True)
    out = stamp_egress(j)
    assert "vault_write" not in out
    assert "sealed" not in out or out.get("arifOS_verdict") != "SEAL"


# ============================================================================
# 7. END-TO-END (run_loop convenience)
# ============================================================================


def test_run_loop_happy_path():
    """Full run_loop on a healthy input."""
    out = run_loop(
        payload={"signal": "cognitive_clarity", "value": 0.85},
        substrate_canon="human",
        decision_class="C2",
        actor_id="arif",
        freshness_raw_hours=2.0,
        human_state=0.85,
        machine_state=0.90,
        governance_state=0.95,
        consent_verified=True,
        dignity_preservation=0.85,
        arifOS_verdict="SEAL",
        arifOS_attested=True,
    )
    assert out["stage"] == "egress"
    assert out["ready_for_egress"] is True
    assert out["readiness_verdict"] in ("STABLE", "OPTIMAL")
    assert all(v == "PASS" for v in out["floor_status"].values())


def test_run_loop_machine_critical():
    """Machine CRITICAL → CRITICAL readiness, low coupling."""
    out = run_loop(
        payload={"signal": "machine_state"},
        substrate_canon="machine",
        decision_class="C2",
        consent_verified=True,
        dignity_preservation=0.85,
        machine_state=0.05,
        arifOS_verdict="SEAL",
        arifOS_attested=True,
    )
    assert out["coupling_state"] < 0.15
    assert out["readiness_verdict"] == "CRITICAL"


def test_run_loop_dignity_violation_downgrades():
    """Dignity violation → decision_class downgraded to C1."""
    out = run_loop(
        payload={"signal": "fatigue"},
        decision_class="C3",
        consent_verified=True,
        dignity_preservation=0.50,  # below floor
        arifOS_verdict="SEAL",
        arifOS_attested=True,
    )
    assert out["decision_class"] == "C1"
    assert "dignity_leakage_advisory" in out


def test_run_loop_c5_irreversible_holds():
    """C5 irreversible → F13 HOLD, not ready_for_egress."""
    out = run_loop(
        payload={"intent": "vault_seal"},
        decision_class="C5",
        consent_verified=True,
        dignity_preservation=0.95,
        arifOS_verdict="SEAL",
        arifOS_attested=True,
    )
    assert out["floor_status"]["F13_sovereign"] == "HOLD"
    assert out["ready_for_egress"] is False


# ============================================================================
# 8. LOOP-MAPPED PROMPTS
# ============================================================================


def test_loop_map_covers_all_9_stages():
    """LOOP_MAP includes all 9 canonical stages."""
    from well_mcp.prompts import LOOP_MAP

    expected = {
        "000_INIT",
        "111_SENSE",
        "333_REASON",
        "444_COMPOSE",
        "555_ROUTE",
        "666_CRITIQUE",
        "777_REPAIR",
        "888_JUDGE",
        "999_SEAL",
    }
    assert set(LOOP_MAP.values()) == expected


# ============================================================================
# 9. CANON RESOURCES (12 expected)
# ============================================================================


def test_all_12_canon_resources_registered():
    """All 12 well:// resources are importable."""
    from well_mcp.resources import RESOURCE_MODULES

    expected_names = {
        "identity",
        "doctrine",
        "bio_signals",
        "flux",
        "decision_classes",
        "coupling",
        "human_substrate",
        "machine_substrate",
        "chemistry_glue",
        "transport_loop",
        "registry",
        "physics_laws",
    }
    actual_names = {m.__name__.split(".")[-1] for m in RESOURCE_MODULES}
    assert actual_names == expected_names


# ============================================================================
# RUNNER
# ============================================================================

if __name__ == "__main__":
    import traceback

    test_funcs = [
        v for k, v in globals().items() if k.startswith("test_") and callable(v)
    ]
    passed = 0
    failed = 0
    for tf in test_funcs:
        try:
            tf()
            passed += 1
            print(f"  PASS  {tf.__name__}")
        except Exception:
            failed += 1
            print(f"  FAIL  {tf.__name__}")
            traceback.print_exc()
    print()
    print(f"  Total: {passed + failed} | Passed: {passed} | Failed: {failed}")
    sys.exit(0 if failed == 0 else 1)
