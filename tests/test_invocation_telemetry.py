"""Tuas 2 — WELL invocation telemetry wiring test (2026-09-19).

Proves IN-PROCESS, against the real dispatch chokepoint
(``server.mcp.call_tool`` -> ``_governance_call_tool``):

  1. one receipt lands per real invocation, organ="WELL", tool=<tool name>
  2. the actor is the CALLER from the federation envelope -- never the human
     subject that WELL's own ``actor_id`` argument names
  3. no envelope -> actor_id=None: honest absence, not an invented label
  4. a forced logger failure does NOT break the call
  5. a governance-blocked call is receipted ok=False with a fixed error class

BOUNDARY (F4): these tests assert the log carries the tool name and the caller
identity and NOTHING else -- no arguments, no intake content, no biometrics,
no human state. That is a correctness requirement, not style.

Run:
  cd /root/WELL && PYTHONPATH=. /root/WELL/.venv/bin/python -m pytest \
      tests/test_invocation_telemetry.py -q
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest

WELL_ROOT = Path(__file__).resolve().parents[1]
if str(WELL_ROOT) not in sys.path:
    sys.path.insert(0, str(WELL_ROOT))

import server  # noqa: E402  -- the live dispatch module under test


def _shared_contract_available() -> bool:
    """The telemetry contract lives in the private AAA repo (/root/AAA/lib).

    A clean CI runner has neither the sibling checkout nor a cross-repo token,
    so this integration test cannot run there. It runs wherever AAA_LIB (or the
    VPS layout) provides the module; skip with an explicit reason otherwise.
    """
    try:
        return server._well_invocation_logger() is not None
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _shared_contract_available(),
    reason="requires shared AAA/lib invocation_log (private cross-repo contract not provisioned on this runner)",
)

TEST_TOOL = "well_test_telemetry_ping"
# WELL's session-validation middleware requires a non-empty session_id on every
# non-exempt tool call; it is transport metadata, never written to telemetry.
SESSION_ID = "TUAS2-test-session"

# Exactly the keys the frozen shared contract writes. If a future edit starts
# logging payload/arguments, this set grows and the boundary test below fails.
CONTRACT_KEYS = {
    "ts",
    "organ",
    "tool",
    "actor_id",
    "ok",
    "duration_ms",
    "session_id",
    "epoch",
    "host",
}


def _read_receipts(sink: Path) -> list[dict]:
    if not sink.exists():
        return []
    out = []
    for line in sink.read_text().splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


@pytest.fixture()
def sink(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Redirect receipts to a tmp sink -- live federation telemetry untouched."""
    p = tmp_path / "tool_invocations.jsonl"
    monkeypatch.setenv(server.WELL_INVOCATION_SINK_ENV, str(p))
    return p


@pytest.fixture()
def dispatch_tool():
    """Register a real FastMCP tool so the wrapper's SUCCESS path is exercised.

    ``_envelope`` and ``actor_id`` are declared parameters so the call passes
    FastMCP's own schema validation; ``actor_id`` here stands in for WELL's
    human-subject argument and must NOT be picked up as the caller.
    """

    @server.mcp.tool(name=TEST_TOOL)
    def _telemetry_ping(
        _envelope: dict | None = None,
        actor_id: str | None = None,
        note: str | None = None,
    ) -> dict:
        return {"ok": True, "tool": TEST_TOOL}

    try:
        yield TEST_TOOL
    finally:
        # pytest-asyncio is not installed in this venv, so tests below drive the
        # async wrapper with asyncio.run (repo convention: see tests/test_well.py).
        try:
            server.mcp.local_provider.remove_tool(TEST_TOOL)
        except Exception:
            try:
                server.mcp.remove_tool(TEST_TOOL)
            except Exception:
                pass


def test_dispatch_chokepoint_is_instrumented() -> None:
    """The telemetry hangs off the real wrapper, not a copy of it."""
    assert server.mcp.call_tool.__name__ == "_governance_call_tool"
    assert callable(server._well_log_invocation)
    assert callable(server._well_resolve_caller_actor)
    assert server._WELL_INVOCATION_ORGAN == "WELL"


def test_receipt_lands_with_caller_identity(sink, dispatch_tool) -> None:
    """Success path: a receipt lands carrying caller identity + tool name only."""
    asyncio.run(
        server.mcp.call_tool(
            TEST_TOOL,
            {
                "_envelope": {"actor_id": "hermes-asi"},
                "actor_id": "arif",
                "session_id": SESSION_ID,
            },
        )
    )
    recs = _read_receipts(sink)
    assert len(recs) == 1, recs
    rec = recs[0]
    assert rec["organ"] == "WELL"
    assert rec["tool"] == TEST_TOOL
    # Caller identity from the envelope -- NOT the human-subject actor_id arg.
    assert rec["actor_id"] == "hermes-asi"
    assert rec["ok"] is True
    assert isinstance(rec["duration_ms"], (int, float))


def test_receipt_carries_no_content(sink, dispatch_tool) -> None:
    """Boundary: no arguments, no payload, no person -- keys are the contract's."""
    asyncio.run(
        server.mcp.call_tool(
            TEST_TOOL,
            {
                "_envelope": {"actor_id": "aaa-auditor"},
                "actor_id": "arif",
                "session_id": SESSION_ID,
                # A person-shaped value that must never reach the telemetry line.
                "note": "biometric 999",
            },
        )
    )
    recs = _read_receipts(sink)
    assert len(recs) == 1, recs
    rec = recs[0]
    assert set(rec) <= CONTRACT_KEYS, sorted(set(rec) - CONTRACT_KEYS)
    assert "arif" not in json.dumps(rec)
    assert "biometric" not in json.dumps(rec)
    # Content marker asserted as the FULL planted value — a bare "999" substring
    # check collides with random hex ids/hashes in receipt fields (flaky-by-design;
    # this failed CI 2026-10-18 with zero content leakage).
    assert "biometric 999" not in json.dumps(rec)


def test_no_envelope_records_honest_absence(sink, dispatch_tool) -> None:
    """No caller envelope -> actor_id=None. Absence, never an invented label."""
    asyncio.run(
        server.mcp.call_tool(TEST_TOOL, {"actor_id": "arif", "session_id": SESSION_ID})
    )
    recs = _read_receipts(sink)
    assert len(recs) == 1, recs
    assert recs[0]["actor_id"] is None
    assert recs[0]["tool"] == TEST_TOOL
    # Caller identity and session are independent: not knowing the caller says
    # nothing about the session, which the transport did supply.
    assert recs[0]["session_id"] == SESSION_ID


# ── P0-1 (2026-09-28): the session behind the call ───────────────────────────


def test_receipt_names_the_session_that_called(sink, dispatch_tool) -> None:
    """P0-1: the receipt carries the MCP session of the request that caused it.

    Before this, `session_id` was null on 0 of 447 live WELL records even though
    the middleware reads it from the transport -- receipts could not be joined to
    a session, so a burst of calls from one session was indistinguishable from
    forty sessions.
    """
    asyncio.run(
        server.mcp.call_tool(
            TEST_TOOL,
            {"_envelope": {"actor_id": "hermes-asi"}, "session_id": SESSION_ID},
        )
    )
    recs = _read_receipts(sink)
    assert len(recs) == 1, recs
    assert recs[0]["session_id"] == SESSION_ID
    assert recs[0]["actor_id"] == "hermes-asi"
    assert recs[0]["ok"] is True


def test_session_context_is_replaced_not_inherited(sink, dispatch_tool) -> None:
    """A previous request's session must never leak into the next receipt."""
    server._WELL_TELEMETRY_SESSION.set("SESSION-OF-A-PREVIOUS-REQUEST")
    asyncio.run(
        server.mcp.call_tool(TEST_TOOL, {"session_id": SESSION_ID})
    )
    recs = _read_receipts(sink)
    assert len(recs) == 1, recs
    assert recs[0]["session_id"] == SESSION_ID
    assert "PREVIOUS" not in json.dumps(recs[0])
    server._WELL_TELEMETRY_SESSION.set(None)


def test_receipt_uses_the_transport_header_when_no_argument_is_passed(
    sink, dispatch_tool, monkeypatch: pytest.MonkeyPatch
) -> None:
    """P0-1 on the production path: the session arrives as an HTTP header.

    Stateless/streamable-HTTP clients never pass session_id as an argument -- the
    middleware reads it off `mcp-session-id`. Only the ASGI request object is
    stubbed here; the resolver, the middleware and the dispatch wrapper all run
    for real, so this exercises the header branch end to end.
    """
    from starlette.requests import Request

    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "POST",
        "path": "/mcp",
        "raw_path": b"/mcp",
        "query_string": b"",
        "scheme": "http",
        "headers": [(b"mcp-session-id", b"HEADER-SESSION-42")],
        "client": ("127.0.0.1", 55555),
        "server": ("testserver", 80),
        "root_path": "",
    }

    monkeypatch.setattr(
        "fastmcp.server.dependencies.get_http_request",
        lambda: Request(scope),
    )
    asyncio.run(
        server.mcp.call_tool(TEST_TOOL, {"_envelope": {"actor_id": "hermes-asi"}})
    )
    recs = _read_receipts(sink)
    assert len(recs) == 1, recs
    assert recs[0]["session_id"] == "HEADER-SESSION-42"


def test_no_session_known_records_null_not_an_invention(sink) -> None:
    """Nothing resolved -> session_id null. Never a hostname, never 'well'."""
    server._WELL_TELEMETRY_SESSION.set(None)
    server._well_log_invocation("well_test_no_session_at_all", None, ok=True)
    recs = _read_receipts(sink)
    assert len(recs) == 1, recs
    assert recs[0]["session_id"] is None
    assert recs[0]["actor_id"] is None


