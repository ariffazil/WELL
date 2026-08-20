"""
well_triad.phase5_observability — Canonical Phase 5 observability surface.

Forged 2026-08-20. F13 SEALED. Production.

Exports 3 read-only tools to be registered with FastMCP in server.py:
  well_get_triadic_snapshot              (read /state/triadic_snapshot.json)
  well_render_hud_panel                  (HUD format from snapshot)
  well_frame_read_snapshot               (FRAME evidence-only reader)

Authority ceiling: REFLECT_ONLY (no write, no propose, no seal).

Snapshot path: /state/triadic_snapshot.json
  - Written by well-snapshot cron (every 60s, hermetic)
  - Read by HUD, AAA, FRAME
  - Schema: triadic_snapshot v1.0
  - F1 amanah: snapshot file is read-only from outside WELL.

Snapshot shape (cron writer wraps well_assess_triadic_state response):
{
  "schema": "triadic_snapshot v1.0",
  "timestamp_utc": "...",
  "source": "well:18083/well_assess_triadic_state",
  "snapshot_path": "/state/triadic_snapshot.json",
  "snapshot_writer": "well-snapshot cron (hermetic)",
  "triadic": <full well_assess_triadic_state response>
}

Floor envelope: F1 (no biometric leak), F2 (provenance), F4 (privacy),
                F8 (OBS evidence), F12 (FRAME never verdict), F13 (sovereign)
"""

from __future__ import annotations

import datetime as _dt
import json
import os
from typing import Any, Optional

from fastmcp import Context


SNAPSHOT_PATH = "/state/triadic_snapshot.json"
SNAPSHOT_SCHEMA = "triadic_snapshot v1.0"


# ── Helpers ─────────────────────────────────────────────────────────────────

def _read_snapshot_raw() -> dict[str, Any]:
    """Read the canonical snapshot file. Returns graceful UNKNOWN if absent."""
    try:
        with open(SNAPSHOT_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "schema": SNAPSHOT_SCHEMA,
            "ok": False,
            "missing_evidence": ["snapshot_not_yet_written"],
        }
    except json.JSONDecodeError as e:
        return {
            "schema": SNAPSHOT_SCHEMA,
            "ok": False,
            "missing_evidence": ["snapshot_corrupted"],
            "error": str(e)[:200],
        }


