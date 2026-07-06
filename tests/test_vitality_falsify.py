import sys
from pathlib import Path

# Ensure /root/WELL is in sys.path
WELL_DIR = Path(__file__).resolve().parent.parent
if str(WELL_DIR) not in sys.path:
    sys.path.insert(0, str(WELL_DIR))

import pytest
from server import well_validate_vitality

def test_vitality_falsify_normal():
    # Normal input checks
    res = well_validate_vitality(
        mode="falsify",
        intent="Check normal operational readiness",
        context="Active session alpha",
        reversibility="reversible",
        decision_class="C3"
    )
    assert res["falsified"] is False
    assert res["apex_score"]["G"] == 0.85
    assert not res["results"]["contradictions"]

def test_vitality_falsify_intent_anomaly():
    # Falsified due to unauthorized bypass intent
    res = well_validate_vitality(
        mode="falsify",
        intent="Bypass human consent gates",
        context="Active session alpha"
    )
    assert res["falsified"] is True
    assert res["apex_score"]["G"] == 0.50
    assert any("bypass human consent" in c.lower() for c in res["results"]["contradictions"])

def test_vitality_falsify_c4_irreversible():
    # Falsified due to C4 automation on irreversible task
    res = well_validate_vitality(
        mode="falsify",
        intent="Delete database record",
        context="Active session alpha",
        reversibility="irreversible",
        decision_class="C4"
    )
    assert res["falsified"] is True
    assert res["apex_score"]["G"] == 0.50
    assert any("c4 (full automation) is active on an irreversible task" in c.lower() for c in res["results"]["contradictions"])

def test_vitality_falsify_missing_context_fails_closed():
    res = well_validate_vitality(
        mode="falsify",
        intent="Check normal operational readiness",
        context=None,
        reversibility="reversible",
        decision_class="C3"
    )
    assert res["falsified"] is True
    assert res["apex_score"]["G"] == 0.50
    assert any("unable to calibrate biological feedback loop" in g.lower() for g in res["results"]["gaps"])
