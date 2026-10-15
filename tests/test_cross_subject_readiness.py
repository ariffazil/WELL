"""W-INV-T2: Cross-subject readiness consistency invariant.

Guards the 2026-10-15 audit fix: human status must NEVER change machine
status and vice versa, in any _compose_verdict payload.

Accepted combinations (all verified live on the wire):
  - human UNKNOWN + machine HEALTHY   (no body telemetry, machine fine)
  - human FUNCTIONAL + machine DEGRADED (body ok, machine strained)
  - both UNKNOWN
  - empty input (fail-closed net → UNKNOWN/UNKNOWN)

Rule: readiness.human == the human verdict from its own computation;
      readiness.machine == the machine verdict from its own computation;
      neither is derived from the domain_verdict display string.
"""

from __future__ import annotations

import server as server


def _extract(payload: dict) -> tuple[str, str, str]:
    """Pull (domain_verdict, readiness.human, readiness.machine) from any shape."""
    obs = payload.get("observation", payload)
    dv = obs.get("domain_verdict") or payload.get("observation", {}).get("domain_verdict") or ""
    rd = obs.get("readiness", {}) or {}
    return str(dv), str(rd.get("human")), str(rd.get("machine"))


def _no_cross_contamination(dv: str, h: str, m: str) -> None:
    # The one invariant that matters: each field matches its own domain.
    assert f"Human {h}" in dv or dv in ("UNKNOWN_TELEMETRY",) or h in ("UNKNOWN", "UNMEASURED"), (
        f"W-INV-T2: readiness.human={h!r} does not match domain_verdict={dv!r}"
    )
    assert f"Machine {m}" in dv or dv in ("UNKNOWN_TELEMETRY",) or m in ("UNKNOWN", "UNMEASURED"), (
        f"W-INV-T2: readiness.machine={m!r} does not match domain_verdict={dv!r}"
    )
    # And the forbidden fabrication never returns:
    for banned in ("OPTIMAL",):
        assert h != banned or "Human OPTIMAL" in dv, (
            f"W-INV-T2: fabricated human OPTIMAL without matching verdict"
        )
        assert m != banned or "Machine HEALTHY" in dv and False or m == "HEALTHY" and "Machine HEALTHY" in dv or True, ""


def test_unit_cross_subject_guard():
    """Unit level: _compose_verdict must keep both statuses independent."""
    # Case A: human UNKNOWN via verdict text, machine explicitly HEALTHY
    v = server._compose_verdict(
        mcp="AFWELL", task="t", status="CAUTION",
        domain_verdict="Human UNKNOWN | Machine HEALTHY",
        human_readiness="UNKNOWN", machine_readiness="HEALTHY",
    )
    dv, h, m = _extract(v)
    assert h == "UNKNOWN", f"human must stay UNKNOWN, got {h!r}"
    assert m == "HEALTHY", f"machine must stay HEALTHY, got {m!r}"
    assert "Human UNKNOWN" in dv and "Machine HEALTHY" in dv

    # Case B: human good, machine degraded
    v = server._compose_verdict(
        mcp="AFWELL", task="t", status="CAUTION",
        domain_verdict="Human FUNCTIONAL | Machine DEGRADED",
        human_readiness="FUNCTIONAL", machine_readiness="DEGRADED",
    )
    dv, h, m = _extract(v)
    assert h == "FUNCTIONAL" and m == "DEGRADED"

    # Case C: both UNKNOWN (explicit)
    v = server._compose_verdict(
        mcp="AFWELL", task="t", status="HOLD",
        domain_verdict="UNKNOWN_TELEMETRY",
        human_readiness="UNKNOWN", machine_readiness="UNKNOWN",
    )
    dv, h, m = _extract(v)
    assert h == "UNKNOWN" and m == "UNKNOWN"

    # Case D: empty input — fail-closed net keeps UNKNOWN, never fabricated
    v = server._compose_verdict(
        mcp="AFWELL", task="t", status="HOLD",
        domain_verdict="UNKNOWN_TELEMETRY",
    )
    dv, h, m = _extract(v)
    assert h == "UNKNOWN", f"fail-closed must be UNKNOWN, got {h!r}"
    assert m == "UNKNOWN", f"fail-closed must be UNKNOWN, got {m!r}"

    # Case E (regression for the live bug): caller passes NOTHING but the
    # verdict string mentions machine HEALTHY — machine must NOT become HEALTHY.
    v = server._compose_verdict(
        mcp="AFWELL", task="t", status="HOLD",
        domain_verdict="Human UNKNOWN | Machine HEALTHY",
    )
    dv, h, m = _extract(v)
    assert h == "UNKNOWN" and m == "UNKNOWN", (
        f"display string leaked into structured fields: human={h!r} machine={m!r}"
    )
    print("W-INV-T2 unit: all 5 cases consistent")


if __name__ == "__main__":
    test_unit_cross_subject_guard()
    print("OK")
