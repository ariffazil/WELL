"""WELL::HUMAN_ASK_GATE::v1 — decision-relevance gate for human WELL input.

Mission: WELL_HUMAN_ATTENTION_DEAMPLIFICATION (F13 directive 2026-11-20).

Contract (binding):
  1. TTL/freshness expiry alone may NEVER produce a human prompt. A stale
     self-report is NOT_RECENT, not a failure, and not a reason to ask.
  2. A human ask is allowed ONLY when ALL hold:
       a. a named consequential decision (decision_object) is currently blocked;
       b. the requested human input can change that decision's verdict;
       c. no scoped answer for the same decision/scope is already available;
       d. no equivalent request is already open (dedup across ALL agents);
       e. the prompt budget permits it (one ask per decision per scope window).
  3. No equivalent request open → agents SUBSCRIBE to the existing request.
     The first requester opens; everyone else defers silently.
  4. Human silence is never classified as illness, distress, fatigue, or any
     health state. This module emits gate state ONLY — it never claims or
     infers human condition.
  5. Scoped modes (NORMAL / LOW_ATTENTION / STOP_NONCRITICAL / HUMAN_ONLY)
     are expiring, revisable, scope-bound, non-diagnostic, and subordinate to
     any newer explicit human instruction (later set_mode replaces earlier).

State: one file, /var/lib/well/human_ask.json, atomic replace, bounded retention.
No daemon: every agent calls check()/open()/resolve() directly against shared
state; the file lock arbitrates cross-agent dedup.
"""

from __future__ import annotations

import fcntl
import json
import os
import tempfile
import time
import uuid
from typing import Any

STATE_PATH = os.environ.get("WELL_ASK_GATE_STATE", "/var/lib/well/human_ask.json")
SUBJECT_ID = "arif"

SCHEMA = "human_ask_gate_v1"

# Prompt budget: after one ask for a decision+scope, a second ask for the SAME
# decision is forbidden until the scope window lapses (material-context rule).
SCOPE_WINDOW_S = 4 * 3600

# A resolved scoped answer satisfies later checks for the same decision while
# its own window is unexpired.
ANSWER_REUSE_S = 3600

MODES = ("NORMAL", "LOW_ATTENTION", "STOP_NONCRITICAL", "HUMAN_ONLY")

RETENTION_MAX_REQUESTS = 100

VALID_REASONS = (
    "NO_DECISION_DEPENDENCY",
    "EQUIVALENT_REQUEST_OPEN",
    "SCOPED_ANSWER_AVAILABLE",
    "PROMPT_BUDGET_EXHAUSTED",
    "HUMAN_INPUT_NOT_REQUIRED",
    "MODE_RESTRICTS",
    "DECISION_BLOCKED",
)


def _now() -> float:
    return time.time()


def _empty_state() -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "subject": SUBJECT_ID,
        "requests": [],
        "modes": [],
        "updated_at_utc": _iso(_now()),
    }


def _iso(ts: float) -> str:
    import datetime as _dt

    return _dt.datetime.fromtimestamp(ts, _dt.timezone.utc).isoformat()


def _load(path: str = STATE_PATH) -> dict[str, Any]:
    try:
        with open(path) as fh:
            state = json.load(fh)
        if isinstance(state, dict) and state.get("schema") == SCHEMA:
            return state
    except (OSError, ValueError):
        pass
    return _empty_state()


def _save(state: dict[str, Any], path: str = STATE_PATH) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    state["updated_at_utc"] = _iso(_now())
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or ".", prefix=".ask_gate_")
    try:
        with os.fdopen(fd, "w") as fh:
            json.dump(state, fh, indent=1)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


class _Locked:
    """Cross-process advisory lock around read-modify-write cycles."""

    def __init__(self, path: str = STATE_PATH) -> None:
        self._lock_path = path + ".lock"
        self._fh: Any = None

    def __enter__(self) -> "_Locked":
        os.makedirs(os.path.dirname(self._lock_path) or ".", exist_ok=True)
        self._fh = open(self._lock_path, "a+")
        fcntl.flock(self._fh.fileno(), fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc: Any) -> None:
        try:
            fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
        finally:
            self._fh.close()
            self._fh = None


