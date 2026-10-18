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

Route decision (F12 recommendation, never verdict) — emitted as `signal`, with
`route` mirrored for existing consumers:
  SABAR   — any organ CRITICAL
  HOLD    — governance breach OR unified < 0.50
  RECOVER — weakest plane = human, score < 0.70
  REDUCE_LOAD — weakest plane = machine, score < 0.85
  PROCEED — unified ≥ 0.85, no breaches
  INSUFFICIENT_EVIDENCE — no plane is currently measured

Weakest-link applies among MEASURED planes only (P0-2, 2026-09-28). A plane whose
data is EXPIRED/UNKNOWN is an absence: it lowers `coverage`, never the score.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
from typing import Any, Optional

from fastmcp import Context

from well_triad import events as _wt_events


# ── Freshness bands ─────────────────────────────────────────────────────────
# How old the DATA is, in the same TTL bands the health endpoint uses tonight:
#   FRESH < 1 h <= AGING < 4 h <= STALE < 24 h <= EXPIRED
# STALE is still a measurement (its number is the truth, its label is capped).
# EXPIRED / UNKNOWN are absences, and an absence must not enter min() -- that is
# how a 289h-old human reading vetoed two healthy planes.
_FRESH_MAX_S = 3600
_AGING_MAX_S = 4 * 3600
_STALE_MAX_S = 24 * 3600
_UNMEASURED_BANDS = ("EXPIRED", "UNKNOWN")


def _freshness_band(measured_at: Any) -> dict[str, Any]:
    """Classify a data timestamp -> {band, age_hours, reason}. Never guesses."""
    if not measured_at:
        return {
            "band": "UNKNOWN",
            "age_hours": None,
            "reason": "no measurement timestamp in the data",
        }
    try:
        ts = _dt.datetime.fromisoformat(str(measured_at).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return {
            "band": "UNKNOWN",
            "age_hours": None,
            "reason": f"unreadable measurement timestamp {measured_at!r}",
        }
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=_dt.timezone.utc)
    age_s = max(0.0, (_dt.datetime.now(_dt.timezone.utc) - ts).total_seconds())
    age_hours = round(age_s / 3600.0, 1)
    if age_s < _FRESH_MAX_S:
        band = "FRESH"
    elif age_s < _AGING_MAX_S:
        band = "AGING"
    elif age_s < _STALE_MAX_S:
        band = "STALE"
    else:
        band = "EXPIRED"
    return {"band": band, "age_hours": age_hours, "reason": f"{band}: data is {age_hours}h old"}


def _live_probe_freshness(probed_at: str) -> dict[str, Any]:
    """Freshness of a plane probed during this call — the data's own stamp is now."""
    return {"measured_at": probed_at, **_freshness_band(probed_at)}


# ── Composition helpers ─────────────────────────────────────────────────────

def _fetch_human_plane(actor_id: str) -> dict[str, Any]:
    """Read human substrate from state.json directly. Hermetic — no server import.

    Returns {score, state, weakest} where score is 0-1 (well_score/100),
    state is OPTIMAL/WATCH/DEGRADED/CRITICAL.
    """
    state_path = os.environ.get("WELL_STATE_PATH", "/var/lib/well/state.json")
    try:
        with open(state_path) as f:
            state = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # No file is an ABSENCE, not a middling measurement: band UNKNOWN keeps it
        # out of the roll-up instead of smuggling a fabricated 0.5 into min().
        return {
            "score": 0.5,
            "state": "UNKNOWN",
            "weakest": "unknown",
            "band": "UNKNOWN",
            "age_hours": None,
            "reason": "no human state file to read",
            "missing_evidence": ["no_state"],
        }

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

    # SELF-REPORT / stale inject must not be sold as OPTIMAL physiology.
    source = str(state.get("source_type") or state.get("truth_status") or "")
    evidence = str(state.get("evidence_class") or "")
    honesty = str(state.get("honesty_banner") or "")
    is_self = (
        "OPERATOR" in source.upper()
        or "SELF" in source.upper()
        or "SELF_REPORT" in evidence.upper()
        or "SELF-REPORT" in honesty.upper()
    )
    if is_self and state_label == "OPTIMAL":
        state_label = "WATCH"

    metrics = state.get("metrics", {})
    weakest = "none"
    weakest_score = 1.0
    for k in ("sleep", "cognitive", "metabolic", "structural"):
        v = metrics.get(k)
        if isinstance(v, dict) and "score" in v:
            if v["score"] < weakest_score:
                weakest_score = v["score"]
                weakest = k

    # The human reading ages from its own observation stamp, not from the moment
    # the file was rewritten: an operator inject refreshes `timestamp` while the
    # underlying substrate read keeps ageing (289h old as of 2026-09-28).
    measured_at = (
        state.get("last_successful_read")
        or state.get("timestamp")
        or state.get("last_successful_write")
    )
    freshness = _freshness_band(measured_at)
    if freshness["band"] in ("STALE", "EXPIRED") and state_label == "OPTIMAL":
        state_label = "WATCH"  # old data is never OPTIMAL physiology

    out = {
        "score": round(score, 3),
        "state": state_label,
        "weakest": weakest,
        "well_score": well_score,
        "measured_at": measured_at,
        "band": freshness["band"],
        "age_hours": freshness["age_hours"],
        "reason": freshness["reason"],
    }
    if is_self:
        out["honesty"] = "SELF_REPORT"
        out["note"] = "Number from sovereign inject / state.json — not a wearable. Do not treat as OPTIMAL physiology."
    return out


