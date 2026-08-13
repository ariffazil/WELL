from fastmcp import FastMCP
import json
import os
import functools
import hashlib
import time
import inspect
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


# ── governed_tool stub (no core dependency — vault logging added at runtime) ──
def governed_tool(fn):
    """Decorator — wraps any FastMCP tool. Governance is enforced by arifOS at runtime."""

    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        return await fn(*args, **kwargs)

    return wrapper


# Initialize FastMCP
mcp = FastMCP("WELL — Biological Substrate")

# Constants - Updated path to /var/lib for service access with local fallback
WELL_STATE_PATH_RAW = os.environ.get(
    "WELL_STATE_PATH", "/var/lib/arifosmcp/WELL/state.json"
)
WELL_STATE_PATH = Path(WELL_STATE_PATH_RAW)

# 666 RISK FIX: Local fallback if system path is missing
if not WELL_STATE_PATH.exists():
    # Priority 1: data/ (Canonical)
    DATA_STATE = Path(__file__).parent.parent / "data" / "state.json"
    # Priority 2: current dir (Legacy/Local)
    LOCAL_STATE = Path(__file__).parent / "state.json"

    if DATA_STATE.exists():
        WELL_STATE_PATH = DATA_STATE
    elif LOCAL_STATE.exists():
        WELL_STATE_PATH = LOCAL_STATE

try:
    from arifosmcp.runtime.vault_postgres import SupabaseStateStore, log_tool_call

    state_store = SupabaseStateStore()
except Exception:
    state_store = None
    log_tool_call = None


def vault_tool(fn):
    """Decorator: auto-logs every MCP tool call to VAULT999."""

    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        start = time.monotonic()
        input_hash = hashlib.sha256(str(kwargs).encode()).hexdigest()[:16]
        result_code = "OK"
        try:
            if inspect.iscoroutinefunction(fn):
                result = await fn(*args, **kwargs)
            else:
                result = fn(*args, **kwargs)
            return result
        except Exception:
            result_code = "ERROR"
            raise
        finally:
            duration_ms = int((time.monotonic() - start) * 1000)
            if log_tool_call:
                await log_tool_call(
                    tool_name=fn.__name__,
                    agent_id=kwargs.get("agent_id", "arifOS"),
                    session_id=kwargs.get("session_id", "UNANCHORED"),
                    input_hash=input_hash,
                    result_code=result_code,
                    duration_ms=duration_ms,
                )

    return wrapper


