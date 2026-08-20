"""
well_triad.phase2_tools — Canonical Phase 2 tool implementations.

Forged 2026-08-20. F13 SEALED. Production.

Exports 6 read-only tools to be registered with FastMCP in server.py:
  well_observe_machine
  well_observe_federation_thermal
  well_observe_scar_load
  well_observe_drift_field
  well_observe_evidence_backlog
  well_classify_machine_state

Authority ceiling: REFLECT_ONLY (no change). Read-only. Appends read-receipt
events to events.jsonl with truth_class="OBS" (direct observation from FRAME
or per-organ /health). F1 no-biometric-leakage enforced on aggregates.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import sys
import time as _time
import urllib.error
import urllib.request
from typing import Any, Literal, Optional

from fastmcp import Context

from well_triad import events as _wt_events


# Federation topology — single source of truth.
# Each entry: (organ_id, port, probe_path)
FEDERATION_ORGANS: tuple[tuple[str, int, str], ...] = (
    ("arifos", 18081, "/health"),
    ("geox",   18082, "/health"),
    ("well",   18083, "/health"),
    ("frame",  18085, "/health"),
    # AAA :18084 has no /mcp; use /health anyway
    ("aaa",    18084, "/health"),
    # Wealth (offline as of probe)
    ("wealth", 18086, "/health"),
)

# Strip these keys from any per-organ payload to enforce F1.
F1_REDACT_KEYS: frozenset[str] = frozenset({
    "biometric", "biometrics", "hrv", "hrv_ms", "resting_hr",
    "weight_kg", "spo2", "spo2_pct", "skin_temp", "body_fat",
    "lean_mass", "vo2_max", "intake", "daily_intake",
    "substances", "alcohol_timeline", "thermal_sessions",
    "consent", "scopes",
})


def _redact_biometric(payload: dict[str, Any]) -> dict[str, Any]:
    """Recursively strip biometric / substrate-leak fields from a payload.

    F1 amanah — no per-agent biometric data leaves the host when crossing
    planes via federation aggregate.
    """
    if not isinstance(payload, dict):
        return payload
    out: dict[str, Any] = {}
    for k, v in payload.items():
        if k in F1_REDACT_KEYS:
            continue
        if isinstance(v, dict):
            out[k] = _redact_biometric(v)
        elif isinstance(v, list):
            out[k] = [
                _redact_biometric(x) if isinstance(x, dict) else x
                for x in v
            ]
        else:
            out[k] = v
    return out


def _probe_organ_http(name: str, port: int, path: str, timeout: float = 2.0) -> dict[str, Any]:
    """Probe an organ's HTTP endpoint. Returns typed dict or error envelope."""
    url = f"http://127.0.0.1:{port}{path}"
    t0 = _time.monotonic()
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            latency_ms = (_time.monotonic() - t0) * 1000.0
            body = resp.read().decode("utf-8")
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                data = {"raw": body[:200]}
            return {
                "ok": True,
                "data": data,
                "latency_ms": round(latency_ms, 2),
                "status_code": resp.status,
            }
    except urllib.error.HTTPError as e:
        latency_ms = (_time.monotonic() - t0) * 1000.0
        return {
            "ok": False,
            "error": f"HTTP_{e.code}",
            "latency_ms": round(latency_ms, 2),
            "status_code": e.code,
        }
    except (urllib.error.URLError, OSError) as e:
        latency_ms = (_time.monotonic() - t0) * 1000.0
        return {
            "ok": False,
            "error": str(e)[:200],
            "latency_ms": round(latency_ms, 2),
            "status_code": None,
        }


def _classify_machine(score: float) -> str:
    """OPTIMAL / WATCH / DEGRADED / CRITICAL from a 0-1 score."""
    if score >= 0.85:
        return "OPTIMAL"
    if score >= 0.70:
        return "WATCH"
    if score >= 0.50:
        return "DEGRADED"
    return "CRITICAL"


