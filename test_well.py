"""
WELL MCP Audit Test Suite
Red · Blue · Gold Team Validation
"""

import asyncio
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

well_dir = Path(__file__).parent
test_dir = Path(tempfile.mkdtemp(prefix="afwell-test-"))
os.environ["WELL_STATE_PATH"] = str(test_dir / "state.json")
os.environ["WELL_EVENTS_PATH"] = str(test_dir / "events.jsonl")
os.environ["WELL_VAULT_PATH"] = str(test_dir / "vault_ledger.jsonl")
server_path = well_dir / "server.py"
spec = importlib.util.spec_from_file_location("afwell_server_under_test", server_path)
assert spec and spec.loader
server_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server_module)
mcp = server_module.mcp


def _write_canonical_state(**overrides):
    """Write a canonical WELL state with optional overrides."""
    import datetime
    state = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "operator_id": "arif",
        "identity": "WELL",
        "role": "Body / Human Intelligence",
        "authority": "REFLECT_ONLY",
        "delta_s": 0.0,
        "peace2": 1.0,
        "kappa_r": 0.95,
        "rasa": True,
        "amanah": "LOCK",
        "metrics": {
            "sleep": {"last_night_hours": 8, "sleep_debt_days": 0, "quality_score": 9},
            "stress": {"subjective_load": 2, "restlessness": 1},
            "cognitive": {"clarity": 10, "decision_fatigue": 2.1, "focus_durability": 9, "pressure_sources": {}},
            "metabolic": {"fasting_window_hours": 0, "perceived_stability": 10, "hydration_status": "STABLE"},
            "structural": {"pain_map": [], "movement_frequency_daily": 5},
        },
        "well_score": 93.8,
        "floors_violated": [],
        "m_machine": {
            "model_reliability": 1.0,
            "tool_availability": 1.0,
            "latency_ms": 200,
            "context_length_pressure": 0.0,
            "memory_integrity": 1.0,
            "api_failure_rate": 0.0,
            "data_freshness": 1.0,
            "compute_budget_pct": 100.0,
            "token_budget_pct": 100.0,
            "security_flags": [],
            "vault_status": "ok",
            "schema_valid": True,
        },
    }
    state.update(overrides)
    Path(os.environ["WELL_STATE_PATH"]).write_text(json.dumps(state))
    return state


def get_data(result):
    """Helper to extract dict from ToolResult."""
    if hasattr(result, "structured_content") and result.structured_content:
        return result.structured_content
    if hasattr(result, "content") and result.content:
        return json.loads(result.content[0].text)
    return {}


# ═══════════════════════════════════════════════════════════════════════════════
# GOLD TEAM — Identity Invariant Tests
# ═══════════════════════════════════════════════════════════════════════════════


def test_identity_invariant_pass():
    _write_canonical_state()
    assert server_module.is_well() is True


def test_identity_invariant_missing_identity():
    _write_canonical_state(identity="NOT_WELL")
    assert server_module.is_well() is False


def test_identity_invariant_missing_role():
    _write_canonical_state(role="Executor")
    assert server_module.is_well() is False


def test_identity_invariant_low_delta_s():
    _write_canonical_state(delta_s=-0.1)
    assert server_module.is_well() is False


def test_identity_invariant_low_peace2():
    _write_canonical_state(peace2=0.5)
    assert server_module.is_well() is False


def test_identity_invariant_low_kappa_r():
    _write_canonical_state(kappa_r=0.5)
    assert server_module.is_well() is False


def test_identity_invariant_rasa_false():
    _write_canonical_state(rasa=False)
    assert server_module.is_well() is False


def test_identity_invariant_amanah_unlocked():
    _write_canonical_state(amanah="UNLOCKED")
    assert server_module.is_well() is False


def test_identity_invariant_authority_overclaim():
    _write_canonical_state(authority="JUDGE")
    assert server_module.is_well() is False


# ═══════════════════════════════════════════════════════════════════════════════
# BLUE TEAM — Input Validation & Adversarial Tests
# ═══════════════════════════════════════════════════════════════════════════════


async def _test_input_validation():
    _write_canonical_state()

    # Negative sleep_hours should be clamped to 0, not crash
    res = await mcp.call_tool("well_log", arguments={"sleep_hours": -100})
    data = get_data(res)
    assert data["ok"] is True, f"Expected ok=True for clamped negative, got {data}"

    # Out-of-range clarity should be clamped
    res = await mcp.call_tool("well_log", arguments={"clarity": 999})
    data = get_data(res)
    assert data["ok"] is True, f"Expected ok=True for clamped high clarity, got {data}"

    # String where number expected should fail gracefully
    # FastMCP/Pydantic rejects at the transport layer; we verify it does not mutate state
    try:
        res = await mcp.call_tool("well_log", arguments={"sleep_hours": "hacked"})
        data = get_data(res)
        assert data["ok"] is False, f"Expected ok=False for string input, got {data}"
    except Exception as e:
        # Pydantic validation error is acceptable — it means schema enforcement is active
        assert "float_parsing" in str(e) or "ValidationError" in str(e) or "unable to parse" in str(e)

    # Verify state was not corrupted by the rejected call
    state_after = server_module._load_state()
    assert state_after.get("well_score") is not None

    # None values should pass (omitted fields)
    res = await mcp.call_tool("well_log", arguments={"sleep_hours": None})
    data = get_data(res)
    assert data["ok"] is True

    # Injection attempt in note should be sanitized
    res = await mcp.call_tool("well_log", arguments={"note": "malicious\x00null\x01byte"})
    data = get_data(res)
    assert data["ok"] is True


async def _test_well_state_reflect_only():
    _write_canonical_state()
    res = await mcp.call_tool("well_state")
    data = get_data(res)
    assert data["ok"] is True
    assert data.get("w0") == "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT"


async def _test_well_log_green_path():
    _write_canonical_state()
    res = await mcp.call_tool("well_log", arguments={"note": "Automated test run"})
    data = get_data(res)
    assert data["ok"] is True


async def _test_well_check_floors_canonical():
    _write_canonical_state()
    res = await mcp.call_tool("well_check_floors")
    data = get_data(res)
    assert data["mcp"] == "AFWELL"
    assert "status" in data
    assert data.get("authority", {}).get("level") == "advisory_only"


