"""P0-2 — a stale plane cannot veto the triad (2026-09-28).

Measured defect: the human plane's own reading was 289h old (/var/lib/well/state.json
`last_successful_read` = 2026-09-15T15:30Z, and the readiness payload says
"No data for 289h") yet it still entered the `min()` that sets the unified score.
An absence winning `min()` forever is a veto wearing a measurement's clothes, and
WELL's charter is mirror, not veto.

The fix is EXCLUSION, not flooring: flooring EXPIRED at 0.05 (attempted and
reverted earlier on 2026-09-28) keeps the plane inside `min()` and makes the veto
permanent. Absence lowers coverage and confidence; it never lowers the score.

Run:
  cd /root/WELL && PYTHONPATH=. .venv/bin/python -m pytest \
      tests/test_triad_phase4_exclusion.py -q
"""

from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path

import pytest

WELL_ROOT = Path(__file__).resolve().parents[1]
if str(WELL_ROOT) not in sys.path:
    sys.path.insert(0, str(WELL_ROOT))

from well_triad import phase4_tools as p4  # noqa: E402

NOW = _dt.datetime.now(_dt.timezone.utc)


def _iso(hours_ago: float) -> str:
    return (NOW - _dt.timedelta(hours=hours_ago)).isoformat()


def _plane(name: str, score: float, band: str, *, age_hours: float | None = None) -> dict:
    return {
        "score": score,
        "state": "WATCH",
        "weakest": "none",
        "band": band,
        "age_hours": age_hours,
        "measured_at": _iso((age_hours or 0.0)),
        "reason": f"{band}: {name} plane data is {age_hours}h old",
    }


@pytest.fixture(autouse=True)
def no_ledger_writes(monkeypatch: pytest.MonkeyPatch) -> None:
    """Composition is a read; the test must not append to the live event ledger."""
    monkeypatch.setattr(p4._wt_events, "append_typed_event", lambda **kw: "")


@pytest.fixture()
def healthy_machine(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        p4,
        "_fetch_machine_plane",
        lambda lookback_hours: {
            **_plane("machine", 0.62, "FRESH", age_hours=0.0),
            "avg_score": 0.9,
            "organs": {},
            "route": "RECOVER",
            "critical_count": 0,
        },
    )


@pytest.fixture()
def healthy_governance(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        p4,
        "_fetch_governance_plane",
        lambda lookback_hours: {
            **_plane("governance", 0.9, "FRESH", age_hours=0.0),
            "consent_intact": True,
            "active_scopes": ["s1"],
            "active_recommendations": 0,
            "open_attestations": 0,
            "governance_signals": 0,
        },
    )


def _triadic(monkeypatch: pytest.MonkeyPatch, human: dict) -> dict:
    monkeypatch.setattr(p4, "_fetch_human_plane", lambda actor_id: human)
    return p4.well_assess_triadic_state(actor_id="arif", lookback_hours=1)


# ── the veto itself ──────────────────────────────────────────────────────────


def test_expired_plane_cannot_drag_the_unified_score(
    monkeypatch: pytest.MonkeyPatch, healthy_machine, healthy_governance
) -> None:
    """An EXPIRED human plane at 0.05 must not decide the unified score."""
    stale = _plane("human", 0.05, "EXPIRED", age_hours=289.0)
    stale["state"] = "CRITICAL"
    out = _triadic(monkeypatch, stale)
    tri = out["triadic"]

    # 0.62 is the healthiest-possible value of the MEASURED planes (machine 0.62,
    # governance 0.90) -- the min() over measured only.
    assert tri["unified_score"] == 0.62, tri
    assert tri["unified_score"] > 0.05
    assert tri["weakest_plane"] == "machine"
    assert tri["coverage"] == "2/3 planes"
    assert "human" in tri["excluded_planes"]
    assert tri["plane_bands"]["human"] == "EXPIRED"
    # The stale number is still reported where it belongs (that plane's own dict),
    # it simply no longer speaks for the whole body.
    assert out["human"]["score"] == 0.05


def test_stale_plane_is_measured_and_counts(
    monkeypatch: pytest.MonkeyPatch, healthy_machine, healthy_governance
) -> None:
    """STALE (<24h) is a measurement: it stays in min() and coverage says 3/3."""
    monkeypatch.setattr(
        p4,
        "_fetch_machine_plane",
        lambda lookback_hours: {
            **_plane("machine", 0.9, "FRESH", age_hours=0.0),
            "avg_score": 0.9,
            "organs": {},
            "route": "PROCEED",
            "critical_count": 0,
        },
    )
    out = _triadic(monkeypatch, _plane("human", 0.884, "STALE", age_hours=10.0))
    tri = out["triadic"]
    assert tri["coverage"] == "3/3 planes"
    assert tri["excluded_planes"] == {}
    assert tri["unified_score"] == 0.884
    assert tri["weakest_plane"] == "human"


