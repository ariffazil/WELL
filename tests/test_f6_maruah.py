"""
F6 MARUAH instrument v0 — regression tests
═══════════════════════════════════════════
Covers the honest contract: null-unless-covered, contamination block,
stale block, envelope shape, and the cutover guard (the tool stays
modular-target-only until H1 parity — production server.py must never
reference it, per the WELL-A4-FIX byte-identity scar).

Self-contained: no HTTP server, no live organ calls.
"""

import json
import time

import pytest

from well_mcp.tools.f6_maruah import well_measure_floor_f6

NOW = 1_800_000_000.0  # fixed epoch for determinism


def _write_state(tmp_path, truth="OPERATOR_VERBAL", age_s=600.0, contaminated=False):
    state = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(NOW - age_s)),
        "truth_status": truth,
        "test_contamination": contaminated,
        "environment": "TEST" if contaminated else "PROD",
    }
    p = tmp_path / "state.json"
    p.write_text(json.dumps(state))
    return str(p)


def _write_intake_log(tmp_path, age_s=120.0, status="NO_INTAKE"):
    p = tmp_path / "intake.log"
    line = json.dumps(
        {
            "tool": "well_ingest",
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(NOW - age_s)),
            "status": status,
            "state_path": "/var/lib/well/state.json",
        }
    )
    p.write_text(line + "\n")
    return str(p)


@pytest.mark.asyncio
async def test_insufficient_returns_null(tmp_path):
    res = await well_measure_floor_f6(
        state_path=str(tmp_path / "missing.json"),
        intake_log=str(tmp_path / "missing.log"),
        server_py="/nonexistent/server.py",
        now=NOW,
    )
    assert res["f6_index"] is None
    assert res["verdict"] == "INSTRUMENTED_COVERAGE_INSUFFICIENT"
    assert len(res["null_reasons"]) == 3


@pytest.mark.asyncio
async def test_covered_returns_partial(tmp_path):
    sp = _write_state(tmp_path)
    ip = _write_intake_log(tmp_path)
    server = tmp_path / "server.py"
    server.write_text("async def well_guard_dignity(): ...\n")
    res = await well_measure_floor_f6(
        state_path=sp,
        intake_log=ip,
        server_py=str(server),
        now=NOW,
    )
    assert res["verdict"] == "MEASURED_V0_PARTIAL"
    assert res["f6_index"] is not None
    assert 0.5 < res["f6_index"] <= 1.0
    assert res["null_reasons"] == []


@pytest.mark.asyncio
async def test_contaminated_state_blocks(tmp_path):
    sp = _write_state(tmp_path, contaminated=True)
    ip = _write_intake_log(tmp_path)
    res = await well_measure_floor_f6(state_path=sp, intake_log=ip, now=NOW)
    assert res["f6_index"] is None
    assert any("human_substrate" in r for r in res["null_reasons"])


@pytest.mark.asyncio
async def test_stale_state_blocks(tmp_path):
    sp = _write_state(tmp_path, age_s=5 * 3600)  # > STATE_MAX_AGE_S (4h)
    ip = _write_intake_log(tmp_path)
    res = await well_measure_floor_f6(state_path=sp, intake_log=ip, now=NOW)
    assert res["f6_index"] is None
    assert any("human_substrate" in r for r in res["null_reasons"])


@pytest.mark.asyncio
async def test_envelope_shape():
    res = await well_measure_floor_f6(now=NOW)
    for key in (
        "floor",
        "name",
        "instrument",
        "version",
        "authority",
        "f6_index",
        "verdict",
        "null_reasons",
        "coverage",
        "kernel_wiring",
        "cutover",
        "generated_utc",
    ):
        assert key in res, f"missing envelope key: {key}"
    assert res["floor"] == "F6"
    assert res["authority"] == "REFLECT_ONLY"
    assert res["kernel_wiring"].startswith("pending OS-1")


def test_cutover_guard_production_server_must_not_reference():
    """A4 scar guard: the F6 instrument stays modular-target-only until H1
    cutover green. The production monolith (server.py) must never gain a
    reference to it — that would create a dual surface (byte-identity)."""
    from pathlib import Path

    prod = Path(__file__).resolve().parents[1] / "server.py"
    assert "well_measure_floor_f6" not in prod.read_text(errors="replace")
