"""well_witness.cross_check — divergence detection for WELL.

Phase 1 implements the two checks that would have caught the live
2026-08-19 state.json leakage:

  1. check_state_honesty: state.json with environment=TEST, or
     truth_status=TEST, or reason starting with "Mocked" is a
     DIVERGENCE. A test fixture in production is a constitutional
     violation (F2 TRUTH), not a benign state.

  2. check_h_well_divergence: well_check_repair.H_WELL must agree
     with well_validate_vitality.H_WELL. If well_check_repair
     leaks a fabricated readiness.human while well_validate_vitality
     returns UNKNOWN, the two paths disagree on the same substrate
     — that is a DIVERGENCE.

Both checks are pure functions (no I/O) so they can be tested
without a running WELL service. The HTTP server (well_witness.server)
delegates to run_all_checks() at GET /divergence.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

# WELL organ location — overridable for tests.
WELL_ROOT = Path(os.environ.get("WELL_ROOT", "/root/WELL"))
STATE_PATH = WELL_ROOT / "state.json"


def check_state_honesty(
    state: dict[str, Any] | None = None,
    state_path: Path | None = None,
) -> dict[str, Any]:
    """Read state.json (or use provided dict). Return DIVERGENCE if
    the state is a test fixture that leaked into production.

    Detection rules (same as vitality_gate.assess_h_well):
      - environment == "TEST"
      - truth_status == "TEST"
      - reason starts with "Mocked"

    Returns a finding dict. NEVER raises.
    """
    if state is None:
        path = state_path or STATE_PATH
        if not path.exists():
            return {
                "verdict": "OK",
                "check": "state_honesty",
                "reason": "no_state_file",
                "evidence": f"path={path} does not exist (honest empty)",
            }
        try:
            state = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            return {
                "verdict": "DIVERGENCE",
                "check": "state_honesty",
                "reason": "state_unparseable",
                "evidence": f"json error: {e}",
            }

    env = state.get("environment")
    truth = state.get("truth_status")
    reason = str(state.get("reason", ""))

    if env == "TEST" or truth == "TEST" or reason.startswith("Mocked"):
        return {
            "verdict": "DIVERGENCE",
            "check": "state_honesty",
            "reason": "test_fixture_detected",
            "evidence": (
                f"env={env} truth={truth} reason={reason[:60]!r}"
            ),
            "remediation": (
                "state.json is a test fixture. Restore to the 4-field "
                "honest empty: {truth_status: INSUFFICIENT_DATA, "
                "environment: PROD, well_score: null, reason: 'no "
                "production state yet'}"
            ),
        }
    return {
        "verdict": "OK",
        "check": "state_honesty",
        "reason": "state_honest",
        "evidence": f"env={env} truth={truth} reason={reason[:60]!r}",
    }


def check_h_well_divergence(
    well_check_repair_fn: Any | None = None,
    well_validate_vitality_fn: Any | None = None,
) -> dict[str, Any]:
    """Cross-check well_check_repair vs well_validate_vitality on H_WELL.

    DIVERGENCE if:
      - well_check_repair leaks a fabricated 'readiness' field at the
        top level or inside its 'observation' envelope (the T3 fix
        should prevent this; if it returns, something is wrong)
      - well_validate_vitality returns no H_WELL field at all
      - the two paths disagree about H_WELL state

    well_check_repair_fn and well_validate_vitality_fn are injectable
    for tests; default is to import from server.py.
    """
    try:
        if well_check_repair_fn is None:
            sys.path.insert(0, str(WELL_ROOT))
            from server import well_check_repair as well_check_repair_fn  # type: ignore
        if well_validate_vitality_fn is None:
            from server import well_validate_vitality as well_validate_vitality_fn  # type: ignore
    except Exception as e:  # noqa: BLE001
        return {
            "verdict": "ERROR",
            "check": "h_well_divergence",
            "reason": "import_failed",
            "evidence": f"{type(e).__name__}: {e}",
        }

    try:
        repair_result = well_check_repair_fn(mode="precheck")
        vitality_result = well_validate_vitality_fn(mode="state")
    except Exception as e:  # noqa: BLE001
        return {
            "verdict": "ERROR",
            "check": "h_well_divergence",
            "reason": "tool_call_failed",
            "evidence": f"{type(e).__name__}: {e}",
        }

    # T3 fix invariant: well_check_repair MUST NOT return readiness.
    repair_leaks_readiness = (
        "readiness" in repair_result
        or (
            isinstance(repair_result.get("observation"), dict)
            and "readiness" in repair_result["observation"]
        )
    )
    if repair_leaks_readiness:
        return {
            "verdict": "DIVERGENCE",
            "check": "h_well_divergence",
            "reason": "well_check_repair_leaks_readiness",
            "evidence": (
                f"repair keys: {list(repair_result.keys())[:10]}; "
                f"observation.readiness = "
                f"{repair_result.get('observation', {}).get('readiness')}"
            ),
            "remediation": (
                "T3 fix regressed. well_check_repair must strip the "
                "fabricated readiness field from well_777_forge output."
            ),
        }

    vitality_h_well = vitality_result.get("H_WELL")
    if vitality_h_well is None:
        return {
            "verdict": "DIVERGENCE",
            "check": "h_well_divergence",
            "reason": "well_validate_vitality_missing_h_well",
            "evidence": (
                f"vitality_result keys: {list(vitality_result.keys())[:10]}"
            ),
        }

    return {
        "verdict": "OK",
        "check": "h_well_divergence",
        "reason": "h_well_consistent",
        "evidence": (
            f"repair_no_readiness=True, vitality_h_well={vitality_h_well!r}"
        ),
    }


def run_all_checks() -> list[dict[str, Any]]:
    """Run every divergence check. Returns a list of findings."""
    return [
        check_state_honesty(),
        check_h_well_divergence(),
    ]


if __name__ == "__main__":
    import pprint
    pprint.pp(run_all_checks())
