#!/usr/bin/env python3
"""
session_bridge.py — WELL ↔ arifOS Session Binding Bridge.

Mints real session IDs from arifOS kernel for WELL tool receipts.
Replaces the "UNBOUND" default with genuine session binding when
the arifOS kernel is reachable.

Design (forged 2026-07-21):
  - Calls arifOS :8088 arif_init to mint sessions
  - Falls back to "UNBOUND" when kernel is unreachable
  - Cached sessions with TTL (don't re-init every tool call)
  - Zero-dependency — uses urllib, no FastMCP imports

Epistemic: OBS (kernel response). Confidence: 0.90 (HTTP round-trip).
"""

from __future__ import annotations

import json
import threading
import time
import urllib.request
from typing import Any

# ── Configuration ────────────────────────────────────────────────────────────
ARIFOS_URL = "http://127.0.0.1:8088"
SESSION_TTL_SECONDS = 300  # 5 minutes
# KRT-2026-08-15 F5: 3.0s → 10.0s. 2-3s budgets timed out against a busy
# single-worker kernel and reported "arifOS bridge unreachable" while the
# kernel was healthy — a false-negative bridge verdict.
REQUEST_TIMEOUT_S = 10.0

# ── Thread-safe session cache ────────────────────────────────────────────────
_cache_lock = threading.Lock()
_cached_session: dict[str, Any] | None = None
_cache_expiry: float = 0.0


def get_session(
    actor_id: str = "WELL", intent: str = "substrate observation"
) -> dict[str, Any]:
    """Get or mint an arifOS session. Returns dict with session_id or 'UNBOUND'.

    Thread-safe. Cached with TTL. Falls back to UNBOUND on any error.
    """
    global _cached_session, _cache_expiry

    # Return cached session if still valid
    with _cache_lock:
        if _cached_session and time.time() < _cache_expiry:
            return _cached_session

    # Try to mint a new session from arifOS
    try:
        payload = json.dumps(
            {
                "mode": "init",
                "actor_id": actor_id,
                "intent": intent,
                "declared_model_key": "well-substrate-observer",
                "requested_authority": "OBSERVE_ONLY",
            }
        ).encode()

        req = urllib.request.Request(
            f"{ARIFOS_URL}/mcp",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_S) as resp:
            # MCP JSON-RPC response
            body = json.loads(resp.read().decode())
            result = body.get("result", {})

            session_id = None
            # Try multiple response formats
            if isinstance(result, dict):
                session_id = result.get("session_id") or result.get("sessionId")

            if session_id:
                session = {
                    "status": "BOUND",
                    "session_id": session_id,
                    "actor_id": actor_id,
                    "kernel_verdict": result.get("verdict", "UNKNOWN"),
                    "minted_at": time.time(),
                }
                with _cache_lock:
                    _cached_session = session
                    _cache_expiry = time.time() + SESSION_TTL_SECONDS
                return session

    except Exception:
        pass

    # Fallback
    return {
        "status": "UNBOUND",
        "session_id": None,
        "actor_id": actor_id,
        "reason": "arifOS unreachable or session init failed",
    }


def invalidate_cache() -> None:
    """Force next get_session() to re-mint from arifOS."""
    global _cached_session, _cache_expiry
    with _cache_lock:
        _cached_session = None
        _cache_expiry = 0.0


def health_check() -> dict[str, Any]:
    """Check if arifOS session bridge is operational."""
    try:
        req = urllib.request.Request(
            f"{ARIFOS_URL}/health",
            headers={"Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT_S) as resp:
            body = json.loads(resp.read().decode())
            return {
                "arifos_reachable": True,
                "verdict": body.get("thermodynamic", {}).get("verdict", "UNKNOWN"),
                "floors": body.get("floors_active", 0),
            }
    except Exception as e:
        return {"arifos_reachable": False, "error": str(e)}


# ── CLI ──────────────────────────────────────────────────────────────────────
def main():
    """Test the session bridge."""
    import sys

    print("═══ WELL ↔ arifOS Session Bridge ═══")
    hc = health_check()
    print(f"arifOS:   reachable={hc['arifos_reachable']}")
    if hc["arifos_reachable"]:
        print(f"  verdict: {hc['verdict']}")
        print(f"  floors:  {hc['floors']}")

    session = get_session()
    print(f"\nSession:  status={session['status']}")
    if session["session_id"]:
        print(f"  id:     {session['session_id'][:20]}...")
    else:
        print(f"  reason: {session.get('reason', 'unknown')}")

    if "--json" in sys.argv:
        print(json.dumps(session, indent=2))


if __name__ == "__main__":
    main()
