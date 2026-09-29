#!/usr/bin/env python3
"""well_auto_keepalive.py — Substrate observability keepalive. Restored 2026-08-02, hardened 2026-08-25.
2026-09-29: retargeted from the /root/WELL/state.json decoy (2026-08-01 test fixture,
keepalive-ticked, environment=TEST) to the LIVE organ (WELL_STATE_PATH convention);
flock added — well_ingest.py runs on the same */30 tick and both are read-modify-write
on this file."""
import fcntl
import json, os, time
from datetime import datetime, timezone
from pathlib import Path

state_path = Path(os.environ.get("WELL_STATE_PATH", "/var/lib/well/state.json"))
now_iso = datetime.now(timezone.utc).isoformat()

if state_path.exists():
    try:
        with open(str(state_path) + ".lock", "w") as lock_fh:
            fcntl.flock(lock_fh, fcntl.LOCK_EX)
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

receipt = {"tool": "well_auto_keepalive", "ts": now_iso, "status": "liveness_only",
           "state_path": str(state_path), "state_refreshed": False}
print(json.dumps(receipt))