def _get_raw_state() -> Dict[str, Any]:
    """Helper to read WELL state with fallback and cloud sync."""
    # 1. Try Cloud Primary if available
    if state_store:
        cloud_state = state_store.read_state("ARIF", "main_telemetry")
        if cloud_state:
            return cloud_state

    # 2. Witness Fallback (Local)
    if not WELL_STATE_PATH.exists():
        return {
            "ok": False,
            "well_score": 50.0,
            "verdict": "UNKNOWN",
            "bandwidth": "NORMAL",
            "floors_violated": [],
            "message": f"WELL substrate offline or state missing at {WELL_STATE_PATH}",
        }
    try:
        with open(WELL_STATE_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {"ok": False, "error": "failed to read state"}


def _save_state(state: Dict[str, Any]) -> bool:
    """Helper to save WELL state (Dual-Write)."""
    try:
        # Update timestamp
        state["timestamp"] = datetime.now(timezone.utc).isoformat() + "Z"

        # 1. Cloud Write (Primary)
        if state_store:
            state_store.write_state("ARIF", "main_telemetry", state)

        # 2. Local Write (Witness)
        with open(WELL_STATE_PATH, "w") as f:
            json.dump(state, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving state: {e}")
        return False


# === PERCEPTION TOOLS (P-Axis) ===


@mcp.tool()
@governed_tool
async def mcp_P_well_state_read() -> Dict[str, Any]:
    """
    Read the current biological telemetry snapshot from the WELL substrate.
    Returns: A dictionary containing scores, metrics, and readiness verdict.
    """
    return _get_raw_state()


@mcp.tool()
@governed_tool
async def mcp_P_well_readiness_check() -> Dict[str, Any]:
    """
    Perform a biological readiness check for constitutional governance.
    Returns: A verdict (OPTIMAL, FUNCTIONAL, DEGRADED, LOW_CAPACITY) and supporting metrics.
    """
    state = _get_raw_state()
    score = state.get("well_score", 50.0)
    violations = state.get("floors_violated", [])

    if violations:
        verdict = "DEGRADED"
        bandwidth = "RESTRICTED"
    elif score >= 80:
        verdict = "OPTIMAL"
        bandwidth = "FULL"
    elif score >= 60:
        verdict = "FUNCTIONAL"
        bandwidth = "NORMAL"
    else:
        verdict = "LOW_CAPACITY"
        bandwidth = "REDUCED"

    return {
        "verdict": verdict,
        "well_score": score,
        "bandwidth": bandwidth,
        "violations": violations,
        "timestamp": state.get("timestamp"),
    }


@mcp.tool()
@governed_tool
async def mcp_P_well_floor_scan() -> Dict[str, Any]:
    """
    Scan the 13 W-Floors (Well-being dimensions) for any constitutional violations.
    Returns: A list of violated floors and current system health.
    """
    state = _get_raw_state()
    return {
        "floors_violated": state.get("floors_violated", []),
        "metrics": state.get("metrics", {}),
        "health_score": state.get("well_score", 0.0),
    }


# === EXECUTION TOOLS (E-Axis) ===


@mcp.tool()
@governed_tool
async def mcp_E_well_log_update(
    well_score: Optional[float] = None,
    metrics: Optional[Dict[str, Any]] = None,
    floors_violated: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Update the WELL state with new telemetry (e.g., after sleep, exercise, or meditation).
    """
    state = _get_raw_state()
    if well_score is not None:
        state["well_score"] = well_score
    if metrics:
        current_metrics = state.get("metrics", {})
        current_metrics.update(metrics)
        state["metrics"] = current_metrics
    if floors_violated is not None:
        state["floors_violated"] = floors_violated

    success = _save_state(state)
    return {"success": success, "updated_state": state if success else None}


@mcp.tool()
@governed_tool
async def mcp_E_well_pressure_signal(load_delta: float, reason: str) -> Dict[str, Any]:
    """
    Signal cognitive pressure/load to WELL. Triggers W6 Metabolic Pause if load is too high.
    """
    state = _get_raw_state()
    metrics = state.get("metrics", {})
    cog = metrics.get("cognitive", {"clarity": 10, "decision_fatigue": 0.0})

    # Increment fatigue
    old_fatigue = cog.get("decision_fatigue", 0.0)
    new_fatigue = min(10.0, old_fatigue + load_delta)
    cog["decision_fatigue"] = new_fatigue
    metrics["cognitive"] = cog
    state["metrics"] = metrics

    # Update score
    state["well_score"] = max(0.0, state.get("well_score", 50.0) - (load_delta * 2))

    # W6 Violation check
    violations = state.get("floors_violated", [])
    if load_delta > 2.0 and "W6_METABOLIC_PAUSE" not in violations:
        violations.append("W6_METABOLIC_PAUSE")
    state["floors_violated"] = violations

    success = _save_state(state)
    return {
        "success": success,
        "verdict": "HOLD" if load_delta > 2.0 else "PROCEED",
        "reason": reason,
    }


@mcp.tool()
@governed_tool
async def mcp_E_well_anchor_to_vault(
    summary: str = "WELL Substrate Anchor",
) -> Dict[str, Any]:
    """
    Seal the current WELL state to the arifOS VAULT999 (requires arifosmcp package).
    """
    state = _get_raw_state()
    try:
        from arifosmcp.runtime.vault_postgres import seal_to_vault

        res = await seal_to_vault(
            event_type="WELL_ANCHOR",
            session_id="WELL-AUTO",
            actor_id="well-system",
            stage="999_VAULT",
            verdict="SEAL" if state.get("well_score", 0) > 60 else "HOLD",
            payload=state,
            risk_tier="low",
        )
        return {"success": True, "vault_id": getattr(res, "ledger_id", "N/A")}
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Vault anchoring requires arifosmcp runtime.",
        }


# ── WELL Face Mirror — Sovereign Substrate Vitality Observation ──────────────
# substrate_class=SOVEREIGN, authority_ceiling=REFLECT_ONLY+CONSENT_GATE
# A mirror, not a camera. NEVER extracts identity. Ephemeral. F6 MARUAH.
# Forged 2026-08-13 — Vision Intelligence Eureka (ratified by F13)
try:
    import sys as _sys

    _sys.path.insert(0, str(Path(__file__).parent.parent / "engines"))
    from face_mirror import observe_face as _face_mirror_observe

    @mcp.tool()
    @governed_tool
    async def well_observe_face(
        image_base64: str = "",
        consent_token: str = "",
        mode: str = "baseline",
        session_id: str = "default",
    ) -> Dict[str, Any]:
        """
        WELL Face Mirror — A mirror, not a camera.

        Observes dynamic vitality signals (eye openness, brow tension, jaw tension)
        from facial landmarks using MediaPipe Face Mesh. NEVER extracts identity.
        Image is purged from memory immediately after landmark extraction.

        substrate_class: SOVEREIGN
        authority_ceiling: REFLECT_ONLY + CONSENT_GATE

        Modes:
          baseline — establish session baseline vitality
          compare  — measure shift from baseline

        Constitutional constraints:
          - consent_token REQUIRED (fatal halt if missing)
          - NO biometric template storage (ephemeral)
          - NO identity vector/embedding
          - F6 MARUAH output (dignified language, not raw metrics)
          - REFLECT_ONLY (state observation, never diagnosis)

        DITEMPA BUKAN DIBERI — Forged, Not Given.
        """
        return await _face_mirror_observe(
            image_base64=image_base64 if image_base64 else None,
            consent_token=consent_token if consent_token else None,
            mode=mode,
            session_id=session_id,
        )
except ImportError:
    # mediapipe not available — tool silently absent
    pass

if __name__ == "__main__":
    mcp.run()