async def _test_well_readiness_canonical():
    _write_canonical_state()
    res = await mcp.call_tool("well_readiness")
    data = get_data(res)
    assert data["mcp"] == "AFWELL"
    assert "risk_level" in data
    assert data.get("authority", {}).get("level") == "advisory_only"


async def _test_well_log_state_green():
    _write_canonical_state()
    res = await mcp.call_tool("well_log_state", arguments={
        "sleep_hours": 8,
        "stress_level": 2,
        "clarity_score": 9,
        "note": "Test Green Path"
    })
    data = get_data(res)
    assert data["tier"] == "GREEN"


async def _test_well_log_state_red():
    _write_canonical_state()
    res = await mcp.call_tool("well_log", arguments={
        "sleep_hours": 2,
        "sleep_debt_days": 5,
        "stress_load": 10,
        "clarity": 2,
        "decision_fatigue": 9,
        "note": "Test Red Path - Extreme Stress"
    })
    data = get_data(res)
    assert data["tier"] == "RED"
    assert data["human_decision_required"] is True
    assert "W1_SLEEP_DEBT" in data["floors_violated"]
    assert "W5_COGNITIVE_ENTROPY" in data["floors_violated"]


async def _test_well_get_readiness():
    _write_canonical_state()
    res = await mcp.call_tool("well_get_readiness")
    data = get_data(res)
    assert data["ok"] is True
    assert "readiness" in data


async def _test_well_check_floor_w1():
    _write_canonical_state()
    res = await mcp.call_tool("well_check_floor", arguments={"floor_id": "W1"})
    data = get_data(res)
    if "mcp" in data:
        assert data["mcp"] == "AFWELL"
    else:
        assert data["floor"] == "W1"


async def _test_well_list_log():
    _write_canonical_state()
    res = await mcp.call_tool("well_list_log", arguments={"limit": 5})
    data = get_data(res)
    assert data["ok"] is True


async def _test_well_seal_vault():
    _write_canonical_state()
    res = await mcp.call_tool("well_seal_vault", arguments={"force": True})
    data = get_data(res)
    # Should fail gracefully (no arifOS in test env), but not leak secrets
    assert "error" not in data or "Vault bridge unavailable" in data.get("error", "")


async def _test_well_coupled_readiness():
    _write_canonical_state()
    res = await mcp.call_tool("well_coupled_readiness")
    data = get_data(res)
    assert data["mcp"] == "AFWELL"
    assert "risk_level" in data
    assert "final_authority" in data
    assert data["final_authority"] == "Arif"


async def _test_well_forge_precheck_conservative():
    _write_canonical_state()
    await mcp.call_tool("well_log", arguments={"stress_load": 9, "clarity": 4})
    res = await mcp.call_tool("well_forge_precheck", arguments={"task_description": "Critical Deployment"})
    data = get_data(res)
    assert data["risk_level"] in ("AMBER", "RED")
    assert data["recommended_mode"] in ("draft_only", "pause")
    assert "final_authority" in data


async def _test_well_decision_classify_advisory_language():
    _write_canonical_state()
    res = await mcp.call_tool("well_decision_classify", arguments={"decision_class": "C5"})
    data = get_data(res)
    assert data["ok"] is True
    # Must not overclaim with BLOCKED / APPROVED
    assert "ADVISORY" in data["verdict"], f"Expected advisory verdict, got {data['verdict']}"


async def _test_well_niat_check_advisory_language():
    _write_canonical_state()
    res = await mcp.call_tool("well_niat_check", arguments={
        "intent": "Deploy production",
        "reversibility": "irreversible"
    })
    data = get_data(res)
    assert data["ok"] is True
    assert "ADVISORY" in data["readiness"], f"Expected advisory readiness, got {data['readiness']}"
    assert "ADVISORY" in data["recommendation"], f"Expected advisory recommendation, got {data['recommendation']}"


async def _test_well_bandwidth_advisory_language():
    _write_canonical_state()
    res = await mcp.call_tool("well_bandwidth_recommendation")
    data = get_data(res)
    assert data["ok"] is True
    # Must not command with LOCKED / FORBIDDEN
    assert "LOCKED" not in data.get("mode", ""), f"Expected non-commanding mode, got {data['mode']}"
    assert "forbidden" not in data, "Must not use 'forbidden' — use 'advised_against'"
    assert "advised_against" in data or "decision_classes_advised_against" in data


async def _test_well_forge_closeout_fatigue_increases():
    _write_canonical_state(metrics={
        "sleep": {"last_night_hours": 8, "sleep_debt_days": 0, "quality_score": 9},
        "stress": {"subjective_load": 2, "restlessness": 1},
        "cognitive": {"clarity": 10, "decision_fatigue": 5.0, "focus_durability": 9, "pressure_sources": {}},
        "metabolic": {"fasting_window_hours": 0, "perceived_stability": 10, "hydration_status": "STABLE"},
        "structural": {"pain_map": [], "movement_frequency_daily": 5},
    })
    res = await mcp.call_tool("well_forge_closeout", arguments={
        "task_description": "test",
        "outcome": "success",
        "errors_encountered": 0,
    })
    data = get_data(res)
    assert data["ok"] is True
    # Fatigue must increase after work (success costs 0.5)
    assert data["fatigue_delta"] > 0, f"Expected fatigue_delta > 0, got {data['fatigue_delta']}"
    assert data["new_fatigue"] > 5.0, f"Expected new_fatigue > 5.0, got {data['new_fatigue']}"


async def _test_well_init_error_no_leak():
    _write_canonical_state()
    res = await mcp.call_tool("well_init")
    data = get_data(res)
    # In test env, arifOS is not available; error must not leak paths
    if not data.get("ok", False):
        err = data.get("error", "")
        assert "arifOS" in err or "Vault bridge unavailable" in err, f"Safe error expected, got: {err}"
        assert "/root/" not in err, f"Path leak in error: {err}"
        assert "traceback" not in err.lower()


