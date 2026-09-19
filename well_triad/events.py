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
    actor_id: Optional[str] = None,
    actor_verified: bool = False,
    note: Optional[str] = None,
    error: Optional[str] = None,
    timestamp_utc: Optional[str] = None,
    claim_class: Optional[str] = None,
) -> str:
    """Append a typed triad event to the substrate ledger.

    Returns event_id (uuid4).
    """
    if _native_append_event is None:
        raise RuntimeError(
            "well_triad.events.install() must be called before append_typed_event"
        )

    ts = timestamp_utc or _dt.datetime.now(_dt.timezone.utc).isoformat()

    # ── Caller identity (2026-09-19, ADDITIVE — DEFECT FIXED HERE) ──────────
    # DEFECT: this payload used to carry the literal "arif" plus
    # actor_verified=True unconditionally, for EVERY event, whoever called. A
    # constant is not an observed identity: WELL could not witness which agent
    # executed anything, and ASD had to be emitted as NOT_APPLICABLE. A hard-coded
    # actor is a fake identity assertion, not telemetry.
    # FIX: the actor is now CALLER-DERIVED. When the caller supplies an identity
    # it is recorded; when none is supplied the field is empty (None) — that
    # absence is the honest reading, never an invented label.
    # `actor_verified` is False unless a caller identity exists AND the caller
    # explicitly asserts it was verified. It is never inferred from a name.
    #
    # BOUNDARY (F4): this field is an EXECUTOR label — MAP, not STORY. It must
    # never carry a human subject, intake content, biometric value or recovery
    # datum. If a value about a person would land here, pass None instead.
    actor_id = (
        actor_id.strip()
        if isinstance(actor_id, str) and actor_id.strip()
        else None
    )
    actor_verified = bool(actor_verified and actor_id is not None)

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
        "actor_id": actor_id,
        "actor_verified": actor_verified,
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
        # Claim-class gate (2026-09-19, ADDITIVE). The epistemic class of the
        # CLAIM this event records — never a class for a person. `None` means
        # undeclared, which the gate treats as fail-closed (UNCLASSIFIED).
        "claim_class": claim_class,
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