def _prune(state: dict[str, Any], now: float | None = None) -> dict[str, Any]:
    """Bounded retention: drop answered/closed whose reuse windows lapsed;
    keep the newest RETENTION_MAX_REQUESTS records."""
    now = now if now is not None else _now()
    kept: list[dict[str, Any]] = []
    for r in state.get("requests", []):
        status = r.get("status")
        if status == "OPEN":
            kept.append(r)
            continue
        exp = r.get("scope_expires_at_epoch")
        if isinstance(exp, (int, float)) and exp > now:
            kept.append(r)
    kept.sort(key=lambda r: r.get("opened_at_epoch", 0), reverse=True)
    state["requests"] = kept[:RETENTION_MAX_REQUESTS]
    state["modes"] = [
        m
        for m in state.get("modes", [])
        if isinstance(m.get("expires_at_epoch"), (int, float))
        and m["expires_at_epoch"] > now
    ]
    return state


def _active_mode(
    state: dict[str, Any], now: float | None = None
) -> dict[str, Any] | None:
    now = now if now is not None else _now()
    modes = [
        m
        for m in state.get("modes", [])
        if isinstance(m.get("expires_at_epoch"), (int, float))
        and m["expires_at_epoch"] > now
    ]
    if not modes:
        return None
    modes.sort(key=lambda m: m.get("set_at_epoch", 0))
    return modes[-1]  # newest explicit instruction wins (subordination rule)


def _dedup_key(decision_object: str, input_class: str, scope: str) -> str:
    return f"{SUBJECT_ID}|{decision_object.strip()}|{input_class.strip()}|{(scope or '').strip()}"


def check(
    decision_object: str | None = None,
    input_class: str = "human_state",
    scope: str = "",
    critical: bool = False,
    path: str = STATE_PATH,
) -> dict[str, Any]:
    """The ONLY sanctioned way an agent decides whether to prompt the human.

    Returns a machine-readable verdict. Suppression reasons (machine food,
    per Phase 4F of the directive):
      NO_DECISION_DEPENDENCY   — no named decision → never ask.
      EQUIVALENT_REQUEST_OPEN  — subscribe to the existing request_id.
      SCOPED_ANSWER_AVAILABLE  — consume the scoped resolution instead.
      PROMPT_BUDGET_EXHAUSTED  — one ask per decision per scope window.
      MODE_RESTRICTS           — an active scoped mode defers non-critical asks.
    YES carries exactly one reason: DECISION_BLOCKED (a request is opened).
    """
    now = _now()
    with _Locked(path):
        state = _prune(_load(path), now)
        mode = _active_mode(state, now)
        if mode is not None and not critical:
            return {
                "well_input_required": False,
                "reason": "MODE_RESTRICTS",
                "mode": mode.get("mode"),
                "request_id": None,
                "note": "non-critical ask deferred by active scoped mode",
            }
        if mode is not None and mode.get("mode") == "STOP_NONCRITICAL" and critical:
            # STOP_NONCRITICAL suppresses even flag-critical asks unless the
            # caller asserts an emergency lane explicitly (out of v1 scope).
            return {
                "well_input_required": False,
                "reason": "MODE_RESTRICTS",
                "mode": mode.get("mode"),
                "request_id": None,
                "note": "STOP_NONCRITICAL active",
            }
        if not decision_object or not str(decision_object).strip():
            return {
                "well_input_required": False,
                "reason": "NO_DECISION_DEPENDENCY",
                "request_id": None,
            }
        key = _dedup_key(str(decision_object), input_class, scope or "")
        matched = False
        for r in state["requests"]:
            if r.get("key") != key:
                continue
            matched = True
            if r["status"] == "OPEN":
                return {
                    "well_input_required": False,
                    "reason": "EQUIVALENT_REQUEST_OPEN",
                    "request_id": r["request_id"],
                    "opened_by": r.get("opened_by"),
                    "note": "subscribe to the existing request; do not ask again",
                }
            if r["status"] == "RESOLVED":
                exp = r.get("scope_expires_at_epoch") or 0
                if exp > now:
                    return {
                        "well_input_required": False,
                        "reason": "SCOPED_ANSWER_AVAILABLE",
                        "request_id": r["request_id"],
                        "resolution": r.get("resolution"),
                        "note": "reuse the scoped answer inside its window",
                    }
        if matched:
            return {
                "well_input_required": False,
                "reason": "PROMPT_BUDGET_EXHAUSTED",
                "request_id": None,
                "note": (
                    "a request for this decision already consumed its budget in "
                    "this scope window; material context change required"
                ),
            }
        return {
            "well_input_required": True,
            "reason": "ELIGIBLE_TO_OPEN",
            "request_id": None,
            "note": (
                "named decision, no open equivalent, no scoped answer, budget "
                "unspent — you may open ONE request via open_request()"
            ),
        }