def _get_triadic_data(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Unwrap triadic payload from snapshot wrapper."""
    return snapshot.get("triadic", {})


def _snapshot_age_seconds(snapshot: dict[str, Any]) -> Optional[float]:
    ts = snapshot.get("timestamp_utc")
    if not ts:
        return None
    try:
        snap_dt = _dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        now = _dt.datetime.now(_dt.timezone.utc)
        return round((now - snap_dt).total_seconds(), 1)
    except Exception:
        return None


def _human_score_int(triadic: dict[str, Any]) -> int:
    human = triadic.get("human", {})
    s = human.get("score", 0) or 0
    return int(round(float(s) * 100))


def _machine_score_int(triadic: dict[str, Any]) -> int:
    machine = triadic.get("machine", {})
    s = machine.get("score", 0) or 0
    return int(round(float(s) * 100))


# ── Tool 1: well_get_triadic_snapshot ───────────────────────────────────────

def well_get_triadic_snapshot(ctx: Optional[Context] = None) -> dict[str, Any]:
    """[Triad Phase 5] Read the canonical triadic snapshot from /state/.

    Returns the snapshot wrapper (with triadic data nested under 'triadic' key).
    """
    snapshot = _read_snapshot_raw()
    triadic = _get_triadic_data(snapshot)
    age = _snapshot_age_seconds(snapshot)

    if not snapshot.get("ok", True) and not triadic:
        return {
            "ok": False,
            "schema": SNAPSHOT_SCHEMA,
            "missing_evidence": snapshot.get("missing_evidence", ["snapshot_not_yet_written"]),
            "error": snapshot.get("error"),
            "snapshot_path": SNAPSHOT_PATH,
            "snapshot_age_seconds": age,
            "f2_provenance": f"file:{SNAPSHOT_PATH}",
            "f4_privacy": "leaves_host:false",
            "f8_truth_class": "OBS",
            "f8_evidence_label": "NONE",
            "f13_sovereign": "OPERATOR_VETO_INTACT",
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        }

    return {
        "ok": True,
        "snapshot": snapshot,
        "snapshot_path": SNAPSHOT_PATH,
        "snapshot_age_seconds": age,
        "triadic": triadic,
        "f2_provenance": f"file:{SNAPSHOT_PATH} (cron-written)",
        "f4_privacy": "leaves_host:false",
        "f8_truth_class": "OBS",
        "f8_evidence_label": "OBS",
        "f13_sovereign": "OPERATOR_VETO_INTACT",
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


# ── Tool 2: well_render_hud_panel ───────────────────────────────────────────

def well_render_hud_panel(ctx: Optional[Context] = None) -> dict[str, Any]:
    """[Triad Phase 5] Render HUD cockpit ASCII panel from triadic snapshot.

    F1 amanah: panel never includes per-biometric fields, only aggregate scores.
    """
    snapshot = _read_snapshot_raw()
    triadic = _get_triadic_data(snapshot)
    age = _snapshot_age_seconds(snapshot)

    if not snapshot.get("ok", True) and not triadic:
        panel_lines = [
            "+- WELL.triad.summary ---------------------+",
            "| snapshot not yet written                |",
            f"| missing: {(snapshot.get('missing_evidence') or ['unknown'])[0]:32s} |",
            "+------------------------------------------+",
        ]
        return {
            "ok": False,
            "panel": "\n".join(panel_lines),
            "missing_evidence": snapshot.get("missing_evidence", ["snapshot_not_yet_written"]),
            "f2_provenance": "compose(snapshot, hud-renderer)",
            "f4_privacy": "leaves_host:false",
            "f8_truth_class": "OBS",
            "f8_evidence_label": "NONE",
            "f13_sovereign": "OPERATOR_VETO_INTACT",
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        }

    human = triadic.get("human", {})
    machine = triadic.get("machine", {})
    governance = triadic.get("governance", {})
    triadic_t = triadic.get("triadic", {})

    human_score = _human_score_int(triadic)
    machine_score = _machine_score_int(triadic)
    gov_intact = governance.get("consent_intact", False)
    gov_label = "OK" if gov_intact else "BREACH"
    route = str(triadic_t.get("route", "UNKNOWN"))
    weakest = str(triadic_t.get("weakest_plane", "unknown"))
    weak_organ = machine.get("weakest_organ", "unknown")
    if weakest == "machine" and weak_organ:
        weakest_line = f"{weakest} ({weak_organ})"
    else:
        weakest_line = weakest
    age_str = f"{age}s ago" if age is not None else "unknown"

    def pad(s: str, w: int) -> str:
        s = str(s)
        return s + " " * max(0, w - len(s))

    panel_lines = [
        "+- WELL.triad.summary ---------------------+",
        "| human    machine    governance    route |",
        f"| {pad(human_score, 7)} {pad(machine_score, 10)} {pad(gov_label, 13)} {pad(route, 8)} |",
        f"| {pad(str(human.get('state', '?')), 7)} {pad(str(machine.get('state', '?')), 10)} {pad(' ', 13)} {pad(' ', 8)} |",
        f"| weakest: {pad(weakest_line, 35)}|",
        f"| snapshot: {pad(age_str, 34)}|",
        "+------------------------------------------+",
    ]
    panel = "\n".join(panel_lines)

    return {
        "ok": True,
        "panel": panel,
        "human": {"score": human.get("score"), "state": human.get("state")},
        "machine": {"score": machine.get("score"), "state": machine.get("state"), "weakest_organ": weak_organ},
        "governance": {"consent_intact": gov_intact},
        "triadic": {
            "unified_score": triadic_t.get("unified_score"),
            "weakest_plane": weakest,
            "route": route,
        },
        "snapshot_age_seconds": age,
        "f2_provenance": f"compose(snapshot@{SNAPSHOT_PATH}, hud-renderer)",
        "f4_privacy": "leaves_host:false (no biometric fields in panel)",
        "f8_truth_class": "OBS",
        "f8_evidence_label": "OBS",
        "f13_sovereign": "OPERATOR_VETO_INTACT",
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


# ── Tool 3: well_frame_read_snapshot ────────────────────────────────────────

def well_frame_read_snapshot(ctx: Optional[Context] = None) -> dict[str, Any]:
    """[Triad Phase 5] FRAME observer reads snapshot as evidence, never verdict.

    F12 verdict hygiene: returns `snapshot` (observation) + `frame_verdict:
    "EVIDENCE_ONLY"`. FRAME is the independent observer — never ratifies decisions.
    """
    snapshot = _read_snapshot_raw()
    triadic = _get_triadic_data(snapshot)
    age = _snapshot_age_seconds(snapshot)
    current_score = (triadic.get("triadic", {}) or {}).get("unified_score", 0.5)

    if not snapshot.get("ok", True) and not triadic:
        return {
            "ok": False,
            "snapshot": snapshot,
            "frame_role": "observer",
            "frame_verdict": "UNKNOWN",
            "frame_drift_delta": 0.0,
            "missing_evidence": snapshot.get("missing_evidence", ["snapshot_not_yet_written"]),
            "f12_verdict_hygiene": "frame_observes_not_verdicts",
            "f2_provenance": f"file:{SNAPSHOT_PATH}",
            "f4_privacy": "leaves_host:false",
            "f8_truth_class": "OBS",
            "f8_evidence_label": "NONE",
            "f13_sovereign": "OPERATOR_VETO_INTACT",
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        }

    return {
        "ok": True,
        "snapshot": snapshot,
        "frame_role": "observer",
        "frame_verdict": "EVIDENCE_ONLY",
        "frame_drift_delta": 0.0,
        "triadic_score_observed": current_score,
        "snapshot_age_seconds": age,
        "f2_provenance": f"file:{SNAPSHOT_PATH} (read by frame-observer)",
        "f4_privacy": "leaves_host:false",
        "f8_truth_class": "OBS",
        "f8_evidence_label": "OBS",
        "f12_verdict_hygiene": "frame_observes_not_verdicts",
        "f13_sovereign": "OPERATOR_VETO_INTACT",
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


# ── Snapshot writer (used by cron, not exposed as MCP tool) ─────────────────

def write_triadic_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Write the canonical triadic snapshot atomically.

    Used by the cron snapshotter. F1 amanah: snapshot is read-only from outside WELL.
    """
    payload = dict(snapshot)
    payload["schema"] = SNAPSHOT_SCHEMA
    payload["timestamp_utc"] = _dt.datetime.now(_dt.timezone.utc).isoformat()
    tmp_path = SNAPSHOT_PATH + ".tmp"
    os.makedirs(os.path.dirname(SNAPSHOT_PATH), exist_ok=True)
    with open(tmp_path, "w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
    os.replace(tmp_path, SNAPSHOT_PATH)
    return payload
