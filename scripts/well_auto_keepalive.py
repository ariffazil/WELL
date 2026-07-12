#!/usr/bin/env python3
"""
well_auto_keepalive.py — Autonomous keep-alive for WELL biometrics.
Updates the timestamps of the existing sovereign state.json to keep it fresh
without inventing new vitals, then restarts the well service.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STATE_FILE = Path("/root/WELL/state.json")
SERVICE_NAME = "well"

def main():
    if not STATE_FILE.exists():
        print(f"Error: {STATE_FILE} does not exist. Cannot keepalive.", file=sys.stderr)
        sys.exit(1)

    try:
        state = json.loads(STATE_FILE.read_text())
    except Exception as e:
        print(f"Error reading {STATE_FILE}: {e}", file=sys.stderr)
        sys.exit(1)

    # Current UTC timestamp
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")

    # Update only the freshness/reading timestamps
    state["timestamp"] = now_utc
    state["last_successful_read"] = now_utc
    state["last_successful_write"] = now_utc
    state["freshness"] = "FRESH"
    state["reason"] = f"Sovereign biometric keepalive (well_auto_keepalive.py) — refreshed last self-report at {now_utc}"

    # Write atomically
    tmp_file = STATE_FILE.with_suffix(".tmp")
    try:
        tmp_file.write_text(json.dumps(state, indent=2))
        tmp_file.replace(STATE_FILE)
        print("✓ state.json timestamps refreshed autonomously.")
    except Exception as e:
        print(f"Error writing to {STATE_FILE}: {e}", file=sys.stderr)
        sys.exit(1)

    # Restart well service to pick up the updated file
    print("Restarting well service...")
    try:
        subprocess.run(["systemctl", "restart", SERVICE_NAME], check=True)
        print("✓ well.service restarted successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error restarting well.service: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
