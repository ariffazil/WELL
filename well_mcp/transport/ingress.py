"""well_mcp.transport.ingress — Stage 1 of the 5-stage reaction loop.

INGEST: receive signal, generate signal_id, stamp source + freshness.

Authority: REFLECT_ONLY. Never mutates state.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid


def stamp_ingress(
    payload: Any,
    source_organ: str = "well",
    source_tool: str = "",
    actor_id: str = "",
    freshness_raw_hours: Optional[float] = None,
    consent_verified: bool = False,
    coercion_signals: Optional[Any] = None,
    reductionism_risk: float = 0.0,
    dignity_preservation: float = 1.0,
) -> Dict[str, Any]:
    """Stage 1 — INGEST.

    Args:
        payload: the incoming signal (dict, scalar, etc.)
        source_organ: which organ emitted (well, geox, wealth, arifos, etc.)
        source_tool: which tool inside that organ
        actor_id: who initiated (F13, well, aforge, etc.)
        freshness_raw_hours: how stale is the underlying signal
        consent_verified, coercion_signals, reductionism_risk,
        dignity_preservation: dignity-floor inputs, stored into the
            partial stamp so stage 2 (encode) can apply the dignity
            floor without re-asking.

    Returns:
        WellStamp.partial dict with signal_id, source, timestamp,
        freshness_raw, payload, and (if provided) dignity-floor inputs.

    Cost: < 5 ms typical, < 50 ms under load.
    """
    return {
        "signal_id": str(uuid.uuid4()),
        "source": {
            "organ": source_organ,
            "tool": source_tool,
            "actor": actor_id,
            "ts": datetime.now(timezone.utc).isoformat(),
        },
        "freshness_raw": freshness_raw_hours,
        "payload": payload,
        "consent_verified": consent_verified,
        "coercion_signals": list(coercion_signals) if coercion_signals else [],
        "reductionism_risk": reductionism_risk,
        "dignity_preservation": dignity_preservation,
        "stage": "ingress",
        "stage_status": "PASS",
    }
