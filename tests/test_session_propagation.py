from __future__ import annotations

from server import _check_dependencies, well_health_check, well_registry_status


def test_well_health_echoes_federation_context() -> None:
    result = well_health_check(
        include_federation=False,
        session_id="SEAL-session-echo",
        actor_id="arif",
        trace_id="trace-echo",
    )
    assert result["session_id"] == "SEAL-session-echo"
    assert result["actor_id"] == "arif"
    assert result["trace_id"] == "trace-echo"
    assert isinstance(result["dependencies_ok"], bool)
    assert "federation_geometry" in result


def test_well_registry_echoes_federation_context() -> None:
    result = well_registry_status(
        mode="status",
        session_id="SEAL-session-echo",
        actor_id="arif",
        trace_id="trace-echo",
    )
    assert result["session_id"] == "SEAL-session-echo"
    assert result["actor_id"] == "arif"
    assert result["trace_id"] == "trace-echo"


def test_canonical_state_schema_satisfies_dependency_probe() -> None:
    import server as _server

    # The autouse isolation fixture points STATE_PATH at a tmp file that is
    # only seeded when a production state.json exists (it does not on a clean
    # checkout). An absent state file is a data condition, not a broken
    # dependency, so seed the isolated path before probing.
    if not _server.STATE_PATH.exists():
        _server.STATE_PATH.write_text("{}", encoding="utf-8")

    dependencies = _check_dependencies()
    assert dependencies["schema_readable"] is True
    assert dependencies["all_ok"] is True