async def _test_health_endpoint_identity():
    from starlette.testclient import TestClient
    import uvicorn
    from fastmcp import FastMCP

    # We can't easily mount the HTTP app here, but we can test the handler directly
    _write_canonical_state()
    # The health_handler is defined inside __main__ block; test via is_well + state
    state = server_module._load_state()
    assert server_module.is_well(state) is True
    assert state.get("identity") == "WELL"
    assert state.get("authority") == "REFLECT_ONLY"


# ═══════════════════════════════════════════════════════════════════════════════
# Test Runners
# ═══════════════════════════════════════════════════════════════════════════════


def test_identity_invariants():
    test_identity_invariant_pass()
    test_identity_invariant_missing_identity()
    test_identity_invariant_missing_role()
    test_identity_invariant_low_delta_s()
    test_identity_invariant_low_peace2()
    test_identity_invariant_low_kappa_r()
    test_identity_invariant_rasa_false()
    test_identity_invariant_amanah_unlocked()
    test_identity_invariant_authority_overclaim()
    print("✅ All identity invariant tests passed")


def test_well_tools():
    asyncio.run(_test_well_tools_core())


async def _test_well_tools_core():
    await _test_well_state_reflect_only()
    await _test_well_log_green_path()
    await _test_well_check_floors_canonical()
    await _test_well_readiness_canonical()
    await _test_well_seal_vault()
    print("✅ Core tool tests passed")


def test_well_phase2_tools():
    asyncio.run(_test_well_phase2_core())


async def _test_well_phase2_core():
    await _test_input_validation()
    await _test_well_log_state_green()
    await _test_well_log_state_red()
    await _test_well_get_readiness()
    await _test_well_check_floor_w1()
    await _test_well_list_log()
    print("✅ Phase 2 tool tests passed")


def test_well_integration_fixes():
    asyncio.run(_test_integration_core())


async def _test_well_unknown_telemetry():
    print("\n🧪 Testing WELL UNKNOWN telemetry paths...")

    # Write state with EMPTY metrics but valid identity
    _write_canonical_state(
        metrics={},
        well_score=50,
        floors_violated=[],
        truth_status="UNVERIFIED"
    )

    # 1. well_check_floors must return UNKNOWN, not PASS/GREEN
    print("\n--- Testing well_check_floors (no telemetry) ---")
    res = await mcp.call_tool("well_check_floors")
    data = get_data(res)
    print(f"Result: {data}")
    assert data["domain_verdict"] == "UNKNOWN_TELEMETRY"
    assert data["risk_level"] == "UNKNOWN"
    assert data["recommended_mode"] == "draft_only"

    # 2. well_readiness must return UNKNOWN
    print("\n--- Testing well_readiness (no telemetry) ---")
    res = await mcp.call_tool("well_readiness")
    data = get_data(res)
    print(f"Result: {data}")
    assert data["domain_verdict"] == "UNKNOWN"
    assert data["risk_level"] == "UNKNOWN"
    assert data["confidence"] == "LOW"

    # 3. well_arifos_packet must redact operator_snapshot
    print("\n--- Testing well_arifos_packet (no telemetry) ---")
    res = await mcp.call_tool("well_arifos_packet")
    data = get_data(res)
    print(f"Result: {data}")
    assert data["readiness"] == "UNKNOWN"
    assert data["has_telemetry"] is False
    snap = data.get("operator_snapshot", {})
    assert snap.get("clarity") is None
    assert snap.get("decision_fatigue") is None

    # 4. well_forge_precheck must return UNKNOWN_TELEMETRY
    print("\n--- Testing well_forge_precheck (no telemetry) ---")
    res = await mcp.call_tool("well_forge_precheck", arguments={"task_description": "test"})
    data = get_data(res)
    print(f"Result: {data}")
    assert data["domain_verdict"] == "UNKNOWN_TELEMETRY"
    assert data["risk_level"] == "UNKNOWN"

    # 5. well_bandwidth_recommendation must return UNKNOWN
    print("\n--- Testing well_bandwidth_recommendation (no telemetry) ---")
    res = await mcp.call_tool("well_bandwidth_recommendation")
    data = get_data(res)
    print(f"Result: {data}")
    assert data["verdict"] == "UNKNOWN"
    assert data["has_telemetry"] is False

    # 6. well_daily_brief must return UNKNOWN
    print("\n--- Testing well_daily_brief (no telemetry) ---")
    res = await mcp.call_tool("well_daily_brief")
    data = get_data(res)
    print(f"Result: {data}")
    assert data["readiness"] == "UNKNOWN"
    assert data["has_telemetry"] is False

    # 7. well_check_floor W1 must return UNKNOWN
    print("\n--- Testing well_check_floor W1 (no telemetry) ---")
    res = await mcp.call_tool("well_check_floor", arguments={"floor_id": "W1"})
    data = get_data(res)
    print(f"Result: {data}")
    assert data["domain_verdict"] == "UNKNOWN_TELEMETRY"

    # 8. well_get_readiness must return UNKNOWN tier
    print("\n--- Testing well_get_readiness (no telemetry) ---")
    res = await mcp.call_tool("well_get_readiness")
    data = get_data(res)
    print(f"Result: {data}")
    assert data["readiness"]["tier"] == "UNKNOWN"
    assert data["has_telemetry"] is False

    print("✅ UNKNOWN telemetry tests passed")


async def _test_integration_core():
    await _test_well_coupled_readiness()
    await _test_well_forge_precheck_conservative()
    await _test_well_decision_classify_advisory_language()
    await _test_well_niat_check_advisory_language()
    await _test_well_bandwidth_advisory_language()
    await _test_well_forge_closeout_fatigue_increases()
    await _test_well_init_error_no_leak()
    await _test_health_endpoint_identity()
    print("✅ Integration fix tests passed")


