"""well_mcp.transport.metabolize — Stage 3 of the 5-stage reaction loop.

METABOLIZE: compute machine_entropy, cognitive_entropy_rate,
metabolic_flux, coupling_state, readiness_verdict.

Authority: REFLECT_ONLY. Reads substrate slice.
"""

from __future__ import annotations

import math
from typing import Any, Dict


# Weights for the metabolic_flux equation.
ALPHA_HUMAN = 0.55
BETA_MACHINE = 0.45

# Machine entropy component weights.
MACHINE_WEIGHTS = {
    "E1": 0.30,  # context_budget_consumed
    "E2": 0.20,  # tool_latency_drift
    "E3": 0.20,  # resource_staleness
    "E4": 0.30,  # tool_error_rate
}

# Flux regime thresholds.
FLUX_REGIMES = [
    (0.40, "STABLE"),
    (0.65, "WARNING"),
    (0.85, "DEGRADED"),
    (1.01, "CRITICAL"),
]


def _flux_regime(flux: float) -> str:
    if flux < 0:
        return "STABLE"
    for cap, label in FLUX_REGIMES:
        if flux < cap:
            return label
    return "CRITICAL"


def _coupling_state(human: float, machine: float, governance: float) -> float:
    """σ(human × machine × governance) — sigmoid to [0.0, 1.0].

    Inputs are 0.0–1.0 (human readiness, machine stability, gov seal).
    Returns 0.0 (broken) to 1.0 (emergent).
    """
    product = human * machine * governance
    # Sigmoid to [0, 1].
    return 1.0 / (1.0 + math.exp(-8.0 * (product - 0.5)))


def stamp_metabolize(
    encoded_stamp: Dict[str, Any],
    human_state: float = 0.70,  # 0.0 = CRITICAL, 1.0 = OPTIMAL
    machine_state: float = 0.70,  # 0.0 = CRITICAL, 1.0 = STABLE
    governance_state: float = 0.85,  # 0.0 = VOID, 1.0 = SEAL
    e1: float = 0.30,  # context_budget_consumed
    e2: float = 0.20,  # tool_latency_drift
    e3: float = 0.20,  # resource_staleness
    e4: float = 0.30,  # tool_error_rate
    cognitive_entropy_rate: float = 0.30,
) -> Dict[str, Any]:
    """Stage 3 — METABOLIZE.

    Args:
        encoded_stamp: output of stamp_encode()
        human_state: well_assess_homeostasis result (0.0–1.0)
        machine_state: well_assess_machine_substrate result (0.0–1.0)
        governance_state: arifOS verdict (0.0=VOID, 1.0=SEAL)
        e1, e2, e3, e4: machine entropy components
        cognitive_entropy_rate: human cognitive entropy (0.0–1.0)

    Returns:
        WellStamp.metabolized with metabolic_flux, machine_entropy,
        coupling_state, readiness_verdict.

    Cost: 20–200 ms typical, 500 ms ceiling.
    """
    # 1. Compute machine_entropy.
    machine_entropy = (
        MACHINE_WEIGHTS["E1"] * e1
        + MACHINE_WEIGHTS["E2"] * e2
        + MACHINE_WEIGHTS["E3"] * e3
        + MACHINE_WEIGHTS["E4"] * e4
    )
    machine_entropy = max(0.0, min(1.0, machine_entropy))

    # 2. Compute metabolic_flux.
    metabolic_flux = (
        ALPHA_HUMAN * cognitive_entropy_rate + BETA_MACHINE * machine_entropy
    )
    metabolic_flux = max(0.0, min(1.0, metabolic_flux))

    # 3. Compute coupling_state.
    coupling = _coupling_state(human_state, machine_state, governance_state)

    # 4. Propose readiness_verdict (not enforced; sovereign decides).
    flux_regime = _flux_regime(metabolic_flux)

    if coupling < 0.15:
        readiness = "CRITICAL"
    elif coupling < 0.40:
        readiness = "DEGRADED"
    elif coupling < 0.65:
        readiness = "STABLE"
    elif coupling < 0.85:
        readiness = "STABLE"
    else:
        readiness = "OPTIMAL"

    metabolized = dict(encoded_stamp)
    metabolized.update(
        {
            "stage": "metabolize",
            "stage_status": "PASS"
            if encoded_stamp.get("stage_status") == "PASS"
            else encoded_stamp.get("stage_status"),
            "human_state": human_state,
            "machine_state": machine_state,
            "governance_state": governance_state,
            "machine_entropy": machine_entropy,
            "cognitive_entropy_rate": cognitive_entropy_rate,
            "metabolic_flux": metabolic_flux,
            "flux_regime": flux_regime,
            "coupling_state": coupling,
            "readiness_verdict": readiness,
        }
    )

    return metabolized