def open_request(
    decision_object: str,
    input_class: str = "human_state",
    scope: str = "",
    critical: bool = False,
    opened_by: str = "agent",
    path: str = STATE_PATH,
) -> dict[str, Any]:
    """Open (or subscribe to) a human-input request for a blocked decision.

    First caller: opens the request, prompt budget 1.
    Any later caller with the same key: subscribes, no second prompt.
    Returns the request view either way.
    """
    now = _now()
    with _Locked(path):
        state = _prune(_load(path), now)
        mode = _active_mode(state, now)
        if mode is not None and not critical:
            return {
                "opened": False,
                "reason": "MODE_RESTRICTS",
                "mode": mode.get("mode"),
                "request_id": None,
            }
        key = _dedup_key(str(decision_object), input_class, scope or "")
        for r in state["requests"]:
            if r.get("key") != key:
                continue
            if r["status"] == "OPEN":
                return {
                    "opened": False,
                    "reason": "EQUIVALENT_REQUEST_OPEN",
                    "request_id": r["request_id"],
                    "note": "subscribed to existing request",
                }
            # budget rule: one ask per decision per scope window; a record
            # still inside its window blocks a second open for the same key.
            exp = r.get("next_eligible_prompt_at_epoch") or 0
            if r.get("status") in ("RESOLVED", "CLOSED") and exp <= now:
                continue
            if r.get("status") in ("RESOLVED", "CLOSED"):
                return {
                    "opened": False,
                    "reason": "PROMPT_BUDGET_EXHAUSTED",
                    "request_id": r["request_id"],
                    "note": "scope window for this decision has not lapsed",
                }
        request_id = f"ask_{uuid.uuid4().hex[:12]}"
        state["requests"].append(
            {
                "request_id": request_id,
                "key": key,
                "decision_object": str(decision_object),
                "input_class": input_class,
                "scope": scope or "",
                "status": "OPEN",
                "opened_by": opened_by,
                "opened_at_epoch": now,
                "opened_at_utc": _iso(now),
                "prompt_count": 1,
                "next_eligible_prompt_at_epoch": now + SCOPE_WINDOW_S,
                "consumers": [opened_by],
                "resolution": None,
                "resolved_at_utc": None,
            }
        )
        _save(state, path)
        return {
            "opened": True,
            "reason": "DECISION_BLOCKED",
            "request_id": request_id,
            "prompt_count": 1,
            "note": "ONE concise ask identifies the decision and why the answer changes it",
        }


def resolve(
    request_id: str,
    resolution: str,
    answer_reuse_s: int = ANSWER_REUSE_S,
    path: str = STATE_PATH,
) -> dict[str, Any]:
    """Human answered once → every subscribed agent consumes the scoped answer."""
    now = _now()
    with _Locked(path):
        state = _prune(_load(path), now)
        for r in state["requests"]:
            if r.get("request_id") == request_id and r["status"] == "OPEN":
                r["status"] = "RESOLVED"
                r["resolution"] = str(resolution)[:400]
                r["resolved_at_epoch"] = now
                r["resolved_at_utc"] = _iso(now)
                r["scope_expires_at_epoch"] = now + answer_reuse_s
                _save(state, path)
                return {
                    "resolved": True,
                    "request_id": request_id,
                    "consumers": r.get("consumers", []),
                    "scope_expires_at_utc": _iso(now + answer_reuse_s),
                }
        return {"resolved": False, "reason": "REQUEST_NOT_FOUND_OR_NOT_OPEN"}


