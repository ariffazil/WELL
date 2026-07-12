#!/usr/bin/env python3
"""
well_auto_feed — TTL watchdog + biometric prompt.

Runs as a cron script (no_agent mode). Checks state.json freshness.
If stale (>12h), outputs a prompt for the agent to ask Arif for biometrics.
If fresh, outputs nothing (silent).

Exit codes:
  0 = fresh (no output, silent)
  1 = stale (output prompt for agent)
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

STATE_FILE = Path("/root/WELL/state.json")
TTL_FRESH_HOURS = 12


def hours_since_last_feed() -> float:
    """Hours since last_successful_read or injection_ts."""
    try:
        state = json.loads(STATE_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return 999.0

    ts_str = state.get("last_successful_read") or state.get("signals_meta", {}).get("injection_ts")
    if not ts_str:
        return 999.0
    try:
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return max(0, (now - ts).total_seconds() / 3600)
    except (ValueError, TypeError):
        return 999.0


def main():
    hours = hours_since_last_feed()

    if hours < TTL_FRESH_HOURS:
        # Fresh — silent
        sys.exit(0)

    # Stale — output prompt for agent
    print(f"WELL BIOMETRIC STALE ({hours:.0f}h since last feed). Ask Arif:")
    print("1. Sleep hours last night? (0-12)")
    print("2. Energy level? (1-10)")
    print("3. Stress level? (1-10)")
    print("4. How do you feel? (grounded/scattered/anxious/tired/clear)")
    print("")
    print("Then call: bash /root/WELL/scripts/biometric_inject.sh --non-interactive \\")
    print("  --delta-s <1.0-energy/10> --peace2 <energy/10> --kappa-r <0.8-default> \\")
    print("  --rasa <feeling> --amanah 0.9")
    sys.exit(1)


if __name__ == "__main__":
    main()
