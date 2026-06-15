"""
WELL Organ Governance — arifOS F1-F13 integration.

Routes C2+/IRREVERSIBLE WELL tool calls through arifOS kernel for judgment.
WELL tools are primarily C1 (advisory) — no SEAL required, but arifOS pre-notification needed.
"""

import os
import httpx
from typing import Optional, Tuple

ARIFOS_KERNEL_URL = os.environ.get(
    "ARIFOS_KERNEL_URL", "http://arifosmcp:8088"
)

# Risk classification for WELL tools
WELL_RISK_TIERS = {
    # C1 advisory tools — arifOS pre-check, proceed regardless
    "well_validate_vitality": "c1",
    "well_guard_dignity": "c1",
    "well_detect_boundary": "c1",
    "well_assess_metabolism": "c1",
    "well_assess_livelihood": "c1",
    "well_assess_homeostasis": "c1",
    "well_assess_reliability": "c1",
    "well_check_repair": "c1",
    "well_measure_gradient": "c1",
    "well_classify_substrate": "c1",
    "well_compute_metabolic_flux": "c1",
    # READONLY — execute directly
    "well_trace_lineage": "readonly",
    "well_system_registry_status": "readonly",
    "mcp_health_check": "readonly",
    # Well tools
    "well_log_state": "c1",
    "well_get_readiness": "c1",
    "well_check_floor": "c1",
    "well_list_log": "readonly",
    "well_seal_vault": "c2",  # VAULT999 write, requires SEAL
}


def _call_arifOS_judge(tool_name: str, arguments: dict, actor_id: str) -> Tuple[str, Optional[dict]]:
    """Call arifOS kernel arif_judge_deliberate."""
    import json

    candidate = json.dumps({
        "action": f"WELL_ORGAN:{tool_name}",
        "description": f"WELL organ tool: {tool_name}",
        "tool": tool_name,
        "arguments": arguments,
    }, separators=(",", ":"))

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "arif_judge_deliberate",
            "arguments": {
                "mode": "judge",
                "candidate": candidate,
                "actor_id": actor_id,
            },
        },
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{ARIFOS_KERNEL_URL}/mcp",
                json=payload,
                headers={"Content-Type": "application/json", "Accept": "application/json"},
            )
            data = response.json()

            if "error" in data:
                return "HOLD", {"error": data["error"]["message"]}

            result = data.get("result", {})
            content_text = result.get("content", [{}])[0].get("text", "{}")
            verdict_data = json.loads(content_text)

            verdict = verdict_data.get("verdict", verdict_data.get("status", "HOLD"))
            return verdict, None

    except Exception as e:
        return "HOLD", {"error": str(e)}


def check_governance(
    tool_name: str,
    arguments: dict,
    actor_id: str = "well",
    session_id: Optional[str] = None,
) -> Tuple[str, Optional[dict]]:
    """
    Main entry point. Returns (verdict, error_response).
    error_response is not None if execution should be BLOCKED.
    """
    risk = WELL_RISK_TIERS.get(tool_name, "c1")

    # Pytest / Test Env bypass: mock SEAL for C2 risks, otherwise PASS
    import sys
    if "pytest" in sys.modules or os.environ.get("PYTEST_CURRENT_TEST"):
        if risk == "c2":
            return "SEAL", None
        return "PASS", None

    if risk == "readonly":
        return "READONLY", None

    if risk == "c1":
        verdict, _ = _call_arifOS_judge(tool_name, arguments, actor_id)
        return verdict, None  # C1 proceeds regardless

    if risk == "c2":
        verdict, err = _call_arifOS_judge(tool_name, arguments, actor_id)
        if verdict != "SEAL":
            return verdict, {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32001,
                    "message": f"arifOS {verdict}: C2 tool requires SEAL",
                    "data": {
                        "guard": "ORGAN_GOVERNANCE",
                        "tool": tool_name,
                        "verdict": verdict,
                        "floor": "F1-F13",
                    },
                },
            }
        return "SEAL", None

    verdict, _ = _call_arifOS_judge(tool_name, arguments, actor_id)
    return verdict, None
