from __future__ import annotations

from server import well_health_check, well_registry_status


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
