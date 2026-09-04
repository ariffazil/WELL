#!/usr/bin/env python3
"""Triadic snapshot writer — calls WELL organ for triadic state and writes to file."""
import json, subprocess, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

MYT = timezone(timedelta(hours=8))
OUT = Path("/root/WELL/state/triadic_snapshot.json")

def main():
    try:
        r = subprocess.run(
            ["curl", "-sf", "-m", "10", "http://127.0.0.1:18083/health"],
            capture_output=True, text=True, timeout=15
        )
        if r.returncode != 0 or not r.stdout.strip():
            print("WELL organ unreachable", file=sys.stderr)
            sys.exit(1)
        health = json.loads(r.stdout)
        
        snapshot = {
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
        
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(snapshot, indent=2))
        print(f"Written: {OUT} ({len(json.dumps(snapshot))} bytes)")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
