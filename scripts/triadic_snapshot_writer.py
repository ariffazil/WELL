#!/usr/bin/env python3
"""Triadic snapshot writer v2 — canonical /state/triadic_snapshot.json (v1.0 schema).

Resurrected 2026-09-04 (cron-zen-audit P0): the original hermetic cron snapshotter
died 2026-08-20 when its scheduler was retired; consumers (well_get_triadic_snapshot,
well_render_hud_panel, well_frame_read_snapshot — HUD/AAA/FRAME) kept reading the
frozen file. v2 composes the FULL triadic assessment via the organ's own canonical
phase4 tool and writes BOTH surfaces:

  1. /state/triadic_snapshot.json            — canonical v1.0 (atomic, phase5 writer)
  2. /root/WELL/state/triadic_snapshot.json  — health digest (compat, same as v1 writer)

Run under /opt/well/.venv/bin/python3 (organ deps). Scheduled 60s by
triadic-snapshot.timer. F1: rollback = restore .bak-20260904-FI008 and disable timer.
"""
import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

MYT = timezone(timedelta(hours=8))
DIGEST = Path("/root/WELL/state/triadic_snapshot.json")

# Prefer the RUNNING organ's code, fall back to repo copy.
for _base in ("/opt/well", "/root/WELL"):
    if _base not in sys.path:
        sys.path.insert(0, _base)

from well_triad.phase4_tools import well_assess_triadic_state
from well_triad.phase5_observability import write_triadic_snapshot


def canonical_snapshot() -> Path:
    """Compose full triadic state and write the canonical snapshot atomically."""
    triadic = well_assess_triadic_state(actor_id="arif", lookback_hours=1)
    snapshot = {
        "schema": "triadic_snapshot v1.0",
        "source": "well:18083/well_assess_triadic_state",
        "snapshot_path": "/state/triadic_snapshot.json",
        "snapshot_writer": "triadic-snapshot.timer (systemd, resurrected 2026-09-04 FI-008)",
        "triadic": triadic,
    }
    write_triadic_snapshot(snapshot)  # atomic + stamps timestamp_utc
    return Path("/state/triadic_snapshot.json")


def health_digest() -> None:
    """Compat digest from /health — identical output to the v1 writer."""
    try:
        r = subprocess.run(
            ["curl", "-sf", "-m", "10", "http://127.0.0.1:18083/health"],
            capture_output=True, text=True, timeout=15,
        )
        if r.returncode != 0 or not r.stdout.strip():
            print("WELL organ unreachable (digest skipped)", file=sys.stderr)
            return
        health = json.loads(r.stdout)
        digest = {
            "timestamp": datetime.now(MYT).isoformat(),
            "source": "triadic_snapshot_writer",
            "organ_status": health.get("status", "unknown"),
            "well_score": health.get("well_score", None),
            "clarity": health.get("metrics", {}).get("cognitive", {}).get("clarity", None),
            "decision_fatigue": health.get("metrics", {}).get("cognitive", {}).get("decision_fatigue", None),
            "human_substrate": health.get("human_substrate", {}).get("status", "unknown"),
            "machine_substrate": health.get("machine_substrate", {}).get("status", "unknown"),
            "freshness": health.get("freshness", {}).get("status", "unknown"),
            "state_age_hours": health.get("state_age_hours", None),
            "floors_violated": health.get("floors_violated", []),
        }
        DIGEST.parent.mkdir(parents=True, exist_ok=True)
        DIGEST.write_text(json.dumps(digest, indent=2))
        print(f"digest: {DIGEST}")
    except Exception as e:
        print(f"digest error (non-fatal): {e}", file=sys.stderr)


def main() -> int:
    rc = 0
    try:
        path = canonical_snapshot()
        print(f"canonical: {path} ({path.stat().st_size} bytes)")
    except Exception as e:
        # Canonical write is the P0 obligation — failure IS fatal for this tick.
        print(f"canonical error: {e}", file=sys.stderr)
        rc = 1
    health_digest()
    return rc


if __name__ == "__main__":
    sys.exit(main())
