#!/usr/bin/env python3
"""ack_consumer — human-acceptance callback consumer (APEX-ZEN 666).

CAPTURE STATUS (2026-09-17): BLOCKED on the shared-bot architecture.
  - Gateway polls getUpdates on ASI_ARIFOS_BOT_TOKEN.
  - cron-deliver sends via ASI_BOT_TOKEN — SAME underlying bot (verified distinct=False).
  - Gateway package contains NO callback_query handling (drops them unlogged).
  Therefore NO live capture path exists today. This consumer is dual-mode and
  ready for either unblock:

    Mode A (dedicated token):  ack_consumer.py poll
      Runs getUpdates(allowed_updates=["callback_query"]) on
      ACK_BOT_TOKEN (a SECOND bot token, F13 procurement). Telegram delivers
      callbacks for messages sent BY that bot — so ACCEPT lanes must also send
      via ACK_BOT_TOKEN. Zero conflict with the gateway bot.

    Mode B (gateway feed):     ack_consumer.py stdin
      A gateway plugin (or any forwarder) pipes callback_query JSON lines to
      stdin. Each line is validated and applied idempotently via ack_apply.

Security:
  - Callbacks accepted ONLY from the original recipient chat (chat_id match
    against the SENT receipt).
  - answerCallbackQuery is sent (stops the button spinner) only when the
    callback came from the authorized chat.

Offline test (no network):    ack_consumer.py --selftest
"""

import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ack_apply import apply as apply_ack  # noqa: E402

AUTHORIZED_CHAT = "267378578"  # Arif DM — the only lane ACCEPT is designed for


def tg(method: str, token: str, payload: dict):
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def handle_callback(cbq: dict, token: str | None = None) -> dict:
    """Validate + apply one callback_query update. Returns disposition."""
    cb = cbq.get("callback_query") or cbq
    data = cb.get("data") or ""
    msg = cb.get("message") or {}
    chat = str(msg.get("chat", {}).get("id", ""))
    received_at = datetime.now(timezone.utc).isoformat()

    if not data.startswith("ack:"):
        return {"result": "ignored", "reason": "not an ack callback"}
    if chat != AUTHORIZED_CHAT:
        _answer(cb, token, "⚠️ Not authorized for this chat")
        return {"result": "rejected", "reason": f"chat {chat} != {AUTHORIZED_CHAT}"}

    _, action, ack_token = (data.split(":") + ["", ""])[:3]
    out: dict = apply_ack(
        {
            "ack_token": ack_token,
            "action": action,
            "chat_id": chat,
            "callback_id": cb.get("id"),
            "received_at": received_at,
        }
    )
    label = {
        "accepted": "✅ Direkodkan",
        "rejected": "❌ Direkodkan",
        "repeat_requested": "🔁 Akan diulang",
    }.get(str(out.get("ack_state") or ""), "✓")
    if out.get("result") == "no-op":
        label = f"✓ Sudah {out.get('reason', 'direkod')}"
    _answer(cb, token, label)
    return out


def _answer(cb: dict, token: str | None, text: str):
    if not token or not cb.get("id"):
        return
    try:
        tg("answerCallbackQuery", token, {"callback_query_id": cb["id"], "text": text})
    except Exception:
        pass  # answer is UX-only; ack state already applied idempotently


def poll():
    token = os.environ.get("ACK_BOT_TOKEN")
    if not token:
        print(
            json.dumps(
                {
                    "result": "blocked",
                    "reason": "ACK_BOT_TOKEN absent — dedicated-token mode unavailable. "
                    "See module docstring: gateway owns the shared bot's poll.",
                }
            )
        )
        sys.exit(2)
    offset = 0
    print(
        f"[ack_consumer] polling callback_query on dedicated token...", file=sys.stderr
    )
    while True:
        try:
            updates = tg(
                "getUpdates",
                token,
                {
                    "offset": offset,
                    "timeout": 25,
                    "allowed_updates": ["callback_query"],
                },
            )
            for u in updates.get("result", []):
                offset = max(offset, u["update_id"] + 1)
                print(json.dumps(handle_callback(u, token)))
        except Exception as e:
            print(json.dumps({"result": "error", "reason": str(e)}), file=sys.stderr)


def stdin_mode():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            print(json.dumps(handle_callback(json.loads(line))))
        except json.JSONDecodeError:
            print(json.dumps({"result": "ignored", "reason": "unparseable line"}))


def selftest():
    """Offline: wrong chat rejected; valid applied once; duplicate = no-op."""
    import tempfile, shutil
    from pathlib import Path
    import ack_apply

    tmp = Path(tempfile.mkdtemp())
    fake_log = tmp / "log.jsonl"
    ack_apply.RECEIPT_LOG = fake_log
    ack_apply.AUDIT_LOG = tmp / "audit.jsonl"
    fake_log.write_text(
        json.dumps(
            {
                "status": "SENT",
                "chat_id": AUTHORIZED_CHAT,
                "telegram_message_id": 111,
                "content_sha256": "abc",
            }
        )
        + "\n"
    )
    r1 = handle_callback(
        {
            "callback_query": {
                "id": "cb1",
                "data": "ack:accept:tok1",
                "message": {"chat": {"id": int(AUTHORIZED_CHAT)}},
            }
        }
    )
    r2 = handle_callback(
        {
            "callback_query": {
                "id": "cb2",
                "data": "ack:accept:tok1",
                "message": {"chat": {"id": 999999}},
            }
        }
    )
    r3 = handle_callback(
        {
            "callback_query": {
                "id": "cb3",
                "data": "ack:accept:tok1",
                "message": {"chat": {"id": int(AUTHORIZED_CHAT)}},
            }
        }
    )
    ok = (
        r1["result"] == "applied"
        and r2["result"].startswith("rejected")
        and r3["result"] == "no-op"
    )
    print(
        json.dumps(
            {
                "selftest": "PASS" if ok else "FAIL",
                "valid_applied": r1["result"],
                "wrong_chat": r2["result"],
                "duplicate": r3["result"],
            },
            indent=1,
        )
    )
    shutil.rmtree(tmp)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "stdin"
    {"poll": poll, "stdin": stdin_mode, "--selftest": selftest}.get(mode, stdin_mode)()
