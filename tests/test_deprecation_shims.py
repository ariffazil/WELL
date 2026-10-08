"""P0-3 — the registry reports its own migration window, and past-due names
answer with the migration signal instead of "Unknown tool" (2026-09-28).

Two measured defects this file pins closed:

  3b  DEPRECATED_TOOLS_MAP listed 6 names with removal_date 2026-09-01, but every
      handler was unregistered 2026-08-04. Live probe 2026-09-28:
      well_readiness -> isError True "Unknown tool: 'well_readiness'".
      The map's comment says its purpose is a migration signal; nothing registered
      could ever fire it. The shims fire it, and nothing else -- no delegation to a
      legacy body, no writes.

  3a  well_registry_status said REGISTRY_DRIFT about 10 intended vs 40 registered,
      while well_reality and the v2 mutation guide both date that exact state as a
      scheduled window (epoch 2026-09-16 -> removal 2026-10-16). A plan read as a
      fault is a false alarm on the sovereign's own surface.

Run:
  cd /root/WELL && PYTHONPATH=. .venv/bin/python -m pytest \
      tests/test_deprecation_shims.py -q
"""

from __future__ import annotations

import asyncio
import datetime as _dt
import json
import sys
from pathlib import Path

import pytest

WELL_ROOT = Path(__file__).resolve().parents[1]
if str(WELL_ROOT) not in sys.path:
    sys.path.insert(0, str(WELL_ROOT))

import server  # noqa: E402

SESSION_ID = "P03-test-session"
DEPRECATED_NAMES = sorted(server.DEPRECATED_TOOLS_MAP)


def _payload(result) -> dict:
    """Dig the tool's JSON out of a FastMCP call result, text or structured."""
    sc = getattr(result, "structured_content", None)
    if isinstance(sc, dict):
        return sc.get("result", sc) if "result" in sc else sc
    content = getattr(result, "content", None) or []
    if content and hasattr(content[0], "text"):
        return json.loads(content[0].text)
    raise AssertionError(f"unparsable tool result: {result!r}")


@pytest.fixture(autouse=True)
def isolate_live_telemetry_sink(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """These tests dispatch for real, so the invocation receipt writes for real.

    Without the redirect every shim call lands in the federation's production
    metrics file (measured: 46 rows did exactly that on 2026-09-28 before this
    fixture existed). Same convention as tests/test_invocation_telemetry.py.
    """
    monkeypatch.setenv(
        server.WELL_INVOCATION_SINK_ENV, str(tmp_path / "tool_invocations.jsonl")
    )


@pytest.fixture(scope="module")
def listed_tool_names() -> list[str]:
    """tools/list exactly as the running server answers it (public surface only)."""
    server._enforce_somatic_boundary(server.mcp)  # no-op if the boundary is already on
    return [t.name for t in asyncio.run(server.mcp.list_tools())]


# ── 3b: past-due names return the migration signal ───────────────────────────


@pytest.mark.parametrize("name", DEPRECATED_NAMES)
def test_deprecated_name_returns_migration_signal(name: str) -> None:
    """No more bare "Unknown tool": the caller is told where the name went."""
    result = asyncio.run(
        server.mcp.call_tool(name, {"session_id": SESSION_ID, "actor_id": "arif"})
    )
    body = _payload(result)
    assert body["error"] == "DEPRECATED_MOVED", body
    assert body["ok"] is False
    assert body["tool"] == name
    # The whole point of the signal: it names where the caller must go.
    assert body["replacement"], body
    assert isinstance(body["replacement_args"], dict)
    assert body["deprecation_epoch"] and body["removal_date"]
    assert isinstance(body["overdue_days"], int) and body["overdue_days"] >= 0
    assert "migrate" in body["signal"].lower()


@pytest.mark.parametrize("name", DEPRECATED_NAMES)
def test_deprecated_name_is_still_absent_from_the_public_surface(name: str, listed_tool_names) -> None:
    """Callable is not discoverable. tools/list must never grow these names."""
    assert name not in listed_tool_names
    assert name not in server.SOMATIC_TOOLS


def test_public_surface_is_unchanged_by_the_shims(listed_tool_names) -> None:
    """Surface stable before and after -- the shims are registered, not exported.

    Count is 10 since the P0 Surface Integrity Release (7a145bf, 2026-10-03)
    contracted the public surface from 40 to the 10 intended tools. The shim
    layer must not move that number either direction."""
    assert len(listed_tool_names) == len(server.SOMATIC_TOOLS) == 10, sorted(
        set(listed_tool_names) ^ set(server.SOMATIC_TOOLS)
    )


def test_shim_body_is_thin_and_delegates_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    """The shim computes a payload and stops there -- no legacy body, no writes."""
    touched = {"n": 0}

    def _legacy_spy(*a, **kw):
        touched["n"] += 1
        raise AssertionError("a deprecation shim must not run the legacy handler")

    for name in DEPRECATED_NAMES:
        monkeypatch.setattr(server, name, _legacy_spy, raising=False)

    for name in DEPRECATED_NAMES:
        shim = server._make_deprecation_shim(name)
        assert shim() == server._well_deprecation_payload(name)
    assert touched["n"] == 0


def test_shim_accepts_the_shape_a_legacy_caller_still_sends() -> None:
    """A not-yet-migrated caller gets the signal, not a schema rejection.

    `detail` was well_readiness' own parameter; actor_id/_envelope arrive from the
    federation bridge. The mirrored schema must swallow all three.
    """
    result = asyncio.run(
        server.mcp.call_tool(
            "well_readiness",
            {
                "session_id": SESSION_ID,
                "detail": "full",
                "actor_id": "arif",
                "_envelope": {"actor_id": "hermes-asi"},
            },
        )
    )
    assert _payload(result)["error"] == "DEPRECATED_MOVED"


def test_shims_are_not_a_catch_all() -> None:
    """Only the six mapped names resolve; an invented name must still be unknown.

    The falsification test: if the shim path swallowed every unregistered name,
    DEPRECATED_MOVED would stop meaning "this moved" and start meaning "anything
    goes" -- and the map would no longer be evidence of anything.
    """
    from fastmcp.exceptions import NotFoundError

    with pytest.raises(NotFoundError, match="Unknown tool"):
        asyncio.run(
            server.mcp.call_tool(
                "well_name_that_never_existed", {"session_id": SESSION_ID}
            )
        )


def test_deprecated_payload_is_the_documented_shape() -> None:
    """The exact keys the brief specifies -- no legacy body fields leak in."""
    body = server._well_deprecation_payload("well_readiness")
    assert set(body) == {
        "ok",
        "error",
        "tool",
        "replacement",
        "replacement_args",
        "deprecation_epoch",
        "removal_date",
        "overdue_days",
        "signal",
    }
    # A real legacy well_readiness run emits these; a shim must not.
    for legacy_key in ("readiness_envelope", "vitality_gate", "color", "domain_verdict"):
        assert legacy_key not in body


def test_overdue_days_tracks_the_removal_date() -> None:
    """2026-09-01 is past due; a future date is not. Never a negative count."""
    assert server._well_overdue_days("2026-09-01") == (
        _dt.datetime.now(_dt.timezone.utc).date() - _dt.date(2026, 9, 1)
    ).days
    assert server._well_overdue_days("2999-01-01") == 0
    assert server._well_overdue_days("not-a-date") == 0


# ── 3a: the registry names its own migration window ──────────────────────────


def test_registry_reports_the_v2_migration_window() -> None:
    """The 10-vs-40 gap is a dated window, and the registry must say so."""
    status = server.well_registry_status(mode="status", session_id=SESSION_ID)
    mig = status["migration"]

    # One source of truth: the same epoch well_reality reports, not a copy.
    from well_v2.surface import _DEPRECATION

    assert mig["epoch"] == _DEPRECATION["epoch"] == "2026-09-16"
    assert mig["removal_date"] == _DEPRECATION["removal"] == "2026-10-16"

    today = _dt.datetime.now(_dt.timezone.utc).date()
    assert mig["in_migration_window"] is (_dt.date(2026, 9, 16) <= today <= _dt.date(2026, 10, 16))
    assert mig["days_to_removal"] == (_dt.date(2026, 10, 16) - today).days
    assert mig["target_surface"] == 10
    # P0 Surface Integrity Release (7a145bf, 2026-10-03) closed the 10-vs-40 gap
    # early: the legacy tools were unregistered ahead of the 2026-10-16 removal date.
    assert mig["current_public_surface"] == 10
    assert mig["legacy_still_registered"] is False

    # Inside the window the label is the truth: a plan in flight, not drift.
    if mig["in_migration_window"]:
        assert status["verdict"] != "REGISTRY_DRIFT"


def test_registry_counts_are_unchanged_by_the_window() -> None:
    """Only the verdict label may move. Every raw count stays as measured."""
    status = server.well_registry_status(mode="status", session_id=SESSION_ID)
    assert status["intended_tools"] == 10
    assert status["registered_tools"] == 10
    for key in ("exported_tools", "callable_tools", "phantom_tools_count",
                "missing_public_tools_count", "unexpected_public_tools_count",
                "alias_conflicts_count", "verdict"):
        assert key in status, key


def test_full_mode_also_carries_the_window() -> None:
    full = server.well_registry_status(mode="full", session_id=SESSION_ID)
    assert "migration" in full
    assert full["migration"]["removal_date"] == "2026-10-16"
    # existing keys preserved for agents that parse the full blueprint payload
    for key in ("somatic_tools", "exported_surface", "canonical_callable",
                "phantom_tools", "legacy_alias_map", "public_canonical_surface"):
        assert key in full, key
