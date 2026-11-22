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
from pathlib import Path

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


def _write_intake_log(tmp_path, age_s=120.0, status="MERGED"):
    """A REAL intake receipt by default.

    2026-11-23 (F13 GO B): the default used to be status="NO_INTAKE" — a cron
    HEARTBEAT — and the covered test asserted a real index from it. That was the
    defect in one line: the flow leg was covered by cron liveness, never by
    reality entering the substrate. Heartbeats are now excluded, so the fixture
    carries a real receipt, and the heartbeat case has its own test below.
    """
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


def _write_self_report_log(tmp_path, age_s=120.0):
    """A self-report receipt in the shape the SELF_REPORT lane actually writes."""
    p = tmp_path / "human_checkins.jsonl"
    rec = {
        "event_id": "fixture",
        "recorded_at_utc": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(NOW - age_s)),
        "observations": [
            {
                "measurement": "sleep_hours",
                "observed_at": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(NOW - age_s)),
                "provenance": "self_reported",
                "source": "telegram_checkin",
                "value": 7.0,
            }
        ],
    }
    p.write_text(json.dumps(rec) + "\n")
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
async def test_string_no_contamination_not_flagged(tmp_path):
    """Regression: live state carries test_contamination as the STRING "NO" —
    bool("NO") is truthy and falsely flagged contamination (caught on the
    first live reading 2026-11-18 00:51 MYT). Parse semantically."""
    sp = _write_state(tmp_path)
    state = json.loads(Path(sp).read_text())
    state["test_contamination"] = "NO"  # string form, as the live file writes it
    Path(sp).write_text(json.dumps(state))
    ip = _write_intake_log(tmp_path)
    res = await well_measure_floor_f6(state_path=sp, intake_log=ip, now=NOW)
    cov = res["coverage"]["human_substrate"]
    assert cov["contaminated"] is False


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


# ── B: the flow leg must measure REALITY, not cron liveness (2026-11-23) ──


@pytest.mark.asyncio
async def test_heartbeat_line_is_not_a_receipt(tmp_path):
    """A NO_INTAKE heartbeat proves the CRON is alive. It does not prove the
    human was measured. Counting it made the flow leg permanently covered with
    zero human input (measured live: 3206 heartbeats, 0 real receipts)."""
    sp = _write_state(tmp_path)
    ip = _write_intake_log(tmp_path, status="NO_INTAKE")
    server = tmp_path / "server.py"
    server.write_text("async def well_guard_dignity(): ...\n")
    res = await well_measure_floor_f6(
        state_path=sp,
        intake_log=ip,
        server_py=str(server),
        now=NOW,
    )
    assert res["f6_index"] is None, "a heartbeat is liveness, not a receipt"
    assert any("consequence_flow" in r for r in res["null_reasons"]), res["null_reasons"]


@pytest.mark.asyncio
async def test_self_report_lane_is_a_real_receipt(tmp_path):
    """The SELF_REPORT lane carries the human's own reported reality — it is a
    real receipt stream and must satisfy the flow leg."""
    sp = _write_state(tmp_path)
    sr = _write_self_report_log(tmp_path)
    server = tmp_path / "server.py"
    server.write_text("async def well_guard_dignity(): ...\n")
    res = await well_measure_floor_f6(
        state_path=sp,
        receipt_logs=[sr],
        server_py=str(server),
        now=NOW,
    )
    assert res["f6_index"] is not None
    assert 0.5 < res["f6_index"] <= 1.0
    assert res["coverage"]["consequence_flow"]["covered"] is True


@pytest.mark.asyncio
async def test_flow_index_decays_with_receipt_age(tmp_path):
    """The v0 formula is 0.5 + 0.5*flow, flow = 1 - age/24h. A 12h-old receipt
    must land below a fresh one — the index is a measurement, not a constant."""
    sp = _write_state(tmp_path)
    server = tmp_path / "server.py"
    server.write_text("async def well_guard_dignity(): ...\n")
    fresh = await well_measure_floor_f6(
        state_path=sp,
        receipt_logs=[_write_intake_log(tmp_path, age_s=60.0)],
        server_py=str(server),
        now=NOW,
    )
    aged = await well_measure_floor_f6(
        state_path=sp,
        receipt_logs=[_write_intake_log(tmp_path, age_s=12 * 3600.0)],
        server_py=str(server),
        now=NOW,
    )
    assert aged["f6_index"] < fresh["f6_index"]
    assert aged["f6_index"] >= 0.5


def test_default_receipt_logs_exclude_machine_observed_and_sensor():
    """A machine-observed signal must not refresh the floor (F13 MARUAH canon
    2026-10-23 — the machine never self-certifies the human in order to unlock
    itself). The SYSTEM_OBSERVED and SENSOR lanes stay out until F13 rules."""
    from well_mcp.receipts import default_receipt_logs

    logs = default_receipt_logs()
    assert any("human_checkins" in p for p in logs), "the SELF_REPORT lane is a real receipt stream"
    assert not any("human_reality" in p for p in logs), "SYSTEM_OBSERVED must stay out of the flow leg"
    assert not any("sensor_events" in p for p in logs), "no device on the mesh yet"


def test_served_leg_views_are_evidence_only(tmp_path):
    """The served legs carry age + band + guard presence. No verdict field."""
    from well_mcp.receipts import consequence_flow_view, dignity_surface_view

    log = _write_intake_log(tmp_path, age_s=90.0)
    flow = consequence_flow_view(intake_log=log, now=NOW)
    assert flow["covered"] is True
    assert flow["last_receipt_age_s"] is not None
    assert flow["band_seconds"] == 24 * 3600
    assert "verdict" not in flow

    server = tmp_path / "server.py"
    server.write_text("async def well_guard_dignity(): ...\n")
    dig = dignity_surface_view(server_py=str(server))
    assert dig["covered"] is True
    assert "verdict" not in dig
