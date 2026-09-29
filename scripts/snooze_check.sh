#!/usr/bin/env bash
# Daily WELL biometric snooze check — runs at 09:00 MYT via user crontab.
# If state.json is older than 24h, prints a one-line nudge to the log.
# If fresh, prints "no action needed".
# Never pages, never emails, never escalates.

set -euo pipefail

STATE_FILE="${WELL_STATE_PATH:-/var/lib/well/state.json}"  # LIVE organ; decoy retired 2026-09-29
LOG_FILE="/var/log/well-biometric-snooze.log"
MAX_AGE_HOURS=24
TS="$(date -u +%Y-%m-%dT%H:%M:%S+00:00)"

mkdir -p "$(dirname "$LOG_FILE")"
touch "$LOG_FILE"

if [[ ! -f "$STATE_FILE" ]]; then
  echo "[$TS] STATE FILE MISSING — run /root/WELL/biometric_inject.sh" >> "$LOG_FILE"
  exit 0
fi

AGE_HOURS="$(python3 -c "
import json, datetime, sys
try:
    d = json.load(open('$STATE_FILE'))
    ts = d.get('timestamp')
    if not ts:
        print('999')
        sys.exit(0)
    t = datetime.datetime.fromisoformat(ts.replace('Z','+00:00'))
    age_h = (datetime.datetime.now(datetime.timezone.utc) - t).total_seconds() / 3600
    print(f'{age_h:.1f}')
except Exception as e:
    print('999')
" 2>/dev/null || echo "999")"

if awk "BEGIN{exit !($AGE_HOURS > $MAX_AGE_HOURS)}"; then
  echo "[$TS] STALE  age=${AGE_HOURS}h — /root/WELL/SNOOZE_BIOMETRIC.md · /root/WELL/biometric_inject.sh" >> "$LOG_FILE"
else
  echo "[$TS] FRESH  age=${AGE_HOURS}h — no action needed" >> "$LOG_FILE"
fi
