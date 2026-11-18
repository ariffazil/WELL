"""WELL::HUMAN_CHECKIN::v1 — Telegram adapter (P2).

The adapter ONLY: reads a reply, hands it to intake, prints a receipt.
No scoring logic lives here. No service restart. No state.json writes.

Usage (CLI, same code path the Telegram wiring will call):
    python -m human_checkin "6.5,5,8"
    python -m human_checkin --status

Telegram message contract (F13 UX, 2026-11-19):
    Ask:  "Tidur, tenaga, beban? Balas: 6.5,5,8"
    Reply format: sleep_hours,energy,load  (partial allowed: 6.5,5)
"""

from __future__ import annotations

import os
import sys

from .intake import DEFAULT_EVENT_LOG, ingest
from .projection import DEFAULT_PROJECTION, apply_to_state, project, refresh


def handle_checkin_reply(
    text: str,
    event_log: str = DEFAULT_EVENT_LOG,
    projection_path: str = DEFAULT_PROJECTION,
    apply_state: bool = True,
) -> str:
    """Full v1 path: intake -> projection refresh -> presence merge -> BM receipt."""
    receipt = ingest(text, event_log=event_log)
    if receipt["status"] == "rejected":
        return f"DITOLAK — {receipt['reason']}\n{receipt['note']}"
    if receipt["status"] == "duplicate":
        return receipt.get("note", "Check-in sama dah tercatat.")
    # accepted: projection reads from the event log, never from state.json;
    # presence merge is allowlist-only and needs a FRESH signal to assert.
    proj = refresh(event_log=event_log, path=projection_path)
    tail = ""
    if apply_state:
        state_path = os.environ.get("WELL_STATE_PATH", "/var/lib/well/state.json")
        merge = apply_to_state(proj, state_path)
        if merge.get("applied"):
            tail = (
                "\nPresence: OPERATOR_REPORTED direkod (F6 kelihatan). Bukan VERIFIED."
            )
        else:
            tail = "\nPresence: tiada isyarat segar — tiada dakwaan presence dibuat."
    head = "✓ " + project(proj)
    return head + tail


def handle_status(projection_path: str = DEFAULT_PROJECTION) -> str:
    """Read-only projection status. No inference beyond the stored envelope."""
    try:
        with open(projection_path, "r", encoding="utf-8") as fh:
            import json

            proj = json.load(fh)
    except (FileNotFoundError, OSError):
        return "Tiada state manusia lagi. Balas check-in: 6.5,5,8 (tidur,tenaga,beban)."
    a = proj.get("attention_readiness", {})
    sig = proj.get("signals", {})
    lines = ["WELL human state (SELF_REPORT sahaja):"]
    for m, label in (("sleep_hours", "Tidur"), ("energy", "Tenaga"), ("load", "Beban")):
        s = sig.get(m, {})
        if s.get("freshness") in ("MISSING", "EXPIRED"):
            lines.append(f"{label}: tiada data segar [{s.get('freshness')}]")
        else:
            unit = "j" if m == "sleep_hours" else "/10"
            lines.append(f"{label}: {s['value']:g}{unit} [{s['freshness']}]")
    lines.append(
        f"Attention: {a.get('state', 'UNKNOWN')} ({a.get('confidence', 'NONE')})"
    )
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if not argv:
        print("Format: tidur,tenaga,beban — cth 6.5,5,8 (atau 6.5,5 untuk separa)")
        return 1
    if argv[0] in ("--status", "-s"):
        print(handle_status())
        return 0
    print(handle_checkin_reply(" ".join(argv)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