async def _test_canonical_tools():
    print("\n🧪 Testing WELL Canonical 13 tools...")

    _write_canonical_state()

    # WELL-01 well_get_health
    print("\n--- well_get_health ---")
    res = await mcp.call_tool("well_get_health")
    data = get_data(res)
    assert data["identity"] == "WELL"
    assert data["authority"] == "REFLECT_ONLY"
    assert data["verdict"] in ("WELL_PASS", "PASS")

    # WELL-02 well_get_state
    print("\n--- well_get_state ---")
    res = await mcp.call_tool("well_get_state")
    data = get_data(res)
    assert data["ok"] is True
    assert data["has_telemetry"] is True
    res = await mcp.call_tool("well_get_state", arguments={"domain": "machine"})
    data = get_data(res)
    assert "m_machine" in data

    # WELL-03 well_check_invariant (identity + floors)
    print("\n--- well_check_invariant ---")
    res = await mcp.call_tool("well_check_invariant")
    data = get_data(res)
    assert data["identity_verdict"] == "WELL_PASS"
    res = await mcp.call_tool("well_check_invariant", arguments={"floor_id": "W0"})
    data = get_data(res)
    assert data["floor"] == "W0"

    # WELL-04 well_log_signal (human)
    print("\n--- well_log_signal (human) ---")
    res = await mcp.call_tool("well_log_signal", arguments={
        "domain": "human",
        "signal": "clarity",
        "value": 8,
        "note": "Canonical test"
    })
    data = get_data(res)
    assert data["ok"] is True

    # WELL-04 well_log_signal (machine)
    print("\n--- well_log_signal (machine) ---")
    res = await mcp.call_tool("well_log_signal", arguments={
        "domain": "machine",
        "signal": "tool_availability",
        "value": 0.95,
    })
    data = get_data(res)
    assert data["ok"] is True

    # WELL-05 well_list_events
    print("\n--- well_list_events ---")
    res = await mcp.call_tool("well_list_events", arguments={"limit": 5, "redact": True})
    data = get_data(res)
    assert data["ok"] is True
    assert data.get("redacted") is True

    # WELL-06 well_reflect_trend
    print("\n--- well_reflect_trend ---")
    res = await mcp.call_tool("well_reflect_trend")
    data = get_data(res)
    assert data["ok"] is True

    # WELL-07 well_reflect_readiness (coupled)
    print("\n--- well_reflect_readiness ---")
    res = await mcp.call_tool("well_reflect_readiness", arguments={"domain": "coupled"})
    data = get_data(res)
    # coupled returns canonical verdict (mcp, task, status) not ok wrapper
    assert data.get("ok") is True or data.get("mcp") == "AFWELL"

    # WELL-08 well_suggest_mode
    print("\n--- well_suggest_mode ---")
    res = await mcp.call_tool("well_suggest_mode", arguments={"domain": "forge", "task_description": "test"})
    data = get_data(res)
    assert data.get("ok") or data.get("mcp") == "AFWELL"

    # WELL-09 well_suggest_recovery
    print("\n--- well_suggest_recovery ---")
    res = await mcp.call_tool("well_suggest_recovery")
    data = get_data(res)
    assert data["ok"] is True

    # WELL-10 well_reflect_niat
    print("\n--- well_reflect_niat ---")
    res = await mcp.call_tool("well_reflect_niat", arguments={"intent": "Deploy to production"})
    data = get_data(res)
    assert data["ok"] is True

    # WELL-11 well_classify_task
    print("\n--- well_classify_task ---")
    res = await mcp.call_tool("well_classify_task", arguments={"decision_class": "C2"})
    data = get_data(res)
    assert data["ok"] is True

    # WELL-12 well_get_packet
    print("\n--- well_get_packet ---")
    res = await mcp.call_tool("well_get_packet", arguments={"target": "arifos", "detail": "minimal"})
    data = get_data(res)
    assert data["ok"] is True

    # WELL-13 well_request_anchor (dry_run)
    print("\n--- well_request_anchor (dry_run) ---")
    res = await mcp.call_tool("well_request_anchor", arguments={"dry_run": True})
    data = get_data(res)
    assert data["ok"] is True
    assert data["dry_run"] is True

    print("✅ Canonical 13 tests passed")


def test_well_unknown_telemetry():
    asyncio.run(_test_well_unknown_telemetry())


def test_canonical_tools():
    asyncio.run(_test_canonical_tools())


# ═══════════════════════════════════════════════════════════════════════════════
# U-WELL — Universal Substrate Vitality Tests
# ═══════════════════════════════════════════════════════════════════════════════


async def _test_universal_classify_substrate():
    print("\n🧪 Testing U-WELL classify_substrate...")

    res = await mcp.call_tool("well_classify_substrate", arguments={"subject": "rock", "description": "granite boulder"})
    data = get_data(res)
    assert data["substrate_class"] == "MATERIAL_OBJECT"
    assert data["vitality_mode"] == "structural integrity, not life"

    res = await mcp.call_tool("well_classify_substrate", arguments={"subject": "virus"})
    data = get_data(res)
    assert data["substrate_class"] == "LIMINAL_BIOLOGICAL"

    res = await mcp.call_tool("well_classify_substrate", arguments={"subject": "AI assistant"})
    data = get_data(res)
    assert data["substrate_class"] == "MACHINE_SYSTEM"

    res = await mcp.call_tool("well_classify_substrate", arguments={"subject": "soul"})
    data = get_data(res)
    assert data["substrate_class"] == "SYMBOLIC_METAPHYSICAL"
    assert data["human_judge_required"] is True

    res = await mcp.call_tool("well_classify_substrate", arguments={"subject": "VP", "description": "vice president person"})
    data = get_data(res)
    assert data["substrate_class"] == "HUMAN_PERSON"

    print("✅ well_classify_substrate tests passed")


async def _test_universal_boundary_check():
    print("\n🧪 Testing U-WELL boundary_check...")

    res = await mcp.call_tool("well_boundary_check", arguments={
        "subject": "rock", "substrate_class": "MATERIAL_OBJECT", "evaluation_intent": "alive_check"
    })
    data = get_data(res)
    assert data["category_error"] is True
    assert data["boundary_violated"] is True

    res = await mcp.call_tool("well_boundary_check", arguments={
        "subject": "soul", "substrate_class": "SYMBOLIC_METAPHYSICAL", "evaluation_intent": "quantify"
    })
    data = get_data(res)
    assert data["category_error"] is True
    assert data["authority_scope"] == "mirror_and_protect_only"

    res = await mcp.call_tool("well_boundary_check", arguments={
        "subject": "Arif", "substrate_class": "HUMAN_PERSON", "evaluation_intent": "vitality"
    })
    data = get_data(res)
    assert data["intent_valid"] is True
    assert data["boundary_violated"] is False

    print("✅ well_boundary_check tests passed")


