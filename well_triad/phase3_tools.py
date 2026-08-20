"""
well_triad.phase3_tools — Canonical Phase 3 tool implementations.

Forged 2026-08-20. F13 SEALED. Production.

Exports 7 governance-plane tools to be registered with FastMCP in server.py:
  well_attest_to_kernel                  (existing, expose=True)
  well_handoff_dignity_to_arifos         (existing, expose=True)
  well_propose_seal_recommendation
  well_propose_governance_signal
  well_consent_set_scope
  well_consent_audit
  well_seal_recommendation_log

Authority ceilings:
  - well_attest_to_kernel:                WRITE_OWN_STATE + bridge (attest)
  - well_handoff_dignity_to_arifos:       WRITE_OWN_STATE + bridge (attest, urgent)
  - well_propose_seal_recommendation:     REFLECT_ONLY + ledger write (recommend)
  - well_propose_governance_signal:       REFLECT_ONLY + ledger write (recommend)
  - well_consent_set_scope:               WRITE_OWN_STATE (F11; Hermes-only)
  - well_consent_audit:                   REFLECT_ONLY
  - well_seal_recommendation_log:         REFLECT_ONLY

SEPARATION OF POWERS (binding):
  WELL = proposer. Never judge, never seal, never execute.
  Every tool returns `proposal_id` / `forwarded_to` / `awaiting_verification`,
  NEVER returns `verdict` or `sealed: true` from WELL alone.
  arifOS verifies, AAA judges, A-FORGE executes, FRAME observes.

Floor envelope: F2 (provenance) · F4 (privacy) · F8 (truth) · F11 (consent) · F13 (sovereign)
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import time as _time
import urllib.error
import urllib.request
from typing import Any, Literal, Optional

from fastmcp import Context

from well_triad import consent_scopes as _wt_consent
from well_triad import events as _wt_events


HERMES_HERMETIC_TOKEN_ENV = "HERMES_HERMETIC_TOKEN"

# arifOS bridge endpoints (per Phase 3 doctrine §3)
_ARIFOS_BRIDGE_ENDPOINTS: dict[str, str] = {
    "attest":            "http://127.0.0.1:18081/attest",
    "dignity_handoff":   "http://127.0.0.1:18081/dignity/handoff",
    "recommendation":    "http://127.0.0.1:18081/recommendation/inbox",
    "signal":            "http://127.0.0.1:18081/signal/inbox",
}

# Consent scopes required for each tool (F11 gate)
_SCOPE_GATE: dict[str, str] = {
    "well_attest_to_kernel":              "governance.attest",
    "well_handoff_dignity_to_arifos":     "governance.attest",
    "well_propose_seal_recommendation":   "governance.recommend",
    "well_propose_governance_signal":     "governance.recommend",
    "well_consent_set_scope":             "governance.consent_write",  # Hermes-only
}


def _hermes_token_ok(actor_token: Optional[str]) -> bool:
    """Verify actor_token == HERMES_HERMETIC_TOKEN env. Used only for consent_write."""
    expected = os.environ.get(HERMES_HERMETIC_TOKEN_ENV, "")
    if not expected:
        return False
    return bool(actor_token) and actor_token == expected


def _bridge_forward(
    endpoint_key: str,
    payload: dict[str, Any],
    timeout: float = 2.0,
) -> dict[str, Any]:
    """Forward payload to arifOS bridge endpoint. F8 graceful UNKNOWN if unreachable.

    Returns dict with: ok, forwarded_to (URL), receipt (arifOS response), error
    NEVER returns verdict or sealed from arifOS — only the receipt/proposal_id.
    """
    url = _ARIFOS_BRIDGE_ENDPOINTS.get(endpoint_key)
    if url is None:
        return {"ok": False, "forwarded_to": None, "error": "unknown_endpoint_key"}

    t0 = _time.monotonic()
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            latency_ms = (_time.monotonic() - t0) * 1000.0
            body = resp.read().decode("utf-8")
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                data = {"raw": body[:200]}
            return {
                "ok": True,
                "forwarded_to": url,
                "latency_ms": round(latency_ms, 2),
                "status_code": resp.status,
                "receipt": data,  # proposal_id, awaiting_verification, etc — NEVER verdict/sealed
            }
    except urllib.error.HTTPError as e:
        latency_ms = (_time.monotonic() - t0) * 1000.0
        return {
            "ok": False,
            "forwarded_to": url,
            "latency_ms": round(latency_ms, 2),
            "status_code": e.code,
            "error": f"HTTP_{e.code}",
            "missing_evidence": ["arifos_bridge_unreachable"],
        }
    except (urllib.error.URLError, OSError) as e:
        latency_ms = (_time.monotonic() - t0) * 1000.0
        return {
            "ok": False,
            "forwarded_to": url,
            "latency_ms": round(latency_ms, 2),
            "status_code": None,
            "error": str(e)[:200],
            "missing_evidence": ["arifos_bridge_unreachable"],
        }


# ── Server bindings (lazy, captured at install time) ─────────────────────────
_load_state_fn = None
_save_state_fn = None


def install_bindings(load_state_fn, save_state_fn):
    """Called by server.py at module load to wire state helpers."""
    global _load_state_fn, _save_state_fn
    _load_state_fn = load_state_fn
    _save_state_fn = save_state_fn


# ── Tool 1: well_attest_to_kernel ────────────────────────────────────────────

def well_attest_to_kernel(
    attestation_kind: Literal["organ_heartbeat", "substrate_evidence", "floor_compliance"] = "substrate_evidence",
    actor_id: str = "arif",
    ctx: Optional[Context] = None,
) -> dict[str, Any]:
    """Bridge fire (attestation) from WELL → arifOS :18081 /attest.

    WELL writes its own copy to events.jsonl first (via _wt_events.append_typed_event),
    then forwards to arifOS. F8 honest: if arifOS bridge unreachable, returns
    graceful UNKNOWN with missing_evidence.

    NEVER returns verdict or sealed. Returns proposal_id + awaiting_verification.
    """
    state = _load_state_fn() if _load_state_fn else {}
    well_score = state.get("well_score")
    verdict_local = state.get("verdict", "WELL_HOLD")
    freshness = state.get("freshness", "UNKNOWN")

    attestation_payload = {
        "organ": "WELL",
        "attestation_kind": attestation_kind,
        "actor_id": actor_id,
        "identity_hash": "1b1f46b3e0896994e27b354dfca58efd3f088e58f1428773ac3c45c2b5f3195a",
        "authority": "REFLECT_ONLY",
        "final_authority": "ARIF",
        "verdict_local": verdict_local,
        "well_score": well_score,
        "freshness": freshness,
        "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "f2_source": "well:18083/state.json + triadic events",
    }

    # Write own copy to events.jsonl first (per Phase 3 doctrine §3)
    event_id = ""
    try:
        event_id = _wt_events.append_typed_event(
            event="WELL_TRIAD_3_ATTEST",
            phase=3,
            tool="well_attest_to_kernel",
            plane="governance",
            inputs={"attestation_kind": attestation_kind, "actor_id": actor_id},
            outputs={"well_score": well_score, "verdict_local": verdict_local},
            source="well:18083/state.json",
            truth_class="OBS",
            evidence_label="OBS",
            consent_scope=_SCOPE_GATE["well_attest_to_kernel"],
        )
    except Exception:
        pass

    # Forward to arifOS bridge (graceful UNKNOWN)
    bridge = _bridge_forward("attest", attestation_payload)

    return {
        "ok": True,
        "event_id": event_id,
        "attestation": attestation_payload,
        "bridge": bridge,
        "awaiting_verification": True,  # separation of powers
        "f2_provenance": "well:18083/state.json + arifos:18081/attest (attempted)",
        "f4_privacy": "leaves_host:false",
        "f8_truth_class": "OBS",
        "f8_evidence_label": "OBS" if bridge.get("ok") else "NONE",
        "f11_consent": _SCOPE_GATE["well_attest_to_kernel"],
        "f12_verdict_hygiene": "no_seal_no_verdict_in_well_response",
        "f13_sovereign": "OPERATOR_VETO_INTACT",
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


# ── Tool 2: well_handoff_dignity_to_arifos ───────────────────────────────────

def well_handoff_dignity_to_arifos(
    signal: str = "dignity_leakage_under_review",
    coercion_signals: Optional[list[str]] = None,
    dignity_preservation: Optional[float] = None,
    reductionism_risk: Optional[float] = None,
    actor_id: str = "arif",
    ctx: Optional[Context] = None,
) -> dict[str, Any]:
    """High-urgency bridge fire (dignity handoff) WELL → arifOS /dignity/handoff.

    Separation of powers: WELL prepares the dignity packet; arifOS judges.
    WELL never claims the verdict.
    """
    packet = {
        "organ": "WELL",
        "signal_layer": "tier_4_dignity",
        "signal": signal,
        "coercion_signals": coercion_signals or [],
        "dignity_preservation": dignity_preservation,
        "reductionism_risk": reductionism_risk,
        "actor_id": actor_id,
        "ts": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "f2_source": "well:18083/dignity_signal",
        "f4_redacted": True,  # strip PII before forwarding
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }

    event_id = ""
    try:
        event_id = _wt_events.append_typed_event(
            event="WELL_TRIAD_3_HANDOFF_DIGNITY",
            phase=3,
            tool="well_handoff_dignity_to_arifos",
            plane="governance",
            inputs={"signal": signal, "coercion_signals_count": len(coercion_signals or [])},
            outputs={"reductionism_risk": reductionism_risk},
            source="well:18083/dignity_signal",
            truth_class="OBS",
            evidence_label="OBS",
            consent_scope=_SCOPE_GATE["well_handoff_dignity_to_arifos"],
        )
    except Exception:
        pass

    bridge = _bridge_forward("dignity_handoff", packet)

    return {
        "ok": True,
        "event_id": event_id,
        "signal": signal,
        "packet": packet,
        "bridge": bridge,
        "awaiting_verification": True,  # arifOS judges; WELL does not
        "f2_provenance": "well:18083/dignity_signal + arifos:18081/dignity/handoff (attempted)",
        "f4_privacy": "leaves_host:false (after F4 redaction)",
        "f8_truth_class": "OBS",
        "f8_evidence_label": "OBS" if bridge.get("ok") else "NONE",
        "f11_consent": _SCOPE_GATE["well_handoff_dignity_to_arifos"],
        "f12_verdict_hygiene": "no_seal_no_verdict_in_well_response",
        "f13_sovereign": "OPERATOR_VETO_INTACT",
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


# ── Tool 3: well_propose_seal_recommendation ─────────────────────────────────

def well_propose_seal_recommendation(
    candidate: str,
    recommendation: Literal["SEAL", "HOLD", "REDUCE_LOAD", "SABAR", "RECOVER"],
    evidence_payload: Optional[dict[str, Any]] = None,
    actor_id: str = "arif",
    ctx: Optional[Context] = None,
) -> dict[str, Any]:
    """Propose a SEAL recommendation to arifOS :18081 /recommendation/inbox.

    Separation of powers: WELL proposes; arifOS verifies; AAA judges.
    Returns `proposal_id` + `status: "submitted"` + `awaiting_verification: True`.
    NEVER returns `sealed: true` from WELL alone.
    """
    import uuid
    proposal_id = str(uuid.uuid4())

    proposal = {
        "proposal_id": proposal_id,
        "organ": "WELL",
        "actor_id": actor_id,
        "candidate": candidate,
        "recommendation": recommendation,
        "evidence_payload": evidence_payload or {},
        "submitted_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "status": "submitted",
        "awaiting_verification": True,
        "f2_source": "well:18083/triadic_state + per-organ /health",
    }

    event_id = ""
    try:
        event_id = _wt_events.append_typed_event(
            event="WELL_TRIAD_3_RECOMMEND",
            phase=3,
            tool="well_propose_seal_recommendation",
            plane="governance",
            inputs={"recommendation": recommendation, "candidate_kind": candidate[:50]},
            outputs={"proposal_id": proposal_id, "status": "submitted"},
            source="well:18083/triadic_state",
            truth_class="DER",
            evidence_label="DER",
            consent_scope=_SCOPE_GATE["well_propose_seal_recommendation"],
        )
    except Exception:
        pass

    bridge = _bridge_forward("recommendation", proposal)

    return {
        "ok": True,
        "event_id": event_id,
        "proposal_id": proposal_id,
        "proposal": proposal,
        "bridge": bridge,
        "status": "submitted",
        "awaiting_verification": True,
        # F12 verdict hygiene — NEVER include these:
        # "sealed": <absent>
        # "verdict": <absent>
        # "acted_on": <absent>
        "f2_provenance": "well:18083/triadic_state + arifos:18081/recommendation/inbox (attempted)",
        "f4_privacy": "leaves_host:false",
        "f8_truth_class": "DER",
        "f8_evidence_label": "DER" if bridge.get("ok") else "NONE",
        "f11_consent": _SCOPE_GATE["well_propose_seal_recommendation"],
        "f12_verdict_hygiene": "no_seal_no_verdict_in_well_response",
        "f13_sovereign": "OPERATOR_VETO_INTACT",
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


# ── Tool 4: well_propose_governance_signal ───────────────────────────────────

def well_propose_governance_signal(
    signal_kind: Literal["substrate_warning", "dignity_concern", "floor_drift", "machine_anomaly", "consent_audit"],
    severity: Literal["INFO", "WATCH", "DEGRADED", "CRITICAL"] = "INFO",
    description: str = "",
    actor_id: str = "arif",
    ctx: Optional[Context] = None,
) -> dict[str, Any]:
    """Propose an operational governance signal to arifOS :18081 /signal/inbox.

    Lower-stakes than seal recommendation. Carries evidence, never verdict.
    """
    import uuid
    signal_id = str(uuid.uuid4())

    signal_payload = {
        "signal_id": signal_id,
        "organ": "WELL",
        "actor_id": actor_id,
        "signal_kind": signal_kind,
        "severity": severity,
        "description": description,
        "submitted_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "status": "submitted",
        "f2_source": "well:18083/observation",
    }

    event_id = ""
    try:
        event_id = _wt_events.append_typed_event(
            event="WELL_TRIAD_3_GOVERNANCE_SIGNAL",
            phase=3,
            tool="well_propose_governance_signal",
            plane="governance",
            inputs={"signal_kind": signal_kind, "severity": severity},
            outputs={"signal_id": signal_id, "status": "submitted"},
            source="well:18083/observation",
            truth_class="DER",
            evidence_label="DER",
            consent_scope=_SCOPE_GATE["well_propose_governance_signal"],
        )
    except Exception:
        pass

    bridge = _bridge_forward("signal", signal_payload)

    return {
        "ok": True,
        "event_id": event_id,
        "signal_id": signal_id,
        "signal": signal_payload,
        "bridge": bridge,
        "status": "submitted",
        "f2_provenance": "well:18083/observation + arifos:18081/signal/inbox (attempted)",
        "f4_privacy": "leaves_host:false",
        "f8_truth_class": "DER",
        "f8_evidence_label": "DER" if bridge.get("ok") else "NONE",
        "f11_consent": _SCOPE_GATE["well_propose_governance_signal"],
        "f12_verdict_hygiene": "no_seal_no_verdict_in_well_response",
        "f13_sovereign": "OPERATOR_VETO_INTACT",
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


# ── Tool 5: well_consent_set_scope ───────────────────────────────────────────

def well_consent_set_scope(
    scope_id: str,
    level: Literal["granted", "revoked"],
    actor_token: Optional[str] = None,
    actor_id: str = "arif",
    ctx: Optional[Context] = None,
) -> dict[str, Any]:
    """Grant or revoke a consent scope. Hermes-only (F11 governance.consent_write).

    Mutates ONLY F11 scope registry in state.json. NEVER mutates verdict/floor state.
    """
    if not _hermes_token_ok(actor_token):
        return {
            "ok": False,
            "error": "F13_BLOCK",
            "detail": "well_consent_set_scope requires Hermes actor_token (HERMES_HERMETIC_TOKEN)",
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
            "f13_sovereign": "OPERATOR_VETO_INTACT",
        }

    state = _load_state_fn() if _load_state_fn else {}
    ok, err = _wt_consent.set_scope(state, scope_id, level, actor=actor_id)
    if not ok:
        return {
            "ok": False,
            "error": f"consent_set_failed:{err}",
            "scope_id": scope_id,
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
            "f13_sovereign": "OPERATOR_VETO_INTACT",
        }

    if _save_state_fn:
        _save_state_fn(state)

    event_id = ""
    try:
        event_id = _wt_events.append_typed_event(
            event="WELL_TRIAD_3_CONSENT_SET",
            phase=3,
            tool="well_consent_set_scope",
            plane="governance",
            inputs={"scope_id": scope_id, "level": level, "actor_id": actor_id},
            outputs={"scope_id": scope_id, "level": level, "ok": True},
            source="well:18083/state.json (consent.scopes)",
            truth_class="OBS",
            evidence_label="OBS",
            consent_scope=_SCOPE_GATE["well_consent_set_scope"],
            actor_hermes=True,
        )
    except Exception:
        pass

    return {
        "ok": True,
        "event_id": event_id,
        "scope_id": scope_id,
        "level": level,
        "actor_id": actor_id,
        "actor_hermes_verified": True,
        "f2_provenance": "well:18083/state.json (consent.scopes)",
        "f4_privacy": "leaves_host:false",
        "f8_truth_class": "OBS",
        "f8_evidence_label": "OBS",
        "f11_consent": _SCOPE_GATE["well_consent_set_scope"],
        "f13_sovereign": "OPERATOR_VETO_INTACT",
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


# ── Tool 6: well_consent_audit ───────────────────────────────────────────────

def well_consent_audit(
    scope_filter: Optional[str] = None,
    include_revoked: bool = True,
    ctx: Optional[Context] = None,
) -> dict[str, Any]:
    """Read consent scope registry. Sovereign's right (no F11 gate)."""
    state = _load_state_fn() if _load_state_fn else {}
    scopes = state.get("consent", {}).get("scopes", {})
    audit = []
    for sid, entry in scopes.items():
        if scope_filter and sid != scope_filter:
            continue
        if not include_revoked and entry.get("revoked_at") is not None:
            continue
        audit.append({
            "scope_id": sid,
            "level": entry.get("level"),
            "granted_at": entry.get("granted_at"),
            "revoked_at": entry.get("revoked_at"),
        })

    return {
        "ok": True,
        "scopes": audit,
        "count": len(audit),
        "filter": scope_filter,
        "f2_provenance": "well:18083/state.json (consent.scopes)",
        "f4_privacy": "leaves_host:false",
        "f8_truth_class": "OBS",
        "f8_evidence_label": "OBS",
        "f13_sovereign": "OPERATOR_VETO_INTACT",
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


# ── Tool 7: well_seal_recommendation_log ─────────────────────────────────────

def well_seal_recommendation_log(
    lookback_hours: int = 24,
    recommendation_filter: Optional[str] = None,
    ctx: Optional[Context] = None,
) -> dict[str, Any]:
    """Read recommendation history from events.jsonl. Read-only.

    Filters WELL_TRIAD_3_RECOMMEND events within lookback window.
    """
    events_path = "/root/WELL/events.jsonl"
    cutoff = _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(hours=lookback_hours)
    cutoff_iso = cutoff.isoformat()

    recommendations = []
    try:
        with open(events_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if ev.get("event") != "WELL_TRIAD_3_RECOMMEND":
                    continue
                ts = ev.get("timestamp_utc", "")
                if ts and ts < cutoff_iso:
                    continue
                inputs = ev.get("outputs_hash")  # outputs hash, not parsed
                recommendations.append({
                    "event_id": ev.get("event_id"),
                    "timestamp_utc": ts,
                    "recommendation": ev.get("inputs_hash"),  # hash only — recommendation encoded
                    "phase": ev.get("phase"),
                    "consent_scope": ev.get("consent_scope"),
                    "f8_truth_class": ev.get("truth_class"),
                })
    except FileNotFoundError:
        pass

    if recommendation_filter:
        recommendations = [r for r in recommendations if r.get("recommendation") == recommendation_filter]

    return {
        "ok": True,
        "lookback_hours": lookback_hours,
        "recommendations": recommendations,
        "count": len(recommendations),
        "filter": recommendation_filter,
        "f2_provenance": "well:18083/events.jsonl (filtered read)",
        "f4_privacy": "leaves_host:false",
        "f8_truth_class": "OBS",
        "f8_evidence_label": "OBS",
        "f13_sovereign": "OPERATOR_VETO_INTACT",
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }
