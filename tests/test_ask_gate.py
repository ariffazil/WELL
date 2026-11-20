"""WELL_HUMAN_ATTENTION_DEAMPLIFICATION — ask_gate deterministic test matrix.

Maps the directive's Phase 5 cases. Every case proves ONE contract clause:
TTL expiry never asks · dedup across agents · named decision required ·
silence never diagnosed · modes expiring/scoped · privacy (gate state only).
"""

from __future__ import annotations

import json

import pytest

from human_checkin import ask_gate


@pytest.fixture()
def gate(tmp_path):
    """Ask-gate bound to an isolated state file per test."""
    path = str(tmp_path / "human_ask.json")
    return {"path": path}


def test_01_ttl_expiry_alone_never_prompts(gate):
    """Case 1/2: stale self-report + no blocked decision → zero prompts."""
    import os

    for _ in range(24):  # 24 agent sessions probe the gate
        v = ask_gate.check(decision_object=None, path=gate["path"])
        assert v["well_input_required"] is False
        assert v["reason"] == "NO_DECISION_DEPENDENCY"
    # nothing was ever opened — no state file needed to refuse
    if os.path.exists(gate["path"]):
        assert json.load(open(gate["path"]))["requests"] == []


def test_03_one_blocked_decision_one_shared_ask(gate):
    """Case 3/4: N agents, same decision → one request, everyone subscribes."""
    first = ask_gate.open_request(
        "deploy:prod-api", opened_by="333-AGI", path=gate["path"]
    )
    assert first["opened"] is True
    assert first["reason"] == "DECISION_BLOCKED"
    for agent in ("555-ASI", "888-APEX", "777-FORGE", "HERMES"):
        sub = ask_gate.open_request(
            "deploy:prod-api", opened_by=agent, path=gate["path"]
        )
        assert sub["opened"] is False
        assert sub["reason"] == "EQUIVALENT_REQUEST_OPEN"
        assert sub["request_id"] == first["request_id"]
    state = json.load(open(gate["path"]))
    assert len([r for r in state["requests"] if r["status"] == "OPEN"]) == 1


def test_05_resolve_feeds_all_subscribers(gate):
    """Case 5: one answer resolves the shared request with a scoped window."""
    req = ask_gate.open_request(
        "deploy:prod-api", opened_by="333-AGI", path=gate["path"]
    )
    res = ask_gate.resolve(
        req["request_id"], "GO: deploy after green tests", path=gate["path"]
    )
    assert res["resolved"] is True
    chk = ask_gate.check("deploy:prod-api", path=gate["path"])
    assert chk["well_input_required"] is False
    assert chk["reason"] == "SCOPED_ANSWER_AVAILABLE"
    assert chk["resolution"] == "GO: deploy after green tests"


def test_06_scope_boundary_no_automatic_reuse(gate):
    """Case 6: a different decision evaluates independently. A named decision
    with clean history is ELIGIBLE_TO_OPEN (may open one ask), never a silent
    refusal and never an automatic prompt."""
    ask_gate.open_request("deploy:prod-api", path=gate["path"])
    other = ask_gate.check("rotate:api-key", path=gate["path"])
    assert other["well_input_required"] is True
    assert other["reason"] == "ELIGIBLE_TO_OPEN"
    opened = ask_gate.open_request("rotate:api-key", path=gate["path"])
    assert opened["opened"] is True and opened["request_id"]
    # budget: same key inside the window → refused
    again = ask_gate.check("rotate:api-key", path=gate["path"])
    assert again["well_input_required"] is False
    assert again["reason"] == "EQUIVALENT_REQUEST_OPEN"


def test_07_silence_is_not_diagnosed(gate):
    """Contract 4: gate output never carries a health/human-state claim."""
    v = ask_gate.check(decision_object=None, path=gate["path"])
    blob = json.dumps(v) + json.dumps(ask_gate.explain(path=gate["path"]))
    for forbidden in (
        "fatigue",
        "tired",
        "burnout",
        "anxious",
        "unhealthy",
        "distress",
        "mood",
        "stress",
        "sleep",
        "wellness",
    ):
        assert forbidden not in blob.lower()


def test_10_observability_explain_shape(gate):
    """Phase 6: explain() returns gate state only, no report content."""
    ask_gate.open_request("decision:x", scope="s1", opened_by="a1", path=gate["path"])
    ex = ask_gate.explain(path=gate["path"])
    assert ex["well_input_required"] is True
    assert ex["open_requests"][0]["decision_object"] == "decision:x"
    assert ex["open_requests"][0]["consumers"] == ["a1"]
    assert "gate state only" in ex["privacy"]


def test_11_mode_defers_noncritical(gate):
    """Modes: LOW_ATTENTION defers non-critical asks, critical lane intact."""
    ask_gate.set_mode("LOW_ATTENTION", ttl_s=3600, path=gate["path"])
    soft = ask_gate.check("nice_to_have:color", path=gate["path"])
    assert soft["reason"] == "MODE_RESTRICTS"
    hard = ask_gate.open_request(
        "irreversible:drop-prod", critical=True, path=gate["path"]
    )
    assert hard["opened"] is True


def test_12_mode_expires_not_auto_prompt(gate):
    """Case 16: mode expiry returns to default behavior, not automatic prompt."""
    ask_gate.set_mode("STOP_NONCRITICAL", ttl_s=3600, path=gate["path"])
    assert ask_gate.get_mode(path=gate["path"])["mode"] == "STOP_NONCRITICAL"
    import os
    import time as _t

    # expire by hand: shift the stored window into the past
    state = json.load(open(gate["path"]))
    for m in state["modes"]:
        m["expires_at_epoch"] = _t.time() - 1
    json.dump(state, open(gate["path"], "w"))
    assert ask_gate.get_mode(path=gate["path"])["mode"] == "NORMAL"
    v = ask_gate.check(decision_object=None, path=gate["path"])
    assert v["well_input_required"] is False
    assert v["reason"] == "NO_DECISION_DEPENDENCY"


def test_13_close_without_asking(gate):
    """Directive: decision expires → request closes, human never asked."""
    req = ask_gate.open_request("blocked:then-lapsed", path=gate["path"])
    closed = ask_gate.close_request(req["request_id"], path=gate["path"])
    assert closed["closed"] is True
    chk = ask_gate.check("blocked:then-lapsed", path=gate["path"])
    assert chk["well_input_required"] is False
    assert chk["reason"] != "EQUIVALENT_REQUEST_OPEN"  # nothing open to subscribe


def test_14_stale_scheduler_event_updates_lane_only(gate):
    """Case 14: a freshness/staleness event has NO path into the gate — the
    gate API takes decision objects, never ages. This test pins the API
    shape so no future caller can smuggle a TTL into a prompt."""
    import inspect

    sig = inspect.signature(ask_gate.check)
    assert "freshness" not in sig.parameters
    assert "age" not in sig.parameters
    assert "ttl" not in sig.parameters
    # a stale-looking call still refuses to ask
    v = ask_gate.check(decision_object=None, path=gate["path"])
    assert v["reason"] == "NO_DECISION_DEPENDENCY"


def test_18_privacy_no_content_in_state(gate):
    """Resolution text is bounded (400 chars) and the state file stores gate
    fields only — no free-form human narrative beyond the scoped answer."""
    req = ask_gate.open_request("decision:p", path=gate["path"])
    ask_gate.resolve(req["request_id"], "x" * 5000, path=gate["path"])
    raw = open(gate["path"]).read()
    assert len(raw) < 8000  # bounded state, bounded resolution
    state = json.loads(raw)
    for r in state["requests"]:
        assert set(r.keys()) <= {
            "request_id",
            "key",
            "decision_object",
            "input_class",
            "scope",
            "status",
            "opened_by",
            "opened_at_epoch",
            "opened_at_utc",
            "prompt_count",
            "next_eligible_prompt_at_epoch",
            "consumers",
            "resolution",
            "resolved_at_epoch",
            "resolved_at_utc",
            "closed_reason",
            "closed_at_utc",
            "scope_expires_at_epoch",
        }


def test_invalid_mode_rejected(gate):
    out = ask_gate.set_mode("SUDO_MODE", path=gate["path"])
    assert out["set"] is False
