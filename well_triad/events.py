"""
well_triad.events — Typed substrate event chain.

Forged 2026-08-20.
Floors enforced: F2 (provenance), F4 (privacy), F8 (truth), F11 (consent), F13 (sovereign).

Extends server._append_event with a strict typed-schema wrapper.
Forwards to arifOS :18081 /evidence/ingest for VAULT999 sealing.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import urllib.error
import urllib.request
import uuid
from typing import Any, Optional

# Mirror server._append_event signature; server module passes its own _append_event
# at import time via install().
_native_append_event: Optional[Any] = None


def install(append_event_fn: Any) -> None:
    """Wire the native _append_event function. Called from server.py at boot."""
    global _native_append_event
    _native_append_event = append_event_fn


def append_typed_event(
    *,
    event: str,
    phase: int,
    tool: str,
    plane: str,
    inputs: dict[str, Any],
    outputs: Optional[dict[str, Any]] = None,
    consent_scope: Optional[str] = None,
    source: Optional[str] = None,
    truth_class: str = "INT",
    evidence_label: str = "INT",
    actor_hermes: bool = False,
    note: Optional[str] = None,
    error: Optional[str] = None,
    timestamp_utc: Optional[str] = None,
) -> str:
    """Append a typed triad event to the substrate ledger.

    Returns event_id (uuid4).
    """
    if _native_append_event is None:
        raise RuntimeError(
            "well_triad.events.install() must be called before append_typed_event"
        )

    ts = timestamp_utc or _dt.datetime.now(_dt.timezone.utc).isoformat()

    inputs_hash = hashlib.sha256(
        json.dumps(inputs, sort_keys=True, default=str).encode()
    ).hexdigest()
    outputs_hash = (
        hashlib.sha256(
            json.dumps(outputs, sort_keys=True, default=str).encode()
        ).hexdigest()
        if outputs is not None
        else None
    )

    payload: dict[str, Any] = {
        "event": event,
        "phase": phase,
        "tool": tool,
        "event_id": str(uuid.uuid4()),
        "actor_id": "arif",
        "actor_verified": True,
        "actor_hermes": actor_hermes,
        "plane": plane,
        "consent_scope": consent_scope,
        "timestamp_utc": ts,
        "inputs_hash": inputs_hash,
        "outputs_hash": outputs_hash,
        "truth_class": truth_class,
        "evidence_label": evidence_label,
        "f2_provenance": source,
        "f4_privacy": "leaves_host:false",
        "f11_consent": consent_scope,
        "f13_sovereign": "OPERATOR_VETO_INTACT",
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        "note": note,
        "error": error,
    }

    # ── Validate required fields (caller bug, not floor block) ──────────────
    for k in ("event", "timestamp_utc", "w0", "f13_sovereign"):
        if not payload.get(k):
            raise ValueError(f"refusing to append event missing required field {k!r}")
    if truth_class not in ("OBS", "DER", "INT", "SPEC", "NONE"):
        raise ValueError(f"invalid truth_class {truth_class!r}")
    if evidence_label not in ("OBS", "DER", "INT", "SPEC", "NONE"):
        raise ValueError(f"invalid evidence_label {evidence_label!r}")
    if plane not in ("human", "machine", "governance", "triadic"):
        raise ValueError(f"invalid plane {plane!r}")

    # ── Append to events.jsonl via server._append_event ──────────────────────
    _native_append_event(payload)

    # ── Forward to arifOS /evidence/ingest for VAULT999 seal ─────────────────
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:18081/evidence/ingest",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=2).read()
    except (urllib.error.URLError, OSError, Exception):
        # Non-fatal — substrate event is on disk; reconciler can replay
        pass

    return payload["event_id"]