def _score_from_organ_data(name: str, data: dict[str, Any]) -> float:
    """Compute a 0-1 thermal score from per-organ /health data.

    Heuristic, NOT a verdict. Returns 0.5 (UNKNOWN) if cannot parse.
    """
    if not data:
        return 0.5
    # Status string
    status = (
        data.get("status")
        or data.get("health")
        or data.get("state")
        or "UNKNOWN"
    )
    s = str(status).upper()
    if s in ("HEALTHY", "OK", "OPTIMAL", "READY", "STABLE", "GREEN"):
        base = 0.95
    elif s in ("WATCH", "WARN", "AMBER", "BELOW_BASELINE", "DEGRADED"):
        base = 0.70
    elif s in ("CRITICAL", "DOWN", "UNHEALTHY", "ERROR", "RED", "OFFLINE"):
        base = 0.30
    else:
        base = 0.55

    # Penalize for slow latency
    latency = data.get("latency_ms") if isinstance(data.get("latency_ms"), (int, float)) else None
    if latency is not None and latency > 500:
        base -= 0.10
    if latency is not None and latency > 1500:
        base -= 0.20
    return max(0.05, min(1.0, base))


# ── Tool 1: well_observe_machine ────────────────────────────────────────────

def well_observe_machine(
    agent_id: Literal["arifos", "geox", "well", "aaa", "frame", "wealth"] = "well",
    surface: Literal["thermal", "drift", "scar", "evidence", "all"] = "all",
    ctx: Optional[Context] = None,
) -> dict[str, Any]:
    """Observe a single organ's thermal/drift/scar/evidence card.

    Bridges to FRAME /frame/probe/{organ} for thermal; FRAME /frame/drift
    for drift; arifOS vault for scar (graceful UNKNOWN if no endpoint);
    AAA cockpit for evidence backlog (graceful UNKNOWN if no endpoint).
    """
    # Find organ in topology
    organ_entry = next((e for e in FEDERATION_ORGANS if e[0] == agent_id), None)
    if organ_entry is None:
        return {
            "ok": False,
            "error": "UNKNOWN_AGENT",
            "detail": f"unknown agent_id {agent_id!r}",
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
            "f13_sovereign": "OPERATOR_VETO_INTACT",
        }

    name, port, path = organ_entry
    out: dict[str, Any] = {
        "ok": True,
        "agent_id": name,
        "port": port,
        "surface": surface,
    }

    # ── Thermal: probe /health directly + FRAME probe (if available) ───────
    if surface in ("thermal", "all"):
        direct = _probe_organ_http(name, port, path)
        if direct["ok"]:
            redacted = _redact_biometric(direct["data"])
            out["thermal"] = {
                "status": redacted.get("status", "UNKNOWN"),
                "latency_ms": direct["latency_ms"],
                "score": _score_from_organ_data(name, redacted),
                "details": redacted,
            }
        else:
            out["thermal"] = {
                "status": "DOWN",
                "latency_ms": direct.get("latency_ms"),
                "score": 0.05,
                "error": direct.get("error"),
            }

    # ── Drift: FRAME /frame/drift filters ──────────────────────────────────
    if surface in ("drift", "all"):
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:18085/frame/drift", method="GET"
            )
            with urllib.request.urlopen(req, timeout=2) as resp:
                drift_all = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            drift_all = {"signals": [], "error": str(e)[:200]}

        signals = [
            s for s in drift_all.get("signals", [])
            if s.get("organ") == name or name in str(s.get("organ", ""))
        ]
        out["drift"] = {
            "samples": signals,
            "count": len(signals),
            "verdict": drift_all.get("overall_verdict", "UNKNOWN"),
            "missing_evidence": [] if signals else ["no_drift_signal_for_organ"],
        }

    # ── Scar: arifOS vault endpoint (graceful UNKNOWN if absent) ──────────
    if surface in ("scar", "all"):
        scar_attempts = []
        for ep in ("/vault/scar_count", "/scar_count", "/vault/scar"):
            r = _probe_organ_http("arifos", 18081, ep)
            scar_attempts.append({"endpoint": ep, "ok": r["ok"], "status": r.get("status_code")})
            if r["ok"]:
                out["scar"] = {
                    "count": r["data"].get("count", 0)
                    if isinstance(r["data"], dict) else 0,
                    "volume": r["data"].get("volume", 0)
                    if isinstance(r["data"], dict) else 0,
                    "source": f"arifos:18081{ep}",
                    "missing_evidence": [],
                }
                break
        else:
            out["scar"] = {
                "count": 0,
                "volume": 0,
                "source": None,
                "missing_evidence": ["no_scar_endpoint"],
                "attempts": scar_attempts,
            }

    # ── Evidence backlog: AAA cockpit (graceful UNKNOWN if absent) ─────────
    if surface in ("evidence", "all"):
        ev_attempts = []
        for ep in ("/cockpit/queue_depth", "/queue_depth", "/cockpit/backlog"):
            r = _probe_organ_http("aaa", 18084, ep)
            ev_attempts.append({"endpoint": ep, "ok": r["ok"], "status": r.get("status_code")})
            if r["ok"]:
                out["evidence"] = {
                    "queue_depth": r["data"].get("queue_depth", 0)
                    if isinstance(r["data"], dict) else 0,
                    "oldest_unsealed_epoch": r["data"].get("oldest_unsealed_epoch")
                    if isinstance(r["data"], dict) else None,
                    "last_seal_epoch": r["data"].get("last_seal_epoch")
                    if isinstance(r["data"], dict) else None,
                    "source": f"aaa:18084{ep}",
                    "missing_evidence": [],
                }
                break
        else:
            out["evidence"] = {
                "queue_depth": 0,
                "oldest_unsealed_epoch": None,
                "last_seal_epoch": None,
                "source": None,
                "missing_evidence": ["no_evidence_endpoint"],
                "attempts": ev_attempts,
            }

    # ── Classification ─────────────────────────────────────────────────────
    if "thermal" in out:
        score = out["thermal"]["score"]
        out["classification"] = _classify_machine(score)
    else:
        out["classification"] = "UNKNOWN"

    # ── Read receipt event ────────────────────────────────────────────────
    try:
        _wt_events.append_typed_event(
            event=f"WELL_TRIAD_2_OBSERVE_MACHINE",
            phase=2,
            tool="well_observe_machine",
            plane="machine",
            inputs={"agent_id": name, "surface": surface},
            outputs={"classification": out.get("classification")},
            source=f"frame:18085 + per-organ :{port}",
            truth_class="OBS",
            evidence_label="OBS",
        )
    except Exception:
        pass  # event chain optional for read tools

    out["f8_truth_class"] = "OBS"
    out["f8_evidence_label"] = "OBS"
    out["f1_no_biometric_leakage"] = True
    out["f13_sovereign"] = "OPERATOR_VETO_INTACT"
    out["w0"] = "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT"
    return out


