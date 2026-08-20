"""
well_triad.consent_scopes — F11 consent scope registry.

Forged 2026-08-20.
Floors enforced: F11 (consent).

Scopes registered at boot:
  intake.basic           — DEFAULT ON, auto-grant on first intake call
  intake.location        — DEFAULT OFF (free-form location is sensitive)
  recovery.basic         — DEFAULT ON, auto-grant on first recovery call
  substance.full         — DEFAULT OFF (caffeine/alcohol/supplements explicit)
  biometric.full         — DEFAULT OFF (Hermes-only)
  governance.recommend   — DEFAULT OFF (Phase 3)
  governance.attest      — DEFAULT OFF (Phase 3)
  governance.consent_write — DEFAULT OFF (Phase 3, Hermes-only)

Returns (active: bool, revoked_at: ISO-8601 | None).
"""

from __future__ import annotations

from typing import Optional, Tuple

# Default scope registry. Idempotent — registered on first import if absent.
DEFAULT_SCOPES: dict[str, dict[str, Optional[str]]] = {
    "intake.basic":           {"level": "granted",     "granted_at": "2026-08-20T00:00:00Z", "revoked_at": None},
    "intake.location":        {"level": "not_granted", "granted_at": None,                    "revoked_at": None},
    "recovery.basic":         {"level": "granted",     "granted_at": "2026-08-20T00:00:00Z", "revoked_at": None},
    "substance.full":         {"level": "not_granted", "granted_at": None,                    "revoked_at": None},
    "biometric.full":         {"level": "not_granted", "granted_at": None,                    "revoked_at": None},
    "governance.recommend":   {"level": "not_granted", "granted_at": None,                    "revoked_at": None},
    "governance.attest":      {"level": "not_granted", "granted_at": None,                    "revoked_at": None},
    "governance.consent_write": {"level": "not_granted", "granted_at": None,                  "revoked_at": None},
}


def _state_get_scopes(state: dict) -> dict:
    """Get consent.scopes from state, registering defaults if absent."""
    consent = state.setdefault("consent", {})
    scopes = consent.setdefault("scopes", {})
    for scope_id, defaults in DEFAULT_SCOPES.items():
        if scope_id not in scopes:
            scopes[scope_id] = dict(defaults)
    return scopes


def consent_active(state: dict, scope: str) -> Tuple[bool, Optional[str]]:
    """Check if scope is active. Returns (active, revoked_at_iso).

    Auto-registers scope registry in state.consent.scopes (idempotent).
    Caller is responsible for _save_state() if scope was newly registered.
    Returns (True, None) if active, (False, revoked_at|None) if not.
    """
    scopes = _state_get_scopes(state)
    entry = scopes.get(scope)
    if entry is None:
        # Unknown scope — treat as not granted
        return (False, None)
    level = entry.get("level", "not_granted")
    revoked_at = entry.get("revoked_at")
    if level == "granted" and revoked_at is None:
        return (True, None)
    return (False, revoked_at)


def set_scope(
    state: dict,
    scope: str,
    level: str,
    actor: str = "arif",
) -> Tuple[bool, Optional[str]]:
    """Grant or revoke a scope. Phase 3 will gate this behind Hermes."""
    if level not in ("granted", "revoked", "not_granted"):
        return (False, "invalid_level")
    scopes = _state_get_scopes(state)
    if scope not in scopes:
        return (False, "unknown_scope")
    import datetime as _dt
    now = _dt.datetime.now(_dt.timezone.utc).isoformat()
    scopes[scope]["level"] = level
    if level == "granted":
        scopes[scope]["granted_at"] = now
        scopes[scope]["revoked_at"] = None
    elif level == "revoked":
        scopes[scope]["revoked_at"] = now
    return (True, None)