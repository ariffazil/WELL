#!/bin/bash
# WELL freshness cron — T1, no LLM. Machine telemetry + health only.
# Silent when service up. Exit 0 on honest INSUFFICIENT_DATA (not fake healthy).
set -euo pipefail
LOG_DIR=/root/forge_work/well-cron
mkdir -p "$LOG_DIR"
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)

if [[ -x /root/WELL/.venv/bin/python3 ]]; then
  /root/WELL/.venv/bin/python3 /root/WELL/scripts/machine_telemetry.py \
    >>"$LOG_DIR/telemetry.log" 2>&1 || true
fi

H=$(curl -sf --max-time 8 http://127.0.0.1:18083/health || true)
if [[ -z "$H" ]]; then
  echo "$TS WELL_DOWN" | tee -a "$LOG_DIR/alerts.log"
  exit 2
fi

echo "$H" | python3 -c "
import json, sys, datetime
d = json.load(sys.stdin)
ts = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
status = d.get('status')
truth = d.get('truth_status')
fresh = d.get('freshness_band')
age = d.get('state_age_hours')
sig = d.get('well_signal')
line = f'{ts} status={status} truth={truth} fresh={fresh} age={age} signal={sig}'
print(line)
open('$LOG_DIR/freshness.log','a').write(line+'\n')
# Honest insufficient biometrics is not a cron failure
if status == 'degraded' and truth == 'INSUFFICIENT_DATA':
    sys.exit(0)
if status in ('healthy', 'ok'):
    sys.exit(0)
if status == 'degraded':
    sys.exit(1)
sys.exit(0)
"
