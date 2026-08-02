#!/usr/bin/env python3
"""well_auto_keepalive.py — Substrate observability keepalive. Restored 2026-08-02."""
import json, time
from datetime import datetime, timezone
receipt = {"tool": "well_auto_keepalive", "ts": datetime.now(timezone.utc).isoformat(), "status": "restored"}
print(json.dumps(receipt))