# ── Tool 2: well_observe_federation_thermal ─────────────────────────────────

def well_observe_federation_thermal(
    lookback_hours: int = 1,
    ctx: Optional[Context] = None,
) -> dict[str, Any]:
    """Aggregate thermal state across all 5 live organs."""
    organs: dict[str, dict[str, Any]] = {}
    unknown_organs: list[str] = []

    for name, port, path in FEDERATION_ORGANS:
        probe = _probe_organ_http(name, port, path)
        if probe["ok"]:
            redacted = _redact_biometric(probe["data"])
            score = _score_from_organ_data(name, redacted)
            organs[name] = {
                "status": redacted.get("status", "UNKNOWN"),
                "score": round(score, 3),
                "classification": _classify_machine(score),
                "latency_ms": probe["latency_ms"],
                "port": port,
                "f1_redacted": True,
            }
        else:
            organs[name] = {
                "status": "DOWN",
                "score": 0.0,
                "classification": "CRITICAL",
                "latency_ms": probe.get("latency_ms"),
                "error": probe.get("error"),
                "port": port,
            }
            unknown_organs.append(name)

    # Find weakest
    scored = {n: v.get("score", 0.0) for n, v in organs.items()}
    weakest = min(scored, key=lambda k: scored[k]) if scored else "unknown"

    # Federation route
    critical_count = sum(1 for v in organs.values() if v.get("classification") == "CRITICAL")
    if critical_count >= 1:
        route = "SABAR"
    elif min(scored.values()) < 0.5:
        route = "HOLD"
    elif min(scored.values()) < 0.7:
        route = "REDUCE_LOAD"
    elif min(scored.values()) < 0.85:
        route = "RECOVER"
    else:
        route = "PROCEED"

    # Read receipt
    try:
        _wt_events.append_typed_event(
            event="WELL_TRIAD_2_OBSERVE_FEDERATION_THERMAL",
            phase=2,
            tool="well_observe_federation_thermal",
            plane="machine",
            inputs={"lookback_hours": lookback_hours},
            outputs={"weakest": weakest, "route": route},
            source="per-organ /health aggregate",
            truth_class="OBS",
            evidence_label="OBS",
        )
    except Exception:
        pass

    return {
        "ok": True,
        "lookback_hours": lookback_hours,
        "organs": organs,
        "weakest": weakest,
        "unknown_organs": unknown_organs,
        "route": route,
        "critical_count": critical_count,
        "f1_no_biometric_leakage": True,
        "f8_truth_class": "OBS",
        "f8_evidence_label": "OBS",
        "f13_sovereign": "OPERATOR_VETO_INTACT",
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


# ── Tool 3: well_observe_scar_load ──────────────────────────────────────────

def well_observe_scar_load(
    agent_id: Optional[str] = None,
    ctx: Optional[Context] = None,
) -> dict[str, Any]:
    """Scar volume per organ. Graceful UNKNOWN if no scar endpoint exists."""
    attempts: list[dict[str, Any]] = []
    data: Optional[dict[str, Any]] = None
    for ep in ("/vault/scar_count", "/scar_count", "/vault/scar"):
        r = _probe_organ_http("arifos", 18081, ep)
        attempts.append({"endpoint": ep, "ok": r["ok"], "status": r.get("status_code")})
        if r["ok"]:
            data = r["data"] if isinstance(r["data"], dict) else {}
            break

    if data is None:
        # Phase 4 will route through well_observe_machine(agent_id, surface="scar").
        # For now, return graceful UNKNOWN with missing_evidence.
        result = {
            "ok": True,
            "agent_id": agent_id or "all",
            "scar_count": 0,
            "scar_volume": 0,
            "oldest_scar_epoch": None,
            "classification": "UNKNOWN",
            "missing_evidence": ["no_scar_endpoint"],
            "attempts": attempts,
            "f8_truth_class": "OBS",
            "f8_evidence_label": "NONE",
            "f13_sovereign": "OPERATOR_VETO_INTACT",
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        }
    else:
        scar_count = data.get("count", 0)
        scar_volume = data.get("volume", 0)
        if scar_count == 0:
            classification = "NOMINAL"
        elif scar_count < 10:
            classification = "ELEVATED"
        elif scar_count < 100:
            classification = "HEAVY"
        else:
            classification = "CRITICAL"
        result = {
            "ok": True,
            "agent_id": agent_id or "all",
            "scar_count": scar_count,
            "scar_volume": scar_volume,
            "oldest_scar_epoch": data.get("oldest_scar_epoch"),
            "classification": classification,
            "source": f"arifos:18081{ep}",
            "f8_truth_class": "OBS",
            "f8_evidence_label": "OBS",
            "f13_sovereign": "OPERATOR_VETO_INTACT",
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        }

    # Read receipt
    try:
        _wt_events.append_typed_event(
            event="WELL_TRIAD_2_OBSERVE_SCAR_LOAD",
            phase=2,
            tool="well_observe_scar_load",
            plane="machine",
            inputs={"agent_id": agent_id},
            outputs={"classification": result.get("classification")},
            source="arifos:18081 vault (attempted)",
            truth_class=result.get("f8_truth_class", "OBS"),
            evidence_label=result.get("f8_evidence_label", "NONE"),
        )
    except Exception:
        pass

    return result


# ── Tool 4: well_observe_drift_field ────────────────────────────────────────

def well_observe_drift_field(
    lookback_hours: int = 24,
    ctx: Optional[Context] = None,
) -> dict[str, Any]:
    """FRAME observer drift over last N hours."""
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:18085/frame/drift", method="GET"
        )
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {
            "ok": False,
            "error": "FRAME_UNREACHABLE",
            "detail": str(e)[:200],
            "lookback_hours": lookback_hours,
            "samples": [],
            "missing_evidence": ["frame_unreachable"],
            "f8_truth_class": "OBS",
            "f8_evidence_label": "NONE",
            "f13_sovereign": "OPERATOR_VETO_INTACT",
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        }

    signals = data.get("signals", [])
    severities = [s.get("severity", "UNKNOWN") for s in signals]
    deltas = []
    for s in signals:
        d = s.get("drift_delta")
        if d is not None:
            try:
                deltas.append(float(d))
            except (TypeError, ValueError):
                pass

    if deltas:
        mean = sum(deltas) / len(deltas)
        max_drift = max(deltas)
    else:
        mean = 0.0
        max_drift = 0.0

    if "CRITICAL" in severities:
        trend = "critical"
    elif abs(max_drift) > 0.5:
        trend = "drifting"
    else:
        trend = "stable"

    result = {
        "ok": True,
        "lookback_hours": lookback_hours,
        "samples": signals,
        "count": len(signals),
        "mean_drift": round(mean, 4),
        "max_drift": round(max_drift, 4),
        "trend": trend,
        "overall_verdict": data.get("overall_verdict", "UNKNOWN"),
        "baseline_age_days": data.get("baseline_age_days"),
        "f8_truth_class": "OBS",
        "f8_evidence_label": "OBS",
        "f13_sovereign": "OPERATOR_VETO_INTACT",
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }

    # Read receipt
    try:
        _wt_events.append_typed_event(
            event="WELL_TRIAD_2_OBSERVE_DRIFT_FIELD",
            phase=2,
            tool="well_observe_drift_field",
            plane="machine",
            inputs={"lookback_hours": lookback_hours},
            outputs={"trend": trend, "max_drift": max_drift},
            source="frame:18085/frame/drift",
            truth_class="OBS",
            evidence_label="OBS",
        )
    except Exception:
        pass

    return result