async def _test_universal_evidence_quality():
    print("\n🧪 Testing U-WELL evidence_quality_check...")

    res = await mcp.call_tool("well_evidence_quality_check", arguments={
        "evidence_source": "direct_observation", "corroboration_count": 2
    })
    data = get_data(res)
    assert data["evidence_quality"] == "STRONG"

    res = await mcp.call_tool("well_evidence_quality_check", arguments={
        "evidence_source": "hearsay", "evidence_age_hours": 200
    })
    data = get_data(res)
    assert data["evidence_quality"] == "INSUFFICIENT"

    print("✅ well_evidence_quality_check tests passed")


async def _test_universal_verdict_packet():
    print("\n🧪 Testing U-WELL verdict_packet...")

    res = await mcp.call_tool("well_verdict_packet", arguments={
        "subject": "rock",
        "substrate_class": "MATERIAL_OBJECT",
        "alive_biologically": False,
        "operational_vitality": "structural_intact",
    })
    data = get_data(res)
    assert data["subject"] == "rock"
    assert data["alive_biologically"] is False
    assert data["machine_authority"] == "advisory_only"
    assert data["w0"] == "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT"

    print("✅ well_verdict_packet tests passed")


async def _test_universal_livelihood_energy():
    print("\n🧪 Testing U-WELL livelihood_energy_check...")

    _write_canonical_state()
    res = await mcp.call_tool("well_livelihood_energy_check")
    data = get_data(res)
    assert data["ok"] is True
    assert "status" in data
    assert "gap" in data

    # Explicit parameters override state
    res = await mcp.call_tool("well_livelihood_energy_check", arguments={
        "energy_level": 2, "duty_load": 9
    })
    data = get_data(res)
    assert data["status"] == "CRITICAL_DEFICIT"
    assert data["human_judge_required"] is True

    print("✅ well_livelihood_energy_check tests passed")


async def _test_universal_livelihood_time():
    print("\n🧪 Testing U-WELL livelihood_time_check...")

    _write_canonical_state()
    res = await mcp.call_tool("well_livelihood_time_check")
    data = get_data(res)
    assert data["ok"] is True
    assert "time_sovereignty_score" in data

    res = await mcp.call_tool("well_livelihood_time_check", arguments={
        "time_sovereignty_score": 2, "competing_demands": ["work", "family", "coding"]
    })
    data = get_data(res)
    assert data["status"] == "LOW"
    assert data["human_judge_required"] is True

    print("✅ well_livelihood_time_check tests passed")


async def _test_universal_livelihood_role():
    print("\n🧪 Testing U-WELL livelihood_role_check...")

    res = await mcp.call_tool("well_livelihood_role_check", arguments={
        "role_clarity": 8, "role_burden": 3
    })
    data = get_data(res)
    assert data["status"] == "HEALTHY"

    res = await mcp.call_tool("well_livelihood_role_check", arguments={
        "role_clarity": 2, "role_burden": 9, "role_contradictions": ["conflict_of_interest"]
    })
    data = get_data(res)
    assert data["status"] == "OVERLOADED"

    print("✅ well_livelihood_role_check tests passed")


async def _test_universal_livelihood_meaning():
    print("\n🧪 Testing U-WELL livelihood_meaning_check...")

    res = await mcp.call_tool("well_livelihood_meaning_check", arguments={
        "purpose_alignment": 8, "niat_clarity": 9
    })
    data = get_data(res)
    assert data["status"] == "ALIGNED"

    res = await mcp.call_tool("well_livelihood_meaning_check", arguments={
        "purpose_alignment": 2, "niat_clarity": 3
    })
    data = get_data(res)
    assert data["status"] == "MISALIGNED"

    print("✅ well_livelihood_meaning_check tests passed")


async def _test_universal_livelihood_dignity():
    print("\n🧪 Testing U-WELL livelihood_dignity_check...")

    res = await mcp.call_tool("well_livelihood_dignity_check", arguments={
        "dignity_preservation": 8, "coercion_signals": []
    })
    data = get_data(res)
    assert data["status"] == "PRESERVED"

    res = await mcp.call_tool("well_livelihood_dignity_check", arguments={
        "dignity_preservation": 2, "coercion_signals": ["forced_overtime", "verbal_abuse"]
    })
    data = get_data(res)
    assert data["status"] == "VIOLATED"
    assert data["human_judge_required"] is True

    print("✅ well_livelihood_dignity_check tests passed")


async def _test_universal_bio_viability():
    print("\n🧪 Testing U-WELL bio_viability_check...")

    # Alive organism
    res = await mcp.call_tool("well_bio_viability_check", arguments={
        "has_metabolism": True, "has_homeostasis": True, "has_growth_repair": True,
        "has_response": True, "has_reproduction": True, "host_dependency": "independent"
    })
    data = get_data(res)
    assert data["viability"] == "ALIVE"

    # Virus (liminal)
    res = await mcp.call_tool("well_bio_viability_check", arguments={
        "has_metabolism": False, "has_reproduction": True, "host_dependency": "host_dependent"
    })
    data = get_data(res)
    assert data["viability"] == "LIMINAL"

    # Dead
    res = await mcp.call_tool("well_bio_viability_check", arguments={
        "has_metabolism": False, "has_homeostasis": False, "has_growth_repair": False,
        "has_response": False, "has_reproduction": False
    })
    data = get_data(res)
    assert data["viability"] == "DEAD"

    print("✅ well_bio_viability_check tests passed")


async def _test_universal_material_integrity():
    print("\n🧪 Testing U-WELL material_integrity_check...")

    res = await mcp.call_tool("well_material_integrity_check", arguments={
        "material_type": "concrete beam", "structural_condition": "good", "age_years": 5
    })
    data = get_data(res)
    assert data["status"] == "SOUND"
    assert data["alive_biologically"] is False

    res = await mcp.call_tool("well_material_integrity_check", arguments={
        "material_type": "rusted pipe", "structural_condition": "critical", "hazard_flags": ["toxic_leak"]
    })
    data = get_data(res)
    assert data["status"] == "CRITICAL"
    assert "toxic_leak" in data["hazard_flags"]

    print("✅ well_material_integrity_check tests passed")


