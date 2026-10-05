#!/bin/bash
# refresh_deploy_stamp.sh — P0 2026-10-05 (FI-008, F13 order "go")
# WELL runs from the /root/WELL checkout (well.service ExecStart), so the
# deployed/built stamps must track repo HEAD. Stale stamps produced FALSE
# deployment_drift → health "degraded" while code was current (stamps were
# aligned 2026-10-01 at 7a145bf; HEAD moved to 3e2e663 on 2026-10-04 and
# nothing refreshed them).
set -u
H="$(git -C /root/WELL rev-parse --short=7 HEAD 2>/dev/null)"
[ -z "${H:-}" ] && exit 0
echo "$H" > /root/WELL/.git_commit 2>/dev/null || true
echo "$H" > /opt/well/.git_commit 2>/dev/null || true
for M in /opt/well/release-manifest.json /root/WELL/release-manifest.json; do
  [ -f "$M" ] || continue
  /root/WELL/.venv/bin/python3 - "$M" "$H" >/dev/null 2>&1 <<'PY' || true
import json, sys, datetime
path, head = sys.argv[1], sys.argv[2]
d = json.load(open(path))
d["git_commit"] = head
d["aligned_at"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
d["note"] = "stamp refreshed: aligned to HEAD (refresh_deploy_stamp.sh)"
json.dump(d, open(path, "w"), indent=2)
PY
done
exit 0