def test_nothing_measured_emits_no_number(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    """Zero measured planes -> unified_score None + INSUFFICIENT_EVIDENCE.

    WELL must report the absence, not manufacture a score-shaped word from it.
    """
    monkeypatch.setattr(
        p4,
        "_fetch_machine_plane",
        lambda lookback_hours: {
            **_plane("machine", 0.05, "UNKNOWN"),
            "avg_score": 0.05,
            "organs": {},
            "route": "SABAR",
            "critical_count": 0,
        },
    )
    monkeypatch.setattr(
        p4,
        "_fetch_governance_plane",
        lambda lookback_hours: {
            **_plane("governance", 0.0, "EXPIRED", age_hours=300.0),
            "consent_intact": False,
            "active_scopes": [],
            "active_recommendations": 0,
            "open_attestations": 0,
            "governance_signals": 0,
        },
    )
    out = _triadic(monkeypatch, _plane("human", 0.05, "EXPIRED", age_hours=289.0))
    tri = out["triadic"]
    assert tri["unified_score"] is None
    assert tri["coverage"] == "0/3 planes"
    assert tri["signal"] == "INSUFFICIENT_EVIDENCE"
    assert tri["route"] == "INSUFFICIENT_EVIDENCE"  # mirrored for old consumers
    assert tri["weakest_plane"] is None
    assert "INSUFFICIENT_EVIDENCE" in tri["f_recommendation"]
    assert out["awaiting_verification"] is True
    # every plane is accounted for as an absence with a reason
    assert set(tri["excluded_planes"]) == {"human", "machine", "governance"}


# ── band derivation from the data's own timestamp ────────────────────────────


@pytest.mark.parametrize(
    "hours_ago,expected",
    [
        (0.5, "FRESH"),
        (2.0, "AGING"),
        (10.0, "STALE"),
        (30.0, "EXPIRED"),
        (289.0, "EXPIRED"),
    ],
)
def test_freshness_bands_from_age(hours_ago: float, expected: str) -> None:
    assert p4._freshness_band(_iso(hours_ago))["band"] == expected


def test_freshness_band_never_invents_a_timestamp() -> None:
    assert p4._freshness_band(None)["band"] == "UNKNOWN"
    assert p4._freshness_band("not-a-date")["band"] == "UNKNOWN"


def test_missing_state_file_is_an_absence_not_a_middling_score(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """No state file used to inject a fabricated 0.5 into min(). It is now UNKNOWN."""
    monkeypatch.setenv("WELL_STATE_PATH", str(tmp_path / "absent.json"))
    human = p4._fetch_human_plane("arif")
    assert human["band"] == "UNKNOWN"
    assert human["missing_evidence"] == ["no_state"]


def test_human_plane_ages_from_its_own_read_not_from_the_file_write(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A fresh file rewrite must not resuscitate a 289h-old reading.

    Live shape of /var/lib/well/state.json on 2026-09-28: `timestamp` written a
    few hours ago by an operator inject, `last_successful_read` 289h old.
    """
    state = {
        "well_score": 88.4,
        "timestamp": _iso(1.0),  # file rewritten an hour ago
        "last_successful_read": _iso(289.0),  # the observation itself
        "source_type": "OPERATOR_REPORTED",
        "metrics": {},
    }
    p = tmp_path / "state.json"
    p.write_text(json.dumps(state))
    monkeypatch.setenv("WELL_STATE_PATH", str(p))

    human = p4._fetch_human_plane("arif")
    assert human["band"] == "EXPIRED"
    assert human["age_hours"] == pytest.approx(289.0, abs=0.2)
    # an expired reading can never be labelled OPTIMAL physiology
    assert human["state"] != "OPTIMAL"


def test_stale_human_reading_is_capped_out_of_optimal(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """STALE keeps its score, loses the OPTIMAL label (measured, not canonical)."""
    state = {
        "well_score": 92.0,  # >= 0.85 would otherwise read OPTIMAL
        "timestamp": _iso(10.0),
        "last_successful_read": _iso(10.0),
        "metrics": {},
    }
    p = tmp_path / "state.json"
    p.write_text(json.dumps(state))
    monkeypatch.setenv("WELL_STATE_PATH", str(p))

    human = p4._fetch_human_plane("arif")
    assert human["band"] == "STALE"
    assert human["score"] == 0.92  # the number is still the truth
    assert human["state"] != "OPTIMAL"


# ── compatibility + verdict hygiene ─────────────────────────────────────────


def test_existing_output_keys_survive(
    monkeypatch: pytest.MonkeyPatch, healthy_machine, healthy_governance
) -> None:
    """phase5 HUD / snapshot consumers read these keys; they must still be there."""
    out = _triadic(monkeypatch, _plane("human", 0.5, "FRESH", age_hours=0.0))
    for key in ("ok", "actor_id", "human", "machine", "governance", "triadic",
                "awaiting_verification", "f2_provenance", "f8_truth_class",
                "f12_verdict_hygiene", "w0"):
        assert key in out, key
    tri = out["triadic"]
    for key in ("unified_score", "weakest_plane", "route", "f_recommendation"):
        assert key in tri, key
    assert tri["signal"] == tri["route"]  # new name and mirror never disagree
    assert out["machine"]["signal"] == out["machine"]["route"]


def test_route_field_cannot_become_a_verdict(
    monkeypatch: pytest.MonkeyPatch, healthy_machine, healthy_governance
) -> None:
    """F12: WELL composes a signal. It never seals, judges, or acts."""
    out = _triadic(monkeypatch, _plane("human", 0.9, "FRESH", age_hours=0.0))
    assert "sealed" not in out and "verdict" not in out and "acted_on" not in out
    assert out["f12_verdict_hygiene"] == "no_seal_no_verdict_in_well_response"
    assert out["triadic"]["signal"] in {
        "SABAR",
        "HOLD",
        "RECOVER",
        "REDUCE_LOAD",
        "PROCEED",
        "INSUFFICIENT_EVIDENCE",
    }


def test_route_decision_reports_absence() -> None:
    """The router cannot name a state it has no evidence for."""
    assert p4._route_decision(None, None, 0) == "INSUFFICIENT_EVIDENCE"
    # a live machine CRITICAL is an observation, not an absence -- still SABAR
    assert p4._route_decision(0.9, "machine", 1) == "SABAR"