def close_request(
    request_id: str,
    reason: str = "DECISION_NO_LONGER_DEPENDS_ON_HUMAN_INPUT",
    path: str = STATE_PATH,
) -> dict[str, Any]:
    """Decision expired or no longer depends on human input → close, no ask."""
    now = _now()
    with _Locked(path):
        state = _prune(_load(path), now)
        for r in state["requests"]:
            if r.get("request_id") == request_id and r["status"] == "OPEN":
                r["status"] = "CLOSED"
                r["closed_reason"] = str(reason)[:200]
                r["closed_at_utc"] = _iso(now)
                r["scope_expires_at_epoch"] = now + 300
                _save(state, path)
                return {"closed": True, "request_id": request_id}
        return {"closed": False, "reason": "REQUEST_NOT_FOUND_OR_NOT_OPEN"}


def set_mode(
    mode: str,
    scope: str = "current work session",
    ttl_s: int = 8 * 3600,
    source: str = "SELF_REPORT",
    path: str = STATE_PATH,
) -> dict[str, Any]:
    """Bounded human mode: expiring, revisable, non-diagnostic, subordinate.

    A later set_mode replaces earlier ones for overlapping scopes (newest
    explicit human instruction wins). Never stored as identity; never used
    for diagnosis; never overrides newer explicit human instructions.
    """
    mode_u = str(mode).upper()
    if mode_u not in MODES:
        return {"set": False, "reason": f"INVALID_MODE (valid: {', '.join(MODES)})"}
    now = _now()
    with _Locked(path):
        state = _prune(_load(path), now)
        state["modes"].append(
            {
                "mode": mode_u,
                "scope": scope,
                "source": source,
                "set_at_epoch": now,
                "set_at_utc": _iso(now),
                "expires_at_epoch": now + ttl_s,
                "expires_at_utc": _iso(now + ttl_s),
            }
        )
        _save(state, path)
        return {"set": True, "mode": mode_u, "expires_at_utc": _iso(now + ttl_s)}


def get_mode(path: str = STATE_PATH) -> dict[str, Any]:
    with _Locked(path):
        state = _prune(_load(path))
        mode = _active_mode(state)
        return {"mode": (mode or {}).get("mode", "NORMAL"), "detail": mode}


def explain(path: str = STATE_PATH) -> dict[str, Any]:
    """Bounded diagnostic (Phase 6): gate state ONLY.

    Contains no self-report content, no health claim, no human-state
    inference — request ids, decisions, suppression reasons, prompt counts.
    """
    with _Locked(path):
        state = _prune(_load(path))
    now = _now()
    open_reqs = [r for r in state["requests"] if r["status"] == "OPEN"]
    return {
        "schema": SCHEMA,
        "subject": SUBJECT_ID,
        "well_input_required": bool(open_reqs),
        "open_requests": [
            {
                "request_id": r["request_id"],
                "decision_object": r["decision_object"],
                "input_class": r["input_class"],
                "scope": r["scope"],
                "opened_by": r["opened_by"],
                "consumers": r.get("consumers", []),
                "prompt_count": r.get("prompt_count", 1),
                "opened_at_utc": r["opened_at_utc"],
            }
            for r in open_reqs
        ],
        "recent_resolved": [
            {
                "request_id": r["request_id"],
                "decision_object": r["decision_object"],
                "scope_expires_at_utc": _iso(r.get("scope_expires_at_epoch", 0)),
            }
            for r in state["requests"]
            if r["status"] == "RESOLVED" and r.get("scope_expires_at_epoch", 0) > now
        ],
        "active_mode": (state["modes"] or [{}])[-1].get("mode", "NORMAL"),
        "privacy": "gate state only — no human-state content is stored or returned",
    }


def main(argv: list[str] | None = None) -> int:  # pragma: no cover — CLI sugar
    import sys

    args = sys.argv[1:] if argv is None else argv
    if not args or args[0] in ("explain", "--explain"):
        print(json.dumps(explain(), indent=1))
        return 0
    if args[0] == "check":
        d = args[1] if len(args) > 1 else None
        print(json.dumps(check(decision_object=d), indent=1))
        return 0
    print("usage: ask_gate.py [explain|check <decision_object>]")
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
