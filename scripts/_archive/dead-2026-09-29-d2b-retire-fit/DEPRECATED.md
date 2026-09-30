# DEPRECATED — google_fit_bridge.py — Retired 2026-09-29

## Reason
- **F13 directive 2026-09-29**: "B-second retire Fit, wire phone-bridge"
- Bridge was 346-byte stub that emitted `{"status":"restored","note":"awaiting sovereign OAuth configuration"}` every 6h since ship day
- Token store `/root/WELL/google_fit_creds.json` never created
- 0 evidence of ever succeeding — declared capability, dead on disk

## Archived files
- google_fit_bridge.py   (sha256: see initial receipt)
- google_fit_auth_helper.py (sha256: see initial receipt)

## Replacement: phone-bridge (already exists, daemon down)
Path: `/root/AAA/phone-bridge/` — FastAPI server on Termux + VPS pickup_proxy.py
Live verbs (no F13 approval needed for read-only):
- `health` — liveness probe
- `battery` — battery_level, charging state
- `device` — model, OS, network
- `sensors` — accelerometer, light, step count

## Activation (F13 binary ONLY)
This is infrastructure mutation. The user must explicitly invoke:

```bash
# 1. On Termux (Arif's phone): start FastAPI server
ssh phone "cd /data/data/com.termux/files/home && nohup python3 phone-bridge/server.py &"

# 2. On VPS: start pickup_proxy
set -a && source /root/.secrets/kunci-root.env && set +a
nohup python3 /root/AAA/phone-bridge/pickup_proxy.py >> /var/log/phone_pickup.log 2>&1 &

# 3. Verify
curl -s http://127.0.0.1:18800/health
curl -s -X POST -H 'Content-Type: application/json' -d '{"verb":"battery"}' http://127.0.0.1:18800/battery
```

## Cron migration
Remove the line:
```
30 */6 * * * /root/.local/bin/jitu-guard google_fit_bridge && /root/WELL/scripts/google_fit_bridge.py >> /var/log/arifos/cron.log 2>&1
```

Replace with (when daemon verified live):
```
*/30 * * * * /usr/bin/curl -s -X POST -H 'Content-Type: application/json' -d '{"verb":"battery"}' http://127.0.0.1:18800/battery >> /var/log/phone_pickup.log 2>&1
```

Until Arif executes the activation steps: WELL state.json continues to use `evidence_class: SOVEREIGN_SELF_REPORT` (manual biometric_inject.sh). No phantom capability claim.

## Reanimation rule (F13 only)
If Arif chooses Fit over phone-bridge later:
1. F13 explicit order
2. Run google_fit_auth_helper.py interactively (browser flow)
3. Save token to /root/WELL/google_fit_creds.json
4. Restore cron entry
Until then: DEPRECATED.
