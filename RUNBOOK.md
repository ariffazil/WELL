> **Canonical RUNBOOK:** `/root/RUNBOOK.md` — this file is organ-specific overrides only.
> **SOT:** 2026-07-24 | **seal_seq:** fed-phase-7

# 📋 RUNBOOK — WELL Operations

> **SOT:** 2026-07-20

## Quick Health
```bash
curl -s http://localhost:18083/health | python3 -m json.tool
```

## Restart
```bash
sudo systemctl restart well
```

## Logs
```bash
journalctl -u well --since "5 min ago" --no-pager
```

## Deploy
```bash
cd /root/WELL
# Build + test, then:
sudo systemctl restart well
curl -s http://localhost:18083/health
```

## Escalation
F13 SOVEREIGN: Muhammad Arif bin Fazil — 888_HOLD for irreversible actions.