def test_session_id_is_resolved_only_from_known_sources() -> None:
    """The resolver reads arguments/header/context -- and invents nothing."""
    server._WELL_TELEMETRY_SESSION.set(None)
    assert server._well_resolve_session_id({"session_id": "  "}, inherit=False) is None
    assert server._well_resolve_session_id({}, inherit=False) is None
    assert (
        server._well_resolve_session_id({"session_id": " real "}, inherit=False)
        == "real"
    )
    server._WELL_TELEMETRY_SESSION.set("ambient-session")
    assert server._well_resolve_session_id({}, inherit=True) == "ambient-session"
    # inherit=False is the top-level reset path: ambient must not win there.
    assert server._well_resolve_session_id({}, inherit=False) is None
    server._WELL_TELEMETRY_SESSION.set(None)


def test_receipt_still_carries_no_content_with_session(sink, dispatch_tool) -> None:
    """P0-1 adds one join key and nothing else -- the F4 boundary still holds."""
    asyncio.run(
        server.mcp.call_tool(
            TEST_TOOL,
            {
                "_envelope": {"actor_id": "aaa-auditor"},
                "actor_id": "arif",
                "session_id": SESSION_ID,
                "note": "sleep 3h, biometric 999",
            },
        )
    )
    recs = _read_receipts(sink)
    assert len(recs) == 1, recs
    assert set(recs[0]) <= CONTRACT_KEYS, sorted(set(recs[0]) - CONTRACT_KEYS)
    assert "arif" not in json.dumps(recs[0])
    assert "biometric" not in json.dumps(recs[0])
    assert "sleep" not in json.dumps(recs[0])


def test_logger_failure_does_not_break_the_call(
    sink, dispatch_tool, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A broken instrument must never take down the tool call it measures."""

    calls = {"n": 0}

    class _ExplodingLogger:
        @staticmethod
        def log_invocation(*args, **kwargs):
            calls["n"] += 1
            raise RuntimeError("telemetry sink exploded")

    monkeypatch.setattr(server, "_well_invocation_logger", lambda: _ExplodingLogger)
    result = asyncio.run(
        server.mcp.call_tool(
            TEST_TOOL, {"_envelope": {"actor_id": "hermes-asi"}, "session_id": SESSION_ID}
        )
    )
    assert result is not None  # the call completed despite the logger blowing up
    assert calls["n"] == 1  # and the failing logger was genuinely invoked
    assert _read_receipts(sink) == []


def test_governance_block_is_receipted(
    sink, dispatch_tool, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A governance HOLD is receipted ok=False and still raises as before."""
    from fastmcp.exceptions import ToolError

    monkeypatch.setattr(
        server,
        "check_governance",
        lambda name, arguments: ("HOLD", {"error": "held"}),
    )
    with pytest.raises(ToolError):
        asyncio.run(
            server.mcp.call_tool(
                TEST_TOOL,
                {"_envelope": {"actor_id": "kimi-code/FI-008"}, "session_id": SESSION_ID},
            )
        )
    recs = _read_receipts(sink)
    assert len(recs) == 1, recs
    assert recs[0]["ok"] is False
    assert recs[0]["error"] == "GOVERNANCE_BLOCK"
    assert recs[0]["actor_id"] == "kimi-code/FI-008"


# ── well_triad/events.py: the hard-coded actor defect ────────────────────────


@pytest.fixture()
def captured_events(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    """Capture typed events without appending to the live ledger or the kernel."""
    from well_triad import events

    captured: list[dict] = []
    monkeypatch.setattr(events, "_native_append_event", captured.append)

    class _NoNet:
        def read(self):  # pragma: no cover - never called
            return b""

    # Never POST a test payload at the live arifOS kernel (:18081).
    monkeypatch.setattr(
        events.urllib.request, "urlopen", lambda *a, **kw: _NoNet()
    )
    return captured


def _triad_event(**overrides) -> dict:
    from well_triad import events

    kwargs = dict(
        event="WELL_TRIAD_TEST",
        phase=1,
        tool="well_test_telemetry_ping",
        plane="machine",
        inputs={"counter": 1},
        source="tests/test_invocation_telemetry.py",
        truth_class="INT",
        evidence_label="INT",
    )
    kwargs.update(overrides)
    events.append_typed_event(**kwargs)
    return kwargs


def test_triad_event_records_caller_not_constant(captured_events) -> None:
    """The actor is caller-derived; 'arif' is no longer asserted for everyone."""
    _triad_event(actor_id="hermes-asi")
    assert len(captured_events) == 1
    payload = captured_events[0]
    assert payload["actor_id"] == "hermes-asi"
    # Verification is never inferred from the presence of a name.
    assert payload["actor_verified"] is False


def test_triad_event_default_is_honest_absence(captured_events) -> None:
    """Existing callers (no actor kwarg) get None/False -- not a fake identity."""
    _triad_event()
    payload = captured_events[0]
    assert payload["actor_id"] is None
    assert payload["actor_verified"] is False


def test_triad_event_explicit_verified_requires_an_actor(captured_events) -> None:
    """actor_verified=True without an actor collapses to False, never a lie."""
    _triad_event(actor_verified=True)
    assert captured_events[0]["actor_verified"] is False

    _triad_event(actor_id="555-asi", actor_verified=True)
    assert captured_events[1]["actor_id"] == "555-asi"
    assert captured_events[1]["actor_verified"] is True
