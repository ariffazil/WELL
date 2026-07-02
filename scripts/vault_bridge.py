# WELL to VAULT999 Bridge — ΔS Cooling Ledger Binding
# Phase 2: Seals WELL metabolic flux + entropy readings to VAULT999 API.
# DITEMPA BUKAN DIBERI.
#
# Trust architecture:
#   1. VAULT999 writer (port 5001) — PRIMARY seal path
#   2. File-based fallback (well_ledger.jsonl) — ADR-001 local-first

import hashlib
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger("well_vault_bridge")

# ── Paths ────────────────────────────────────────────────────────
WELL_STATE_PATH = Path("/root/WELL/state.json")
LEGACY_VAULT_LOG_PATH = Path("/root/arifOS/core/vault999/well_ledger.jsonl")

# ── VAULT999 API (Phase 2: primary seal path) ────────────────────
VAULT999_API_HOST = os.getenv("VAULT999_API_HOST", "127.0.0.1")
VAULT999_API_PORT = int(os.getenv("VAULT999_API_PORT", "8100"))
VAULT999_WRITER_HOST = os.getenv("VAULT999_WRITER_HOST", "127.0.0.1")
VAULT999_WRITER_PORT = int(os.getenv("VAULT999_WRITER_PORT", "5001"))
VAULT999_API_BASE = f"http://{VAULT999_API_HOST}:{VAULT999_API_PORT}"
VAULT999_WRITER_BASE = f"http://{VAULT999_WRITER_HOST}:{VAULT999_WRITER_PORT}"

# ── Thresholds ────────────────────────────────────────────────────
FLUX_CRITICAL_THRESHOLD = 0.65
FLUX_SYSTEM_HOLD_THRESHOLD = 0.85
MIN_SCORE_DELTA_FOR_SEAL = 10  # only seal if score changed by >= 10


def _load_well_state() -> dict[str, Any] | None:
    """Load and minimally validate WELL state from canonical path."""
    if not WELL_STATE_PATH.exists():
        logger.warning(f"WELL state not found at {WELL_STATE_PATH}")
        return None
    try:
        with open(WELL_STATE_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"WELL state read error: {e}")
        return None


def _compute_freshness(state: dict[str, Any]) -> dict[str, Any]:
    """Compute freshness band from state timestamp vs now."""
    ts_str = state.get("timestamp") or state.get("last_successful_read")
    if not ts_str:
        return {"status": "UNKNOWN", "age_hours": 0, "is_stale": True}

    try:
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        age_seconds = (datetime.now(timezone.utc) - ts).total_seconds()
        age_hours = age_seconds / 3600
        if age_hours < 1:
            return {"status": "FRESH", "age_hours": age_hours, "is_stale": False}
        elif age_hours < 24:
            return {"status": "STALE", "age_hours": age_hours, "is_stale": False}
        else:
            return {"status": "EXPIRED", "age_hours": age_hours, "is_stale": True}
    except (ValueError, TypeError):
        return {"status": "UNKNOWN", "age_hours": 0, "is_stale": True}


def _extract_flux(state: dict[str, Any]) -> dict[str, Any]:
    """Extract metabolic flux from state, with fallback defaults."""
    flux = state.get("metabolic_flux", {})
    if isinstance(flux, dict) and flux.get("metabolic_flux") is not None:
        return {
            "flux": flux["metabolic_flux"],
            "verdict": flux.get("verdict", "UNKNOWN"),
            "compulsory_reallocation": flux.get("compulsory_reallocation", False),
        }
    # Fallback: compute from cognitive + machine metrics
    cognitive = state.get("metrics", {}).get("cognitive", {})
    m_machine = state.get("m_machine", {})
    cognitive_entropy = state.get("cognitive_entropy", 0.30)
    machine_entropy = state.get("machine_entropy", 0.10)
    context_pressure = m_machine.get("context_pressure", 0.0)
    # Simplified flux = weighted average
    flux_val = round(
        0.35 * cognitive_entropy
        + 0.25 * machine_entropy
        + 0.20 * context_pressure
        + 0.20 * (1.0 - (m_machine.get("compute_budget_pct", 100) / 100.0)),
        4,
    )
    return {
        "flux": flux_val,
        "verdict": "COMPULSORY_REALLOCATION"
        if flux_val >= FLUX_CRITICAL_THRESHOLD
        else "SYSTEM_HOLD"
        if flux_val >= FLUX_SYSTEM_HOLD_THRESHOLD
        else "NOMINAL",
        "compulsory_reallocation": flux_val >= FLUX_CRITICAL_THRESHOLD,
    }


