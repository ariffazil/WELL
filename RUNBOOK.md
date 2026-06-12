# RUNBOOK.md — WELL (Human Readiness)

> **Organ:** WELL | **Port:** 18083
> **Last Updated:** 2026-06-12

## Start / Stop
```bash
systemctl start well
systemctl stop well
systemctl restart well
systemctl status well
```

## Health Check
```bash
curl -s http://127.0.0.1:18083/health | python3 -m json.tool
```

## Test
```bash
cd /root/WELL
pip install -e .
python test_well.py
```

## Logs
```bash
journalctl -u well -n 50 --no-pager
```

## Common Failure Modes
| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| WELL_HOLD / truth_status=EXPIRED | Stale biometric state | Arif must call `well_log_state` with fresh data |
| /health unreachable | Service crashed | `systemctl restart well` |
| well_score low | Mock data in state.json | See SNOOZE_BIOMETRIC.md for auto-sleeper |

## What NOT to Do
- Do NOT inject fake biometric data (F13 sovereign territory)
- Do NOT change REFLECT_ONLY authority boundary
- Do NOT bind to 0.0.0.0
