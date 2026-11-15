#!/usr/bin/env python3
"""Hourly bounded disk-evidence scan -> /var/lib/well/disk_evidence.json.

Run via well-disk-evidence.service (Nice=19, IOSchedulingClass=idle).
Env: WELL_DISK_PER_PATH_TIMEOUT_S (default 900), WELL_DISK_TOTAL_BUDGET_S (2400).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import disk_evidence as de  # noqa: E402


def main() -> int:
    ev = de.collect(
        per_path_timeout_s=float(os.environ.get("WELL_DISK_PER_PATH_TIMEOUT_S", 900)),
        total_budget_s=float(os.environ.get("WELL_DISK_TOTAL_BUDGET_S", 2400)),
    )
    de.write_evidence(ev)
    r = de.reconcile(ev)
    print(f"[disk-evidence] status={ev['status']} took={ev['collection_seconds']}s "
          f"confidence={r['confidence']} :: {r['message']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