async def _seal_to_vault_api(payload: dict[str, Any]) -> dict[str, Any]:
    """Seal a WELL entropy event to VAULT999 via writer /transition (port 5001).

    The writer's /transition endpoint accepts KSR_TRANSITION events without
    requiring human signature — suitable for automated entropy reports.

    Returns SUCCESS with seal_hash or ERROR with details.
    Falls back to local file if writer is unreachable (ADR-001).
    """
    transition_payload = {
        "action": "well_entropy_seal",
        "from_state": "OBSERVING",
        "to_state": "SEALED",
        "claim_state": "OBSERVED",
        "agent_id": "well-vault-bridge",
        "payload": payload,
    }

    # Build auth header if token is available
    headers = {}
    _token = os.getenv("VAULT_WRITER_TOKEN") or os.getenv("VAULT999_WRITER_TOKEN")
    if _token:
        headers["X-Writer-Token"] = _token

    # Try VAULT999 writer /transition first
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{VAULT999_WRITER_BASE}/transition",
                json=transition_payload,
                headers=headers,
            )
            if resp.status_code == 200:
                result = resp.json()
                return {
                    "status": "SUCCESS",
                    "method": "vault-api",
                    "seal_id": result.get("id"),
                    "seal_hash": result.get("seal_hash"),
                    "chain_hash": result.get("chain_hash"),
                    "epoch": result.get("epoch"),
                }
            else:
                logger.warning(
                    f"VAULT999 /transition returned {resp.status_code}: {resp.text[:200]}"
                )
    except Exception as e:
        logger.warning(f"VAULT999 /transition unreachable: {e}")

    # Fallback: local file (ADR-001: localhost trust)
    try:
        LEGACY_VAULT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LEGACY_VAULT_LOG_PATH, "a") as f:
            f.write(json.dumps(payload) + "\n")
        return {
            "status": "SUCCESS",
            "method": "local-file",
            "path": str(LEGACY_VAULT_LOG_PATH),
        }
    except OSError as e:
        return {"status": "ERROR", "message": f"Local write failed: {e}"}


async def bridge_to_vault(force: bool = False) -> dict[str, Any]:
    """Bridge WELL state to VAULT999 cooling ledger.

    Seals metabolic flux + entropy readings to VAULT999.
    Only seals on significant events (score delta, flux critical, violations)
    unless force=True.
    """
    state = _load_well_state()
    if not state:
        return {
            "status": "ERROR",
            "message": "WELL state not found — run well_well_compute_metabolic_flux first",
        }

    # Check identity invariant
    identity_ok = state.get("identity") == "WELL" and state.get("authority") in (
        "REFLECT_ONLY",
        "Body",
        "Body / Human Intelligence",
    )
    if not identity_ok and not force:
        return {
            "status": "ERROR",
            "message": "WELL identity invariant failed — seal rejected",
        }

    # Extract data
    current_score = state.get("well_score", 0)
    violations = state.get("floors_violated", [])
    flux_info = _extract_flux(state)
    freshness = _compute_freshness(state)

    # Condition logic: only seal on high-signal events
    is_stale = freshness["is_stale"]
    is_degraded = len(violations) > 0 or current_score < 70
    is_flux_critical = flux_info["verdict"] in (
        "COMPULSORY_REALLOCATION",
        "SYSTEM_HOLD",
    )
    is_low_capacity = current_score < 70

    should_seal = (
        force or is_degraded or is_flux_critical or (is_stale and current_score < 80)
    )

    if not should_seal:
        return {
            "status": "SKIPPED",
            "message": f"Signal-to-noise suppressed. score={current_score}, flux={flux_info['flux']:.4f}, stale={is_stale}",
        }

    # Build entropy seal payload
    payload = {
        "vault_type": "well_entropy_event",
        "epoch": datetime.now(timezone.utc).isoformat(),
        "well_score": current_score,
        "status": "FLUX_CRITICAL"
        if is_flux_critical
        else "DEGRADED"
        if is_degraded
        else "STALE"
        if is_stale
        else "STABLE",
        "violations": violations,
        "metabolic_flux": flux_info["flux"],
        "flux_verdict": flux_info["verdict"],
        "compulsory_reallocation": flux_info["compulsory_reallocation"],
        "freshness_hours": round(freshness["age_hours"], 1),
        "state_age_hours": round(freshness["age_hours"], 1),
        "delta_S": -flux_info["flux"],  # entropy absorbed (cooling)
        "peace2": max(0.0, 1.0 - flux_info["flux"]),  # peace = 1 - flux
        "domain_law": "SUBSTRATE_LAW",
        "w0_assertion": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        "trigger": "FLUX_CRITICAL"
        if is_flux_critical
        else "DEGRADED"
        if is_degraded
        else "STALE"
        if is_stale
        else "FORCE",
    }
    payload["hash"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()

    # Seal to VAULT999
    seal_result = await _seal_to_vault_api(payload)
    seal_result["payload"] = payload
    return seal_result


# ── CLI entry point ───────────────────────────────────────────────
if __name__ == "__main__":
    import asyncio

    force_sync = "--force" in sys.argv
    result = asyncio.run(bridge_to_vault(force=force_sync))
    print(json.dumps(result, indent=2, default=str))