# ── Tool 5: well_observe_evidence_backlog ───────────────────────────────────

def well_observe_evidence_backlog(
    agent_id: Optional[str] = None,
    ctx: Optional[Context] = None,
) -> dict[str, Any]:
    """Receipt queue depth. Graceful UNKNOWN if no endpoint exists."""
    attempts: list[dict[str, Any]] = []
    data: Optional[dict[str, Any]] = None
    for ep in ("/cockpit/queue_depth", "/queue_depth", "/cockpit/backlog"):
        r = _probe_organ_http("aaa", 18084, ep)
        attempts.append({"endpoint": ep, "ok": r["ok"], "status": r.get("status_code")})
        if r["ok"]:
            data = r["data"] if isinstance(r["data"], dict) else {}
            break

    if data is None:
        result = {
            "ok": True,
            "agent_id": agent_id or "all",
            "queue_depth": 0,
            "oldest_unsealed_epoch": None,
            "last_seal_epoch": None,
            "missing_evidence": ["no_evidence_endpoint"],
            "attempts": attempts,
            "f8_truth_class": "OBS",
            "f8_evidence_label": "NONE",
            "f13_sovereign": "OPERATOR_VETO_INTACT",
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        }
    else:
        queue_depth = data.get("queue_depth", 0)
        if queue_depth == 0:
            classification = "NOMINAL"
        elif queue_depth < 10:
            classification = "WATCH"
        elif queue_depth < 100:
            classification = "ELEVATED"
        else:
            classification = "BACKLOG"
        result = {
            "ok": True,
            "agent_id": agent_id or "all",
            "queue_depth": queue_depth,
            "oldest_unsealed_epoch": data.get("oldest_unsealed_epoch"),
            "last_seal_epoch": data.get("last_seal_epoch"),
            "classification": classification,
            "source": f"aaa:18084{ep}",
            "f8_truth_class": "OBS",
            "f8_evidence_label": "OBS",
            "f13_sovereign": "OPERATOR_VETO_INTACT",
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        }

    # Read receipt
    try:
        _wt_events.append_typed_event(
            event="WELL_TRIAD_2_OBSERVE_EVIDENCE_BACKLOG",
            phase=2,
            tool="well_observe_evidence_backlog",
            plane="machine",
            inputs={"agent_id": agent_id},
            outputs={"classification": result.get("classification")},
            source="aaa:18084 cockpit (attempted)",
            truth_class=result.get("f8_truth_class", "OBS"),
            evidence_label=result.get("f8_evidence_label", "NONE"),
        )
    except Exception:
        pass

    return result