async def _test_universal_institution_entropy():
    print("\n🧪 Testing U-WELL institution_entropy_check...")

    res = await mcp.call_tool("well_institution_entropy_check", arguments={
        "mission_clarity": 8, "cashflow_status": "positive", "role_integrity": 7, "trust_trend": "stable"
    })
    data = get_data(res)
    assert data["status"] == "VIABLE"

    res = await mcp.call_tool("well_institution_entropy_check", arguments={
        "mission_clarity": 2, "cashflow_status": "critical", "role_integrity": 3, "trust_trend": "falling"
    })
    data = get_data(res)
    assert data["status"] == "DEGRADING"
    assert "cashflow_crisis" in data["entropy_flags"]

    print("✅ well_institution_entropy_check tests passed")


async def _test_universal_info_coherence():
    print("\n🧪 Testing U-WELL info_coherence_check...")

    res = await mcp.call_tool("well_info_coherence_check", arguments={
        "internal_consistency": 8, "version_integrity": True, "executable_status": "passing", "maintainability_score": 7
    })
    data = get_data(res)
    assert data["status"] == "COHERENT"

    res = await mcp.call_tool("well_info_coherence_check", arguments={
        "internal_consistency": 2, "version_integrity": False, "executable_status": "broken"
    })
    data = get_data(res)
    assert data["status"] == "FRAGMENTED"

    print("✅ well_info_coherence_check tests passed")


async def _test_universal_symbolic_domain():
    print("\n🧪 Testing U-WELL symbolic_domain_check...")

    res = await mcp.call_tool("well_symbolic_domain_check", arguments={"subject": "soul"})
    data = get_data(res)
    assert data["is_symbolic_domain"] is True
    assert data["machine_authority"] == "none"
    assert "quantify" in data["invalid_well_action"]

    res = await mcp.call_tool("well_symbolic_domain_check", arguments={"subject": "rock"})
    data = get_data(res)
    assert data["is_symbolic_domain"] is False
    assert data["machine_authority"] == "advisory_only"

    res = await mcp.call_tool("well_symbolic_domain_check", arguments={
        "subject": "dignity", "reductionism_risk": 9
    })
    data = get_data(res)
    assert data["reductionism_status"] == "HIGH_RISK"
    assert data["guard_action"] == "BLOCK_REDUCTION"

    print("✅ well_symbolic_domain_check tests passed")


async def _test_universal_tools_core():
    await _test_universal_classify_substrate()
    await _test_universal_boundary_check()
    await _test_universal_evidence_quality()
    await _test_universal_verdict_packet()
    await _test_universal_livelihood_energy()
    await _test_universal_livelihood_time()
    await _test_universal_livelihood_role()
    await _test_universal_livelihood_meaning()
    await _test_universal_livelihood_dignity()
    await _test_universal_bio_viability()
    await _test_universal_material_integrity()
    await _test_universal_institution_entropy()
    await _test_universal_info_coherence()
    await _test_universal_symbolic_domain()
    print("\n✅ All U-WELL universal substrate tests passed")