def _fetch_machine_plane(lookback_hours: int) -> dict[str, Any]:
    """Aggregate machine plane by reading per-organ /health directly. Hermetic stdlib.

    Returns {score, state, weakest, organs}.
    """
    import urllib.error
    import urllib.request
    import time as _time

    FEDERATION = (
        # FIXED 2026-09-04 FI-008: arifos 18081→8088, geox 18082→8081 (was crossing
        # into WEALTH), wealth 18086→18082. Verified vs live `ss -tlnp`.
        ("arifos", 8088),
        ("geox",   8081),
        ("well",   18083),
        ("aaa",    18084),
        ("frame",  18085),
        ("wealth", 18082),
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
    # APEX-ZEN FIX: floor dominates aggregate (arifOS rule). The machine plane's
    # state + route must reflect the WEAKEST organ, not the mean. A single
    # DEGRADED organ (e.g. well at 0.70) must NOT be painted "OPTIMAL/PROCEED"
    # by the average — mirrors the triadic plane's own floor-dominance behavior.
    floor_score = weakest_score if scores else 0.5
    floor_classification = (
        "OPTIMAL" if floor_score >= 0.85 else
        "WATCH" if floor_score >= 0.70 else
        "DEGRADED" if floor_score >= 0.50 else
        "CRITICAL"
    )

    critical_count = sum(1 for v in organs.values() if v.get("classification") == "CRITICAL")
    if critical_count >= 1:
        route = "SABAR"
    elif floor_score < 0.5:
        route = "HOLD"
    elif floor_score < 0.7:
        route = "REDUCE_LOAD"
    elif floor_score < 0.85:
        route = "RECOVER"
    else:
        route = "PROCEED"

    return {
        "score": round(floor_score, 3),
        "state": floor_classification,
        "avg_score": round(avg_score, 3),
        "weakest": weakest,
        "organs": organs,
        "route": route,
        "signal": route,
        "critical_count": critical_count,
        # The /health probes ran inside this call, so this data is `now` old.
        **_live_probe_freshness(_dt.datetime.now(_dt.timezone.utc).isoformat()),
    }


def _fetch_governance_plane(lookback_hours: int) -> dict[str, Any]:
    """Read governance plane: consent registry + recent recommendations.

    Returns {score, consent_intact, active_recommendations, open_attestations}.
    """
    state_path = os.environ.get("WELL_STATE_PATH", "/var/lib/well/state.json")
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
        # Consent registry and event ledger were read inside this call; there is
        # no cached observation here to age. A plane that later moves to a cached
        # read must carry its own measured_at so the roll-up can band it.
        **_live_probe_freshness(_dt.datetime.now(_dt.timezone.utc).isoformat()),
    }


