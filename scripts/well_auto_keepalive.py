#!/usr/bin/env python3
"""well_auto_keepalive.py — Substrate observability keepalive. Restored 2026-08-02, hardened 2026-08-25."""
import json, os, time
from datetime import datetime, timezone
from pathlib import Path

state_path = Path("/root/WELL/state.json")
now_iso = datetime.now(timezone.utc).isoformat()

if state_path.exists():
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # This job proves the CRON is alive. It does not prove the human was measured,
        # so it may only write its own liveness fields. Advancing last_successful_*
        # here (the old behaviour) manufactured an observation clock, and stamping
        # freshness "FRESH" made a stale or absent reading look current -- twice: the
        # 2026-08-01 pytest fixture at this path stayed labelled FRESH for 8 weeks.
        data["keepalive_ts"] = now_iso
        data["keepalive_status"] = "ALIVE"
        with open(state_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        pass

receipt = {"tool": "well_auto_keepalive", "ts": now_iso, "status": "liveness_only", "state_refreshed": False}
print(json.dumps(receipt))
