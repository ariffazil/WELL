#!/usr/bin/env python3
"""G9 — RASA WITNESS FAILS OPEN (HUMAN_RASA P0 REMEDIATION ::v1.0).

Audit evidence (GAP_REGISTER 2026-11-01): gate/well_gate.py:195-208 —
`except ImportError: pass`, so reflect_readiness() continued WITHOUT the
Rasa Witness Contract and could still report STABLE.

Contract under test (tightening only, no gate removed):
  witness unavailable (ImportError) OR witness raising  ->  status "HOLD"
  with reason RASA_WITNESS_UNAVAILABLE. Never "it ran fine without it".

Fixtures are synthetic only (no real human message, audio, image or record).
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import gate.well_gate as well_gate  # noqa: E402


SYNTHETIC_STATE = {
    "well_score": 100,
    "metrics": {
        "sleep": {"sleep_debt_days": 0},
        "cognitive": {"clarity": 9},
    },
}


@pytest.fixture
def state_file(tmp_path, monkeypatch):
    """Synthetic well_state so reflect_readiness gets past the UNANCHORED check."""
    path = tmp_path / "state.json"
    path.write_text(json.dumps(SYNTHETIC_STATE))
    monkeypatch.setattr(well_gate, "WELL_STATE_PATH", path)
    return path


def test_g9_import_error_returns_hold_not_stable(state_file, monkeypatch):
    """ImportError inside the rasa witness call must HOLD, not pass silently."""
    # Forces `from gate.rasa_witness import rasa_witness_gate` to raise ImportError.
    monkeypatch.setitem(sys.modules, "gate.rasa_witness", None)

    status, msg, score, violations, rasa = well_gate.reflect_readiness()

    assert status == "HOLD", f"expected HOLD when witness unavailable, got {status!r}"
    assert "RASA_WITNESS_UNAVAILABLE" in msg, msg
    assert "RASA_WITNESS_UNAVAILABLE" in violations, violations
    assert rasa is None


def test_g9_witness_exception_returns_hold_not_error_pass(state_file, monkeypatch):
    """A raising witness must also HOLD with the same reason (fail-closed)."""
    import gate.rasa_witness as rw

    def _boom(*_args, **_kwargs):
        raise RuntimeError("synthetic witness failure")

    monkeypatch.setattr(rw, "rasa_witness_gate", _boom)

    status, msg, score, violations, rasa = well_gate.reflect_readiness()

    assert status == "HOLD", f"expected HOLD when witness raises, got {status!r}"
    assert "RASA_WITNESS_UNAVAILABLE" in msg, msg
    assert "RASA_WITNESS_UNAVAILABLE" in violations, violations
    assert rasa is None


def test_g9_witness_available_path_unchanged(state_file):
    """Regression: with the witness importable, behaviour is the pre-G9 path."""
    status, msg, score, violations, rasa = well_gate.reflect_readiness()

    assert status in ("STABLE", "DEGRADED", "ERROR"), status
    assert "RASA_WITNESS_UNAVAILABLE" not in msg, msg
    assert "RASA_WITNESS_UNAVAILABLE" not in violations, violations
