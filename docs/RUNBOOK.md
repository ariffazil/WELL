# RUNBOOK.md — WELL (Human Readiness)

> **Organ:** WELL | **Port:** 18083
> **Last Updated:** 2026-07-01
> **Tools:** 22 somatic | **Server:** `server.py` (~15,755 lines)

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
uv sync --frozen
pytest tests/ -q --tb=short
python test_well.py
```

## Logs
```bash
journalctl -u well -n 50 --no-pager
journalctl -u well -f         # Follow live
```

## Deploy
```bash
cd /root/WELL
git pull
systemctl restart well
curl -s http://127.0.0.1:18083/health | python3 -m json.tool
```

## Common Failure Modes
| Symptom | Likely Cause | Fix |
|---------|-------------|------|
| WELL_HOLD / truth_status=EXPIRED | Stale biometric state | Arif must call `well_log_state` with fresh data |
| /health unreachable | Service crashed | `systemctl restart well` |
| vault_bridge errors | VAULT999 writer unavailable | Check vault999-writer.service on port 5001 |
| Metabolic flux alarm | Accumulated cognitive load | Reallocation signal at flux >= 0.65; system hold at >= 0.85 |

## What NOT to Do
- Do NOT inject fake biometric data (F13 sovereign territory)
- Do NOT change REFLECT_ONLY authority boundary
- Do NOT bind to 0.0.0.0
- Do NOT persist biometric data to cloud (ADR-001 — local disk only)
