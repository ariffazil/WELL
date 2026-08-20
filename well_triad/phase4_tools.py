"""
well_triad.phase4_tools — Canonical Phase 4 tool implementation.

Forged 2026-08-20. F13 SEALED. Production.

Exports 1 triadic-composition tool to be registered with FastMCP in server.py:
  well_assess_triadic_state

Authority ceiling: REFLECT_ONLY (compose only, no write).
F12 verdict hygiene: NEVER returns sealed/verdict/acted_on.
F8 truth class: DER (composition is derivation, not direct observation).

Composition:
  human      ← well_assess_homeostasis (canonical, server.py)
  machine    ← well_observe_federation_thermal (Phase 2)
  governance ← well_consent_audit + events.jsonl scan (Phase 3)

Route decision (F12 recommendation, never verdict):
  SABAR   — any organ CRITICAL
  HOLD    — governance breach OR unified < 0.50
  RECOVER — weakest plane = human, score < 0.70
  REDUCE_LOAD — weakest plane = machine, score < 0.85
  PROCEED — unified ≥ 0.85, no breaches
"""

from __future__ import annotations

import datetime as _dt
import json
import os
from typing import Any, Optional

from fastmcp import Context

from well_triad import events as _wt_events


# ── Composition helpers ─────────────────────────────────────────────────────

def _fetch_human_plane(actor_id: str) -> dict[str, Any]:
    """Read human substrate from state.json directly. Hermetic — no server import.

    Returns {score, state, weakest} where score is 0-1 (well_score/100),
    state is OPTIMAL/WATCH/DEGRADED/CRITICAL.
    """
    state_path = os.environ.get("WELL_STATE_PATH", "/root/WELL/state.json")
    try:
        with open(state_path) as f:
            state = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"score": 0.5, "state": "UNKNOWN", "weakest": "unknown", "missing_evidence": ["no_state"]}

    well_score = state.get("well_score", 50)
    if not isinstance(well_score, (int, float)):
        well_score = 50
    score = max(0.0, min(1.0, well_score / 100.0))

    if score >= 0.85:
        state_label = "OPTIMAL"
    elif score >= 0.70:
        state_label = "WATCH"
    elif score >= 0.50:
        state_label = "DEGRADED"
    else:
        state_label = "CRITICAL"

    metrics = state.get("metrics", {})
    weakest = "none"
    weakest_score = 1.0
    for k in ("sleep", "cognitive", "metabolic", "structural"):
        v = metrics.get(k)
        if isinstance(v, dict) and "score" in v:
            if v["score"] < weakest_score:
                weakest_score = v["score"]
                weakest = k

    return {
        "score": round(score, 3),
        "state": state_label,
        "weakest": weakest,
        "well_score": well_score,
    }