async def _test_omega_well_core():
    print("\n🧪 Testing Ω-WELL 13-Tool Polymorphic Stack...")

    _write_canonical_state()

    # Ω-00 init
    print("--- well_classify_substrate (init) ---")
    res = await mcp.call_tool("well_classify_substrate", arguments={"mode": "assert"})
    data = get_data(res)
    assert data["ok"] is True
    assert data["Ω"]["stage"] == "000_INIT"
    assert "arifos" in data
    assert "aaa" in data

    # Ω-01 sense
    print("--- well_classify_substrate (sense) ---")
    res = await mcp.call_tool("well_classify_substrate", arguments={"mode": "classify", "subject": "virus"})
    data = get_data(res)
    assert data["Ω"]["stage"] == "111_SENSE"
    assert data["data"]["substrate_class"] == "LIMINAL_BIOLOGICAL"

    res = await mcp.call_tool("well_classify_substrate", arguments={"mode": "boundary", "subject": "soul", "evaluation_intent": "quantify"})
    data = get_data(res)
    assert data["Ω"]["verdict"] == "HOLD"

    # Ω-02 fetch
    print("--- well_measure_gradient ---")
    res = await mcp.call_tool("well_measure_gradient", arguments={"mode": "evidence", "evidence_source": "direct_observation", "corroboration_count": 2})
    data = get_data(res)
    assert data["Ω"]["stage"] == "222_FETCH"
    assert data["data"]["evidence_quality"] == "STRONG"

    # Ω-03 mind
    print("--- well_assess_metabolism ---")
    res = await mcp.call_tool("well_assess_metabolism", arguments={"mode": "human"})
    data = get_data(res)
    assert data["Ω"]["stage"] == "333_MIND"
    assert "energy" in data["data"]
    assert "dignity" in data["data"]

    res = await mcp.call_tool("well_assess_metabolism", arguments={"mode": "symbolic", "subject": "soul"})
    data = get_data(res)
    assert data["Ω"]["lane"] == "APEX"

    res = await mcp.call_tool("well_assess_metabolism", arguments={"mode": "material", "material_type": "beam", "structural_condition": "critical"})
    data = get_data(res)
    assert data["data"]["status"] == "CRITICAL"

    # Ω-04 kernel
    print("--- well_reflect_intelligence ---")
    res = await mcp.call_tool("well_reflect_intelligence", arguments={"mode": "route"})
    data = get_data(res)
    assert data["Ω"]["stage"] == "444_KERNEL"
    assert data["data"]["recommended_lane"] in ("AGI", "ASI", "APEX")

    res = await mcp.call_tool("well_reflect_intelligence", arguments={"mode": "list"})
    data = get_data(res)
    assert "AGI" in data["data"]["lanes"]

    # Ω-05 memory
    print("--- well_trace_lineage ---")
    res = await mcp.call_tool("well_trace_lineage", arguments={"mode": "context"})
    data = get_data(res)
    assert data["Ω"]["stage"] == "555_MEMORY"
    assert "state" in data["data"]

    # Ω-06 heart
    print("--- well_guard_dignity ---")
    res = await mcp.call_tool("well_assess_homeostasis", arguments={"mode": "empathize"})
    data = get_data(res)
    assert data["Ω"]["stage"] == "666_HEART"
    assert "human_impact_load" in data["data"]

    res = await mcp.call_tool("well_assess_homeostasis", arguments={"mode": "redteam"})
    data = get_data(res)
    assert "attack_surface" in data["data"]

    res = await mcp.call_tool("well_guard_dignity", arguments={"mode": "maruah", "dignity_preservation": 8})
    data = get_data(res)
    assert data["data"]["maruah_score"] >= 0.7

    # Ω-07 forge
    print("--- well_check_repair ---")
    res = await mcp.call_tool("well_check_repair", arguments={"mode": "mode"})
    data = get_data(res)
    assert data["Ω"]["stage"] == "777_FORGE"

    res = await mcp.call_tool("well_check_repair", arguments={"mode": "bandwidth"})
    data = get_data(res)
    assert data["ok"] is True

    # Ω-08 judge
    print("--- well_validate_vitality ---")
    res = await mcp.call_tool("well_validate_vitality", arguments={"mode": "readiness"})
    data = get_data(res)
    assert data["Ω"]["stage"] == "888_JUDGE"

    res = await mcp.call_tool("well_validate_vitality", arguments={"mode": "niat", "intent": "test", "reversibility": "reversible"})
    data = get_data(res)
    assert data["ok"] is True

    # Ω-09 vault (dry_run)
    print("--- well_anchor_evidence ---")
    res = await mcp.call_tool("well_anchor_evidence", arguments={"mode": "anchor", "dry_run": True})
    data = get_data(res)
    assert data["Ω"]["stage"] == "999_VAULT"

    res = await mcp.call_tool("well_anchor_evidence", arguments={"mode": "verify"})
    data = get_data(res)
    assert data["ok"] is True

    # Ω-10 reply
    print("--- well_anchor_evidence (reply) ---")
    res = await mcp.call_tool("well_anchor_evidence", arguments={"mode": "packet", "target": "arifos", "detail": "minimal"})
    data = get_data(res)
    assert data["Ω"]["stage"] == "444r_REPLY"

    res = await mcp.call_tool("well_anchor_evidence", arguments={"mode": "brief"})
    data = get_data(res)
    assert data["ok"] is True

    # Ω-11 gateway
    print("--- well_detect_boundary ---")
    res = await mcp.call_tool("well_detect_boundary", arguments={"mode": "status"})
    data = get_data(res)
    assert data["Ω"]["stage"] == "444g_GATEWAY"

    res = await mcp.call_tool("well_detect_boundary", arguments={"mode": "manifest"})
    data = get_data(res)
    assert "federation" in data["data"]

    # Ω-12 ops
    print("--- well_assess_reliability ---")
    res = await mcp.call_tool("well_assess_reliability", arguments={"mode": "health"})
    data = get_data(res)
    assert data["Ω"]["stage"] == "000_OPS"

    res = await mcp.call_tool("well_assess_reliability", arguments={"mode": "vitals"})
    data = get_data(res)
    assert "human_health" in data["data"]
    assert "machine_health" in data["data"]

    # Ω-13 unified packet — live reflection via well_get_packet
    print("--- well_get_packet (unified) ---")
    res = await mcp.call_tool("well_get_packet", arguments={"target": "unified"})
    data = get_data(res)
    assert data["ok"] is True
    assert "human" in data
    assert "machine" in data
    assert "mcp" in data
    assert "coupled" in data
    assert data["coupled"]["human_ready"] in ("READY", "OPTIMAL", "DEGRADED", "UNKNOWN", "LOW_CAPACITY", "FUNCTIONAL")
    assert data["coupled"]["machine_ready"] in ("HEALTHY", "DEGRADED", "CRITICAL")
    assert data["coupled"]["mcp_ready"] in ("HEALTHY", "DEGRADED")
    assert data["w0"] == "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT"

    # Ω-13 unified packet — anchor receipt via well_anchor_evidence
    print("--- well_anchor_evidence (unified) ---")
    res = await mcp.call_tool("well_anchor_evidence", arguments={"mode": "unified", "dry_run": True})
    data = get_data(res)
    assert data["ok"] is True
    assert "receipt_hash" in data["data"]
    assert data["data"]["dry_run"] is True
    assert data["data"]["coupled_verdict"] in ("PROCEED", "CAUTION", "HOLD")

    print("✅ All Ω-WELL 13-tool tests passed")


def test_omega_well_tools():
    asyncio.run(_test_omega_well_core())


# test_universal_tools() removed — U-WELL Phase 4 tools absorbed into Ω-WELL modes.
# Use test_omega_well_tools() for universal substrate coverage.


def test_omega_well_tools():
    asyncio.run(_test_omega_well_core())


# ═══════════════════════════════════════════════════════════════════════════════
# G-WELL Registry Truth Gate
# Every declared tool must be callable at runtime.
# ═══════════════════════════════════════════════════════════════════════════════


