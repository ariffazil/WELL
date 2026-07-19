# WELL Biometrics — Accept Degraded (2026-07-12)

**Decision:** ACCEPT_DEGRADED (agentic Phase 888 #5)  
**Epoch:** 2026-07-12T05:45:31.848204+00:00

## Facts
- Service `well` **active**; MCP tools/list = **24** tools.
- Health may report `degraded` / `WELL_HOLD` / `INSUFFICIENT_DATA` when biometric `state.json` is stale.
- This is **not** organ death.

## What we will not do
- Invent or inject synthetic vitals (F2 TRUTH / F9 ANTI-HANTU).
- Auto-run `biometric_inject.sh` without Arif self-report.

## What clears RED/STALE
- Arif runs sovereign self-report: `WELL/scripts/biometric_inject.sh` (or equivalent consented input).

## Status
Federation continues with WELL as **REFLECT_ONLY** mirror. Degraded biometrics = honesty, not failure.
