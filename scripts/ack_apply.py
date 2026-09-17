#!/usr/bin/env python3
"""ack_apply — idempotent human-acceptance state applier (APEX-ZEN 666).

State chain (never collapsed):
  produced ≠ sent ≠ delivered ≠ observed ≠ ACKNOWLEDGED
Telegram API success proves platform acceptance for transmission — NOT human
observation. A button callback proves a deliberate tap — NOT comprehension.

Idempotency law: ack may transition pending → {accepted|rejected|repeat_requested}
EXACTLY ONCE per receipt. Duplicate callbacks, retries, or replays are no-ops
with an audit line. Original production/delivery evidence is NEVER overwritten.

Usage:
  ack_apply.py <callback_json>        # apply one callback
  echo '{...}' | ack_apply.py -       # stdin

Callback contract (from ack_consumer or future gateway plugin):
  {"ack_token": "...", "action": "accept|reject|repeat",
   "chat_id": "...", "callback_id": "...", "received_at": "ISO"}
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

RECEIPT_LOG = Path("/root/WELL/state/digest_delivery_log.jsonl")
AUDIT_LOG = Path("/root/WELL/state/ack_audit.jsonl")
VALID_ACTIONS = {
    "accept": "accepted",
    "reject": "rejected",
    "repeat": "repeat_requested",
}


def apply(cb: dict) -> dict:
    token = cb.get("ack_token", "")
    action = cb.get("action", "")
    if action not in VALID_ACTIONS:
        return {"result": "rejected", "reason": f"invalid action '{action}'"}
    state = VALID_ACTIONS[action]
    now = datetime.now(timezone.utc).isoformat()

    entries = []
    if RECEIPT_LOG.exists():
        entries = [
            json.loads(l) for l in RECEIPT_LOG.read_text().splitlines() if l.strip()
        ]

    # find target: latest SENT receipt carrying this ack_token's chat + content linkage
    target_idx = None
    for i in range(len(entries) - 1, -1, -1):
        e = entries[i]
        if e.get("status") != "SENT":
            continue
        if str(e.get("chat_id")) != str(cb.get("chat_id")):
            continue
        target_idx = i
        break

    audit = {
        "received_at": cb.get("received_at", now),
        "ack_token": token,
        "action": action,
        "chat_id": cb.get("chat_id"),
        "callback_id": cb.get("callback_id"),
        "applied_at": now,
    }

    if target_idx is None:
        audit["result"] = "rejected"
        audit["reason"] = "no SENT receipt for chat"
        _audit(audit)
        return {"result": "rejected", "reason": "no SENT receipt for chat"}

    tgt = entries[target_idx]
    ack = tgt.get("human_ack_state") or tgt.get("ack_state")

    if ack in ("accepted", "rejected", "repeat_requested"):
        audit["result"] = "no-op"
        audit["reason"] = f"already {ack} (idempotent)"
        _audit(audit)
        return {"result": "no-op", "reason": f"already {ack}"}

    # linkage fields — additive, never overwriting delivery evidence
    tgt["logical_obligation_id"] = tgt.get("logical_obligation_id") or cb.get(
        "logical_obligation_id"
    )
    tgt["ack_state"] = state
    tgt["ack_at"] = now
    tgt["ack_actor_chat_id"] = cb.get("chat_id")
    tgt["ack_callback_id"] = cb.get("callback_id")
    tgt["ack_token"] = token

    RECEIPT_LOG.write_text(
        "\n".join(json.dumps(e, ensure_ascii=False) for e in entries) + "\n"
    )
    audit["result"] = "applied"
    audit["receipt_index"] = target_idx
    _audit(audit)
    return {"result": "applied", "ack_state": state, "receipt_index": target_idx}


def _audit(a: dict):
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_LOG.open("a") as f:
        f.write(json.dumps(a, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    raw = (
        sys.stdin.read()
        if (len(sys.argv) < 2 or sys.argv[1] == "-")
        else open(sys.argv[1]).read()
    )
    print(json.dumps(apply(json.loads(raw)), indent=1))