def test_well_registry_declared_surface_matches_callable():
    """
    G-WELL Registry Truth Gate:
    No declared tool may exist only in docs/manifest/schema.
    Every declared tool must be callable at runtime.
    """
    print("\n🧪 Testing G-WELL Registry Truth Gate...")

    # All tools that should exist at runtime
    DECLARED_TOOLS = {
        # Heartbeat
        "mcp_health_check",
        # Legacy (Phase 1-2)
        "well_state", "well_log", "well_readiness", "well_init", "well_anchor",
        "well_check_floors", "well_check_floor", "well_log_state", "well_get_readiness",
        "well_list_log", "well_seal_vault", "well_get_health", "well_get_state",
        "well_check_invariant", "well_log_signal", "well_list_events", "well_reflect_trend",
        "well_reflect_readiness", "well_suggest_mode", "well_suggest_recovery",
        "well_reflect_niat", "well_classify_task", "well_get_packet", "well_request_anchor",
        "well_trend_analysis", "well_bandwidth_recommendation", "well_recovery_protocol",
        "well_niat_check", "well_decision_classify", "well_arifos_packet", "well_consent_status",
        "well_medical_boundary", "well_pressure_ledger", "well_daily_brief",
        "well_machine_state", "well_coupled_readiness",
        "well_decision_bandwidth", "well_forge_precheck", "well_forge_closeout",
        # Ω-WELL aliases (13)
        "well_000_init", "well_111_sense", "well_222_fetch", "well_333_mind",
        "well_444_kernel", "well_555_memory", "well_666_heart", "well_777_forge",
        "well_888_judge", "well_999_vault", "well_444_reply", "well_444_gateway",
        "well_000_ops",
        # Canonical 13
        "well_classify_substrate", "well_trace_lineage", "well_detect_boundary",
        "well_measure_gradient", "well_assess_metabolism", "well_assess_homeostasis",
        "well_check_repair", "well_validate_vitality", "well_assess_livelihood",
        "well_assess_reliability", "well_reflect_intelligence", "well_guard_dignity",
        "well_anchor_evidence",
        # G-WELL governance
        "well_assess_governance", "well_trace_decision", "well_validate_consensus",
        # M-WELL expansion
        "well_machine_log_signal", "well_machine_trend", "well_machine_health_probe",
        # H-WELL expansion
        "well_fatigue_accumulator", "well_circadian_phase",
    }

    _write_canonical_state()
    import asyncio

    async def _check_registry():
        tools = await mcp.call_tool("mcp_health_check")  # verify server is loaded
        all_tools = await mcp.list_tools()
        callable_names = {t.name for t in all_tools}

        missing = DECLARED_TOOLS - callable_names
        extra = callable_names - DECLARED_TOOLS

        if missing:
            print(f"\n  ❌ Missing from runtime: {sorted(missing)}")
        if extra:
            print(f"\n  📝 Undeclared but present: {sorted(extra)[:10]}...")

        assert len(missing) == 0, f"G-WELL Registry Gate FAILED. {len(missing)} declared tools not callable: {sorted(missing)}"
        assert len(callable_names) == len(DECLARED_TOOLS), f"Tool count mismatch: {len(callable_names)} callable vs {len(DECLARED_TOOLS)} declared"

        print(f"  ✅ All {len(DECLARED_TOOLS)} declared tools callable at runtime")
        print(f"  ✅ Registry size match: {len(callable_names)} = {len(DECLARED_TOOLS)}")
        return callable_names

    callable_set = asyncio.run(_check_registry())

    # Verify all Ω-WELL aliases callable individually
    for alias in ["well_000_init", "well_111_sense", "well_222_fetch", "well_333_mind",
                  "well_444_kernel", "well_555_memory", "well_666_heart", "well_777_forge",
                  "well_888_judge", "well_999_vault", "well_444_reply", "well_444_gateway",
                  "well_000_ops"]:
        assert alias in callable_set, f"Alias {alias} missing from runtime"

    print("  ✅ Ω-WELL aliases: all 13 present")
    print("\n✅ G-WELL Registry Truth Gate PASSED")


# ═══════════════════════════════════════════════════════════════════════════════
# Schema Compliance Gate
# Every structured payload must include required fields.
# ═══════════════════════════════════════════════════════════════════════════════


def test_well_todo_payload_requires_priority():
    """
    Schema compliance gate: todo objects must include priority field.
    Prevents malformed payloads from reaching external tools.
    Uses build_well_todo() from server module.
    """
    # Valid todo
    todo = server_module.build_well_todo("Validate registry", "pending", "high")
    assert todo["content"] == "Validate registry"
    assert todo["status"] == "pending"
    assert todo["priority"] == "high"

    # Missing priority should raise
    try:
        server_module.build_well_todo("no status", status="invalid")
        assert False, "Should have raised ValueError for invalid status"
    except ValueError as e:
        assert "status" in str(e)

    try:
        server_module.build_well_todo("no priority", status="pending", priority="urgent")
        assert False, "Should have raised ValueError for invalid priority"
    except ValueError as e:
        assert "priority" in str(e)

    try:
        server_module.build_well_todo("", status="pending", priority="high")
        assert False, "Should have raised ValueError for empty content"
    except ValueError as e:
        assert "content" in str(e)

    print(f"  ✅ Schema gate catches: invalid status, invalid priority, empty content")


def test_well_output_contains_w0():
    """
    Constitutional compliance gate: every tool output must carry w0 invariant.
    """
    REQUIRED_FIELDS = {"w0"}

    state = _write_canonical_state()
    import asyncio

    async def _check_outputs():
        output_tools = [
            ("well_state", {}),
            ("well_readiness", {}),
            ("well_get_health", {}),
            ("well_get_state", {}),
            ("well_get_readiness", {}),
            ("well_daily_brief", {}),
            ("well_arifos_packet", {}),
            ("well_coupled_readiness", {}),
            ("well_forge_precheck", {"task_description": "test"}),
            ("well_bandwidth_recommendation", {}),
            ("well_assess_governance", {"mode": "full"}),
            ("well_trace_decision", {}),
            ("well_validate_consensus", {"action": "test"}),
            ("well_machine_health_probe", {"targets": ["well"]}),
            ("well_fatigue_accumulator", {"mode": "check"}),
            ("well_circadian_phase", {}),
        ]
        failures = []
        for name, args in output_tools:
            try:
                res = await mcp.call_tool(name, arguments=args)
                data = json.loads(res.content[0].text)
                if not REQUIRED_FIELDS.issubset(data.keys()):
                    missing = REQUIRED_FIELDS - data.keys()
                    failures.append(f"{name}: missing {missing}")
            except Exception as e:
                failures.append(f"{name}: error {e}")
        return failures

    failures = asyncio.run(_check_outputs())
    assert len(failures) == 0, f"Output compliance failures:\n" + "\n".join(failures)
    print(f"  ✅ All 16 tested outputs carry w0 invariant")


if __name__ == "__main__":
    try:
        test_identity_invariants()
        test_well_tools()
        test_well_phase2_tools()
        test_well_integration_fixes()
        test_well_unknown_telemetry()
        test_canonical_tools()
        test_omega_well_tools()
        test_well_registry_declared_surface_matches_callable()
        test_well_todo_payload_requires_priority()
        test_well_output_contains_w0()
        print("\n✅ All AFWELL Audit tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