def _fetch_machine_plane(lookback_hours: int) -> dict[str, Any]:
    """Aggregate machine plane by reading per-organ /health directly. Hermetic stdlib.

    Returns {score, state, weakest, organs}.
    """
    import urllib.error
    import urllib.request
    import time as _time

    FEDERATION = (
        ("arifos", 18081),
        ("geox",   18082),
        ("well",   18083),
        ("aaa",    18084),
        ("frame",  18085),
        ("wealth", 18086),
    )

    organs: dict[str, dict[str, Any]] = {}
    weakest = "unknown"
    weakest_score = 1.0
    scores = []

    for name, port in FEDERATION:
        t0 = _time.monotonic()
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{port}/health", method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                latency = (_time.monotonic() - t0) * 1000.0
                body = resp.read().decode("utf-8")
                data = json.loads(body)
                status = str(data.get("status") or data.get("health") or data.get("state") or "UNKNOWN").upper()
                if status in ("HEALTHY", "OK", "OPTIMAL", "READY", "STABLE", "GREEN"):
                    score = 0.95
                elif status in ("WATCH", "WARN", "AMBER", "DEGRADED"):
                    score = 0.70
                elif status in ("CRITICAL", "DOWN", "UNHEALTHY", "ERROR", "RED", "OFFLINE"):
                    score = 0.30
                else:
                    score = 0.55
                if latency > 500:
                    score -= 0.10
                score = max(0.05, min(1.0, score))
                classification = (
                    "OPTIMAL" if score >= 0.85 else
                    "WATCH" if score >= 0.70 else
                    "DEGRADED" if score >= 0.50 else
                    "CRITICAL"
                )
                organs[name] = {
                    "status": status,
                    "score": round(score, 3),
                    "classification": classification,
                    "latency_ms": round(latency, 2),
                }
        except Exception as e:
            organs[name] = {
                "status": "DOWN",
                "score": 0.05,
                "classification": "CRITICAL",
                "error": str(e)[:200],
            }
            score = 0.05

        scores.append(score)
        if score < weakest_score:
            weakest_score = score
            weakest = name

    avg_score = sum(scores) / len(scores) if scores else 0.5
    avg_classification = (
        "OPTIMAL" if avg_score >= 0.85 else
        "WATCH" if avg_score >= 0.70 else
        "DEGRADED" if avg_score >= 0.50 else
        "CRITICAL"
    )

    critical_count = sum(1 for v in organs.values() if v.get("classification") == "CRITICAL")
    if critical_count >= 1:
        route = "SABAR"
    elif avg_score < 0.5:
        route = "HOLD"
    elif avg_score < 0.7:
        route = "REDUCE_LOAD"
    elif avg_score < 0.85:
        route = "RECOVER"
    else:
        route = "PROCEED"

    return {
        "score": round(avg_score, 3),
        "state": avg_classification,
        "weakest": weakest,
        "organs": organs,
        "route": route,
        "critical_count": critical_count,
    }


def _fetch_governance_plane(lookback_hours: int) -> dict[str, Any]:
    """Read governance plane: consent registry + recent recommendations.

    Returns {score, consent_intact, active_recommendations, open_attestations}.
    """
    state_path = os.environ.get("WELL_STATE_PATH", "/root/WELL/state.json")
    try:
        with open(state_path) as f:
            state = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        state = {}

    scopes = state.get("consent", {}).get("scopes", {})
    active_scopes = [sid for sid, e in scopes.items() if e.get("level") == "granted" and e.get("revoked_at") is None]
    consent_intact = len(active_scopes) > 0

    # Count recent events
    cutoff = _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(hours=lookback_hours)
    cutoff_iso = cutoff.isoformat()
    counts = {"RECOMMEND": 0, "ATTEST": 0, "GOVERNANCE_SIGNAL": 0}
    events_path = "/root/WELL/events.jsonl"
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
                ts = ev.get("timestamp_utc", "")
                if ts and ts < cutoff_iso:
                    continue
                event_name = ev.get("event", "")
                if "RECOMMEND" in event_name:
                    counts["RECOMMEND"] += 1
                elif "ATTEST" in event_name:
                    counts["ATTEST"] += 1
                elif "GOVERNANCE_SIGNAL" in event_name:
                    counts["GOVERNANCE_SIGNAL"] += 1
    except FileNotFoundError:
        pass

    # Score governance by consent + recommendation activity
    # consent_intact=1.0 if any scope active, 0.0 if none
    # subtract 0.1 per active recommendation (pressure signal)
    base = 1.0 if consent_intact else 0.0
    pressure_penalty = min(0.4, counts["RECOMMEND"] * 0.1)
    score = max(0.0, base - pressure_penalty)

    return {
        "score": round(score, 3),
        "consent_intact": consent_intact,
        "active_scopes": active_scopes,
        "active_recommendations": counts["RECOMMEND"],
        "open_attestations": counts["ATTEST"],
        "governance_signals": counts["GOVERNANCE_SIGNAL"],
    }