# ── Tool 6: well_classify_machine_state ─────────────────────────────────────

def well_classify_machine_state(
    agent_id: Literal["arifos", "geox", "well", "aaa", "frame", "wealth"] = "well",
    ctx: Optional[Context] = None,
) -> dict[str, Any]:
    """Compose prior tools for one agent, return classification + reason + evidence.

    Never writes verdict to vault. Recommendation only.
    """
    # Compose via well_observe_machine(agent_id, surface="thermal")
    thermal_card = well_observe_machine(agent_id=agent_id, surface="thermal")
    thermal_score = thermal_card.get("thermal", {}).get("score", 0.5)
    thermal_class = thermal_card.get("thermal", {}).get("status", "UNKNOWN")
    classification = thermal_card.get("classification", "UNKNOWN")

    # Drift also from FRAME
    drift_card = well_observe_machine(agent_id=agent_id, surface="drift")
    drift_signals = drift_card.get("drift", {}).get("samples", [])
    drift_critical = any(s.get("severity") == "CRITICAL" for s in drift_signals)

    # Reason
    if classification == "CRITICAL" or drift_critical:
        reason = (
            f"thermal={thermal_class} (score {thermal_score}); "
            f"drift_critical={drift_critical}"
        )
    elif classification == "WATCH":
        reason = f"thermal={thermal_class} (score {thermal_score}); watching for degradation"
    else:
        reason = f"thermal={thermal_class} (score {thermal_score})"

    # NEVER seal — recommendation only
    result = {
        "ok": True,
        "agent_id": agent_id,
        "classification": classification,
        "reason": reason,
        "evidence": [
            {"source": "thermal", "score": thermal_score, "status": thermal_class},
            {"source": "drift", "samples": len(drift_signals), "critical": drift_critical},
        ],
        "thermal_score": thermal_score,
        "drift_critical": drift_critical,
        # F12 verdict hygiene — never return these:
        # "sealed": <absent>
        # "verdict": <absent>
        # "acted_on": <absent>
        "f8_truth_class": "DER",
        "f8_evidence_label": "DER",
        "f12_verdict_hygiene": "no_seal_no_verdict_in_well_response",
        "f13_sovereign": "OPERATOR_VETO_INTACT",
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }

    # Read receipt
    try:
        _wt_events.append_typed_event(
            event="WELL_TRIAD_2_CLASSIFY_MACHINE_STATE",
            phase=2,
            tool="well_classify_machine_state",
            plane="machine",
            inputs={"agent_id": agent_id},
            outputs={"classification": classification},
            source="compose(thermal,drift)",
            truth_class="DER",
            evidence_label="DER",
        )
    except Exception:
        pass

    return result