def _route_decision(
    unified_score: float | None, weakest_plane: str | None, machine_critical_count: int
) -> str:
    """F12 verdict-hygiene route matrix. Recommendation, never verdict.

    Per `07-PHASE-4-TRIADIC-COMPOSITION.md` §3:
    - SABAR  : any machine CRITICAL
    - HOLD   : governance breach OR unified < 0.50
    - RECOVER: weakest plane = human, score < 0.70
    - REDUCE_LOAD: weakest plane = machine, score < 0.85 (or unified 0.50-0.70)
    - PROCEED: unified >= 0.85
    - INSUFFICIENT_EVIDENCE: nothing measured -- absence is not a score.
    """
    if unified_score is None or weakest_plane is None:
        return "INSUFFICIENT_EVIDENCE"
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

    Returns unified_score (over measured planes only), weakest_plane, coverage,
    excluded_planes and `signal` (F12 recommendation only; `route` is mirrored).
    NEVER returns sealed=True or verdict=<value> from WELL alone.

    When no plane is measured, unified_score is None and the signal is
    INSUFFICIENT_EVIDENCE -- WELL reports the absence instead of inventing a number.

    The signal is a recommendation, not a verdict. Caller must still pass
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

    # 4. Unified roll-up — weakest-link among MEASURED planes only (P0-2, 2026-09-28).
    #    An EXPIRED/UNKNOWN plane is an absence, and an absence that enters min()
    #    becomes a permanent veto wearing a measurement's clothes: a 289h-old human
    #    reading collapsed the unified score to ~0.05 while the machine and
    #    governance planes were healthy. Flooring it instead (the reverted attempt
    #    of 2026-09-28) only made that veto permanent. Absence lowers coverage and
    #    confidence, never the score.
    planes = [
        {
            "name": "human",
            "score": human_score,
            "band": human.get("band", "UNKNOWN"),
            "reason": human.get("reason", "no freshness reported for the human plane"),
        },
        {
            "name": "machine",
            "score": machine_score,
            "band": machine.get("band", "UNKNOWN"),
            "reason": machine.get("reason", "no freshness reported for the machine plane"),
        },
        {
            "name": "governance",
            "score": gov_score,
            "band": governance.get("band", "UNKNOWN"),
            "reason": governance.get("reason", "no freshness reported for the governance plane"),
        },
    ]
    measured = [
        p
        for p in planes
        if p["band"] not in _UNMEASURED_BANDS and isinstance(p["score"], (int, float))
    ]
    measured_names = {p["name"] for p in measured}
    excluded = {p["name"]: p["reason"] for p in planes if p["name"] not in measured_names}
    coverage = f"{len(measured)}/3 planes"

    if measured:
        unified_score = min(p["score"] for p in measured)
        # `planes` order keeps the historic tie-break: human, then machine, then
        # governance.
        weakest_plane = next(p["name"] for p in measured if p["score"] <= unified_score)
    else:
        unified_score = None
        weakest_plane = None
    unified_out = round(unified_score, 3) if unified_score is not None else None

    # 5. Signal (F12 recommendation only). The field is named `signal` because a
    #    composed recommendation is not a verdict; `route` is mirrored so existing
    #    consumers (phase5 HUD, snapshot readers) keep working.
    signal = _route_decision(unified_score, weakest_plane, machine_critical)
    if unified_out is None:
        f_recommendation = (
            f"{signal}: no plane is measured ({coverage}). WELL will not compose a "
            "score out of absence — restore a fresh read before interpreting state."
        )
    else:
        f_recommendation = (
            f"{signal}: triadic score {unified_out:.2f}, "
            f"weakest plane: {weakest_plane}. "
            "WELL does not seal — pass through arifOS.verify → AAA.judge."
        )

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
                "unified_score": unified_out,
                "weakest_plane": weakest_plane,
                "route": signal,
                "signal": signal,
                "coverage": coverage,
                "excluded_planes": sorted(excluded),
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
            "band": machine.get("band"),
            "measured_at": machine.get("measured_at"),
            "weakest_organ": machine["weakest"],
            "route": machine["route"],
            "signal": machine["route"],
            "critical_count": machine_critical,
            "organs": machine["organs"],
        },
        "governance": governance,
        "triadic": {
            "unified_score": unified_out,
            "weakest_plane": weakest_plane,
            "signal": signal,
            "route": signal,  # mirrored key -- existing consumers read triadic.route
            "coverage": coverage,
            "measured_planes": sorted(measured_names),
            "excluded_planes": excluded,
            "plane_bands": {p["name"]: p["band"] for p in planes},
            "f_recommendation": f_recommendation,
        },
        "awaiting_verification": signal != "PROCEED",
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