def _route_decision(unified_score: float, weakest_plane: str, machine_critical_count: int) -> str:
    """F12 verdict-hygiene route matrix. Recommendation, never verdict.

    Per `07-PHASE-4-TRIADIC-COMPOSITION.md` §3:
    - SABAR  : any machine CRITICAL
    - HOLD   : governance breach OR unified < 0.50
    - RECOVER: weakest plane = human, score < 0.70
    - REDUCE_LOAD: weakest plane = machine, score < 0.85 (or unified 0.50-0.70)
    - PROCEED: unified >= 0.85
    """
    if machine_critical_count >= 1:
        return "SABAR"
    if weakest_plane == "governance":
        return "HOLD"
    if unified_score < 0.50:
        return "HOLD"
    if weakest_plane == "human" and unified_score < 0.70:
        return "RECOVER"
    if weakest_plane == "machine" and unified_score < 0.85:
        return "REDUCE_LOAD"
    if unified_score < 0.70:
        return "REDUCE_LOAD"
    if unified_score < 0.85:
        return "RECOVER"
    return "PROCEED"


# ── Tool: well_assess_triadic_state ──────────────────────────────────────────

def well_assess_triadic_state(
    actor_id: str = "arif",
    lookback_hours: int = 1,
    ctx: Optional[Context] = None,
) -> dict[str, Any]:
    """[Triad Phase 4] Headline composition: human × machine × governance → unified signal.

    Returns unified_score, weakest_plane, route (F12 recommendation only).
    NEVER returns sealed=True or verdict=<value> from WELL alone.

    The route is a recommendation, not a verdict. Caller must still pass
    arifOS.verify → AAA.judge before any action.
    """
    # 1. Human plane
    human = _fetch_human_plane(actor_id)
    human_score = human["score"]

    # 2. Machine plane (aggregate across 6 organs)
    machine = _fetch_machine_plane(lookback_hours)
    machine_score = machine["score"]
    machine_critical = machine.get("critical_count", 0)

    # 3. Governance plane (consent + recent recommendations)
    governance = _fetch_governance_plane(lookback_hours)
    gov_score = governance["score"]

    # 4. Unified roll-up — weakest-link principle
    weakest_score = min(human_score, machine_score, gov_score)
    if human_score <= machine_score and human_score <= gov_score:
        weakest_plane = "human"
    elif machine_score <= gov_score:
        weakest_plane = "machine"
    else:
        weakest_plane = "governance"

    # 5. Route decision (F12 recommendation only)
    route = _route_decision(weakest_score, weakest_plane, machine_critical)

    # 6. Append read receipt
    event_id = ""
    try:
        event_id = _wt_events.append_typed_event(
            event="WELL_TRIAD_4_ASSESS",
            phase=4,
            tool="well_assess_triadic_state",
            plane="triadic",
            inputs={"actor_id": actor_id, "lookback_hours": lookback_hours},
            outputs={
                "unified_score": round(weakest_score, 3),
                "weakest_plane": weakest_plane,
                "route": route,
                "machine_critical_count": machine_critical,
            },
            source="compose(human=state.json, machine=/health×6, governance=consent+events.jsonl)",
            truth_class="DER",
            evidence_label="DER",
        )
    except Exception:
        pass

    return {
        "ok": True,
        "actor_id": actor_id,
        "lookback_hours": lookback_hours,
        "human": human,
        "machine": {
            "score": machine["score"],
            "state": machine["state"],
            "weakest_organ": machine["weakest"],
            "route": machine["route"],
            "critical_count": machine_critical,
            "organs": machine["organs"],
        },
        "governance": governance,
        "triadic": {
            "unified_score": round(weakest_score, 3),
            "weakest_plane": weakest_plane,
            "route": route,
            "f_recommendation": (
                f"{route}: triadic score {weakest_score:.2f}, "
                f"weakest plane: {weakest_plane}. "
                "WELL does not seal — pass through arifOS.verify → AAA.judge."
            ),
        },
        "awaiting_verification": route != "PROCEED",
        # F12 verdict hygiene — NEVER include these:
        # "sealed": <absent>
        # "verdict": <absent>
        # "acted_on": <absent>
        "f2_provenance": "compose(human=well state.json, machine=per-organ /health, governance=consent+events.jsonl)",
        "f4_privacy": "leaves_host:false",
        "f8_truth_class": "DER",
        "f8_evidence_label": "DER",
        "f11_consent": None,
        "f12_verdict_hygiene": "no_seal_no_verdict_in_well_response",
        "f13_sovereign": "OPERATOR_VETO_INTACT",
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }
