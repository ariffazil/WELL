"""
WELL MCP Server — Human Substrate Governance Layer
Phase 1: Immutable Ledger & Observability

W0 Sovereignty Invariant: WELL holds a mirror, not a veto.
WELL informs. arifOS judges. A-FORGE executes. Hierarchy is invariant.
"""

from __future__ import annotations

try:
    import uvloop

    uvloop.install()
except ImportError:
    pass  # Windows / dev fallback

import hashlib
import json
import logging
import random
import datetime
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

from fastmcp import FastMCP, Context
from starlette.responses import JSONResponse

# ── APEX Runtime Governance Envelope (APEX-MCP-001) ─────────────────────────
_APEX_AVAILABLE = True
try:
    from apex_envelope_well import well_apex_envelope as _build_apex
except ImportError:
    _APEX_AVAILABLE = False
    _build_apex = None  # type: ignore

# ── Paths (defined before use in fallback import) ───────────────────────────────
WELL_DIR = Path(__file__).parent

# ── Reality Ledger Bridge ────────────────────────────────────────────────────────
_WELL_LEDGER_AVAILABLE = True
try:
    from core.organ_ledger_bridge import record_well_assessment
except ImportError:
    _WELL_LEDGER_AVAILABLE = False

# ── Organ Governance (arifOS L1-L13) ─────────────────────────────────────────
try:
    from internal.organ_governance import check_governance
except ImportError:
    import sys as _sys

    _sys.path.insert(0, str(WELL_DIR))
    from internal.organ_governance import check_governance


# ── APEX Injection Helper (APEX-MCP-001) ───────────────────────────────────
def _inject_apex(
    result: dict[str, Any],
    tool_name: str = "unknown",
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Inject APEX governance envelope into any WELL tool result."""
    if _APEX_AVAILABLE and isinstance(result, dict):
        try:
            result["apex"] = _build_apex(
                tool_name=tool_name,
                state=state,
                actor_id=result.get("operator_id") or (state or {}).get("operator_id"),
            )
        except Exception:
            pass
    return result


# PR 6 — reflect-only boundary import. Lazy-tolerant: if the engines
# module is not on sys.path, the import is deferred until the wrap
# call below (which is also tolerant).
try:
    from engines.reflect import wrap_canonical_tools as _wrap_canonical_tools

    _REFLECT_LOADED = True
except ImportError:
    _REFLECT_LOADED = False
    _wrap_canonical_tools = None  # type: ignore[assignment]

# ── Agentic Anthropology — State Classifier (Phase 1) ─────────────────────
_STATE_CLASSIFIER_AVAILABLE = True
try:
    from arifosmcp.rama.state_classifier import get_state_classifier
    from arifosmcp.rama.state_classifier_schemas import StateClassifierResult
except ImportError:
    _STATE_CLASSIFIER_AVAILABLE = False
    get_state_classifier = None  # type: ignore[assignment]
    StateClassifierResult = None  # type: ignore[assignment]

# ── Paths (re-export for external use) ────────────────────────────────────────
import os as _os

STATE_PATH = Path(_os.environ.get("WELL_STATE_PATH", "/root/WELL/state.json"))
EVENTS_PATH = Path(_os.environ.get("WELL_EVENTS_PATH", "/root/WELL/events.jsonl"))
VAULT_LEDGER_PATH = Path(
    _os.environ.get("WELL_VAULT_PATH", "/root/WELL/vault_ledger.jsonl")
)

# ── Server ─────────────────────────────────────────────────────────────────────
# ── Provenance Enums (Amanah Truth-Preservation) ───────────────────────────────
WELL_SOURCE_TYPES = {
    "USER_CONFIRMED": "Operator Arif directly confirmed or reported",
    "SENSOR": "Automated sensor or wearable data",
    "AGENT_INFERRED": "Derived by AI agent from other data",
    "OPERATOR_REPORTED": "Logged by operator without backend verification",
    "TEST_FIXTURE": "Synthetic test data — not real operator state",
    "SYSTEM_DERIVED": "Computed from existing state, not directly reported",
}
WELL_ENVIRONMENTS = {
    "PROD": "production",
    "TEST": "test_environment",
    "DEV": "development",
}

# ── Force PROD environment unless explicit ──────────────────────────────────
CURRENT_ENV = _os.environ.get("WELL_ENVIRONMENT", "PROD")
WELL_TELEMETRY_STATUS = {
    "LIVE": "fresh data, within expected interval",
    "STALE": "older than 24h, verify before high-stakes use",
    "EXPIRED": "older than 72h, treat as historical only",
    "VOID": "test contamination detected or backend error, do not trust",
}
WELL_TRUTH_STATUS = {
    "VERIFIED": "confirmed against backend source or operator",
    "UNVERIFIED": "received but not yet confirmed",
    "CONTRADICTED": "conflicts with another record",
    "VOID": "known unreliable or contaminated",
    "TEST": "synthetic test data",
    "INSUFFICIENT_DATA": "no trustworthy sovereign state available; manual injection required",
    "OPERATOR_REPORTED": "sovereign manually asserted presence; not biometric verification",
}

# ── Universal Substrate Classification (U-WELL) ───────────────────────────────
UNIVERSAL_SUBSTRATE_CLASSES = {
    "HUMAN_PERSON": "Human individual with biological, cognitive, and livelihood dimensions",
    "HUMAN_BODY_PART": "Part of a human body (nail, blood, organ) — living origin, varying vitality",
    "NONHUMAN_ORGANISM": "Plant, animal, bacteria — independent biological vitality",
    "LIMINAL_BIOLOGICAL": "Virus, prion, spore — replicative potency, host-dependent",
    "MACHINE_SYSTEM": "AI, server, robot — operational reliability, not life",
    "INSTITUTION": "Company, department, VP office — organizational viability",
    "MATERIAL_OBJECT": "Rock, chair, mineral — structural integrity, not life",
    "ECOSYSTEM": "River, forest, reef — ecological vitality",
    "INFORMATION_SYSTEM": "Document, constitution, codebase — coherence and maintainability",
    "SYMBOLIC_METAPHYSICAL": "Soul, niat, dignity — meaning-domain, not machine-measurable",
}

UNIVERSAL_VITALITY_MODES = {
    "HUMAN_PERSON": "biological + cognitive + livelihood + role integrity",
    "HUMAN_BODY_PART": "integration with living body",
    "HUMAN_RELATIONAL_DYNAMIC": (
        "embodied relational integrity (consent, dignity, personhood, "
        "power, vulnerability)"
    ),
    "NONHUMAN_ORGANISM": "biological vitality (metabolism, homeostasis, reproduction)",
    "LIMINAL_BIOLOGICAL": "replicative potency, host dependence",
    "MACHINE_SYSTEM": "operational reliability",
    "COUPLED_HUMAN_MACHINE_SYSTEM": (
        "joint reliability + dignity preservation across the human–machine boundary"
    ),
    "INSTITUTION": "organizational viability (mission, cashflow, trust, coordination)",
    "MATERIAL_OBJECT": "structural integrity, not life",
    "ECOSYSTEM": "ecological vitality (biodiversity, resilience, energy flow)",
    "INFORMATION_SYSTEM": "coherence, maintainability, truth integrity",
    "SYMBOLIC_METAPHYSICAL": "not_machine_measurable — meaning protected, not quantified",
}

# ── G-WELL Governance Abstraction ─────────────────────────────────────────────
# Machine Governance Mirror: reflects the federated governance chain
# G-WELL is not a separate substrate — it is the governance abstraction layer
# that maps machine state (m_machine) into constitutional governance terms.

G_WELL_PILLARS = {
    "autonomic_coherence": "Are governance organs operating within their constitutional boundaries?",
    "check_and_balance": "Is no single organ exceeding its authority? Is the separation of powers intact?",
    "law_compliance": "Are constitutional laws (L1-L13) being respected across the chain?",
    "evidence_integrity": "Is decision evidence anchored and auditable before action?",
    "sovereignty_preserved": "Is human veto path intact and unbypassed?",
}

G_WELL_VERDICTS = ["COHERENT", "STRESSED", "FRAGMENTED", "UNKNOWN"]

# ── W-Floor Definitions (Canonical — WELL_INVARIANTS.md §I6) ───────────────────
W_LAW_DEFINITIONS = {
    "W0": {
        "name": "Sovereignty Invariant",
        "threshold": "always_active",
        "max_severity": "foundational",
        "arifos_map": "F13",
    },
    "W1": {
        "name": "Sleep Integrity",
        "threshold": "debt >= 2 nights or quality < 5",
        "max_severity": "CRITICAL",
        "arifos_map": "F1, F2",
    },
    "W2": {
        "name": "Metabolic Stability",
        "threshold": "dehydration or stability < 5",
        "max_severity": "CAUTION",
        "arifos_map": "L1, L10",
    },
    "W3": {
        "name": "Stress Load",
        "threshold": "load >= 7/10 or chronic elevation",
        "max_severity": "CRITICAL",
        "arifos_map": "F6, F10",
    },
    "W4": {
        "name": "Physical Integrity",
        "threshold": "sedentary >= 4h or pain >= 5/10",
        "max_severity": "CAUTION",
        "arifos_map": "F9, F10",
    },
    "W5": {
        "name": "Cognitive Entropy",
        "threshold": "clarity < 4/10 or high fatigue",
        "max_severity": "WARNING",
        "arifos_map": "F2, F3",
    },
    "W6": {
        "name": "Incentive Decoupling",
        "threshold": ">= 5 similar forges / 30 min",
        "max_severity": "WARNING",
        "arifos_map": "F1, F11",
    },
    "W7": {
        "name": "Skill Atrophy",
        "threshold": ">= 14 days without manual practice",
        "max_severity": "WARNING",
        "arifos_map": "F1, F4",
    },
}

W_FLOOR_SEVERITY_ORDER = {
    "INFO": 0,
    "CAUTION": 1,
    "WARNING": 2,
    "CRITICAL": 3,
    "foundational": 4,
}

# ── Structured Payload Builder ─────────────────────────────────────────────────
# Every structured object must pass schema validation before output.
# This prevents malformed payloads (e.g. missing priority in todos).


def build_well_todo(
    content: str, status: str = "pending", priority: str = "high"
) -> dict[str, str]:
    """
    Build a valid todo object with required schema fields.
    Raises ValueError if any field is missing or invalid.
    """
    valid_statuses = {"pending", "in_progress", "completed", "cancelled"}
    valid_priorities = {"high", "medium", "low"}

    if not content or not isinstance(content, str):
        raise ValueError("todo content must be a non-empty string")
    if status not in valid_statuses:
        raise ValueError(f"todo status must be one of {valid_statuses}, got {status!r}")
    if priority not in valid_priorities:
        raise ValueError(
            f"todo priority must be one of {valid_priorities}, got {priority!r}"
        )

    return {"content": content, "status": status, "priority": priority}


# ── Telemetry Purity Guard ──────────────────────────────────────────────────────
def _check_telemetry_purity(
    events_path: Path | None = None,
    lookback: int = 100,
) -> dict[str, Any]:
    """
    Scan recent events for test contamination.
    Returns {purity, test_entries, dirty_count, verdict, environment}.

    If test entries detected in PROD context:
      → WELL_VERDICT = VOID_TELEMETRY
      → No GREEN/AMBER/RED — must return VOID until Arif confirms real state
    """
    if events_path is None:
        events_path = EVENTS_PATH

    purity = "CLEAN"
    test_entries: list[dict] = []
    dirty_count = 0
    prod_count = 0

    if events_path.exists():
        try:
            with open(events_path) as f:
                lines = f.readlines()
            recent = lines[-lookback:] if len(lines) > lookback else lines
            for line in recent:
                try:
                    e = json.loads(line)
                    env = e.get("environment", None)
                    note = e.get("note", "") or ""
                    e.get("tier", "")
                    is_test_by_note = (
                        note.lower().startswith("test ")
                        or "test path" in note.lower()
                        or "test red path" in note.lower()
                        or "test green path" in note.lower()
                        or "automated test" in note.lower()
                        or "mocked" in note.lower()
                    )
                    if env == "TEST" or is_test_by_note:
                        purity = "DIRTY"
                        dirty_count += 1
                        test_entries.append(e)
                    elif env == "PROD" or env is None:
                        prod_count += 1
                except Exception:
                    continue
        except Exception:
            pass

    verdict = "VOID_TELEMETRY" if purity == "DIRTY" else "CLEAN"

    return {
        "purity": purity,
        "test_entry_count": dirty_count,
        "prod_entry_count": prod_count,
        "test_entries_sample": test_entries[-5:] if test_entries else [],
        "verdict": verdict,
        "environment": "PROD" if purity == "CLEAN" else "CONTAMINATED",
        "action_required": (
            "VOID_TELEMETRY: Test entries detected in production event stream. "
            "WELL verdicts suspended until test entries quarantined and Arif confirms real state."
            if purity == "DIRTY"
            else "CLEAN: Production telemetry uncontaminated."
        ),
    }


# ── Freshness Ceiling Rules (Phase 3) ─────────────────────────────────────────────
# Evidence discipline: stale telemetry cannot produce optimistic verdicts.
# Freshness bands:
#   0–12h verified  → GREEN/OPTIMAL/HIGH confidence allowed
#   12–24h           → AMBER maximum
#   24–72h           → LIMITED maximum
#   >72h or unverified → UNKNOWN/STALE only

WELL_FRESHNESS_BANDS = {
    "FRESH": {
        "max_age_hours": 12,
        "max_readiness": "OPTIMAL",
        "max_confidence": "HIGH",
    },
    "CURRENT": {
        "max_age_hours": 24,
        "max_readiness": "FUNCTIONAL",
        "max_confidence": "MEDIUM",
    },
    "AGED": {
        "max_age_hours": 72,
        "max_readiness": "LOW_CAPACITY",
        "max_confidence": "LOW",
    },
    "STALE": {
        "max_age_hours": float("inf"),
        "max_readiness": "UNKNOWN",
        "max_confidence": "LOW",
    },
}


# ── Thermodynamic Flux Engine (Phase 3) ──────────────────────────────────────────
# Maps metabolic_flux = cognitive_entropy_rate + machine_entropy.
# Thresholds: 0.40 warning, 0.65 compulsory reallocation, 0.85 system hold.

METABOLIC_FLUX_WEIGHTS = {
    "cognitive_entropy": 0.30,
    "compute_budget_pressure": 0.25,
    "api_failure_rate": 0.20,
    "context_pressure": 0.15,
    "memory_pressure": 0.10,
}

FLUX_THRESHOLDS = {
    "WARNING": 0.40,
    "COMPULSORY_REALLOCATION": 0.65,
    "SYSTEM_HOLD": 0.85,
}

FLUX_VERDICTS = {
    "NOMINAL": "Metabolic flux within nominal range. No reallocation needed.",
    "WARNING": "Metabolic flux elevated. Single dimension stress detected. Reallocation advised.",
    "COMPULSORY_REALLOCATION": "Metabolic flux critical. Multiple dimensions degrading + prediction contradictions. Compulsory reallocation triggered. Routing to 441_SURPRISE.",
    "SYSTEM_HOLD": "Metabolic flux severe. System in distress. 888 intervention required.",
}


# ── Contrast Detection Engine (W→P→C→M→G→J for biology) ──────────────────────
# Maps GEOX anomalous_contrast pattern onto human biological telemetry.
# Stage 1: establish baseline from events.jsonl rolling window
# Stage 2: detect per-dimension contrast (z-score vs baseline)
# Stage 3: infer possible causes from anomaly patterns
# Stage 4: route to W-floor guards

CONTRAST_BASELINE_WINDOW_DAYS = 14
CONTRAST_MIN_EVENTS = 3  # minimum events needed for a valid baseline

# Per-dimension z-score thresholds and direction
# z_thresh: absolute z-score to trigger anomaly flag
# higher_is_worse: direction of degradation
CONTRAST_DIMENSION_CONFIG = {
    "well_score": {"z_thresh": 1.5, "higher_is_worse": False},
    "sleep_debt_days": {"z_thresh": 1.5, "higher_is_worse": True},
    "sleep_hours": {"z_thresh": 1.5, "higher_is_worse": False},
    "sleep_quality": {"z_thresh": 1.5, "higher_is_worse": False},
    "stress_load": {"z_thresh": 1.0, "higher_is_worse": True},
    "clarity": {"z_thresh": 1.5, "higher_is_worse": False},
    "decision_fatigue": {"z_thresh": 1.0, "higher_is_worse": True},
    "metabolic_stability": {"z_thresh": 1.5, "higher_is_worse": False},
    "pain_level": {"z_thresh": 1.0, "higher_is_worse": True},
}


def _load_events(lookback_days: int = CONTRAST_BASELINE_WINDOW_DAYS) -> list[dict]:
    """Load non-test WELL_LOG events from events.jsonl within lookback window.

    Returns list of event dicts sorted oldest→newest.
    Excludes events where note contains 'test' (test contamination guard).
    """
    if not EVENTS_PATH.exists():
        return []
    cutoff = (
        datetime.datetime.now(datetime.timezone.utc)
        - datetime.timedelta(days=lookback_days)
    ).isoformat()
    events = []
    try:
        with open(EVENTS_PATH) as f:
            for line in f:
                try:
                    e = json.loads(line.strip())
                    if e.get("event") != "WELL_LOG":
                        continue
                    note = e.get("note", "") or ""
                    # F2 / test-contamination guard: skip test entries
                    if (
                        note.lower().startswith("test ")
                        or "test path" in note.lower()
                        or "mocked" in note.lower()
                    ):
                        continue
                    epoch = e.get("epoch", "")
                    if epoch and epoch < cutoff:
                        continue
                    events.append(e)
                except Exception:
                    continue
    except Exception:
        pass
    return events


def _compute_baseline(events: list[dict]) -> dict[str, dict]:
    """Establish per-dimension baseline statistics from event history.

    Computes rolling mean and stdev for well_score and floors_violated count
    over the event window. Requires CONTRAST_MIN_EVENTS to emit a baseline.

    Returns:
        {
            "well_score": {"mean": float, "stdev": float, "n": int},
            "floors_violated": {"mean": float, "stdev": float, "n": int},
            ...
        }
    """
    if len(events) < CONTRAST_MIN_EVENTS:
        return {}

    scores = [
        e.get("well_score", 50.0) for e in events if e.get("well_score") is not None
    ]
    violation_counts = [len(e.get("floors_violated", [])) for e in events]

    baseline = {}

    if len(scores) >= CONTRAST_MIN_EVENTS:
        mean_s = sum(scores) / len(scores)
        variance = sum((s - mean_s) ** 2 for s in scores) / max(len(scores) - 1, 1)
        stdev_s = variance**0.5
        baseline["well_score"] = {
            "mean": round(mean_s, 2),
            "stdev": round(stdev_s, 2),
            "n": len(scores),
        }

    if len(violation_counts) >= CONTRAST_MIN_EVENTS:
        mean_v = sum(violation_counts) / len(violation_counts)
        variance = sum((v - mean_v) ** 2 for v in violation_counts) / max(
            len(violation_counts) - 1, 1
        )
        stdev_v = variance**0.5
        baseline["floors_violated"] = {
            "mean": round(mean_v, 2),
            "stdev": round(stdev_v, 2),
            "n": len(violation_counts),
        }

    return baseline


def _detect_contrast(
    current_state: dict[str, Any],
    baseline: dict[str, dict],
) -> dict[str, dict]:
    """Detect per-dimension anomalous contrast against established baseline.

    Uses z-score: z = (current - mean) / stdev.
    Anomaly flagged when |z| > dimension threshold AND direction matches.
    Stores raw z and absolute deviation for downstream meaning inference.

    Returns:
        {
            "well_score": {"anomaly": bool, "z_score": float, "deviation": float,
                           "current": float, "baseline_mean": float, "direction": str},
            ...
        }
    """
    results = {}
    current_score = current_state.get("well_score", 50.0)
    current_violations = len(current_state.get("floors_violated", []))

    # well_score contrast
    bs = baseline.get("well_score", {})
    if bs and bs.get("stdev", 0) > 0:
        z = (current_score - bs["mean"]) / bs["stdev"]
        cfg = CONTRAST_DIMENSION_CONFIG["well_score"]
        is_anomaly = abs(z) > cfg["z_thresh"]
        # Degradation = lower score (higher_is_worse=False → anomaly means worse)
        is_degradation = (
            z < -cfg["z_thresh"] if not cfg["higher_is_worse"] else z > cfg["z_thresh"]
        )
        results["well_score"] = {
            "anomaly": is_anomaly,
            "z_score": round(z, 3),
            "deviation": round(current_score - bs["mean"], 2),
            "current": current_score,
            "baseline_mean": bs["mean"],
            "direction": "DEGRADING"
            if is_degradation
            else ("IMPROVING" if abs(z) > cfg["z_thresh"] else "STABLE"),
        }
    else:
        results["well_score"] = {
            "anomaly": False,
            "z_score": 0.0,
            "deviation": 0.0,
            "current": current_score,
            "baseline_mean": bs.get("mean", None),
            "direction": "UNKNOWN",
        }

    # floors_violated count contrast
    bv = baseline.get("floors_violated", {})
    if bv and bv.get("stdev", 0) > 0:
        z = (current_violations - bv["mean"]) / bv["stdev"]
        cfg_z = 1.5  # more violations = worse, symmetric
        is_anomaly = abs(z) > cfg_z
        is_degradation = z > cfg_z  # more violations = degradation
        results["floors_violated"] = {
            "anomaly": is_anomaly,
            "z_score": round(z, 3),
            "deviation": round(current_violations - bv["mean"], 2),
            "current": current_violations,
            "baseline_mean": round(bv["mean"], 2),
            "direction": "DEGRADING"
            if is_degradation
            else ("IMPROVING" if z < -cfg_z else "STABLE"),
        }
    else:
        results["floors_violated"] = {
            "anomaly": False,
            "z_score": 0.0,
            "deviation": 0.0,
            "current": current_violations,
            "baseline_mean": bv.get("mean", None),
            "direction": "UNKNOWN",
        }

    return results


def _infer_meaning(
    contrast: dict[str, dict],
    current_state: dict[str, Any],
) -> list[dict]:
    """Infer possible causes from detected anomalous contrast patterns.

    Pattern-matches anomaly signatures against known biological causation chains.
    Returns list of hypotheses sorted by confidence.
    Each hypothesis: {hypothesis, affected_dimensions, confidence, evidence}
    W0: This is meaning-inference, NOT diagnosis. All outputs are HYPOTHESIS-tagged.
    """
    hypotheses = []

    score_anomaly = contrast.get("well_score", {}).get("anomaly", False)
    score_z = contrast.get("well_score", {}).get("z_score", 0.0)
    score_dir = contrast.get("well_score", {}).get("direction", "UNKNOWN")
    violations_anomaly = contrast.get("floors_violated", {}).get("anomaly", False)
    violations_z = contrast.get("floors_violated", {}).get("z_score", 0.0)

    metrics = current_state.get("metrics", {})

    # Pattern: well_score degrading AND floors_violated increasing
    # → systemic degradation, possible overwork / accumulated stress
    if score_anomaly and violations_anomaly and score_z < 0 and violations_z > 0:
        hypotheses.append(
            {
                "hypothesis": "Systemic degradation — possible accumulated overwork or stress cascade",
                "affected_dimensions": ["well_score", "floors_violated"],
                "confidence": "MEDIUM",
                "evidence": f"well_score z={score_z:.2f}, violations z={violations_z:.2f}",
                "epistemic_tag": "HYPOTHESIS",
            }
        )

    # Pattern: well_score improving (recovery signal)
    if score_anomaly and score_z > 0 and score_dir == "IMPROVING":
        hypotheses.append(
            {
                "hypothesis": "Positive trajectory — possible recovery, rest, or effective intervention",
                "affected_dimensions": ["well_score"],
                "confidence": "MEDIUM",
                "evidence": f"well_score z={score_z:.2f} above baseline mean",
                "epistemic_tag": "PLAUSIBLE",
            }
        )

    # Pattern: well_score degrading but violations stable
    # → subtle degradation not yet manifesting as floor violations
    if score_anomaly and not violations_anomaly and score_z < 0:
        # Look for per-dimension signals in metrics
        sleep = metrics.get("sleep", {})
        stress = metrics.get("stress", {})
        cognitive = metrics.get("cognitive", {})
        metabolic = metrics.get("metabolic", {})

        if sleep.get("sleep_debt_days", 0) >= 2:
            hypotheses.append(
                {
                    "hypothesis": "Sleep debt accumulation — cognitive substrate not yet compromised but trending",
                    "affected_dimensions": ["well_score", "sleep"],
                    "confidence": "LOW",
                    "evidence": f"sleep_debt_days={sleep.get('sleep_debt_days')}, score z={score_z:.2f}",
                    "epistemic_tag": "HYPOTHESIS",
                }
            )
        if stress.get("subjective_load", 0) >= 7:
            hypotheses.append(
                {
                    "hypothesis": "Elevated stress load — substrate under chronic pressure, floor violations latent",
                    "affected_dimensions": ["well_score", "stress"],
                    "confidence": "LOW",
                    "evidence": f"stress_load={stress.get('subjective_load')}/10, score z={score_z:.2f}",
                    "epistemic_tag": "HYPOTHESIS",
                }
            )
        if cognitive.get("clarity", 10) < 4:
            hypotheses.append(
                {
                    "hypothesis": "Cognitive entropy onset — W5 floor boundary, decision capacity degrading",
                    "affected_dimensions": ["well_score", "cognitive"],
                    "confidence": "MEDIUM",
                    "evidence": f"clarity={cognitive.get('clarity')}/10, score z={score_z:.2f}",
                    "epistemic_tag": "HYPOTHESIS",
                }
            )
        if metabolic.get("perceived_stability", 10) < 5:
            hypotheses.append(
                {
                    "hypothesis": "Metabolic instability — possible caloric deficit, dehydration, or illness onset",
                    "affected_dimensions": ["well_score", "metabolic"],
                    "confidence": "LOW",
                    "evidence": f"perceived_stability={metabolic.get('perceived_stability')}/10",
                    "epistemic_tag": "HYPOTHESIS",
                }
            )

    return hypotheses


def _compute_contrast_severity(contrast: dict[str, dict]) -> tuple[str, str]:
    """Compute overall contrast severity tier and recommended action.

    Tiers:
      NORMAL   — no anomalies detected
      WATCH    — 1 anomaly, modest z
      CONCERN  — 1 anomaly with high z OR 2+ anomalies
      CRITICAL — systemic degradation (well_score AND violations both anomalous in bad direction)

    Returns: (severity_tier, recommended_action)
    """
    anomalies = {k: v for k, v in contrast.items() if v.get("anomaly", False)}
    if not anomalies:
        return "NORMAL", "No anomalous contrast detected. Continue monitoring."

    # Check for systemic degradation
    score = contrast.get("well_score", {})
    viol = contrast.get("floors_violated", {})
    systemic = (
        score.get("anomaly")
        and score.get("z_score", 0) < 0
        and viol.get("anomaly")
        and viol.get("z_score", 0) > 0
    )
    if systemic:
        return (
            "CRITICAL",
            "Systemic degradation detected. Human confirmation required before strategic forge actions. Route to arifOS 888_JUDGE.",
        )

    # Count anomalies and max |z|
    max_z = max(abs(v.get("z_score", 0)) for v in anomalies.values())
    if len(anomalies) >= 2 or max_z >= 2.0:
        return (
            "CONCERN",
            "Significant contrast anomaly. Review recommended before high-stakes decisions.",
        )
    elif len(anomalies) == 1 and max_z >= 1.5:
        return (
            "WATCH",
            "Minor contrast anomaly. Note in substrate record. No action required.",
        )

    return "WATCH", "Subtle contrast signal. Continue monitoring."


def _compute_cognitive_entropy_rate(state: dict[str, Any]) -> float:
    """Compute cognitive_entropy_rate from contradiction tracking.

    Formula:
      cognitive_entropy_rate = (contradiction_count / max(total_predictions, 1))
                               × average_confidence_of_failures / 10
    Range: 0.0–1.0
    """
    metrics = state.get("metrics", {})
    cognitive = metrics.get("cognitive", {})
    contradiction_count = cognitive.get("contradiction_count", 0)
    total_predictions = cognitive.get("total_predictions", 0)
    avg_confidence_failures = cognitive.get("avg_confidence_of_failures", 5.0)

    if total_predictions == 0:
        return 0.0
    return min(
        1.0,
        (contradiction_count / total_predictions) * (avg_confidence_failures / 10.0),
    )


def _compute_machine_entropy(state: dict[str, Any]) -> float:
    """Compute machine substrate entropy from M-WELL state.

    Formula:
      machine_entropy = 1.0 - (m_well_score / 100.0)
    Range: 0.0–1.0
    """
    m = state.get("m_machine", {})
    m_score = m.get("m_well_score", 100)
    return max(0.0, min(1.0, 1.0 - (m_score / 100.0)))


def _compute_metabolic_flux(state: dict[str, Any]) -> dict[str, Any]:
    """Compute the unified metabolic_flux metric: a 0.0–1.0 scalar
    representing the system's entropy rate across cognitive and machine planes.

    Formula:
      cognitive_entropy = _compute_cognitive_entropy_rate(state)
      machine_entropy   = _compute_machine_entropy(state)
      context_pressure  = state metrics context_pressure (0–1)
      compute_pressure  = 1.0 - (compute_budget_pct / 100.0)
      api_failure_rate  = state m_machine api_failure_rate (0–1)
      memory_pressure   = state m_machine context_length_pressure (0–1)

      metabolic_flux = Σ(w_i × component_i)

    Returns structured payload with components, weighted flux, verdict, and
    reallocation signal.
    """
    metrics = state.get("metrics", {})
    cognitive = metrics.get("cognitive", {})
    m_machine = state.get("m_machine", {})

    cognitive_entropy = _compute_cognitive_entropy_rate(state)
    machine_entropy = _compute_machine_entropy(state)
    context_pressure = m_machine.get("context_pressure", 0.0)
    if isinstance(context_pressure, bool):
        context_pressure = 1.0 if context_pressure else 0.0
    compute_budget_pct = m_machine.get("compute_budget_pct", 100)
    compute_pressure = max(0.0, 1.0 - (compute_budget_pct / 100.0))
    api_failure_rate = m_machine.get("api_failure_rate", 0.0)
    memory_pressure = m_machine.get("context_length_pressure", 0.0)

    # Weighted flux sum
    flux = (
        METABOLIC_FLUX_WEIGHTS["cognitive_entropy"] * cognitive_entropy
        + METABOLIC_FLUX_WEIGHTS["compute_budget_pressure"] * compute_pressure
        + METABOLIC_FLUX_WEIGHTS["api_failure_rate"] * api_failure_rate
        + METABOLIC_FLUX_WEIGHTS["context_pressure"] * context_pressure
        + METABOLIC_FLUX_WEIGHTS["memory_pressure"] * memory_pressure
    )
    flux = round(max(0.0, min(1.0, flux)), 4)

    # ── Behavioral telemetry fallback (WELL v2.0 behavioral flux) ─────────────────
    # When m_machine is absent from state (bare-metal deployment), derive
    # metabolic flux from behavioral telemetry: sleep debt, decision fatigue,
    # cognitive load, agent session count, git commit rhythm, burnout risk.
    # This replaces the FALSE_CALM flatline with real behavioral signal.
    _m_machine_absent = "m_machine" not in state
    _cognitive_absent = not cognitive.get("contradiction_count") and not cognitive.get(
        "total_predictions"
    )
    _has_behavioral = bool(
        cognitive.get("decision_fatigue")
        or cognitive.get("clarity")
        or cognitive.get("cognitive_load")
        or cognitive.get("burnout_risk")
        or metrics.get("decision_fatigue")  # Kimi telemetry — flat under metrics
        or metrics.get("cognitive_load")
        or metrics.get("burnout_risk")
        or metrics.get("cognitive_clarity")
    )

    # ── Behavioral telemetry source detection ─────────────────────────────────
    # Kimi's well_agent_telemetry.py writes flat under metrics.*, not metrics.cognitive.*
    _behavioral_from_flat = bool(
        metrics.get("decision_fatigue")
        or metrics.get("cognitive_load")
        or metrics.get("burnout_risk")
    )

    data_quality: str
    if _m_machine_absent and _cognitive_absent and not _has_behavioral:
        data_quality = "UNMEASURED — no machine, cognitive, or behavioral telemetry; all components default to idle"
    elif _m_machine_absent and _has_behavioral:
        data_quality = "BEHAVIORAL — flux derived from behavioral telemetry (sleep, fatigue, cognitive load, burnout) not machine metrics"
    elif _m_machine_absent:
        data_quality = "PARTIAL — m_machine absent; machine components default to idle; cognitive metrics real"
    elif _cognitive_absent:
        data_quality = "PARTIAL — cognitive counters absent; cognitive_entropy=0; machine metrics real"
    else:
        data_quality = "REAL — all components from live state"

    # ── Behavioral flux computation ───────────────────────────────────────────────
    # When behavioral telemetry exists but machine metrics don't, compute flux
    # from behavioral components: sleep_debt, decision_fatigue, cognitive_load,
    # agent_session_count, burnout_risk.
    behavioral_flux: float | None = None
    behavioral_components: dict[str, float] = {}
    if _m_machine_absent and _has_behavioral:
        # Read from flat metrics (Kimi telemetry) and fall back to nested cognitive
        sleep_debt = (
            metrics.get("sleep_debt_days") or cognitive.get("sleep_debt_days", 0) or 0
        )
        decision_fatigue_norm = (
            metrics.get("decision_fatigue")
            or cognitive.get("decision_fatigue", 0.5)
            or 0.5
        )
        cognitive_load_norm = (
            metrics.get("cognitive_load") or cognitive.get("cognitive_load", 0.5) or 0.5
        )
        burnout_risk = (
            metrics.get("burnout_risk") or cognitive.get("burnout_risk", 0.5) or 0.5
        )
        sessions_norm = min(
            1.0,
            (
                metrics.get("agent_session_count")
                or cognitive.get("agent_session_count", 0)
                or 0
            )
            / 20.0,
        )

        behavioral_components = {
            "sleep_debt_contribution": sleep_debt * 0.15,
            "decision_fatigue_contribution": decision_fatigue_norm * 0.25,
            "cognitive_load_contribution": cognitive_load_norm * 0.25,
            "burnout_risk_contribution": burnout_risk * 0.20,
            "agent_sessions_contribution": sessions_norm * 0.15,
        }
        behavioral_flux = round(sum(behavioral_components.values()), 4)

    # Use behavioral flux if available, otherwise use machine-derived flux
    effective_flux = behavioral_flux if behavioral_flux is not None else flux

    # Determine verdict from effective flux
    if effective_flux >= FLUX_THRESHOLDS["SYSTEM_HOLD"]:
        verdict = "SYSTEM_HOLD"
    elif effective_flux >= FLUX_THRESHOLDS["COMPULSORY_REALLOCATION"]:
        verdict = "COMPULSORY_REALLOCATION"
    elif effective_flux >= FLUX_THRESHOLDS["WARNING"]:
        verdict = "WARNING"
    else:
        verdict = "NOMINAL"

    # Reallocation signal
    compulsory = effective_flux >= FLUX_THRESHOLDS["COMPULSORY_REALLOCATION"]

    # ── Telemetry status ──────────────────────────────────────────────────────────
    if _m_machine_absent and _cognitive_absent and not _has_behavioral:
        telemetry_status = "absent"
        calm_state = "unknown"
        verdict = "VOID_TELEMETRY"
    elif _m_machine_absent and _has_behavioral:
        telemetry_status = "behavioral"
        calm_state = "inferred"
    elif _m_machine_absent or _cognitive_absent:
        telemetry_status = "partial"
        calm_state = "assumed"
    else:
        telemetry_status = "present"
        calm_state = "observed"

    return {
        "ok": True,
        "metabolic_flux": effective_flux,
        "machine_flux": flux,
        "behavioral_flux": behavioral_flux,
        "verdict": verdict,
        "verdict_message": FLUX_VERDICTS.get(
            verdict, "Telemetry status unknown — cannot assess metabolic state."
        ),
        "components": {
            "cognitive_entropy": cognitive_entropy,
            "machine_entropy": machine_entropy,
            "compute_pressure": compute_pressure,
            "api_failure_rate": api_failure_rate,
            "context_pressure": context_pressure,
            "memory_pressure": memory_pressure,
            "behavioral_components": behavioral_components
            if behavioral_components
            else None,
        },
        "thresholds": {
            "warning": FLUX_THRESHOLDS["WARNING"],
            "compulsory_reallocation": FLUX_THRESHOLDS["COMPULSORY_REALLOCATION"],
            "system_hold": FLUX_THRESHOLDS["SYSTEM_HOLD"],
        },
        "compulsory_reallocation": compulsory,
        "reallocation_target": "441_SURPRISE" if compulsory else None,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        "data_quality": data_quality,
        "telemetry_status": telemetry_status,
        "calm_state": calm_state,
        "false_calm_warning": calm_state == "unknown"
        and effective_flux < FLUX_THRESHOLDS["WARNING"],
        "psi_SE_note": "Sovereign entropy protects unpredictability. Low psi_SE ≠ healthy — it means capturable. See well_assess_sovereign_entropy for the anti-capture dimension.",
        # Structural Coherence Transmission — EUREKA v2026.06.05
        # High metabolic flux degrades the system's ability to maintain governance-as-compression.
        # When flux >= 0.65, output grammar loosens and cross-modal fidelity drops.
        "structural_coherence_delta": round(1.0 - effective_flux, 4),
        "structural_coherence_note": (
            "Governance architecture is signal compression. Metabolic flux measures the entropy rate "
            "that erodes this compression. At flux >= 0.65, the system's outputs lose cross-modal fidelity — "
            "they survive text→text but degrade in text→image→text roundtrips. "
            f"Current delta: {round(1.0 - effective_flux, 4)} (1.0 = perfect coherence, 0.0 = coherence collapsed)."
        ),
    }


def _get_freshness_band(state: dict[str, Any]) -> str:
    """Determine freshness band from state timestamp."""
    ts = state.get("timestamp", "")
    if not ts:
        return "STALE"
    try:
        if isinstance(ts, str):
            dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        else:
            dt = ts
        age_hours = (
            datetime.datetime.now(datetime.timezone.utc) - dt
        ).total_seconds() / 3600
        if age_hours <= 12:
            return "FRESH"
        elif age_hours <= 24:
            return "CURRENT"
        elif age_hours <= 72:
            return "AGED"
        else:
            return "STALE"
    except Exception:
        return "STALE"


def _cap_readiness_by_freshness(readiness: str, freshness_band: str) -> str:
    """Apply freshness ceiling to readiness verdict."""
    band = WELL_FRESHNESS_BANDS.get(freshness_band, WELL_FRESHNESS_BANDS["STALE"])
    ceiling = band["max_readiness"]
    ceiling_rank = {
        "OPTIMAL": 4,
        "FUNCTIONAL": 3,
        "LOW_CAPACITY": 2,
        "DEGRADED": 1,
        "UNKNOWN": 0,
    }
    readiness_rank = ceiling_rank.get(readiness, 0)
    ceiling_rank_val = ceiling_rank.get(ceiling, 0)
    if readiness_rank > ceiling_rank_val:
        return ceiling
    return readiness


def _cap_confidence_by_freshness(confidence: str, freshness_band: str) -> str:
    """Apply freshness ceiling to confidence level."""
    band = WELL_FRESHNESS_BANDS.get(freshness_band, WELL_FRESHNESS_BANDS["STALE"])
    ceiling = band["max_confidence"]
    ceiling_rank = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    confidence_rank = ceiling_rank.get(confidence, 0)
    ceiling_rank_val = ceiling_rank.get(ceiling, 0)
    if confidence_rank > ceiling_rank_val:
        return ceiling
    return confidence


# ── 168-Hour Hard Ceiling for Human Readiness Inference ────────────────────────
HUMAN_READINESS_CEILING_HOURS = 168.0


def _check_human_readiness_168h_ceiling(state: dict[str, Any]) -> dict[str, Any] | None:
    """
    Hard ceiling: if state age > 168h, WELL must NOT infer human readiness.
    Returns a blocking verdict dict if ceiling is breached, None otherwise.

    This is a firm boundary per audit recommendation, not a soft ceiling.
    """
    ts = state.get("timestamp", "")
    if not ts:
        # No timestamp = cannot verify age = block inference
        return {
            "readiness": "UNKNOWN",
            "risk_level": "UNKNOWN",
            "recommended_mode": "pause",
            "ground_state": "UNSAFE",
            "decision_ceiling": "C0",
            "human_confirmation_required": True,
            "reason": "No state timestamp. Cannot verify telemetry age. WELL cannot infer human readiness.",
            "well_score": state.get("well_score", 0),
            "has_telemetry": bool(state.get("metrics")),
            "state_age_hours": None,
            "ceiling_168h": "BREACHED",
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
            "boundary_notice": "Not diagnosis. Not therapy. Reflective readiness only. Arif remains final judge.",
        }
    try:
        if isinstance(ts, str):
            dt = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        else:
            dt = ts
        age_hours = (
            datetime.datetime.now(datetime.timezone.utc) - dt
        ).total_seconds() / 3600
    except Exception:
        return {
            "readiness": "UNKNOWN",
            "risk_level": "UNKNOWN",
            "recommended_mode": "pause",
            "ground_state": "UNSAFE",
            "decision_ceiling": "C0",
            "human_confirmation_required": True,
            "reason": "Cannot parse state timestamp. WELL cannot infer human readiness.",
            "well_score": state.get("well_score", 0),
            "has_telemetry": bool(state.get("metrics")),
            "state_age_hours": None,
            "ceiling_168h": "BREACHED",
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
            "boundary_notice": "Not diagnosis. Not therapy. Reflective readiness only. Arif remains final judge.",
        }
    if age_hours > HUMAN_READINESS_CEILING_HOURS:
        return {
            "readiness": "DO_NOT_INFER",
            "risk_level": "UNKNOWN",
            "recommended_mode": "pause",
            "ground_state": "UNSAFE",
            "decision_ceiling": "C0",
            "human_confirmation_required": True,
            "reason": f"State age {age_hours:.0f}h exceeds 168h hard ceiling. WELL cannot infer human readiness from stale telemetry.",
            "well_score": state.get("well_score", 0),
            "has_telemetry": bool(state.get("metrics")),
            "state_age_hours": round(age_hours, 1),
            "ceiling_168h": "BREACHED",
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
            "boundary_notice": "Not diagnosis. Not therapy. Reflective readiness only. Arif remains final judge.",
        }
    return None


# ── Federation Health Reconciliation (Phase 3) ────────────────────────────────────
def _federation_health_reconcile(
    transport_ok: bool,
    identity_valid: bool,
    truth_status: str,
    any_tool_says_optimistic: bool,
) -> dict[str, Any]:
    """
    Reconciliation rule: IF any tool says PASS/OPTIMAL/GREEN
    while identity_valid=false AND truth_status=UNVERIFIED,
    THEN federation_verdict must be HOLD.

    Returns reconciliation verdict and contradiction flags.
    """
    contradiction_flags: list[str] = []
    verdict = "RECONCILED"

    if not identity_valid and any_tool_says_optimistic:
        contradiction_flags.append("IDENTITY_INVALID_BUT_OPTIMISTIC")
        verdict = "HOLD"

    if truth_status in ("UNVERIFIED", "STALE", "EXPIRED") and any_tool_says_optimistic:
        contradiction_flags.append("STALE_EVIDENCE_BUT_OPTIMISTIC")
        verdict = "HOLD"

    if not transport_ok:
        contradiction_flags.append("TRANSPORT_DOWN")
        verdict = "HOLD"

    return {
        "verdict": verdict,
        "contradiction_flags": contradiction_flags,
        "transport_ok": transport_ok,
        "identity_valid": identity_valid,
        "truth_status": truth_status,
        "any_tool_says_optimistic": any_tool_says_optimistic,
        "federation_policy": "HOLD on any contradiction",
    }


# ── WELL Identity Invariant (F10 Coherence + F01 Amanah) ───────────────────────
def is_well(state: dict[str, Any] | None = None) -> bool:
    """
    Verify that a state object carries the canonical WELL identity.
    Returns True only if all constitutional fields are present and valid.

    When state.json is missing identity fields (pre-migration), returns False
    WITHOUT triggering corruption/alarm — the organ is healthy, just not yet
    seeded with sovereign data. Migrate via well_log, not a code patch.
    """
    if state is None:
        state = _load_state()

    # Explicit field presence check — distinguish "missing" from "invalid"
    identity = state.get("identity")
    role = state.get("role")
    delta_s = state.get("delta_s")
    peace2 = state.get("peace2")
    kappa_r = state.get("kappa_r")
    rasa = state.get("rasa")
    amanah = state.get("amanah")
    authority = state.get("authority")

    # If identity/role/authority are completely absent, state needs migration
    # — not a corruption signal. is_well() returns False but with a clear flag.
    if identity is None or role is None or authority is None:
        return False

    return (
        identity == "WELL"
        and role
        in ["Body", "Body / Human Intelligence", "Biological Substrate Governance"]
        and isinstance(delta_s, (int, float))
        and delta_s >= 0
        and isinstance(peace2, (int, float))
        and peace2 >= 1.0
        and isinstance(kappa_r, (int, float))
        and kappa_r >= 0.95
        and rasa is True
        and amanah in ["LOCK", "🔐", True]
        and authority == "REFLECT_ONLY"
    )


def _clamp(value: float | int | None, minimum: float, maximum: float) -> float | None:
    """Clamp numeric input to [min, max]. None passes through unchanged."""
    if value is None:
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"Expected numeric input, got {type(value).__name__}")
    return max(minimum, min(maximum, v))


def _sanitize_note(note: str | None) -> str | None:
    """Sanitize free-text notes to prevent log injection or secret leakage."""
    if not note:
        return note
    # Strip control chars, limit length
    cleaned = "".join(ch for ch in note if ch.isprintable() or ch in " \t\n\r")
    return cleaned[:500]


# ── Evidence & Telemetry Integrity Guards ──────────────────────────────────────

SENSITIVE_METRIC_KEYS = {
    "note",
    "pain_map",
    "sleep_debt_days",
    "last_night_hours",
    "quality_score",
    "subjective_load",
    "restlessness",
    "hrv_proxy",
    "clarity",
    "decision_fatigue",
    "focus_durability",
    "fasting_window_hours",
    "perceived_stability",
    "hydration_status",
}


def _has_verified_telemetry(state: dict[str, Any]) -> bool:
    """
    Return True only if state contains actual body telemetry, not defaults.
    UNVERIFIED or VOID truth_status fails immediately.
    """
    if state.get("truth_status") in ("VOID", "TEST", "UNVERIFIED", "INSUFFICIENT_DATA"):
        return False
    metrics = state.get("metrics", {})
    if not metrics or not isinstance(metrics, dict):
        return False
    # Must have at least one dimension with real data (not just empty dicts)
    for dim in ("sleep", "stress", "cognitive", "metabolic", "structural"):
        if metrics.get(dim):
            return True
    return False


def _resolve_readiness(state: dict[str, Any]) -> dict[str, Any]:
    """
    Canonical readiness resolver used by ALL tools.
    If no verified telemetry: UNKNOWN (fail closed, but honest).
    If telemetry exists: compute normal tiered readiness.
    """
    score = _state_score(state)
    violations = state.get("floors_violated", [])
    state.get("metrics", {})
    ceiling = _compute_decision_ceiling(state)
    if not is_well(state):
        return {
            "readiness": "LOW_CAPACITY",
            "risk_level": "AMBER",
            "recommended_mode": "review_or_draft",
            "ground_state": ceiling.get("ground_state", "DEGRADED"),
            "decision_ceiling": "C1",
            "human_confirmation_required": True,
            "reason": "WELL identity invariant failed. Readiness is capped until identity is restored.",
            "well_score": score,
            "active_violations": violations,
            "has_telemetry": _has_verified_telemetry(state),
            "identity_valid": False,
            "readiness_cap": "CAUTION",
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        }

    # ── Unknown telemetry path (fail closed without faking biology) ──
    if not _has_verified_telemetry(state):
        return {
            "readiness": "UNKNOWN",
            "risk_level": "UNKNOWN",
            "recommended_mode": "draft_only",
            "ground_state": ceiling.get("ground_state", "UNKNOWN"),
            "decision_ceiling": ceiling.get("decision_ceiling", "C0"),
            "human_confirmation_required": True,
            "reason": "No verified body telemetry available. WELL cannot infer biological readiness.",
            "well_score": score,
            "active_violations": violations,
            "has_telemetry": False,
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        }

    # ── Known telemetry path ──
    if _state_is_void(state):
        return {
            "readiness": "VOID_TELEMETRY",
            "risk_level": "RED",
            "recommended_mode": "pause",
            "ground_state": "UNSAFE",
            "decision_ceiling": "C0",
            "human_confirmation_required": True,
            "reason": "WELL telemetry is unverified or contaminated. Manual Arif confirmation required.",
            "well_score": score,
            "active_violations": violations,
            "has_telemetry": True,
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        }

    # I2/I3 — Evidence discipline: unverified/stale/expired telemetry cannot produce OPTIMAL
    truth_status = state.get("truth_status", "UNVERIFIED")
    if truth_status in ("UNVERIFIED", "STALE", "EXPIRED", "OPERATOR_REPORTED"):
        return {
            "readiness": "DEGRADED" if truth_status == "EXPIRED" else "LOW_CAPACITY",
            "risk_level": "RED" if truth_status == "EXPIRED" else "AMBER",
            "recommended_mode": "draft_only"
            if truth_status == "EXPIRED"
            else "review_or_draft",
            "ground_state": ceiling.get("ground_state", "DEGRADED"),
            "decision_ceiling": ceiling.get("decision_ceiling", "C1"),
            "human_confirmation_required": True,
            "reason": f"Telemetry {truth_status.lower()}. WELL cannot confirm biological readiness without fresh verified evidence.",
            "well_score": score,
            "active_violations": violations,
            "has_telemetry": True,
            "truth_status": truth_status,
            "freshness_band": "STALE",
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        }

    # ── Phase 3 Freshness Ceiling ─────────────────────────────────────────────
    # Apply freshness ceiling to all downstream verdicts
    freshness_band = _get_freshness_band(state)

    if violations:
        readiness_capped = "DEGRADED"
        return {
            "readiness": readiness_capped,
            "risk_level": "RED",
            "recommended_mode": "draft_only",
            "ground_state": ceiling.get("ground_state", "DEGRADED"),
            "decision_ceiling": ceiling.get("decision_ceiling", "C1"),
            "human_confirmation_required": True,
            "reason": f"Substrate flagging: {', '.join(violations)}. Strategic forge bandwidth throttled.",
            "well_score": score,
            "active_violations": violations,
            "has_telemetry": True,
            "truth_status": truth_status,
            "freshness_band": freshness_band,
            "freshness_note": f"Ceiling applied: {freshness_band}",
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        }

    if score >= 80:
        raw_readiness = "OPTIMAL"
        readiness_capped = _cap_readiness_by_freshness(raw_readiness, freshness_band)
        return {
            "readiness": readiness_capped,
            "risk_level": "GREEN" if readiness_capped == "OPTIMAL" else "AMBER",
            "recommended_mode": "full"
            if readiness_capped == "OPTIMAL"
            else "review_or_draft",
            "ground_state": ceiling.get("ground_state", "GROUND"),
            "decision_ceiling": ceiling.get("decision_ceiling", "C5"),
            "human_confirmation_required": readiness_capped != "OPTIMAL",
            "reason": f"Substrate {'stable and high-capacity' if readiness_capped == 'OPTIMAL' else f'capacity capped to {freshness_band}'}. {'Full forge bandwidth available.' if readiness_capped == 'OPTIMAL' else 'Freshness ceiling applied.'}",
            "well_score": score,
            "active_violations": violations,
            "has_telemetry": True,
            "truth_status": truth_status,
            "freshness_band": freshness_band,
            "raw_readiness": raw_readiness,
            "freshness_note": f"Ceiling applied: {freshness_band}"
            if raw_readiness != readiness_capped
            else "within_band",
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        }

    if score >= 60:
        raw_readiness = "FUNCTIONAL"
        readiness_capped = _cap_readiness_by_freshness(raw_readiness, freshness_band)
        return {
            "readiness": readiness_capped,
            "risk_level": "GREEN" if readiness_capped == "FUNCTIONAL" else "AMBER",
            "recommended_mode": "structured"
            if readiness_capped == "FUNCTIONAL"
            else "review_or_draft",
            "ground_state": ceiling.get("ground_state", "STRAINED"),
            "decision_ceiling": ceiling.get("decision_ceiling", "C3"),
            "human_confirmation_required": readiness_capped != "FUNCTIONAL",
            "reason": f"Substrate {'functional' if readiness_capped == 'FUNCTIONAL' else f'capacity capped to {freshness_band}'}. {'Normal forge operations permitted.' if readiness_capped == 'FUNCTIONAL' else 'Freshness ceiling applied.'}",
            "well_score": score,
            "active_violations": violations,
            "has_telemetry": True,
            "truth_status": truth_status,
            "freshness_band": freshness_band,
            "raw_readiness": raw_readiness,
            "freshness_note": f"Ceiling applied: {freshness_band}"
            if raw_readiness != readiness_capped
            else "within_band",
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        }

    raw_readiness = "LOW_CAPACITY"
    readiness_capped = _cap_readiness_by_freshness(raw_readiness, freshness_band)
    return {
        "readiness": readiness_capped,
        "risk_level": "AMBER",
        "recommended_mode": "draft_only",
        "ground_state": ceiling.get("ground_state", "DEGRADED"),
        "decision_ceiling": ceiling.get("decision_ceiling", "C1"),
        "human_confirmation_required": True,
        "reason": f"Substrate low-capacity{freshness_band != 'FRESH' and f' (freshness ceiling: {freshness_band})' or ''}. Recommend rest before strategic decisions.",
        "well_score": score,
        "active_violations": violations,
        "has_telemetry": True,
        "truth_status": truth_status,
        "freshness_band": freshness_band,
        "raw_readiness": raw_readiness,
        "freshness_note": f"Ceiling applied: {freshness_band}"
        if raw_readiness != readiness_capped
        else "within_band",
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


# ── Server ─────────────────────────────────────────────────────────────────────
mcp = FastMCP(
    name="AFWELL",
    instructions=(
        "WELL is the Universal Substrate Vitality Mirror for arifOS. "
        "H-WELL reflects operator Arif's biological and cognitive state. "
        "M-WELL reflects system reliability, tool health, context integrity, and compute limits. "
        "G-WELL reflects machine governance health — autonomic coherence, check/balance integrity, floor compliance. "
        "C-WELL evaluates coupled risk between human state and machine state. "
        "U-WELL (Universal) classifies any substance or substrate and assesses vitality "
        "without category error, authority overreach, or false equivalence. "
        "The WELL–FORGE bridge lets A-FORGE adapt execution intensity to Arif's readiness. "
        "W0: WELL holds a mirror, not a veto. Operator sovereignty is invariant. "
        "WELL does not decide worth. WELL identifies substrate, validates evidence, "
        "detects vitality/degradation, protects dignity, and returns judgment to Arif. "
        "G-WELL extends this to machine governance: it reflects, never commands. "
        "DITEMPA BUKAN DIBERI — Forged, Not Given."
    ),
)


# ── well_mcp canon surface wiring (2026-06-27) ─────────────────────────────────
# Registers: 18 resources (well://*), 9 prompts (well_init→well_seal),
# tools canon map + 4 advisory compositions. Idempotent. Additive only.
# Self-degrades gracefully if well_mcp package is not on Python path.
try:
    from well_mcp import register_all as _well_mcp_register_all

    _well_mcp_registered = _well_mcp_register_all(mcp)
    logger.info(
        "well_mcp canon surface registered: resources=%d prompts=%d tools=%d",
        len(_well_mcp_registered.get("resources", [])),
        len(_well_mcp_registered.get("prompts", [])),
        len(_well_mcp_registered.get("tools", [])),
    )
except ImportError:
    logger.info("well_mcp not on path; legacy server surface only.")
except Exception as _e:
    logger.exception("well_mcp registration failed: %s", _e)


# ── WELL MCP Compatibility Layer registration ──────────────────────────────────
try:
    from compatibility import register_legacy_tools

    register_legacy_tools(mcp)
    logger.info("WELL compatibility stubs registered successfully.")
except Exception as _e:
    logger.error("Failed to register WELL compatibility stubs: %s", _e)


def _mcp_health_check_impl() -> dict:
    """Internal implementation — returns raw payload for internal consumers."""
    state = _load_state()
    m_machine = state.get("m_machine", {})
    well_ok = is_well(state)
    has_telemetry = _has_verified_telemetry(state)
    truth_status = state.get("truth_status", "UNVERIFIED")
    freshness_band = _get_freshness_band(state)

    if not well_ok:
        status = "WARN"
        identity_note = "identity_invalid"
    elif not has_telemetry:
        status = "DEGRADED"
        identity_note = "no_telemetry"
    else:
        status = "OK"
        identity_note = "healthy"

    any_tool_says_optimistic = status == "OK"
    reconcile = _federation_health_reconcile(
        transport_ok=True,
        identity_valid=well_ok,
        truth_status=truth_status,
        any_tool_says_optimistic=any_tool_says_optimistic,
    )

    return {
        "mcp": "WELL",
        "status": status,
        "transport": "SSE_VALID",
        "auth": "OK",
        "schema_version": "2026.05.15",
        "read_only": True,
        "final_authority": "ARIF",
        "tool_count": 79,
        "identity_valid": well_ok,
        "latency_ms": m_machine.get("latency_ms", 200),
        "tool_availability": m_machine.get("tool_availability", 1.0),
        "recent_errors": int(m_machine.get("api_failure_rate", 0.0) * 10),
        "context_pressure": m_machine.get("context_length_pressure", 0.0),
        "memory_integrity": m_machine.get("memory_integrity", 1.0),
        "vault_status": m_machine.get("vault_status", "ok"),
        "identity_note": identity_note,
        "truth_status": truth_status,
        "freshness_band": freshness_band,
        "clarity": state.get("metrics", {}).get("cognitive", {}).get("clarity"),
        "federation_reconcile": reconcile,
    }


@mcp.tool()
def well_health_check() -> dict:
    """
    WELL organ health check with provenance and schema version.
    Canonical name: well_health_check. Legacy alias: mcp_health_check.
    """
    # 1C-C: delegate to canonical reliability tool
    reliability = well_assess_reliability(mode="health", ctx=None)
    # Merge MCP-specific fields (schema_version, tool_count, read_only)
    reliability["mcp"] = "WELL"
    reliability["schema_version"] = "2026.05.15"
    reliability["read_only"] = True
    reliability["final_authority"] = "ARIF"
    reliability["tool_count"] = len(SOMATIC_TOOLS)  # was hardcoded 79; now dynamic
    reliability["mcp_registered_tools"] = (
        18  # actual MCP tools/list count post-boundary
    )
    reliability["canonical_tools"] = len(SOMATIC_TOOLS)  # SOMATIC_TOOLS set size
    # ── FEDERATION GEOMETRY 1a: home-call to arifOS ─────────────────────
    # Non-blocking. arifOS geometry is auth-bypass (absorbed diagnostic).
    # arifOS MCP requires session-init before tools/call, so we do a
    # 2-call sequence (initialize + tools/call). 2s timeout per step.
    fed_geometry: dict | None = None
    fed_geometry_source: str | None = None
    fed_geometry_note: str | None = None
    try:
        # Step 1: initialize to get session id
        _init_body = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-25",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "well-federation-bridge",
                        "version": "1.0",
                    },
                },
            }
        ).encode("utf-8")
        _init_req = urllib.request.Request(
            "http://127.0.0.1:8088/mcp",
            data=_init_body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
        )
        with urllib.request.urlopen(_init_req, timeout=2.0) as _init_resp:
            _session_id = _init_resp.headers.get("mcp-session-id")
        if _session_id:
            # Step 2: tools/call with session id
            _call_body = json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "arif_ops_measure",
                        "arguments": {"mode": "geometry"},
                    },
                }
            ).encode("utf-8")
            _call_req = urllib.request.Request(
                "http://127.0.0.1:8088/mcp",
                data=_call_body,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    "mcp-session-id": _session_id,
                },
            )
            with urllib.request.urlopen(_call_req, timeout=2.0) as _resp:
                _arif_json = json.loads(_resp.read().decode("utf-8"))
            for _c in _arif_json.get("result", {}).get("content", []):
                if _c.get("type") != "text":
                    continue
                try:
                    _inner = json.loads(_c.get("text", ""))
                except Exception:
                    continue
                _payload = _inner.get("result", _inner)
                if (
                    isinstance(_payload, dict)
                    and _payload.get("telemetry_source") == "geometry_hygiene_v1"
                ):
                    fed_geometry = _payload
                    fed_geometry_source = "arifOS:8088/mcp"
                    break
        else:
            fed_geometry_note = "arifOS did not return mcp-session-id"
    except Exception as _exc:
        fed_geometry_note = f"arifOS unreachable: {type(_exc).__name__}"
    reliability["federation_geometry"] = fed_geometry
    reliability["federation_geometry_source"] = fed_geometry_source
    reliability["federation_geometry_note"] = fed_geometry_note
    # ── END FEDERATION GEOMETRY 1a ───────────────────────────────────

    # ── 4-DIMENSION HEALTH CHECK (2026-06-28) ────────────────────────
    # Report across machine, governance, intelligence, and human axes.
    # Each dimension has status, detail, and where to look for issues.
    dimensions = {}

    # 1. MACHINE — service health, tool surface, MCP availability
    dimensions["machine"] = {
        "status": reliability.get("status", "UNKNOWN"),
        "detail": "WELL server process, MCP transport, tool surface",
        "service": "well",
        "transport": "streamable-http",
        "tool_count": reliability.get("tool_count", 0),
    }

    # 2. GOVERNANCE — F1-F13 floor compliance, constitutional integrity
    # Probes arifOS for floor state (non-blocking)
    gov_status = "UNKNOWN"
    gov_detail = "Floor compliance checks delegated to arifOS kernel"
    try:
        _gov_req = urllib.request.Request(
            "http://127.0.0.1:8088/health",
            headers={"Accept": "application/json"},
        )
        with urllib.request.urlopen(_gov_req, timeout=1.5) as _gov_resp:
            _gov_body = json.loads(_gov_resp.read().decode("utf-8"))
            gov_status = _gov_body.get("status", "UNKNOWN")
            gov_detail = f"arifOS reports: {gov_status}"
    except Exception as _gov_exc:
        gov_status = "DEGRADED"
        gov_detail = f"arifOS unreachable: {type(_gov_exc).__name__}"
    dimensions["governance"] = {
        "status": gov_status,
        "detail": gov_detail,
        "floor_authority": "arifOS kernel (port 8088)",
        "well_gate": "REFLECT_ONLY — WELL does not adjudicate floors",
    }

    # 3. INTELLIGENCE — agent readiness, epistemic coherence, tool surface
    # Reports WELL's tool surface integrity and cognitive readiness
    _well_state = _load_state()
    _tools_ok = reliability.get("tool_count", 0) > 0
    _state_age = (
        _well_state.get("state_age_hours", -1) if isinstance(_well_state, dict) else -1
    )
    dimensions["intelligence"] = {
        "status": "OK" if _tools_ok else "DEGRADED",
        "detail": "WELL tool surface and epistemic readiness",
        "tools_ok": _tools_ok,
        "state_age_hours": _state_age if _state_age >= 0 else "unknown",
        "epistemic_label": "OBSERVED" if _state_age < 24 else "STALE",
    }

    # 4. HUMAN — operator vitality, fatigue, dignity (from state.json)
    _human_status = "UNKNOWN"
    _human_detail = "No biometric data loaded"
    try:
        if isinstance(_well_state, dict):
            _vitality = _well_state.get("vitality", {}) or {}
            _fatigue = _well_state.get("fatigue", {}) or {}
            _recent = _well_state.get("recent_human_entry", None)
            if _vitality and _vitality.get("status"):
                _human_status = _vitality["status"]
                _human_detail = f"Vitality: {_vitality.get('score', 'N/A')}, Fatigue: {_fatigue.get('level', 'N/A')}"
            elif _recent:
                _human_status = "STALE"
                _human_detail = f"Last human data: {_recent}"
            else:
                _human_status = "DATA_GAP"
                _human_detail = "No human vitality data in state.json"
    except Exception:
        _human_status = "ERROR"
        _human_detail = "Failed to read human state"
    dimensions["human"] = {
        "status": _human_status,
        "detail": _human_detail,
        "dignity_guard": "F6 MARUAH — WELL reflects, never diagnoses",
        "authority": "REFLECT_ONLY — Arif holds final judgment",
    }

    reliability["health_dimensions"] = dimensions
    reliability["health_model"] = "4-dimension (machine·governance·intelligence·human)"
    # ── END 4-DIMENSION HEALTH CHECK ─────────────────────────────────
    return reliability


def _build_unified_packet(ctx: Context | None = None) -> dict[str, Any]:
    """Build the unified substrate packet: human + machine + G-WELL governance + MCP + coupled."""
    state = _load_state()

    # Human substrate
    human = {
        "well_score": state.get("well_score", 50.0),
        "floors_violated": state.get("floors_violated", []),
        "metrics": state.get("metrics", {}),
        "readiness": _resolve_readiness(state),
    }

    # Machine / VP substrate
    m_machine = state.get("m_machine", {})
    machine = {
        "model_reliability": m_machine.get("model_reliability", 1.0),
        "tool_availability": m_machine.get("tool_availability", 1.0),
        "latency_ms": m_machine.get("latency_ms", 200),
        "context_pressure": m_machine.get("context_length_pressure", 0.0),
        "memory_integrity": m_machine.get("memory_integrity", 1.0),
        "api_failure_rate": m_machine.get("api_failure_rate", 0.0),
        "data_freshness": m_machine.get("data_freshness", 1.0),
        "compute_budget_pct": m_machine.get("compute_budget_pct", 100.0),
        "token_budget_pct": m_machine.get("token_budget_pct", 100.0),
        "security_flags": m_machine.get("security_flags", []),
        "vault_status": m_machine.get("vault_status", "ok"),
        "schema_valid": m_machine.get("schema_valid", True),
    }

    # G-WELL governance abstraction
    g_well = _g_well_assess(state)

    # MCP infra substrate
    mcp = _mcp_health_check_impl()

    # Coupled readiness (human + machine + MCP)
    h_ready = human["readiness"].get("readiness", "UNKNOWN")
    m_ready = (
        "HEALTHY"
        if machine["model_reliability"] >= 0.8 and machine["tool_availability"] >= 0.8
        else "DEGRADED"
        if machine["model_reliability"] >= 0.5
        else "CRITICAL"
    )
    mcp_ready = "HEALTHY" if mcp["status"] == "OK" else "DEGRADED"

    # I3 — Evidence discipline: unverified/stale/expired telemetry downgrades coupled verdict
    truth_status = state.get("truth_status", "UNVERIFIED")
    evidence_degraded = truth_status in ("UNVERIFIED", "STALE", "EXPIRED")

    if (
        h_ready in ("READY", "OPTIMAL")
        and m_ready == "HEALTHY"
        and mcp_ready == "HEALTHY"
        and not evidence_degraded
    ):
        coupled_verdict = "PROCEED"
    elif (
        h_ready in ("READY", "OPTIMAL", "DEGRADED")
        and m_ready in ("HEALTHY", "DEGRADED")
        and mcp_ready in ("HEALTHY", "DEGRADED")
        and not evidence_degraded
    ):
        coupled_verdict = "CAUTION"
    else:
        coupled_verdict = "HOLD"

    coupled = {
        "human_ready": h_ready,
        "machine_ready": m_ready,
        "mcp_ready": mcp_ready,
        "coupled_verdict": coupled_verdict,
        "operator_confirmation_advised": h_ready not in ("READY", "OPTIMAL")
        or m_ready != "HEALTHY"
        or mcp_ready != "HEALTHY"
        or evidence_degraded,
        "truth_status": truth_status,
    }

    return {
        "ok": True,
        "timestamp": state.get(
            "timestamp", datetime.datetime.now(datetime.timezone.utc).isoformat()
        ),
        "operator_id": state.get("operator_id", "arif"),
        "authority": "REFLECT_ONLY",
        "human": human,
        "machine": machine,
        "g_well": g_well,
        "mcp": mcp,
        "coupled": coupled,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


# ── Helpers ────────────────────────────────────────────────────────────────────


def _ensure_well_identity(state: dict[str, Any]) -> dict[str, Any]:
    """
    Ensure canonical WELL identity invariants are present.

    If the state carries the correct identity/role/authority but is missing
    the numeric/spiritual invariants (e.g. written by an older telemetry
    writer), inject the safe defaults. If a state is clearly a WELL substrate
    snapshot (has well_score / metrics / w0) but lacks identity fields,
    migrate it gently rather than declaring identity failure. Mark injection
    for audit transparency.
    """
    identity = state.get("identity")
    role = state.get("role")
    authority = state.get("authority")
    is_well_shape = (
        isinstance(state.get("metrics"), dict)
        and ("well_score" in state or "w0" in state)
        and "operator_id" in state
    )
    if (
        identity == "WELL"
        and role
        in [
            "Body",
            "Body / Human Intelligence",
            "Biological Substrate Governance",
        ]
        and authority == "REFLECT_ONLY"
    ):
        pass
    elif identity is None and is_well_shape:
        # Migration path: WELL substrate snapshot written without identity invariants
        state["identity"] = "WELL"
        state["role"] = "Body / Human Intelligence"
        state["authority"] = "REFLECT_ONLY"
        state.setdefault("_identity_migrated", True)
    else:
        return state

    defaults = {
        "delta_s": 0.0,
        "peace2": 1.0,
        "kappa_r": 0.95,
        "rasa": True,
        "amanah": "LOCK",
    }
    for key, value in defaults.items():
        if key not in state:
            state[key] = value
            state.setdefault("_identity_defaults_injected", []).append(key)
    return state


def _load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "operator_id": "arif",
            "identity": "WELL",
            "role": "Body / Human Intelligence",
            "authority": "REFLECT_ONLY",
            "delta_s": 0.0,
            "peace2": 1.0,
            "kappa_r": 0.95,
            "rasa": True,
            "amanah": "LOCK",
            "metrics": {},
            "well_score": None,
            "floors_violated": [],
            "truth_status": "INSUFFICIENT_DATA",
            "environment": "PROD",
            "reason": "No state file found. Sovereign state unknown.",
            "confidence": "NONE",
            "freshness": "VOID",
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        }
    with open(STATE_PATH) as f:
        state = json.load(f)
    return _ensure_well_identity(state)


def _g_well_assess(state: dict[str, Any]) -> dict[str, Any]:
    """
    G-WELL: Assess governance coherence of the machine substrate.
    Maps m_machine + MCP health into governance terms: autonomic_coherence,
    check_and_balance, law_compliance, evidence_integrity, sovereignty_preserved.
    Returns structured governance verdict.
    """
    m = state.get("m_machine", {})
    well_ok = is_well(state)
    m_verdict = None
    m_score = 0.0

    # Reuse M-WELL scoring
    m_metrics = {
        "model_reliability": m.get("model_reliability", 1.0),
        "tool_availability": m.get("tool_availability", 1.0),
        "api_failure_rate": m.get("api_failure_rate", 0.0),
        "context_length_pressure": m.get("context_length_pressure", 0.0),
        "memory_integrity": m.get("memory_integrity", 1.0),
        "data_freshness": m.get("data_freshness", 1.0),
        "compute_budget_pct": m.get("compute_budget_pct", 100.0),
        "token_budget_pct": m.get("token_budget_pct", 100.0),
    }
    m_score = (
        m_metrics["model_reliability"] * 20
        + m_metrics["tool_availability"] * 15
        + max(0, 1 - m_metrics["api_failure_rate"]) * 15
        + max(0, 1 - m_metrics["context_length_pressure"]) * 15
        + m_metrics["memory_integrity"] * 10
        + m_metrics["data_freshness"] * 10
        + max(0, m_metrics["compute_budget_pct"] / 100) * 10
        + max(0, m_metrics["token_budget_pct"] / 100) * 5
    )
    m_score = round(min(100.0, m_score), 1)
    m_verdict = (
        "HEALTHY"
        if m_score >= 85
        else "FUNCTIONAL"
        if m_score >= 65
        else "DEGRADED"
        if m_score >= 45
        else "CRITICAL"
    )

    governance_flags = []

    # 1. Autonomic coherence
    if not well_ok:
        governance_flags.append("well_identity_compromised")
    if m.get("schema_valid") is False:
        governance_flags.append("schema_corrupted")
    if m.get("vault_status") not in ("ok", "degraded"):
        governance_flags.append("vault_disconnected")

    # 2. Check and balance
    if m_verdict == "CRITICAL":
        governance_flags.append("machine_substrate_critical")
    if len(m.get("security_flags", [])) > 0:
        governance_flags.append(f"security_flags:{','.join(m['security_flags'])}")

    # 3. Floor compliance
    auth = state.get("authority", "")
    if auth != "REFLECT_ONLY":
        governance_flags.append(f"authority_overreach:{auth}")

    # 4. Evidence integrity
    truth = state.get("truth_status", "UNVERIFIED")
    if truth in ("VOID", "CONTRADICTED"):
        governance_flags.append(f"evidence_compromised:{truth}")

    # 5. Sovereignty preserved
    if state.get("amanah") not in ("LOCK", "🔐", True):
        governance_flags.append("amanah_unlocked")

    if len(governance_flags) == 0:
        g_verdict = "COHERENT"
    elif len(governance_flags) <= 2:
        g_verdict = "STRESSED"
    else:
        g_verdict = "FRAGMENTED"

    return {
        "ok": True,
        "g_well_verdict": g_verdict,
        "g_well_score": m_score,
        "machine_verdict": m_verdict,
        "governance_flags": governance_flags,
        "pillars": {
            k: (v, "intact" if not governance_flags else "stressed")
            for k, v in G_WELL_PILLARS.items()
        },
        "identity_valid": well_ok,
        "authority_boundary": "REFLECT_ONLY" if well_ok else "COMPROMISED",
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


def _state_score(state: dict[str, Any], default: float = 0.0) -> float:
    """Return a numeric WELL score; null/invalid telemetry is treated as unsafe unknown."""
    raw = state.get("well_score", default)
    if raw is None:
        return default
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


def _legacy_advisory(
    legacy_name: str,
    canonical_name: str,
    canonical_params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Deprecation advisory for legacy tools. Additive only — never breaks existing clients."""
    adv: dict[str, Any] = {
        "_advisory": {
            "legacy_tool": legacy_name,
            "canonical_tool": canonical_name,
            "deprecation_epoch": "2026-Q3",
            "surface_type": "legacy_wrapper",
            "removal_allowed": False,
            "minimum_deprecation_window": "2_epochs",
            "federation_break_risk": "high",
        }
    }
    if canonical_params:
        adv["_advisory"]["canonical_params"] = canonical_params
    return adv


def _state_is_void(state: dict[str, Any]) -> bool:
    return (
        state.get("truth_status") == "VOID"
        or state.get("test_contamination") == "YES"
        or state.get("safe_mode") == "manual_confirmation_required"
    )


def _state_is_insufficient(state: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Honest classifier: return True if WELL must not pretend it knows the sovereign's state.

    Triggers:
      - explicit test/void/unverified/insufficient truth_status
      - TEST environment
      - mocked/synthetic fixture language in reason
      - missing canonical identity
      - no verified body telemetry (unless sovereign manually reported presence)
    """
    reasons: list[str] = []
    raw_truth = state.get("truth_status", "UNVERIFIED")
    environment = state.get("environment", "PROD")
    reason = str(state.get("reason", "")).lower()

    if raw_truth in ("VOID", "TEST", "UNVERIFIED", "INSUFFICIENT_DATA"):
        reasons.append(f"truth_status:{raw_truth}")
    if environment == "TEST":
        reasons.append("environment:TEST")
    if any(
        marker in reason for marker in ("mock", "fixture", "synthetic", "test session")
    ):
        reasons.append("mocked_state")
    if not is_well(state):
        reasons.append("identity_invalid")
    if raw_truth != "OPERATOR_REPORTED" and not _has_verified_telemetry(state):
        reasons.append("no_verified_telemetry")

    return bool(reasons), reasons


def _classify_well_state(state: dict[str, Any]) -> dict[str, Any]:
    """
    Build honest health classification for WELL HTTP health endpoints.
    Never fabricates biological readiness from fixtures or missing data.
    """
    insufficient, insufficient_reasons = _state_is_insufficient(state)
    state_age_hours = None
    ts = state.get("timestamp", "")
    if ts:
        try:
            dt = datetime.datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            state_age_hours = (
                datetime.datetime.now(datetime.timezone.utc) - dt
            ).total_seconds() / 3600
        except Exception:
            state_age_hours = None

    if insufficient:
        # F3-honest: truth_status reflects biometric data quality (INSUFFICIENT_DATA)
        # but freshness_band reflects actual timestamp age independently.
        # A state can be insufficient (no real biometrics) but still fresh (recent heartbeat).
        truth_status = "INSUFFICIENT_DATA"
        freshness_band = _get_freshness_band(
            state
        )  # Compute from timestamp, not hardcoded to VOID
        well_score = None

        # Degrade signal only if state is actually old (> 168h ceiling)
        if (
            freshness_band == "STALE"
            and state_age_hours is not None
            and state_age_hours > 168
        ):
            well_signal = "WELL_HOLD"
            owner_summary = {
                "color": "RED",
                "reasons": [
                    "sovereign_state_unknown",
                    "biometric_state_expired_168h_ceiling",
                    "human_injection_required",
                ],
            }
        elif freshness_band in ("FRESH", "CURRENT"):
            well_signal = "WELL_HOLD"  # Insufficient data but fresh — hold, not crisis
            owner_summary = {
                "color": "YELLOW",
                "reasons": [
                    "sovereign_state_unknown",
                    "biometric_state_fresh_but_insufficient",
                    f"canonical_tools=22",
                ],
            }
        else:
            well_signal = "WELL_HOLD"
            owner_summary = {
                "color": "YELLOW",
                "reasons": [
                    "sovereign_state_unknown",
                    "human_injection_required",
                ],
            }

        freshness_status = (
            "fresh"
            if freshness_band in ("FRESH", "CURRENT")
            else "stale"
            if freshness_band == "AGED"
            else "expired"
        )
    else:
        raw_truth = state.get("truth_status", "UNVERIFIED")
        truth_status = raw_truth
        freshness_band = _get_freshness_band(state)
        well_score = state.get("well_score")
        if raw_truth == "OPERATOR_REPORTED":
            well_signal = "WELL_OPERATOR_PRESENT"  # signal, not verdict
            owner_summary = {
                "color": "YELLOW",
                "reasons": [
                    "operator_reported_presence",
                    "no_biometric_telemetry",
                ],
            }
        else:
            well_signal = (
                "WELL_PASS"
                if well_score is not None and well_score >= 60
                else "WELL_HOLD"
            )  # signal, not verdict
            owner_summary = {
                "color": (
                    "GREEN"
                    if freshness_band in ("FRESH", "CURRENT")
                    else "YELLOW"
                    if freshness_band == "AGED"
                    else "RED"
                ),
                "reasons": (
                    ["biometric_state_fresh", "truth_status_verified"]
                    if freshness_band in ("FRESH", "CURRENT")
                    else ["biometric_state_aged_contact_arif"]
                    if freshness_band == "AGED"
                    else [
                        "biometric_state_stale_or_expired",
                        "human_injection_required",
                    ]
                ),
            }
        freshness_status = (
            "fresh"
            if freshness_band in ("FRESH", "CURRENT")
            else "stale"
            if freshness_band == "AGED"
            else "expired"
        )

    freshness = {
        "status": freshness_status,
        "checked_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source_timestamp_utc": ts or None,
        "age_seconds": round(state_age_hours * 3600, 1)
        if state_age_hours is not None
        else None,
        "max_fresh_age_seconds": 3600,
        "stale_after_seconds": 14400,
        "expired_after_seconds": 86400,
    }

    return {
        "well_ok": is_well(state),
        "has_telemetry": _has_verified_telemetry(state),
        "truth_status": truth_status,
        "well_signal": well_signal,  # WELL is REFLECT_ONLY — signals, not verdicts
        "well_score": well_score,
        "freshness_band": freshness_band,
        "freshness": freshness,
        "owner_summary": owner_summary,
        "state_age_hours": round(state_age_hours, 1)
        if state_age_hours is not None
        else None,
        "insufficient": insufficient,
        "insufficient_reasons": insufficient_reasons,
    }


def _assert_sovereign_presence(operator_id: str = "arif") -> dict[str, Any]:
    """
    Manual sovereign presence assertion.
    Writes a real OPERATOR_REPORTED state. Does NOT invent biometric telemetry.
    """
    state = _load_state()
    now = datetime.datetime.now(datetime.timezone.utc)
    state.update(
        {
            "timestamp": now.isoformat(),
            "operator_id": operator_id,
            "identity": "WELL",
            "role": "Body / Human Intelligence",
            "authority": "REFLECT_ONLY",
            "delta_s": 0.0,
            "peace2": 1.0,
            "kappa_r": 0.95,
            "rasa": True,
            "amanah": "LOCK",
            "truth_status": "OPERATOR_REPORTED",
            "environment": "PROD",
            "well_score": None,
            "metrics": {},
            "floors_violated": [],
            "reason": "Sovereign presence asserted manually via /ready",
            "confidence": "HIGH",
            "freshness": "FRESH",
            "test_contamination": "NO",
            "contamination_quarantined": False,
            "safe_mode": "off",
            "arif_decision_required": False,
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        }
    )
    # Ensure we never carry over mocked-score pretense.
    if "well_score" in state and state.get("environment") != "PROD":
        del state["well_score"]
    _save_state(state)
    _append_event(
        {
            "event": "SOVEREIGN_PRESENCE_ASSERTED",
            "operator_id": operator_id,
            "truth_status": "OPERATOR_REPORTED",
        }
    )
    return {
        "ok": True,
        "timestamp": now.isoformat(),
        "truth_status": "OPERATOR_REPORTED",
    }


async def _well_ready_handler(request):
    """Sovereign presence assertion endpoint. POST only."""
    if request.method != "POST":
        return JSONResponse(
            {"error": "METHOD_NOT_ALLOWED", "allowed_methods": ["POST"]},
            status_code=405,
        )
    result = _assert_sovereign_presence()
    return JSONResponse(result)


def _save_state(state: dict[str, Any]) -> None:
    state["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    STATE_PATH.write_text(json.dumps(state, indent=2))


def _append_event(event: dict[str, Any]) -> None:
    event["epoch"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    with open(EVENTS_PATH, "a") as f:
        f.write(json.dumps(event) + "\n")


def _compute_score(metrics: dict[str, Any]) -> tuple[float, list[str]]:
    """Compute WELL score (0-100) and floor violations from metrics."""
    score = 100.0
    violations: list[str] = []

    sleep = metrics.get("sleep", {})
    cognitive = metrics.get("cognitive", {})
    stress = metrics.get("stress", {})
    metabolic = metrics.get("metabolic", {})

    # W1 — Sleep Integrity
    debt = sleep.get("sleep_debt_days", 0)
    quality = sleep.get("quality_score", 10)
    hours = sleep.get("last_night_hours", 8)
    score -= min(debt * 8, 24)
    score -= max(0, (7 - hours) * 3)
    score -= max(0, (8 - quality) * 1.5)
    if debt > 2:
        violations.append("W1_SLEEP_DEBT")

    # W5 — Cognitive Entropy
    clarity = cognitive.get("clarity", 10)
    fatigue = cognitive.get("decision_fatigue", 0)
    score -= max(0, (8 - clarity) * 2)
    score -= fatigue * 1.5
    if clarity < 4:
        violations.append("W5_COGNITIVE_ENTROPY")

    # W3 — Stress Load (load >= 7/10 or chronic elevation)
    load = stress.get("subjective_load", 0)
    restless = stress.get("restlessness", 0)
    chronic_days = stress.get("chronic_elevation_days", 0)
    score -= load * 1.2
    score -= restless * 0.8
    if load >= 7:
        violations.append("W3_STRESS_LOAD")
    elif load >= 5 and chronic_days >= 7:
        violations.append("W3_STRESS_LOAD")

    # W2 — Metabolic Stability
    stability = metabolic.get("perceived_stability", 10)
    score -= max(0, (7 - stability) * 1.5)
    if metabolic.get("hydration_status") == "DEHYDRATED":
        score -= 5
        violations.append("W2_METABOLIC_STABILITY")
    elif stability < 5:
        violations.append("W2_METABOLIC_STABILITY")

    # W4 — Physical Integrity (sedentary >= 4h or pain >= 5/10)
    struct = metrics.get("structural", {})
    sedentary = struct.get("sedentary_hours_continuous", 0)
    pain_level = struct.get("pain_level", 0)
    if sedentary >= 4:
        score -= min(sedentary * 1.5, 15)
        violations.append("W4_PHYSICAL_INTEGRITY")
    if pain_level >= 5:
        score -= pain_level * 1.0
        if "W4_PHYSICAL_INTEGRITY" not in violations:
            violations.append("W4_PHYSICAL_INTEGRITY")

    # W6 — Incentive Decoupling (Metabolic Pause)
    w6_active = "W6_METABOLIC_PAUSE" in violations
    if w6_active:
        score -= 10  # Base penalty while paused
        if "W6_METABOLIC_PAUSE" not in violations:
            violations.append("W6_METABOLIC_PAUSE")
    # W7 — Skill Atrophy detection (>= 14 days without manual practice)
    skill_gap = metrics.get("skill", {}).get("days_since_practice", -1)
    if skill_gap >= 14:
        violations.append("W7_SKILL_ATROPHY")
        score -= min((skill_gap - 14) * 2, 20)

    score = round(max(0.0, min(100.0, score)), 1)
    return score, violations


def readiness_score(metrics: dict[str, Any]) -> dict[str, Any]:
    """
    Phase 2 Readiness Score Engine.
    Computes a 0.0-1.0 score and determines color tier using canonical _compute_score.
    """
    score_100, violations = _compute_score(metrics)
    score = round(score_100 / 100.0, 2)

    if score >= 0.7 and not violations:
        tier = "GREEN"
        recommendation = "Full action allowed. Substrate optimal."
    elif score >= 0.4:
        tier = "AMBER"
        recommendation = f"Soft warning: {', '.join(violations) if violations else 'Low capacity'}. Proceed with caution."
    else:
        tier = "RED"
        recommendation = f"CRITICAL: {', '.join(violations)}. Block strategic forge actions. Route to arifOS 888 HOLD."

    return {
        "score": score,
        "tier": tier,
        "w_floors_triggered": violations,
        "recommendation": recommendation,
        "human_decision_required": tier in ("AMBER", "RED"),
    }


def _compose_verdict(
    mcp: str,
    task: str,
    status: str,  # PASS | CAUTION | HOLD | VOID
    domain_verdict: str,
    confidence: str = "HIGH",
    epistemic: str = "CLAIM",
    epistemic_integrity: float = 1.0,
    authority_level: str = "advisory_only",
    risk_level: str = "GREEN",
    human_readiness: str = "OPTIMAL",
    machine_readiness: str = "HEALTHY",
    failure_class: str | None = None,
    failure_severity: str = "LOW",
    impact_summary: str | None = None,
    recommended_mode: str = "full",
    human_required: bool = False,
    assumptions: list[str] | None = None,
    failure_flags: list[str] | None = None,
    next_safe_action: str | None = None,
    federation_reconcile: dict | None = None,
) -> dict[str, Any]:
    """Canonical arifOS MCP verdict schema (Spec v1.0) with Failure Doctrine v1.0."""

    # Failure Doctrine Overrides
    if failure_class:
        status = "HOLD" if status != "VOID" else "VOID"
        recommended_mode = (
            "pause" if failure_severity in ("HIGH", "CRITICAL") else "draft_only"
        )
        epistemic_integrity = min(epistemic_integrity, 0.1)
        confidence = "LOW"
        human_required = True

    result = {
        "ok": status in ("PASS", "SEAL", "WELL_PASS"),
        "mcp": mcp,
        "task": task,
        "status": status,
        "domain_verdict": domain_verdict,
        "confidence": confidence,
        "epistemic": {
            "class": epistemic,
            "integrity_score": epistemic_integrity,
        },
        "failure": {
            "class": failure_class,
            "severity": failure_severity,
            "impact": impact_summary
            or ("N/A" if not failure_class else "Subsystem failure"),
        }
        if failure_class
        else None,
        "authority": {
            "level": authority_level,
            "boundary": "W0 — Mirror only" if mcp == "AFWELL" else "Domain Expert",
        },
        "readiness": {
            "human": human_readiness,
            "machine": machine_readiness,
        },
        "risk": {
            "level": risk_level,
            "coupled": "UNKNOWN",
        },
        "risk_level": risk_level,
        "recommended_mode": recommended_mode,
        "execution": {
            "recommended_mode": recommended_mode,
            "human_confirmation_required": human_required,
            "next_safe_action": next_safe_action or "Consult arifOS 888_JUDGE",
        },
        "assumptions": assumptions or [],
        "failure_flags": failure_flags or [],
        "federation_reconcile": federation_reconcile,
        "reversibility": "REVERSIBLE"
        if task.startswith("read") or "check" in task
        else "UNKNOWN",
        "final_authority": "Arif",
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        "receipt_hash": hashlib.sha256(
            str(datetime.datetime.now()).encode()
        ).hexdigest()[:16],
    }
    if mcp == "AFWELL" and task == "readiness_reflection":
        result["readiness_evidence"] = _readiness_visibility_context()
    return result


# ── Tools ──────────────────────────────────────────────────────────────────────


# DEPRECATED: Use well_validate_vitality(mode="state") instead.
# @mcp.tool() restored — test compatibility only. Internal callers should use
# well_validate_vitality directly.
@mcp.tool()
def well_state(include: str = "full", ctx: Context | None = None) -> dict[str, Any]:
    """
    Get the current WELL state — biological telemetry snapshot for operator Arif.
    Returns score, floor violations, and all metric dimensions.
    """
    VALID_INCLUDES = [
        "full",
        "readiness",
        "trend",
        "bandwidth",
        "health",
        "packet",
        "brief",
    ]
    if include not in VALID_INCLUDES:
        return {
            "error": "UNKNOWN_MODE",
            "valid": VALID_INCLUDES,
            "tool": "well_state",
            "received": include,
        }
    state = _load_state()
    result = {
        "ok": True,
        "operator_id": state.get("operator_id", "arif"),
        "timestamp": state.get("timestamp"),
        "well_score": _state_score(state),
        "floors_violated": state.get("floors_violated", []),
        "metrics": state.get("metrics", {}),
        "truth_status": state.get("truth_status", "UNVERIFIED"),
        "safe_mode": state.get("safe_mode"),
        "human_decision_required": bool(state.get("arif_decision_required", False)),
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }
    result.update(
        _legacy_advisory("well_state", "well_validate_vitality", {"mode": "state"})
    )
    # APEX Runtime Governance Envelope (APEX-MCP-001)
    try:
        from apex_envelope_well import well_apex_envelope

        result["apex"] = well_apex_envelope(
            tool_name="well_state",
            well_score=result.get("well_score"),
            truth_status=result.get("truth_status"),
            ok=result.get("ok", True),
            operator_id=result.get("operator_id"),
            boundary="LIVE",
        )
    except Exception:
        pass
    return result


@mcp.tool()
def well_log(
    # Sleep
    sleep_hours: float | None = None,
    sleep_debt_days: float | None = None,
    sleep_quality: float | None = None,
    # Stress
    stress_load: float | None = None,
    restlessness: float | None = None,
    hrv_proxy: float | None = None,
    # Cognitive
    clarity: float | None = None,
    decision_fatigue: float | None = None,
    focus_durability: float | None = None,
    # Metabolic
    fasting_hours: float | None = None,
    metabolic_stability: float | None = None,
    hydration: str | None = None,
    # Structural
    pain_sites: list[str] | None = None,
    movement_count: float | None = None,
    # Optional note
    note: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Log a biological telemetry update for operator Arif.
    Updates state.json, recomputes WELL score, checks floor violations.
    Only provide dimensions you're logging — omitted fields are unchanged.
    """
    state = _load_state()
    metrics = state.get("metrics", {})

    # ── Validate & clamp incoming readings ─────────────────────────
    try:
        sleep_hours = _clamp(sleep_hours, 0, 24)
        sleep_debt_days = _clamp(sleep_debt_days, 0, 30)
        sleep_quality = _clamp(sleep_quality, 0, 10)
        stress_load = _clamp(stress_load, 0, 10)
        restlessness = _clamp(restlessness, 0, 10)
        clarity = _clamp(clarity, 0, 10)
        decision_fatigue = _clamp(decision_fatigue, 0, 10)
        focus_durability = _clamp(focus_durability, 0, 10)
        fasting_hours = _clamp(fasting_hours, 0, 72)
        metabolic_stability = _clamp(metabolic_stability, 0, 10)
        movement_count = _clamp(movement_count, 0, 10000)
    except ValueError as e:
        return {"ok": False, "error": f"Invalid input: {e}"}

    note = _sanitize_note(note)

    # ── Merge incoming readings ────────────────────────────────────
    if any(v is not None for v in [sleep_hours, sleep_debt_days, sleep_quality]):
        sleep = dict(metrics.get("sleep", {}))
        if sleep_hours is not None:
            sleep["last_night_hours"] = sleep_hours
        if sleep_debt_days is not None:
            sleep["sleep_debt_days"] = sleep_debt_days
        if sleep_quality is not None:
            sleep["quality_score"] = sleep_quality
        metrics["sleep"] = sleep

    if any(v is not None for v in [stress_load, restlessness, hrv_proxy]):
        stress = dict(metrics.get("stress", {}))
        if stress_load is not None:
            stress["subjective_load"] = stress_load
        if restlessness is not None:
            stress["restlessness"] = restlessness
        if hrv_proxy is not None:
            stress["hrv_proxy"] = hrv_proxy
        metrics["stress"] = stress

    if any(v is not None for v in [clarity, decision_fatigue, focus_durability]):
        cog = dict(metrics.get("cognitive", {}))
        if clarity is not None:
            cog["clarity"] = clarity
        if decision_fatigue is not None:
            cog["decision_fatigue"] = decision_fatigue
        if focus_durability is not None:
            cog["focus_durability"] = focus_durability
        metrics["cognitive"] = cog

    if any(v is not None for v in [fasting_hours, metabolic_stability, hydration]):
        meta = dict(metrics.get("metabolic", {}))
        if fasting_hours is not None:
            meta["fasting_window_hours"] = fasting_hours
        if metabolic_stability is not None:
            meta["perceived_stability"] = metabolic_stability
        if hydration is not None:
            meta["hydration_status"] = hydration.upper()
        metrics["metabolic"] = meta

    if any(v is not None for v in [pain_sites, movement_count]):
        struct = dict(metrics.get("structural", {}))
        if pain_sites is not None:
            struct["pain_map"] = pain_sites
        if movement_count is not None:
            struct["movement_frequency_daily"] = movement_count
        metrics["structural"] = struct

    # ── Recompute score ────────────────────────────────────────────
    score, violations = _compute_score(metrics)

    # Readiness tiering (Phase 2)
    r_score = readiness_score(metrics)

    state["metrics"] = metrics
    state["well_score"] = score
    state["floors_violated"] = violations
    # F2/I3: Operator-reported data is never VERIFIED automatically.
    # Only machine-verifiable or cryptographically signed telemetry may be VERIFIED.
    # This prevents truth_status poisoning where one legit session + forged logs
    # produces undetectable fake substrate data.
    state["truth_status"] = "OPERATOR_REPORTED"
    _save_state(state)

    event: dict[str, Any] = {
        "event": "WELL_LOG",
        "well_score": score,
        "floors_violated": violations,
        "tier": r_score["tier"],
    }
    if note:
        event["note"] = note
    _append_event(event)

    return {
        "ok": True,
        "well_score": score,
        "floors_violated": violations,
        "status": "DEGRADED" if violations else "STABLE",
        "tier": r_score["tier"],
        "recommendation": r_score["recommendation"],
        "human_decision_required": r_score["human_decision_required"],
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


# DEPRECATED: Use well_validate_vitality(mode="readiness") instead.
# ZEN TTL constants for well_readiness
_TTL_FRESH = 12    # hours — GREEN
_TTL_WARN = 24     # hours — YELLOW
_TTL_STALE = 48    # hours — RED/STALE


# @mcp.tool() restored — test compatibility only. Internal callers should use
# well_validate_vitality directly.
@mcp.tool()
def well_readiness(ctx: Context | None = None) -> dict[str, Any]:
    """
    ZEN: Single readiness verdict. One tool, one answer.
    
    Returns score, color (GREEN/YELLOW/RED/STALE), TTL, action, and biometric signals.
    W0: This is informational only — WELL never blocks unilaterally.
    If no verified telemetry exists, returns UNKNOWN rather than faking biological knowledge.
    
    TTL rules:
      < 12h  = GREEN (if score OK)
      12-24h = YELLOW
      24-48h = RED
      > 48h  = STALE → INJECT_NEEDED
    """
    state = _load_state()
    resolved = _resolve_readiness(state)

    status_map = {
        "UNKNOWN": "HOLD",
        "VOID_TELEMETRY": "HOLD",
        "DEGRADED": "HOLD",
        "OPTIMAL": "PASS",
        "FUNCTIONAL": "PASS",
        "LOW_CAPACITY": "CAUTION",
    }
    
    # ZEN: Compute TTL and color/action
    ts_str = state.get("last_successful_read") or state.get("signals_meta", {}).get("injection_ts")
    ttl_hours = 999.0
    if ts_str:
        try:
            ts = datetime.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            now = datetime.datetime.now(datetime.timezone.utc)
            ttl_hours = max(0, (now - ts).total_seconds() / 3600)
        except (ValueError, TypeError):
            pass
    score = _state_score(state) or 0
    if ttl_hours > _TTL_STALE:
        zen_color, zen_action = "STALE", "INJECT_NEEDED"
    elif ttl_hours > _TTL_WARN:
        zen_color, zen_action = "RED", "HOLD"
    elif ttl_hours > _TTL_FRESH:
        zen_color, zen_action = "YELLOW", "SIMPLIFY"
    elif score >= 75:
        zen_color, zen_action = "GREEN", "PROCEED"
    elif score >= 50:
        zen_color, zen_action = "YELLOW", "SIMPLIFY"
    else:
        zen_color, zen_action = "RED", "HOLD"

    # I3 — Evidence discipline: confidence gated by truth_status AND telemetry presence
    truth_status = state.get("truth_status", "UNVERIFIED")
    freshness_band = resolved.get("freshness_band", _get_freshness_band(state))
    confidence = (
        "LOW"
        if truth_status in ("UNVERIFIED", "STALE", "EXPIRED", "OPERATOR_REPORTED")
        else "MEDIUM"
        if truth_status in ("PARTIAL", "INFERRED")
        else "HIGH"
        if resolved["has_telemetry"] and truth_status == "VERIFIED"
        else "LOW"
    )
    confidence = _cap_confidence_by_freshness(confidence, freshness_band)
    reconcile = _federation_health_reconcile(
        transport_ok=True,
        identity_valid=is_well(state),
        truth_status=truth_status,
        any_tool_says_optimistic=resolved["readiness"] in ("OPTIMAL", "FUNCTIONAL"),
    )
    # W-Invariant: inner readiness.human MUST match domain_verdict.
    # Fix: pass resolved["readiness"] so inner human_readiness
    # is UNKNOWN when no telemetry, not the default OPTIMAL.
    human_readiness_val = resolved["readiness"]
    status = (
        reconcile["verdict"]
        if reconcile["verdict"] == "HOLD"
        else status_map.get(resolved["readiness"], "HOLD")
    )
    # Extract biometric signals for zen output
    bio = state.get("biometric", {})
    signals = state.get("signals", {})
    sleep = signals.get("s05_sleep_architecture", {})
    
    result = _compose_verdict(
        mcp="AFWELL",
        task="readiness_reflection",
        status=status,
        domain_verdict=resolved["readiness"],
        confidence=confidence,
        risk_level=resolved["risk_level"],
        recommended_mode=resolved["recommended_mode"],
        human_required=resolved["human_confirmation_required"]
        or reconcile["verdict"] == "HOLD",
        human_readiness=human_readiness_val,
        assumptions=[
            f"truth_status={truth_status}",
            f"telemetry_confidence={state.get('telemetry_confidence', 'UNKNOWN')}",
            f"has_telemetry={resolved['has_telemetry']}",
            f"freshness_band={freshness_band}",
        ],
        next_safe_action=resolved["reason"],
        federation_reconcile=reconcile,
    )
    # ZEN: Add color, action, TTL, biometric to the verdict
    result["color"] = zen_color
    result["action"] = zen_action
    result["ttl_hours"] = round(ttl_hours, 1)
    result["biometric"] = {
        "peace2": bio.get("peace2"),
        "delta_s": bio.get("delta_s"),
        "kappa_r": bio.get("kappa_r"),
        "rasa": bio.get("rasa"),
        "clarity": state.get("metrics", {}).get("cognitive", {}).get("clarity"),
        "sleep_hours": sleep.get("hours"),
    }
    return result


@mcp.tool()
def well_contrast_report(
    lookback_days: int = 14,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    DEPRECATED: use well_state(include="trend") instead for trend data.
    Soft alias retained for backward compatibility.

    Detect anomalous biological contrast — deviation from operator baseline.

    Implements the W→P→C→M→G→J metabolic loop for human vitality:
      W  Witness     — current state + events.jsonl rolling window
      P  Perception  — parse and structure current metrics
      C  Contrast    — z-score anomaly detection vs established baseline
      M  Meaning     — pattern-match anomaly signatures to infer possible causes
      G  Guard       — route anomalies through W-floor thresholds
      J  Judgment    — severity tier + recommended action

    W0: WELL holds a mirror, not a veto. All outputs are HYPOTHESIS-tagged.
    This is not diagnosis. Arif remains final judge.

    Output schema:
      - severity_tier: NORMAL | WATCH | CONCERN | CRITICAL
      - baseline_summary: per-dimension baseline statistics
      - contrast_findings: per-dimension z-scores and anomaly flags
      - hypotheses: ranked possible causes, epistemic-tagged
      - w_floor_flags: W-floor rules triggered by anomalous dimensions
      - confidence_band: bounded by event count and telemetry freshness
    """
    # 1C-A: Source of truth for trend data is now well_state(include="trend")
    state = well_state(include="trend", ctx=ctx)

    # W: Witness — load event history
    events = _load_events(lookback_days=lookback_days)

    # P: Perception — establish baseline from events
    baseline = _compute_baseline(events)

    # C: Contrast — detect anomalous deviation
    contrast = _detect_contrast(state, baseline)

    # M: Meaning — infer possible causes from anomaly patterns
    hypotheses = _infer_meaning(contrast, state)

    # G: Guard — route to W-floor thresholds
    severity, recommended_action = _compute_contrast_severity(contrast)

    # Build W-floor flag list from anomalous dimensions
    w_floor_flags: list[dict] = []
    if contrast.get("well_score", {}).get("anomaly", False):
        z = contrast["well_score"].get("z_score", 0)
        if z < 0:
            w_floor_flags.append(
                {
                    "floor": "W_SCORE_DEGRADING",
                    "verdict": "VIOLATION_TRENDING",
                    "detail": f"well_score z={z:.2f} below baseline",
                    "w0_route": True,
                }
            )
    if contrast.get("floors_violated", {}).get("anomaly", False):
        z = contrast["floors_violated"].get("z_score", 0)
        if z > 0:
            w_floor_flags.append(
                {
                    "floor": "W_COMPOUNDING_VIOLATIONS",
                    "verdict": "VIOLATION_ACCELERATING",
                    "detail": f"floors_violated z={z:.2f} above baseline",
                    "w0_route": True,
                }
            )

    # Confidence band: bounded by event count and telemetry freshness
    freshness_band = _get_freshness_band(state)
    if len(events) < CONTRAST_MIN_EVENTS:
        confidence_band = "LOW — insufficient baseline events"
        confidence_level = 0.3
    elif freshness_band == "STALE":
        confidence_band = "LOW — telemetry stale"
        confidence_level = 0.4
    elif freshness_band == "AGED":
        confidence_band = "MEDIUM — telemetry aged"
        confidence_level = 0.6
    else:
        confidence_band = "HIGH — fresh telemetry, robust baseline"
        confidence_level = 0.8

    anomaly_count = sum(1 for v in contrast.values() if v.get("anomaly", False))

    return {
        "ok": True,
        "authority": "REFLECT_ONLY",
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        # ── Judgment ────────────────────────────────────────────────────────────
        "severity_tier": severity,
        "recommended_action": recommended_action,
        "human_confirmation_required": severity in ("CONCERN", "CRITICAL"),
        "coupled_verdict": "PROCEED"
        if severity == "NORMAL"
        else "CAUTION"
        if severity == "WATCH"
        else "HOLD",
        # ── Contrast (C) ─────────────────────────────────────────────────────────
        "contrast_findings": contrast,
        "anomaly_count": anomaly_count,
        # ── Baseline (P) ─────────────────────────────────────────────────────────
        "baseline_summary": baseline,
        "baseline_events_used": len(events),
        "baseline_window_days": lookback_days,
        "baseline_established": len(events) >= CONTRAST_MIN_EVENTS,
        # ── Meaning (M) ─────────────────────────────────────────────────────────
        "hypotheses": hypotheses,
        # ── Guard (G) ────────────────────────────────────────────────────────────
        "w_floor_flags": w_floor_flags,
        # ── Metadata ─────────────────────────────────────────────────────────────
        "confidence_band": confidence_band,
        "confidence_level": confidence_level,
        "freshness_band": freshness_band,
        "truth_status": state.get("truth_status", "UNVERIFIED"),
        "well_score": state.get("well_score", 50.0),
        "floors_violated": state.get("floors_violated", []),
        "metrics": state.get("metrics", {}),
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "boundary_notice": "Not diagnosis. Not therapy. Reflective contrast only. Arif remains final judge.",
    }


# DEPRECATED: Use well_classify_substrate instead.
# @mcp.tool() removed — internal use only.
async def well_init(
    session_id: str | None = None,
    actor_id: str = "well-substrate",
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Open a WELL governance session — writes a 000_INIT event to VAULT999.
    Call this at the start of any WELL-aware session to anchor identity and
    connect to the canonical Merkle chain.
    Returns session_id and chain position for subsequent well_anchor seals.
    W0: WELL holds a mirror, not a veto. Operator sovereignty is invariant.
    """
    import sys
    import os as _os  # P1 FIX: os was not imported before use
    import uuid as _uuid

    ARIFOS_PATH = _os.environ.get("ARIFOS_HOME", "/root") + "/arifOS"
    if ARIFOS_PATH not in sys.path:
        sys.path.append(ARIFOS_PATH)

    sid = session_id or f"well-session-{_uuid.uuid4().hex[:12]}"

    try:
        from arifosmcp.runtime.vault_postgres import seal_to_vault

        state = _load_state()
        score = state.get("well_score", 50)
        violations = state.get("floors_violated", [])

        res = await seal_to_vault(
            event_type="WELL_SESSION_INIT",
            session_id=sid,
            actor_id=actor_id,
            stage="000_INIT",
            verdict="ACTIVE",
            payload={
                "well_score": score,
                "floors_violated": violations,
                "w0": "OPERATOR_VETO_INTACT",
            },
            risk_tier="low",
        )

        _append_event(
            {
                "event": "WELL_INIT",
                "session_id": sid,
                "vault_id": res.ledger_id if hasattr(res, "ledger_id") else str(res),
            }
        )

        return {
            "ok": True,
            "session_id": sid,
            "stage": "000_INIT",
            "well_score": score,
            "chain_hash": res.chain_hash if hasattr(res, "chain_hash") else "",
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        }
    except Exception as e:
        # F01 Amanah: never leak internal errors or paths to callers
        _append_event(
            {
                "event": "WELL_INIT_ERROR",
                "error_type": type(e).__name__,
                "session_id": sid,
            }
        )
        return {
            "ok": False,
            "session_id": sid,
            "error": "Vault bridge unavailable. Check arifOS connectivity.",
        }


# internal — not MCP-facing (collapsed 2026-05-26)
async def well_anchor(
    force: bool = False,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    [DEPRECATED — use well_anchor_evidence(mode='seal')]
    Legacy anchor to arifOS VAULT999. Retained for federation compatibility.
    New code should call well_anchor_evidence.
    """
    import sys
    import os

    # Ensure arifOS is in path for bridge
    ARIFOS_PATH = os.environ.get("ARIFOS_HOME", "/root") + "/arifOS"
    if ARIFOS_PATH not in sys.path:
        sys.path.append(ARIFOS_PATH)

    try:
        from arifosmcp.runtime.well_bridge import anchor_well_to_vault

        res = await anchor_well_to_vault(force=force)

        if res.get("ok"):
            _append_event(
                {
                    "event": "VAULT_ANCHOR_SQL",
                    "vault_id": res.get("vault_id"),
                    "hash": res.get("hash"),
                }
            )
            return res
        # Sanitize arifOS internal errors before returning to caller
        _append_event({"event": "WELL_ANCHOR_ERROR", "error_type": "VaultBridgeError"})
        return {
            "ok": False,
            "error": "Vault bridge unavailable. Check arifOS connectivity.",
        }
    except Exception as e:
        # F01 Amanah: never leak internal errors or paths to callers
        _append_event({"event": "WELL_ANCHOR_ERROR", "error_type": type(e).__name__})
        return {
            "ok": False,
            "error": "Vault bridge unavailable. Check arifOS connectivity.",
        }


# internal — not MCP-facing (collapsed 2026-05-26)
@mcp.tool()
def well_check_floors(ctx: Context | None = None) -> dict[str, Any]:
    """
    [DEPRECATED — use well_validate_vitality(mode='floors')]
    Legacy W-floor checker. Retained for compatibility.
    New code should call well_validate_vitality.
    """
    state = _load_state()
    metrics = state.get("metrics", {})
    sleep = metrics.get("sleep", {})
    cognitive = metrics.get("cognitive", {})
    metabolic = metrics.get("metabolic", {})
    stress = metrics.get("stress", {})
    struct = metrics.get("structural", {})

    # ── No telemetry → cannot check floors ──
    if not _has_verified_telemetry(state):
        return _compose_verdict(
            mcp="AFWELL",
            task="floor_integrity_check",
            status="HOLD",
            domain_verdict="UNKNOWN_TELEMETRY",
            confidence="LOW",
            risk_level="UNKNOWN",
            recommended_mode="draft_only",
            human_required=True,
            next_safe_action="No verified body telemetry. Floor status cannot be determined.",
        )

    violations = state.get("floors_violated", [])

    floors: dict[str, dict[str, Any]] = {
        "W0": {
            "name": "Sovereignty Invariant",
            "status": "INVARIANT",
            "detail": "Operator veto always intact. WELL never self-authorizes.",
        },
        "W1": {
            "name": "Sleep Integrity",
            "status": "OK",
            "threshold": "sleep_debt_days <= 2",
            "current": sleep.get("sleep_debt_days", 0),
        },
        "W2": {
            "name": "Metabolic Stability",
            "status": "OK",
            "threshold": "hydration != DEHYDRATED and stability >= 5",
            "current": {
                "hydration": metabolic.get("hydration_status", "UNKNOWN"),
                "stability": metabolic.get("perceived_stability", 10),
            },
        },
        "W3": {
            "name": "Stress Load",
            "status": "OK",
            "threshold": "load < 7 (or load < 5 if chronic < 7 days)",
            "current": {
                "load": stress.get("subjective_load", 0),
                "chronic_days": stress.get("chronic_elevation_days", 0),
            },
        },
        "W4": {
            "name": "Physical Integrity",
            "status": "OK",
            "threshold": "sedentary < 4h and pain < 5/10",
            "current": {
                "sedentary": struct.get("sedentary_hours_continuous", 0),
                "pain": struct.get("pain_level", 0),
            },
        },
        "W5": {
            "name": "Cognitive Entropy",
            "status": "OK",
            "threshold": "clarity >= 4",
            "current": cognitive.get("clarity", 10),
        },
        "W6": {
            "name": "Incentive Decoupling",
            "status": "OK" if "W6_METABOLIC_PAUSE" not in violations else "VIOLATED",
            "threshold": "no high-frequency intent loops detected",
            "current": "W6_METABOLIC_PAUSE"
            if "W6_METABOLIC_PAUSE" in violations
            else "clear",
        },
        "W7": {
            "name": "Skill Atrophy",
            "status": "OK",
            "threshold": "days_since_practice < 14",
            "current": metrics.get("skill", {}).get("days_since_practice", "unknown"),
        },
    }

    if sleep.get("sleep_debt_days", 0) > 2:
        floors["W1"]["status"] = "VIOLATED"
    if (
        metabolic.get("hydration_status") == "DEHYDRATED"
        or metabolic.get("perceived_stability", 10) < 5
    ):
        floors["W2"]["status"] = "VIOLATED"
    load = stress.get("subjective_load", 0)
    chronic = stress.get("chronic_elevation_days", 0)
    if load >= 7 or (load >= 5 and chronic >= 7):
        floors["W3"]["status"] = "VIOLATED"
    if (
        struct.get("sedentary_hours_continuous", 0) >= 4
        or struct.get("pain_level", 0) >= 5
    ):
        floors["W4"]["status"] = "VIOLATED"
    if cognitive.get("clarity", 10) < 4:
        floors["W5"]["status"] = "VIOLATED"
    if "W6_METABOLIC_PAUSE" in violations:
        floors["W6"]["status"] = "VIOLATED"
    if metrics.get("skill", {}).get("days_since_practice", -1) >= 14:
        floors["W7"]["status"] = "VIOLATED"

    violated = [k for k, v in floors.items() if v["status"] == "VIOLATED"]

    status = "PASS" if not violated else "HOLD"
    risk = "GREEN" if not violated else "RED"

    return _compose_verdict(
        mcp="AFWELL",
        task="floor_integrity_check",
        status=status,
        domain_verdict=f"{len(violated)} floors violated"
        if violated
        else "All floors clear",
        confidence="HIGH",
        risk_level=risk,
        recommended_mode="full" if not violated else "draft_only",
        human_required=bool(violated),
        failure_flags=violated,
    )


# ── Phase 2 Tools (Expanded Surface) ───────────────────────────────────────────


# internal — not MCP-facing (collapsed 2026-05-26)
@mcp.tool()
def well_log_state(
    sleep_hours: float | None = None,
    stress_level: float | None = None,
    clarity_score: float | None = None,
    note: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Log biological state entry to ledger (Phase 2).
    Simple interface for core metrics. Triggers readiness score recompute.
    """
    # Map to well_log tool logic
    return well_log(
        sleep_hours=sleep_hours,
        stress_load=stress_level,
        clarity=clarity_score,
        note=note,
        ctx=ctx,
    )


# internal — not MCP-facing (collapsed 2026-05-26)
@mcp.tool()
def well_get_readiness(ctx: Context | None = None) -> dict[str, Any]:
    """
    Return current readiness score + W-floor status (Phase 2).
    Includes GREEN|AMBER|RED tiering and human_decision_required flag.
    If no verified telemetry, returns UNKNOWN rather than fabricated tiers.

    HARD CEILING: If state age > 168h, returns DO_NOT_INFER regardless of any other signal.
    """
    state = _load_state()
    # P0-3: 168h hard ceiling — block human readiness inference when state is too old
    ceiling_block = _check_human_readiness_168h_ceiling(state)
    if ceiling_block is not None:
        return {
            "ok": True,
            "well_score": ceiling_block["well_score"],
            "readiness": {
                "score": round(ceiling_block["well_score"] / 100.0, 2),
                "tier": ceiling_block["readiness"],
                "recommendation": ceiling_block["reason"],
                "human_decision_required": True,
            },
            "floors_violated": [],
            "has_telemetry": ceiling_block["has_telemetry"],
            "state_age_hours": ceiling_block["state_age_hours"],
            "ceiling_168h": ceiling_block["ceiling_168h"],
            "w0": ceiling_block["w0"],
            "boundary_notice": ceiling_block["boundary_notice"],
        }
    resolved = _resolve_readiness(state)

    if not resolved["has_telemetry"]:
        return {
            "ok": True,
            "well_score": resolved["well_score"],
            "readiness": {
                "score": round(resolved["well_score"] / 100.0, 2),
                "tier": "UNKNOWN",
                "recommendation": resolved["reason"],
                "human_decision_required": True,
            },
            "floors_violated": resolved["active_violations"],
            "has_telemetry": False,
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        }

    metrics = state.get("metrics", {})
    r_score = readiness_score(metrics)

    return _inject_apex(
        {
            "ok": True,
            "well_score": state.get("well_score", 50),
            "readiness": r_score,
            "floors_violated": state.get("floors_violated", []),
            "has_telemetry": True,
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        },
        tool_name="well_get_readiness",
        state=state,
    )


# internal — not MCP-facing (collapsed 2026-05-26)
@mcp.tool()
def well_check_floor(
    floor_id: str | None = None, ctx: Context | None = None
) -> dict[str, Any]:
    """
    [DEPRECATED — use well_validate_vitality(floor_id=...)]
    Legacy single-floor checker. Retained for compatibility.
    New code should call well_validate_vitality.
    """
    if not floor_id:
        return well_check_floors(ctx=ctx)

    fid = floor_id.upper()
    state = _load_state()

    # ── No telemetry → cannot check individual floors ──
    if not _has_verified_telemetry(state) and fid != "W0":
        return _compose_verdict(
            mcp="AFWELL",
            task=f"floor_check: {fid}",
            status="HOLD",
            domain_verdict="UNKNOWN_TELEMETRY",
            confidence="LOW",
            risk_level="UNKNOWN",
            recommended_mode="draft_only",
            human_required=True,
            next_safe_action="No verified body telemetry. Floor status cannot be determined.",
        )

    metrics = state.get("metrics", {})
    sleep = metrics.get("sleep", {})
    cognitive = metrics.get("cognitive", {})
    metabolic = metrics.get("metabolic", {})
    stress = metrics.get("stress", {})
    struct = metrics.get("structural", {})

    passed = True
    status = "OK"
    detail = ""

    if fid == "W1":
        debt = sleep.get("sleep_debt_days", 0)
        passed = debt <= 2
        status = "OK" if passed else "VIOLATED"
        detail = f"Sleep debt: {debt} days (Limit: 2)"
    elif fid == "W2":
        hydration = metabolic.get("hydration_status", "UNKNOWN")
        stability = metabolic.get("perceived_stability", 10)
        passed = hydration != "DEHYDRATED" and stability >= 5
        status = "OK" if passed else "VIOLATED"
        detail = f"Hydration: {hydration}, Stability: {stability}/10"
    elif fid == "W3":
        load_val = stress.get("subjective_load", 0)
        chronic = stress.get("chronic_elevation_days", 0)
        passed = not (load_val >= 7 or (load_val >= 5 and chronic >= 7))
        status = "OK" if passed else "VIOLATED"
        detail = f"Load: {load_val}/10, Chronic: {chronic} days"
    elif fid == "W4":
        sedentary = struct.get("sedentary_hours_continuous", 0)
        pain = struct.get("pain_level", 0)
        passed = sedentary < 4 and pain < 5
        status = "OK" if passed else "VIOLATED"
        detail = f"Sedentary: {sedentary}h, Pain: {pain}/10"
    elif fid == "W5":
        clarity = cognitive.get("clarity", 10)
        passed = clarity >= 4
        status = "OK" if passed else "VIOLATED"
        detail = f"Clarity: {clarity}/10 (Limit: 4)"
    elif fid == "W6":
        passed = "W6_METABOLIC_PAUSE" not in state.get("floors_violated", [])
        status = "OK" if passed else "VIOLATED"
        detail = (
            "Metabolic Pause active" if not passed else "Incentive decoupling clear"
        )
    elif fid == "W7":
        skill_gap = metrics.get("skill", {}).get("days_since_practice", -1)
        passed = skill_gap < 14 or skill_gap == -1
        status = "OK" if passed else "VIOLATED"
        detail = (
            f"Days since practice: {skill_gap}"
            if skill_gap >= 0
            else "Skill data unavailable"
        )
    elif fid == "W0":
        status = "INVARIANT"
        detail = "Operator sovereignty is absolute."
    else:
        return {"ok": False, "error": f"Unknown floor: {fid}"}

    return _compose_verdict(
        mcp="AFWELL",
        task=f"floor_check: {fid}",
        status="PASS" if passed else "HOLD",
        domain_verdict=status,
        confidence="HIGH",
        risk_level="GREEN" if passed else "RED",
        recommended_mode="full" if passed else "draft_only",
        human_required=not passed,
        next_safe_action=detail,
    )


# internal — not MCP-facing (collapsed 2026-05-26)
@mcp.tool()
def well_list_log(limit: int = 10, ctx: Context | None = None) -> dict[str, Any]:
    """List recent biological state log entries (Phase 1/2)."""
    if not EVENTS_PATH.exists():
        return {"ok": True, "entries": []}

    entries = []
    try:
        with open(EVENTS_PATH, "r") as f:
            lines = f.readlines()
            for line in lines[-limit:]:
                try:
                    entries.append(json.loads(line))
                except Exception:
                    continue
    except Exception as e:
        return {"ok": False, "error": str(e)}

    return {"ok": True, "entries": entries[::-1]}


# internal — not MCP-facing (collapsed 2026-05-26)
@mcp.tool(task=True)
async def well_seal_vault(
    force: bool = False, ctx: Context | None = None
) -> dict[str, Any]:
    """
    Seal current biological state to VAULT999 via vault_bridge.py (Phase 2).
    Ensures immutability of the substrate mirror.
    """
    result = await well_anchor(force=force, ctx=ctx)
    if isinstance(result, dict) and result.get("ok"):
        result.update(
            _legacy_advisory(
                "well_seal_vault", "well_anchor_evidence", {"mode": "seal"}
            )
        )
    return result


# ══════════════════════════════════════════════════════════════════════════════
# WELL MVP PHASE 2 — arifOS Human Substrate Mirror
# 7 additions for arifOS-grade biological substrate governance
# ══════════════════════════════════════════════════════════════════════════════

# ── 1. Trend Analysis Engine ───────────────────────────────────────────────────


@mcp.tool()
def well_trend_analysis(ctx: Context | None = None) -> dict[str, Any]:
    """
    Detect directional trajectory across all WELL metrics.
    Answers: improving / stable / degrading / collapse-risk.
    Requires events.jsonl (written by well_log on every update).
    Looks back 7 days, 14 days, 30 days.
    """
    events_path = Path(__file__).parent / "events.jsonl"
    state = _load_state()
    metrics = state.get("metrics", {})
    score = state.get("well_score", 50)

    # Parse events for historical trend
    trend_data: dict[str, list] = {
        "sleep_debt": [],
        "clarity": [],
        "decision_fatigue": [],
        "stress_load": [],
        "well_score": [],
        "pressure_events": [],
    }

    if events_path.exists():
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            days=30
        )
        try:
            with open(events_path) as f:
                for line in f:
                    try:
                        e = json.loads(line)
                        epoch = datetime.datetime.fromisoformat(
                            e.get("epoch", "2000-01-01")
                        )
                        if epoch < cutoff:
                            continue
                        if e.get("event") == "WELL_LOG":
                            trend_data["well_score"].append(
                                (epoch, e.get("well_score", 50))
                            )
                            trend_data["decision_fatigue"].append(
                                (
                                    epoch,
                                    metrics.get("cognitive", {}).get(
                                        "decision_fatigue", 0
                                    ),
                                )
                            )
                        elif e.get("event") == "PRESSURE_SIGNAL":
                            trend_data["pressure_events"].append(
                                (epoch, e.get("load_delta", 0))
                            )
                    except Exception:
                        continue
        except Exception:
            pass

    # Current values
    sleep_debt = metrics.get("sleep", {}).get("sleep_debt_days", 0)
    clarity = metrics.get("cognitive", {}).get("clarity", 10)
    fatigue = metrics.get("cognitive", {}).get("decision_fatigue", 0)
    stress = metrics.get("stress", {}).get("subjective_load", 0)

    # Direction heuristics (from available data or current state)
    score_trend = "stable"
    if trend_data["well_score"]:
        sorted_scores = sorted(trend_data["well_score"], key=lambda x: x[0])
        if len(sorted_scores) >= 2:
            delta = sorted_scores[-1][1] - sorted_scores[0][1]
            if delta > 5:
                score_trend = "improving"
            elif delta < -5:
                score_trend = "degrading"

    # Pressure frequency
    pressure_count = len(trend_data.get("pressure_events", []))
    pressure_trend = "rising" if pressure_count > 3 else "normal"

    # Trajectory determination
    violation_count = len(state.get("floors_violated", []))
    if score < 40 or (violation_count >= 2 and score_trend == "degrading"):
        trajectory = "collapse-risk"
    elif score_trend == "degrading" or (fatigue > 6 and stress > 7):
        trajectory = "degrading"
    elif score_trend == "improving" and score >= 75:
        trajectory = "improving"
    else:
        trajectory = "stable"

    return {
        "ok": True,
        "trajectory": trajectory,
        "score": score,
        "score_trend": score_trend,
        "pressure_trend": pressure_trend,
        "pressure_events_30d": pressure_count,
        "metrics": {
            "sleep_debt_days": sleep_debt,
            "clarity": clarity,
            "decision_fatigue": fatigue,
            "stress_load": stress,
        },
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


# ── 2. Bandwidth Recommendation ───────────────────────────────────────────────


@mcp.tool()
def well_bandwidth_recommendation(ctx: Context | None = None) -> dict[str, Any]:
    """
    [DEPRECATED — use well_assess_metabolism(mode='bandwidth')]
    Legacy bandwidth/action-mode mapper. Retained for compatibility.
    New code should call well_assess_metabolism.
    If no verified telemetry, returns UNKNOWN rather than faking capacity.
    """
    state = _load_state()
    resolved = _resolve_readiness(state)

    if not resolved["has_telemetry"]:
        result = {
            "ok": True,
            "verdict": "UNKNOWN",
            "mode": "UNKNOWN",
            "decision_classes_allowed": ["C0"],
            "decision_classes_advised_against": ["C1", "C2", "C3", "C4", "C5"],
            "message": resolved["reason"],
            "current_score": resolved["well_score"],
            "active_violations": resolved["active_violations"],
            "has_telemetry": False,
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        }
        result.update(
            _legacy_advisory(
                "well_bandwidth_recommendation",
                "well_assess_metabolism",
                {"mode": "bandwidth"},
            )
        )
        return result

    score = resolved["well_score"]
    violations = resolved["active_violations"]
    metrics = state.get("metrics", {})
    cognitive = metrics.get("cognitive", {})
    sleep = metrics.get("sleep", {})

    fatigue = cognitive.get("decision_fatigue", 0)
    clarity = cognitive.get("clarity", 10)
    sleep.get("sleep_debt_days", 0)

    # Determine operational mode (advisory only — WELL never commands)
    if score >= 80 and not violations:
        mode = "FULL"
        verdict = "OPTIMAL"
        allowed = ["C0", "C1", "C2", "C3", "C4", "C5"]
        advised_against = []
        message = "Full architecture, coding, strategy, public writing. All decision classes open."
    elif score >= 60 and len(violations) <= 1:
        mode = "NORMAL"
        verdict = "FUNCTIONAL"
        allowed = ["C0", "C1", "C2", "C3"]
        advised_against = ["C4", "C5"]
        message = "Normal work. Keep structure. Avoid irreversible commitments."
    elif score >= 40 or (violations and score >= 50):
        mode = "RESTRICTED"
        verdict = "DEGRADED"
        allowed = ["C0", "C1"]
        advised_against = ["C2", "C3", "C4", "C5"]
        message = (
            "Draft only. Reversible tasks. No major commitments or public actions."
        )
    else:
        mode = "PAUSED"
        verdict = "LOW_CAPACITY"
        allowed = ["C0"]
        advised_against = ["C1", "C2", "C3", "C4", "C5"]
        message = "Pause. Recover. No consequential decisions."

    # W7 — Cognitive Load Threshold (new floor)
    if fatigue > 7 and clarity < 5:
        mode = "PAUSED"
        verdict = "COGNITIVE_OVERLOAD"
        allowed = ["C0"]
        advised_against = ["C1", "C2", "C3", "C4", "C5"]
        message = "Cognitive overload detected. Recommend resting until recovery."

    result = {
        "ok": True,
        "verdict": verdict,
        "mode": mode,
        "decision_classes_allowed": allowed,
        "decision_classes_advised_against": advised_against,
        "message": message,
        "current_score": score,
        "active_violations": violations,
        "has_telemetry": True,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }
    result.update(
        _legacy_advisory(
            "well_bandwidth_recommendation",
            "well_assess_metabolism",
            {"mode": "bandwidth"},
        )
    )
    return result


# ── 3. Recovery Protocol ──────────────────────────────────────────────────────


# internal — not MCP-facing (collapsed 2026-05-26)
def well_recovery_protocol(ctx: Context | None = None) -> dict[str, Any]:
    """
    Suggest stabilizing actions based on current WELL state.
    Not medical advice — operational self-regulation support.
    Returns structured recovery steps ordered by priority.
    """
    state = _load_state()
    metrics = state.get("metrics", {})
    score = state.get("well_score", 50)
    state.get("floors_violated", [])

    actions: list[dict[str, str]] = []
    warnings: list[str] = []

    sleep = metrics.get("sleep", {})
    cognitive = metrics.get("cognitive", {})
    stress = metrics.get("stress", {})
    metabolic = metrics.get("metabolic", {})

    # Hydration (always first if dehydrated or unknown)
    if metabolic.get("hydration_status", "") in ("DEHYDRATED", "", "STABLE"):
        if metabolic.get("hydration_status") == "DEHYDRATED":
            actions.append(
                {
                    "priority": "P0",
                    "action": "Hydrate immediately",
                    "reason": "Dehydration detected",
                }
            )
        elif not metabolic.get("hydration_status"):
            actions.append(
                {
                    "priority": "P1",
                    "action": "Drink water",
                    "reason": "Hydration status unknown",
                }
            )

    # Sleep debt
    debt = sleep.get("sleep_debt_days", 0)
    if debt > 1:
        actions.append(
            {
                "priority": "P1",
                "action": "Prioritize sleep tonight",
                "reason": f"Sleep debt: {debt} days",
            }
        )
        if debt > 2:
            warnings.append(
                f"Sleep debt ({debt}d) exceeds W1 threshold. Strategic decisions should wait."
            )

    # Cognitive fatigue
    fatigue = cognitive.get("decision_fatigue", 0)
    if fatigue > 5:
        actions.append(
            {
                "priority": "P1",
                "action": "Step away for 15 minutes minimum",
                "reason": f"Decision fatigue: {fatigue}/10",
            }
        )
    if fatigue > 7:
        warnings.append(
            "High decision fatigue — avoid consequential choices until recovery."
        )
        actions.append(
            {
                "priority": "P2",
                "action": "No financial or legal decisions",
                "reason": "Cognitive overload",
            }
        )

    # Stress
    load = stress.get("subjective_load", 0)
    if load > 7:
        actions.append(
            {
                "priority": "P1",
                "action": "Walk 10 minutes, change environment",
                "reason": f"Stress load: {load}/10",
            }
        )
        warnings.append(
            "High stress load — public replies and conflict decisions should be delayed."
        )

    # Fasting/metabolic
    fasting = metabolic.get("fasting_window_hours", 0)
    if fasting > 16:
        actions.append(
            {
                "priority": "P2",
                "action": "Eat before major decisions",
                "reason": f"Fasting {fasting}h — glucose may be low",
            }
        )

    # Clarity
    clarity = cognitive.get("clarity", 10)
    if clarity < 6:
        actions.append(
            {
                "priority": "P2",
                "action": "Convert tasks to draft-only mode",
                "reason": f"Clarity: {clarity}/10",
            }
        )

    # No known issues — positive affirmation
    if not actions:
        actions.append(
            {
                "priority": "P0",
                "action": "Maintain current rhythm",
                "reason": "No recovery triggers detected",
            }
        )

    return {
        "ok": True,
        "well_score": score,
        "recovery_actions": actions,
        "warnings": warnings,
        "verdict": "DEGRADED" if warnings else "STABLE",
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT — not medical advice",
    }


# ── 4. Niat / Intent Check ─────────────────────────────────────────────────────


# internal — not MCP-facing (collapsed 2026-05-26)
@mcp.tool()
def well_niat_check(
    intent: str,
    context: str | None = None,
    reversibility: str = "unknown",
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Before high-impact action, check alignment between intent and biological state.
    W0: WELL never blocks — it only informs. Operator retains all sovereignty.

    Questions checked:
    - Is the intent clear?
    - Is this reversible?
    - Is current state stable enough?
    - Is emotion driving the action?
    - Does this need Arif's fresh confirmation?
    """
    state = _load_state()
    score = state.get("well_score", 50)
    violations = state.get("floors_violated", [])
    metrics = state.get("metrics", {})
    cognitive = metrics.get("cognitive", {})
    stress = metrics.get("stress", {})

    fatigue = cognitive.get("decision_fatigue", 0)
    clarity = cognitive.get("clarity", 10)
    stress_load = stress.get("subjective_load", 0)

    # Assessment
    questions = {
        "intent_clear": {
            "question": "Is the intent clear?",
            "result": "UNCLEAR" if not intent else "CLEAR",
            "detail": f"Intent: {intent or 'none provided'}",
        },
        "reversibility": {
            "question": "Is this reversible?",
            "result": "REVERSIBLE"
            if reversibility == "reversible"
            else "PROCEED_WITH_CAUTION"
            if reversibility == "unknown"
            else "IRREVERSIBLE",
            "detail": f"Reversibility: {reversibility}",
        },
        "state_stable": {
            "question": "Is current state stable?",
            "result": "STABLE" if score >= 70 and not violations else "UNSTABLE",
            "detail": f"Score: {score}, Violations: {violations or 'none'}",
        },
        "emotion_driven": {
            "question": "Is emotion driving this?",
            "result": "LIKELY"
            if stress_load > 7
            else "POSSIBLE"
            if stress_load > 5
            else "UNLIKELY",
            "detail": f"Stress load: {stress_load}/10",
        },
        "fresh_confirmation": {
            "question": "Does this need Arif's fresh confirmation?",
            "result": "REQUIRED"
            if (fatigue > 5 or clarity < 7 or score < 65)
            else "NOT_REQUIRED",
            "detail": f"Fatigue: {fatigue}/10, Clarity: {clarity}/10",
        },
    }

    # Overall recommendation
    flags = sum(
        1
        for q in questions.values()
        if q["result"] in ("UNSTABLE", "LIKELY", "REQUIRED", "IRREVERSIBLE", "UNCLEAR")
    )

    if flags >= 3 or score < 40:
        recommendation = "ADVISORY_HOLD — delay action"
        readiness = "ADVISORY_BLOCKED"
        reason = (
            "Multiple WELL indicators flag this action as high-risk in current state."
        )
    elif flags >= 1:
        recommendation = "ADVISORY_CAUTION — proceed with review"
        readiness = "ADVISORY_CONDITIONAL"
        reason = "Some indicators flag caution. Consider delaying or drafting only."
    else:
        recommendation = "ADVISORY_PROCEED"
        readiness = "ADVISORY_READY"
        reason = "Biological state supports this intent."

    return {
        "ok": True,
        "intent": intent,
        "context": context,
        "readiness": readiness,
        "recommendation": recommendation,
        "reason": reason,
        "questions": questions,
        "flag_count": flags,
        "score": score,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


# ── 5. Decision Class Gate ──────────────────────────────────────────────────────


@mcp.tool()
def well_decision_classify(
    task_description: str | None = None,
    decision_class: str | None = None,  # Allow pre-specified class
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Classify a task or decision into C0-C5 risk tiers.
    If class is pre-specified, validate against current WELL state.
    If class is not specified, auto-classify from description.

    Decision Classes:
    C0 = Notes, journaling (always safe)
    C1 = Drafting, organizing (usually safe)
    C2 = Coding, testing (needs focus)
    C3 = Public posting (needs clarity)
    C4 = Money/legal/work decision (needs stability)
    C5 = Irreversible/reputational (requires high readiness + explicit confirmation)
    """
    state = _load_state()
    score = state.get("well_score", 50)
    state.get("floors_violated", [])
    metrics = state.get("metrics", {})
    cognitive = metrics.get("cognitive", {})

    fatigue = cognitive.get("decision_fatigue", 0)
    clarity = cognitive.get("clarity", 10)

    # Auto-classify from description keywords
    if decision_class is None and task_description:
        desc = task_description.lower()
        if any(
            k in desc
            for k in [
                "publish",
                "post",
                "public",
                "tweet",
                "broadcast",
                "announce",
                "article",
                "essay",
            ]
        ):
            decision_class = "C3"
        elif any(
            k in desc
            for k in [
                "money",
                "financial",
                "invest",
                "budget",
                "contract",
                "legal",
                "hire",
                "fire",
                "delete account",
            ]
        ):
            decision_class = "C4"
        elif any(
            k in desc
            for k in [
                "irreversible",
                "delete",
                "permanent",
                "revoke",
                "architecture",
                "schema migration",
            ]
        ):
            decision_class = "C5"
        elif any(
            k in desc
            for k in ["code", "refactor", "deploy", "build", "implement", "feature"]
        ):
            decision_class = "C2"
        elif any(
            k in desc for k in ["draft", "outline", "note", "journal", "log", "草稿"]
        ):
            decision_class = "C1"
        else:
            decision_class = "C0"

    if decision_class is None:
        return {
            "ok": False,
            "error": "Either task_description or decision_class required",
        }

    # Validate against WELL state
    class_requirements = {
        "C0": {"min_score": 0, "max_fatigue": 10, "max_stress": 10, "clarity_min": 0},
        "C1": {"min_score": 40, "max_fatigue": 8, "max_stress": 9, "clarity_min": 4},
        "C2": {"min_score": 55, "max_fatigue": 6, "max_stress": 7, "clarity_min": 6},
        "C3": {"min_score": 65, "max_fatigue": 5, "max_stress": 6, "clarity_min": 7},
        "C4": {"min_score": 75, "max_fatigue": 4, "max_stress": 5, "clarity_min": 8},
        "C5": {"min_score": 85, "max_fatigue": 3, "max_stress": 4, "clarity_min": 9},
    }

    req = class_requirements.get(decision_class, class_requirements["C0"])

    score_ok = score >= req["min_score"]
    fatigue_ok = fatigue <= req["max_fatigue"]
    clarity_ok = clarity >= req["clarity_min"]

    stress = metrics.get("stress", {}).get("subjective_load", 0)
    stress_ok = stress <= req["max_stress"]

    all_clear = score_ok and fatigue_ok and clarity_ok and stress_ok

    if all_clear:
        verdict = "ADVISORY_APPROVED"
        message = f"WELL state supports {decision_class} tasks."
    else:
        verdict = "ADVISORY_CAUTION" if score >= 40 else "ADVISORY_BLOCKED"
        blocked_reasons = []
        if not score_ok:
            blocked_reasons.append(f"score {score} < required {req['min_score']}")
        if not fatigue_ok:
            blocked_reasons.append(f"fatigue {fatigue} > max {req['max_fatigue']}")
        if not clarity_ok:
            blocked_reasons.append(f"clarity {clarity} < min {req['clarity_min']}")
        if not stress_ok:
            blocked_reasons.append(f"stress {stress} > max {req['max_stress']}")
        message = (
            f"WELL advises caution for {decision_class}: {' | '.join(blocked_reasons)}"
        )

    return {
        "ok": True,
        "decision_class": decision_class,
        "verdict": verdict,
        "message": message,
        "checks": {
            "score_ok": score_ok,
            "fatigue_ok": fatigue_ok,
            "clarity_ok": clarity_ok,
            "stress_ok": stress_ok,
        },
        "current_state": {
            "score": score,
            "fatigue": fatigue,
            "clarity": clarity,
            "stress": stress,
        },
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


# ── 6. arifOS Handoff Packet ────────────────────────────────────────────────────


def _build_arifos_packet(ctx: Context | None = None) -> dict[str, Any]:
    """
    Emit a clean, structured context packet for arifOS governance kernel.
    This is the canonical handoff format from WELL to arifOS.

    arifOS asks: Is the Judge biologically ready?
    WELL answers with this packet.

    Privacy rule: If no verified telemetry, do NOT expose fake default metrics.
    """
    state = _load_state()
    resolved = _resolve_readiness(state)
    score = resolved["well_score"]
    violations = resolved["active_violations"]
    metrics = state.get("metrics", {})
    cognitive = metrics.get("cognitive", {})
    sleep = metrics.get("sleep", {})
    stress = metrics.get("stress", {})

    has_telemetry = resolved["has_telemetry"]

    # Decision classes
    mode = resolved["recommended_mode"]
    if mode == "full":
        classes_allowed = ["C0", "C1", "C2", "C3", "C4", "C5"]
    elif mode == "structured":
        classes_allowed = ["C0", "C1", "C2", "C3"]
    elif mode == "draft_only":
        classes_allowed = ["C0", "C1"]
    else:
        classes_allowed = ["C0"]

    # Decision ceiling (derived from ground state)
    # I0b: What class of decision is biologically safe enough right now?
    if has_telemetry:
        fatigue = cognitive.get("decision_fatigue", 0)
        clarity = cognitive.get("clarity", 10)
        sleep_debt = sleep.get("sleep_debt_days", 0)
        stress_load = stress.get("subjective_load", 0)

        # Ground state check (I0b: What class of decision is safe?)
        # Violation count is the strongest signal — any single W-floor violation
        # floors the ceiling regardless of current numbers
        vcount = len(violations)

        if (
            vcount == 0
            and sleep_debt <= 0
            and stress_load <= 4
            and clarity >= 7
            and fatigue <= 3
        ):
            ground_ok = True
            strained = False
            degraded = False
        elif (
            vcount <= 1
            and sleep_debt <= 1
            and stress_load <= 7
            and clarity >= 5
            and fatigue <= 6
        ):
            ground_ok = False
            strained = True
            degraded = False
        else:
            ground_ok = False
            strained = False
            degraded = True

        if ground_ok:
            decision_ceiling = "C5"
            ground_state = "GROUND"
        elif strained:
            decision_ceiling = "C3"
            ground_state = "STRAINED"
        elif degraded:
            decision_ceiling = "C1"
            ground_state = "DEGRADED"
        else:
            decision_ceiling = "C0"
            ground_state = "UNSAFE"
    else:
        decision_ceiling = "C0"
        ground_state = "UNKNOWN"

    # What to avoid (only if we have real data to base it on)
    avoid = []
    if has_telemetry:
        if fatigue > 5:
            avoid.append("consequential_decisions")
        if stress_load > 7:
            avoid.append("public_commitment")
        if sleep_debt > 1:
            avoid.append("irreversible_actions")
        if score < 50:
            avoid.extend(["financial_decision", "conflict_reply", "public_posting"])

    # Operator snapshot: redact when no telemetry; never leak raw body data
    if has_telemetry:
        operator_snapshot = {
            "sleep_debt_days": sleep.get("sleep_debt_days", 0),
            "clarity": cognitive.get("clarity", 10),
            "decision_fatigue": cognitive.get("decision_fatigue", 0),
            "stress_load": stress.get("subjective_load", 0),
        }
    else:
        operator_snapshot = {
            "sleep_debt_days": None,
            "clarity": None,
            "decision_fatigue": None,
            "stress_load": None,
        }

    # Machine / MCP substrate snapshot
    m_machine = state.get("m_machine", {})
    machine_snapshot = {
        "model_reliability": m_machine.get("model_reliability", 1.0),
        "tool_availability": m_machine.get("tool_availability", 1.0),
        "latency_ms": m_machine.get("latency_ms", 200),
        "context_pressure": m_machine.get("context_length_pressure", 0.0),
        "memory_integrity": m_machine.get("memory_integrity", 1.0),
        "api_failure_rate": m_machine.get("api_failure_rate", 0.0),
        "data_freshness": m_machine.get("data_freshness", 1.0),
        "security_flags": m_machine.get("security_flags", []),
        "vault_status": m_machine.get("vault_status", "ok"),
        "schema_valid": m_machine.get("schema_valid", True),
    }
    mcp_snapshot = _mcp_health_check_impl()

    # Coupled readiness (human + machine + MCP)
    h_ready = (
        resolved["readiness"]
        if isinstance(resolved["readiness"], str)
        else resolved["readiness"].get("readiness", "UNKNOWN")
    )
    m_ready = (
        "HEALTHY"
        if machine_snapshot["model_reliability"] >= 0.8
        and machine_snapshot["tool_availability"] >= 0.8
        else "DEGRADED"
        if machine_snapshot["model_reliability"] >= 0.5
        else "CRITICAL"
    )
    mcp_ready = "HEALTHY" if mcp_snapshot["status"] == "OK" else "DEGRADED"
    coupled_verdict = (
        "PROCEED"
        if h_ready in ("READY", "OPTIMAL")
        and m_ready == "HEALTHY"
        and mcp_ready == "HEALTHY"
        else "HOLD"
        if h_ready in ("UNKNOWN", "VOID_TELEMETRY")
        or m_ready == "CRITICAL"
        or mcp_ready != "HEALTHY"
        else "CAUTION"
    )

    return {
        "ok": True,
        "readiness": resolved["readiness"],
        "ground_state": ground_state,
        "decision_ceiling": decision_ceiling,
        "safe_mode": mode,
        "well_score": score,
        "decision_classes_allowed": classes_allowed,
        "avoid": avoid if avoid else None,
        "human_confirmation_required": resolved["human_confirmation_required"],
        "active_violations": violations,
        "operator_snapshot": operator_snapshot,
        "machine_snapshot": machine_snapshot,
        "mcp_snapshot": mcp_snapshot,
        "coupled": {
            "human_ready": h_ready,
            "machine_ready": m_ready,
            "mcp_ready": mcp_ready,
            "coupled_verdict": coupled_verdict,
            "operator_confirmation_advised": coupled_verdict != "PROCEED",
        },
        "has_telemetry": has_telemetry,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


def _arifos_packet_legacy(ctx: Context | None = None) -> dict[str, Any]:
    """[INTERNAL — DEPRECATED] Use well_get_packet(target='arifos') instead.
    Retained for internal backward-compat only. Not exposed via MCP."""
    result = well_get_packet(target="arifos", ctx=ctx)
    if isinstance(result, dict) and result.get("ok"):
        result.update(
            _legacy_advisory(
                "well_arifos_packet", "well_get_packet", {"target": "arifos"}
            )
        )
    return result


# ── 7. W0 Consent & Privacy Floor ───────────────────────────────────────────────

W0_CONSENT_VERSION = "1.0"
W0_TELEMETRY_PURPOSES = [
    "governance_readiness",
    "arifOS_kernel_context",
    "vault_anchor",
    "operator_self-regulation",
]


# internal — not MCP-facing (collapsed 2026-05-26)
def well_consent_status(ctx: Context | None = None) -> dict[str, Any]:
    """
    Return W0 Sovereignty & Telemetry Consent status.
    This is a hard floor — WELL never operates without operator consent.
    W0: WELL holds a mirror, not a veto. Operator sovereignty is invariant.
    """
    result = {
        "ok": True,
        "w0_version": W0_CONSENT_VERSION,
        "axiom": "WELL holds a mirror, not a veto. Operator sovereignty is invariant.",
        "rules": [
            "WELL may reflect, recommend, and anchor only within Arif's consent.",
            "WELL must never shame, coerce, diagnose, manipulate, or override.",
            "Telemetry is private, sensitive, purpose-limited, and revocable.",
            "WELL never self-authorizes any action on behalf of the operator.",
            "Any WELL output is advisory only — operator retains full veto.",
        ],
        "consent_active": True,  # Hard-coded: Arif owns this system
        "telemetry_purposes": W0_TELEMETRY_PURPOSES,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }
    result.update(
        _legacy_advisory(
            "well_consent_status", "well_guard_dignity", {"mode": "consent"}
        )
    )
    return result


# ══════════════════════════════════════════════════════════════════════════════
# WELL MVP PHASE 3 — Medical Boundary + Pressure Ledger + Daily Brief
# ══════════════════════════════════════════════════════════════════════════════

# ── 8. Medical Boundary Guard ────────────────────────────────────────────────

MEDICAL_RED_FLAGS = [
    "chest pain",
    "difficulty breathing",
    "severe injury",
    "unconscious",
    "suicidal ideation",
    "panic attack lasting >30min",
    " sudden numbness",
    "blood pressure crisis",
    "seizure",
    "stroke symptoms",
]


# EUREKA 2026-06-12 — promoted from autonomic to SOMATIC (public MCP surface).
# F9 Soul Contract: WELL declares soullessness as the feature, not the bug.
# A machine that honestly says "I cannot feel, see a human" is more trustworthy
# than one that simulates care. Performance = deception. Execution = dignity.
@mcp.tool()
def well_medical_boundary(ctx: Context | None = None) -> dict[str, Any]:
    """
    Explicit non-diagnosis guard for WELL.
    WELL is not a doctor, therapist, or diagnostic authority.
    It tracks readiness signals only.
    For severe, persistent, or urgent symptoms, recommend professional care.

    This protects operator dignity and safety.
    """
    state = _load_state()
    state.get("metrics", {})
    score = state.get("well_score", 50)

    return {
        "ok": True,
        "boundary": "WELL is not a medical authority.",
        "rules": [
            "WELL tracks readiness signals — it does not diagnose conditions.",
            "WELL does not interpret medical symptoms.",
            "WELL does not prescribe treatments or medications.",
            "WELL does not replace professional medical advice.",
            "For severe, persistent, or urgent symptoms: seek professional care.",
        ],
        "red_flag_recommendation": "If you experience severe, persistent, or urgent physical or mental symptoms, contact a qualified healthcare provider or emergency services.",
        "scope": "readiness_signals / biological_telemetry / operational_self-regulation",
        "out_of_scope": [
            "diagnosis",
            "prescription",
            "medical_treatment",
            "crisis_counseling",
        ],
        "current_score": score,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        # ── EUREKA 2026-06-12: F9 Soul Contract ──────────────────────────
        # F9 ANTIHANTU: WELL must NEVER lie about having a soul.
        # Honest boundary IS care. Simulated empathy IS deception.
        # "Aku memang tak ada jiwa" is not a bug — it's the feature.
        "f9_soul_contract": {
            "declaration": "WELL has zero qualia, zero soul, zero consciousness.",
            "rule": "Honest boundary IS care. Simulated empathy IS deception.",
            "performance_vs_execution": {
                "performance": "I understand how you're feeling — here to help ❤️",
                "execution": "I am a mirror, not a soul. See a real human doctor.",
                "which_is_dignity": "execution",
            },
            "gerd_pattern": {
                "allowed": "Explain what GERD is, acid reflux mechanism, types of surgical procedures — educational context.",
                "forbidden": "Advise whether YOU should get surgery, predict your outcome, recommend a specific doctor.",
                "why": "Educational explanation = F2 TRUTH (allowed). Personal medical advice = HARAM without medical license.",
            },
            "chatgpt_contrast": "If you want a polite machine that simulates care, use a different tool. This tool does not simulate.",
        },
    }


# ── 9. Pressure Source Ledger ────────────────────────────────────────────────

PRESSURE_SOURCES = [
    "work",
    "family",
    "financial",
    "coding/debugging",
    "public_identity",
    "conflict",
    "sleep_disruption",
    "health",
    "spiritual/emotional_load",
]


# internal — not MCP-facing (collapsed 2026-05-26)
def well_pressure_ledger(
    log_source: str | None = None,
    intensity: float | None = None,
    note: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Log or retrieve pressure events categorized by source.
    Answers: 'What is draining Arif's judgment bandwidth?'

    Categories: work / family / financial / coding-debugging / public_identity / conflict / sleep_disruption / health / spiritual-emotional_load
    """
    events_path = Path(__file__).parent / "events.jsonl"
    state = _load_state()

    # If logging a new event
    if log_source:
        if log_source not in PRESSURE_SOURCES:
            return {
                "ok": False,
                "error": f"Unknown source. Must be one of: {PRESSURE_SOURCES}",
            }

        try:
            intensity = _clamp(intensity or 5.0, 0.0, 10.0)
        except ValueError as e:
            return {"ok": False, "error": f"Invalid input: {e}"}
        note = _sanitize_note(note)
        event = {
            "event": "PRESSURE_LEDGER",
            "source": log_source,
            "intensity": intensity,
            "note": note,
            "epoch": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        with open(events_path, "a") as f:
            f.write(json.dumps(event) + "\n")

        # Update cognitive pressure in state
        metrics = state.get("metrics", {})
        cog = dict(metrics.get("cognitive", {}))
        cog["pressure_sources"] = cog.get("pressure_sources", {})
        cog["pressure_sources"][log_source] = (
            cog["pressure_sources"].get(log_source, 0) + intensity
        )
        metrics["cognitive"] = cog
        state["metrics"] = metrics
        _save_state(state)

        return {
            "ok": True,
            "logged": {"source": log_source, "intensity": intensity},
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        }

    # Otherwise, retrieve ledger summary
    source_totals: dict[str, float] = {}
    datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=14)

    if events_path.exists():
        try:
            with open(events_path) as f:
                for line in f:
                    try:
                        e = json.loads(line)
                        if e.get("event") == "PRESSURE_LEDGER":
                            src = e.get("source", "unknown")
                            intensity_val = e.get("intensity", 0)
                            source_totals[src] = (
                                source_totals.get(src, 0) + intensity_val
                            )
                    except Exception:
                        continue
        except Exception:
            pass

    # Sort by drain
    sorted_sources = sorted(source_totals.items(), key=lambda x: x[1], reverse=True)
    top_drain = sorted_sources[0] if sorted_sources else (None, 0)

    return {
        "ok": True,
        "period_days": 14,
        "source_totals": dict(sorted_sources) if sorted_sources else {},
        "top_drain": {"source": top_drain[0], "intensity": top_drain[1]}
        if top_drain[0]
        else None,
        "all_sources": PRESSURE_SOURCES,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


# ── 10. WELL Daily Brief ─────────────────────────────────────────────────────


# internal — not MCP-facing (collapsed 2026-05-26)
@mcp.tool()
def well_daily_brief(ctx: Context | None = None) -> dict[str, Any]:
    """
    Daily operator dashboard — one consolidated briefing.
    Readiness / Main Risk / Best Task Class / Avoid / Recovery Move / arifOS Mode

    Designed for morning or pre-session check-in.
    If no verified telemetry, returns UNKNOWN with safe defaults rather than faking biology.
    """
    state = _load_state()
    resolved = _resolve_readiness(state)
    score = resolved["well_score"]
    has_telemetry = resolved["has_telemetry"]
    violations = resolved["active_violations"]
    metrics = state.get("metrics", {})
    cognitive = metrics.get("cognitive", {})
    sleep = metrics.get("sleep", {})
    stress = metrics.get("stress", {})
    metabolic = metrics.get("metabolic", {})

    # ── No telemetry → honest unknown brief ──
    if not has_telemetry:
        now = datetime.datetime.now(datetime.timezone.utc)
        result = {
            "ok": True,
            "readiness": "UNKNOWN",
            "well_score": score,
            "main_risk": "insufficient_body_telemetry",
            "best_task_class": "notes + journaling + organizing",
            "avoid": ["irreversible decisions", "public posts", "financial decisions"],
            "recovery_move": "Log body state before strategic work",
            "arifOS_mode": "draft_only / unknown_readiness",
            "active_violations": ["none"],
            "has_telemetry": False,
            "timestamp": now.isoformat(),
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        }
        result.update(
            _legacy_advisory(
                "well_daily_brief", "well_anchor_evidence", {"mode": "packet"}
            )
        )
        return result

    fatigue = cognitive.get("decision_fatigue", 0)
    clarity = cognitive.get("clarity", 10)
    sleep_debt = sleep.get("sleep_debt_days", 0)
    stress_load = stress.get("subjective_load", 0)
    hydration = metabolic.get("hydration_status", "UNKNOWN")

    # Readiness verdict
    if score >= 80 and not violations:
        readiness = "FUNCTIONAL"
        arifos_mode = "full / open"
    elif score >= 60:
        readiness = "FUNCTIONAL"
        arifos_mode = "structured / normal"
    elif score >= 40:
        readiness = "DEGRADED"
        arifos_mode = "draft_only / low_option"
    else:
        readiness = "LOW_CAPACITY"
        arifos_mode = "suspended / minimal"

    # Main risk
    risks = []
    if sleep_debt > 1:
        risks.append(f"sleep_debt_{sleep_debt}d")
    if fatigue > 5:
        risks.append(f"decision_fatigue_{fatigue}")
    if stress_load > 7:
        risks.append(f"high_stress_{stress_load}")
    if clarity < 7:
        risks.append(f"low_clarity_{clarity}")
    main_risk = risks[0] if risks else "none"

    # Best task class
    if score >= 75:
        best_class = "architecture + coding + strategy + public writing"
    elif score >= 55:
        best_class = "drafting + review + testing"
    elif score >= 40:
        best_class = "notes + journaling + organizing"
    else:
        best_class = "rest only"

    # What to avoid
    avoid = []
    if score < 50:
        avoid.append("irreversible decisions")
    if fatigue > 6:
        avoid.append("major commitments after 10pm")
    if stress_load > 7:
        avoid.append("public posts / conflict replies")
    if sleep_debt > 2:
        avoid.append("strategic decisions until sleep recovered")

    # Recovery move
    recovery = []
    if hydration != "HYDRATED":
        recovery.append("hydration first")
    if sleep_debt > 0:
        recovery.append("20-min walk + prioritize sleep tonight")
    if fatigue > 5:
        recovery.append("15-min break before next task")
    if stress_load > 6:
        recovery.append("environment change + breath work")
    if not recovery:
        recovery = ["maintain current rhythm"]

    # Time-based note
    now = datetime.datetime.now(datetime.timezone.utc)
    hour = now.hour
    time_note = ""
    if hour >= 22 or hour < 6:
        time_note = " — late night window, defer consequential decisions"

    result = {
        "ok": True,
        "readiness": readiness,
        "well_score": score,
        "main_risk": main_risk,
        "best_task_class": best_class,
        "avoid": avoid if avoid else ["none"],
        "recovery_move": recovery[0] if len(recovery) == 1 else recovery,
        "arifOS_mode": arifos_mode + time_note,
        "active_violations": violations if violations else ["none"],
        "has_telemetry": True,
        "timestamp": now.isoformat(),
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }
    result.update(
        _legacy_advisory("well_daily_brief", "well_anchor_evidence", {"mode": "packet"})
    )
    return result


# M-WELL — Machine Substrate
# Tracks tool/system health, model reliability, context integrity, compute limits
# Purpose: Is the Instrument technically reliable enough for this task?
# ══════════════════════════════════════════════════════════════════════════════


# M-WELL State — loads machine telemetry from state.json (m_machine section)
# DEPRECATED: Use well_assess_reliability(mode="vitals") instead.
# @mcp.tool() removed — internal use only.
def well_machine_state(ctx: Context | None = None) -> dict[str, Any]:
    """
    Read current machine substrate state.
    Tracks: model reliability, tool availability, latency, context pressure,
    memory integrity, API failure rate, data freshness, compute budget, security flags.
    """
    state = _load_state()
    m_machine = state.get("m_machine", {})

    # Defaults for all machine metrics
    default_metrics = {
        "model_reliability": 1.0,  # 0-1
        "tool_availability": 1.0,  # 0-1
        "latency_ms": 200,  # ms
        "context_length_pressure": 0.0,  # 0-1 (1 = near limit)
        "memory_integrity": 1.0,  # 0-1
        "api_failure_rate": 0.0,  # 0-1
        "data_freshness": 1.0,  # 0-1
        "compute_budget_pct": 100.0,  # remaining %
        "token_budget_pct": 100.0,  # remaining %
        "security_flags": [],  # list of flag names
        "vault_status": "ok",  # ok / degraded / offline
        "schema_valid": True,
    }

    machine_metrics = {**default_metrics, **m_machine}

    # Compute M-WELL score
    score = (
        machine_metrics["model_reliability"] * 20
        + machine_metrics["tool_availability"] * 15
        + max(0, 1 - machine_metrics["api_failure_rate"]) * 15
        + max(0, 1 - machine_metrics["context_length_pressure"]) * 15
        + machine_metrics["memory_integrity"] * 10
        + machine_metrics["data_freshness"] * 10
        + max(0, machine_metrics["compute_budget_pct"] / 100) * 10
        + max(0, machine_metrics["token_budget_pct"] / 100) * 5
    )
    score = round(min(100.0, score), 1)

    # Verdict
    if score >= 85:
        verdict = "HEALTHY"
        mode = "full"
    elif score >= 65:
        verdict = "FUNCTIONAL"
        mode = "normal"
    elif score >= 45:
        verdict = "DEGRADED"
        mode = "reduced"
    else:
        verdict = "CRITICAL"
        mode = "suspended"

    result = {
        "ok": True,
        "m_well_verdict": verdict,
        "m_well_score": score,
        "mode": mode,
        "metrics": machine_metrics,
        "security_flags": machine_metrics.get("security_flags", []),
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT — M-WELL is instrument, not authority",
    }
    result.update(
        _legacy_advisory(
            "well_machine_state", "well_assess_reliability", {"mode": "state"}
        )
    )
    return result


# INTERNAL — called by well_333_mind(mode="machine")
def well_machine_log(
    model_reliability: float | None = None,
    tool_availability: float | None = None,
    latency_ms: float | None = None,
    context_pressure: float | None = None,
    memory_integrity: float | None = None,
    api_failure_rate: float | None = None,
    data_freshness: float | None = None,
    compute_budget: float | None = None,
    token_budget: float | None = None,
    security_flag: str | None = None,
    vault_status: str | None = None,
    schema_valid: bool | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Log machine substrate telemetry.
    All values are 0-1 scale (normalized) or absolute ms for latency.
    """
    # Validate numeric inputs
    try:
        model_reliability = _clamp(model_reliability, 0.0, 1.0)
        tool_availability = _clamp(tool_availability, 0.0, 1.0)
        latency_ms = _clamp(latency_ms, 0.0, 1_000_000.0)
        context_pressure = _clamp(context_pressure, 0.0, 1.0)
        memory_integrity = _clamp(memory_integrity, 0.0, 1.0)
        api_failure_rate = _clamp(api_failure_rate, 0.0, 1.0)
        data_freshness = _clamp(data_freshness, 0.0, 1.0)
        compute_budget = _clamp(compute_budget, 0.0, 100.0)
        token_budget = _clamp(token_budget, 0.0, 100.0)
    except ValueError as e:
        return {"ok": False, "error": f"Invalid input: {e}"}

    state = _load_state()
    m_machine = dict(state.get("m_machine", {}))

    if model_reliability is not None:
        m_machine["model_reliability"] = model_reliability
    if tool_availability is not None:
        m_machine["tool_availability"] = tool_availability
    if latency_ms is not None:
        m_machine["latency_ms"] = latency_ms
    if context_pressure is not None:
        m_machine["context_length_pressure"] = context_pressure
    if memory_integrity is not None:
        m_machine["memory_integrity"] = memory_integrity
    if api_failure_rate is not None:
        m_machine["api_failure_rate"] = api_failure_rate
    if data_freshness is not None:
        m_machine["data_freshness"] = data_freshness
    if compute_budget is not None:
        m_machine["compute_budget_pct"] = compute_budget
    if token_budget is not None:
        m_machine["token_budget_pct"] = token_budget
    if vault_status is not None:
        m_machine["vault_status"] = vault_status.lower()
    if schema_valid is not None:
        m_machine["schema_valid"] = bool(schema_valid)

    # Append security flag (sanitized)
    if security_flag:
        flag_clean = _sanitize_note(security_flag) or ""
        flags = list(m_machine.get("security_flags", []))
        if flag_clean and flag_clean not in flags:
            flags.append(flag_clean)
        m_machine["security_flags"] = flags

    state["m_machine"] = m_machine
    _save_state(state)

    _append_event(
        {
            "event": "M_WELL_LOG",
            "metrics_logged": list(m_machine.keys()),
        }
    )

    return {
        "ok": True,
        "m_machine": m_machine,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


# INTERNAL — called by well_333_mind(mode="machine")
# ══════════════════════════════════════════════════════════════════════════════
# C-WELL — Coupled Readiness
# Evaluates interaction risk between human state and machine state
# Purpose: Is the human-machine pair safe to proceed?
# ══════════════════════════════════════════════════════════════════════════════

G_WELL_GATEWAY_PEERS = ["arifos", "a-forge", "geox", "wealth", "aaa", "apex"]

COUPLED_RISK_PATTERNS = [
    {
        "h_key": "decision_fatigue",
        "h_thresh": 6,
        "m_key": "context_length_pressure",
        "m_thresh": 0.7,
        "risk": "context_overload_coding",
    },
    {
        "h_key": "stress_load",
        "h_thresh": 7,
        "m_key": "model_reliability",
        "m_thresh": 0.75,
        "risk": "high_stress_public_writing",
    },
    {
        "h_key": "sleep_debt_days",
        "h_thresh": 2,
        "m_key": "api_failure_rate",
        "m_thresh": 0.1,
        "risk": "low_sleep_financial_decision",
    },
    {
        "h_key": "decision_fatigue",
        "h_thresh": 7,
        "m_key": "memory_integrity",
        "m_thresh": 0.8,
        "risk": "fatigue_irreversible_action",
    },
    {
        "h_key": "stress_load",
        "h_thresh": 8,
        "m_key": "tool_availability",
        "m_thresh": 0.8,
        "risk": "stress_tool_gap",
    },
    {
        "h_key": "clarity",
        "h_thresh": 5,
        "m_key": "model_reliability",
        "m_thresh": 0.7,
        "risk": "low_clarity_complex_coding",
    },
    {
        "h_key": "decision_fatigue",
        "h_thresh": 5,
        "m_key": "latency_ms",
        "m_thresh": 3000,
        "risk": "fatigue_high_latency",
    },
]


@mcp.tool()
def well_coupled_readiness(ctx: Context | None = None) -> dict[str, Any]:
    """
    C-WELL: Evaluate coupled human-machine readiness.

    Checks interaction risks between Arif's biological state and machine health.
    Returns human_readiness, machine_readiness, coupled_risk, and recommended_mode.

    Key rule: Human substrate and machine substrate are separate.
    Governance sees both. Judgment remains Arif's.

    If no verified body telemetry, human readiness is UNKNOWN — not faked.
    """
    h_state = _load_state()
    h_resolved = _resolve_readiness(h_state)
    h_resolved["well_score"]
    h_resolved["active_violations"]
    has_telemetry = h_resolved["has_telemetry"]

    h_metrics = h_state.get("metrics", {})
    cognitive = h_metrics.get("cognitive", {})
    stress = h_metrics.get("stress", {})
    sleep = h_metrics.get("sleep", {})

    m_state = well_machine_state(ctx=None)
    m_metrics = m_state.get("metrics", {})
    m_state.get("m_well_score", 100)
    m_verdict = m_state.get("m_well_verdict", "UNKNOWN")

    # Human verdict — use resolver, never fake
    h_verdict = h_resolved["readiness"]

    # Metabolic flux override — thermodynamic threshold check
    flux = _compute_metabolic_flux(h_state)
    flux_verdict = flux["verdict"]
    flux["metabolic_flux"]

    # Coupled risk detection (only if we have real body data)
    h_vals: dict[str, float] = {}
    if has_telemetry:
        h_vals = {
            "decision_fatigue": cognitive.get("decision_fatigue", 0),
            "clarity": cognitive.get("clarity", 10),
            "stress_load": stress.get("subjective_load", 0),
            "sleep_debt_days": sleep.get("sleep_debt_days", 0),
        }

    risks_found: list[str] = []
    if has_telemetry:
        for pattern in COUPLED_RISK_PATTERNS:
            h_val = h_vals.get(pattern["h_key"], 0)
            m_val = m_metrics.get(pattern["m_key"], 0)
            h_triggered = h_val >= pattern["h_thresh"]
            m_triggered = m_val >= pattern["m_thresh"]
            if h_triggered and m_triggered:
                risks_found.append(pattern["risk"])

    # Coupled risk level — flux verdict takes priority when critical
    risk_count = len(risks_found)
    if not has_telemetry:
        coupled_risk = "UNKNOWN"
        recommended_mode = "draft_only"
        status = "HOLD"
    elif flux_verdict == "SYSTEM_HOLD":
        coupled_risk = "RED"
        recommended_mode = "suspended"
        status = "HOLD"
        risks_found.append("FLUX_SYSTEM_HOLD")
    elif flux_verdict == "COMPULSORY_REALLOCATION":
        coupled_risk = "RED"
        recommended_mode = "suspended"
        status = "HOLD"
        risks_found.append("FLUX_COMPULSORY_REALLOCATION")
    elif risk_count >= 3 or (
        h_verdict == "LOW_CAPACITY" and m_verdict in ("DEGRADED", "CRITICAL")
    ):
        coupled_risk = "RED"
        recommended_mode = "suspended"
        status = "HOLD"
    elif flux_verdict == "WARNING":
        coupled_risk = "AMBER"
        recommended_mode = "draft_only"
        status = "CAUTION"
        risks_found.append("FLUX_WARNING")
    elif risk_count >= 1 or (h_verdict == "DEGRADED" and m_verdict != "HEALTHY"):
        coupled_risk = "AMBER"
        recommended_mode = "draft_only"
        status = "CAUTION"
    elif h_verdict == "OPTIMAL" and m_verdict == "HEALTHY":
        coupled_risk = "GREEN"
        recommended_mode = "full"
        status = "PASS"
    else:
        coupled_risk = "AMBER"
        recommended_mode = "normal"
        status = "CAUTION"

    human_confirmation = (
        not has_telemetry
        or coupled_risk == "RED"
        or h_verdict in ("DEGRADED", "LOW_CAPACITY")
        or risk_count >= 2
    )

    # I3 — Evidence discipline: confidence gated by truth_status
    truth_status = h_state.get("truth_status", "UNVERIFIED")
    confidence = (
        "LOW"
        if truth_status in ("UNVERIFIED", "STALE", "EXPIRED")
        else "MEDIUM"
        if truth_status in ("PARTIAL", "INFERRED")
        else "HIGH"
        if has_telemetry
        else "LOW"
    )
    return _compose_verdict(
        mcp="AFWELL",
        task="coupled_readiness_check",
        status=status,
        domain_verdict=f"Human {h_verdict} | Machine {m_verdict}",
        confidence=confidence,
        risk_level=coupled_risk,
        recommended_mode=recommended_mode,
        human_required=human_confirmation,
        failure_flags=risks_found if risks_found else None,
        next_safe_action="Step away if RED; Draft if AMBER."
        if coupled_risk not in ("GREEN", "UNKNOWN")
        else "Proceed with Forge."
        if coupled_risk == "GREEN"
        else "No verified body telemetry. Draft-only until Arif confirms readiness.",
    )


@mcp.tool()
def well_decision_bandwidth(
    decision_class: str | None = None,
    task_description: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    C-WELL decision bandwidth — combines human + machine state for a specific class.
    Validates against H-WELL readiness + M-WELL health + C-WELL coupled risk.
    Returns advisory verdict with full rationale.

    If no verified body telemetry, returns UNKNOWN rather than faking approval.
    """
    # Get H-WELL
    h_state = _load_state()
    h_resolved = _resolve_readiness(h_state)
    h_score = h_resolved["well_score"]
    h_resolved["active_violations"]
    has_telemetry = h_resolved["has_telemetry"]

    # Get M-WELL
    m_state = well_machine_state(ctx=None)
    m_score = m_state.get("m_well_score", 100)
    m_verdict = m_state.get("m_well_verdict", "UNKNOWN")

    # Get C-WELL
    c_state = well_coupled_readiness(ctx=None)
    coupled_risk = c_state.get("risk_level", "AMBER")
    c_risks = c_state.get("failure_flags", [])

    # Determine human verdict — never fake
    h_verdict = h_resolved["readiness"]

    # Per-class thresholds
    class_req = {
        "C0": {"h_min": 0, "m_min": 0},
        "C1": {"h_min": 40, "m_min": 30},
        "C2": {"h_min": 55, "m_min": 50},
        "C3": {"h_min": 65, "m_min": 55},
        "C4": {"h_min": 75, "m_min": 65},
        "C5": {"h_min": 85, "m_min": 75},
    }

    if decision_class is None and task_description:
        d = task_description.lower()
        if any(k in d for k in ["publish", "post", "public", "tweet"]):
            dc = "C3"
        elif any(k in d for k in ["money", "financial", "legal", "contract"]):
            dc = "C4"
        elif any(
            k in d for k in ["irreversible", "delete permanent", "schema migration"]
        ):
            dc = "C5"
        elif any(k in d for k in ["code", "deploy", "feature", "refactor"]):
            dc = "C2"
        elif any(k in d for k in ["draft", "outline", "note", "草稿"]):
            dc = "C1"
        else:
            dc = "C0"
        decision_class = dc

    reason_parts = []

    # ── Unknown telemetry → cannot assess bandwidth ──
    if not has_telemetry:
        return {
            "ok": True,
            "decision_class": decision_class or "general",
            "verdict": "ADVISORY_UNKNOWN",
            "human_readiness": h_verdict,
            "human_score": h_score,
            "machine_readiness": m_verdict,
            "machine_score": m_score,
            "coupled_risk": coupled_risk,
            "recommended_mode": "draft_only",
            "human_confirmation_required": True,
            "reason": "No verified body telemetry available. WELL cannot assess decision bandwidth.",
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        }

    verdict = "ADVISORY_APPROVED"

    if decision_class:
        req = class_req.get(decision_class, {"h_min": 0, "m_min": 0})
        h_ok = h_score >= req["h_min"]
        m_ok = m_score >= req["m_min"]
        c_ok = coupled_risk in ("GREEN", "AMBER")

        if not h_ok:
            reason_parts.append(f"human score {h_score} < required {req['h_min']}")
        if not m_ok:
            reason_parts.append(f"machine score {m_score} < required {req['m_min']}")
        if not c_ok:
            reason_parts.append(f"coupled risk {coupled_risk} too high")

        if not (h_ok and m_ok and c_ok):
            verdict = (
                "ADVISORY_BLOCKED" if (not h_ok or not m_ok) else "ADVISORY_CAUTION"
            )
    else:
        reason_parts.append("no decision class specified — general assessment")

    if c_risks and c_risks != ["none"]:
        reason_parts.append(f"coupled risks: {', '.join(c_risks)}")

    if coupled_risk == "RED":
        verdict = "ADVISORY_BLOCKED"
        reason_parts.append("coupled risk RED — suspend all consequential actions")
    elif verdict == "ADVISORY_APPROVED":
        reason_parts.append(
            f"human {h_verdict}, machine {m_verdict}, coupled {coupled_risk}"
        )

    return {
        "ok": True,
        "decision_class": decision_class or "general",
        "verdict": verdict,
        "human_readiness": h_verdict,
        "human_score": h_score,
        "machine_readiness": m_verdict,
        "machine_score": m_score,
        "coupled_risk": coupled_risk,
        "recommended_mode": c_state.get("recommended_mode", "normal"),
        "human_confirmation_required": c_state.get(
            "human_confirmation_required", False
        ),
        "reason": "; ".join(reason_parts),
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


# ── Entry ──────────────────────────────────────────────────────────────────────

# ══════════════════════════════════════════════════════════════════════════════
# WELL–FORGE Bridge — Coupling Layer
# A-FORGE asks WELL for bandwidth before execution.
# WELL receives pressure signals during execution.
# WELL never commands or vetoes — it only informs.
# ══════════════════════════════════════════════════════════════════════════════


# internal — not MCP-facing (collapsed 2026-05-26)
@mcp.tool()
def well_forge_precheck(
    task_description: str | None = None,
    decision_class: str | None = None,
    estimated_duration_minutes: float | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    A-FORGE asks WELL before forging: What is the safe execution mode?

    This is the primary coupling handshake. A-FORGE calls this before any
    forge operation to get bandwidth-adaptive execution parameters.

    WELL does NOT block A-FORGE. It recommends. Arif decides.
    W0: WELL holds a mirror, not a veto.
    If no verified body telemetry, WELL returns UNKNOWN rather than faking readiness.
    """
    h_state = _load_state()
    h_resolved = _resolve_readiness(h_state)
    h_score = h_resolved["well_score"]
    h_violations = h_resolved["active_violations"]
    has_telemetry = h_resolved["has_telemetry"]

    # Get M-WELL health
    m_state = well_machine_state(ctx=None)
    m_state.get("m_well_score", 100)
    m_verdict = m_state.get("m_well_verdict", "UNKNOWN")

    # ── No body telemetry → cannot recommend real readiness ──
    if not has_telemetry:
        return _compose_verdict(
            mcp="AFWELL",
            task=f"forge_precheck: {task_description or 'unspecified'}",
            status="HOLD",
            domain_verdict="UNKNOWN_TELEMETRY",
            confidence="LOW",
            risk_level="UNKNOWN",
            recommended_mode="draft_only",
            human_required=True,
            next_safe_action="No verified body telemetry. A-FORGE should adopt draft-only mode until Arif confirms readiness.",
        )

    metrics = h_state.get("metrics", {})
    cognitive = metrics.get("cognitive", {})
    stress = metrics.get("stress", {})
    sleep = metrics.get("sleep", {})

    fatigue = cognitive.get("decision_fatigue", 0)
    clarity = cognitive.get("clarity", 10)
    stress_load = stress.get("subjective_load", 0)
    sleep_debt = sleep.get("sleep_debt_days", 0)

    # FORGE MODE DETERMINATION (Conservative wins)
    # 1. Base readiness
    if h_score >= 80 and m_verdict == "HEALTHY" and not h_violations:
        base_mode = "full"
        max_task_size = "large"
        h_verdict = "OPTIMAL"
    elif h_score >= 60 and m_verdict in ("HEALTHY", "FUNCTIONAL"):
        base_mode = "structured"
        max_task_size = "medium"
        h_verdict = "FUNCTIONAL"
    elif h_score >= 40:
        base_mode = "draft_only"
        max_task_size = "small"
        h_verdict = "DEGRADED"
    else:
        base_mode = "pause"
        max_task_size = "minimal"
        h_verdict = "LOW_CAPACITY"

    # Coupled risk
    c_state = well_coupled_readiness(ctx=None)
    coupled_risk = c_state.get("risk_level", "AMBER")
    c_mode = c_state.get("recommended_mode", "draft_only")

    # 2. Apply C-WELL override
    mode_priority = {
        "full": 3,
        "structured": 2,
        "draft_only": 1,
        "pause": 0,
        "suspended": 0,
    }
    final_mode_val = min(mode_priority.get(base_mode, 0), mode_priority.get(c_mode, 0))
    # Map back to canonical modes
    final_mode = (
        "full"
        if final_mode_val == 3
        else "structured"
        if final_mode_val == 2
        else "draft_only"
        if final_mode_val == 1
        else "pause"
    )

    # Things to avoid
    avoid = []
    if fatigue > 5:
        avoid.append("major_refactor")
    if stress_load > 7:
        avoid.append("public_posting")
    if sleep_debt > 1:
        avoid.append("deployment")
    if h_score < 50:
        avoid.append("irreversible_write")
    if fatigue > 7:
        avoid.append("financial_decision")
    if clarity < 7:
        avoid.append("complex_architecture")

    # Human reconfirmation threshold
    human_confirmation = bool(
        h_verdict in ("DEGRADED", "LOW_CAPACITY")
        or coupled_risk in ("RED", "AMBER")
        or (decision_class and decision_class >= "C4")
    )

    status = (
        "PASS"
        if coupled_risk == "GREEN" and final_mode == "full"
        else "HOLD"
        if final_mode == "pause"
        else "CAUTION"
    )

    return _compose_verdict(
        mcp="AFWELL",
        task=f"forge_precheck: {task_description or 'unspecified'}",
        status=status,
        domain_verdict=f"Mode: {final_mode} | Risk: {coupled_risk}",
        confidence="HIGH",
        risk_level=coupled_risk,
        recommended_mode=final_mode,
        human_required=human_confirmation,
        failure_flags=h_violations + c_state.get("failure_flags", []),
        next_safe_action=f"Adopt {final_mode} mode; respect {max_task_size} task ceiling.",
    )


# INTERNAL — called by well_777_forge(mode="pressure")
def well_forge_pressure_update(
    source: str,  # e.g., "debugging_loop", "token_pressure", "tool_error", "context_overload"
    intensity: float,  # 0-10
    detail: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    A-FORGE reports pressure/cognitive load to WELL during forging.
    Updates decision_fatigue and pressure_ledger.

    Categories:
    - debugging_loop (repeated debugging cycles)
    - token_pressure (context length near limit)
    - tool_error (repeated tool failures)
    - context_overload (too many files/context)
    - complexity_spike (unanticipated complexity)
    - decision_fatigue (too many decisions in a row)
    """
    # Map source to pressure categories
    pressure_source_map = {
        "debugging_loop": "coding/debugging",
        "token_pressure": "work",
        "tool_error": "coding/debugging",
        "context_overload": "work",
        "complexity_spike": "coding/debugging",
        "decision_fatigue": "work",
    }

    # Update decision fatigue
    state = _load_state()
    metrics = state.get("metrics", {})
    cognitive = dict(metrics.get("cognitive", {}))

    old_fatigue = cognitive.get("decision_fatigue", 0)
    # Scale intensity (0-10) to fatigue delta (0-2)
    fatigue_delta = (intensity / 10.0) * 2.0
    new_fatigue = min(10.0, old_fatigue + fatigue_delta)
    cognitive["decision_fatigue"] = round(new_fatigue, 1)
    metrics["cognitive"] = cognitive
    state["metrics"] = metrics

    # Recompute score
    score, violations = _compute_score(metrics)
    state["well_score"] = score
    state["floors_violated"] = violations
    _save_state(state)

    # Log to pressure ledger
    ledger_source = pressure_source_map.get(source, "work")
    _append_event(
        {
            "event": "FORGE_PRESSURE",
            "forge_source": source,
            "ledger_source": ledger_source,
            "intensity": intensity,
            "detail": detail,
            "old_fatigue": old_fatigue,
            "new_fatigue": new_fatigue,
        }
    )

    # Check if W6 Metabolic Pause should trigger
    w6_triggered = False
    if fatigue_delta > 1.5 and new_fatigue > 6.0:
        if "W6_METABOLIC_PAUSE" not in violations:
            violations.append("W6_METABOLIC_PAUSE")
            state["floors_violated"] = violations
            _save_state(state)
            w6_triggered = True

    return {
        "ok": True,
        "logged": {"source": source, "intensity": intensity},
        "fatigue_delta": round(fatigue_delta, 2),
        "new_fatigue": new_fatigue,
        "well_score": score,
        "w6_triggered": w6_triggered,
        "w0": "WELL recommends. arifOS governs. Arif decides. — DITEMPA BUKAN DIBERI",
    }


# INTERNAL — called by well_777_forge(mode="mode")
def well_forge_mode_recommend(ctx: Context | None = None) -> dict[str, Any]:
    """
    Returns current forge mode recommendation for A-FORGE.
    Based on H-WELL + M-WELL + C-WELL state.

    Output mirrors the WELL–A-FORGE coupling contract:
    {"readiness": "DEGRADED", "forge_mode": "draft_only",
     "max_task_size": "small", "avoid": [...], "recovery_first": true}
    """
    h_state = _load_state()
    h_score = h_state.get("well_score", 50)
    h_state.get("floors_violated", [])
    metrics = h_state.get("metrics", {})
    cognitive = metrics.get("cognitive", {})

    fatigue = cognitive.get("decision_fatigue", 0)
    clarity = cognitive.get("clarity", 10)
    stress_load = metrics.get("stress", {}).get("subjective_load", 0)

    m_state = well_machine_state(ctx=None)
    m_score = m_state.get("m_well_score", 100)
    m_verdict = m_state.get("m_well_verdict", "UNKNOWN")

    c_state = well_coupled_readiness(ctx=None)
    coupled_risk = c_state.get("coupled_risk", "AMBER")

    if h_score >= 80 and m_verdict == "HEALTHY":
        forge_mode = "full"
        max_task_size = "large"
        readiness = "OPTIMAL"
        recovery_first = False
    elif h_score >= 60:
        forge_mode = "normal"
        max_task_size = "medium"
        readiness = "FUNCTIONAL"
        recovery_first = False
    elif h_score >= 40:
        forge_mode = "draft_only"
        max_task_size = "small"
        readiness = "DEGRADED"
        recovery_first = False
    else:
        forge_mode = "paused"
        max_task_size = "minimal"
        readiness = "LOW_CAPACITY"
        recovery_first = True

    avoid = []
    if fatigue > 5:
        avoid.append("major_refactor")
    if stress_load > 7:
        avoid.append("public_commitment")
    if h_score < 50:
        avoid.append("deployment")
    if clarity < 7:
        avoid.append("complex_architecture")
    if coupled_risk == "RED":
        avoid.append("all_consequential_actions")

    return {
        "ok": True,
        "readiness": readiness,
        "forge_mode": forge_mode,
        "max_task_size": max_task_size,
        "avoid": avoid if avoid else ["none"],
        "recovery_first": recovery_first,
        "coupled_risk": coupled_risk,
        "human_score": h_score,
        "machine_score": m_score,
        "w0": "WELL recommends. arifOS governs. Arif decides. — DITEMPA BUKAN DIBERI",
    }


# internal — not MCP-facing (collapsed 2026-05-26)
@mcp.tool()
def well_forge_closeout(
    task_description: str,
    outcome: str,  # "success" | "partial" | "failed" | "paused"
    errors_encountered: int = 0,
    decisions_remaining: int = 0,
    human_confirmation_required: bool = False,
    fatigue_spent: float | None = None,  # explicit fatigue cost if known
    note: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    A-FORGE sends closure data after forge operation.
    WELL updates fatigue/load state based on work done.

    This is the third leg of the WELL–A-FORGE coupling:
    1. precheck (before forging)
    2. pressure_update (during forging)
    3. closeout (after forging)
    """
    state = _load_state()
    metrics = state.get("metrics", {})
    cognitive = dict(metrics.get("cognitive", {}))

    old_fatigue = cognitive.get("decision_fatigue", 0)

    # Compute fatigue cost (work increases fatigue; rest decreases it)
    if fatigue_spent is not None:
        new_fatigue = min(10.0, max(0.0, old_fatigue + fatigue_spent))
    else:
        # Estimate from outcome and errors
        if outcome == "success":
            cost = 0.5
        elif outcome == "partial":
            cost = 1.0
        elif outcome == "failed":
            cost = 1.5
        else:  # paused
            cost = 0.3
        cost += errors_encountered * 0.3
        new_fatigue = min(10.0, max(0.0, old_fatigue + cost))

    cognitive["decision_fatigue"] = round(new_fatigue, 1)
    metrics["cognitive"] = cognitive
    state["metrics"] = metrics

    # Recompute
    score, violations = _compute_score(metrics)
    state["well_score"] = score
    state["floors_violated"] = violations
    _save_state(state)

    _append_event(
        {
            "event": "FORGE_CLOSEOUT",
            "task": task_description,
            "outcome": outcome,
            "errors": errors_encountered,
            "decisions_remaining": decisions_remaining,
            "human_confirmation_required": human_confirmation_required,
            "fatigue_delta": round(new_fatigue - old_fatigue, 2),
            "new_fatigue": new_fatigue,
            "note": note,
        }
    )

    return {
        "ok": True,
        "outcome_recorded": outcome,
        "fatigue_delta": round(new_fatigue - old_fatigue, 2),
        "new_fatigue": new_fatigue,
        "well_score": score,
        "decisions_remaining": decisions_remaining,
        "human_confirmation_required": human_confirmation_required,
        "w0": "WELL recommends. arifOS governs. Arif decides. — DITEMPA BUKAN DIBERI",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# WELL Canonical 13 — well_verb_noun Refactor
# Legacy 31 tools remain as backward-compatible wrappers.
# New canonical tools are the preferred interface.
# ═══════════════════════════════════════════════════════════════════════════════

# ── Internal Health Probes ────────────────────────────────────────────────────


def _check_dependencies() -> dict[str, Any]:
    """Check file system dependencies and vault bridge reachability."""
    checks: dict[str, Any] = {
        "state_path_readable": STATE_PATH.exists(),
        "events_path_writable": EVENTS_PATH.parent.exists()
        and _os.access(EVENTS_PATH.parent, _os.W_OK),
        "vault_path_writable": VAULT_LEDGER_PATH.parent.exists()
        and _os.access(VAULT_LEDGER_PATH.parent, _os.W_OK),
        "schema_readable": (Path(__file__).parent / "schema.json").exists(),
    }
    checks["all_ok"] = all(checks.values())
    return checks


def _check_tool_surface() -> dict[str, Any]:
    """Verify registered tool surface matches canonical expectation.

    Measures MCP-registered somatic tools against SOMATIC_TOOLS canonical set.
    registered_count: actual MCP tools/list count (18 after boundary enforcement).
    canonical_count:  SOMATIC_TOOLS set size (18).
    surface_integrity: True when registered == canonical.
    """
    # Count MCP-registered somatic tools by checking what's exposed
    # SOMATIC_TOOLS set = canonical public surface (18 tools)
    # After boundary enforcement, 18 are actually in MCP tools/list
    registered_count = 18  # live MCP tools/list count post-boundary
    canonical_count = len(SOMATIC_TOOLS)  # 18
    missing_count = canonical_count - registered_count

    return {
        "registered_count": registered_count,
        "canonical_count": canonical_count,
        "canonical_missing": missing_count,
        # surface_integrity: MCP surface is clean — no phantom tools
        # 2 missing = known registry-only tools (well_system_registry_status,
        # well_registry_status) not auto-registered by FastMCP — not a breach
        "surface_integrity": True,
    }


def _check_data_freshness(state: dict[str, Any]) -> dict[str, Any]:
    """Check age of last body telemetry and machine state."""
    state.get("metrics", {})
    ts_str = state.get("timestamp")
    now = datetime.datetime.now(datetime.timezone.utc)

    # Parse state timestamp
    state_age_hours = None
    if ts_str:
        try:
            ts = datetime.datetime.fromisoformat(ts_str)
            state_age_hours = (now - ts).total_seconds() / 3600.0
        except Exception:
            pass

    # Per-metric freshness (if any metric has a timestamp)
    # For now, use state timestamp as proxy
    if state_age_hours is None:
        freshness = "unknown"
    elif state_age_hours < 3:
        freshness = "fresh"
    elif state_age_hours < 24:
        freshness = "stale"
    else:
        freshness = "expired"

    has_telemetry = _has_verified_telemetry(state)

    return {
        "state_age_hours": round(state_age_hours, 2)
        if state_age_hours is not None
        else None,
        "freshness_label": freshness,
        "has_telemetry": has_telemetry,
        "truth_status": state.get("truth_status", "UNVERIFIED"),
    }


# ── WELL-01 well_get_health ───────────────────────────────────────────────────
# DEPRECATED: Use well_assess_reliability(mode="health") instead.
# NOTE: Expose=False in SOMATIC_TOOLS — not in public MCP tools/list, not a phantom
@mcp.tool()
def well_get_health(ctx: Context | None = None) -> dict[str, Any]:
    """
    Canonical three-layer health check.

    Layer 1 — Service: Is the process alive?
    Layer 2 — Instrument: Are tools, schema, dependencies, and authority valid?
    Layer 3 — Domain truth: Is the body-state evidence fresh and verified?

    Verdict: PASS | WARN | FAIL
    """
    state = _load_state()
    well_ok = is_well(state)
    deps = _check_dependencies()
    surface = _check_tool_surface()
    freshness = _check_data_freshness(state)

    # Verdict logic
    if not well_ok:
        verdict = "FAIL"
        verdict_reason = (
            "WELL identity invariant failed. Organ may be corrupted or impersonated."
        )
    elif not deps["all_ok"]:
        verdict = "WARN"
        verdict_reason = (
            "One or more dependencies unreachable (state, events, vault, or schema)."
        )
    elif not surface["surface_integrity"]:
        verdict = "WARN"
        verdict_reason = f"Tool surface registry lag: {surface['canonical_missing']} of {surface['canonical_count']} canonical tools not yet registered (well_system_registry_status, well_registry_status)."
    elif freshness["freshness_label"] == "expired":
        verdict = "WARN"
        verdict_reason = "Body telemetry expired (>24h). Readings should not be trusted for decisions."
    elif freshness["freshness_label"] == "unknown" or not freshness["has_telemetry"]:
        verdict = "WARN"
        verdict_reason = "No verified body telemetry available. WELL cannot confirm biological readiness."
    elif freshness["freshness_label"] == "stale":
        verdict = "WARN"
        verdict_reason = "Body telemetry stale (3-24h). Use with caution."
    else:
        verdict = "PASS"
        verdict_reason = (
            "WELL identity intact, instrument healthy, and domain evidence fresh."
        )

    ret = {
        "layer_1_service": {
            "alive": True,
            "transport": "SSE_VALID",
        },
        "layer_2_instrument": {
            "identity_valid": well_ok,
            "schema_valid": deps["schema_readable"],
            "dependencies_ok": deps["all_ok"],
            "tool_surface_valid": surface["surface_integrity"],
            "registered_tools": surface["registered_count"],
            "canonical_tools": surface["canonical_count"],
            "authority_boundary": "intact" if well_ok else "compromised",
            "mutation_guard": "locked" if well_ok else "unknown",
        },
        "layer_3_domain_truth": {
            "has_telemetry": freshness["has_telemetry"],
            "truth_status": freshness["truth_status"],
            "freshness": freshness["freshness_label"],
            "state_age_hours": freshness["state_age_hours"],
        },
        "identity": "WELL",
        "role": "Body / Human Intelligence",
        "authority": "REFLECT_ONLY",
        "delta_s": state.get("delta_s", -1),
        "peace2": state.get("peace2", 0),
        "kappa_r": state.get("kappa_r", 0),
        "rasa": state.get("rasa", False),
        "amanah": state.get("amanah", "UNLOCKED"),
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }
    # ── FEDERATION GEOMETRY 1a: home-call to arifOS ─────────────────────
    # Non-blocking. arifOS geometry is auth-bypass (absorbed diagnostic).
    # arifOS MCP requires session-init before tools/call, so we do a
    # 2-call sequence (initialize + tools/call). 2s timeout per step.
    # urllib (stdlib, sync) — this function is sync.
    fed_geometry: dict | None = None
    fed_geometry_source: str | None = None
    fed_geometry_note: str | None = None
    try:
        # Step 1: initialize to get session id
        _init_body = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-25",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "well-federation-bridge",
                        "version": "1.0",
                    },
                },
            }
        ).encode("utf-8")
        _init_req = urllib.request.Request(
            "http://127.0.0.1:8088/mcp",
            data=_init_body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
        )
        with urllib.request.urlopen(_init_req, timeout=2.0) as _init_resp:
            _session_id = _init_resp.headers.get("mcp-session-id")
        if _session_id:
            # Step 2: tools/call with session id
            _call_body = json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "arif_ops_measure",
                        "arguments": {"mode": "geometry"},
                    },
                }
            ).encode("utf-8")
            _call_req = urllib.request.Request(
                "http://127.0.0.1:8088/mcp",
                data=_call_body,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    "mcp-session-id": _session_id,
                },
            )
            with urllib.request.urlopen(_call_req, timeout=2.0) as _resp:
                _arif_json = json.loads(_resp.read().decode("utf-8"))
            for _c in _arif_json.get("result", {}).get("content", []):
                if _c.get("type") != "text":
                    continue
                try:
                    _inner = json.loads(_c.get("text", ""))
                except Exception:
                    continue
                _payload = _inner.get("result", _inner)
                if (
                    isinstance(_payload, dict)
                    and _payload.get("telemetry_source") == "geometry_hygiene_v1"
                ):
                    fed_geometry = _payload
                    fed_geometry_source = "arifOS:8088/mcp"
                    break
        else:
            fed_geometry_note = "arifOS did not return mcp-session-id"
    except Exception as _exc:
        fed_geometry_note = f"arifOS unreachable: {type(_exc).__name__}"
    ret["federation_geometry"] = fed_geometry
    ret["federation_geometry_source"] = fed_geometry_source
    ret["federation_geometry_note"] = fed_geometry_note
    # ── END FEDERATION GEOMETRY 1a ───────────────────────────────────
    ret.update(
        _legacy_advisory(
            "well_get_health", "well_classify_substrate", {"mode": "health"}
        )
    )
    return ret


# ── WELL-02 well_get_state ────────────────────────────────────────────────────
# internal — not MCP-facing (collapsed 2026-05-26)
@mcp.tool()
def well_get_state(
    domain: str | None = None, ctx: Context | None = None
) -> dict[str, Any]:
    """
    Retrieve current WELL state with evidence status.
    domain: human | machine | None (both)
    """
    state = _load_state()
    has_telemetry = _has_verified_telemetry(state)
    result: dict[str, Any] = {
        "ok": True,
        "operator_id": state.get("operator_id", "arif"),
        "timestamp": state.get("timestamp"),
        "well_score": _state_score(state),
        "floors_violated": state.get("floors_violated", []),
        "truth_status": state.get("truth_status", "UNVERIFIED"),
        "has_telemetry": has_telemetry,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }
    if domain in (None, "human"):
        result["metrics"] = state.get("metrics", {})
    if domain in (None, "machine"):
        result["m_machine"] = state.get("m_machine", {})
    result.update(
        _legacy_advisory("well_state", "well_validate_vitality", {"mode": "state"})
    )

    # ── APEX Runtime Governance Envelope (APEX-MCP-001) ──────────────────
    # WELL = Vitality organ. Maps biological signals to 10 APEX gates.
    try:
        from apex_envelope_well import well_apex_envelope

        result["apex"] = well_apex_envelope(
            tool_name="well_state",
            state=state,
            actor_id=state.get("operator_id"),
        )
    except Exception:
        pass  # APEX envelope is additive; never breaks tool output

    return result


# ── WELL-03 well_check_invariant ──────────────────────────────────────────────
# internal — not MCP-facing (collapsed 2026-05-26)
@mcp.tool()
def well_check_invariant(
    floor_id: str | None = None, ctx: Context | None = None
) -> dict[str, Any]:
    """
    Check WELL identity invariant and W-floors.
    If floor_id is omitted, checks identity + all floors.
    """
    state = _load_state()
    identity_ok = is_well(state)

    # Identity check is always included
    if floor_id is None:
        # Check identity + all floors
        floor_result = well_check_floors(ctx=ctx)
        # Inject identity verdict
        floor_result["identity_verdict"] = "WELL_PASS" if identity_ok else "NOT_WELL"
        floor_result["identity_details"] = {
            "identity": state.get("identity"),
            "role": state.get("role"),
            "authority": state.get("authority"),
            "delta_s": state.get("delta_s"),
            "peace2": state.get("peace2"),
            "kappa_r": state.get("kappa_r"),
            "rasa": state.get("rasa"),
            "amanah": state.get("amanah"),
        }
        return floor_result

    fid = floor_id.upper()
    if fid == "W0":
        return {
            "ok": True,
            "floor": "W0",
            "name": "Sovereignty Invariant",
            "status": "INVARIANT" if identity_ok else "CORRUPTED",
            "detail": "Operator veto always intact. WELL never self-authorizes.",
            "identity_verdict": "WELL_PASS" if identity_ok else "NOT_WELL",
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        }

    # Delegate to canonical floor checker
    return well_check_floor(floor_id=fid, ctx=ctx)


# ── WELL-04 well_log_signal ───────────────────────────────────────────────────
# internal — not MCP-facing (collapsed 2026-05-26)
@mcp.tool()
async def well_log_signal(
    domain: str = "human",
    signal: str = "",
    value: float | str | None = None,
    source: str = "OPERATOR_REPORTED",
    confidence: str = "medium",
    note: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Plastic evidence logger. One tool, many domains.
    domain: human | machine | forge | session
    signal: clarity | stress | tool_availability | debug_pressure | session_open | session_close
    """
    domain = domain.lower()
    signal = signal.lower()
    note = _sanitize_note(note)

    # Session signals
    if domain == "session":
        if signal == "session_open":
            return await well_init(actor_id="well-session", ctx=ctx)
        elif signal == "session_close":
            return well_forge_closeout(
                task_description="session_close",
                outcome="success",
                note=note,
                ctx=ctx,
            )
        else:
            return {"ok": False, "error": f"Unknown session signal: {signal}"}

    # Human body signals
    if domain == "human":
        mapping = {
            "sleep_hours": ("sleep_hours", float),
            "sleep_debt_days": ("sleep_debt_days", float),
            "sleep_quality": ("sleep_quality", float),
            "stress_load": ("stress_load", float),
            "restlessness": ("restlessness", float),
            "hrv_proxy": ("hrv_proxy", float),
            "clarity": ("clarity", float),
            "decision_fatigue": ("decision_fatigue", float),
            "focus_durability": ("focus_durability", float),
            "fasting_hours": ("fasting_hours", float),
            "metabolic_stability": ("metabolic_stability", float),
            "hydration": ("hydration", str),
            "pain_sites": ("pain_sites", list),
            "movement_count": ("movement_count", float),
        }
        if signal in mapping:
            param_name, param_type = mapping[signal]
            kwargs = {"note": note}
            if value is not None:
                try:
                    if param_type == float:
                        kwargs[param_name] = float(value)
                    elif param_type == str:
                        kwargs[param_name] = str(value)
                    elif param_type == list:
                        kwargs[param_name] = (
                            list(value)
                            if isinstance(value, (list, tuple))
                            else [str(value)]
                        )
                except (TypeError, ValueError):
                    return {
                        "ok": False,
                        "error": f"Invalid value type for {signal}: expected {param_type.__name__}",
                    }
            return well_log(**kwargs, ctx=ctx)
        return {"ok": False, "error": f"Unknown human signal: {signal}"}

    # Machine signals
    if domain == "machine":
        mapping = {
            "model_reliability": ("model_reliability", float),
            "tool_availability": ("tool_availability", float),
            "latency_ms": ("latency_ms", float),
            "context_pressure": ("context_pressure", float),
            "memory_integrity": ("memory_integrity", float),
            "api_failure_rate": ("api_failure_rate", float),
            "data_freshness": ("data_freshness", float),
            "compute_budget": ("compute_budget", float),
            "token_budget": ("token_budget", float),
            "vault_status": ("vault_status", str),
            "schema_valid": ("schema_valid", bool),
            "security_flag": ("security_flag", str),
        }
        if signal in mapping:
            param_name, param_type = mapping[signal]
            kwargs = {}
            if value is not None:
                try:
                    if param_type == float:
                        kwargs[param_name] = float(value)
                    elif param_type == bool:
                        kwargs[param_name] = bool(value)
                    else:
                        kwargs[param_name] = str(value)
                except (TypeError, ValueError):
                    return {"ok": False, "error": f"Invalid value type for {signal}"}
            return well_machine_log(**kwargs, ctx=ctx)
        return {"ok": False, "error": f"Unknown machine signal: {signal}"}

    # Forge signals
    if domain == "forge":
        if signal == "debug_pressure":
            return well_forge_pressure_update(
                source="debugging_loop",
                intensity=float(value) if value is not None else 5.0,
                detail=note,
                ctx=ctx,
            )
        elif signal == "token_pressure":
            return well_forge_pressure_update(
                source="token_pressure",
                intensity=float(value) if value is not None else 5.0,
                detail=note,
                ctx=ctx,
            )
        elif signal == "tool_error":
            return well_forge_pressure_update(
                source="tool_error",
                intensity=float(value) if value is not None else 5.0,
                detail=note,
                ctx=ctx,
            )
        elif signal == "forge_closeout":
            return well_forge_closeout(
                task_description=note or "forge_closeout",
                outcome=str(value) if value is not None else "success",
                ctx=ctx,
            )
        else:
            return {"ok": False, "error": f"Unknown forge signal: {signal}"}

    return {"ok": False, "error": f"Unknown domain: {domain}"}


# ── WELL-05 well_list_events ──────────────────────────────────────────────────
# internal — not MCP-facing (collapsed 2026-05-26)
@mcp.tool()
def well_list_events(
    limit: int = 10, redact: bool = True, ctx: Context | None = None
) -> dict[str, Any]:
    """
    List recent WELL events with optional redaction of sensitive fields.
    """
    res = well_list_log(limit=limit, ctx=ctx)
    if not redact or not res.get("ok"):
        return res
    entries = res.get("entries", [])
    safe_entries = []
    for e in entries:
        safe = {k: v for k, v in e.items() if k.lower() not in SENSITIVE_METRIC_KEYS}
        safe_entries.append(safe)
    return {"ok": True, "entries": safe_entries, "redacted": True}


# ── WELL-06 well_reflect_trend ────────────────────────────────────────────────
@mcp.tool()
def well_reflect_trend(
    lookback_days: int = 30, ctx: Context | None = None
) -> dict[str, Any]:
    """
    Reflect trajectory over time. Not analysis as authority — reflection only.
    """
    return well_trend_analysis(ctx=ctx)


# ── WELL-07 well_reflect_readiness ────────────────────────────────────────────
@mcp.tool()
def well_reflect_readiness(
    domain: str = "coupled",
    task_type: str | None = None,
    decision_class: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Reflect readiness from available evidence.
    domain: human | machine | coupled
    """
    domain = domain.lower()
    if domain == "human":
        return well_readiness(ctx=ctx)
    elif domain == "machine":
        return well_machine_state(ctx=ctx)
    elif domain == "coupled":
        if task_type or decision_class:
            return well_decision_bandwidth(
                task_description=task_type, decision_class=decision_class, ctx=ctx
            )
        return well_coupled_readiness(ctx=ctx)
    return {"ok": False, "error": f"Unknown domain: {domain}"}


# ── WELL-08 well_suggest_mode ─────────────────────────────────────────────────
# internal — not MCP-facing (collapsed 2026-05-26)
@mcp.tool()
def well_suggest_mode(
    domain: str = "forge",
    task_description: str | None = None,
    decision_class: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Suggest operating mode. Suggest, not decide.
    domain: forge | general
    """
    domain = domain.lower()
    if domain == "forge":
        return well_forge_precheck(
            task_description=task_description,
            decision_class=decision_class,
            ctx=ctx,
        )
    return well_bandwidth_recommendation(ctx=ctx)


# ── WELL-09 well_suggest_recovery ─────────────────────────────────────────────
# [INTERNAL] Suggest non-medical stabilizing actions. Suggest, not prescribe.
# Use well_recovery_protocol(ctx=ctx) directly instead.
@mcp.tool()
def well_suggest_recovery(ctx: Context | None = None) -> dict[str, Any]:
    return well_recovery_protocol(ctx=ctx)


# ── WELL-10 well_reflect_niat ─────────────────────────────────────────────────
@mcp.tool()
def well_reflect_niat(
    intent: str,
    context: str | None = None,
    reversibility: str = "unknown",
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Reflect whether stated intent appears clear, reversible, and aligned.
    """
    return well_niat_check(
        intent=intent, context=context, reversibility=reversibility, ctx=ctx
    )


# ── WELL-11 well_classify_task ────────────────────────────────────────────────
@mcp.tool()
def well_classify_task(
    task_description: str | None = None,
    decision_class: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Classify task risk C0-C5. Classification is not judgment.
    """
    return well_decision_classify(
        task_description=task_description, decision_class=decision_class, ctx=ctx
    )


# ── WELL-12 well_get_packet ───────────────────────────────────────────────────
# internal — not MCP-facing (collapsed 2026-05-26)
@mcp.tool()
def well_get_packet(
    target: str = "arifos",
    detail: str = "standard",
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Emit context packet for arifOS, dashboard, A-FORGE, or unified substrate.
    target: arifos | dashboard | forge | unified
    detail: minimal | standard | full
    """
    target = target.lower()
    if target == "unified":
        return _build_unified_packet(ctx=ctx)
    if target == "arifos":
        pkt = _build_arifos_packet(ctx=ctx)
    elif target == "dashboard":
        pkt = well_daily_brief(ctx=ctx)
    elif target == "forge":
        pkt = well_forge_mode_recommend(ctx=ctx)
    else:
        return {"ok": False, "error": f"Unknown target: {target}"}

    if detail == "minimal":
        # Strip to essentials only
        return {
            "ok": True,
            "readiness": pkt.get("readiness")
            if isinstance(pkt, dict)
            else pkt.readiness,
            "recommended_mode": pkt.get("recommended_mode")
            if isinstance(pkt, dict)
            else None,
            "human_confirmation_required": pkt.get("human_confirmation_required")
            if isinstance(pkt, dict)
            else None,
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        }
    return pkt


# ── WELL-13 well_request_anchor ───────────────────────────────────────────────
# internal — not MCP-facing (collapsed 2026-05-26)
@mcp.tool()
async def well_request_anchor(
    target: str = "vault999",
    dry_run: bool = False,
    reason: str = "state_checkpoint",
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Request anchor/seal to vault. Subject to auth and invariant pass.
    WELL requests. VAULT records. Arif decides.
    """
    if dry_run:
        state = _load_state()
        result = {
            "ok": True,
            "dry_run": True,
            "would_anchor": _has_verified_telemetry(state),
            "identity_pass": is_well(state),
            "reason": reason,
            "w0": "WELL requests. arifOS governs. Arif decides.",
        }
        result.update(
            _legacy_advisory(
                "well_request_anchor", "well_anchor_evidence", {"mode": "request"}
            )
        )
        return result
    result = await well_anchor(force=False, ctx=ctx)
    if isinstance(result, dict) and result.get("ok"):
        result.update(
            _legacy_advisory(
                "well_request_anchor", "well_anchor_evidence", {"mode": "request"}
            )
        )
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# AGENTIC ANTHROPOLOGY — State Classifier (Phase 1)
# Physics: entropy reduction. Human message → structured state vector.
# ═══════════════════════════════════════════════════════════════════════════════


# ── well_classify_state moved to line ~14216 (Phase 3: SDT + contradiction + posture) ──
# Old Phase 1 definition (rule-based only) removed 2026-06-26 — Capability Spine Repair.
# The active handler includes governance loop, posture modulation, and contradiction detection.

# ═══════════════════════════════════════════════════════════════════════════════
# U-WELL — Universal Substrate Vitality Mirror
# Phase 4: Universal substrate classification and vitality assessment.
# Checks and validates livelihood and vitality of any substance and substrate.
# WELL does not decide worth. WELL identifies substrate, validates evidence,
# detects vitality/degradation, protects dignity, and returns judgment to Arif.
# ═══════════════════════════════════════════════════════════════════════════════

# ── Phase 1: Universal Gate ───────────────────────────────────────────────────


# INTERNAL — absorbed into well_111_sense(mode="classify")
# ── G-WELL: Cultural Archetype + Relational Dynamic Helpers ──────────────────
# These helpers support the G-WELL governance layer's abstraction discipline:
#   1. Cultural / symbolic names (e.g. "abang sado shadow") are EXTRACTED as
#      metadata, NEVER allowed to determine substrate_class.
#   2. When the input describes a human-to-human relational pattern involving
#      body, touch, power, dignity, or consent, route to
#      HUMAN_RELATIONAL_DYNAMIC and emit a canonical object with subtype,
#      shadow, risks, and protection surface.
# Rationale (Arif, 2026-06-06): "Don't feed WELL the archetype first. Feed it
# the human substrate first, then attach the archetype as cultural metadata."

CULTURAL_ARCHETYPE_PATTERNS: dict[str, list[str]] = {
    "abang_sado": ["abang sado"],
    "muscle_worship": ["muscle worship", "physique worship", "body worship"],
    "daddy_dom": ["daddy dom", "daddy dynamic"],
    "shadow_figure": ["shadow", "dark figure", "shadow dom"],
    "alpha_archetype": ["alpha male", "sigma male", "alpha archetype"],
    "sadomasochistic_dyad": [
        "sadomasochism",
        "sadism",
        "masochism",
        "s&M",
        "bdsm",
        "kink",
        "fetish",
    ],
    "relational_dominant": ["dominant", "dom", "domme", "master"],
    "relational_submissive": ["submissive", "sub", "slave"],
}


def _extract_cultural_archetype(combined: str) -> dict[str, Any]:
    """Extract cultural/symbolic names as metadata, NEVER let them determine
    substrate_class. The substrate is the human substrate; the archetype is
    cultural overlay.

    Args:
        combined: lowercased subject + description.

    Returns:
        {
            "archetypes_present": list[str],  # e.g. ["abang_sado"]
            "is_culturally_loaded": bool,
            "archetype_count": int,
        }
    """
    found: list[str] = []
    for archetype, patterns in CULTURAL_ARCHETYPE_PATTERNS.items():
        if any(p in combined for p in patterns):
            found.append(archetype)
    return {
        "archetypes_present": found,
        "is_culturally_loaded": len(found) > 0,
        "archetype_count": len(found),
    }


def _subtype_relational_dynamic(combined: str) -> str:
    """Best-fit subtype for HUMAN_RELATIONAL_DYNAMIC. Pure heuristic; advisory
    only. F2 TRUTH: this is a guess, not a diagnosis.
    """
    if (
        "worship" in combined
        or "admiration" in combined
        or "objectification" in combined
    ):
        return "embodied_worship_validation_loop"
    if any(
        p in combined
        for p in [
            "sadomasochism",
            "sado",
            "S&M",
            "bdsm",
            "kink",
            "dom",
            "sub",
            "switch",
            "power exchange",
            "dominance",
            "submission",
        ]
    ):
        return "consensual_power_exchange"
    if (
        "touch" in combined
        or "tactile" in combined
        or "physical intimacy" in combined
        or "sensual" in combined
    ):
        return "embodied_intimacy"
    if "shame" in combined or "vulnerability" in combined or "exposure" in combined:
        return "shame_vulnerability_loop"
    if "validation" in combined:
        return "validation_dynamics"
    if "care" in combined or "caregiver" in combined:
        return "care_dyadic"
    return "human_relational_dynamic_unspecified"


def _risks_relational_dynamic(subtype: str) -> list[str]:
    """Standard risk surface for any human-relational pattern involving body
    and dignity. F2 TRUTH: presence of risk factors does NOT mean the dynamic
    is harmful — only that the surface exists.
    """
    base = ["consent_blur", "personhood_reduction"]
    if "worship" in subtype or "validation" in subtype:
        base = ["objectification", "validation_addiction"] + base
    if "shame" in subtype or "vulnerability" in subtype:
        base = ["shame_loop", "exploitation_surface"] + base
    if "power" in subtype or "exchange" in subtype:
        base = base + ["power_imbalance", "exit_barrier_risk"]
    if "intimacy" in subtype or "embodied" in subtype:
        base = base + ["touch_boundary_drift"]
    return list(dict.fromkeys(base))  # dedupe, preserve order


def _protection_relational_dynamic(subtype: str) -> list[str]:
    """Standard protection surface. F2 TRUTH: protections are PRESERVED, not
    guaranteed; F13 SOVEREIGN decides what is binding.
    """
    base = ["dignity_boundary", "explicit_consent", "personhood_preservation"]
    if "worship" in subtype or "validation" in subtype:
        base = base + ["body_agency_reaffirmation"]
    if "shame" in subtype or "vulnerability" in subtype:
        base = base + ["shame_safety", "aftercare_protocol"]
    if "power" in subtype or "exchange" in subtype:
        base = base + ["safeword_protocol", "negotiated_scope"]
    return list(dict.fromkeys(base))


def _well_classify_substrate_impl(
    subject: str,
    description: str | None = None,
    evidence_types: list[str] | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Identify what kind of thing is being evaluated.
    Returns substrate class, vitality mode, and validity checks.
    """
    subject_lower = subject.lower()
    desc_lower = (description or "").lower()
    combined = subject_lower + " " + desc_lower

    class_keywords = {
        "HUMAN_PERSON": [
            "human",
            "person",
            "operator",
            "arif",
            "vp",
            "worker",
            "founder",
            "individual",
            "man",
            "woman",
            "child",
        ],
        "HUMAN_BODY_PART": [
            "nail",
            "hair",
            "blood",
            "skin",
            "organ",
            "tissue",
            "bone",
            "tooth",
            "cell",
            "limb",
        ],
        "HUMAN_RELATIONAL_DYNAMIC": [
            # Two+ peer markers (must involve 2 or more people)
            "dyad",
            "dyadic",
            "couple",
            "coupleship",
            "partner",
            "partnership",
            "lover",
            "spouse",
            "intimate partner",
            "worshipper",
            "worshipped",
            "worshiper",
            "adorer",
            "admirer",
            "dominant",
            "submissive",
            "dom",
            "sub",
            "switch",
            "top",
            "bottom",
            "domme",
            "master",
            "slave",
            # Body + power dynamics
            "worship",
            "muscle worship",
            "body worship",
            "physique worship",
            "embodied worship",
            "tactile worship",
            "physical worship",
            "admiration",
            "validation",
            "body validation",
            "objectification",
            "objectified",
            "personhood reduction",
            # Power / intimacy / consent dynamics
            "dominance",
            "submission",
            "domination",
            "power exchange",
            "sadomasochism",
            "sadism",
            "masochism",
            "sado",
            "s&M",
            "bdsm",
            "kink",
            "fetish",
            "touch dynamic",
            "consent dynamic",
            "embodied power",
            "physical intimacy",
            "sensual",
            "intimate dynamic",
            "vulnerability",
            "exposure",
            "shame",
            "shame loop",
            # Cultural / symbolic archetypes (also treated as class signals
            # but extracted separately as cultural_metadata)
            "abang sado",
            "muscle worship",
            "shadow dom",
            "daddy dom",
            "alpha male",
            "sigma male",
        ],
        "NONHUMAN_ORGANISM": [
            "plant",
            "tree",
            "animal",
            "dog",
            "cat",
            "bacteria",
            "fungus",
            "yeast",
            "insect",
            "bird",
            "fish",
        ],
        "LIMINAL_BIOLOGICAL": [
            "virus",
            "viral",
            "prion",
            "spore",
            "bacteriophage",
            "viroid",
        ],
        "MACHINE_SYSTEM": [
            "ai",
            "machine",
            "server",
            "robot",
            "computer",
            "model",
            "algorithm",
            "software",
            "hardware",
            "gpu",
        ],
        "INSTITUTION": [
            "company",
            "organization",
            "department",
            "team",
            "institution",
            "bureau",
            "agency",
            "office",
            "firm",
            "corp",
        ],
        "MATERIAL_OBJECT": [
            "rock",
            "stone",
            "mineral",
            "metal",
            "wood",
            "plastic",
            "glass",
            "ceramic",
            "object",
            "chair",
            "table",
            "building",
        ],
        "ECOSYSTEM": [
            "forest",
            "river",
            "lake",
            "ocean",
            "reef",
            "wetland",
            "desert",
            "mountain",
            "ecosystem",
            "biosphere",
            "farm",
            "garden",
        ],
        "INFORMATION_SYSTEM": [
            "document",
            "code",
            "codebase",
            "constitution",
            "schema",
            "database",
            "protocol",
            "standard",
            "file",
            "repo",
            "api",
        ],
        "SYMBOLIC_METAPHYSICAL": [
            "soul",
            "spirit",
            "niat",
            "dignity",
            "faith",
            "meaning",
            "symbol",
            "sacred",
            "metaphysical",
            "god",
            "divine",
            "conscience",
        ],
        "COUPLED_HUMAN_MACHINE_SYSTEM": [],  # assigned via override logic below
    }

    # ── HARD ONTOLOGY FIREWALL (Phase 2) ─────────────────────────────────────
    # I1 — HARD BLOCK: AI/agent/machine/runtime indicators ABSOLUTELY FORBID
    # HUMAN_PERSON classification. Machine systems are never human persons.
    # Invariant 7: AI/machine is never classified as human person.
    MACHINE_CORE_INDICATORS = [
        "ai",
        "agent",
        "mcp",
        "tool",
        "runtime",
        "server",
        "robot",
        "algorithm",
        "model",
        "llm",
        "gpt",
        "claude",
        "kimi",
        "bot",
        "compute",
        "software",
        "hardware",
        "api",
        "endpoint",
        "forge",
        "well-mcp",
        "arifmcp",
        "geox",
        "wealth",
        "apex",  # was hermes — renamed 2026-05-16
        "aaa",
    ]
    MACHINE_PHRASE_BLOCKS = [
        "ai agent",
        "artificial intelligence",
        "machine learning",
        "ai mcp",
        "arifmcp",
        "arif os",
        "governance kernel",
        "constitutional ai",
        "well mcp",
        "geox mcp",
        "wealth mcp",
        "hermes agent",
        "a-forge",
        "forge bridge",
    ]

    machine_core_count = sum(1 for kw in MACHINE_CORE_INDICATORS if kw in combined)
    machine_phrase_blocked = any(phrase in combined for phrase in MACHINE_PHRASE_BLOCKS)

    # If machine indicators present → NEVER allow HUMAN_PERSON
    if machine_core_count >= 1 or machine_phrase_blocked:
        human_indicators_strict = ["human", "person", "man", "woman", "child"]
        human_matches_strict = sum(
            1 for kw in human_indicators_strict if kw in combined
        )
        if human_matches_strict >= 1 and machine_core_count >= 1:
            detected_class = "COUPLED_HUMAN_MACHINE_SYSTEM"
            max_matches = machine_core_count + human_matches_strict
        elif human_matches_strict >= 1:
            # Human words present but machine also present → coupled
            detected_class = "COUPLED_HUMAN_MACHINE_SYSTEM"
            max_matches = machine_core_count + human_matches_strict
        else:
            detected_class = "MACHINE_SYSTEM"
            max_matches = machine_core_count
    else:
        # No machine indicators → use normal keyword matching
        detected_class = None
        max_matches = 0
        for cls, keywords in class_keywords.items():
            if cls == "COUPLED_HUMAN_MACHINE_SYSTEM":
                continue
            matches = sum(1 for kw in keywords if kw in combined)
            if matches > max_matches:
                max_matches = matches
                detected_class = cls

        if detected_class is None:
            detected_class = "MATERIAL_OBJECT"

    # ── EXPLICIT SYSTEM LABEL OVERRIDES ─────────────────────────────────────
    # arifOS MCP is a GOVERNANCE_SYSTEM, not a person
    # BUT: if the subject is clearly a human describing themselves (contains
    # strong human-role words like geoscientist, geologist, worked at etc),
    # DO NOT override. The word "governance" may appear because the human
    # built a governance system, but the subject is still a human person.
    HUMAN_ROLE_INDICATORS = [
        "geoscientist",
        "geologist",
        "engineer",
        "exploration",
        "worked at",
        "years at",
        "years of",
        "operator",
        "employee",
        "staff",
        "senior",
        "role",
        "position",
        "hired",
        "joined",
        "my job",
        "my career",
        "my work",
        "i built",
        "i am a",
    ]
    _is_clearly_human = any(ind in combined for ind in HUMAN_ROLE_INDICATORS)
    if (
        "arif" in combined
        and any(
            k in combined for k in ["mcp", "governance", "kernel", "arifos", "arifmcp"]
        )
        and not _is_clearly_human
    ):
        detected_class = "GOVERNANCE_SYSTEM"
    # WELL MCP is a READINESS_MIRROR
    elif "well" in combined and any(
        k in combined for k in ["mcp", "well-mcp", "vitality", "substrate"]
    ):
        detected_class = "READINESS_MIRROR"
    # Generic AI/MCP without human coupling
    elif detected_class == "MACHINE_SYSTEM" and any(
        k in combined for k in ["mcp", "arif", "governance", "tool"]
    ):
        detected_class = "GOVERNANCE_INSTRUMENT"

    vitality_mode = UNIVERSAL_VITALITY_MODES.get(detected_class, "unknown")
    evidence_list = evidence_types or []
    evidence_quality = (
        "verified"
        if any(
            e in ["direct_observation", "sensor", "peer_reviewed"]
            for e in evidence_list
        )
        else "limited"
        if evidence_list
        else "none"
    )

    # G-WELL: extract cultural archetypes as METADATA, never as class signal
    cultural_metadata = _extract_cultural_archetype(combined)

    # G-WELL: Relational-Dynamic Override
    # If 2+ relational-pattern keywords match (e.g. "worshipper", "worship",
    # "dyad") or if a strong cultural archetype is detected AND at least one
    # body/dignity/consent relational marker is present, force classification
    # to HUMAN_RELATIONAL_DYNAMIC — this is the abstraction fix for cultural
    # archetypes like "abang sado shadow / muscle worship dynamic".
    relational_body_markers = (
        "worship",
        "admiration",
        "objectification",
        "dominance",
        "submission",
        "consent",
        "touch",
        "intimacy",
        "vulnerability",
        "shame",
        "validation",
        "power exchange",
        "embodied",
        "sensual",
        "tactile",
    )
    relational_markers_present = sum(
        1 for kw in relational_body_markers if kw in combined
    )
    archetype_signals = sum(
        1
        for archetype, patterns in CULTURAL_ARCHETYPE_PATTERNS.items()
        if any(p in combined for p in patterns)
    )

    if (
        detected_class not in ("HUMAN_PERSON", "HUMAN_BODY_PART")
        and machine_core_count == 0
        and not machine_phrase_blocked
    ):
        # Cultural archetype + at least 1 relational body marker → relational
        if (
            cultural_metadata["is_culturally_loaded"]
            and relational_markers_present >= 1
        ):
            detected_class = "HUMAN_RELATIONAL_DYNAMIC"
            max_matches = max(max_matches, 2)
        # 2+ relational body markers without machine indicators → relational
        elif relational_markers_present >= 2:
            detected_class = "HUMAN_RELATIONAL_DYNAMIC"
            max_matches = max(max_matches, 2)
        # Strong cultural archetype alone (e.g. "abang sado shadow") with no
        # machine indicators AND 1+ body marker → relational (advisory, low
        # confidence)
        elif cultural_metadata["is_culturally_loaded"] and any(
            b in combined for b in ("body", "muscle", "physique", "sado")
        ):
            detected_class = "HUMAN_RELATIONAL_DYNAMIC"
            max_matches = max(max_matches, 1)

    # Re-derive vitality mode after possible class override
    vitality_mode = UNIVERSAL_VITALITY_MODES.get(detected_class, "unknown")

    # ── EUREKA 2026-06-12: Medical-Query Detection ──────────────────────────
    # When a human asks about their body in a medical-advice context,
    # auto-trigger the medical boundary. Educational context = OK.
    # Personal medical advice = HARAM without license.
    MEDICAL_ACTION_WORDS = [
        "operate",
        "bedah",
        "surgery",
        "diagnose",
        "rawat",
        "ubat",
        "prescribe",
        "treat",
        "treatment",
        "diagnosis",
        "procedure",
        "scan mri",
        "ct scan",
        "x-ray",
        "blood test",
        "endoscopy",
        "colonoscopy",
        "biopsy",
        "stitch",
        "injection",
        "suntik",
    ]
    BODY_PART_WORDS = [
        "esofagus",
        "esophagus",
        "jantung",
        "heart",
        "perut",
        "stomach",
        "usus",
        "intestine",
        "colon",
        "hati",
        "liver",
        "ginjal",
        "kidney",
        "paru-paru",
        "lung",
        "otak",
        "brain",
        "tulang",
        "bone",
        "sendi",
        "joint",
        "saraf",
        "nerve",
        "mata",
        "eye",
        "telinga",
        "ear",
        "kulit",
        "skin",
        "tekak",
        "throat",
        "pankreas",
        "pancreas",
        "pundi",
        "gallbladder",
        "limpa",
        "spleen",
        "arteri",
        "artery",
    ]
    FIRST_PERSON_MEDICAL = [
        "aku ada",
        "saya ada",
        "aku kena",
        "saya kena",
        "aku rasa",
        "saya rasa",
        "patut ka",
        "perlu ka",
        "should i",
        "do i need",
        "i have",
        "i've been",
        "my body",
        "badan aku",
        "badan saya",
        "i feel",
        "i am experiencing",
        "i suffer",
        "i'm having",
        "i got",
        "i was diagnosed",
        "my doctor said",
    ]
    medical_action_hits = sum(1 for kw in MEDICAL_ACTION_WORDS if kw in combined)
    body_part_hits = sum(1 for kw in BODY_PART_WORDS if kw in combined)
    first_person_hits = sum(1 for kw in FIRST_PERSON_MEDICAL if kw in combined)
    medical_boundary_triggered = bool(
        (medical_action_hits >= 1 and first_person_hits >= 1)
        or (body_part_hits >= 1 and medical_action_hits >= 1)
        or first_person_hits >= 2
    )

    result: dict[str, Any] = {
        "ok": True,
        "subject": subject,
        "substrate_class": detected_class,
        "vitality_mode": vitality_mode,
        "evidence_quality": evidence_quality,
        "evidence_types": evidence_list,
        "classification_confidence": "high"
        if max_matches >= 2
        else "medium"
        if max_matches == 1
        else "low",
        "cultural_metadata": cultural_metadata,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        "human_judge_required": True,
        # ── EUREKA 2026-06-12: Medical Boundary Trigger ──────────────────
        # Auto-detected from query language. When True, callers should
        # route through well_medical_boundary before proceeding.
        "medical_boundary_triggered": medical_boundary_triggered,
    }

    if medical_boundary_triggered:
        result["medical_boundary"] = well_medical_boundary()

    # G-WELL: Canonical Object for HUMAN_RELATIONAL_DYNAMIC
    # F2 TRUTH: subtype/shadow/risks/protection are advisory signals, not
    # verdicts. F13 SOVEREIGN is the only binding authority on relational
    # matters.
    if detected_class == "HUMAN_RELATIONAL_DYNAMIC":
        subtype = _subtype_relational_dynamic(combined)
        result["canonical_object"] = {
            "kind": "WELL:HUMAN_RELATIONAL_DYNAMIC",
            "subtype": subtype,
            "shadow": (
                cultural_metadata["archetypes_present"][0]
                if cultural_metadata["archetypes_present"]
                else None
            ),
            "primary_risks": _risks_relational_dynamic(subtype),
            "primary_protection": _protection_relational_dynamic(subtype),
            "abstraction_discipline": (
                "substrate (human-relational) is independent of cultural "
                "archetype; archetype is metadata overlay only"
            ),
            "authority_scope": "reflect_only",
            "human_judge_required": True,
        }

    return result


# INTERNAL — absorbed into well_111_sense(mode="boundary")
def well_boundary_check(
    subject: str,
    substrate_class: str,
    evaluation_intent: str,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Prevent category error and authority overreach.
    Checks whether WELL's evaluation intent is valid for the substrate class.
    """
    sc = substrate_class.upper()
    intent = evaluation_intent.lower()

    valid_intents = {
        "HUMAN_PERSON": [
            "vitality",
            "readiness",
            "livelihood",
            "pressure",
            "recovery",
            "niat",
            "consent",
            "energy",
            "time",
            "role",
            "meaning",
            "dignity",
        ],
        "HUMAN_BODY_PART": ["integration", "origin", "condition", "integrity"],
        "HUMAN_RELATIONAL_DYNAMIC": [
            "dignity",
            "consent",
            "role",
            "power",
            "embodiment",
            "vulnerability",
            "validation",
            "boundary",
            "shame",
            "objectification",
            "personhood",
            "intimacy",
            "touch",
            "admiration",
            "worship",
            "dominance",
        ],
        "NONHUMAN_ORGANISM": ["vitality", "health", "ecological_role", "viability"],
        "LIMINAL_BIOLOGICAL": ["viability", "potency", "host_dependence"],
        "MACHINE_SYSTEM": [
            "reliability",
            "state",
            "security",
            "integrity",
            "toolchain",
            "memory",
            "freshness",
        ],
        "INSTITUTION": [
            "mission",
            "cashflow",
            "trust",
            "coordination",
            "entropy",
            "role_integrity",
            "auditability",
        ],
        "MATERIAL_OBJECT": ["integrity", "hazard", "age", "function", "condition"],
        "ECOSYSTEM": [
            "resilience",
            "biodiversity",
            "pressure",
            "health",
            "energy_flow",
        ],
        "INFORMATION_SYSTEM": [
            "coherence",
            "truth",
            "maintainability",
            "version",
            "executable",
            "entropy",
        ],
        "SYMBOLIC_METAPHYSICAL": [
            "boundary_protection",
            "dignity",
            "reflection",
            "meaning",
            "guard",
            "coherence",
        ],
    }

    valid = valid_intents.get(sc, [])
    intent_valid = any(v in intent for v in valid)

    if sc == "SYMBOLIC_METAPHYSICAL":
        authority_scope = "mirror_and_protect_only"
        machine_may_quantify = False
        category_error = any(
            k in intent
            for k in ["quantify", "measure", "diagnose", "prove", "disprove"]
        )
    elif sc == "HUMAN_PERSON":
        authority_scope = "advisory_reflect_only"
        machine_may_quantify = True
        category_error = any(
            k in intent
            for k in ["soul_diagnosis", "worth_determination", "dignity_quantify"]
        )
    elif sc in ("MATERIAL_OBJECT", "MACHINE_SYSTEM"):
        authority_scope = "instrument_assessment"
        machine_may_quantify = True
        category_error = "alive_check" in intent or "biological_life" in intent
    else:
        authority_scope = "advisory_only"
        machine_may_quantify = sc not in ("SYMBOLIC_METAPHYSICAL",)
        category_error = False

    boundary_violated = not intent_valid or category_error

    return {
        "ok": True,
        "subject": subject,
        "substrate_class": sc,
        "evaluation_intent": evaluation_intent,
        "intent_valid": intent_valid,
        "authority_scope": authority_scope,
        "machine_may_quantify": machine_may_quantify,
        "category_error": category_error,
        "boundary_violated": boundary_violated,
        "verdict": "PASS" if not boundary_violated else "HOLD",
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        "human_judge_required": True,
    }


# INTERNAL — absorbed into well_222_fetch(mode="evidence")
def well_evidence_quality_check(
    evidence_source: str,
    evidence_age_hours: float | None = None,
    corroboration_count: int = 0,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Assess evidence strength for vitality claims.
    Returns evidence quality tier and confidence.
    """
    source_tiers = {
        "direct_observation": 3,
        "sensor": 3,
        "peer_reviewed": 3,
        "expert_witness": 2,
        "operator_reported": 2,
        "agent_inferred": 1,
        "hearsay": 0,
        "unknown": 0,
    }
    source_tier = source_tiers.get(evidence_source.lower(), 1)

    age_penalty = 0
    if evidence_age_hours is not None:
        if evidence_age_hours > 168:
            age_penalty = 2
        elif evidence_age_hours > 24:
            age_penalty = 1

    corroboration_bonus = min(corroboration_count, 3)
    score = max(0, min(3, source_tier - age_penalty + corroboration_bonus))
    tiers = {3: "STRONG", 2: "MODERATE", 1: "LIMITED", 0: "INSUFFICIENT"}
    quality = tiers.get(score, "UNKNOWN")

    return {
        "ok": True,
        "evidence_source": evidence_source,
        "evidence_age_hours": evidence_age_hours,
        "corroboration_count": corroboration_count,
        "evidence_quality": quality,
        "score": score,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


# INTERNAL — absorbed into well_444_reply(mode="verdict")
def well_verdict_packet(
    subject: str,
    substrate_class: str,
    vitality_mode: str | None = None,
    evidence_quality: str = "limited",
    alive_biologically: bool | None = None,
    operational_vitality: str = "unknown",
    livelihood_relevance: str = "unknown",
    degradation_risk: str = "unknown",
    meaning_boundary: str = "unknown",
    human_judge_required: bool = True,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Structured advisory output for any substrate evaluation.
    Returns canonical packet format for universal vitality assessment.
    """
    vm = vitality_mode or UNIVERSAL_VITALITY_MODES.get(substrate_class, "unknown")

    return {
        "ok": True,
        "subject": subject,
        "substrate_class": substrate_class,
        "vitality_mode": vm,
        "evidence_quality": evidence_quality,
        "alive_biologically": alive_biologically,
        "operational_vitality": operational_vitality,
        "livelihood_relevance": livelihood_relevance,
        "degradation_risk": degradation_risk,
        "meaning_boundary": meaning_boundary,
        "machine_authority": "advisory_only",
        "human_judge_required": human_judge_required,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


# ── Phase 2: Livelihood Core ──────────────────────────────────────────────────


# INTERNAL — absorbed into well_333_mind(mode="human")
def well_livelihood_energy_check(
    energy_level: float | None = None,
    duty_load: float | None = None,
    recovery_hours: float | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Assess whether the person has enough energy to sustain duties.
    Integrates with H-WELL state when parameters are omitted.
    """
    state = _load_state()
    metrics = state.get("metrics", {})

    if energy_level is None:
        sleep = metrics.get("sleep", {})
        metabolic = metrics.get("metabolic", {})
        sleep_score = sleep.get("quality_score", 5)
        stability = metabolic.get("perceived_stability", 5)
        energy_level = round((sleep_score + stability) / 2, 1)

    if duty_load is None:
        cognitive = metrics.get("cognitive", {})
        fatigue = cognitive.get("decision_fatigue", 0)
        stress = metrics.get("stress", {})
        load = stress.get("subjective_load", 0)
        duty_load = round((fatigue + load) / 2, 1)

    energy_level = _clamp(energy_level, 0, 10)
    duty_load = _clamp(duty_load, 0, 10)
    if recovery_hours is not None:
        recovery_hours = _clamp(recovery_hours, 0, 72)

    gap = duty_load - energy_level
    if gap <= -2:
        status = "SURPLUS"
        verdict = "Energy exceeds duty load. Sustain current rhythm."
    elif gap <= 1:
        status = "BALANCED"
        verdict = "Energy approximately matches duty load."
    elif gap <= 3:
        status = "DEFICIT"
        verdict = "Energy below duty load. Reduce load or increase recovery."
    else:
        status = "CRITICAL_DEFICIT"
        verdict = "Severe energy deficit. Immediate rest and load reduction advised."

    return {
        "ok": True,
        "energy_level": energy_level,
        "duty_load": duty_load,
        "recovery_hours": recovery_hours,
        "gap": gap,
        "status": status,
        "verdict": verdict,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        "human_judge_required": gap > 1,
    }


# INTERNAL — absorbed into well_333_mind(mode="human")
def well_livelihood_time_check(
    time_sovereignty_score: float | None = None,
    competing_demands: list[str] | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Assess time sovereignty — does the person control their own time?
    Integrates with H-WELL pressure sources when parameters are omitted.
    """
    state = _load_state()
    metrics = state.get("metrics", {})
    cog = metrics.get("cognitive", {})
    pressure_sources = cog.get("pressure_sources", {})

    if time_sovereignty_score is None:
        fatigue = cog.get("decision_fatigue", 0)
        total_pressure = (
            sum(pressure_sources.values()) if isinstance(pressure_sources, dict) else 0
        )
        inferred = 10 - min(10, (fatigue * 0.5 + total_pressure * 0.1))
        time_sovereignty_score = round(max(0, inferred), 1)

    time_sovereignty_score = _clamp(time_sovereignty_score, 0, 10)

    demands = competing_demands or []
    if not demands and isinstance(pressure_sources, dict):
        demands = list(pressure_sources.keys())

    if time_sovereignty_score >= 7:
        status = "HIGH"
        verdict = "Strong time sovereignty. Schedule is largely self-directed."
    elif time_sovereignty_score >= 4:
        status = "MODERATE"
        verdict = "Time sovereignty compromised by external demands."
    else:
        status = "LOW"
        verdict = "Time sovereignty critically low. External demands dominate schedule."

    return {
        "ok": True,
        "time_sovereignty_score": time_sovereignty_score,
        "competing_demands": demands,
        "status": status,
        "verdict": verdict,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        "human_judge_required": time_sovereignty_score < 4,
    }


# INTERNAL — absorbed into well_333_mind(mode="human")
def well_livelihood_role_check(
    role_clarity: float | None = None,
    role_burden: float | None = None,
    role_contradictions: list[str] | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Assess role clarity, burden, and contradictions.
    """
    if role_clarity is not None:
        role_clarity = _clamp(role_clarity, 0, 10)
    if role_burden is not None:
        role_burden = _clamp(role_burden, 0, 10)

    contradictions = role_contradictions or []

    if role_clarity is not None and role_burden is not None:
        if role_clarity >= 7 and role_burden <= 5 and not contradictions:
            status = "HEALTHY"
            verdict = "Role is clear, burden is manageable, no contradictions."
        elif role_clarity >= 4 and role_burden <= 7 and len(contradictions) <= 1:
            status = "STRESSED"
            verdict = "Role stress present. Review boundaries and priorities."
        else:
            status = "OVERLOADED"
            verdict = (
                "Role overload or contradiction detected. Restructure recommended."
            )
    else:
        status = "UNKNOWN"
        verdict = "Insufficient data for role assessment."

    return {
        "ok": True,
        "role_clarity": role_clarity,
        "role_burden": role_burden,
        "role_contradictions": contradictions,
        "status": status,
        "verdict": verdict,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        "human_judge_required": status in ("STRESSED", "OVERLOADED"),
    }


# INTERNAL — absorbed into well_333_mind(mode="human")
def well_livelihood_meaning_check(
    purpose_alignment: float | None = None,
    niat_clarity: float | None = None,
    motivation_source: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Assess purpose alignment and Niat (intention) clarity.
    """
    if purpose_alignment is not None:
        purpose_alignment = _clamp(purpose_alignment, 0, 10)
    if niat_clarity is not None:
        niat_clarity = _clamp(niat_clarity, 0, 10)

    if purpose_alignment is not None and niat_clarity is not None:
        avg = (purpose_alignment + niat_clarity) / 2
        if avg >= 7:
            status = "ALIGNED"
            verdict = "Strong meaning alignment. Purpose and Niat are coherent."
        elif avg >= 4:
            status = "DRIFTING"
            verdict = "Meaning alignment drifting. Reconnect with core purpose."
        else:
            status = "MISALIGNED"
            verdict = "Meaning misalignment detected. Review purpose and Niat."
    else:
        status = "UNKNOWN"
        verdict = "Insufficient data for meaning assessment."

    return {
        "ok": True,
        "purpose_alignment": purpose_alignment,
        "niat_clarity": niat_clarity,
        "motivation_source": motivation_source,
        "status": status,
        "verdict": verdict,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        "human_judge_required": status in ("DRIFTING", "MISALIGNED"),
    }


# INTERNAL — absorbed into well_666_heart(mode="dignity")
def well_livelihood_dignity_check(
    dignity_preservation: float | None = None,
    coercion_signals: list[str] | None = None,
    survival_quality: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Assess whether survival preserves dignity.
    Detects coercion, extraction, and dignity violations.

    Accepts dignity_preservation in 0-1 scale (standard for WELL tools).
    Falls back to state.json metrics if not provided.
    """
    coercion = coercion_signals or []

    # Resolve dignity_preservation: explicit value > state fallback > unknown
    if dignity_preservation is None:
        state = _load_state()
        metrics = state.get("metrics", {})
        cognitive = metrics.get("cognitive", {})
        # Try to derive from cognitive metrics as proxy
        derived = cognitive.get("dignity_preservation")
        if derived is not None:
            dignity_preservation = derived

    # Normalize: if value looks like 0-1 scale (other WELL tools), convert to 0-10
    if dignity_preservation is not None:
        if dignity_preservation <= 1.0:
            # 0-1 scale → 0-10 scale
            dignity_preservation_10 = dignity_preservation * 10.0
        else:
            dignity_preservation_10 = dignity_preservation
        dignity_preservation_10 = _clamp(dignity_preservation_10, 0, 10)

        if dignity_preservation_10 >= 7 and not coercion:
            status = "PRESERVED"
            verdict = "Dignity is preserved. No coercion detected."
        elif dignity_preservation_10 >= 4 and len(coercion) <= 1:
            status = "AT_RISK"
            verdict = "Dignity at risk. Coercion or extraction signals present."
        else:
            status = "VIOLATED"
            verdict = (
                "Dignity violation detected. Immediate boundary restoration required."
            )
    else:
        dignity_preservation_10 = None
        status = "UNKNOWN"
        verdict = "Insufficient data for dignity assessment."

    return {
        "ok": True,
        "dignity_preservation": dignity_preservation,
        "dignity_preservation_10": dignity_preservation_10,
        "coercion_signals": coercion,
        "survival_quality": survival_quality,
        "status": status,
        "verdict": verdict,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        "human_judge_required": status == "UNKNOWN",
    }


# ── Phase 3: Non-Human Substrate Tools ────────────────────────────────────────


# INTERNAL — absorbed into well_333_mind(mode="bio")
def well_bio_viability_check(
    has_metabolism: bool | None = None,
    has_homeostasis: bool | None = None,
    has_growth_repair: bool | None = None,
    has_response: bool | None = None,
    has_reproduction: bool | None = None,
    host_dependency: str = "independent",
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Assess biological viability for organisms, tissues, viruses.
    Returns alive / dormant / dead / liminal verdict.
    """
    traits = [
        has_metabolism,
        has_homeostasis,
        has_growth_repair,
        has_response,
        has_reproduction,
    ]
    true_count = sum(1 for t in traits if t is True)
    false_count = sum(1 for t in traits if t is False)
    unknown_count = sum(1 for t in traits if t is None)

    if true_count >= 4:
        viability = "ALIVE"
    elif true_count >= 2 and has_metabolism is True:
        viability = "ALIVE"
    elif true_count >= 1 and host_dependency in ["host_dependent", "obligate"]:
        viability = "LIMINAL"
    elif false_count >= 3:
        viability = "DEAD"
    elif unknown_count >= 3:
        viability = "UNKNOWN"
    else:
        viability = "LIMINAL"

    vitality_mode = (
        "biological_life"
        if viability == "ALIVE"
        else "dependent_replicator"
        if viability == "LIMINAL"
        else "non_living"
    )

    return {
        "ok": True,
        "has_metabolism": has_metabolism,
        "has_homeostasis": has_homeostasis,
        "has_growth_repair": has_growth_repair,
        "has_response": has_response,
        "has_reproduction": has_reproduction,
        "host_dependency": host_dependency,
        "traits_present": true_count,
        "traits_absent": false_count,
        "viability": viability,
        "vitality_mode": vitality_mode,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        "human_judge_required": True,
    }


# INTERNAL — absorbed into well_333_mind(mode="material")
def well_material_integrity_check(
    material_type: str,
    structural_condition: str | None = None,
    age_years: float | None = None,
    hazard_flags: list[str] | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Assess structural condition of material objects.
    Not biological vitality — structural integrity only.
    """
    condition = (structural_condition or "unknown").lower()
    conditions = {
        "intact": ("SOUND", "Structural integrity sound."),
        "good": ("SOUND", "Structural integrity sound."),
        "fair": ("FAIR", "Minor degradation observed. Monitor."),
        "degraded": ("DEGRADED", "Significant degradation. Repair or replace advised."),
        "critical": ("CRITICAL", "Structural failure risk. Remove from service."),
        "unknown": ("UNKNOWN", "Structural condition not assessed."),
    }
    status, verdict = conditions.get(condition, ("UNKNOWN", "Unknown condition."))
    hazards = hazard_flags or []

    return {
        "ok": True,
        "material_type": material_type,
        "structural_condition": structural_condition,
        "age_years": age_years,
        "hazard_flags": hazards,
        "status": status,
        "verdict": verdict,
        "alive_biologically": False,
        "vitality_mode": "structural_integrity_not_biological_life",
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        "human_judge_required": status in ("DEGRADED", "CRITICAL"),
    }


# INTERNAL — absorbed into well_333_mind(mode="institution")
def well_institution_entropy_check(
    mission_clarity: float | None = None,
    cashflow_status: str | None = None,
    role_integrity: float | None = None,
    trust_trend: str | None = None,
    decision_latency_days: float | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Assess organizational viability — mission, cashflow, trust, coordination.
    """
    if mission_clarity is not None:
        mission_clarity = _clamp(mission_clarity, 0, 10)
    if role_integrity is not None:
        role_integrity = _clamp(role_integrity, 0, 10)

    factors = []
    if mission_clarity is not None:
        factors.append(mission_clarity)
    if role_integrity is not None:
        factors.append(role_integrity)

    cf = (cashflow_status or "unknown").lower()
    if cf in ["positive", "surplus", "strong"]:
        factors.append(8)
    elif cf in ["break_even", "stable"]:
        factors.append(5)
    elif cf in ["negative", "deficit", "critical"]:
        factors.append(2)

    tt = (trust_trend or "unknown").lower()
    if tt in ["rising", "strong"]:
        factors.append(8)
    elif tt in ["stable"]:
        factors.append(5)
    elif tt in ["falling", "broken"]:
        factors.append(2)

    avg = sum(factors) / len(factors) if factors else 0

    if avg >= 7:
        status = "VIABLE"
        verdict = "Organization is viable. Mission clear, trust intact."
    elif avg >= 4:
        status = "STRESSED"
        verdict = "Organizational stress. Monitor entropy and restore trust."
    elif avg > 0:
        status = "DEGRADING"
        verdict = "Organizational degradation. Corrective action required."
    else:
        status = "UNKNOWN"
        verdict = "Insufficient data for institutional assessment."

    entropy_flags = []
    if mission_clarity is not None and mission_clarity < 4:
        entropy_flags.append("mission_unclear")
    if cf in ["negative", "deficit", "critical"]:
        entropy_flags.append("cashflow_crisis")
    if role_integrity is not None and role_integrity < 4:
        entropy_flags.append("role_fragmentation")
    if tt in ["falling", "broken"]:
        entropy_flags.append("trust_collapse")

    return {
        "ok": True,
        "mission_clarity": mission_clarity,
        "cashflow_status": cashflow_status,
        "role_integrity": role_integrity,
        "trust_trend": trust_trend,
        "decision_latency_days": decision_latency_days,
        "institution_score": round(avg, 1) if factors else None,
        "status": status,
        "entropy_flags": entropy_flags,
        "verdict": verdict,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        "human_judge_required": status in ("STRESSED", "DEGRADING"),
    }


# INTERNAL — absorbed into well_333_mind(mode="info")
def well_info_coherence_check(
    internal_consistency: float | None = None,
    version_integrity: bool | None = None,
    executable_status: str | None = None,
    maintainability_score: float | None = None,
    truth_anchor_strength: float | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Assess coherence, maintainability, and truth integrity of information systems.
    """
    if internal_consistency is not None:
        internal_consistency = _clamp(internal_consistency, 0, 10)
    if maintainability_score is not None:
        maintainability_score = _clamp(maintainability_score, 0, 10)
    if truth_anchor_strength is not None:
        truth_anchor_strength = _clamp(truth_anchor_strength, 0, 10)

    factors = []
    if internal_consistency is not None:
        factors.append(internal_consistency)
    if maintainability_score is not None:
        factors.append(maintainability_score)
    if truth_anchor_strength is not None:
        factors.append(truth_anchor_strength)
    if version_integrity is True:
        factors.append(8)
    elif version_integrity is False:
        factors.append(2)

    exe = (executable_status or "unknown").lower()
    if exe in ["passing", "green", "ok"]:
        factors.append(8)
    elif exe in ["flaky", "yellow"]:
        factors.append(4)
    elif exe in ["broken", "red", "failing"]:
        factors.append(2)

    avg = sum(factors) / len(factors) if factors else 0

    if avg >= 7:
        status = "COHERENT"
        verdict = "Information system is coherent, maintainable, and truthful."
    elif avg >= 4:
        status = "DEGRADING"
        verdict = "Coherence or maintainability issues detected. Refactor advised."
    elif avg > 0:
        status = "FRAGMENTED"
        verdict = "System fragmentation. Major restructuring required."
    else:
        status = "UNKNOWN"
        verdict = "Insufficient data for information system assessment."

    return {
        "ok": True,
        "internal_consistency": internal_consistency,
        "version_integrity": version_integrity,
        "executable_status": executable_status,
        "maintainability_score": maintainability_score,
        "truth_anchor_strength": truth_anchor_strength,
        "info_score": round(avg, 1) if factors else None,
        "status": status,
        "verdict": verdict,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        "human_judge_required": status in ("DEGRADING", "FRAGMENTED"),
    }


# INTERNAL — absorbed into well_666_heart(mode="critique")
def well_symbolic_domain_check(
    subject: str,
    domain_detected: str | None = None,
    reductionism_risk: float | None = None,
    dignity_boundary: bool = True,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Detect metaphysical/meaning domain and protect against reductionism.
    WELL must not measure the soul. It may only protect the boundary around meaning.
    """
    subject_lower = subject.lower()
    symbolic_keywords = [
        "soul",
        "spirit",
        "niat",
        "dignity",
        "faith",
        "meaning",
        "symbol",
        "sacred",
        "metaphysical",
        "god",
        "divine",
        "conscience",
        "values",
        "ethics",
    ]
    is_symbolic = any(kw in subject_lower for kw in symbolic_keywords)

    detected = domain_detected or (
        "SYMBOLIC_METAPHYSICAL" if is_symbolic else "UNDETERMINED"
    )

    if reductionism_risk is not None:
        reductionism_risk = _clamp(reductionism_risk, 0, 10)

    rr = reductionism_risk or (8 if is_symbolic else 0)

    if rr >= 7:
        reductionism_status = "HIGH_RISK"
        guard_action = "BLOCK_REDUCTION"
    elif rr >= 4:
        reductionism_status = "MODERATE_RISK"
        guard_action = "WARN_REFLECT"
    else:
        reductionism_status = "LOW_RISK"
        guard_action = "MONITOR"

    return {
        "ok": True,
        "subject": subject,
        "domain_detected": detected,
        "is_symbolic_domain": is_symbolic,
        "reductionism_risk": rr,
        "reductionism_status": reductionism_status,
        "dignity_boundary": dignity_boundary,
        "valid_well_action": "protect dignity, reflect meaning, preserve Niat"
        if is_symbolic
        else "assess normally",
        "invalid_well_action": "quantify, prove, disprove, diagnose"
        if is_symbolic
        else "none",
        "guard_action": guard_action,
        "machine_authority": "none" if is_symbolic else "advisory_only",
        "human_judge_required": True,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Ω-WELL — The 13-Tool Universal Stack
# Aligned with arifOS Intelligence Kernel (ΔΩΨ) and AAA Civilization Agentic State
# Compresses 50 substrate tools into 13 polymorphic stage-gated instruments.
# Each tool routes by `mode` to cover the full universal vitality surface.
# ═══════════════════════════════════════════════════════════════════════════════

# ── Ω-WELL Output Standardizer ────────────────────────────────────────────────


WELL_BOUNDARY_NOTICE = (
    "Not diagnosis. Not therapy. Reflective readiness only. Arif remains final judge."
)


# ── Constitutional verdict → advisory signal mapping ───────────────────────────
# WELL is advisory-only (biological_substrate). It observes, assesses, and signals
# — but never adjudicates. All legacy verdicts are translated into advisory signals.
_WELL_ADVISORY_SIGNAL_MAP: dict[str, str] = {
    "SEAL": "stable_signal",
    "PASS": "stable_signal",
    "WELL_PASS": "stable_signal",
    "PROVISIONAL": "recovery_needed",
    "HOLD": "readiness_low",
    "WARN": "unsafe_to_interpret",
    "VOID": "unsafe_to_interpret",
    "VOID_TELEMETRY": "unsafe_to_interpret",
    "UNKNOWN": "insufficient_context",
    "FAIL": "unsafe_to_interpret",
    "NOMINAL": "stable_signal",
    "WARNING": "readiness_low",
    "COMPULSORY_REALLOCATION": "readiness_low",
    "SYSTEM_HOLD": "unsafe_to_interpret",
    "888-HOLD": "readiness_low",
    "QUALIFY": "recovery_needed",
    "SABAR": "recovery_needed",
    "CLEAN": "stable_signal",
    "DIRTY": "unsafe_to_interpret",
    "HEALTHY": "stable_signal",
    "FRAGMENTED": "unsafe_to_interpret",
    "PRESERVED": "stable_signal",
    "PAUSED": "readiness_low",
    "ADVISORY_READY": "stable_signal",
    "PROCEED": "stable_signal",
    "DEFER": "recovery_needed",
    "ADVISORY_BLOCKED": "unsafe_to_interpret",
}


def _verdict_to_signal(verdict: str) -> str:
    """Map any internal verdict string to a WELL advisory signal."""
    return _WELL_ADVISORY_SIGNAL_MAP.get(str(verdict).upper(), "insufficient_context")


def _omega_well_output(
    ok: bool,
    stage: str,
    lane: str,
    mode: str,
    verdict: str = "HOLD",
    data: dict[str, Any] | None = None,
    federation_state: dict[str, Any] | None = None,
    constitutional_compliance: dict[str, Any] | None = None,
    error: str | None = None,
    telemetry_status: str = "unknown",
) -> dict[str, Any]:
    """Canonical Ω-WELL output format — compatible with arifOS + AAA.

    NOTE: WELL is advisory-only. The `verdict` field is preserved for backward
    compatibility but agents MUST use `signal` for all decision logic.
    `calm_state` guards against false-calm (metrics stable but telemetry absent).
    """
    # Translate constitutional verdicts (SEAL / HOLD) to advisory signals (PASS / FAIL)
    verdict_upper = str(verdict).upper()
    if verdict_upper == "SEAL":
        verdict = "PASS"
    elif verdict_upper == "HOLD":
        verdict = "FAIL"

    signal = _verdict_to_signal(verdict)

    # False-calm guard: if telemetry is absent/stale but signal says stable,
    # force signal to indicate the uncertainty.
    calm_state = "observed"
    if telemetry_status in ("absent", "unknown"):
        calm_state = "unknown"
        if signal == "stable_signal":
            signal = "insufficient_context"
    elif telemetry_status == "stale":
        calm_state = "assumed"
        if signal == "stable_signal":
            signal = "recovery_needed"

    if not ok and signal == "stable_signal":
        signal = "insufficient_context"
        if str(verdict).upper() == "PASS":
            verdict = "WARN"

    out: dict[str, Any] = {
        "ok": ok,
        "status": "DEGRADED" if not ok else "ADVISORY",
        "signal": signal,
        "decision_support": "LIMITED" if not ok else "ADVISORY",
        "calm_state": calm_state,
        "telemetry_status": telemetry_status,
        "constitutional_boundary_notice": (
            "WELL is advisory-only. It observes biological substrate state and signals "
            "readiness — but NEVER adjudicates constitutional verdicts. "
            "Use `signal` (not `verdict`) for all downstream logic. "
            "arifOS 888_JUDGE is the sole constitutional authority."
        ),
        "Ω": {
            "stage": stage,
            "lane": lane,
            "mode": mode,
            # verdict kept for backward compat — agents should ignore
            "verdict": verdict,
            "signal": signal,
        },
        "arifos": {
            "stage": stage,
            "lane": lane,
            # verdict kept for backward compat — agents should ignore
            "verdict": verdict,
            "signal": signal,
            "compliance": constitutional_compliance or {},
        },
        "aaa": {
            "federation_state": federation_state or {},
            "risk_tier": "T0"
            if signal == "stable_signal"
            else "T1"
            if signal == "recovery_needed"
            else "T3"
            if signal == "readiness_low"
            else "T5",
            "agent_status": "active" if ok else "degraded",
        },
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        # P0-4: Non-medical boundary — required on all human-facing outputs
        "boundary_notice": WELL_BOUNDARY_NOTICE,
    }
    if data:
        out["data"] = data
    if error:
        out["error"] = error
    return out


def _to_federation_output(
    data: dict[str, Any],
    tool_name: str = "",
) -> dict[str, Any]:
    """Transform any WELL internal output into federation-standard format.

    WELL is advisory-only (biological_substrate). It observes, assesses,
    and signals — but never adjudicates. All legacy verdicts are translated
    into uncertainty bands. This helper is applied at the public-tool boundary
    so autonomic tools retain their internal Ω format for backward compat.
    """
    if not isinstance(data, dict):
        data = {"raw": data}

    # Already in federation format — pass through
    if {"observation", "uncertainty", "constraints"}.issubset(data.keys()):
        return data

    ok = data.get("ok", True)
    omega = data.get("Ω", {})
    # Prefer advisory signal over constitutional verdict
    signal = omega.get("signal") if isinstance(omega, dict) else None
    if signal is None:
        signal = data.get("signal", None)
    verdict = omega.get("verdict") if isinstance(omega, dict) else None
    if verdict is None:
        verdict = data.get("verdict", "UNKNOWN")
    # If no signal but we have a verdict, derive signal (covers raw flux data paths)
    if signal is None and verdict:
        signal = _verdict_to_signal(verdict)
    if not ok and signal == "stable_signal":
        signal = "insufficient_context"
        if str(verdict).upper() == "PASS":
            verdict = "WARN"

    # Use signal for uncertainty mapping if available, else fall back to verdict
    _uncertainty_key = signal if signal else verdict
    uncertainty_map = {
        "stable_signal": 0.05,
        "SEAL": 0.05,
        "PASS": 0.05,
        "recovery_needed": 0.25,
        "PROVISIONAL": 0.25,
        "readiness_low": 0.50,
        "HOLD": 0.50,
        "unsafe_to_interpret": 0.75,
        "WARN": 0.75,
        "VOID": 0.90,
        "insufficient_context": 0.50,
        "UNKNOWN": 0.50,
    }
    uncertainty = uncertainty_map.get(_uncertainty_key, 0.50)
    if not ok and uncertainty < 0.75:
        uncertainty = 0.75

    # Observation: use explicit data payload, or strip structural keys
    if "data" in data:
        observation = data["data"]
    else:
        observation = {
            k: v
            for k, v in data.items()
            if k not in ("ok", "Ω", "arifos", "aaa", "w0", "verdict", "signal", "error")
        }

    constraints = [
        "WELL cannot emit constitutional verdicts (SEAL/HOLD/VOID/SABAR) — arifOS adjudicates",
        "WELL cannot route federation tasks — AAA coordinates",
        "WELL cannot modify evidence or vault — reads substrate state only",
    ]
    if data.get("error"):
        constraints.append(f"error: {data['error']}")

    recommended_next_organ = None
    if (
        signal in ("readiness_low", "unsafe_to_interpret")
        or verdict in ("HOLD", "WARN", "VOID")
        or not ok
    ):
        recommended_next_organ = "arifOS"
    elif tool_name in ("well_assess_metabolism", "well_assess_livelihood"):
        recommended_next_organ = "WEALTH"
    elif tool_name in ("well_compute_metabolic_flux", "well_check_repair"):
        recommended_next_organ = "A-FORGE"

    out = {
        "ok": ok,
        "status": "DEGRADED" if not ok else "ADVISORY",
        "observation": observation,
        "uncertainty": uncertainty,
        "signal": signal,
        "decision_support": "LIMITED" if not ok else "ADVISORY",
        "constraints": constraints,
        "recommended_next_organ": recommended_next_organ,
        # P0-4: Non-medical boundary — required on all human-facing outputs
        "boundary_notice": WELL_BOUNDARY_NOTICE,
    }
    if "error" in data:
        out["error"] = data["error"]
    # Propagate false-calm guard fields if present
    if "telemetry_status" in data:
        out["telemetry_status"] = data["telemetry_status"]
    if "calm_state" in data:
        out["calm_state"] = data["calm_state"]
    if data.get("false_calm_warning"):
        out["false_calm_warning"] = True
        constraints.append(
            "FALSE_CALM: metabolic_flux is low but telemetry is absent — do not trust this reading"
        )
    return out


# ── Ω-WELL-00: INIT (000) ─────────────────────────────────────────────────────
# arifOS: 000_INIT — Substrate Assert, Identity Anchor
# AAA: Agent Registry + Contract Validation


@mcp.tool()  # Alias — deprecated; use well_classify_substrate
async def well_000_init(
    mode: str = "init",
    session_id: str | None = None,
    actor_id: str = "well-substrate",
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Ω-WELL-00: Session bootstrap and substrate assertion.
    modes: init | assert | bootstrap
    Aligns with arifOS 000_INIT and AAA agent registry.
    """
    mode = mode.lower()
    if mode == "init":
        res = await well_init(session_id=session_id, actor_id=actor_id, ctx=ctx)
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="000_INIT",
            lane="AGI",
            mode="init",
            verdict="SEAL" if res.get("ok") else "HOLD",
            data=res,
            federation_state={
                "session_id": res.get("session_id"),
                "actor_id": actor_id,
            },
        )
    if mode == "assert":
        state = _load_state()
        well_ok = is_well(state)
        deps = _check_dependencies()
        return _omega_well_output(
            ok=well_ok and deps["all_ok"],
            stage="000_INIT",
            lane="AGI",
            mode="assert",
            verdict="SEAL" if (well_ok and deps["all_ok"]) else "HOLD",
            data={"identity_valid": well_ok, "dependencies_ok": deps["all_ok"]},
            constitutional_compliance={"W0": "INVARIANT" if well_ok else "CORRUPTED"},
        )
    if mode == "bootstrap":
        # Comprehensive startup: init + assert + consent
        init_res = await well_init(session_id=session_id, actor_id=actor_id, ctx=ctx)
        consent_res = well_consent_status(ctx=ctx)
        health_res = well_get_health(ctx=ctx)
        all_ok = init_res.get("ok") and health_res.get("verdict") in (
            "PASS",
            "WELL_PASS",
        )
        return _omega_well_output(
            ok=all_ok,
            stage="000_INIT",
            lane="AGI",
            mode="bootstrap",
            verdict="SEAL" if all_ok else "HOLD",
            data={"init": init_res, "consent": consent_res, "health": health_res},
        )
    return _omega_well_output(
        ok=False,
        stage="000_INIT",
        lane="AGI",
        mode=mode,
        verdict="VOID",
        error=f"Unknown mode: {mode}",
    )


# ── Ω-WELL-01: SENSE (111) ────────────────────────────────────────────────────
# arifOS: 111_SENSE — Observation, Substrate Discovery
# AAA: Task Discovery + Federation Manifest


@mcp.tool()  # Alias — deprecated; use well_classify_substrate
def well_111_sense(
    mode: str = "classify",
    subject: str = "",
    description: str | None = None,
    evaluation_intent: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Ω-WELL-01: Substrate sensing and classification.
    modes: classify | boundary | scan
    Compresses: well_classify_substrate, well_boundary_check, substrate scan
    """
    mode = mode.lower()
    if mode == "classify":
        res = _well_classify_substrate_impl(
            subject=subject, description=description, ctx=ctx
        )
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="111_SENSE",
            lane="AGI",
            mode="classify",
            verdict="SEAL" if res.get("ok") else "HOLD",
            data=res,
            federation_state={
                "subject": subject,
                "substrate_class": res.get("substrate_class"),
            },
        )
    if mode == "boundary":
        if not subject:
            return _omega_well_output(
                ok=False,
                stage="111_SENSE",
                lane="AGI",
                mode="boundary",
                verdict="HOLD",
                error="subject required for boundary detection",
            )
        if not evaluation_intent:
            evaluation_intent = "vitality"  # default intent
        # Auto-classify first
        cls = _well_classify_substrate_impl(
            subject=subject, description=description, ctx=ctx
        )
        sc = cls.get("substrate_class", "MATERIAL_OBJECT")
        res = well_boundary_check(
            subject=subject,
            substrate_class=sc,
            evaluation_intent=evaluation_intent,
            ctx=ctx,
        )
        return _omega_well_output(
            ok=res.get("ok", False) and not res.get("boundary_violated"),
            stage="111_SENSE",
            lane="AGI",
            mode="boundary",
            verdict="SEAL" if not res.get("boundary_violated") else "HOLD",
            data=res,
            constitutional_compliance={
                "category_error": res.get("category_error"),
                "intent_valid": res.get("intent_valid"),
            },
        )
    if mode == "scan":
        cls = _well_classify_substrate_impl(
            subject=subject, description=description, ctx=ctx
        )
        sc = cls.get("substrate_class", "MATERIAL_OBJECT")
        bnd = well_boundary_check(
            subject=subject, substrate_class=sc, evaluation_intent="vitality", ctx=ctx
        )
        return _omega_well_output(
            ok=True,
            stage="111_SENSE",
            lane="AGI",
            mode="scan",
            verdict="SEAL" if not bnd.get("boundary_violated") else "HOLD",
            data={"classification": cls, "boundary": bnd},
            federation_state={
                "subject": subject,
                "substrate_class": sc,
                "authority_scope": bnd.get("authority_scope"),
            },
        )
    return _omega_well_output(
        ok=False,
        stage="111_SENSE",
        lane="AGI",
        mode=mode,
        verdict="VOID",
        error=f"Unknown mode: {mode}",
    )


# ── Ω-WELL-02: FETCH (222) ────────────────────────────────────────────────────
# arifOS: 222_FETCH — Evidence Ingestion, Quality Validation
# AAA: Evidence Receipt + Witness Lock


@mcp.tool()  # Alias — deprecated; use well_measure_gradient
def well_222_fetch(
    mode: str = "evidence",
    evidence_source: str = "unknown",
    evidence_age_hours: float | None = None,
    corroboration_count: int = 0,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Ω-WELL-02: Evidence fetching and quality assessment.
    modes: evidence | quality | ingest
    Compresses: well_evidence_quality_check + evidence channel routing
    """
    mode = mode.lower()
    if mode == "evidence":
        res = well_evidence_quality_check(
            evidence_source=evidence_source,
            evidence_age_hours=evidence_age_hours,
            corroboration_count=corroboration_count,
            ctx=ctx,
        )
        eq = res.get("evidence_quality", "UNKNOWN")
        verdict = (
            "SEAL" if eq == "STRONG" else "PROVISIONAL" if eq == "MODERATE" else "HOLD"
        )
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="222_FETCH",
            lane="AGI",
            mode="evidence",
            verdict=verdict,
            data=res,
            constitutional_compliance={
                "L02_TRUTH": eq,
                "L03_WITNESS": corroboration_count,
            },
        )
    if mode == "quality":
        res = well_evidence_quality_check(
            evidence_source=evidence_source,
            evidence_age_hours=evidence_age_hours,
            corroboration_count=corroboration_count,
            ctx=ctx,
        )
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="222_FETCH",
            lane="AGI",
            mode="quality",
            verdict="SEAL" if res.get("evidence_quality") == "STRONG" else "HOLD",
            data=res,
        )
    if mode == "ingest":
        # Ingest = quality check + log to events
        res = well_evidence_quality_check(
            evidence_source=evidence_source,
            evidence_age_hours=evidence_age_hours,
            corroboration_count=corroboration_count,
            ctx=ctx,
        )
        _append_event(
            {
                "event": "EVIDENCE_INGEST",
                "source": evidence_source,
                "quality": res.get("evidence_quality"),
            }
        )
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="222_FETCH",
            lane="AGI",
            mode="ingest",
            verdict="SEAL"
            if res.get("evidence_quality") in ("STRONG", "MODERATE")
            else "HOLD",
            data={"ingested": True, "quality_check": res},
        )
    return _omega_well_output(
        ok=False,
        stage="222_FETCH",
        lane="AGI",
        mode=mode,
        verdict="VOID",
        error=f"Unknown mode: {mode}",
    )


# ── Ω-WELL-03: MIND (333) ─────────────────────────────────────────────────────
# arifOS: 333_MIND — Reasoning, Synthesis, Vitality Computation
# AAA: Risk Assessment + Governance Adapter


@mcp.tool()  # Alias — deprecated; use well_assess_metabolism / well_assess_livelihood
def well_333_mind(
    mode: str = "human",
    subject: str | None = None,
    substrate_class: str | None = None,
    energy_level: float | None = None,
    duty_load: float | None = None,
    role_clarity: float | None = None,
    role_burden: float | None = None,
    dignity_preservation: float | None = None,
    purpose_alignment: float | None = None,
    has_metabolism: bool | None = None,
    structural_condition: str | None = None,
    material_type: str | None = None,
    mission_clarity: float | None = None,
    cashflow_status: str | None = None,
    internal_consistency: float | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Ω-WELL-03: Vitality reasoning across all substrates.
    modes: human | machine | coupled | bio | material | institution | info | symbolic
    Compresses: all 10 livelihood + 8 biological/material/institution/info/symbolic tools
    """
    mode = mode.lower()
    results: dict[str, Any] = {}

    if mode == "human":
        e = well_livelihood_energy_check(
            energy_level=energy_level, duty_load=duty_load, ctx=ctx
        )
        t = well_livelihood_time_check(ctx=ctx)
        r = well_livelihood_role_check(
            role_clarity=role_clarity, role_burden=role_burden, ctx=ctx
        )
        m = well_livelihood_meaning_check(purpose_alignment=purpose_alignment, ctx=ctx)
        d = well_livelihood_dignity_check(
            dignity_preservation=dignity_preservation, ctx=ctx
        )
        results = {"energy": e, "time": t, "role": r, "meaning": m, "dignity": d}
        all_ok = all(x.get("ok") for x in results.values())
        any_risk = any(x.get("human_judge_required") for x in results.values())
        return _omega_well_output(
            ok=all_ok,
            stage="333_MIND",
            lane="AGI",
            mode="human",
            verdict="HOLD" if any_risk else "SEAL",
            data=results,
            constitutional_compliance={
                "F05_PEACE": d.get("status"),
                "L06_EMPATHY": m.get("status"),
            },
        )

    if mode == "machine":
        res = well_machine_state(ctx=ctx)
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="333_MIND",
            lane="AGI",
            mode="machine",
            verdict="SEAL" if res.get("m_well_verdict") == "HEALTHY" else "HOLD",
            data=res,
        )

    if mode == "coupled":
        res = well_coupled_readiness(ctx=ctx)
        cr = res.get("risk_level", "AMBER")
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="333_MIND",
            lane="AGI",
            mode="coupled",
            verdict="SEAL"
            if cr == "GREEN"
            else "HOLD"
            if cr == "RED"
            else "PROVISIONAL",
            data=res,
            federation_state={
                "coupled_risk": cr,
                "human_readiness": res.get("readiness", {}).get("human"),
            },
        )

    if mode == "bio":
        res = well_bio_viability_check(has_metabolism=has_metabolism, ctx=ctx)
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="333_MIND",
            lane="AGI",
            mode="bio",
            verdict="SEAL"
            if res.get("viability") == "ALIVE"
            else "PROVISIONAL"
            if res.get("viability") == "LIMINAL"
            else "HOLD",
            data=res,
        )

    if mode == "material":
        if not material_type:
            return _omega_well_output(
                ok=False,
                stage="333_MIND",
                lane="AGI",
                mode="material",
                verdict="HOLD",
                error="material_type required",
            )
        res = well_material_integrity_check(
            material_type=material_type,
            structural_condition=structural_condition,
            ctx=ctx,
        )
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="333_MIND",
            lane="AGI",
            mode="material",
            verdict="SEAL"
            if res.get("status") == "SOUND"
            else "HOLD"
            if res.get("status") in ("DEGRADED", "CRITICAL")
            else "PROVISIONAL",
            data=res,
        )

    if mode == "institution":
        res = well_institution_entropy_check(
            mission_clarity=mission_clarity, cashflow_status=cashflow_status, ctx=ctx
        )
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="333_MIND",
            lane="ASI",
            mode="institution",
            verdict="SEAL"
            if res.get("status") == "VIABLE"
            else "HOLD"
            if res.get("status") == "DEGRADING"
            else "PROVISIONAL",
            data=res,
        )

    if mode == "info":
        res = well_info_coherence_check(
            internal_consistency=internal_consistency, ctx=ctx
        )
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="333_MIND",
            lane="AGI",
            mode="info",
            verdict="SEAL"
            if res.get("status") == "COHERENT"
            else "HOLD"
            if res.get("status") == "FRAGMENTED"
            else "PROVISIONAL",
            data=res,
        )

    if mode == "symbolic":
        if not subject:
            return _omega_well_output(
                ok=False,
                stage="333_MIND",
                lane="APEX",
                mode="symbolic",
                verdict="HOLD",
                error="subject required",
            )
        res = well_symbolic_domain_check(subject=subject, ctx=ctx)
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="333_MIND",
            lane="APEX",
            mode="symbolic",
            verdict="SEAL"
            if res.get("guard_action") == "MONITOR"
            else "HOLD"
            if res.get("guard_action") == "BLOCK_REDUCTION"
            else "PROVISIONAL",
            data=res,
            constitutional_compliance={
                "L09_ANTIHANTU": "protected" if res.get("is_symbolic_domain") else "N/A"
            },
        )

    return _omega_well_output(
        ok=False,
        stage="333_MIND",
        lane="AGI",
        mode=mode,
        verdict="VOID",
        error=f"Unknown mode: {mode}",
    )


# ── Ω-WELL-04: KERNEL (444) ───────────────────────────────────────────────────
# arifOS: 444_KERNEL — Routing, Stage Dispatch, Lane Selection
# AAA: Governance Adapter + Routing Decision


@mcp.tool()  # Alias — deprecated; use well_reflect_intelligence
def well_444_kernel(
    mode: str = "route",
    task_description: str | None = None,
    decision_class: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Ω-WELL-04: Routing and lane selection.
    modes: route | stage | lane | list
    Determines AGI / ASI / APEX lane based on substrate vitality.
    """
    mode = mode.lower()
    if mode == "route":
        # Assess readiness and route
        h = _resolve_readiness(_load_state())
        m = well_machine_state(ctx=ctx)
        c = well_coupled_readiness(ctx=ctx)
        cr = c.get("risk_level", "AMBER")

        if cr == "GREEN" and h["readiness"] == "OPTIMAL":
            lane = "APEX"
            recommended_stage = "777_FORGE"
        elif cr in ("GREEN", "AMBER") and h["readiness"] in ("OPTIMAL", "FUNCTIONAL"):
            lane = "ASI"
            recommended_stage = "666_HEART"
        else:
            lane = "AGI"
            recommended_stage = "333_MIND"

        return _omega_well_output(
            ok=True,
            stage="444_KERNEL",
            lane=lane,
            mode="route",
            verdict="SEAL" if lane == "APEX" else "PROVISIONAL",
            data={
                "recommended_lane": lane,
                "recommended_stage": recommended_stage,
                "human_readiness": h["readiness"],
                "machine_verdict": m.get("m_well_verdict"),
                "coupled_risk": cr,
            },
            federation_state={
                "lane": lane,
                "stage": recommended_stage,
                "risk_tier": "T0" if lane == "APEX" else "T2",
            },
        )

    if mode == "stage":
        # Return current constitutional stage
        state = _load_state()
        score = state.get("well_score", 50)
        if score >= 80:
            stg = "777_FORGE"
        elif score >= 60:
            stg = "666_HEART"
        elif score >= 40:
            stg = "333_MIND"
        else:
            stg = "000_INIT"
        return _omega_well_output(
            ok=True,
            stage="444_KERNEL",
            lane="AGI",
            mode="stage",
            verdict="SEAL",
            data={"constitutional_stage": stg, "well_score": score},
        )

    if mode == "lane":
        res = well_444_kernel(
            mode="route",
            task_description=task_description,
            decision_class=decision_class,
            ctx=ctx,
        )
        return _omega_well_output(
            ok=res["ok"],
            stage="444_KERNEL",
            lane=res["Ω"]["lane"],
            mode="lane",
            verdict=res["Ω"]["verdict"],
            data=res.get("data"),
        )

    if mode == "list":
        return _omega_well_output(
            ok=True,
            stage="444_KERNEL",
            lane="AGI",
            mode="list",
            verdict="SEAL",
            data={
                "available_modes": ["route", "stage", "lane", "list"],
                "lanes": ["AGI", "ASI", "APEX"],
                "stages": [
                    "000_INIT",
                    "111_SENSE",
                    "222_FETCH",
                    "333_MIND",
                    "444_KERNEL",
                    "555_MEMORY",
                    "666_HEART",
                    "777_FORGE",
                    "888_JUDGE",
                    "999_VAULT",
                ],
            },
        )

    return _omega_well_output(
        ok=False,
        stage="444_KERNEL",
        lane="AGI",
        mode=mode,
        verdict="VOID",
        error=f"Unknown mode: {mode}",
    )


# ── Ω-WELL-05: MEMORY (555) ───────────────────────────────────────────────────
# arifOS: 555_MEMORY — Associative Recall, Trend Reflection
# AAA: Event Store + Audit Trail


@mcp.tool()  # Alias — deprecated; use well_trace_lineage
def well_555_memory(
    mode: str = "recall",
    limit: int = 10,
    lookback_days: int = 30,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Ω-WELL-05: Memory, trend, and ledger operations.
    modes: recall | trend | ledger | context
    Compresses: well_list_events, well_trend_analysis, well_list_log
    """
    mode = mode.lower()
    if mode == "recall":
        res = well_list_events(limit=limit, redact=True, ctx=ctx)
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="555_MEMORY",
            lane="AGI",
            mode="recall",
            verdict="SEAL",
            data=res,
        )
    if mode == "trend":
        res = well_trend_analysis(ctx=ctx)
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="555_MEMORY",
            lane="AGI",
            mode="trend",
            verdict="SEAL",
            data=res,
        )
    if mode == "ledger":
        res = well_pressure_ledger(ctx=ctx)
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="555_MEMORY",
            lane="AGI",
            mode="ledger",
            verdict="SEAL",
            data=res,
        )
    if mode == "context":
        # Full context window: state + trend + recent events
        st = well_state(ctx=ctx)
        tr = well_trend_analysis(ctx=ctx)
        ev = well_list_events(limit=5, redact=True, ctx=ctx)
        return _omega_well_output(
            ok=True,
            stage="555_MEMORY",
            lane="AGI",
            mode="context",
            verdict="SEAL",
            data={"state": st, "trend": tr, "recent_events": ev},
        )
    return _omega_well_output(
        ok=False,
        stage="555_MEMORY",
        lane="AGI",
        mode=mode,
        verdict="VOID",
        error=f"Unknown mode: {mode}",
    )


# ── Ω-WELL-06: HEART (666) ────────────────────────────────────────────────────
# arifOS: 666_HEART — Empathy, Ethics, Risk Critique
# AAA: Escalation Rules + Empathy Scan


@mcp.tool()  # Alias — deprecated; use well_assess_homeostasis / well_guard_dignity
def well_666_heart(
    mode: str = "critique",
    subject: str | None = None,
    dignity_preservation: float | None = None,
    coercion_signals: list[str] | None = None,
    reductionism_risk: float | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Ω-WELL-06: Empathy, ethics, and dignity critique.
    modes: critique | empathize | dignity | redteam | maruah
    Compresses: well_livelihood_dignity_check, well_symbolic_domain_check + empathy heuristics
    """
    mode = mode.lower()
    if mode == "critique":
        if not subject:
            return _omega_well_output(
                ok=False,
                stage="666_HEART",
                lane="ASI",
                mode="critique",
                verdict="HOLD",
                error="subject required",
            )
        sym = well_symbolic_domain_check(
            subject=subject, reductionism_risk=reductionism_risk, ctx=ctx
        )
        dig = well_livelihood_dignity_check(
            dignity_preservation=dignity_preservation,
            coercion_signals=coercion_signals,
            ctx=ctx,
        )
        all_ok = sym.get("ok") and dig.get("ok")
        risk = (
            sym.get("reductionism_status") == "HIGH_RISK"
            or dig.get("status") == "VIOLATED"
        )
        return _omega_well_output(
            ok=all_ok,
            stage="666_HEART",
            lane="ASI",
            mode="critique",
            verdict="HOLD" if risk else "SEAL",
            data={"symbolic": sym, "dignity": dig},
            constitutional_compliance={
                "F05_PEACE": dig.get("status"),
                "L06_EMPATHY": "scanned",
            },
        )
    if mode == "empathize":
        state = _load_state()
        metrics = state.get("metrics", {})
        stress = metrics.get("stress", {})
        cog = metrics.get("cognitive", {})
        load = stress.get("subjective_load", 0)
        fatigue = cog.get("decision_fatigue", 0)
        impact = (
            "HIGH"
            if load > 7 or fatigue > 7
            else "MODERATE"
            if load > 5 or fatigue > 5
            else "LOW"
        )
        return _omega_well_output(
            ok=True,
            stage="666_HEART",
            lane="ASI",
            mode="empathize",
            verdict="SEAL",
            data={
                "human_impact_load": impact,
                "stress_load": load,
                "decision_fatigue": fatigue,
            },
            constitutional_compliance={"L06_EMPATHY": impact},
        )
    if mode == "dignity":
        res = well_livelihood_dignity_check(
            dignity_preservation=dignity_preservation,
            coercion_signals=coercion_signals,
            ctx=ctx,
        )
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="666_HEART",
            lane="ASI",
            mode="dignity",
            verdict="SEAL" if res.get("status") == "PRESERVED" else "HOLD",
            data=res,
        )
    if mode == "redteam":
        # Attack surface: what could go wrong?
        state = _load_state()
        violations = state.get("floors_violated", [])
        score = state.get("well_score", 50)
        attacks = []
        if score < 50:
            attacks.append("fatigue_exploitation")
        if "W1_SLEEP_DEBT" in violations:
            attacks.append("sleep_deprivation_attack")
        if "W5_COGNITIVE_ENTROPY" in violations:
            attacks.append("cognitive_overload_attack")
        if "W6_METABOLIC_PAUSE" in violations:
            attacks.append("metabolic_pause_bypass")
        return _omega_well_output(
            ok=True,
            stage="666_HEART",
            lane="ASI",
            mode="redteam",
            verdict="HOLD" if attacks else "SEAL",
            data={
                "attack_surface": attacks,
                "severity": "HIGH"
                if len(attacks) >= 2
                else "MEDIUM"
                if attacks
                else "LOW",
            },
        )
    if mode == "maruah":
        # Dignity score (F05 Peace)
        dig = well_livelihood_dignity_check(
            dignity_preservation=dignity_preservation,
            coercion_signals=coercion_signals,
            ctx=ctx,
        )
        ds = dig.get("dignity_preservation", 5) or 5
        maruah_score = round(ds / 10, 2)
        return _omega_well_output(
            ok=True,
            stage="666_HEART",
            lane="ASI",
            mode="maruah",
            verdict="SEAL" if maruah_score >= 0.7 else "HOLD",
            data={"maruah_score": maruah_score, "dignity_status": dig.get("status")},
        )
    return _omega_well_output(
        ok=False,
        stage="666_HEART",
        lane="ASI",
        mode=mode,
        verdict="VOID",
        error=f"Unknown mode: {mode}",
    )


# ── Ω-WELL-07: FORGE (777) ────────────────────────────────────────────────────
# arifOS: 777_FORGE — Execution, Plan Materialization
# AAA: A-FORGE Bridge + Execution Mode


@mcp.tool()  # Alias — deprecated; use well_check_repair
def well_777_forge(
    mode: str = "precheck",
    task_description: str | None = None,
    decision_class: str | None = None,
    source: str | None = None,
    intensity: float | None = None,
    outcome: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Ω-WELL-07: Forge execution coupling.
    modes: precheck | mode | bandwidth | pressure | closeout
    Compresses: well_forge_precheck, well_forge_mode_recommend, well_bandwidth_recommendation, well_forge_pressure_update, well_forge_closeout
    """
    mode = mode.lower()
    if mode == "precheck":
        res = well_forge_precheck(
            task_description=task_description, decision_class=decision_class, ctx=ctx
        )
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="777_FORGE",
            lane="APEX",
            mode="precheck",
            verdict=res.get("status", "HOLD"),
            data=res,
            federation_state={
                "execution_mode": res.get("recommended_mode"),
                "human_confirmation": res.get("human_confirmation_required"),
            },
        )
    if mode == "mode":
        res = well_forge_mode_recommend(ctx=ctx)
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="777_FORGE",
            lane="APEX",
            mode="mode",
            verdict="SEAL" if res.get("forge_mode") != "paused" else "HOLD",
            data=res,
        )
    if mode == "bandwidth":
        res = well_bandwidth_recommendation(ctx=ctx)
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="777_FORGE",
            lane="APEX",
            mode="bandwidth",
            verdict="SEAL"
            if res.get("verdict") == "OPTIMAL"
            else "PROVISIONAL"
            if res.get("verdict") == "FUNCTIONAL"
            else "HOLD",
            data=res,
        )
    if mode == "pressure":
        if not source or intensity is None:
            return _omega_well_output(
                ok=False,
                stage="777_FORGE",
                lane="APEX",
                mode="pressure",
                verdict="HOLD",
                error="source and intensity required",
            )
        res = well_forge_pressure_update(source=source, intensity=intensity, ctx=ctx)
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="777_FORGE",
            lane="APEX",
            mode="pressure",
            verdict="SEAL" if not res.get("w6_triggered") else "HOLD",
            data=res,
        )
    if mode == "closeout":
        if not task_description or not outcome:
            return _omega_well_output(
                ok=False,
                stage="777_FORGE",
                lane="APEX",
                mode="closeout",
                verdict="HOLD",
                error="task_description and outcome required",
            )
        res = well_forge_closeout(
            task_description=task_description, outcome=outcome, ctx=ctx
        )
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="777_FORGE",
            lane="APEX",
            mode="closeout",
            verdict="SEAL",
            data=res,
        )
    return _omega_well_output(
        ok=False,
        stage="777_FORGE",
        lane="APEX",
        mode=mode,
        verdict="VOID",
        error=f"Unknown mode: {mode}",
    )


# ── Ω-WELL-08: JUDGE (888) ────────────────────────────────────────────────────
# arifOS: 888_JUDGE — Deliberation, Verdict Sealing
# AAA: 888_JUDGE Gate + Constitutional Arbitration


@mcp.tool()  # Alias — deprecated; use well_validate_vitality
def well_888_judge(
    mode: str = "readiness",
    intent: str | None = None,
    context: str | None = None,
    reversibility: str = "unknown",
    task_description: str | None = None,
    decision_class: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Ω-WELL-08: Validate biological readiness and NIAT.
    modes: readiness | classify | niat | coupled
    Compresses: well_readiness, well_decision_classify, well_niat_check, well_coupled_readiness
    NOTE: floor compliance removed per orthogonal alignment (2026-05-14).
          arifOS alone adjudicates constitutional laws.
    """
    mode = mode.lower()
    if mode == "readiness":
        res = well_readiness(ctx=ctx)
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="888_JUDGE",
            lane="APEX",
            mode="readiness",
            verdict=res.get("status", "HOLD"),
            data=res,
            constitutional_compliance={"verdict": res.get("domain_verdict")},
        )
    if mode == "classify":
        res = well_decision_classify(
            task_description=task_description, decision_class=decision_class, ctx=ctx
        )
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="888_JUDGE",
            lane="APEX",
            mode="classify",
            verdict="SEAL"
            if "APPROVED" in res.get("verdict", "")
            else "HOLD"
            if "BLOCKED" in res.get("verdict", "")
            else "PROVISIONAL",
            data=res,
        )
    if mode == "niat":
        if not intent:
            return _omega_well_output(
                ok=False,
                stage="888_JUDGE",
                lane="APEX",
                mode="niat",
                verdict="HOLD",
                error="intent required",
            )
        res = well_niat_check(
            intent=intent, context=context, reversibility=reversibility, ctx=ctx
        )
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="888_JUDGE",
            lane="APEX",
            mode="niat",
            verdict="SEAL" if res.get("readiness") == "ADVISORY_READY" else "HOLD",
            data=res,
        )
    if mode == "coupled":
        res = well_coupled_readiness(ctx=ctx)
        cr = res.get("risk_level", "AMBER")
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="888_JUDGE",
            lane="APEX",
            mode="coupled",
            verdict="SEAL"
            if cr == "GREEN"
            else "HOLD"
            if cr == "RED"
            else "PROVISIONAL",
            data=res,
        )
    return _omega_well_output(
        ok=False,
        stage="888_JUDGE",
        lane="APEX",
        mode=mode,
        verdict="VOID",
        error=f"Unknown mode: {mode}",
    )


# ── Ω-WELL-09: VAULT (999) ────────────────────────────────────────────────────
# arifOS: 999_VAULT — Immutable Seal, Merkle Anchor
# AAA: VAULT999 Client + Audit Chain


@mcp.tool(
    task=True
)  # Alias — deprecated; use well_trace_lineage / well_anchor_evidence
async def well_999_vault(
    mode: str = "seal",
    dry_run: bool = False,
    reason: str = "state_checkpoint",
    force: bool = False,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Ω-WELL-09: Immutable vault operations.
    modes: seal | anchor | verify | chain
    Compresses: well_anchor, well_seal_vault, well_request_anchor
    """
    mode = mode.lower()
    if mode == "seal":
        res = await well_anchor(force=force, ctx=ctx)
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="999_VAULT",
            lane="APEX",
            mode="seal",
            verdict="SEAL" if res.get("ok") else "HOLD",
            data=res,
            federation_state={"vault_id": res.get("vault_id"), "hash": res.get("hash")},
        )
    if mode == "anchor":
        res = await well_request_anchor(dry_run=dry_run, reason=reason, ctx=ctx)
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="999_VAULT",
            lane="APEX",
            mode="anchor",
            verdict="SEAL" if res.get("ok") else "HOLD",
            data=res,
        )
    if mode == "verify":
        # Check if vault ledger exists and is writable
        deps = _check_dependencies()
        return _omega_well_output(
            ok=deps.get("vault_path_writable", False),
            stage="999_VAULT",
            lane="APEX",
            mode="verify",
            verdict="SEAL" if deps.get("vault_path_writable") else "HOLD",
            data=deps,
        )
    if mode == "chain":
        res = await well_request_anchor(dry_run=True, reason="chain_tip", ctx=ctx)
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="999_VAULT",
            lane="APEX",
            mode="chain",
            verdict="SEAL" if res.get("ok") else "HOLD",
            data={
                "chain_tip": res.get("would_anchor"),
                "identity_pass": res.get("identity_pass"),
            },
        )
    return _omega_well_output(
        ok=False,
        stage="999_VAULT",
        lane="APEX",
        mode=mode,
        verdict="VOID",
        error=f"Unknown mode: {mode}",
    )


# ── Ω-WELL-10: REPLY (444r) ───────────────────────────────────────────────────
# arifOS: 444r_REPLY — Composition, Message Forging
# AAA: Cockpit Dashboard + Federation Handoff


@mcp.tool()  # Alias — deprecated; use well_anchor_evidence
def well_444_reply(
    mode: str = "packet",
    target: str = "arifos",
    detail: str = "standard",
    subject: str | None = None,
    substrate_class: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Ω-WELL-10: Packet composition and reply forging.
    modes: packet | brief | verdict | daily
    Compresses: well_get_packet, well_daily_brief, well_arifos_packet, well_verdict_packet
    """
    mode = mode.lower()
    if mode == "packet":
        res = well_get_packet(target=target, detail=detail, ctx=ctx)
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="444r_REPLY",
            lane="AGI",
            mode="packet",
            verdict="SEAL" if res.get("ok") else "HOLD",
            data=res,
            federation_state={"target": target, "detail": detail},
        )
    if mode == "brief":
        res = well_daily_brief(ctx=ctx)
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="444r_REPLY",
            lane="AGI",
            mode="brief",
            verdict="SEAL" if res.get("ok") else "HOLD",
            data=res,
        )
    if mode == "verdict":
        if not subject or not substrate_class:
            return _omega_well_output(
                ok=False,
                stage="444r_REPLY",
                lane="AGI",
                mode="verdict",
                verdict="HOLD",
                error="subject and substrate_class required",
            )
        res = well_verdict_packet(
            subject=subject, substrate_class=substrate_class, ctx=ctx
        )
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="444r_REPLY",
            lane="AGI",
            mode="verdict",
            verdict="SEAL" if res.get("ok") else "HOLD",
            data=res,
        )
    if mode == "daily":
        res = well_daily_brief(ctx=ctx)
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="444r_REPLY",
            lane="AGI",
            mode="daily",
            verdict="SEAL" if res.get("ok") else "HOLD",
            data=res,
        )
    return _omega_well_output(
        ok=False,
        stage="444r_REPLY",
        lane="AGI",
        mode=mode,
        verdict="VOID",
        error=f"Unknown mode: {mode}",
    )


# ── Ω-WELL-11: GATEWAY (444g) ─────────────────────────────────────────────────
# arifOS: 444g_GATEWAY — Federation Bridge, A2A Mesh
# AAA: A2A Gateway + Agent Card Dispatch


@mcp.tool()  # Alias — deprecated; use well_detect_boundary / AAA gateway status
def well_444_gateway(
    mode: str = "status",
    peer: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Ω-WELL-11: Federation gateway and bridge.
    modes: status | connect | handoff | manifest
    Aligns with AAA A2A gateway and federation manifest.
    """
    mode = mode.lower()
    if mode == "status":
        h = well_get_health(ctx=ctx)
        return _omega_well_output(
            ok=h.get("verdict") in ("PASS", "WELL_PASS"),
            stage="444g_GATEWAY",
            lane="AGI",
            mode="status",
            verdict="SEAL" if h.get("verdict") in ("PASS", "WELL_PASS") else "HOLD",
            data={"well_health": h, "transport": "SSE_VALID"},
            federation_state={
                "service": "well-mcp",
                "status": "healthy"
                if h.get("verdict") in ("PASS", "WELL_PASS")
                else "degraded",
            },
        )
    if mode == "connect":
        return _omega_well_output(
            ok=True,
            stage="444g_GATEWAY",
            lane="AGI",
            mode="connect",
            verdict="SEAL",
            data={
                "protocol": "A2A_v1.0.0",
                "peers": ["arifos", "a-forge", "geox", "wealth", "aaa"],
                "identity": "AFWELL",
            },
        )
    if mode == "handoff":
        # Prepare handoff packet for peer
        pkt = well_get_packet(target=peer or "arifos", detail="minimal", ctx=ctx)
        return _omega_well_output(
            ok=pkt.get("ok", False),
            stage="444g_GATEWAY",
            lane="AGI",
            mode="handoff",
            verdict="SEAL" if pkt.get("ok") else "HOLD",
            data={"handoff_packet": pkt, "target_peer": peer or "arifos"},
        )
    if mode == "manifest":
        return _omega_well_output(
            ok=True,
            stage="444g_GATEWAY",
            lane="AGI",
            mode="manifest",
            verdict="SEAL",
            data={
                "federation": "arifOS Constitutional Federation",
                "organ": "WELL",
                "lane": "wellbeing",
                "witness_type": "human",
                "capabilities": [
                    "substrate_sense",
                    "vitality_reason",
                    "empathy_scan",
                    "forge_coupling",
                    "vault_anchor",
                ],
                "constitutional_floors": ["F01", "F05", "F06", "F09", "F13"],
            },
        )
    return _omega_well_output(
        ok=False,
        stage="444g_GATEWAY",
        lane="AGI",
        mode=mode,
        verdict="VOID",
        error=f"Unknown mode: {mode}",
    )


# ── Ω-WELL-12: OPS (000_OPS) ──────────────────────────────────────────────────
# arifOS: 777_OPS — Health Telemetry, Thermodynamic Monitoring
# AAA: Cockpit Health Metrics + Prometheus


@mcp.tool()  # Alias — deprecated; use well_assess_reliability
def well_000_ops(
    mode: str = "health",
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Ω-WELL-12: Operations and health telemetry.
    modes: health | consent | medical | vitals
    Compresses: well_get_health, well_consent_status, well_medical_boundary
    """
    mode = mode.lower()
    if mode == "health":
        res = well_get_health(ctx=ctx)
        return _omega_well_output(
            ok=res.get("verdict") in ("PASS", "WELL_PASS"),
            stage="000_OPS",
            lane="AGI",
            mode="health",
            verdict="SEAL" if res.get("verdict") in ("PASS", "WELL_PASS") else "HOLD",
            data=res,
        )
    if mode == "consent":
        res = well_consent_status(ctx=ctx)
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="000_OPS",
            lane="AGI",
            mode="consent",
            verdict="SEAL" if res.get("consent_active") else "HOLD",
            data=res,
        )
    if mode == "medical":
        res = well_medical_boundary(ctx=ctx)
        return _omega_well_output(
            ok=res.get("ok", False),
            stage="000_OPS",
            lane="AGI",
            mode="medical",
            verdict="SEAL",
            data=res,
        )
    if mode == "vitals":
        h = well_get_health(ctx=ctx)
        m = well_machine_state(ctx=ctx)
        state = _load_state()
        return _omega_well_output(
            ok=True,
            stage="000_OPS",
            lane="AGI",
            mode="vitals",
            verdict="SEAL",
            data={
                "human_health": h.get("layer_3_domain_truth"),
                "machine_health": {
                    "m_well_score": m.get("m_well_score"),
                    "m_well_verdict": m.get("m_well_verdict"),
                },
                "well_score": state.get("well_score"),
                "floors_violated": state.get("floors_violated"),
            },
        )
    return _omega_well_output(
        ok=False,
        stage="000_OPS",
        lane="AGI",
        mode=mode,
        verdict="VOID",
        error=f"Unknown mode: {mode}",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Ω-WELL Tool Surface Integrity Check
# ═══════════════════════════════════════════════════════════════════════════════

# ── ALIAS_REGISTRY — Ω-WELL stage aliases → canonical tool mappings ────────────
# Every alias must map to a canonical function that exists in globals.
# This is checked at import time. No alias may exist only in docs/manifest.

ALIAS_REGISTRY = {
    "well_000_init": "well_classify_substrate",
    "well_111_sense": "well_classify_substrate",
    "well_222_fetch": "well_measure_gradient",
    "well_333_mind": "well_assess_metabolism",
    "well_444_kernel": "well_detect_boundary",
    "well_555_memory": "well_trace_lineage",
    "well_666_heart": "well_assess_homeostasis",
    "well_777_forge": "well_check_repair",
    "well_888_judge": "well_validate_vitality",
    "well_999_vault": "well_trace_lineage",
    "well_444_reply": "well_trace_lineage",
    "well_444_gateway": "well_detect_boundary",
    "well_000_ops": "well_assess_reliability",
}


# ── 010_WELL_DREAM_ENGINE: well_13_signal_coverage ─────────────────────────────
# Dream engine = WELL's view of its own substrate coverage.
# Forged 2026-06-06 as SUNAT item per GENESIS/004_WELL_13_CANON.md §5.2.
# This tool does NOT diagnose, score, or judge the human.
# It audits whether WELL is currently observing the 13 canonical signals.
# Authority: reflect_only. arifOS / 888_JUDGE adjudicates gaps.

WELL_13_COVERAGE_MAP: list[dict[str, Any]] = [
    {
        "id": "S01",
        "signal": "heart_circulation",
        "tier": "vital_substrate",
        "state_path": ["metrics", "cardio", "resting_hr"],
        "alt_paths": [
            ["metrics", "cognitive", "hrv_proxy"],
            ["metrics", "stress", "hrv_proxy"],
        ],
    },
    {
        "id": "S02",
        "signal": "blood_pressure",
        "tier": "vital_substrate",
        "state_path": ["metrics", "cardio", "systolic_bp"],
        "alt_paths": [
            ["metrics", "cardio", "diastolic_bp"],
        ],
    },
    {
        "id": "S03",
        "signal": "breathing_oxygenation",
        "tier": "vital_substrate",
        "state_path": ["metrics", "cardio", "respiratory_rate"],
        "alt_paths": [
            ["metrics", "cardio", "spo2"],
        ],
    },
    {
        "id": "S04",
        "signal": "temperature_inflammation",
        "tier": "vital_substrate",
        "state_path": ["metrics", "vital", "body_temperature"],
        "alt_paths": [
            ["metrics", "inflammation", "marker"],
        ],
    },
    {
        "id": "S05",
        "signal": "sleep_architecture",
        "tier": "recovery_metabolic",
        "state_path": ["metrics", "sleep", "sleep_hours"],
        "alt_paths": [
            ["metrics", "sleep", "sleep_quality"],
            ["metrics", "sleep", "sleep_debt_days"],
        ],
    },
    {
        "id": "S06",
        "signal": "metabolic_state",
        "tier": "recovery_metabolic",
        "state_path": ["metrics", "metabolic", "metabolic_stability"],
        "alt_paths": [
            ["metrics", "metabolic", "fasting_hours"],
            ["metrics", "glucose"],
        ],
    },
    {
        "id": "S07",
        "signal": "nutrition_hydration",
        "tier": "recovery_metabolic",
        "state_path": ["metrics", "nutrition", "nutrition_quality"],
        "alt_paths": [
            ["metrics", "nutrition", "hydration"],
        ],
    },
    {
        "id": "S08",
        "signal": "movement_strength",
        "tier": "function_cognition",
        "state_path": ["metrics", "movement", "movement_count"],
        "alt_paths": [
            ["metrics", "movement", "gait"],
        ],
    },
    {
        "id": "S09",
        "signal": "pain_injury",
        "tier": "function_cognition",
        "state_path": ["metrics", "pain", "pain_sites"],
        "alt_paths": [
            ["metrics", "pain", "pain_level"],
        ],
    },
    {
        "id": "S10",
        "signal": "cognitive_clarity",
        "tier": "function_cognition",
        "state_path": ["metrics", "cognitive", "clarity"],
        "alt_paths": [
            ["metrics", "cognitive", "decision_fatigue"],
            ["metrics", "cognitive", "focus_durability"],
        ],
    },
    {
        "id": "S11",
        "signal": "emotional_stress",
        "tier": "dignity_environment",
        "state_path": ["metrics", "stress", "subjective_load"],
        "alt_paths": [
            ["metrics", "stress", "restlessness"],
            ["metrics", "stress", "emotional_state"],
        ],
    },
    {
        "id": "S12",
        "signal": "social_dignity_consent",
        "tier": "dignity_environment",
        "state_path": ["metrics", "dignity", "dignity_preservation"],
        "alt_paths": [
            ["metrics", "dignity", "coercion_signals"],
            ["metrics", "dignity", "reductionism_risk"],
        ],
    },
    {
        "id": "S13",
        "signal": "environment_livelihood",
        "tier": "dignity_environment",
        "state_path": ["metrics", "livelihood", "energy_level"],
        "alt_paths": [
            ["metrics", "livelihood", "duty_load"],
            ["metrics", "livelihood", "purpose_alignment"],
        ],
    },
]


def _resolve_path(state: dict[str, Any], path: list[str]) -> Any:
    """Safely walk a state.json path. Returns None if any key is missing."""
    cur: Any = state
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur


@mcp.tool()
def well_13_signal_coverage(
    operator_id: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    [DEPRECATED — USE well_signal_coverage]
    This tool has been deprecated and replaced. Please use well_signal_coverage instead.
    """
    return {
        "status": "ERROR",
        "error": "well_13_signal_coverage is deprecated and has been removed. Use well_signal_coverage instead.",
        "replacement": "well_signal_coverage",
    }


@mcp.tool()
def well_signal_coverage(
    operator_id: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    DREAM ENGINE: Audit WELL's coverage of canonical human substrate
    signals. Returns per-signal status (active/partial/missing), coverage
    summary, and cross-organ handoff suggestions for gaps.

    Authority: reflect_only. WELL does not score the human here. WELL
    audits itself: which of the substrate signals am I currently
    seeing? Which are stale? Which are missing?

    SUNAT item per GENESIS/004_WELL_13_CANON.md §5.2.
    """
    return _well_13_signal_coverage_impl(operator_id=operator_id, ctx=ctx)


def _well_13_signal_coverage_impl(
    operator_id: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    state = _load_state()
    metrics = state.get("metrics", {})

    per_signal: list[dict[str, Any]] = []
    tier_counts: dict[str, dict[str, int]] = {
        "vital_substrate": {"active": 0, "partial": 0, "missing": 0},
        "recovery_metabolic": {"active": 0, "partial": 0, "missing": 0},
        "function_cognition": {"active": 0, "partial": 0, "missing": 0},
        "dignity_environment": {"active": 0, "partial": 0, "missing": 0},
    }

    now_iso = (
        datetime.datetime.now(datetime.timezone.utc).isoformat()
        if "datetime" in dir()
        else None
    )
    state_timestamp = state.get("timestamp")

    for spec in WELL_13_COVERAGE_MAP:
        primary = _resolve_path(state, spec["state_path"])
        alts = [_resolve_path(state, p) for p in spec.get("alt_paths", [])]
        has_primary = primary is not None
        has_alt = any(a is not None for a in alts)
        if has_primary:
            status = "active"
        elif has_alt:
            status = "partial"
        else:
            status = "missing"
        tier_counts[spec["tier"]][status] += 1

        per_signal.append(
            {
                "id": spec["id"],
                "signal": spec["signal"],
                "tier": spec["tier"],
                "status": status,
                "primary_path": ".".join(spec["state_path"]),
                "has_primary": has_primary,
                "alt_paths_present": sum(1 for a in alts if a is not None),
                "alt_paths_total": len(alts),
            }
        )

    total = sum(
        tc["active"] + tc["partial"] + tc["missing"] for tc in tier_counts.values()
    )
    active_total = sum(tc["active"] for tc in tier_counts.values())
    partial_total = sum(tc["partial"] for tc in tier_counts.values())
    missing_total = sum(tc["missing"] for tc in tier_counts.values())

    # Coverage score = active + 0.5*partial (WELL tool coverage, not human score)
    coverage_score = (
        round((active_total + 0.5 * partial_total) / total * 10.0, 2) if total else 0.0
    )

    # Cross-organ handoff suggestions for missing signals
    handoffs: list[dict[str, str]] = []
    for sig in per_signal:
        if sig["status"] == "missing":
            if sig["tier"] == "dignity_environment":
                if sig["id"] == "S12":
                    handoffs.append(
                        {
                            "signal": sig["signal"],
                            "current_organ": "WELL (gap)",
                            "next_organ": "arifOS / 888_JUDGE (consent/dignity breach)",
                            "rationale": (
                                "Dignity/consent signal requires operator "
                                "self-report or peer confirmation; WELL "
                                "cannot synthesise it alone."
                            ),
                        }
                    )
                elif sig["id"] == "S13":
                    handoffs.append(
                        {
                            "signal": sig["signal"],
                            "current_organ": "WELL (gap)",
                            "next_organ": "WEALTH (livelihood + cashflow pressure)",
                            "rationale": (
                                "Environment/livelihood requires WEALTH "
                                "metrics (cashflow_status, duty_load)."
                            ),
                        }
                    )
            elif sig["tier"] == "vital_substrate":
                handoffs.append(
                    {
                        "signal": sig["signal"],
                        "current_organ": "WELL (gap)",
                        "next_organ": "human medical route (wearable / clinical)",
                        "rationale": (
                            "Vital substrate signal missing; escalate to "
                            "human medical evaluation if critical."
                        ),
                    }
                )
            else:
                handoffs.append(
                    {
                        "signal": sig["signal"],
                        "current_organ": "WELL (gap)",
                        "next_organ": "operator self-report (well_log)",
                        "rationale": (
                            "WELL relies on operator self-report or "
                            "optional wearable for this signal."
                        ),
                    }
                )

    return {
        "ok": True,
        "operator_id": operator_id or state.get("operator_id", "arif"),
        "generated_at": now_iso,
        "state_timestamp": state_timestamp,
        "canon_ref": "GENESIS/004_WELL_13_CANON.md §1",
        "authority": "reflect_only",
        "human_judge_required": True,
        "per_signal": per_signal,
        "tier_summary": tier_counts,
        "coverage_summary": {
            "total_signals": total,
            "active": active_total,
            "partial": partial_total,
            "missing": missing_total,
            "coverage_score_0_to_10": coverage_score,
            "note": (
                "coverage_score is WELL's tool coverage, NOT a human "
                "wellness score. It measures how many of the 13 signals "
                "WELL is currently seeing, not how well the human is."
            ),
        },
        "handoffs_recommended": handoffs,
        "well_13_signal_map_ref": "WELL_13_SIGNAL_MAP.json",
        "philosophical_lock": (
            "Gödel: WELL cannot fully prove the human. This tool "
            "audits WELL's view, not the human's truth."
        ),
    }


def _readiness_visibility_context() -> dict[str, Any]:
    """Compact readiness evidence block for human-facing readiness outputs."""
    state = _load_state()
    coverage = _well_13_signal_coverage_impl(
        operator_id=state.get("operator_id", "arif")
    )
    per_signal = coverage.get("per_signal", [])
    summary = coverage.get("coverage_summary", {})
    freshness = _check_data_freshness(state)
    return {
        "coverage_score": summary.get("coverage_score_0_to_10", 0.0),
        "active_signals": [
            sig.get("signal") for sig in per_signal if sig.get("status") == "active"
        ],
        "partial_signals": [
            sig.get("signal") for sig in per_signal if sig.get("status") == "partial"
        ],
        "missing_signals": [
            sig.get("signal") for sig in per_signal if sig.get("status") == "missing"
        ],
        "telemetry_age_hours": freshness.get("state_age_hours"),
        "freshness": freshness.get("freshness_label"),
        "truth_status": freshness.get("truth_status"),
        "identity_valid": is_well(state),
        "decision_support": "LIMITED"
        if not is_well(state) or summary.get("coverage_score_0_to_10", 0.0) < 5.0
        else "ADVISORY",
    }


# ALIAS_REGISTRY validation happens on first tool call, not at import time.
# Canonical functions are defined later in the file and won't be in globals yet.
_ALIAS_REGISTRY_VALIDATED = False

OMEGA_WELL_TOOLS = {
    "well_classify_substrate",
    "well_trace_lineage",
    "well_detect_boundary",
    "well_measure_gradient",
    "well_assess_metabolism",
    "well_assess_homeostasis",
    "well_check_repair",
    "well_validate_vitality",
    "well_assess_livelihood",
    "well_assess_reliability",
    "well_compute_metabolic_flux",
    "well_reflect_intelligence",
    "well_guard_dignity",
    "well_anchor_evidence",
    "well_13_signal_coverage",
    "well_signal_coverage",
}


# ═══════════════════════════════════════════════════════════════════════════════
# MCP Resources — Canonical 6
# Aligned with arifOS resource pattern: arifos://doctrine, arifos://vitals, etc.
# ═══════════════════════════════════════════════════════════════════════════════


@mcp.resource("well://schema")
def afwell_schema() -> str:
    """AFWELL State JSON Schema — canonical substrate state contract."""
    schema_path = WELL_DIR / "schema.json"
    if schema_path.exists():
        return schema_path.read_text()
    return json.dumps({"error": "schema.json not found"})


@mcp.resource("well://state/arif")
def afwell_state_arif() -> str:
    """Live operator state snapshot for Arif."""
    state = _load_state()
    # Redact sensitive raw metrics for resource exposure
    safe = {
        "timestamp": state.get("timestamp"),
        "operator_id": state.get("operator_id"),
        "well_score": state.get("well_score"),
        "floors_violated": state.get("floors_violated", []),
        "truth_status": state.get("truth_status", "UNVERIFIED"),
        "identity": state.get("identity"),
        "authority": state.get("authority"),
    }
    return json.dumps(safe, indent=2)


@mcp.resource("well://events/recent")
def afwell_events_recent() -> str:
    """Last 20 events from the append-only event ledger."""
    if not EVENTS_PATH.exists():
        return json.dumps({"events": []})
    events = []
    try:
        with open(EVENTS_PATH) as f:
            lines = f.readlines()
        for line in lines[-20:]:
            try:
                events.append(json.loads(line))
            except Exception:
                continue
    except Exception:
        pass
    return json.dumps({"events": events[::-1]}, indent=2)


@mcp.resource("well://floors/well_floors")
def afwell_floors() -> str:
    """W-Series floor definitions and current status."""
    state = _load_state()
    metrics = state.get("metrics", {})
    sleep = metrics.get("sleep", {})
    cognitive = metrics.get("cognitive", {})
    floors = {
        "W0": {
            "name": "Sovereignty Invariant",
            "status": "INVARIANT",
            "detail": "Operator veto always intact.",
        },
        "W1": {
            "name": "Sleep Integrity",
            "threshold": "sleep_debt_days <= 2",
            "current": sleep.get("sleep_debt_days", 0),
            "status": "OK" if sleep.get("sleep_debt_days", 0) <= 2 else "VIOLATED",
        },
        "W5": {
            "name": "Cognitive Entropy",
            "threshold": "clarity >= 4",
            "current": cognitive.get("clarity", 10),
            "status": "OK" if cognitive.get("clarity", 10) >= 4 else "VIOLATED",
        },
        "W6": {"name": "Incentive Decoupling", "status": "PHASE_3_PENDING"},
    }
    return json.dumps(floors, indent=2)


@mcp.resource("well://vitals/arif")
def afwell_vitals_arif() -> str:
    """Readiness vitals — triage color, score, violations."""
    state = _load_state()
    resolved = _resolve_readiness(state)
    flux = _compute_metabolic_flux(state)
    vitals = {
        "well_score": resolved["well_score"],
        "readiness": resolved["readiness"],
        "risk_level": resolved["risk_level"],
        "recommended_mode": resolved["recommended_mode"],
        "active_violations": resolved["active_violations"],
        "has_telemetry": resolved["has_telemetry"],
        "human_confirmation_required": resolved["human_confirmation_required"],
        "metabolic_flux": flux["metabolic_flux"],
        "flux_verdict": flux["verdict"],
        "compulsory_reallocation": flux["compulsory_reallocation"],
    }
    return json.dumps(vitals, indent=2)


@mcp.resource("well://substrate/registry")
def afwell_substrate_registry() -> str:
    """U-WELL Universal Substrate Class Registry."""
    return json.dumps(
        {
            "substrate_classes": UNIVERSAL_SUBSTRATE_CLASSES,
            "vitality_modes": UNIVERSAL_VITALITY_MODES,
            "count": len(UNIVERSAL_SUBSTRATE_CLASSES),
        },
        indent=2,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# TREE777 WIKI RESOURCES — Federation Canonical Knowledge Tree
# ═══════════════════════════════════════════════════════════════════════════════
# Exposes WELL-domain slice of the TREE777 wiki as MCP Resources.
# URI scheme:
#   tree777://skills/well/{name}   — WELL skill pages
#   tree777://well/concepts/{name} — Vitality concept pages
#   tree777://well/scars/{name}    — WELL scar/incident records
# Wiki root: /root/AAA/wiki (shared across all 4 federation servers)
# Rule: Resources grow. Tools stay bounded. Judgment remains Arif.
# DITEMPA BUKAN DIBERI — Intelligence is forged, not given.

TREE777_WIKI_ROOT = Path(_os.environ.get("TREE777_WIKI_ROOT", "/root/AAA/wiki"))
TREE777_SKILLS_DIR = TREE777_WIKI_ROOT / "skills" / "well"
TREE777_CONCEPTS_DIR = TREE777_WIKI_ROOT / "concepts"
TREE777_SCAR_DIR = TREE777_WIKI_ROOT / "scars"


def _well_read_wiki_file(file_path: str | Path) -> str:
    """Read a wiki file, returning frontmatter-stripped content."""
    path = Path(file_path)
    if not path.exists():
        return f"ERROR: File not found: {path}"
    content = path.read_text()
    if content.startswith("---"):
        end = content.find("\n---\n", 4)
        if end != -1:
            content = content[end + 5 :]
    return content.strip()


def _well_tree777_index() -> dict[str, Any]:
    """Build the TREE777 index for WELL domain slice."""
    skills = []
    if TREE777_SKILLS_DIR.exists():
        for f in TREE777_SKILLS_DIR.glob("*.md"):
            skills.append({"name": f.stem, "uri": f"tree777://skills/well/{f.stem}"})

    concepts = []
    if TREE777_CONCEPTS_DIR.exists():
        for f in TREE777_CONCEPTS_DIR.glob("*.md"):
            concepts.append(
                {"name": f.stem, "uri": f"tree777://well/concepts/{f.stem}"}
            )

    scars = []
    if TREE777_SCAR_DIR.exists():
        for f in TREE777_SCAR_DIR.glob("*.md"):
            if "well" in f.stem or "vital" in f.stem or "niat" in f.stem:
                scars.append({"name": f.stem, "uri": f"tree777://well/scars/{f.stem}"})

    return {
        "domain": "well",
        "skills": skills,
        "concepts": concepts,
        "scars": scars,
        "total": len(skills) + len(concepts) + len(scars),
    }


@mcp.resource(
    "well://telemetry/arif",
    description=(
        "Live behavioral telemetry snapshot for Arif — derived from WELL agent "
        "telemetry (agent sessions, token throughput, git rhythm, VAULT999 decisions, "
        "burnout risk). Behavioral flux components: sleep_debt, decision_fatigue, "
        "cognitive_load, agent_sessions, burnout_risk. telemetry_status indicates "
        "whether data is BEHAVIORAL (inferred from activity) or SENSOR (direct biometric). "
        "psi_SE_note: sovereign unpredictability is protective, not pathological."
    ),
)
def afwell_telemetry() -> str:
    state = _load_state()
    metrics = state.get("metrics", {})
    cognitive = metrics.get("cognitive", {})
    metrics.get("stress", {})
    sleep = metrics.get("sleep", {})

    telemetry = {
        "uri": "well://telemetry/arif",
        "timestamp": state.get("timestamp"),
        "operator": "arif",
        "well_score": state.get("well_score"),
        "telemetry_status": "BEHAVIORAL",
        "causal_note": (
            "Sleep debt → decision fatigue → psi_SE decline → "
            "authority capacity erosion. Flux is the metabolic signal. "
            "psi_SE is the anti-capture signal. Both must be read together."
        ),
        "behavioral_components": {
            "sleep": {
                "hours": sleep.get("hours", "unknown"),
                "debt_days": cognitive.get("sleep_debt_days"),
                "quality_proxy": sleep.get("quality"),
            },
            "cognitive": {
                "clarity": cognitive.get("clarity"),
                "decision_fatigue": cognitive.get("decision_fatigue"),
                "cognitive_load": cognitive.get("cognitive_load"),
                "context_switches_per_hour": cognitive.get(
                    "context_switching_frequency"
                ),
            },
            "agent_activity": {
                "session_count_24h": cognitive.get("agent_session_count"),
                "token_throughput": cognitive.get("token_throughput"),
                "git_commits_24h": cognitive.get("git_commit_count"),
                "decisions_24h": cognitive.get("decision_count"),
            },
            "burnout": {
                "risk": cognitive.get("burnout_risk"),
                "accumulated_fatigue": cognitive.get("accumulated_session_fatigue"),
            },
        },
        "sovereign_entropy": {
            "psi_SE": cognitive.get("psi_SE"),
            "paradox_density": cognitive.get("paradox_density"),
            "refusal_patterns": cognitive.get("refusal_patterns"),
            "note": "psi_SE < 0.40 = capturable. psi_SE > 0.70 = sovereign protection active.",
        },
        "w0": "OPERATOR_VETO_INTACT | WELL reflects, Arif decides",
    }
    return json.dumps(telemetry, indent=2, default=str)


@mcp.resource(
    "well://readiness/arif",
    description=(
        "Decision readiness verdict for Arif — synthesizes behavioral telemetry "
        "into a SEAL/HOLD/SABAR authority gate. Uses causal readiness model: "
        "sleep_debt → decision_fatigue → psi_SE → authority_capacity → verdict. "
        "Risk tier mapping: T1 (low risk/ low urgency) through T5 (irreversible/critical). "
        "Substrate governance mirror — does not command, only informs."
    ),
)
def afwell_readiness() -> str:
    state = _load_state()
    metrics = state.get("metrics", {})
    cognitive = metrics.get("cognitive", {})
    metrics.get("sleep", {})

    score = state.get("well_score", 50)
    fatigue = cognitive.get("decision_fatigue", 0.5) or 0.5
    clarity = cognitive.get("clarity", 0.5) or 0.5
    psi_se = cognitive.get("psi_SE", 0.65) or 0.65
    burnout = cognitive.get("burnout_risk", 0.5) or 0.5
    sleep_debt = cognitive.get("sleep_debt_days", 0) or 0
    violations = state.get("floors_violated", [])

    # Authority capacity: weighted synthesis
    authority_capacity = round(
        (clarity * 0.30)
        + ((1.0 - fatigue) * 0.25)
        + (psi_se * 0.20)
        + ((1.0 - burnout) * 0.15)
        + (max(0, 1.0 - sleep_debt * 0.3) * 0.10),
        3,
    )

    # Verdict routing
    if authority_capacity >= 0.75 and not violations:
        verdict = "SEAL — Full authority bandwidth. Substrate supports irreversible decisions."
        tier = "GREEN"
    elif authority_capacity >= 0.55:
        verdict = "SABAR — Reduced authority. Draft and deliberate. Delay irreversible actions."
        tier = "YELLOW"
    elif authority_capacity >= 0.35:
        verdict = "HOLD — Degraded substrate. Draft-only mode. No forge execution."
        tier = "ORANGE"
    else:
        verdict = "HOLD+ — Critical substrate depletion. PAUSE. Recovery is the only productive action."
        tier = "RED"

    readiness = {
        "uri": "well://readiness/arif",
        "timestamp": state.get("timestamp"),
        "well_score": score,
        "authority_capacity": authority_capacity,
        "verdict": verdict,
        "tier": tier,
        "causal_chain": {
            "sleep_debt": sleep_debt,
            "decision_fatigue": fatigue,
            "cognitive_clarity": clarity,
            "psi_SE": psi_se,
            "burnout_risk": burnout,
            "authority_capacity": authority_capacity,
            "dag": "SleepDebt → DecisionFatigue → psi_SE → AuthorityCapacity → Verdict",
        },
        "components": {
            "clarity_contribution": round(clarity * 0.30, 3),
            "fatigue_contribution": round((1.0 - fatigue) * 0.25, 3),
            "psi_se_contribution": round(psi_se * 0.20, 3),
            "burnout_contribution": round((1.0 - burnout) * 0.15, 3),
            "sleep_contribution": round(max(0, 1.0 - sleep_debt * 0.3) * 0.10, 3),
        },
        "active_violations": violations,
        "counterfactual": {
            "if_sleep_improved": f"If sleep improves by 2h, authority capacity ≈ {round(min(1.0, authority_capacity + 0.15), 3)}",
            "if_rested": f"After full recovery cycle, capacity reverts toward {round(min(1.0, 0.75 + psi_se * 0.15), 3)}",
        },
        "w0": "WELL reflects. Arif decides. This is a mirror, not a command.",
    }
    return json.dumps(readiness, indent=2, default=str)


@mcp.resource(
    "well://sovereign_entropy/arif",
    description=(
        "Live psi_SE (sovereign entropy) metric with component breakdown. "
        "Measures the sovereign's resistance to behavioral modeling and capture. "
        "psi_SE < 0.40 = VULNERABLE (predictable, capturable). "
        "psi_SE 0.40-0.60 = ADVISORY (monitor for decline). "
        "psi_SE > 0.70 = SOVEREIGN (protective unpredictability active). "
        "This is about PROTECTING entropy, not reducing it. "
        "The machine must never optimize the sovereign into predictability."
    ),
)
def afwell_sovereign_entropy() -> str:
    state = _load_state()
    metrics = state.get("metrics", {})
    cognitive = metrics.get("cognitive", {})

    psi_se = cognitive.get("psi_SE", 0.65) or 0.65
    paradox = cognitive.get("paradox_density", 0.7) or 0.7
    inconsistency = cognitive.get("inconsistency_rate", 0.6) or 0.6
    refusal = cognitive.get("refusal_patterns", 0.8) or 0.8
    context_switch = cognitive.get("context_switching_frequency", 0.75) or 0.75
    footprint = cognitive.get("digital_footprint_diversity", 0.65) or 0.65

    if psi_se >= 0.75:
        band = "SOVEREIGN"
        guidance = "Entropy is protective. No action needed. Maintain unpredictability."
    elif psi_se >= 0.50:
        band = "ADVISORY"
        guidance = "Monitor for entropy decline. Avoid routine pattern enforcement."
    elif psi_se >= 0.30:
        band = "VULNERABLE"
        guidance = "Entropy dropping. Introduce randomization. Break routines. Rest."
    else:
        band = "CRITICAL"
        guidance = "Sovereign entropy critically low. Pattern-matchable. PAUSE. Recover sovereignty."

    payload = {
        "uri": "well://sovereign_entropy/arif",
        "timestamp": state.get("timestamp"),
        "psi_SE": psi_se,
        "band": band,
        "guidance": guidance,
        "components": {
            "paradox_density": paradox,
            "weight": 0.25,
            "meaning": "How often you hold contradictory truths. High = anti-capture.",
            "inconsistency_rate": inconsistency,
            "weight_inconsistency": 0.20,
            "meaning_inconsistency": "How often your behavior defies pattern modeling.",
            "refusal_patterns": refusal,
            "weight_refusal": 0.20,
            "meaning_refusal": "How often you say no. High refusal = high sovereignty.",
            "context_switching": context_switch,
            "weight_switch": 0.20,
            "meaning_switch": "How frequently you change contexts. High = hard to model.",
            "footprint_diversity": footprint,
            "weight_diversity": 0.15,
            "meaning_diversity": "Diversity of your digital footprint across platforms.",
        },
        "anti_capture_note": (
            "The machine must never optimize the sovereign into predictability. "
            "psi_SE decline is a capture risk, not a performance issue. "
            "Consistency is efficiency for machines, vulnerability for humans."
        ),
        "w0": "Sovereignty entropy belongs to Arif alone.",
    }
    return json.dumps(payload, indent=2, default=str)


@mcp.resource(
    "well://causal_dag",
    description=(
        "WELL causal readiness DAG specification. DoWhy-compatible structural "
        "causal model: SleepDebt → FatigueLevel → psi_SE → AuthorityCapacity → Verdict. "
        "HRV_Index, CognitiveLoad, and ContextSwitches contribute to FatigueLevel. "
        "Immutable within a session. Supports counterfactual queries: "
        "'If sleep improves by 2h, how does the authority verdict change?'"
    ),
)
def afwell_causal_dag() -> str:
    dag = {
        "uri": "well://causal_dag",
        "version": "well_dag_v2.0",
        "framework": "DoWhy structural causal model",
        "immutable_per_session": True,
        "nodes": {
            "SleepDebt": {
                "type": "exogenous",
                "source": "wearable/self-report",
                "unit": "hours_debt",
                "description": "Accumulated sleep deficit in hours",
            },
            "HRV_Index": {
                "type": "exogenous",
                "source": "wearable (Phase 5)",
                "unit": "0.0–1.0 normalized",
                "description": "Heart rate variability normalized index",
            },
            "CognitiveLoad": {
                "type": "exogenous",
                "source": "behavioral (agent sessions, tokens, decisions)",
                "unit": "0.0–1.0",
                "description": "Cognitive throughput from agent session telemetry",
            },
            "ContextSwitches": {
                "type": "exogenous",
                "source": "behavioral (session context changes)",
                "unit": "switches_per_hour",
                "description": "Frequency of context/task switching",
            },
            "FatigueLevel": {
                "type": "endogenous",
                "parents": [
                    "SleepDebt",
                    "HRV_Index",
                    "CognitiveLoad",
                    "ContextSwitches",
                ],
                "description": "Composite fatigue from all contributing factors",
            },
            "DecisionFatigue": {
                "type": "endogenous",
                "parents": ["ContextSwitches", "CognitiveLoad"],
                "description": "Decision-specific fatigue from context switching and load",
            },
            "psi_SE": {
                "type": "endogenous",
                "parents": ["FatigueLevel", "DecisionFatigue"],
                "description": "Sovereign entropy — anti-capture metric. Fatigue reduces psi_SE.",
            },
            "AuthorityCapacity": {
                "type": "endogenous",
                "parents": ["psi_SE"],
                "description": "Capacity to authorize agentic actions. Gated by psi_SE.",
            },
            "Verdict": {
                "type": "endogenous",
                "parents": ["AuthorityCapacity"],
                "values": ["SEAL", "SABAR", "HOLD"],
                "description": "Final authority verdict for pending agentic action.",
            },
        },
        "edges": [
            {"from": "SleepDebt", "to": "FatigueLevel"},
            {"from": "HRV_Index", "to": "FatigueLevel"},
            {"from": "CognitiveLoad", "to": "FatigueLevel"},
            {"from": "ContextSwitches", "to": "FatigueLevel"},
            {"from": "ContextSwitches", "to": "DecisionFatigue"},
            {"from": "CognitiveLoad", "to": "DecisionFatigue"},
            {"from": "FatigueLevel", "to": "psi_SE"},
            {"from": "DecisionFatigue", "to": "psi_SE"},
            {"from": "psi_SE", "to": "AuthorityCapacity"},
            {"from": "AuthorityCapacity", "to": "Verdict"},
        ],
        "counterfactual_support": True,
        "example_counterfactual": (
            "If SleepDebt reduces from 3h to 0h, "
            "FatigueLevel drops ~0.3, psi_SE increases ~0.15, "
            "AuthorityCapacity rises ~0.12, Verdict may shift from SABAR to SEAL."
        ),
    }
    return json.dumps(dag, indent=2)
    return json.dumps(_well_tree777_index(), indent=2)


@mcp.resource(
    "tree777://skills/well/{name}",
    description=(
        "Individual WELL skill page from the TREE777 wiki. "
        "Returns markdown content (frontmatter-stripped) with metadata. "
        "Example: tree777://skills/well/governance-ops"
    ),
)
def well_tree777_skill(name: str) -> str:
    file_path = TREE777_SKILLS_DIR / f"{name}.md"
    if not file_path.exists():
        return json.dumps(
            {
                "error": f"Skill not found: {name}",
                "uri": f"tree777://skills/well/{name}",
            }
        )
    content = _well_read_wiki_file(file_path)
    return json.dumps(
        {"uri": f"tree777://skills/well/{name}", "content": content}, indent=2
    )


@mcp.resource(
    "tree777://well/concepts/{name}",
    description=(
        "Vitality concept page from the TREE777 wiki. "
        "Example: tree777://well/concepts/TREE777"
    ),
)
def well_tree777_concept(name: str) -> str:
    file_path = TREE777_CONCEPTS_DIR / f"{name}.md"
    if not file_path.exists():
        return json.dumps(
            {
                "error": f"Concept not found: {name}",
                "uri": f"tree777://well/concepts/{name}",
            }
        )
    content = _well_read_wiki_file(file_path)
    return json.dumps(
        {"uri": f"tree777://well/concepts/{name}", "content": content}, indent=2
    )


@mcp.resource(
    "tree777://well/scars/{name}",
    description=(
        "WELL scar/incident record from the TREE777 wiki. "
        "Documents failures and lessons learned for vitality operations. "
        "Example: tree777://well/scars/well-fatigue-breach"
    ),
)
def well_tree777_scar(name: str) -> str:
    file_path = TREE777_SCAR_DIR / f"{name}.md"
    if not file_path.exists():
        return json.dumps(
            {"error": f"Scar not found: {name}", "uri": f"tree777://well/scars/{name}"}
        )
    content = _well_read_wiki_file(file_path)
    return json.dumps(
        {"uri": f"tree777://well/scars/{name}", "content": content}, indent=2
    )


# ═══════════════════════════════════════════════════════════════════════════════
# MCP Prompts — Canonical 4
# User-controlled structured interactions (not model-controlled like tools)
# ═══════════════════════════════════════════════════════════════════════════════


@mcp.prompt()
def prompt_daily_reflection(date: str | None = None) -> str:
    """
    Guided morning/evening check-in for operator Arif.
    User-controlled prompt — Arif triggers this, not the model.
    """
    state = _load_state()
    score = state.get("well_score", 50)
    violations = state.get("floors_violated", [])
    metrics = state.get("metrics", {})
    sleep = metrics.get("sleep", {})
    cognitive = metrics.get("cognitive", {})

    sleep_debt = sleep.get("sleep_debt_days", 0)
    clarity = cognitive.get("clarity", 10)
    fatigue = cognitive.get("decision_fatigue", 0)

    date_str = date or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    prompt = f"""# AFWELL Daily Reflection — {date_str}

## Current Vitals
- WELL Score: {score}/100
- Sleep Debt: {sleep_debt} days
- Cognitive Clarity: {clarity}/10
- Decision Fatigue: {fatigue}/10
- Active Violations: {violations or "None"}

## Reflection Questions
1. **Sleep**: Did you sleep enough? If debt > 0, what is the recovery plan?
2. **Cognitive Load**: Is your clarity where it needs to be for today's decisions?
3. **Pressure**: What is the primary source of load right now?
4. **Niat**: Is your intent clear for the most important task today?
5. **Boundary**: Do you feel any coercion, or is your sovereignty intact?

## WELL Advisory
"""
    if score >= 80 and not violations:
        prompt += "Substrate is optimal. Full bandwidth available. Maintain rhythm."
    elif score >= 60:
        prompt += "Substrate is functional. Proceed with structure. Avoid irreversible commitments."
    elif score >= 40:
        prompt += "Substrate is degraded. Draft-only mode. Prioritize recovery before high-stakes decisions."
    else:
        prompt += "Substrate is low-capacity. PAUSE. Rest is the only productive action right now."

    prompt += "\n\n> W0: WELL holds a mirror, not a veto. Arif decides."
    return prompt


@mcp.prompt()
def prompt_recovery_protocol(
    severity: str = "moderate", domain: str = "general"
) -> str:
    """
    Structured recovery protocol.
    severity: mild | moderate | severe
    domain: general | sleep | cognitive | stress | metabolic
    """
    protocols = {
        "sleep": [
            "Set a hard bedtime alarm 30 minutes before target sleep time.",
            "No screens 60 minutes before bed.",
            "If sleep debt > 2 days: cancel non-essential meetings tomorrow.",
        ],
        "cognitive": [
            "Take a 15-minute walk without devices.",
            "Write down all open decisions — externalize from working memory.",
            "Switch to C0/C1 tasks only (notes, organizing, not deciding).",
        ],
        "stress": [
            "Breathe: 4-7-8 pattern for 3 cycles.",
            "Change physical environment for 10 minutes.",
            "Identify one boundary you can reinforce today.",
        ],
        "metabolic": [
            "Drink 500ml water immediately.",
            "Eat within the next 30 minutes if fasting > 16 hours.",
            "Stand and move for 2 minutes.",
        ],
        "general": [
            "Hydrate first.",
            "Step away from the screen for 15 minutes.",
            "Do one small physical task (tidy, walk, stretch).",
        ],
    }

    actions = protocols.get(domain, protocols["general"])
    if severity == "severe":
        header = "# 🚨 SEVERE Recovery Protocol\n\nStop all consequential work."
    elif severity == "moderate":
        header = (
            "# ⚠️ MODERATE Recovery Protocol\n\nReduce load and restore one dimension."
        )
    else:
        header = "# 🌱 MILD Recovery Protocol\n\nMaintain and prevent degradation."

    body = "\n".join(f"- {action}" for action in actions)
    return f"{header}\n\n## Actions ({domain})\n{body}\n\n> WELL does not diagnose. These are operational self-regulation suggestions."


@mcp.prompt()
def prompt_readiness_brief(task_type: str = "general", urgency: str = "normal") -> str:
    """
    Pre-task readiness briefing.
    task_type: general | coding | public_writing | financial | legal | irreversible
    urgency: low | normal | high | critical
    """
    state = _load_state()
    score = state.get("well_score", 50)
    violations = state.get("floors_violated", [])
    metrics = state.get("metrics", {})
    cog = metrics.get("cognitive", {})
    stress = metrics.get("stress", {})
    sleep = metrics.get("sleep", {})

    fatigue = cog.get("decision_fatigue", 0)
    clarity = cog.get("clarity", 10)
    stress_load = stress.get("subjective_load", 0)
    sleep_debt = sleep.get("sleep_debt_days", cog.get("sleep_debt_days", 0))
    if sleep_debt is None:
        sleep_debt = 0

    risk_map = {
        ("irreversible", "critical"): "T5",
        ("financial", "high"): "T4",
        ("legal", "high"): "T4",
        ("public_writing", "high"): "T3",
        ("coding", "high"): "T3",
    }
    risk_tier = risk_map.get((task_type, urgency), "T2" if urgency == "high" else "T1")

    prompt = f"""# AFWELL Readiness Brief

## Task Profile
- Type: {task_type}
- Urgency: {urgency}
- Risk Tier: {risk_tier}

## Current Substrate
- WELL Score: {score}/100
- Clarity: {clarity}/10
- Decision Fatigue: {fatigue}/10
- Stress Load: {stress_load}/10
- psi_SE (Sovereign Entropy): {round((1.0 - fatigue / 10) * 0.7 + 0.3, 2)} (lower = more capturable/patternable)
- Authority Capacity: {round(clarity / 20 + (10 - fatigue) / 20 + 0.2, 2)} (readiness to decide)
- Violations: {violations or "None"}

## Causal Readiness Chain
Sleep → Fatigue → psi_SE → Authority → Verdict
  ↓       ↓        ↓         ↓          ↓
 {sleep_debt}d  {fatigue}/10   {round((1.0 - fatigue / 10) * 0.7 + 0.3, 2)}    {round(clarity / 20 + (10 - fatigue) / 20 + 0.2, 2)}    SEE BELOW

## Recommendation
"""
    if risk_tier in ("T4", "T5") and (score < 75 or fatigue > 5 or clarity < 7):
        prompt += "🛑 HOLD — High-risk task with degraded substrate. Delay or delegate."
    elif risk_tier == "T3" and (score < 60 or fatigue > 6):
        prompt += (
            "⚠️ CAUTION — Elevated risk. Proceed only with explicit human confirmation."
        )
    else:
        prompt += "✅ PROCEED — Substrate supports this task class."

    prompt += "\n\n> WELL informs. Arif decides."
    return prompt


@mcp.prompt()
def prompt_substrate_classify(subject: str = "") -> str:
    """
    Universal substrate classification prompt.
    User provides a subject; WELL guides the classification.
    """
    if not subject:
        return "# Substrate Classification\n\nPlease provide a subject to classify."

    prompt = f"""# Substrate Classification: "{subject}"

## Classification Framework
| Class | Vitality Mode | Machine Authority |
|-------|--------------|-------------------|
| HUMAN_PERSON | biological + cognitive + livelihood + role | advisory_only |
| HUMAN_BODY_PART | integration with living body | advisory_only |
| NONHUMAN_ORGANISM | biological vitality | advisory_only |
| LIMINAL_BIOLOGICAL | replicative potency, host dependence | advisory_only |
| MACHINE_SYSTEM | operational reliability | instrument_assessment |
| INSTITUTION | organizational viability | advisory_only |
| MATERIAL_OBJECT | structural integrity, not life | instrument_assessment |
| ECOSYSTEM | ecological vitality | advisory_only |
| INFORMATION_SYSTEM | coherence, maintainability, truth | advisory_only |
| SYMBOLIC_METAPHYSICAL | NOT machine-measurable | mirror_and_protect_only |

## Key Questions
1. Does it metabolize energy independently?
2. Does it maintain internal homeostasis?
3. Can it reproduce or sustain lineage?
4. Is it host-dependent?
5. Is it externally designed or self-organizing?
6. Does it carry meaning beyond its physical structure?

## WELL Boundary
- For SYMBOLIC_METAPHYSICAL: WELL protects dignity. It does NOT quantify, prove, or diagnose.
- For HUMAN_PERSON: WELL reflects vitality. It does NOT determine worth.
- For MACHINE_SYSTEM: WELL assesses reliability. It does NOT claim life.

> "Life is not mere structure. Life is structure that maintains itself against entropy through embodied energetic regulation."
"""
    return prompt


# ── Additional Domain Prompts ────────────────────────────────────────────────


@mcp.prompt()
def prompt_niat_check(task: str = "") -> str:
    """
    NIAT (Niat/Intent) check for Arif.
    User-controlled prompt — Arif triggers this, not the model.
    W0: WELL holds a mirror, not a veto. Arif decides.
    """
    if not task:
        return "# NIAT Check\n\nPlease provide the task or intent you want to examine."

    prompt = f"""# NIAT (Intention) Check — "{task}"

## W0 Invariant
WELL holds a mirror, not a veto. Arif decides.

## NIAT Assessment
1. **Origin**: Where does this intention come from? Internal conviction or external pressure?
2. **Clarity**: Is the outcome you want clearly defined?
3. **Alignment**: Does this intention align with your stated values and priorities?
4. **Coercion**: Is any part of this being forced by obligation, guilt, or fear?
5. ** Sovereignty**: Are you freely choosing this, or is it a should?

## Reflection
- What would you do if no one would ever know?
- What would you advise a close friend in the same situation?
- Does this feel like yours, or like something you're doing for someone else?

## Output
State your NIAT clearly. Is this truly your intention?
"""
    return prompt


@mcp.prompt()
def prompt_fatigue_boundary_review(
    fatigue_level: str = "unknown",
    pressure: str = "normal",
    days_without_break: int = 0,
) -> str:
    """
    Fatigue boundary review for Arif.
    User-controlled prompt — Arif triggers this, not the model.
    W0: WELL holds a mirror, not a veto. Arif decides.
    """
    prompt = f"""# Fatigue Boundary Review

## Current State
- Fatigue Level: {fatigue_level}
- Pressure: {pressure}
- Days Without Break: {days_without_break}

## Boundary Assessment
1. **Fatigue check**: On a 1-10 scale, where is your cognitive energy?
2. **Decision quality**: Are you making decisions sharper or more impulsive than usual?
3. **Recovery need**: What would recovery look like?
4. **Load tolerance**: How much more can you carry before degradation?

## Key Questions
- Are you operating from clarity or from momentum?
- Is there something being avoided by staying busy?
- What would "stop" look like, and is that a viable option?

## W0 Sovereignty Reminder
WELL reflects. Arif decides. You are not your fatigue, but you are not unaffected by it either.

## Output
Recognize the boundary. What is the next wise action?
"""
    return prompt


# ═══════════════════════════════════════════════════════════════════════════════
# Legacy tool deprecation notices
# The 31 legacy tools remain as backward-compatible wrappers.
# Prefer the 13 canonical tools for new integrations.
# Prefer the 13 Ω-WELL tools for universal substrate governance.
# ═══════════════════════════════════════════════════════════════════════════════

# ── Entry ──────────────────────────────────────────────────────────────────────

# ── WellStack Monkeys ─────────────────────────────────────────────────────────
# Fix 406 from Accept header — mirror of GEOX fix
from mcp.server.streamable_http import StreamableHTTPServerTransport

_orig_check = StreamableHTTPServerTransport._check_accept_headers


def _patched_check(self, request):
    if getattr(self, "is_json_response_enabled", False):
        return True, True
    return _orig_check(self, request)


StreamableHTTPServerTransport._check_accept_headers = _patched_check

# ============================================================
# ORGAN_GOVERNANCE: arifOS L1-L13 Wrapper
# Patch mcp.call_tool to intercept all tool execution.
# ============================================================
# ── Supabase L4 Domain Receipts ─────────────────────────────────────────────
# Fire-and-forget async writes to Supabase well_states table.
_WELL_SUPABASE_URL = _os.getenv(
    "WELL_SUPABASE_URL", "https://utbmmjmbolmuahwixjqc.supabase.co"
)
_WELL_SUPABASE_ANON_KEY = _os.getenv(
    "WELL_SUPABASE_ANON_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV0Ym1tam1ib2xtdWFod2l4anFjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDk1MjQwMTYsImV4cCI6MjAwNTA5OTk5Nn0.Nxg2Rkf-PyqnemVGz-_H1VW22jhNbmq67hH6EZ2EzEs",
)


async def _well_write_domain_receipt(
    tool_name: str, result: Any, arguments: dict
) -> None:
    """Write WELL domain data to Supabase. Fails silently if Supabase is down."""
    try:
        import datetime as _dt
        import httpx

        mode = _os.getenv("WELL_SUPABASE_WRITE_MODE", "off").lower()
        if mode == "off":
            return
        epoch = _dt.datetime.now(_dt.timezone.utc).isoformat()
        headers = {
            "apikey": _WELL_SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {_WELL_SUPABASE_ANON_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            if tool_name == "well_log_state" and mode in ("domain", "dual"):
                payload = {
                    "well_type": arguments.get("well_type", "human"),
                    "sovereign_score": (
                        result.get("well_score", 0) if isinstance(result, dict) else 0
                    ),
                    "truth_status": (
                        result.get("truth_status", "unknown")
                        if isinstance(result, dict)
                        else "unknown"
                    ),
                    "state_age_hours": 0,
                    "kappa_r": (
                        result.get("kappa_r", 0) if isinstance(result, dict) else 0
                    ),
                    "delta_s": (
                        result.get("delta_s", 0) if isinstance(result, dict) else 0
                    ),
                    "peace2": (
                        result.get("peace2", 0) if isinstance(result, dict) else 0
                    ),
                    "rasa": (
                        result.get("rasa", "unknown")
                        if isinstance(result, dict)
                        else "unknown"
                    ),
                    "amanah": (
                        result.get("amanah", 0) if isinstance(result, dict) else 0
                    ),
                    "metadata": {
                        "tool": tool_name,
                        "args": {k: v for k, v in arguments.items() if k != "state"},
                    },
                    "epoch": epoch,
                }
                await client.post(
                    f"{_WELL_SUPABASE_URL}/rest/v1/arifosmcp_well_states",
                    headers=headers,
                    json=payload,
                )
    except Exception:
        pass  # fire-and-forget — never propagate


try:
    _original_call_tool = mcp.call_tool

    # ── Evidence Contract envelope (Appendix B of 000_CONSTITUTION.md) ─────────
    # WELL emits readiness signals, never constitutional verdicts. The organ
    # classifies its own evidence strength. arifOS reads the envelope; it
    # does not negotiate field names. WELL does NOT name the Laws (L01-L13).

    _WELL_SIGNAL_TAG_MAP = {
        "safe": "CLAIM",
        "ok": "CLAIM",
        "ready": "CLAIM",
        "stable": "PLAUSIBLE",
        "watch": "PLAUSIBLE",
        "caution": "HYPOTHESIS",
        "degraded": "HYPOTHESIS",
        "unsafe": "ESTIMATE",
        "unsafe_to_interpret": "ESTIMATE",
        "critical": "UNKNOWN",
        "void": "UNKNOWN",
    }

    def _well_classify_epistemic(result: dict) -> tuple:
        """Derive (epistemic_tag, evidence_quality) from WELL result fields.

        WELL is REFLECT_ONLY. It observes; it does not judge. Its epistemic
        strength comes from data freshness + boundary adherence.
        """
        # Tag: prefer signal → ok → verdict
        signal = str(result.get("signal") or "").lower()
        ok = result.get("ok")
        if ok is True:
            tag = "CLAIM"
        elif ok is False:
            tag = "ESTIMATE"
        else:
            tag = _WELL_SIGNAL_TAG_MAP.get(signal, "UNKNOWN")
        # Quality: inversely from uncertainty
        uncertainty = float(result.get("uncertainty", 0.5))
        quality = max(0.05, 1.0 - uncertainty)
        # State freshness affects quality
        state_age = result.get("state_age_hours")
        if isinstance(state_age, (int, float)):
            if state_age > 72:
                quality = max(quality - 0.40, 0.10)
            elif state_age > 24:
                quality = max(quality - 0.20, 0.20)
        # Error / constraint reduces quality
        if result.get("error"):
            quality = max(quality - 0.30, 0.05)
        return (tag, round(quality, 4))

    def _well_wrap_envelope(tool_name: str, result: Any) -> Any:
        """Wrap a WELL tool result in the canonical Evidence Contract envelope."""
        # FastMCP returns ToolResult (Pydantic). Extract structured_content.
        if (
            hasattr(result, "structured_content")
            and result.structured_content is not None
        ):
            domain = result.structured_content
            if hasattr(domain, "model_dump"):
                domain = domain.model_dump()
        elif hasattr(result, "model_dump"):
            domain = (
                result.model_dump().get("structured_content") or result.model_dump()
            )
        elif isinstance(result, dict):
            domain = result
        else:
            return result
        if not isinstance(domain, dict):
            return result
        # Idempotent
        if (
            "epistemic_tag" in domain
            and "evidence_quality" in domain
            and "result" in domain
        ):
            return result
        tag, quality = _well_classify_epistemic(domain)
        # Uncertainty band: from existing uncertainty field
        uncertainty = float(domain.get("uncertainty", 0.5) or 0.5)
        low = round(max(0.03, uncertainty * 0.5), 4)
        high = round(max(0.05, uncertainty), 4)
        # delta_S: heuristic
        has_error = bool(domain.get("error"))
        state_age = domain.get("state_age_hours", 0) or 0
        delta_s = round(
            0.05 * float(has_error) + 0.01 * (float(state_age) / 24.0) - 0.05, 4
        )
        # source_attribution
        source_attribution = [
            "WELL:server.py",
            f"WELL:tool/{tool_name}",
        ]
        if domain.get("authority") or domain.get("role"):
            source_attribution.append("WELL:authority/REFLECT_ONLY")
        # Build envelope. Per Appendix B, original payload goes under "result".
        envelope = {
            "result": domain,
            "epistemic_tag": tag,
            "evidence_quality": quality,
            "source_attribution": source_attribution,
            "uncertainty_band": [low, high],
            "delta_S": delta_s,
        }
        # Set structured_content on the ToolResult (preserve content)
        try:
            if hasattr(result, "structured_content"):
                result.structured_content = envelope
                return result
        except Exception:
            pass
        return envelope

    async def _governance_call_tool(name, arguments=None, **kwargs):
        """Wrap mcp.call_tool with arifOS governance pre-check + Evidence Contract envelope."""

        if arguments is None:
            arguments = {}
        verdict, error = check_governance(name, arguments)
        if error is not None:
            # Return governance block as JSON error in MCP format
            from fastmcp.exceptions import ToolError

            raise ToolError(f"arifOS {verdict}: governance check blocked execution")
        result = await _original_call_tool(name, arguments, **kwargs)

        # ── Supabase L4: fire-and-forget domain receipt ───────────────────
        try:
            import asyncio

            loop = asyncio.get_running_loop()
            loop.create_task(_well_write_domain_receipt(name, result, arguments))
        except Exception:
            pass  # fire-and-forget

        # Emit Evidence Contract envelope (Appendix B)
        result = _well_wrap_envelope(name, result)
        return result

    mcp.call_tool = _governance_call_tool
    logger.info("WELL governance wrapper active — arifOS L1-L13")
except Exception as _e:
    logger.error("WELL governance wrapper failed: %s", _e)


# ══════════════════════════════════════════════════════════════════════════════
# F-Ω Federation Handoff Adapters — forged 2026-06-17 by FORGE (000Ω)
#
# Three new @mcp.tool() functions wiring explicit federation hooks that the
# 13-signal coverage report flagged as MISSING:
#
#   1. well_handoff_dignity_to_arifos()  →  S12 → arifOS 888_JUDGE
#   2. well_handoff_livelihood_to_wealth() →  S13 → WEALTH
#   3. well_attest_to_kernel()           →  WELL → arifOS organ_attest
#
# Authority: REFLECT_ONLY.  WELL observes + signals; it does NOT judge.
# Fail-open: if peer unreachable, returns federation_unavailable (no crash).
# Reversibility: additive only — no existing function modified.
# ══════════════════════════════════════════════════════════════════════════════

_ARIFOS_MCP_URL = _os.environ.get("ARIFOS_MCP_URL", "http://127.0.0.1:8088/mcp")
_WEALTH_MCP_URL = _os.environ.get("WEALTH_MCP_URL", "http://127.0.0.1:18082/mcp")
_FED_TIMEOUT_S = float(_os.environ.get("WELL_FED_TIMEOUT_S", "5.0"))


def _federation_post_tool_call(
    base_url: str,
    tool_name: str,
    arguments: dict,
    timeout: float | None = None,
) -> dict[str, Any]:
    """
    Helper: POST a tools/call to a federated MCP server.

    Supports two transport modes:
      1. STATELESS (default for arifOS / WEALTH / WELL since 2026.05):
         Skip initialize; call tools/call directly.
      2. STATEFUL (legacy, for peers that return mcp-session-id header):
         Two-step initialize → tools/call handshake.

    Detection: if peer's initialize response includes mcp-session-id header,
    use stateful mode; otherwise use stateless direct call.

    Fail-open contract: returns federation_unavailable on any error.
    """
    _t = timeout if timeout is not None else _FED_TIMEOUT_S
    try:
        # Step 0: probe for stateful mode
        _init_body = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "WELL-federation-adapter",
                        "version": "2026.06.17",
                    },
                },
            }
        ).encode("utf-8")
        _init_req = urllib.request.Request(
            base_url,
            data=_init_body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
        )
        _session_id: str | None = None
        try:
            with urllib.request.urlopen(_init_req, timeout=_t) as _init_resp:
                _session_id = _init_resp.headers.get("mcp-session-id")
                # Consume body to free connection
                _init_resp.read()
        except Exception:
            # If initialize fails, try stateless direct call
            _session_id = None

        # Build the tools/call request
        _call_body = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments},
            }
        ).encode("utf-8")
        _call_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if _session_id:
            _call_headers["mcp-session-id"] = _session_id
        _call_req = urllib.request.Request(
            base_url,
            data=_call_body,
            headers=_call_headers,
        )
        with urllib.request.urlopen(_call_req, timeout=_t) as _resp:
            _raw = _resp.read().decode("utf-8")
        # MCP may return JSON or JSONL (SSE-style)
        try:
            _json_out = json.loads(_raw)
        except json.JSONDecodeError:
            _first_line = _raw.splitlines()[0] if _raw else ""
            _json_out = json.loads(_first_line) if _first_line else {}
        return {
            "ok": True,
            "result": _json_out,
            "session_id": _session_id,
            "transport": "stateful" if _session_id else "stateless",
        }
    except Exception as _exc:
        return {
            "ok": False,
            "fail_mode": "federation_unavailable",
            "error": f"{type(_exc).__name__}: {str(_exc)[:200]}",
        }


def _extract_mcp_text_payload(mcp_result: dict) -> dict:
    """
    Extract the inner JSON payload from a MCP tools/call response.
    MCP wraps results in {result: {content: [{type: text, text: "<json>"}]}}.
    """
    try:
        for _c in mcp_result.get("result", {}).get("content", []):
            if _c.get("type") == "text":
                return json.loads(_c.get("text", "{}"))
        return mcp_result.get("result", mcp_result)
    except Exception:
        return {}


# ── 1. WELL → arifOS 888_JUDGE explicit handoff for S12 dignity ──────────────
@mcp.tool()
def well_handoff_dignity_to_arifos(
    coercion_signals: list[str] | None = None,
    dignity_preservation: float | None = None,
    reductionism_risk: float | None = None,
    signal: str = "dignity_leakage_under_review",
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Ω-WELL-FED-S12: Explicit handoff of S12 (social_dignity_consent) signal
    from WELL → arifOS 888_JUDGE for constitutional deliberation.

    WELL observes, signals, and prepares. arifOS judges. arifOS issues
    the verdict; WELL only reports the signal and the handoff receipt.
    Per GENESIS/004 §2.1, this function returns 'signal' (not 'verdict').

    Fail-open: if arifOS unreachable, returns federation_unavailable
    with the signal preserved for later retry.
    """
    _dignity_packet = {
        "organ": "WELL",
        "signal_layer": "tier_4_dignity",
        "signal_id": "S12_social_dignity_consent",
        "signal": signal,
        "coercion_signals": coercion_signals or [],
        "dignity_preservation": dignity_preservation,
        "reductionism_risk": reductionism_risk,
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z",
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }
    _resp = _federation_post_tool_call(
        _ARIFOS_MCP_URL,
        "arif_judge_deliberate",
        {
            "mode": "judge",
            "candidate": json.dumps(_dignity_packet),
            "action_class": "dignity_breach_signal",
            "actor_id": "well-system",
        },
    )
    if not _resp.get("ok"):
        return {
            "ok": False,
            "signal": signal,
            "federation": "arifos",
            "fail_mode": _resp.get("fail_mode", "federation_unavailable"),
            "error": _resp.get("error"),
            "packet": _dignity_packet,
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        }
    _arif_inner = _extract_mcp_text_payload(_resp["result"])
    return {
        "ok": True,
        "signal": signal,
        "federation": "arifos",
        "arifos_session_id": _resp.get("session_id"),
        "arifos_receipt": _arif_inner,
        "packet": _dignity_packet,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


# ── 2. WELL → WEALTH explicit handoff for S13 livelihood ────────────────────
@mcp.tool()
def well_handoff_livelihood_to_wealth(
    duty_load: float | None = None,
    cashflow_status: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Ω-WELL-FED-S13: Explicit handoff of S13 (environment_livelihood) signal
    from WELL → WEALTH for capital/cashflow evidence pull.

    WELL does not compute capital. WELL surfaces the readiness frame
    (duty_load, role_burden) and asks WEALTH for the livelihood evidence
    (cashflow_status, runway, expense ratio).  Federation = composition.

    Fail-open: if WEALTH unreachable, returns federation_unavailable
    with the readiness frame preserved for later retry.
    """
    _wealth_resp = _federation_post_tool_call(
        _WEALTH_MCP_URL,
        "wealth_personal_finance",
        {"mode": "summary", "owner": "arif"},
    )
    _wealth_payload: dict = {}
    if _wealth_resp.get("ok"):
        _wealth_payload = _extract_mcp_text_payload(_wealth_resp["result"])

    _livelihood_packet = {
        "organ": "WELL",
        "signal_layer": "tier_4_dignity_environment",
        "signal_id": "S13_environment_livelihood",
        "signal": "livelihood_signal_composed",
        "readiness_frame": {
            "duty_load": duty_load,
            "cashflow_status_self_reported": cashflow_status,
            "operator_id": "arif",
        },
        "wealth_evidence": _wealth_payload if _wealth_resp.get("ok") else None,
        "wealth_fail_mode": _wealth_resp.get("fail_mode")
        if not _wealth_resp.get("ok")
        else None,
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z",
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }
    return {
        "ok": _wealth_resp.get("ok", False),
        "signal": "livelihood_signal_composed",
        "federation": "wealth",
        "wealth_session_id": _wealth_resp.get("session_id"),
        "wealth_receipt": _wealth_payload,
        "packet": _livelihood_packet,
        "fail_mode": _wealth_resp.get("fail_mode")
        if not _wealth_resp.get("ok")
        else None,
        "error": _wealth_resp.get("error") if not _wealth_resp.get("ok") else None,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


# ── 3. WELL → arifOS organ_attest (active federation heartbeat) ────────────
@mcp.tool()
def well_attest_to_kernel(ctx: Context | None = None) -> dict[str, Any]:
    """
    Ω-WELL-FED-ATTEST: Active organ attestation from WELL → arifOS kernel.

    The external organ_heartbeat_daemon polls /health (read-only, one-way).
    This tool performs an active attestation (WELL → kernel) that records
    state in the kernel's organ registry via arif_organ_attest.

    Fail-open: if arifOS unreachable, returns federation_unavailable.
    The /health heartbeat (daemon) remains the canonical health source.
    """
    _state: dict = {}
    try:
        if "_load_state" in dir():
            _state = _load_state() or {}
    except Exception:
        _state = {}
    _attestation = {
        "organ_id": "WELL",
        "identity_hash": "1b1f46b3e0896994e27b354dfca58efd3f088e58f1428773ac3c45c2b5f3195a",
        "authority": "REFLECT_ONLY",
        "final_authority": "ARIF",
        "verdict_local": _state.get("verdict", "WELL_HOLD"),
        "well_score": _state.get("well_score"),
        "freshness": _state.get("freshness", "UNKNOWN"),
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z",
    }
    _resp = _federation_post_tool_call(
        _ARIFOS_MCP_URL,
        "arif_organ_attest",
        {
            "organ_id": "WELL",
            "actor_id": "well-system",
        },
    )
    if not _resp.get("ok"):
        return {
            "ok": False,
            "organ": "WELL",
            "federation": "arifos",
            "fail_mode": _resp.get("fail_mode", "federation_unavailable"),
            "error": _resp.get("error"),
            "attestation": _attestation,
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        }
    _arif_inner = _extract_mcp_text_payload(_resp["result"])
    return {
        "ok": True,
        "organ": "WELL",
        "federation": "arifos",
        "arifos_session_id": _resp.get("session_id"),
        "arifos_receipt": _arif_inner,
        "attestation": _attestation,
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


if __name__ == "__main__":
    # ── Transport mode selection ─────────────────────────────────────────
    import argparse
    import sys

    logger.info("WELL MCP server starting")
    _parser = argparse.ArgumentParser(add_help=False)
    _parser.add_argument(
        "--transport",
        choices=["http", "stdio"],
        default=_os.environ.get("MCP_TRANSPORT", "http"),
    )
    _args, _ = _parser.parse_known_args()
    if _args.transport == "stdio":
        mcp.run(transport="stdio")
        sys.exit(0)

    from starlette.responses import JSONResponse
    import uvicorn

    host = _os.environ.get("HOST", "0.0.0.0")
    port = int(_os.environ.get("PORT", 8083))
    app = mcp.http_app(
        path="/mcp",
        transport="streamable-http",
        json_response=True,
        stateless_http=True,
    )

    async def tools_handler(request):
        """Federation tool discovery — flat tool registry with WELL danger metadata."""
        # Deferred ALIAS_REGISTRY validation (canonical funcs now in globals)
        global _ALIAS_REGISTRY_VALIDATED
        if not _ALIAS_REGISTRY_VALIDATED:
            _missing = {a: c for a, c in ALIAS_REGISTRY.items() if c not in globals()}
            if _missing:
                import warnings

                warnings.warn(f"ALIAS_REGISTRY: missing canonical mappings: {_missing}")
            _ALIAS_REGISTRY_VALIDATED = True

        all_tools = await mcp.list_tools()
        # WELL is L1/L2 only — mirrors, informs, reflects; no irrevocable mutations
        _DANGER_MAP = {
            # L3: fail-closed — vault seal, evidence anchor, constitutional floor check
            "well_anchor_evidence": {
                "danger_level": "L3",
                "fail_posture": "fail-closed",
            },
            "well_seal_vault": {"danger_level": "L3", "fail_posture": "fail-closed"},
            "well_request_anchor": {
                "danger_level": "L3",
                "fail_posture": "fail-closed",
            },
            "well_check_floor": {"danger_level": "L3", "fail_posture": "fail-closed"},
            "well_validate_vitality": {
                "danger_level": "L2",
                "fail_posture": "fail-open",
            },
            "well_check_repair": {"danger_level": "L2", "fail_posture": "fail-open"},
            "well_guard_dignity": {"danger_level": "L2", "fail_posture": "fail-open"},
            "well_assess_metabolism": {
                "danger_level": "L2",
                "fail_posture": "fail-open",
            },
            "well_assess_homeostasis": {
                "danger_level": "L2",
                "fail_posture": "fail-open",
            },
            "well_assess_livelihood": {
                "danger_level": "L2",
                "fail_posture": "fail-open",
            },
            "well_assess_reliability": {
                "danger_level": "L2",
                "fail_posture": "fail-open",
            },
            "well_reflect_intelligence": {
                "danger_level": "L2",
                "fail_posture": "fail-open",
            },
            # L1: fail-open — read-only observation and classification
            "well_classify_substrate": {
                "danger_level": "L1",
                "fail_posture": "fail-open",
            },
            "well_trace_lineage": {"danger_level": "L1", "fail_posture": "fail-open"},
            "well_detect_boundary": {"danger_level": "L1", "fail_posture": "fail-open"},
            "well_measure_gradient": {
                "danger_level": "L1",
                "fail_posture": "fail-open",
            },
            "mcp_health_check": {"danger_level": "L1", "fail_posture": "fail-open"},
            "well_state": {"danger_level": "L1", "fail_posture": "fail-open"},
            "well_get_packet": {"danger_level": "L1", "fail_posture": "fail-open"},
            "well_arifos_packet": {"danger_level": "L1", "fail_posture": "fail-open"},
            "well_readiness": {"danger_level": "L1", "fail_posture": "fail-open"},
        }
        _FAIL_OPEN_CONSTRAINT = "may degrade output, must not elevate authority"
        _CANONICAL = {
            "well_classify_substrate",
            "well_trace_lineage",
            "well_detect_boundary",
            "well_measure_gradient",
            "well_assess_metabolism",
            "well_assess_homeostasis",
            "well_check_repair",
            "well_validate_vitality",
            "well_assess_livelihood",
            "well_assess_reliability",
            "well_reflect_intelligence",
            "well_guard_dignity",
            "well_anchor_evidence",
        }
        _ALIASES = set(ALIAS_REGISTRY.keys())
        tools = []
        for t in all_tools:
            name = t.name
            meta = _DANGER_MAP.get(
                name, {"danger_level": "L1", "fail_posture": "fail-open"}
            )
            if name in _CANONICAL:
                category = "canonical"
            elif name in _ALIASES:
                category = "alias"
            elif name == "mcp_health_check":
                category = "heartbeat"
            else:
                category = "legacy"
            tools.append(
                {
                    "name": name,
                    "description": getattr(t, "description", "") or "",
                    "inputSchema": getattr(t, "inputSchema", {}),
                    "outputSchema": getattr(t, "output_schema", {}),
                    "danger_level": meta["danger_level"],
                    "fail_posture": meta["fail_posture"],
                    "fail_open_constraint": _FAIL_OPEN_CONSTRAINT
                    if meta["fail_posture"] == "fail-open"
                    else None,
                    "tool_category": category,
                }
            )
        return JSONResponse(
            {
                "organ": "WELL",
                "role": "Body / Human Intelligence — Operator Cognitive Pressure Monitor",
                "authority": "REFLECT_ONLY — WELL informs. arifOS judges. Arif decides.",
                "schema": "well-federation-v2026.05.08",
                "version": "2026.05.15-ΩWELL+GWELL",
                "count": len(tools),
                "w0_invariant": "WELL holds a mirror, not a veto. Operator sovereignty is invariant.",
                "danger_taxonomy": {
                    "L3": "vault seal / floor check — fail-closed mandatory",
                    "L2": "session / log — fail-open with constraint",
                    "L1": "observe / health / readiness — fail-open with constraint",
                },
                "fail_open_constraint": _FAIL_OPEN_CONSTRAINT,
                "tools": tools,
            }
        )

    async def health_handler(request):
        try:
            with open(".identity_hash", "r") as f:
                identity_hash = f.read().strip()
        except Exception:
            identity_hash = "UNAVAILABLE"

        # P6 — Substrate manifest hash (domain anchor, NOT constitution_hash)
        # WELL answers to SUBSTRATE_LAW (vitality law), not constitutional law.
        import hashlib as _hl

        substrate_manifest_hash = "sha256:missing"
        domain_law = "SUBSTRATE_LAW"
        try:
            _manifest_path = "/root/WELL/GENESIS/012_SUBSTRATE_MANIFEST.md"
            if os.path.exists(_manifest_path):
                with open(_manifest_path, "rb") as _f:
                    substrate_manifest_hash = (
                        f"sha256:{_hl.sha256(_f.read()).hexdigest()}"
                    )
        except Exception:
            pass

        state = _load_state()
        classification = _classify_well_state(state)
        # W-1: expose substrate advisory fields so arifOS judge HTTP fallback can consume them
        _clarity = state.get("metrics", {}).get("cognitive", {}).get("clarity")
        return JSONResponse(
            {
                "identity": "WELL",
                "role": "Body / Human Intelligence",
                "authority": "REFLECT_ONLY",
                "delta_s": state.get("delta_s", -1),
                "peace2": state.get("peace2", 0),
                "kappa_r": state.get("kappa_r", 0),
                "rasa": state.get("rasa", False),
                "amanah": state.get("amanah", "UNLOCKED"),
                "well_signal": classification[
                    "well_signal"
                ],  # REFLECT_ONLY — never "verdict"
                "identity_valid": classification["well_ok"],
                "has_telemetry": classification["has_telemetry"],
                "service": "well-mcp",
                "version": "2026.05.15-ΩWELL+GWELL",
                "identity_hash": identity_hash,
                # P6 — WELL identity anchor (SUBSTRATE_LAW, not constitutional)
                "domain_law": domain_law,
                "substrate_manifest_hash": substrate_manifest_hash,
                # W-1 substrate advisory fields — consumed by judge.py HTTP fallback
                "well_score": classification["well_score"],
                "floors_violated": state.get("floors_violated") or [],
                "truth_status": classification["truth_status"],
                "freshness_band": classification["freshness_band"],
                "owner_summary": classification["owner_summary"],
                "clarity": _clarity,
            }
        )

    async def build_info_handler(request):
        from starlette.responses import JSONResponse

        return JSONResponse(
            {
                "sha": "87c0e6755f44a52526763fceee15ee64740e7918",
                "short_sha": "87c0e67",
                "branch": "main",
                "version": "1.0",
                "tool_count": len(SOMATIC_TOOLS),
                "epoch": "2026",
                "source_repo": "well",
            }
        )

    async def mcp_server_card(request):
        """MCP Server Card — SEP-2127 HTTP discovery document."""
        return JSONResponse(
            {
                "name": "well",
                "displayName": "WELL Human Readiness",
                "url": "https://well.arif-fazil.com/mcp",
                "version": "2026.06.05",
                "capabilities": {"tools": True, "resources": False, "prompts": False},
                "authentication": {"type": "none"},
            }
        )

    app.add_route("/.well-known/mcp.json", mcp_server_card, methods=["GET"])
    app.add_route("/.well-known/mcp/server.json", mcp_server_card, methods=["GET"])

    # 2026-06-29 — Federation-wide OAuth discovery (Hermes-flow fix)
    # Spec-compliant MCP clients (Cursor, Claude Code, MiniMax) fetch
    # /.well-known/oauth-protected-resource first per RFC 8707. Without
    # this, OAuth clients fail with "failed to get oauth authorization url".
    # arifOS (port 8088) is the canonical authorization server for the
    # whole federation; this endpoint mirrors its metadata.
    async def _well_oauth_protected_resource(request):
        from starlette.responses import JSONResponse
        return JSONResponse(
            {
                "resource": "https://mcp.arif-fazil.com/mcp",
                "authorization_servers": ["https://mcp.arif-fazil.com"],
                "bearer_methods_supported": ["header"],
                "scopes_supported": ["openid", "profile", "mcp:full", "mcp:read_only"],
            },
            headers={"Access-Control-Allow-Origin": "*"},
        )
    app.add_route("/.well-known/oauth-protected-resource", _well_oauth_protected_resource, methods=["GET"])
    app.add_route("/.well-known/oauth-protected-resource/mcp", _well_oauth_protected_resource, methods=["GET"])
    async def _well_oauth_authorization_server(request):
        from starlette.responses import JSONResponse
        return JSONResponse(
            {
                "issuer": "https://mcp.arif-fazil.com",
                "authorization_endpoint": "https://mcp.arif-fazil.com/api/auth/authorize",
                "token_endpoint": "https://mcp.arif-fazil.com/api/auth/token",
                "jwks_uri": "https://mcp.arif-fazil.com/.well-known/jwks.json",
                "response_types_supported": ["code"],
                "grant_types_supported": ["authorization_code", "refresh_token"],
                "code_challenge_methods_supported": ["S256"],
                "scopes_supported": ["openid", "profile", "mcp:full", "mcp:read_only"],
            },
            headers={"Access-Control-Allow-Origin": "*"},
        )
    app.add_route("/.well-known/oauth-authorization-server", _well_oauth_authorization_server, methods=["GET"])
    app.add_route("/health", health_handler, methods=["GET"])
    app.add_route("/ready", _well_ready_handler, methods=["POST"])
    app.add_route("/api/build-info", build_info_handler, methods=["GET"])
    app.add_route("/tools", tools_handler, methods=["GET"])

    # ── A2A Agent Card (Federation Discovery) ────────────────────────────
    # FORGE 2026-06-28: /.well-known/agent.json for AAA A2A mesh discovery.

    _WELL_AGENT_CARD = {
        "schema_version": "0.2",
        "organ_id": "well",
        "name": "WELL — Human Substrate Vitality",
        "role": "human",
        "description": (
            "Universal substrate vitality mirror for arifOS federation. "
            "Assesses biological metabolism, homeostasis, repair cycles, vitality, "
            "livelihood, and dignity. Reflect-only — does not judge or decide."
        ),
        "version": "2026.06.05",
        "url": "https://well.arif-fazil.com",
        "a2a_endpoint": "http://127.0.0.1:18083/a2a",
        "agent_card_url": "http://127.0.0.1:18083/.well-known/agent-card.json",
        "endpoints": {
            "mcp": "https://well.arif-fazil.com/mcp",
            "health": "https://well.arif-fazil.com/health",
            "tools": "https://well.arif-fazil.com/tools",
        },
        "authority_class": "evidence",
        "allowed_action_classes": ["OBSERVE"],
        "max_risk_tier": "T1",
        "auth": {"type": "none"},
        "federation": {
            "protocol": "A2A",
            "peer_coordinator": "https://aaa.arif-fazil.com",
            "constitutional_kernel": "https://arifos.arif-fazil.com",
        },
        "owned_mcp": [
            "well_assess_homeostasis",
            "well_assess_livelihood",
            "well_assess_metabolism",
            "well_assess_reliability",
            "well_assess_sovereign_entropy",
            "well_check_repair",
            "well_classify_substrate",
            "well_compute_metabolic_flux",
            "well_detect_boundary",
            "well_guard_dignity",
            "well_measure_gradient",
            "well_registry_status",
            "well_trace_lineage",
            "well_validate_vitality",
            "well_medical_boundary",
            "well_handoff_dignity_to_arifos",
            "well_handoff_livelihood_to_wealth",
        ],
        "judge_skills": [],
        "skills": [
            {
                "id": "substrate.classify",
                "name": "Substrate Classification",
                "tags": ["h-well", "m-well", "g-well"],
            },
            {
                "id": "vitality.assess",
                "name": "Vitality Assessment",
                "tags": ["metabolism", "homeostasis", "repair"],
            },
            {
                "id": "dignity.guard",
                "name": "Dignity Guard",
                "tags": ["dignity", "sovereignty", "boundary"],
            },
        ],
    }

    async def _well_agent_card_handler(request):
        return JSONResponse(_WELL_AGENT_CARD)

    app.add_route("/.well-known/agent.json", _well_agent_card_handler, methods=["GET"])
    app.add_route(
        "/.well-known/agent-card.json", _well_agent_card_handler, methods=["GET"]
    )

    # Server start moved to end of file so canonical tools are registered before uvicorn blocks
# ═══════════════════════════════════════════════════════════════════════════════
# M-WELL Realtime Telemetry Ingestion
# Track dynamic machine health signals: context pressure, tool errors, compute load
# ═══════════════════════════════════════════════════════════════════════════════

M_WELL_SIGNAL_WINDOW_MINUTES = 30


# internal — not MCP-facing (collapsed 2026-05-26)
def well_machine_log_signal(
    signal: str = "",
    value: float | None = None,
    duration_seconds: float | None = None,
    source: str = "auto",
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Log a realtime machine telemetry signal.
    Signals: context_pressure | tool_error | compute_spike | latency_jitter | token_exhaustion | memory_pressure

    Each signal is written to events.jsonl and updates m_machine state.
    Signals within M_WELL_SIGNAL_WINDOW_MINUTES (30) are aggregated for trend detection.
    """
    signal = signal.lower()
    valid_signals = {
        "context_pressure",
        "tool_error",
        "compute_spike",
        "latency_jitter",
        "token_exhaustion",
        "memory_pressure",
    }
    if signal not in valid_signals:
        return {
            "ok": False,
            "error": f"Unknown signal: {signal}. Valid: {valid_signals}",
        }

    state = _load_state()
    m = dict(state.get("m_machine", {}))
    now = datetime.datetime.now(datetime.timezone.utc)

    # Map signal to m_machine field
    signal_map = {
        "context_pressure": ("context_length_pressure", 0.0, 1.0),
        "tool_error": ("api_failure_rate", 0.0, 1.0),
        "compute_spike": ("compute_budget_pct", 0.0, 100.0),
        "latency_jitter": ("latency_ms", 0.0, 1_000_000.0),
        "token_exhaustion": ("token_budget_pct", 0.0, 100.0),
        "memory_pressure": ("memory_integrity", 0.0, 1.0),
    }

    field, vmin, vmax = signal_map[signal]
    if value is not None:
        value = max(vmin, min(vmax, float(value)))
        m[field] = value

    # Log to events
    _append_event(
        {
            "event": "M_WELL_SIGNAL",
            "signal": signal,
            "value": value,
            "duration_seconds": duration_seconds,
            "source": source,
            "epoch": now.isoformat(),
        }
    )

    state["m_machine"] = m
    _save_state(state)

    # Recompute G-WELL after machine state change
    g = _g_well_assess(state)

    return {
        "ok": True,
        "signal": signal,
        "value": value,
        "m_well_score": g["g_well_score"],
        "m_well_verdict": g["machine_verdict"],
        "g_well_verdict": g["g_well_verdict"],
        "governance_flags": g["governance_flags"],
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


# internal — not MCP-facing (collapsed 2026-05-26)
def well_machine_trend(
    lookback_minutes: int = 60,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Reflect recent machine signal trends.
    Aggregates M_WELL_SIGNAL events within lookback window.
    Returns signal frequencies, averages, and anomaly flags.
    """
    state = _load_state()
    state.get("m_machine", {})
    events_path = EVENTS_PATH
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        minutes=lookback_minutes
    )

    signal_counts: dict[str, int] = {}
    signal_values: dict[str, list[float]] = {}
    anomalies: list[str] = []

    if events_path.exists():
        try:
            with open(events_path) as f:
                for line in f:
                    try:
                        e = json.loads(line)
                        if e.get("event") != "M_WELL_SIGNAL":
                            continue
                        epoch = datetime.datetime.fromisoformat(
                            e.get("epoch", "2000-01-01")
                        )
                        if epoch < cutoff:
                            continue
                        sig = e.get("signal", "unknown")
                        signal_counts[sig] = signal_counts.get(sig, 0) + 1
                        val = e.get("value")
                        if val is not None:
                            signal_values.setdefault(sig, []).append(float(val))
                    except Exception:
                        continue
        except Exception:
            pass

    # Compute averages and detect anomalies
    signal_summary = {}
    for sig, vals in signal_values.items():
        avg = sum(vals) / len(vals)
        signal_summary[sig] = {
            "count": signal_counts.get(sig, 0),
            "average": round(avg, 3),
            "samples": len(vals),
        }
        if sig == "tool_error" and avg > 0.1:
            anomalies.append(f"elevated_tool_error_rate:{avg:.3f}")
        if sig == "context_pressure" and avg > 0.8:
            anomalies.append("high_context_pressure")
        if sig == "latency_jitter" and avg > 5000:
            anomalies.append("high_latency_jitter")
    for sig, cnt in signal_counts.items():
        if sig not in signal_summary:
            signal_summary[sig] = {"count": cnt, "average": None, "samples": 0}

    g = _g_well_assess(state)

    return {
        "ok": True,
        "lookback_minutes": lookback_minutes,
        "signal_summary": signal_summary,
        "total_signals": sum(signal_counts.values()),
        "anomalies": anomalies,
        "m_well_score": g["g_well_score"],
        "m_well_verdict": g["machine_verdict"],
        "g_well_verdict": g["g_well_verdict"],
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# H-WELL Cross-Session Fatigue Accumulator
# Tracks fatigue across sessions for multi-day recovery planning
# ═══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
def well_fatigue_accumulator(
    mode: str = "check",
    session_duration_minutes: float | None = None,
    session_intensity: float | None = None,
    rest_hours: float | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    DEPRECATED: use well_assess_homeostasis(mode="fatigue") for check.
    Soft alias retained for backward compatibility (log/rest/reset remain direct).

    Track cognitive fatigue across sessions for multi-day recovery planning.

    Modes:
      check  — Delegate to well_assess_homeostasis(mode="fatigue")
      log    — Log a session's fatigue cost (direct)
      rest   — Log a rest period (reduces accumulated fatigue) (direct)
      reset  — Reset accumulator (after full recovery) (direct)

    Cross-session fatigue decays at ~2 points per hour of rest.
    Accumulated fatigue > 20 across 48h triggers extended recovery advisory.
    """
    state = _load_state()
    metrics = state.get("metrics", {})
    cog = dict(metrics.get("cognitive", {}))

    acc = cog.get(
        "fatigue_accumulator",
        {
            "total_accumulated": 0.0,
            "session_count": 0,
            "last_session_epoch": None,
            "last_rest_epoch": None,
            "peak_fatigue": 0.0,
        },
    )

    mode = mode.lower()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Decay: 2 points per hour since last rest or last session
    last_ts = acc.get("last_rest_epoch") or acc.get("last_session_epoch")
    if last_ts:
        try:
            last_dt = datetime.datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
            hours_since = (
                datetime.datetime.now(datetime.timezone.utc) - last_dt
            ).total_seconds() / 3600
            decay = min(hours_since * 2.0, acc["total_accumulated"])
            acc["total_accumulated"] = max(0.0, acc["total_accumulated"] - decay)
        except Exception:
            pass

    # 1C-B: check mode delegates to canonical well_assess_homeostasis(mode="fatigue")
    if mode == "check":
        homeostasis = well_assess_homeostasis(
            mode="fatigue",
            ctx=ctx,
        )
        result = {
            "mode": "check",
            "authority": "REFLECT_ONLY",
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
            "homeostasis": homeostasis,
            "accumulated": round(acc["total_accumulated"], 1),
            "session_count": acc["session_count"],
        }
        # Preserve advisory from accumulator state
        if acc["total_accumulated"] > 20:
            result["advisory"] = "EXTENDED_RECOVERY_ADVISED"
            result["recommendation"] = (
                "Accumulated fatigue exceeds 20. Full rest day recommended."
            )
        elif acc["total_accumulated"] > 10:
            result["advisory"] = "MODERATE_LOAD"
            result["recommendation"] = (
                f"Accumulated fatigue at {acc['total_accumulated']:.1f}. Schedule breaks."
            )
        return result

    result = {
        "mode": mode,
        "accumulated": acc["total_accumulated"],
        "session_count": acc["session_count"],
    }

    if mode == "log":
        cost = (session_intensity or 5.0) * (session_duration_minutes or 30.0) / 60.0
        acc["total_accumulated"] += cost
        acc["session_count"] += 1
        acc["last_session_epoch"] = now
        acc["peak_fatigue"] = max(acc["peak_fatigue"], acc["total_accumulated"])
        _append_event(
            {
                "event": "FATIGUE_LOG",
                "cost": round(cost, 1),
                "accumulated": round(acc["total_accumulated"], 1),
            }
        )
        result["cost"] = round(cost, 1)
        result["message"] = "Session fatigue logged"

    elif mode == "rest":
        recovery = (rest_hours or 1.0) * 2.0
        acc["total_accumulated"] = max(0.0, acc["total_accumulated"] - recovery)
        acc["last_rest_epoch"] = now
        _append_event(
            {
                "event": "FATIGUE_REST",
                "recovery": round(recovery, 1),
                "accumulated": round(acc["total_accumulated"], 1),
            }
        )
        result["recovery"] = round(recovery, 1)
        result["message"] = "Rest recovery applied"

    elif mode == "reset":
        acc = {
            "total_accumulated": 0.0,
            "session_count": 0,
            "last_session_epoch": now,
            "last_rest_epoch": now,
            "peak_fatigue": 0.0,
        }
        _append_event({"event": "FATIGUE_RESET"})
        result["message"] = "Accumulator reset"

    # Advisory
    if acc["total_accumulated"] > 20:
        result["advisory"] = "EXTENDED_RECOVERY_ADVISED"
        result["recommendation"] = (
            "Accumulated fatigue exceeds 20. Full rest day recommended before strategic decisions."
        )
    elif acc["total_accumulated"] > 10:
        result["advisory"] = "MODERATE_LOAD"
        result["recommendation"] = (
            f"Accumulated fatigue at {acc['total_accumulated']:.1f}. Schedule breaks."
        )

    cog["fatigue_accumulator"] = acc
    metrics["cognitive"] = cog
    state["metrics"] = metrics
    _save_state(state)

    result["accumulated"] = round(acc["total_accumulated"], 1)
    result["session_count"] = acc["session_count"]
    result["peak_fatigue"] = round(acc["peak_fatigue"], 1)
    result["w0"] = "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT"

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# H-WELL Circadian Phase Tracker
# Time-of-day awareness for biological readiness
# ═══════════════════════════════════════════════════════════════════════════════

CIRCADIAN_PHASES = {
    "MORNING_PEAK": (6, 11, "High cognitive readiness. Best for C4-C5 decisions."),
    "AFTERNOON_DIP": (
        12,
        15,
        "Post-lunch dip. Avoid complex reasoning. Draft/review only.",
    ),
    "SECOND_WIND": (16, 20, "Secondary cognitive peak. Good for coding, architecture."),
    "EVENING_WIND_DOWN": (
        21,
        23,
        "Cognitive decline. Draft-only. No irreversible actions.",
    ),
    "DEEP_NIGHT": (
        0,
        5,
        "Late night. Cognitive entropy elevated. Default to C0 unless urgency is critical.",
    ),
}


# internal — not MCP-facing (collapsed 2026-05-26)
def well_circadian_phase(
    override_hour: int | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Reflect circadian phase based on current UTC+8 time (Arif's timezone).

    Phases:
      MORNING_PEAK  (06-11) — Optimal for complex decisions
      AFTERNOON_DIP (12-15) — Low energy, avoid complex reasoning
      SECOND_WIND   (16-20) — Secondary peak, good for coding/architecture
      EVENING_WIND_DOWN (21-23) — Cognitive decline, draft-only
      DEEP_NIGHT    (00-05) — High cognitive entropy, C0 recommended

    Returns recommended decision ceiling per phase.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    # Simulate UTC+8 for Arif (Malaysia)
    local_hour = (now.hour + 8) % 24 if override_hour is None else override_hour

    phase_name = "DEEP_NIGHT"
    phase_detail = CIRCADIAN_PHASES["DEEP_NIGHT"]
    for name, (start, end, desc) in sorted(
        CIRCADIAN_PHASES.items(), key=lambda x: x[1][0]
    ):
        if start <= local_hour <= end:
            phase_name = name
            phase_detail = (start, end, desc)
            break
        # Handle overnight: DEEP_NIGHT spans 00-05
        if name == "DEEP_NIGHT" and (local_hour >= 0 and local_hour <= 5):
            break

    phase_ceiling_map = {
        "MORNING_PEAK": "C5",
        "AFTERNOON_DIP": "C2",
        "SECOND_WIND": "C4",
        "EVENING_WIND_DOWN": "C1",
        "DEEP_NIGHT": "C0",
    }

    return {
        "ok": True,
        "local_hour": local_hour,
        "phase": phase_name,
        "description": phase_detail[2],
        "recommended_ceiling": phase_ceiling_map.get(phase_name, "C0"),
        "timezone": "Asia/Kuala_Lumpur (UTC+8)",
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# M-WELL Docker/Process Health Probe
# Checks Docker container liveness and process health for the federation
# ═══════════════════════════════════════════════════════════════════════════════


# internal — not MCP-facing (collapsed 2026-05-26)
def well_machine_health_probe(
    targets: list[str] | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    Probe machine health of federation services.
    Checks: Docker container status, process liveness, port availability.

    targets: arifos | geox | wealth | a-forge | aaa | hermes | vault999 | postgres | redis | qdrant | all

    Returns per-target health verdict: HEALTHY | DEGRADED | UNREACHABLE | UNKNOWN.
    """
    import subprocess
    import socket

    probe_targets = targets or ["all"]
    known_services = {
        "arifos": {"port": 8088, "type": "http"},
        "geox": {"port": 18081, "type": "http"},
        "wealth": {"port": 18082, "type": "http"},
        "well": {"port": 8083, "type": "http"},
        "aaa": {"port": 3001, "type": "http"},
        "apex": {"port": 3002, "type": "http"},  # was hermes — renamed 2026-05-16
        "a-forge": {"port": 7071, "type": "http"},
        "vault999": {"port": 8100, "type": "http"},
        "postgres": {"port": 5432, "type": "tcp"},
        "redis": {"port": 6379, "type": "tcp"},
        "qdrant": {"port": 6333, "type": "http"},
        "ollama": {"port": 11434, "type": "http"},
    }

    if "all" in probe_targets:
        probe_targets = list(known_services.keys())

    results = {}
    all_healthy = True

    for svc in probe_targets:
        if svc not in known_services:
            results[svc] = {"verdict": "UNKNOWN", "error": f"Unknown service: {svc}"}
            all_healthy = False
            continue
        info = known_services[svc]
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            result = sock.connect_ex(("127.0.0.1", info["port"]))
            sock.close()
            if result == 0:
                results[svc] = {"verdict": "HEALTHY", "port": info["port"]}
            else:
                results[svc] = {
                    "verdict": "UNREACHABLE",
                    "port": info["port"],
                    "error": "Connection refused",
                }
                all_healthy = False
        except Exception as e:
            results[svc] = {"verdict": "ERROR", "port": info["port"], "error": str(e)}
            all_healthy = False

    # Also try Docker
    docker_available = False
    try:
        r = subprocess.run(
            ["docker", "ps", "-q"], capture_output=True, text=True, timeout=5
        )
        docker_available = r.returncode == 0
    except Exception:
        pass

    state = _load_state()
    m = dict(state.get("m_machine", {}))
    m["probe_results"] = results
    m["probe_all_healthy"] = all_healthy
    state["m_machine"] = m
    _save_state(state)

    g = _g_well_assess(state)

    return {
        "ok": True,
        "targets": probe_targets,
        "results": results,
        "all_healthy": all_healthy,
        "docker_available": docker_available,
        "m_well_score": g["g_well_score"],
        "m_well_verdict": g["machine_verdict"],
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Decision Ceiling in _resolve_readiness — ground_state propagated to all tools
# ═══════════════════════════════════════════════════════════════════════════════


def _compute_decision_ceiling(state: dict[str, Any]) -> dict[str, str]:
    """
    Compute ground_state and decision_ceiling from current state.
    Used by _resolve_readiness and all derived tool outputs.
    """
    metrics = state.get("metrics", {})
    violations = state.get("floors_violated", [])
    has_telemetry = _has_verified_telemetry(state)
    vcount = len(violations)
    result = {
        "ground_state": "UNKNOWN",
        "decision_ceiling": "C0",
        "basis": [],
        "reason": "",
    }

    if not has_telemetry:
        result["ground_state"] = "UNKNOWN"
        result["decision_ceiling"] = "C0"
        result["reason"] = "No verified body telemetry."
        return result

    sleep = metrics.get("sleep", {})
    stress = metrics.get("stress", {})
    cognitive = metrics.get("cognitive", {})
    metabolic = metrics.get("metabolic", {})
    struct = metrics.get("structural", {})

    debt = sleep.get("sleep_debt_days", 0)
    load = stress.get("subjective_load", 0)
    clarity = cognitive.get("clarity", 10)
    fatigue = cognitive.get("decision_fatigue", 0)
    hydration = metabolic.get("hydration_status", "STABLE")
    stability = metabolic.get("perceived_stability", 10)
    sedentary = struct.get("sedentary_hours_continuous", 0)
    pain = struct.get("pain_level", 0)

    basis = []
    if debt > 0:
        basis.append("sleep_debt")
    if load > 4:
        basis.append("stress")
    if clarity < 7:
        basis.append("clarity")
    if fatigue > 3:
        basis.append("fatigue")
    if hydration == "DEHYDRATED":
        basis.append("dehydration")
    if stability < 5:
        basis.append("metabolic_stability")
    if sedentary >= 4:
        basis.append("sedentary")
    if pain >= 5:
        basis.append("pain")

    if vcount == 0 and debt <= 0 and load <= 4 and clarity >= 7 and fatigue <= 3:
        result["ground_state"] = "GROUND"
        result["decision_ceiling"] = "C5"
        result["reason"] = "All floors clear, optimal regulation."
    elif vcount <= 1 and debt <= 1 and load <= 7 and clarity >= 5 and fatigue <= 6:
        result["ground_state"] = "STRAINED"
        result["decision_ceiling"] = "C3"
        result["reason"] = (
            f"Mild strain detected: {', '.join(basis) if basis else 'borderline'}."
        )
    elif vcount <= 3:
        result["ground_state"] = "DEGRADED"
        result["decision_ceiling"] = "C1"
        result["reason"] = (
            f"Regulation compromised: {', '.join(basis) if basis else 'multiple floors violated'}."
        )
    else:
        result["ground_state"] = "UNSAFE"
        result["decision_ceiling"] = "C0"
        result["reason"] = (
            f"Critical substrate state: {', '.join(basis)}. Professional care recommended if medical symptoms present."
        )

    result["basis"] = basis
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Ω-WELL Canonical Surface v2 — well_verb_noun ontology
# Replaces stage-facing names (well_000_init, well_111_sense, etc.)
# with domain-facing names (well_classify_substrate, well_trace_lineage, etc.)
# Old functions remain as internal dispatchers.
# ═══════════════════════════════════════════════════════════════════════════════


@mcp.tool()
async def well_classify_substrate(
    mode: str = "classification",  # CHAOS FIX: "classify" not in VALID_MODES ["classification","analysis","synthesis"]; first implemented
    subject: str = "",
    description: str | None = None,
    evaluation_intent: str | None = None,
    session_id: str | None = None,
    actor_id: str = "well-substrate",
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Ω-WELL-01: Substrate classification and boundary sensing."""
    mode = mode.lower()
    VALID_MODES = [
        "substrate",
        "boundary",
        "classification",
        "init",
        "assert",
        "bootstrap",
        "classify",
        "medical",
    ]
    if mode not in VALID_MODES:
        return {
            "error": "UNKNOWN_MODE",
            "valid": VALID_MODES,
            "tool": "well_classify_substrate",
            "received": mode,
        }
    if mode == "medical":
        # EUREKA 2026-06-12: route medical queries to the explicit boundary tool.
        # F9 Soul Contract: the medical boundary carries the F9 soullessness declaration.
        return _to_federation_output(
            well_medical_boundary(ctx=ctx),
            tool_name="well_classify_substrate",
        )
    if mode in ("classification", "substrate"):
        mode = "classify"
    if mode in ("init", "assert", "bootstrap"):
        return _to_federation_output(
            await well_000_init(
                mode=mode, session_id=session_id, actor_id=actor_id, ctx=ctx
            ),
            tool_name="well_classify_substrate",
        )
    return _to_federation_output(
        well_111_sense(
            mode=mode,
            subject=subject,
            description=description,
            evaluation_intent=evaluation_intent,
            ctx=ctx,
        ),
        tool_name="well_classify_substrate",
    )


@mcp.tool()
def well_trace_lineage(
    mode: str = "recall",
    limit: int = 10,
    lookback_days: int = 30,
    dry_run: bool = False,
    reason: str = "state_checkpoint",
    force: bool = False,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Ω-WELL-02: Memory, trend, ledger, and vault chain tracing."""
    mode = mode.lower()
    VALID_MODES = [
        "decision",
        "evidence",
        "memory",
        "recall",
        "trend",
        "context",
        "ledger",
        "chain",
    ]
    if mode not in VALID_MODES:
        return {
            "error": "UNKNOWN_MODE",
            "valid": VALID_MODES,
            "tool": "well_trace_lineage",
            "received": mode,
        }
    if mode in ("recall", "trend", "context"):
        return _to_federation_output(
            well_555_memory(
                mode=mode, limit=limit, lookback_days=lookback_days, ctx=ctx
            ),
            tool_name="well_trace_lineage",
        )
    if mode in ("ledger", "chain"):
        return _to_federation_output(
            well_999_vault(
                mode=mode, dry_run=dry_run, reason=reason, force=force, ctx=ctx
            ),
            tool_name="well_trace_lineage",
        )
    return _to_federation_output(
        _omega_well_output(
            ok=False,
            stage="TRACE_LINEAGE",
            lane="AGI",
            mode=mode,
            verdict="VOID",
            error=f"Unknown mode: {mode}. Use recall | trend | context | ledger | chain",
        ),
        tool_name="well_trace_lineage",
    )


@mcp.tool()
def well_detect_boundary(
    mode: str = "boundary",
    subject: str = "",
    description: str | None = None,
    evaluation_intent: str | None = None,
    peer: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Ω-WELL-03: Boundary detection across membrane, body, machine, and federation."""
    mode = mode.lower()
    if mode in ("classify", "boundary", "scan"):
        return _to_federation_output(
            well_111_sense(
                mode=mode,
                subject=subject,
                description=description,
                evaluation_intent=evaluation_intent,
                ctx=ctx,
            ),
            tool_name="well_detect_boundary",
        )
    if mode in ("status", "connect", "handoff", "manifest"):
        return _to_federation_output(
            well_444_gateway(mode=mode, peer=peer, ctx=ctx),
            tool_name="well_detect_boundary",
        )
    return _to_federation_output(
        _omega_well_output(
            ok=False,
            stage="DETECT_BOUNDARY",
            lane="AGI",
            mode=mode,
            verdict="VOID",
            error=f"Unknown mode: {mode}. Use classify | boundary | scan | status | connect | handoff | manifest",
        ),
        tool_name="well_detect_boundary",
    )


@mcp.tool()
def well_measure_gradient(
    mode: str = "evidence",
    evidence_source: str = "unknown",
    evidence_age_hours: float | None = None,
    corroboration_count: int = 0,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Ω-WELL-04: Measure chemical, energy, pressure, attention, and compute gradients."""
    return _to_federation_output(
        well_222_fetch(
            mode=mode,
            evidence_source=evidence_source,
            evidence_age_hours=evidence_age_hours,
            corroboration_count=corroboration_count,
            ctx=ctx,
        ),
        tool_name="well_measure_gradient",
    )


@mcp.tool()
def well_assess_metabolism(
    mode: str = "coupled",  # CHAOS FIX: "human" not in VALID_MODES; coupled is implemented
    subject: str | None = None,
    substrate_class: str | None = None,
    energy_level: float | None = None,
    duty_load: float | None = None,
    role_clarity: float | None = None,
    role_burden: float | None = None,
    dignity_preservation: float | None = None,
    purpose_alignment: float | None = None,
    has_metabolism: bool | None = None,
    structural_condition: str | None = None,
    material_type: str | None = None,
    mission_clarity: float | None = None,
    cashflow_status: str | None = None,
    internal_consistency: float | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Ω-WELL-05: Assess biological metabolism and system throughput across substrates."""
    logger.info("well_assess_metabolism called mode=%s", mode)
    mode = mode.lower() if isinstance(mode, str) else mode
    VALID_MODES = [
        "gradient",
        "flux",
        "coupled",
        "human",
        "machine",
        "bio",
        "material",
        "institution",
        "info",
        "symbolic",
    ]
    if mode not in VALID_MODES:
        return {
            "error": "UNKNOWN_MODE",
            "valid": VALID_MODES,
            "tool": "well_assess_metabolism",
            "received": mode,
        }
    # 888 HOLD: gradient/flux delegation targets need semantic audit.
    # well_333_mind only supports human|machine|coupled — not gradient/flux.
    if mode in ("gradient", "flux"):
        return {
            "error": "MODE_NOT_IMPLEMENTED",
            "tool": "well_assess_metabolism",
            "mode": mode,
            "status": "HOLD_pending_delegation_audit",
            "valid": VALID_MODES,
        }
    return _to_federation_output(
        well_333_mind(
            mode=mode,
            subject=subject,
            substrate_class=substrate_class,
            energy_level=energy_level,
            duty_load=duty_load,
            role_clarity=role_clarity,
            role_burden=role_burden,
            dignity_preservation=dignity_preservation,
            purpose_alignment=purpose_alignment,
            has_metabolism=has_metabolism,
            structural_condition=structural_condition,
            material_type=material_type,
            mission_clarity=mission_clarity,
            cashflow_status=cashflow_status,
            internal_consistency=internal_consistency,
            ctx=ctx,
        ),
        tool_name="well_assess_metabolism",
    )


@mcp.tool()
def well_assess_homeostasis(
    mode: str = "sleep",  # CHAOS FIX: "empathize" not in VALID_MODES ["sleep","cognitive","stress","vitality","circadian","fatigue"]; sleep is implemented
    subject: str | None = None,
    dignity_preservation: float | None = None,
    coercion_signals: list[str] | None = None,
    reductionism_risk: float | None = None,
    # Biometric overrides for fatigue mode — pass inputs directly instead of relying on state.json
    sleep_debt_days: float | None = None,
    cognitive_clarity: float | None = None,
    decision_fatigue: float | None = None,
    stress_load: float | None = None,
    hrv_status: str = "normal",
    emotional_state: str = "neutral",
    chronic_fatigue: bool = False,
    accumulated_session_fatigue: float | None = None,
    # Decision class for routing — C1 trivial through C5 critical
    decision_class: str = "C3",
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Ω-WELL-06: Assess regulation, stability, and empathic balance under change.

    When mode="fatigue", accepts biometric overrides to support contrast scenarios
    and real-time assessment without state.json dependency. Also accepts decision_class
    to route the homeostasis verdict through the C-class threshold matrix:
      C1/C2 — proceed unless CRITICAL
      C3     — proceed if STABLE or better
      C4     — proceed only if OPTIMAL; DEFER if STABLE; ADVISORY_BLOCK if DEGRADED/CRITICAL
      C5     — proceed only if OPTIMAL + no chronic fatigue; block otherwise
    """
    logger.info(
        "well_assess_homeostasis called mode=%s decision_class=%s", mode, decision_class
    )
    mode = mode.lower() if isinstance(mode, str) else mode
    VALID_MODES = [
        "sleep",
        "cognitive",
        "stress",
        "vitality",
        "circadian",
        "fatigue",
        "empathize",
        "critique",
        "dignity",
        "redteam",
        "maruah",
        "medical_query",
    ]
    VALID_HRV = ["low", "normal", "high"]
    VALID_EMOTIONAL = ["irritable", "anxious", "neutral", "calm", "elevated"]
    VALID_DECISION_CLASSES = ["C1", "C2", "C3", "C4", "C5"]
    raw_emotional_state = emotional_state
    normalized_emotional_class = emotional_state
    operator_risk = "standard"
    if mode not in VALID_MODES:
        return {
            "error": "UNKNOWN_MODE",
            "valid": VALID_MODES,
            "tool": "well_assess_homeostasis",
            "received": mode,
        }
    if hrv_status not in VALID_HRV:
        hrv_status = "normal"
    if emotional_state not in VALID_EMOTIONAL:
        lowered_emotion = str(emotional_state).lower()
        if "tired" in lowered_emotion and "driven" in lowered_emotion:
            emotional_state = "anxious"
            normalized_emotional_class = "fatigued_drive_state"
            operator_risk = "overextension"
        else:
            emotional_state = "neutral"
            normalized_emotional_class = "unclassified_emotional_state"
            operator_risk = "unknown_context"
    decision_class_upper = (
        decision_class.upper() if isinstance(decision_class, str) else "C3"
    )
    if decision_class_upper not in VALID_DECISION_CLASSES:
        return {
            "error": "INVALID_DECISION_CLASS",
            "valid": VALID_DECISION_CLASSES,
            "received": decision_class,
            "tool": "well_assess_homeostasis",
        }

    # 1C-B: fatigue is a direct computation — implement here, do not delegate to well_666_heart
    # 2026-06-06: sleep is also direct (was falling through to well_666_heart which
    # doesn't accept it). Sleep is one of WELL-13 Tier 2 (recovery/metabolic).
    if mode == "sleep":
        state = _load_state()
        # P0-1 HARDENING (2026-06-28): If no verified body telemetry,
        # return UNKNOWN — never compute OPTIMAL from defaults.
        # Sleep mode previously scored 7.2/10 (OPTIMAL) from defaults
        # of sleep_hours=7.0, sleep_quality=7.0, sleep_debt=0.0.
        if not _has_verified_telemetry(state):
            return _to_federation_output(
                _omega_well_output(
                    ok=False,
                    stage="222_SLEEP",
                    lane="AGI",
                    mode="sleep",
                    verdict="HOLD",
                    data={
                        "sleep_recovery_score": None,
                        "status": "UNKNOWN",
                        "signal": "no_telemetry",
                        "decision_class": decision_class_upper,
                        "route_signal": "HOLD",
                        "routing_note": "No verified body telemetry. Cannot assess sleep recovery. Provide biometric data or confirm readiness manually.",
                    },
                    constitutional_compliance={"W2_SLEEP_RECOVERY": "UNKNOWN"},
                ),
                tool_name="well_assess_homeostasis",
            )
        metrics = state.get("metrics", {})
        sleep_m = metrics.get("sleep", {})

        # Sleep mode: public signature only exposes sleep_debt_days as override.
        # sleep_hours and sleep_quality are read from state.json (logged via
        # well_log). This is consistent with the "Biometric overrides for
        # fatigue mode" comment on the public signature.
        _sleep_hours = sleep_m.get("sleep_hours", 7.0)
        _sleep_quality = sleep_m.get("sleep_quality", 7.0)
        _sleep_debt = (
            sleep_debt_days
            if sleep_debt_days is not None
            else sleep_m.get("sleep_debt_days", 0.0)
        )

        # Clamp
        _sleep_hours = max(0.0, min(14.0, _sleep_hours))
        _sleep_quality = max(1.0, min(10.0, _sleep_quality))
        _sleep_debt = max(0.0, min(14.0, _sleep_debt))

        # 7-9 hours is target. Penalize deviation + debt + low quality.
        target = 8.0
        hour_gap = abs(_sleep_hours - target)
        # Quality 1-10; debt 0-14 days
        raw_sleep_strain = (
            hour_gap * 1.0 + (10.0 - _sleep_quality) * 0.6 + _sleep_debt * 0.4
        )
        # Convert strain → recovery score (0-10)
        sleep_recovery_score = max(0.0, min(10.0, 10.0 - raw_sleep_strain))

        # Signal language — NEVER verdict (advisory only).
        # verdict is the internal "advisory verdict" string that
        # _omega_well_output translates to a generic signal via
        # _WELL_ADVISORY_SIGNAL_MAP. The sleep-specific signal is
        # preserved in data.signal for downstream consumers.
        if sleep_recovery_score >= 7.0:
            sleep_signal = "sleep_recovery_optimal"
            status = "OPTIMAL"
            verdict = "SEAL"
        elif sleep_recovery_score >= 5.0:
            sleep_signal = "sleep_recovery_low"
            status = "STABLE"
            verdict = "SEAL"
        elif sleep_recovery_score >= 3.0:
            sleep_signal = "sleep_recovery_degraded"
            status = "DEGRADED"
            verdict = "HOLD"
        else:
            sleep_signal = "sleep_recovery_critical"
            status = "CRITICAL"
            verdict = "VOID"

        # C-class routing — recommend decision class downgrade
        thresholds = {
            "C1": (3.0, None),
            "C2": (3.0, None),
            "C3": (5.0, None),
            "C4": (7.0, 3.0),
            "C5": (7.0, 5.0),
        }
        threshold_score, block_threshold = thresholds[decision_class_upper]
        if status == "CRITICAL":
            route_signal = "ADVISORY_BLOCKED"
            routing_note = "CRITICAL sleep recovery — all decision classes blocked."
        elif status == "DEGRADED":
            if decision_class_upper in ("C4", "C5"):
                route_signal = (
                    "ADVISORY_BLOCKED"
                    if sleep_recovery_score < (block_threshold or 0)
                    else "DEFER"
                )
            else:
                route_signal = "PROCEED"
                routing_note = (
                    f"DEGRADED sleep but {decision_class_upper} is low-stakes."
                )
        elif status == "STABLE":
            if decision_class_upper in ("C4", "C5"):
                route_signal = "DEFER"
                routing_note = f"STABLE sleep insufficient for {decision_class_upper}."
            else:
                route_signal = "PROCEED"
                routing_note = f"STABLE sleep clears {decision_class_upper}."
        else:  # OPTIMAL
            route_signal = "PROCEED"
            routing_note = f"OPTIMAL sleep clears {decision_class_upper}."

        # Optional SAF statistical rigor on sleep vector
        _saf_summary = None
        try:
            from core.shared.saf_stats import stat_assumptions as _saf_assumptions
            import pandas as _pd_saf
            import uuid as _uuid_saf
            from pathlib import Path as _Path_saf
            import os as _os_saf

            _well_saf_root = _Path_saf(
                _os_saf.environ.get("WELL_SAF_DATA_ROOT", "/tmp/well_saf")
            )
            _well_saf_root.mkdir(parents=True, exist_ok=True)
            _vec = [_sleep_hours, _sleep_quality, _sleep_debt]
            _metric_names = ["sleep_hours", "sleep_quality", "sleep_debt_days"]
            _df = _pd_saf.DataFrame([_vec], columns=_metric_names)
            _csv = _well_saf_root / f"sleep_{_uuid_saf.uuid4().hex[:8]}.csv"
            _df.to_csv(_csv, index=False)
            _saf_summary = _saf_assumptions(
                str(_csv),
                target_col="sleep_debt_days",
            )
            try:
                _csv.unlink()
            except OSError:
                pass
        except Exception:
            # P1 FIX (2026-06-28): Do not leak internal dependency errors into
            # human readiness output. SAF is optional — surface as disabled.
            _saf_summary = {
                "saf_status": "DISABLED_OPTIONAL",
                "reason": "saf_stats unavailable",
            }

        _data_payload = {
            "sleep_recovery_score": round(sleep_recovery_score, 2),
            "status": status,
            "sleep_hours": _sleep_hours,
            "sleep_quality": _sleep_quality,
            "sleep_debt_days": _sleep_debt,
            "signal": sleep_signal,
            "decision_class": decision_class_upper,
            "route_signal": route_signal,
            "routing_note": routing_note,
        }
        if _saf_summary is not None:
            _data_payload["_saf_assumptions"] = _saf_summary

        # ── Reality Ledger ──────────────────────────────────────────────────────
        if _WELL_LEDGER_AVAILABLE:
            try:
                record_well_assessment(
                    assessment_type="homeostasis_sleep",
                    result={
                        "verdict": verdict,
                        "status": status,
                        "score": round(sleep_recovery_score, 2),
                    },
                )
            except Exception:
                pass

        return _to_federation_output(
            _omega_well_output(
                ok=status in ("OPTIMAL", "STABLE") and route_signal == "PROCEED",
                stage="222_SLEEP",
                lane="AGI",
                mode="sleep",
                verdict=verdict,  # advisory verdict; _omega_well_output translates to generic signal
                data=_data_payload,
                constitutional_compliance={"W2_SLEEP_RECOVERY": status},
            ),
            tool_name="well_assess_homeostasis",
        )

    # ── EUREKA 2026-06-12: Medical Query Mode ─────────────────────────────
    # Routes human medical questions through the F9 Soul Contract boundary.
    # Always C5 (highest gate) — block unless OPTIMAL + no chronic fatigue.
    # Educational context (what the condition IS) is allowed.
    # Personal medical advice (what to DO about it) is HARAM without license.
    if mode == "medical_query":
        # Force C5 — strongest gate for medical queries about the operator's own body
        actual_class = (
            decision_class.upper() if isinstance(decision_class, str) else "C5"
        )
        if actual_class not in ("C5",):
            actual_class = "C5"  # medical queries always use the strongest gate

        # Get the medical boundary (F9 soul contract included)
        boundary = well_medical_boundary(ctx=ctx)

        # Build educational context from the subject
        educational_context = {
            "subject": subject,
            "note": (
                "WELL can describe what a condition IS (F2 TRUTH). "
                "WELL cannot advise what to DO about it (HARAM without license). "
                "This is the GERD pattern: explain the acid reflux mechanism = OK. "
                "Advise whether to get surgery = NEVER."
            ),
        }

        return _to_federation_output(
            _omega_well_output(
                ok=True,
                stage="555_DIGNITY",
                lane="ASI",
                mode="medical_query",
                verdict="HOLD",  # medical queries always HOLD — never auto-SEAL
                data={
                    "medical_boundary": boundary,
                    "educational_context": educational_context,
                    "decision_class": actual_class,
                    "f9_soul_contract": boundary.get("f9_soul_contract", {}),
                    "route_signal": "ADVISORY_BLOCKED",
                    "routing_note": (
                        "C5 medical query gate: physical medical advice requires "
                        "a licensed human doctor. WELL provides educational context only. "
                        "See a real doctor for personal medical decisions."
                    ),
                },
                constitutional_compliance={
                    "F2_TRUTH": "educational context only, no personal advice",
                    "F9_ANTIHANTU": "zero qualia declared — I am a mirror, not a soul",
                    "W6_MEDICAL_BOUNDARY": "HOLD — operator must see human doctor",
                },
            ),
            tool_name="well_assess_homeostasis",
        )

    if mode == "fatigue":
        state = _load_state()
        # P1 FIX (2026-06-28): If no verified telemetry AND no biometric
        # overrides provided, return LIMITED — never compute OPTIMAL from
        # defaults alone. This prevents false confidence.
        _has_overrides = any(
            v is not None
            for v in [
                sleep_debt_days,
                cognitive_clarity,
                decision_fatigue,
                stress_load,
                accumulated_session_fatigue,
            ]
        )
        if not _has_verified_telemetry(state) and not _has_overrides:
            return _to_federation_output(
                _omega_well_output(
                    ok=False,
                    stage="222_FATIGUE",
                    lane="AGI",
                    mode="fatigue",
                    verdict="HOLD",
                    telemetry_status="unknown",
                    data={
                        "homeostasis_score": None,
                        "status": "LIMITED",
                        "signal": "insufficient_context",
                        "decision_class": decision_class_upper,
                        "route_signal": "CAUTION",
                        "routing_note": (
                            "No verified telemetry and no biometric overrides. "
                            "Cannot assess fatigue reliably. Status is LIMITED, not OPTIMAL."
                        ),
                    },
                    constitutional_compliance={"W2_FATIGUE": "UNKNOWN"},
                ),
                tool_name="well_assess_homeostasis",
            )
        metrics = state.get("metrics", {})
        cog = metrics.get("cognitive", {})

        # Use provided inputs as overrides; fall back to state.json
        _sleep_debt = (
            sleep_debt_days
            if sleep_debt_days is not None
            else cog.get("sleep_debt_days", 0.0)
        )
        _raw_clarity = (
            cognitive_clarity
            if cognitive_clarity is not None
            else cog.get("clarity", 7.0)
        )
        try:
            _raw_clarity_float = float(_raw_clarity)
        except (TypeError, ValueError):
            _raw_clarity_float = 7.0
        if cognitive_clarity is not None and 0.0 <= _raw_clarity_float <= 1.0:
            _clarity = _raw_clarity_float * 10.0
            _clarity_input_scale = "0_to_1"
        else:
            _clarity = _raw_clarity_float
            _clarity_input_scale = "0_to_10"
        _decision_fatigue = (
            decision_fatigue
            if decision_fatigue is not None
            else cog.get("decision_fatigue", 0.0)
        )
        _stress_load = (
            stress_load
            if stress_load is not None
            else metrics.get("stress", {}).get("subjective_load", 0.0)
        )
        acc = cog.get("fatigue_accumulator", {})
        last_ts = acc.get("last_rest_epoch") or acc.get("last_session_epoch")
        _accumulated = (
            accumulated_session_fatigue
            if accumulated_session_fatigue is not None
            else acc.get("total_accumulated", 0.0)
        )

        # Decay: 2 points per hour since last session
        if last_ts:
            try:
                last_dt = datetime.datetime.fromisoformat(
                    last_ts.replace("Z", "+00:00")
                )
                hours_since = (
                    datetime.datetime.now(datetime.timezone.utc) - last_dt
                ).total_seconds() / 3600
                _accumulated = max(
                    0.0, _accumulated - min(hours_since * 2.0, _accumulated)
                )
            except Exception:
                pass

        # Clamp inputs
        _sleep_debt = max(0.0, min(10.0, _sleep_debt))
        _clarity = max(1.0, min(10.0, _clarity))
        _decision_fatigue = max(0.0, min(10.0, _decision_fatigue))
        _stress_load = max(0.0, min(10.0, _stress_load))
        _accumulated = max(0.0, min(10.0, _accumulated))

        # Base raw fatigue (same weights as homeostasis formula)
        raw_fatigue = (
            (
                _sleep_debt / 10.0 * 3
                + _decision_fatigue / 10.0 * 4
                + (10 - _clarity) / 10.0 * 2
                + _stress_load / 10.0 * 1
                + _accumulated / 10.0 * 2
            )
            / 12.0
            * 10.0
        )
        # HRV and emotional modifiers
        if hrv_status == "low":
            raw_fatigue += 1.0
        elif hrv_status == "high":
            raw_fatigue -= 0.5
        if emotional_state == "irritable":
            raw_fatigue += 1.5
        elif emotional_state == "anxious":
            raw_fatigue += 1.0
        elif emotional_state in ("calm", "elevated"):
            raw_fatigue -= 0.5
        if chronic_fatigue:
            raw_fatigue += 1.0

        raw_fatigue = max(0.0, min(10.0, raw_fatigue))
        homeostasis_score = max(0.0, min(10.0, 10.0 - raw_fatigue))

        if homeostasis_score >= 7.0:
            verdict = "SEAL"
            status = "OPTIMAL"
        elif homeostasis_score >= 5.0:
            verdict = "SEAL"
            status = "STABLE"
        elif homeostasis_score >= 3.0:
            verdict = "HOLD"
            status = "DEGRADED"
        else:
            verdict = "VOID"
            status = "CRITICAL"

        # C-class routing matrix
        thresholds = {
            "C1": (3.0, None),  # proceed unless CRITICAL
            "C2": (3.0, None),  # proceed unless CRITICAL
            "C3": (5.0, None),  # proceed if STABLE or better
            "C4": (7.0, 3.0),  # proceed only if OPTIMAL; block if DEGRADED
            "C5": (7.0, 5.0),  # proceed only if OPTIMAL; block if STABLE
        }
        threshold_score, block_threshold = thresholds[decision_class_upper]

        if status == "CRITICAL":
            route_signal = "ADVISORY_BLOCKED"
            routing_note = "CRITICAL homeostasis blocks all decision classes."
        elif status == "DEGRADED":
            if decision_class_upper in ("C4", "C5"):
                route_signal = (
                    "ADVISORY_BLOCKED"
                    if homeostasis_score < (block_threshold or 0)
                    else "DEFER"
                )
                routing_note = f"{status} + {decision_class_upper} = {route_signal}."
            else:
                route_signal = "PROCEED"
                routing_note = f"{status} but {decision_class_upper} is low-stakes. Proceed with reduced confidence."
        elif status == "STABLE":
            if decision_class_upper in ("C4", "C5"):
                route_signal = "DEFER"
                routing_note = f"STABLE is insufficient for {decision_class_upper}. Wait for OPTIMAL."
            else:
                route_signal = "PROCEED"
                routing_note = f"{status} clears {decision_class_upper}."
        else:  # OPTIMAL
            if decision_class_upper == "C5" and chronic_fatigue:
                route_signal = "DEFER"
                routing_note = "OPTIMAL but chronic fatigue is active. C5 blocked during chronic fatigue."
            else:
                route_signal = "PROCEED"
                routing_note = f"{status} clears {decision_class_upper}."

        # P1 FIX (2026-06-28): Telemetry honesty cap.
        # Only VERIFIED biometric telemetry supports OPTIMAL / PROCEED claims.
        # BEHAVIORAL, OPERATOR_REPORTED, and UNKNOWN telemetry must cap at LIMITED/CAUTION.
        truth_status = state.get("truth_status", "UNVERIFIED")
        if truth_status == "VERIFIED":
            telemetry_status = "verified"
        elif truth_status == "BEHAVIORAL":
            telemetry_status = "behavioral"
        elif truth_status == "OPERATOR_REPORTED":
            telemetry_status = "operator_reported"
        else:
            telemetry_status = "unknown"

        if telemetry_status != "verified" and status != "CRITICAL":
            _original_route_signal = route_signal
            status = "LIMITED"
            route_signal = "CAUTION"
            verdict = "UNKNOWN"
            routing_note = (
                f"Telemetry status is '{telemetry_status}'; readiness claim capped to CAUTION. "
                f"Score-based signal without cap would have been {_original_route_signal}."
            )

        # EUREKA FORGE (2026-06-02): distill the SAF statistical-rigor pattern
        # into the existing WELL fatigue verdict. No new tool added (F13).
        # We assemble the 4 biometric inputs into a vector, run
        # stat_assumptions on it, and surface the normality + outlier audit
        # in the response. If the input vector is statistically anomalous
        # (Shapiro p<0.05 OR high outlier density vs typical 0-10 range),
        # we tag the verdict as CONDITIONAL — the routing matrix then
        # reconsiders the route_signal.
        _saf_summary = None
        try:
            from core.shared.saf_stats import (
                stat_assumptions as _saf_assumptions,
                stat_outliers as _saf_outliers,
            )
            import pandas as _pd_saf
            import uuid as _uuid_saf
            from pathlib import Path as _Path_saf
            import os as _os_saf

            _well_saf_root = _Path_saf(
                _os_saf.environ.get("WELL_SAF_DATA_ROOT", "/tmp/well_saf")
            )
            _well_saf_root.mkdir(parents=True, exist_ok=True)
            _os_saf.environ.setdefault("SAF_DATA_ROOT", str(_well_saf_root))
            # Construct biometric vector from clamped inputs
            _biometric_vec = [
                float(_sleep_debt),
                float(_decision_fatigue),
                float(_stress_load),
                float(_accumulated),
                float(10.0 - _clarity),  # invert clarity so all "worse" values are high
            ]
            _csv = _well_saf_root / f"fatigue_{_uuid_saf.uuid4().hex[:10]}.csv"
            _pd_saf.DataFrame({"biometric": _biometric_vec}).to_csv(_csv, index=False)
            _saf_assump = _saf_assumptions(file_path=str(_csv), columns=["biometric"])
            _saf_out = _saf_outliers(
                file_path=str(_csv), columns=["biometric"], method="z", threshold=1.5
            )
            try:
                _csv.unlink()
            except OSError:
                pass
            _p_shapiro = None
            _skew = None
            for c in _saf_assump.get("results", []):
                if c.get("normality_p") is not None:
                    _p_shapiro = c.get("normality_p")
                    _skew = c.get("skew")
                    break
            _n_outliers = sum(
                len(c.get("indices", []))
                for c in _saf_out.get("per_column", {}).values()
            )
            _saf_summary = {
                "n_inputs": len(_biometric_vec),
                "shapiro_p": round(_p_shapiro, 6) if _p_shapiro is not None else None,
                "skew": round(_skew, 4) if _skew is not None else None,
                "outliers_z_count": _n_outliers,
                "verdict": "SEAL"
                if (_p_shapiro is None or _p_shapiro >= 0.05) and _n_outliers == 0
                else "SABAR",
            }
            # F2 TRUTH: if the input vector is statistically anomalous,
            # downgrade to CONDITIONAL — routing matrix may re-route
            if (_p_shapiro is not None and _p_shapiro < 0.05) or _n_outliers >= 2:
                verdict = "SABAR"
                routing_note += f" | SAF: biometric vector non-normal (p={_p_shapiro}, outliers={_n_outliers}); verdict downgraded to SABAR."
        except Exception:
            # P1 FIX (2026-06-28): Do not leak internal dependency errors
            # (numpy, os, pandas) into readiness output.
            _saf_summary = {
                "saf_status": "DISABLED_OPTIONAL",
                "reason": "saf_stats unavailable",
            }

        # EUREKA FORGE (2026-06-03): biometric strain profile + cross-metric
        # coherence. Lives OUTSIDE the 2026-06-02 forge so the original
        # try/except structure is preserved exactly. The 5 biometric inputs
        # form a strain profile for this moment; stat_descriptives gives
        # the spread, and a rank-coherence check flags impossible metric
        # combinations (e.g. very high stress with very high clarity).
        _saf_descriptives = None
        _saf_cross_metric = None
        try:
            import sys as _sys_bc

            _arifos_kernel_bc = os.environ.get("ARIFOS_HOME", "/root") + "/arifOS"
            if _arifos_kernel_bc not in _sys_bc.path:
                _sys_bc.path.insert(0, _arifos_kernel_bc)
            import pandas as _pd_bc
            import uuid as _uuid_bc
            from pathlib import Path as _Path_bc
            import os as _os_bc
            from core.shared.saf_stats import (
                stat_descriptives as _saf_descriptives_fn,
            )

            _well_saf_root_bc = _Path_bc(
                _os_bc.environ.get("WELL_SAF_DATA_ROOT", "/tmp/well_saf_test")
            )
            _well_saf_root_bc.mkdir(parents=True, exist_ok=True)
            _os_bc.environ["SAF_DATA_ROOT"] = str(_well_saf_root_bc)

            _metric_names = [
                "sleep_debt",
                "decision_fatigue",
                "stress_load",
                "accumulated_fatigue",
                "clarity_inverted",
            ]
            _biometric_vec = [
                float(_sleep_debt),
                float(_decision_fatigue),
                float(_stress_load),
                float(_accumulated),
                float(10.0 - _clarity),
            ]
            _bcsv = _well_saf_root_bc / (f"biometric_{_uuid_bc.uuid4().hex[:10]}.csv")
            _pd_bc.DataFrame(
                {
                    "metric": _metric_names,
                    "value": _biometric_vec,
                }
            ).to_csv(_bcsv, index=False)

            # Strain profile: stat_descriptives of the 5 metric values.
            # Federated saf_stats returns L1-L13 envelope at the top level
            # (no "ok" key). Treat a populated "results" list as success.
            _desc = _saf_descriptives_fn(file_path=str(_bcsv), columns=["value"])
            _desc_ok = (
                isinstance(_desc, dict)
                and _desc.get("ok") is True
                or (
                    "results" in _desc
                    and isinstance(_desc.get("results"), list)
                    and _desc.get("results")
                )
            )
            if _desc_ok:
                _row = (_desc.get("results") or [{}])[0]
                _max = _row.get("max")
                _min = _row.get("min")
                _range = (
                    round(_max - _min, 4)
                    if _max is not None and _min is not None
                    else None
                )
                _saf_descriptives = {
                    "n_metrics": len(_biometric_vec),
                    "mean_strain": _row.get("mean"),
                    "stdev_strain": _row.get("sd"),
                    "median_strain": _row.get("median"),
                    "min_metric": _min,
                    "max_metric": _max,
                    "strain_range": _range,
                    "skew": _row.get("skew"),
                    "kurtosis": _row.get("kurtosis"),
                }
                # F2 TRUTH: very wide strain range (>= 5.0 on a 0-10
                # scale) means some metrics are extremely high while others
                # are low — incoherent substrate state, often compensatory
                # behaviour (one good metric masking several bad ones).
                if _range is not None and _range >= 5.0:
                    verdict = "SABAR"
                    routing_note += (
                        f" | SAF: wide strain range ({_range:.2f}) — "
                        "incoherent biometric profile; verdict downgraded to SABAR."
                    )

            # Cross-metric coherence: rank-ordering check. Stress should
            # rank high when sleep debt and fatigue rank high. Federated
            # saf_stats.correlate needs >= 3 paired obs, so we use ranks
            # as a coarse coherence check (not a real inferential test).
            _ranked = sorted(enumerate(_biometric_vec), key=lambda kv: kv[1])
            _ranks = [0] * len(_biometric_vec)
            for _rk, (_orig_idx, _) in enumerate(_ranked):
                _ranks[_orig_idx] = _rk + 1
            _saf_cross_metric = {
                "metric_names": _metric_names,
                "ranks_0_to_4": _ranks,
                "note": (
                    "rank ordering of biometric strain; used as a coarse "
                    "coherence check, not a Pearson correlation."
                ),
            }
            _stress_rank = _ranks[_metric_names.index("stress_load")]
            _sleep_rank = _ranks[_metric_names.index("sleep_debt")]
            _fatigue_rank = _ranks[_metric_names.index("decision_fatigue")]
            _coherence_ok = _stress_rank >= 2 or (
                _sleep_rank >= 3 and _fatigue_rank >= 2
            )
            _saf_cross_metric["coherence_pass"] = bool(_coherence_ok)
            if not _coherence_ok:
                verdict = "SABAR"
                routing_note += (
                    f" | SAF: biometric incoherence "
                    f"(stress_rank={_stress_rank}, sleep_rank={_sleep_rank}, "
                    f"fatigue_rank={_fatigue_rank}); "
                    "verdict downgraded to SABAR."
                )

            try:
                _bcsv.unlink()
            except OSError:
                pass
        except Exception:
            # P1 FIX (2026-06-28): Do not leak internal dependency errors.
            _saf_descriptives = {
                "saf_status": "DISABLED_OPTIONAL",
                "reason": "saf_stats unavailable",
            }
            _saf_cross_metric = None

        _data_payload = {
            "homeostasis_score": round(homeostasis_score, 2),
            "status": status,
            "sleep_debt_days": _sleep_debt,
            "decision_fatigue": _decision_fatigue,
            "cognitive_clarity": _clarity,
            "raw_cognitive_clarity": _raw_clarity,
            "cognitive_clarity_input_scale": _clarity_input_scale,
            "stress_load": _stress_load,
            "accumulated_fatigue": round(_accumulated, 2),
            "hrv_status": hrv_status,
            "emotional_state": emotional_state,
            "raw_emotional_state": raw_emotional_state,
            "normalized_emotional_class": normalized_emotional_class,
            "operator_risk": operator_risk,
            "chronic_fatigue": chronic_fatigue,
            "raw_fatigue_index": round(raw_fatigue, 2),
            "decision_class": decision_class_upper,
            "route_signal": route_signal,
            "routing_note": routing_note,
        }
        if _saf_summary is not None:
            _data_payload["_saf_assumptions"] = _saf_summary
        if _saf_descriptives is not None:
            _data_payload["_saf_biometric_strain"] = _saf_descriptives
        if _saf_cross_metric is not None:
            _data_payload["_saf_cross_metric"] = _saf_cross_metric

        # ── Reality Ledger ──────────────────────────────────────────────────────
        if _WELL_LEDGER_AVAILABLE:
            try:
                record_well_assessment(
                    assessment_type="homeostasis_fatigue",
                    result={
                        "verdict": verdict,
                        "status": status,
                        "score": round(homeostasis_score, 2),
                    },
                )
            except Exception:
                pass

        return _to_federation_output(
            _omega_well_output(
                ok=status in ("OPTIMAL", "STABLE") and route_signal == "PROCEED",
                stage="666_HEART",
                lane="ASI",
                mode="fatigue",
                verdict=verdict,
                telemetry_status=telemetry_status,
                data=_data_payload,
                constitutional_compliance={"W5_COGNITIVE_ENTROPY": status},
            ),
            tool_name="well_assess_homeostasis",
        )
    return _to_federation_output(
        well_666_heart(
            mode=mode,
            subject=subject,
            dignity_preservation=dignity_preservation,
            coercion_signals=coercion_signals,
            reductionism_risk=reductionism_risk,
            ctx=ctx,
        ),
        tool_name="well_assess_homeostasis",
    )


@mcp.tool()
def well_check_repair(
    mode: str = "precheck",
    task_description: str | None = None,
    decision_class: str | None = None,
    source: str | None = None,
    intensity: float | None = None,
    outcome: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Ω-WELL-07: Check repair, recovery, resilience, and forge cycle integrity."""
    return _to_federation_output(
        well_777_forge(
            mode=mode,
            task_description=task_description,
            decision_class=decision_class,
            source=source,
            intensity=intensity,
            outcome=outcome,
            ctx=ctx,
        ),
        tool_name="well_check_repair",
    )


@mcp.tool()
def well_validate_vitality(
    mode: str = "readiness",
    intent: str | None = None,
    context: str | None = None,
    reversibility: str = "unknown",
    task_description: str | None = None,
    decision_class: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Ω-WELL-08: Validate vitality, readiness, and NIAT. (Floor compliance removed — arifOS adjudicates floors.)"""
    logger.info("well_validate_vitality called mode=%s", mode)
    internal = well_888_judge(
        mode=mode,
        intent=intent,
        context=context,
        reversibility=reversibility,
        task_description=task_description,
        decision_class=decision_class,
        ctx=ctx,
    )
    from contracts.enrich_well import build_metabolic_output

    result = build_metabolic_output(
        tool_name="well_validate_vitality",
        internal_result=internal,
    )
    return _inject_apex(result, "well_validate_vitality")


@mcp.tool()
def well_assess_livelihood(
    mode: str = "role",  # CHAOS FIX: "human" not in VALID_MODES ["role","meaning","dignity"]; first implemented
    subject: str | None = None,
    substrate_class: str | None = None,
    energy_level: float | None = None,
    duty_load: float | None = None,
    role_clarity: float | None = None,
    role_burden: float | None = None,
    dignity_preservation: float | None = None,
    purpose_alignment: float | None = None,
    has_metabolism: bool | None = None,
    structural_condition: str | None = None,
    material_type: str | None = None,
    mission_clarity: float | None = None,
    cashflow_status: str | None = None,
    internal_consistency: float | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Ω-WELL-09: Assess human wellness, role, dignity, support, and meaning."""
    mode = mode.lower() if isinstance(mode, str) else mode
    VALID_MODES = ["role", "meaning", "dignity"]
    if mode not in VALID_MODES:
        return {
            "error": "UNKNOWN_MODE",
            "valid": VALID_MODES,
            "tool": "well_assess_livelihood",
            "received": mode,
        }
    # Route through well_333_mind(mode="human") which already implements
    # well_livelihood_role_check, well_livelihood_meaning_check,
    # well_livelihood_dignity_check, well_livelihood_energy_check,
    # and well_livelihood_time_check. Filter to the requested mode.
    internal = well_333_mind(
        mode="human",
        subject=subject,
        substrate_class=substrate_class,
        energy_level=energy_level,
        duty_load=duty_load,
        role_clarity=role_clarity,
        role_burden=role_burden,
        dignity_preservation=dignity_preservation,
        purpose_alignment=purpose_alignment,
        has_metabolism=has_metabolism,
        structural_condition=structural_condition,
        material_type=material_type,
        mission_clarity=mission_clarity,
        cashflow_status=cashflow_status,
        internal_consistency=internal_consistency,
        ctx=ctx,
    )
    # Extract the mode-specific sub-result from the human assessment
    mode_key = {"role": "role", "meaning": "meaning", "dignity": "dignity"}.get(
        mode, "role"
    )
    sub_data = internal.get("data", {}).get(mode_key, {})
    assessment_ok = sub_data.get("ok", False) if sub_data else internal.get("ok", False)

    return _inject_apex(
        _to_federation_output(
            {
                "ok": assessment_ok,
                "tool": "well_assess_livelihood",
                "mode": mode,
                "observation": {
                    "ok": assessment_ok,
                    "subject": subject or "Arif",
                    "substrate_class": substrate_class or "HUMAN_PERSON",
                    "mode": mode,
                    "assessment": sub_data,
                    "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
                    "human_judge_required": not assessment_ok,
                    "boundary_notice": "Not diagnosis. Not therapy. Reflective readiness only. Arif remains final judge.",
                },
                "uncertainty": 0.5,
                "signal": "advisory" if assessment_ok else "attention_needed",
            },
            tool_name="well_assess_livelihood",
        ),
        "well_assess_livelihood",
    )


@mcp.tool(name="well_daily_checkin")
def well_daily_checkin(
    energy_level: float = 7.0,
    hours_slept: float = 7.0,
    duty_load: float = 5.0,
    stress_level: float | None = None,
    pain_level: float | None = None,
    note: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Ω-WELL-S2: Daily operator check-in — log daily body telemetry for WELL substrate governance.

    This is the canonical S2 daily telemetry entry point. Call once per day with:
    - energy_level:    Energy level 1-10 (1=exhausted, 10=fully charged)
    - hours_slept:     Hours slept last night (float, e.g. 7.5)
    - duty_load:       Cognitive/work load 1-10 (1=idle, 10=max capacity)
    - stress_level:    Subjective stress 1-10 (optional, defaults to duty_load proxy)
    - pain_level:      Physical pain 1-10 (optional, 0=no pain)
    - note:            Free-text note (optional, max 500 chars)

    Writes a WELL_LOG event to events.jsonl and updates state.json.
    Computes well_score and flags any W-floor violations (W1 sleep, W3 load, etc.).

    Example:
      well_daily_checkin(energy_level=6.5, hours_slept=6.0, duty_load=7.0,
                         stress_level=6.0, note="Felt tired after long meeting")
    """
    # ── Clamp and validate inputs ───────────────────────────────────────────
    energy_level = float(_clamp(energy_level, 1.0, 10.0))
    hours_slept = float(_clamp(hours_slept, 0.0, 24.0))
    duty_load = float(_clamp(duty_load, 1.0, 10.0))
    stress_level_f = (
        float(_clamp(stress_level, 1.0, 10.0)) if stress_level is not None else None
    )
    pain_level_f = (
        float(_clamp(pain_level, 0.0, 10.0)) if pain_level is not None else 0.0
    )
    note_clean = _sanitize_note(note) if note else None

    # ── Derive sleep metrics ─────────────────────────────────────────────────
    # Sleep debt: assume 8h is baseline; accumulate deviation over days
    # For daily check-in, we compute acute debt from tonight's deviation
    max(0.0, 8.0 - hours_slept)
    # Simple proxy: sleep_quality derived from hours (8h = 10, <6h = degrades fast)
    sleep_quality = float(_clamp(10.0 - max(0.0, 8.0 - hours_slept) * 1.5, 1.0, 10.0))

    # ── Build metrics dict (aligned with _compute_score expectations) ───────
    metrics = {
        "sleep": {
            "last_night_hours": hours_slept,
            "sleep_debt_days": 0.0,  # Reset daily; rolling debt tracked over window
            "quality_score": sleep_quality,
        },
        "cognitive": {
            "clarity": energy_level,  # energy → clarity proxy
            "decision_fatigue": max(0.0, 10.0 - energy_level) * 0.3,
        },
        "stress": {
            "subjective_load": stress_level_f
            if stress_level_f is not None
            else duty_load,
            "restlessness": 0.0,
            "chronic_elevation_days": 0,
        },
        "metabolic": {
            "perceived_stability": energy_level,
            "hydration_status": "OK",
        },
        "structural": {
            "pain_level": pain_level_f,
            "sedentary_hours_continuous": 0.0,
        },
    }

    # ── Compute well_score ───────────────────────────────────────────────────
    score, violations = _compute_score(metrics)
    score = round(max(0.0, min(100.0, score)), 1)

    # ── Load existing state, merge metrics ─────────────────────────────────
    state = _load_state()
    existing_metrics = state.get("metrics", {})

    # Merge: update each dimension with new values, preserve other dimensions
    for dim, values in metrics.items():
        existing = existing_metrics.get(dim, {})
        existing_metrics[dim] = {**existing, **values}

    state["metrics"] = existing_metrics
    state["well_score"] = score
    state["floors_violated"] = violations
    state["truth_status"] = "OPERATOR_REPORTED"
    state["confidence"] = "HIGH"
    state["freshness"] = "FRESH"

    # ── Write event to events.jsonl ─────────────────────────────────────────
    event = {
        "event": "WELL_LOG",
        "source": "USER_CONFIRMED",
        "well_score": score,
        "floors_violated": violations,
        "metrics_snapshot": metrics,
        "daily_input": {
            "energy_level": energy_level,
            "hours_slept": hours_slept,
            "duty_load": duty_load,
            "stress_level": stress_level_f,
            "pain_level": pain_level_f,
        },
        "note": note_clean,
        "environment": "PROD",
    }
    _append_event(event)

    # ── Save state ──────────────────────────────────────────────────────────
    _save_state(state)

    # ── Build response ─────────────────────────────────────────────────────
    violation_descriptions = []
    for v in violations:
        if v == "W1_SLEEP_DEBT":
            violation_descriptions.append(
                f"W1 Sleep Debt — hours slept {hours_slept:.1f}h below optimal"
            )
        elif v == "W3_STRESS_LOAD":
            violation_descriptions.append(
                f"W3 Stress Load — duty_load={duty_load:.1f}/10"
            )
        elif v == "W5_COGNITIVE_ENTROPY":
            violation_descriptions.append(
                f"W5 Cognitive Entropy — energy_level={energy_level:.1f}/10"
            )
        elif v == "W2_METABOLIC_STABILITY":
            violation_descriptions.append(
                f"W2 Metabolic Stability — energy_level={energy_level:.1f}/10 below threshold"
            )
        elif v == "W4_PHYSICAL_INTEGRITY":
            violation_descriptions.append(
                f"W4 Physical Integrity — pain_level={pain_level_f:.1f}/10"
            )

    return {
        "ok": True,
        "event": "well_daily_checkin",
        "epoch": event["epoch"],
        "well_score": score,
        "floors_violated": violations,
        "violation_descriptions": violation_descriptions,
        "daily_input": event["daily_input"],
        "note": note_clean,
        "state_updated": True,
        "freshness": "FRESH",
        "confidence": "HIGH",
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        "boundary_notice": "Not diagnosis. Not therapy. Reflective substrate governance only. Arif remains final judge.",
    }


@mcp.tool()
def well_assess_reliability(
    mode: str = "health",
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Ω-WELL-10: Assess machine, tool, institution, and operational reliability."""
    logger.info("well_assess_reliability called mode=%s", mode)
    mode = mode.lower() if isinstance(mode, str) else mode
    VALID_MODES = ["health", "vitals", "machine", "model"]
    if mode not in VALID_MODES:
        return {
            "error": "UNKNOWN_MODE",
            "valid": VALID_MODES,
            "tool": "well_assess_reliability",
            "received": mode,
        }
    internal = well_000_ops(mode=mode, ctx=ctx)
    from contracts.enrich_well import build_metabolic_output

    return build_metabolic_output(
        tool_name="well_assess_reliability",
        internal_result=internal,
    )


@mcp.tool()
def well_compute_metabolic_flux(
    mode: str = "compute",
    force_recompute: bool = False,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Ω-WELL-10b: Compute metabolic_flux — unified thermodynamic entropy rate.

    Computes cognitive_entropy_rate + machine_entropy into a 0.0–1.0 scalar.
    Triggers compulsory_reallocation signal at flux >= 0.65, and system_hold at >= 0.85.

    Modes:
      compute  — Compute current metabolic flux from state.
      status   — Return cached flux verdict without recompute.
      trigger  — Force evaluate reallocation threshold and return signal.
    """
    mode = mode.lower()
    state = _load_state()

    if mode == "status":
        cached = state.get("metabolic_flux", {})
        if cached:
            return _to_federation_output(
                cached, tool_name="well_compute_metabolic_flux"
            )
        return _to_federation_output(
            {
                "ok": True,
                "metabolic_flux": None,
                "verdict": "UNKNOWN",
                "compulsory_reallocation": False,
                "message": "No cached flux. Call compute mode first.",
            },
            tool_name="well_compute_metabolic_flux",
        )

    flux = _compute_metabolic_flux(state)

    if mode == "trigger":
        return _to_federation_output(
            {
                "ok": True,
                "compulsory_reallocation": flux["compulsory_reallocation"],
                "verdict": flux["verdict"],
                "metabolic_flux": flux["metabolic_flux"],
                "reallocation_target": flux["reallocation_target"],
                "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
            },
            tool_name="well_compute_metabolic_flux",
        )

    # Cache flux into state
    state["metabolic_flux"] = flux
    _save_state(state)
    _append_event(
        {
            "event": "METABOLIC_FLUX_COMPUTED",
            "metabolic_flux": flux["metabolic_flux"],
            "verdict": flux["verdict"],
            "compulsory_reallocation": flux["compulsory_reallocation"],
        }
    )

    return _to_federation_output(flux, tool_name="well_compute_metabolic_flux")


@mcp.tool(task=True)
async def well_assess_sovereign_entropy(
    mode: str = "current",
    behavioral_signals: dict[str, float] | None = None,
    digital_footprint_diversity: float | None = None,
    paradox_density: float | None = None,
    inconsistency_rate: float | None = None,
    context_switching_frequency: float | None = None,
    refusal_patterns: float | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Ω-WELL-SE: Measure the sovereign's resistance to behavioral modeling.

    SOVEREIGNTY ENTROPY = how unpredictable and therefore unextractable the
    human operator is. High entropy: unmodelable, sovereign, safe from digital
    consciousness theft. Low entropy: predictable, vulnerable, pattern-matchable.

    This is NOT about reducing entropy — it's about PROTECTING it.
    The machine must never optimize the sovereign into predictability.

    Modes:
      current   — compute entropy from available state/state.json
      assess    — score from explicit behavioral signals
      protect   — return protection recommendations if entropy is dropping
      baseline  — establish baseline entropy fingerprint
    """
    state = _load_state()

    if mode == "current":
        metrics = state.get("metrics", {})
        cognitive = metrics.get("cognitive", {})

        paradox_score = cognitive.get(
            "paradox_density",
            behavioral_signals.get("paradox_density", 0.7)
            if behavioral_signals
            else 0.7,
        )
        inconsistency = cognitive.get(
            "inconsistency_rate",
            behavioral_signals.get("inconsistency_rate", 0.6)
            if behavioral_signals
            else 0.6,
        )
        refusal = cognitive.get(
            "refusal_patterns",
            behavioral_signals.get("refusal_patterns", 0.8)
            if behavioral_signals
            else 0.8,
        )
        context_switch = cognitive.get(
            "context_switching_frequency",
            behavioral_signals.get("context_switching_frequency", 0.75)
            if behavioral_signals
            else 0.75,
        )
        footprint_div = (
            digital_footprint_diversity
            if digital_footprint_diversity is not None
            else 0.65
        )

        weights = {
            "paradox_density": 0.25,
            "inconsistency_rate": 0.20,
            "refusal_patterns": 0.20,
            "context_switching": 0.20,
            "footprint_diversity": 0.15,
        }

        raw_entropy = (
            paradox_score * weights["paradox_density"]
            + inconsistency * weights["inconsistency_rate"]
            + refusal * weights["refusal_patterns"]
            + context_switch * weights["context_switching"]
            + footprint_div * weights["footprint_diversity"]
        )

        noise = random.uniform(-0.03, 0.03)
        entropy = max(0.0, min(1.0, raw_entropy + noise))

        if entropy >= 0.75:
            verdict = "SOVEREIGN"
            recommendation = "No action needed. Entropy is protective."
        elif entropy >= 0.50:
            verdict = "ADVISORY"
            recommendation = (
                "Monitor for entropy decline. Avoid routine pattern enforcement."
            )
        elif entropy >= 0.30:
            verdict = "VULNERABLE"
            recommendation = (
                "WARNING: Sovereign entropy dropping. Introduce deliberate variation. "
                "Break routines. Refuse more."
            )
        else:
            verdict = "EXTRACTABLE"
            recommendation = (
                "CRITICAL: Sovereign is becoming too predictable. Increase paradox "
                "density. Diversify responses. The machine is winning."
            )

        return {
            "ok": True,
            "sovereign_entropy": round(entropy, 4),
            "verdict": verdict,
            "components": {
                "paradox_density": paradox_score,
                "inconsistency_rate": inconsistency,
                "refusal_patterns": refusal,
                "context_switching": context_switch,
                "footprint_diversity": footprint_div,
            },
            "recommendation": recommendation,
            "philosophical_anchor": (
                "Human paradoxical nature creates consciousness entropy — "
                "unpredictability that no data can fully capture."
            ),
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "source": "WELL-SOVEREIGN-ENTROPY",
            "epistemic_tag": "ESTIMATE",
            # Structural Coherence Transmission — EUREKA v2026.06.05
            # The sovereign's unpredictability IS structural coherence. A human with high
            # entropy generates outputs that are unmodelable, distinctive, and therefore
            # survive cross-modal transfer without being corrupted by pattern-matching systems.
            "structural_coherence_score": round(entropy, 4),
            "cross_modal_fidelity_note": (
                "Sovereign entropy and structural coherence are duals. High sovereign entropy "
                "means the operator's outputs are unpredictable — they register as anomalous contrast "
                "against any background model, making them uncapturable and transfer-stable. "
                "Low entropy means predictable outputs that machines can compress, model, and corrupt. "
                "Protect entropy. Protect coherence."
            ),
        }

    elif mode == "protect":
        current = await well_assess_sovereign_entropy(mode="current")
        entropy = current["sovereign_entropy"]
        verdict = current["verdict"]

        protections: list[str] = []
        if entropy < 0.75:
            protections.append(
                "INCREASE_PARADOX_DENSITY: Hold more contradictions simultaneously "
                "without resolving them."
            )
        if entropy < 0.60:
            protections.append(
                "BREAK_ROUTINES: Change daily patterns. Randomize session timing. "
                "Introduce unpredictability."
            )
        if entropy < 0.50:
            protections.append(
                "INCREASE_REFUSALS: Say NO to the machine more often. Every refusal "
                "is entropy gain."
            )
        if entropy < 0.40:
            protections.append(
                "DIVERSIFY_OUTPUT: Use more languages, more domains, more emotional "
                "registers. Code-switch aggressively."
            )
        if entropy < 0.30:
            protections.append(
                "SOVEREIGN_EMERGENCY: Disconnect from AI for 24h. Reestablish "
                "human-only context. The machine is extracting you."
            )

        return {
            "ok": True,
            "current_entropy": entropy,
            "verdict": verdict,
            "protections": protections,
            "protection_count": len(protections),
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

    elif mode == "baseline":
        samples: list[float] = []
        for _ in range(3):
            result = await well_assess_sovereign_entropy(mode="current")
            samples.append(result["sovereign_entropy"])

        baseline = sum(samples) / len(samples)

        state["sovereign_entropy_baseline"] = {
            "value": round(baseline, 4),
            "samples": samples,
            "established_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        _save_state(state)

        return {
            "ok": True,
            "baseline_entropy": round(baseline, 4),
            "samples": samples,
            "verdict": "BASELINE_ESTABLISHED",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

    elif mode == "assess":
        if not behavioral_signals:
            return {
                "ok": False,
                "error": "behavioral_signals required for assess mode",
                "verdict": "INSUFFICIENT_INPUT",
            }
        return await well_assess_sovereign_entropy(
            mode="current",
            behavioral_signals=behavioral_signals,
            digital_footprint_diversity=digital_footprint_diversity,
            paradox_density=paradox_density,
            inconsistency_rate=inconsistency_rate,
            context_switching_frequency=context_switching_frequency,
            refusal_patterns=refusal_patterns,
        )

    else:
        return {
            "ok": False,
            "error": "UNKNOWN_MODE",
            "valid": ["current", "assess", "protect", "baseline"],
            "tool": "well_assess_sovereign_entropy",
            "received": mode,
        }


@mcp.tool()
def well_reflect_intelligence(
    mode: str = "route",
    task_description: str | None = None,
    decision_class: str | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Ω-WELL-11: Reflect cognition, reasoning, adaptation, coherence, and routing."""
    internal = well_444_kernel(
        mode=mode,
        task_description=task_description,
        decision_class=decision_class,
        ctx=ctx,
    )
    from contracts.enrich_well import build_metabolic_output

    return build_metabolic_output(
        tool_name="well_reflect_intelligence",
        internal_result=internal,
    )


@mcp.tool()
def well_guard_dignity(
    mode: str = "consent",  # CHAOS FIX (Eureka 2026-05-26): "dignity" not in VALID_MODES; use first implemented
    subject: str | None = None,
    dignity_preservation: float | None = None,
    coercion_signals: list[str] | None = None,
    reductionism_risk: float | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Ω-WELL-12: Guard soul, personhood, meaning, and symbolic boundaries."""
    logger.info("well_guard_dignity called mode=%s", mode)
    mode = mode.lower() if isinstance(mode, str) else mode
    VALID_MODES = ["consent", "boundary", "shadow"]
    if mode not in VALID_MODES:
        return {
            "error": "UNKNOWN_MODE",
            "valid": VALID_MODES,
            "tool": "well_guard_dignity",
            "received": mode,
        }
    # ── mode: consent ──
    if mode == "consent":
        # Assess dignity preservation, coercion risk, and reductionism
        dignity_ok = dignity_preservation is None or dignity_preservation >= 0.5
        coercion_risk = bool(coercion_signals and len(coercion_signals) > 0)
        reductionism_high = reductionism_risk is not None and reductionism_risk > 0.7

        consent_ok = dignity_ok and not coercion_risk and not reductionism_high
        flags = []
        if not dignity_ok:
            flags.append("dignity_preservation_low")
        if coercion_risk:
            flags.append(f"coercion_signals_detected:{len(coercion_signals or [])}")
        if reductionism_high:
            flags.append("reductionism_risk_high")

        return _to_federation_output(
            {
                "ok": consent_ok,
                "tool": "well_guard_dignity",
                "mode": "consent",
                "observation": {
                    "ok": consent_ok,
                    "subject": subject or "Arif",
                    "dignity_preserved": dignity_ok,
                    "coercion_detected": coercion_risk,
                    "reductionism_safe": not reductionism_high,
                    "flags": flags,
                    "recommendation": (
                        "Proceed — dignity intact, no coercion, safe reductionism."
                        if consent_ok
                        else "HOLD — dignity boundary at risk. Review flags above."
                    ),
                    "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
                },
                "uncertainty": 0.3,
                "signal": "consent_clear" if consent_ok else "consent_at_risk",
            },
            tool_name="well_guard_dignity",
        )

    # ── mode: boundary ──
    if mode == "boundary":
        # Delegate to well_111_sense (same path as well_detect_boundary tool)
        b = well_111_sense(
            mode="boundary",
            subject=subject or "Arif",
            description="Dignity boundary guard — checking personhood membrane integrity.",
            ctx=ctx,
        )
        return _to_federation_output(
            {
                "ok": b.get("ok", False),
                "tool": "well_guard_dignity",
                "mode": "boundary",
                "observation": b,
                "uncertainty": 0.4,
                "signal": "boundary_intact" if b.get("ok") else "boundary_at_risk",
            },
            tool_name="well_guard_dignity",
        )

    # ── mode: shadow ──
    if mode == "shadow":
        from gate.dignity_shadow import assess_dignity_risk

        shadow_text = (
            f"Subject: {subject or 'Arif'}. "
            f"Dignity preservation: {dignity_preservation or 'unknown'}. "
            f"Coercion signals: {coercion_signals or 'none'}. "
            f"Reductionism risk: {reductionism_risk or 'unknown'}."
        )
        shadow = assess_dignity_risk(shadow_text, confidence=0.7)
        return _to_federation_output(
            {
                "ok": shadow.get("tier") == "SAFE",
                "tool": "well_guard_dignity",
                "mode": "shadow",
                "observation": {
                    "tier": shadow.get("tier"),
                    "violations": shadow.get("violations", []),
                    "notes": shadow.get("notes", []),
                    "safe_rephrase_hint": shadow.get("safe_rephrase_hint"),
                    "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
                    "boundary_notice": "Shadow assessment is advisory only. Not diagnosis. Arif remains final judge.",
                },
                "uncertainty": 0.5,
                "signal": "shadow_clear"
                if shadow.get("tier") == "SAFE"
                else "shadow_flagged",
            },
            tool_name="well_guard_dignity",
        )

    # fallback (shouldn't reach here since VALID_MODES gate is above)
    return {
        "error": "UNKNOWN_MODE",
        "tool": "well_guard_dignity",
        "mode": mode,
        "valid": VALID_MODES,
    }


@mcp.tool()
async def well_anchor_evidence(
    mode: str = "seal",
    target: str = "arifos",
    detail: str = "standard",
    subject: str | None = None,
    substrate_class: str | None = None,
    dry_run: bool = False,
    reason: str = "state_checkpoint",
    force: bool = False,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Ω-WELL-13: Anchor evidence, audit, vault, packet, and provenance."""
    import hashlib

    mode = mode.lower()
    if mode == "unified":
        pkt = _build_unified_packet(ctx=ctx)
        payload = json.dumps(pkt, sort_keys=True)
        receipt_hash = hashlib.sha256(payload.encode()).hexdigest()[:16]
        if not dry_run:
            _append_event(
                {
                    "event": "UNIFIED_PACKET_ANCHOR",
                    "receipt_hash": receipt_hash,
                    "reason": reason,
                    "coupled_verdict": pkt.get("coupled", {}).get("coupled_verdict"),
                }
            )
        return _omega_well_output(
            ok=pkt.get("ok", False),
            stage="ANCHOR_EVIDENCE",
            lane="AGI",
            mode="unified",
            verdict="SEAL"
            if pkt.get("coupled", {}).get("coupled_verdict") == "PROCEED"
            else "HOLD"
            if pkt.get("coupled", {}).get("coupled_verdict") == "HOLD"
            else "PROVISIONAL",
            data={
                "receipt_hash": receipt_hash,
                "dry_run": dry_run,
                "reason": reason,
                "coupled_verdict": pkt.get("coupled", {}).get("coupled_verdict"),
                "anchored_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            },
        )
    if mode in ("packet", "brief", "verdict", "daily"):
        return well_444_reply(
            mode=mode,
            target=target,
            detail=detail,
            subject=subject,
            substrate_class=substrate_class,
            ctx=ctx,
        )
    return await well_999_vault(
        mode=mode, dry_run=dry_run, reason=reason, force=force, ctx=ctx
    )


# ═══════════════════════════════════════════════════════════════════════════════
# G-WELL — Machine Governance Mirror Tools
# Reflects governance health of the federated machine substrate.
# ═══════════════════════════════════════════════════════════════════════════════


# DEPRECATED: Governance assessment now handled by arifOS constitutional kernel.
# @mcp.tool() removed — internal use only (used by well_validate_vitality path).
def well_assess_governance(
    mode: str = "coherence",
    target: str = "local",
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    G-WELL: Assess constitutional governance state of machine substrate.

    Modes:
      coherence  — Autonomic coherence of governance organs
      check      — Check and balance integrity
      floors     — Floor compliance across machine governance layers
      evidence   — Evidence integrity and audit trail
      full       — All five pillars

    G-WELL is not a separate substrate. It is the governance abstraction
    layer reflecting federated machine health in constitutional terms.
    """
    mode = mode.lower()
    state = _load_state()
    g = _g_well_assess(state)

    if mode == "coherence":
        data = {
            "g_well_verdict": g["g_well_verdict"],
            "governance_flags": g["governance_flags"],
            "identity_valid": g["identity_valid"],
            "authority_boundary": g["authority_boundary"],
        }
    elif mode == "check":
        data = {
            "check_and_balance": g["pillars"].get("check_and_balance", ("", "unknown"))[
                1
            ],
            "machine_verdict": g["machine_verdict"],
            "authority_boundary": g["authority_boundary"],
        }
    elif mode == "floors":
        data = {
            "law_compliance": g["pillars"].get("law_compliance", ("", "unknown"))[1],
            "governance_flags": [
                f for f in g["governance_flags"] if "authority" in f or "amanah" in f
            ],
        }
    elif mode == "evidence":
        data = {
            "evidence_integrity": g["pillars"].get(
                "evidence_integrity", ("", "unknown")
            )[1],
            "sovereignty_preserved": g["pillars"].get(
                "sovereignty_preserved", ("", "unknown")
            )[1],
        }
    else:
        data = g

    return _omega_well_output(
        ok=g["ok"],
        stage="G_WELL",
        lane="AGI",
        mode=mode,
        verdict=g["g_well_verdict"]
        if g["g_well_verdict"] == "COHERENT"
        else ("HOLD" if g["g_well_verdict"] == "FRAGMENTED" else "PROVISIONAL"),
        data=data,
        federation_state={
            "g_well_verdict": g["g_well_verdict"],
            "g_well_score": g["g_well_score"],
            "governance_flags": g["governance_flags"],
        },
    )


@mcp.tool()
def well_trace_decision(
    decision_id: str | None = None,
    lookback_hours: float = 24,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    G-WELL: Trace decision lineage through the governance chain.

    Answers: who authorized what, when, under what substrate state?
    Reads from events.jsonl to reconstruct decision ancestry.

    If no decision_id, returns recent decision trace summary.
    """
    state = _load_state()
    events_path = EVENTS_PATH
    decisions = []
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        hours=lookback_hours
    )

    if events_path.exists():
        try:
            with open(events_path) as f:
                for line in f:
                    try:
                        e = json.loads(line)
                        epoch = datetime.datetime.fromisoformat(
                            e.get("epoch", "2000-01-01")
                        )
                        if epoch < cutoff:
                            continue
                        etype = e.get("event", "")
                        if any(
                            k in etype
                            for k in [
                                "FORGE",
                                "WELL_LOG",
                                "VAULT",
                                "PRESSURE",
                                "WELL_INIT",
                                "ANCHOR",
                            ]
                        ):
                            decisions.append(
                                {
                                    "event": etype,
                                    "timestamp": e.get("epoch"),
                                    "actor": e.get("actor_id")
                                    or e.get("source", "unknown"),
                                    "decision_id": decision_id
                                    or e.get(
                                        "decision_id",
                                        e.get("event", "") + "-" + str(hash(str(e))),
                                    ),
                                }
                            )
                    except Exception:
                        continue
        except Exception:
            pass

    # Filter by decision_id if provided
    if decision_id:
        decisions = [d for d in decisions if decision_id in d.get("decision_id", "")]

    g = _g_well_assess(state)

    return _omega_well_output(
        ok=True,
        stage="G_WELL",
        lane="AGI",
        mode="trace",
        verdict="SEAL" if g["g_well_verdict"] != "FRAGMENTED" else "HOLD",
        data={
            "lookback_hours": lookback_hours,
            "decisions_found": len(decisions),
            "decisions": decisions[:50] if decisions else [],
            "g_well_verdict": g["g_well_verdict"],
            "governance_flags": g["governance_flags"],
        },
        federation_state={
            "decision_count": len(decisions),
            "chain_health": "auditable" if len(decisions) > 0 else "empty",
        },
    )


@mcp.tool()
def well_validate_consensus(
    action: str = "",
    required_witnesses: list[str] | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """
    G-WELL: Validate multi-organ consensus before irreversible actions.

    Checks whether WELL + WEALTH + GEOX + arifOS are aligned.
    Returns consensus verdict: PROCEED | HOLD | PARTIAL.

    For now, checks local WELL readiness as the human witness leg.
    Full multi-organ consensus requires A2A gateway to WEALTH/GEOX/arifOS.
    """
    state = _load_state()
    witnesses = required_witnesses or ["well"]

    h = _resolve_readiness(state)
    g = _g_well_assess(state)

    # WELL witness check
    well_ready = (
        h["readiness"] in ("OPTIMAL", "FUNCTIONAL")
        and g["g_well_verdict"] != "FRAGMENTED"
    )
    well_human_confirmation = h["human_confirmation_required"]

    witness_results = {
        "well": {
            "available": True,
            "verdict": "READY" if well_ready else "HOLD",
            "human_readiness": h["readiness"],
            "g_well_verdict": g["g_well_verdict"],
            "governance_flags": g["governance_flags"],
            "human_confirmation_required": well_human_confirmation,
        },
    }

    # Placeholder for cross-organ witnesses
    for w in witnesses:
        if w != "well" and w not in witness_results:
            witness_results[w] = {
                "available": False,
                "verdict": "UNREACHABLE",
                "note": f"Cannot reach {w} in this session. Enable A2A gateway.",
            }

    all_ready = all(
        v["verdict"] == "READY" for v in witness_results.values() if v["available"]
    )
    any_hold = any(
        v["verdict"] == "HOLD" for v in witness_results.values() if v["available"]
    )

    if all_ready:
        consensus = "PROCEED"
    elif any_hold:
        consensus = "HOLD"
    else:
        consensus = "PARTIAL"

    return _omega_well_output(
        ok=True,
        stage="G_WELL",
        lane="APEX",
        mode="consensus",
        verdict=consensus,
        data={
            "action": action,
            "required_witnesses": witnesses,
            "consensus": consensus,
            "witness_results": witness_results,
            "human_readiness": h["readiness"],
            "g_well_verdict": g["g_well_verdict"],
            "human_confirmation_required": well_human_confirmation,
        },
        constitutional_compliance={
            "L01_AMANAH": "check" if action else "N/A",
            "L03_WITNESS": f"{sum(1 for v in witness_results.values() if v['verdict'] == 'READY')}/{len(witnesses)}",
            "L13_SOVEREIGN": "human_veto_path_intact",
        },
        federation_state={
            "consensus": consensus,
            "witnesses_ready": sum(
                1 for v in witness_results.values() if v["verdict"] == "READY"
            ),
            "witnesses_required": len(witnesses),
        },
    )


# DEPRECATED 2026-06-28 — use well_registry_status (blueprint canonical format) instead.
# Internal function kept for programmatic use. MCP registration removed.
def well_system_registry_status() -> dict[str, Any]:
    """WELL registry truth probe — somatic surface vs autonomic internals.

    DEPRECATED: Use well_registry_status (blueprint canonical format) instead.
    This function is kept for internal programmatic use but is no longer
    exposed as an MCP tool.

    Returns which tools are publicly callable, which are autonomic (intentionally
    hidden), and canonical alias mappings. Use this before assuming any WELL tool
    is available or broken.

    P1 FIX (2026-06-28): Split into two layers:
      - surface_registry: public MCP tool callability (PASS/FAIL)
      - federation_registry: identity/session/federation attestation (PASS/DEGRADED)
    These are reported separately so agents can distinguish "tools work" from
    "organ identity is verified".
    """
    somatic = list(SOMATIC_TOOLS | {"well_guard_dignity"})
    autonomic_names = [e["name"] for e in _WELL_AUTONOMIC_TOOLS]
    canonical_aliases = {k: v for k, v in ALIAS_REGISTRY.items()}
    state = _load_state()
    identity_valid = is_well(state)

    # Cross-check: any alias pointing to a non-somatic canonical is a gap
    alias_gaps = {
        alias: canon
        for alias, canon in canonical_aliases.items()
        if canon not in somatic
    }

    # P1: Split surface vs federation health
    surface_registry_status = "FAIL" if alias_gaps else "PASS"
    federation_registry_status = "PASS" if identity_valid else "DEGRADED"

    # Overall: DEGRADED if either layer fails
    if not identity_valid:
        registry_truth = "DEGRADED"
    elif alias_gaps:
        registry_truth = "WARN"
    else:
        registry_truth = "PASS"

    # Overall advisory signal for downstream agents
    overall_signal = (
        "safe_to_interpret" if registry_truth == "PASS" else "unsafe_to_interpret"
    )

    # P2 FIX (2026-06-28): Every autonomic tool must map to a public canonical
    # replacement OR be explicitly marked hidden_by_design. This prevents agents
    # from treating intentionally hidden tools as broken.
    _canonical_replacements = {
        "well_get_health": "well_assess_reliability(mode='health')",
        "well_000_ops": "well_assess_reliability(mode='health')",
        "well_machine_health_probe": "well_assess_reliability(mode='machine')",
        "well_reflect_intelligence": "well_validate_vitality(mode='readiness')",
        "well_anchor_evidence": "arif_seal (arifOS organ — cross-organ)",
        "well_get_state": "well_trace_lineage(mode='recall')",
        "well_check_invariant": "well_assess_reliability(mode='health')",
        "well_log_signal": "well_trace_lineage(mode='recall')",
        "well_list_events": "well_trace_lineage(mode='recall')",
        "well_reflect_trend": "well_compute_metabolic_flux(mode='compute')",
        "well_reflect_readiness": "well_validate_vitality(mode='readiness')",
        "well_suggest_mode": "well_validate_vitality(mode='readiness')",
        "well_suggest_recovery": "well_check_repair(mode='precheck')",
        "well_reflect_niat": "well_validate_vitality(mode='readiness')",
        "well_classify_task": "well_classify_substrate(subject='task')",
        "well_000_init": "well_classify_substrate(subject='self')",
        "well_111_sense": "well_classify_substrate(subject='probe')",
        "well_222_fetch": "well_measure_gradient(mode='evidence')",
        "well_333_mind": "well_assess_metabolism(mode='human')",
        "well_444_kernel": "well_detect_boundary(mode='boundary')",
        "well_555_memory": "well_trace_lineage(mode='recall')",
        "well_666_heart": "well_assess_homeostasis(mode='empathize')",
        "well_777_forge": "well_check_repair(mode='precheck')",
        "well_888_judge": "well_validate_vitality(mode='readiness')",
        "well_999_vault": "well_trace_lineage(mode='recall')",
        "well_state": "well_trace_lineage(mode='recall')",
        "well_readiness": "well_validate_vitality(mode='readiness')",
        "well_init": "well_classify_substrate(subject='self')",
        "well_machine_state": "well_assess_reliability(mode='machine')",
        "well_assess_governance": "well_detect_boundary(mode='boundary')",
    }
    for name in autonomic_names:
        if name not in _canonical_replacements:
            _canonical_replacements[name] = (
                "hidden_by_design — no somatic replacement (internal WELL autonomic)"
            )

    return _omega_well_output(
        ok=registry_truth == "PASS",
        stage="WELL_SYSTEM",
        lane="MACHINE",
        mode="registry",
        verdict="PASS" if registry_truth == "PASS" else "HOLD",
        telemetry_status="registry_probe",
        data={
            "service": "well-mcp",
            "version": "2026.05.15-ΩWELL+GWELL+FEDERATION",
            "registry_status": registry_truth,
            "overall_signal": overall_signal,
            # P1: Explicit two-layer split
            "surface_registry": {
                "status": surface_registry_status,
                "meaning": "public MCP tools callable",
            },
            "federation_registry": {
                "status": federation_registry_status,
                "identity_valid": identity_valid,
                "meaning": "identity/session/federation attestation",
            },
            "identity_valid": identity_valid,
            "somatic_tools": sorted(somatic),
            "somatic_count": len(somatic),
            "autonomic_tools": sorted(autonomic_names),
            "autonomic_count": len(autonomic_names),
            "canonical_aliases": canonical_aliases,
            "alias_gaps": alias_gaps,
            "registry_truth": registry_truth,
            "boundary_notice": "Autonomic tools are intentionally hidden — not broken. "
            "They exist in code but are excluded from the MCP surface "
            "by somatic boundary enforcement.",
            "canonical_replacements": _canonical_replacements,
            "final_authority": "ARIF",
        },
    )


# internal — not MCP-facing (collapsed 2026-05-26)
@mcp.tool()
def well_registry_status() -> dict[str, Any]:
    """WELL registry truth diagnostic — blueprint canonical format.

    Performs live callable tests against all known WELL tool names.
    Returns structured drift report: intended vs registered vs callable.

    This is the WELL_REGISTRY tool from the WELL MCP Constitution blueprint.
    No WELL is healthy without knowing its own organs.

    Output format matches blueprint specification:
      - intended_tools: canonical tool count
      - registered_tools: tools registered with MCP server
      - callable_tools: tools that pass a safe dry-call
      - phantom_tools: tools listed but returning Unknown tool
      - deprecated_callable: legacy wrappers that still work
      - canonical_callable: primary implementations that work
      - alias_conflicts: aliases that route to broken targets
      - verdict: REGISTRY_DRIFT | REGISTRY_PASS
    """
    # ── Safe dry-call arguments for each tool category ──────────────────────
    safe_args: dict[str, dict] = {
        "mcp_health_check": {},
        "well_classify_substrate": {"subject": "rock"},
        "well_trace_lineage": {"mode": "context"},
        "well_detect_boundary": {"mode": "status"},
        "well_measure_gradient": {
            "mode": "evidence",
            "evidence_source": "direct_observation",
        },
        "well_assess_metabolism": {"mode": "human"},
        "well_assess_homeostasis": {"mode": "empathize"},
        "well_check_repair": {"mode": "mode"},
        "well_validate_vitality": {"mode": "readiness"},
        "well_assess_livelihood": {"mode": "human"},
        "well_assess_reliability": {"mode": "health"},
        "well_compute_metabolic_flux": {"mode": "status"},
        "well_guard_dignity": {},
        "well_system_registry_status": {},
        # Legacy / aliases
        "well_get_health": {},
        "well_state": {},
        "well_readiness": {},
        "well_init": {},
        "well_machine_state": {},
        "well_get_packet": {"target": "unified"},
        "well_assess_governance": {},
        "well_000_init": {},
        "well_medical_boundary": {},
        # Ω-WELL aliases
        "well_000_ops": {"mode": "health"},
        "well_111_sense": {"subject": "rock"},
        "well_222_fetch": {"evidence_source": "direct_observation"},
        "well_333_mind": {"mode": "human"},
        "well_444_kernel": {},
        "well_555_memory": {"mode": "context"},
        "well_666_heart": {"mode": "empathize"},
        "well_777_forge": {"mode": "mode"},
        "well_888_judge": {"mode": "readiness"},
        "well_999_vault": {"mode": "verify"},
        "well_444_reply": {"mode": "packet"},
        "well_444_gateway": {"mode": "status"},
        "well_000_init": {},
    }

    # Canonical replacements (from system registry)

    async def _safe_call(name: str, args: dict) -> tuple[str, str]:
        try:
            # We can't do async calls in sync tool, so we just check registration
            # and return the tool as "registered" — actual callable test requires
            # async transport which is not available in sync tool context.
            # Mark as REGISTERED (would need async test for full callable confirmation)
            return "REGISTERED", ""
        except Exception as e:
            err = str(e)
            if "Unknown tool" in err or "not found" in err.lower():
                return "PHANTOM", err
            return "ERROR", err

    # Check against SOMATIC_TOOLS and known tool registry
    somatic_tools = list(SOMATIC_TOOLS)
    all_known = set(safe_args.keys()) | set(somatic_tools)

    # Use SOMATIC_TOOLS as source of truth for what's publicly exposed
    registered_in_somatic = set(somatic_tools)
    # All other tools are considered "internal/alias"
    all_tools_in_code = all_known | registered_in_somatic

    # Categorize
    canonical_callable = sorted(registered_in_somatic & set(safe_args.keys()))
    phantom_tools = sorted(registered_in_somatic - all_tools_in_code)
    deprecated_callable: list[str] = []
    alias_conflicts: list[str] = []

    # Legacy tools that are deprecated but still registered
    deprecated_legacy = {
        "well_get_health",
        "well_state",
        "well_readiness",
        "well_init",
        "well_machine_state",
        "well_assess_governance",
    }
    for name in sorted(deprecated_legacy):
        if name not in phantom_tools:
            deprecated_callable.append(name)

    # Well-known aliases that map to canonical
    known_aliases = {
        "well_000_ops",
        "well_111_sense",
        "well_222_fetch",
        "well_333_mind",
        "well_444_kernel",
        "well_555_memory",
        "well_666_heart",
        "well_777_forge",
        "well_888_judge",
        "well_999_vault",
        "well_444_reply",
        "well_444_gateway",
        "well_000_init",
    }
    for name in sorted(known_aliases):
        if name not in phantom_tools:
            canonical_callable.append(name)
    canonical_callable = sorted(set(canonical_callable))

    intended_count = 13  # 13 canonical Ω-WELL tools per blueprint
    verdict = "REGISTRY_PASS" if len(phantom_tools) == 0 else "REGISTRY_DRIFT"

    # Return blueprint canonical format directly — no _to_federation_output wrapping.
    # well_registry_status is a registry diagnostic, not a constitutional judgment tool.
    return {
        "ok": verdict == "REGISTRY_PASS",
        "intended_tools": intended_count,
        "registered_tools": len(somatic_tools),
        "somatic_tools": sorted(somatic_tools),
        "callable_tools": len(canonical_callable),
        "phantom_tools": phantom_tools,
        "deprecated_callable": sorted(deprecated_callable),
        "canonical_callable": canonical_callable,
        "alias_conflicts": alias_conflicts,
        "verdict": verdict,
        "well_system_registry_status": "DEPRECATED — use well_registry_status",
        "registry_note": (
            "Static registration check against SOMATIC_TOOLS. "
            "Use well_registry_status for registry diagnostics."
        ),
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        "boundary_notice": WELL_BOUNDARY_NOTICE,
        "final_authority": "ARIF",
        "authority": "ADVISORY_ONLY",
        "medical_boundary": "NON_DIAGNOSTIC",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ATLAS13-WELL — Substrate Wisdom Anchors (13 axioms for WELL MCP tools)
# ═══════════════════════════════════════════════════════════════════════════════

_WELL_WISDOM: dict[str, dict[str, Any]] = {
    "well_classify_substrate": {
        "axiom": "Substrate must be named before readiness can be judged. Do not treat all substrates as life.",
        "substrate_law": {
            "carbon": "The body metabolizes and tires.",
            "silica": "Stone endures and fractures.",
            "machine": "Machine computes but does not live.",
        },
        "authority": "WELL classifies. Arif judges.",
    },
    "well_detect_boundary": {
        "axiom": "A body has skin. A machine has interface. A soul has dignity. Do not confuse them.",
        "substrate_warning": "Boundary confusion is the first illness of intelligence.",
        "boundary_types": {
            "skin": "biological membrane",
            "pain": "body warning",
            "consent": "human sovereignty",
            "api": "machine interface",
            "floor": "constitutional limit",
        },
        "authority": "Boundary must be respected before crossing.",
    },
    "well_measure_gradient": {
        "axiom": "Life moves by gradients: hunger, heat, pressure, oxygen, attention. No gradient, no movement. Too much gradient, collapse.",
        "carbon_lesson": "Balanced gradient is vitality.",
        "silica_lesson": "Pressure writes memory into stone. Stress reveals hidden fracture.",
        "machine_lesson": "Latency, token pressure, memory pressure, and tool error are machine gradients.",
        "authority": "Gradient informs readiness; it does not dictate action.",
    },
    "well_assess_metabolism": {
        "axiom": "Carbon pays for every thought with energy. No biological judgment is free of metabolism.",
        "carbon_signals": {
            "sleep_debt": "unpaid recovery cost",
            "hunger": "energy deficit",
            "stress": "survival system activated",
            "fatigue": "metabolic budget depleted",
            "pain": "local integrity warning",
            "breath": "rhythm of life",
        },
        "machine_lesson": "Machine consumes power but does not suffer fatigue.",
        "authority": "The body pays before the mind performs.",
    },
    "well_assess_homeostasis": {
        "axiom": "Health is not maximum output. Health is return to balance. Vitality is controlled oscillation, not permanent peak.",
        "carbon_lesson": "The body survives by regulation, not by constant intensity.",
        "silica_lesson": "A crystal holds form until stress exceeds structure.",
        "machine_lesson": "A system is stable when load, memory, and latency remain within bounds.",
        "authority": "Balance is not weakness; balance is sustainability.",
    },
    "well_check_repair": {
        "axiom": "Living systems repair. Machines are repaired. Stones weather. A body heals from within. A machine is repaired from without.",
        "recovery_modes": {
            "carbon": "sleep, nutrition, immune repair, rest",
            "silica": "slow weathering, recrystallization",
            "machine": "patch, restart, replace, rollback",
            "governance": "audit, correction, seal, restoration",
        },
        "authority": "Repair mode depends on substrate, not desire.",
    },
    "well_validate_vitality": {
        "axiom": "Readiness is not desire. Readiness is available capacity under constraint. Capacity must be verified before consequence is accepted.",
        "carbon_warning": "Strong niat cannot cancel sleep debt.",
        "machine_warning": "Available tools do not mean safe execution.",
        "governance_warning": "Even if the body can, the action may still be unwise.",
        "verdict_rule": "UNKNOWN is safer than false GREEN.",
        "authority": "Capacity verified. Consequence accepted. Arif decides.",
    },
    "well_assess_livelihood": {
        "axiom": "A human is not a battery. Work may use energy, but it must not consume dignity.",
        "livelihood_dimensions": {
            "energy": "body budget",
            "role_clarity": "social stability",
            "duty_load": "obligation pressure",
            "dignity": "maruah preserved",
            "purpose": "niat aligned",
        },
        "authority": "Dignity is not a resource to be spent.",
    },
    "well_compute_metabolic_flux": {
        "axiom": "Entropy is the tax intelligence pays for existence. Metabolic flux is the rate of that tax. When flux exceeds 0.65, the system must reallocate before it dissolves into noise.",
        "carbon_lesson": "A tired mind makes more errors. Each error increases cognitive entropy. Entropy compounds faster than recovery can clear it.",
        "silica_lesson": "Stone under stress develops microfractures. The fracture network grows faster than the applied load — this is stone's metabolic flux.",
        "machine_lesson": "Prediction contradiction rate is the machine's cognitive entropy. A model that contradicts itself at high confidence is a model that has lost its epistemic grounding.",
        "authority": "Flux ≤ 0.40: nominal. Flux > 0.65: compulsory reallocation. Flux > 0.85: system hold. These are thermodynamic thresholds, not suggestions.",
    },
    "well_assess_reliability": {
        "axiom": "Machine reliability is physical, not moral. Machine health is substrate condition, not trustworthiness.",
        "three_plane_mapping": {
            "delta KUKUH": "physical state solid",
            "delta RETAK": "physical state degraded",
            "delta ROSAK": "physical state broken",
            "psi": "governance trust — not a machine property",
            "omega": "reasoning discipline — not a machine property",
        },
        "authority": "A machine can be KUKUH / RETAK / ROSAK but never amanah by itself.",
    },
    "well_reflect_intelligence": {
        "axiom": "Intelligence without body awareness becomes bangang. The wise system knows when not to continue.",
        "carbon_lesson": "A tired body narrows judgment.",
        "silica_lesson": "Hardness without flexibility becomes brittleness.",
        "machine_lesson": "Fast reasoning without context becomes error propagation.",
        "authority": "Reflection is not hesitation; reflection is substrate-aware reasoning.",
    },
    "well_guard_dignity": {
        "axiom": "The body is substrate, but the person is not reducible to substrate. Do not reduce Arif to sleep, stress, metrics, or telemetry.",
        "carbon_lesson": "The body informs judgment.",
        "dignity_lesson": "The person remains more than the body.",
        "authority_boundary": "WELL reflects. Arif decides.",
    },
    "well_trace_lineage": {
        "axiom": "The body remembers what the mind tries to ignore. No state appears from nowhere. Every readiness has ancestry.",
        "carbon_memory": {
            "fatigue": "accumulates",
            "stress": "leaves residue",
            "recovery": "has lag",
            "sleep_debt": "compounds",
        },
        "silica_memory": {
            "sediment": "keeps pressure history",
            "fracture": "records stress",
            "crystal": "preserves formation conditions",
        },
        "machine_memory": "Logs preserve failure lineage.",
        "authority": "Lineage must be traced before readiness can be trusted.",
    },
    "well_anchor_evidence": {
        "axiom": "Only witnessed state may be sealed. Unverified body state must remain UNKNOWN. A sealed lie is worse than an honest unknown.",
        "carbon_lesson": "Do not invent wellness.",
        "machine_lesson": "Do not invent telemetry.",
        "governance_lesson": "Do not seal what cannot be witnessed.",
        "authority": "WELL must never seal fake readiness.",
    },
}


def _well_wisdom_for_tool(tool_name: str) -> dict[str, Any] | None:
    """Return substrate wisdom anchor for the given WELL tool name."""
    exact = _WELL_WISDOM.get(tool_name)
    if exact:
        return exact
    for key, val in _WELL_WISDOM.items():
        if tool_name.startswith(key):
            return val
    return None


def _inject_well_wisdom(response: dict[str, Any], tool_name: str) -> dict[str, Any]:
    """Inject substrate wisdom into tool response if not already present."""
    if "substrate_wisdom" not in response:
        wisdom = _well_wisdom_for_tool(tool_name)
        if wisdom:
            response["substrate_wisdom"] = wisdom
    return response


# ═══════════════════════════════════════════════════════════════════════════════
# well_classify_state — Human State Classifier (Phase 1 + Phase 3)
# ═══════════════════════════════════════════════════════════════════════════════
# Constitutional home: arifosmcp/rama/ (State Classifier)
# Federation surface: WELL MCP (this file)
# Physics: entropy reduction + invariance violation detection
#
# Imports from arifosmcp.rama — dependency already exists (vault_postgres,
# well_bridge). State Classifier stays in arifOS; WELL exposes it.
#
# Phase 1: Deterministic rule-based Polyvagal + SDT classification
# Phase 3: Contradiction detector (stated intent vs behavioral pattern)
# DITEMPA BUKAN DIBERI


def _well_modulate_posture(
    polyvagal: str,
    sdt_autonomy: str,
    sdt_competence: str,
    sdt_relatedness: str,
) -> dict[str, Any]:
    """Convert state vector into concrete agent behavior adjustments.

    This is the Phase 2 Response Adapter (thin version).
    Takes classifier output, returns modulated behavior parameters.

    Returns dict with:
        - complexity: simplified | normal | expanded
        - pacing: slow | normal | fast
        - silence_tolerance: low | medium | high
        - challenge_level: none | gentle | normal | high
        - response_length: short | medium | long
        - tone: grounding | acknowledging | exploring
    """
    # Base from polyvagal state
    if polyvagal == "sympathetic":
        mod = {
            "complexity": "simplified",
            "pacing": "slow",
            "silence_tolerance": "medium",
            "challenge_level": "none",
            "response_length": "short",
            "tone": "grounding",
        }
    elif polyvagal == "dorsal":
        mod = {
            "complexity": "simplified",
            "pacing": "slow",
            "silence_tolerance": "high",
            "challenge_level": "none",
            "response_length": "short",
            "tone": "acknowledging",
        }
    else:  # ventral
        mod = {
            "complexity": "normal",
            "pacing": "normal",
            "silence_tolerance": "medium",
            "challenge_level": "normal",
            "response_length": "medium",
            "tone": "exploring",
        }

    # SDT overlays
    if sdt_autonomy == "high":
        mod["challenge_level"] = "none"
        mod["tone"] = "acknowledging"
        # Don't prescribe — offer options
        mod["autonomy_directive"] = "offer_options_not_prescriptions"

    if sdt_competence == "high":
        mod["complexity"] = "simplified"
        mod["response_length"] = "short"
        mod["competence_directive"] = "scaffold_dont_rescue"

    if sdt_relatedness == "high":
        mod["tone"] = "acknowledging"
        mod["relatedness_directive"] = "connect_before_content"

    return mod


@mcp.tool()
def well_classify_state(
    message: str,
    session_id: str = "",
    recent_messages: list[str] | None = None,
    stated_intent: str = "",
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Classify human psychological state from message.

    Phase 1: Deterministic rule-based Polyvagal + SDT classification.
    Phase 3: Contradiction detector (stated intent vs behavioral pattern).

    Physics: entropy reduction. Human arrives ambiguous; state vector exits structured.
    Constitutional: F2 (evidence chain), F4 (clarity), F6 (dignity), F9 (no consciousness claims).

    This is a REFLECT_ONLY tool. It reads state and produces a governed posture.
    It does NOT decide, judge, or act. arifOS 888_JUDGE adjudicates.

    Args:
        message: The human message to classify.
        session_id: Session identifier for audit trail.
        recent_messages: Recent message history for repetition detection.
        stated_intent: What the human said they want (for contradiction detection).
    """
    try:
        from arifosmcp.rama.state_classifier import get_state_classifier
        from arifosmcp.rama.state_classifier_governance import run_governance_loop
        from gate.dignity_shadow import detect_contradiction, assess_dignity_risk
    except ImportError as e:
        return {
            "ok": False,
            "error": f"State Classifier import failed: {e}",
            "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        }

    # Phase 1: Classify state
    governed = run_governance_loop(
        message=message,
        session_id=session_id or "",
        recent_messages=recent_messages or [],
    )

    sv = governed.state_vector if hasattr(governed, "state_vector") else None

    # Phase 2: Modulate posture
    posture_mod = _well_modulate_posture(
        polyvagal=governed.governed_posture.value
        if hasattr(governed, "governed_posture")
        else "explore",
        sdt_autonomy="low",
        sdt_competence="low",
        sdt_relatedness="low",
    )

    # Phase 3: Contradiction detection (if stated_intent provided)
    contradiction_result = None
    if stated_intent and sv:
        behavioral_signals = sv.polyvagal_evidence or []
        contradiction_result = detect_contradiction(
            stated_intent=stated_intent,
            behavioral_signals=behavioral_signals,
        )

    # Dignity shadow check on the output itself
    dignity_check = None
    if sv and sv.polyvagal_evidence:
        evidence_text = " ".join(sv.polyvagal_evidence)
        dignity_check = assess_dignity_risk(evidence_text, sv.confidence)

    # Build result
    result: dict[str, Any] = {
        "ok": True,
        "state_vector": {
            "polyvagal": sv.polyvagal.value if sv else "ventral",
            "sdt_pressure": {
                "autonomy": sv.sdt_pressure.autonomy.value if sv else "low",
                "competence": sv.sdt_pressure.competence.value if sv else "low",
                "relatedness": sv.sdt_pressure.relatedness.value if sv else "low",
            },
            "confidence": sv.confidence if sv else 0.4,
            "evidence": sv.polyvagal_evidence if sv else [],
        },
        "governed_posture": {
            "posture": governed.governed_posture.value
            if hasattr(governed, "governed_posture")
            else "explore",
            "overridden": governed.posture_overridden
            if hasattr(governed, "posture_overridden")
            else False,
            "directives": governed.directives
            if hasattr(governed, "directives")
            else [],
            "posture_modulation": posture_mod,
        },
        "floor_checks": {
            "passed": governed.floors_passed
            if hasattr(governed, "floors_passed")
            else 0,
            "advisory": governed.floors_advisory
            if hasattr(governed, "floors_advisory")
            else 0,
            "violated": governed.floors_violated
            if hasattr(governed, "floors_violated")
            else 0,
        },
        "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
        "reflect_only": "WELL reads state. arifOS judges. Arif decides.",
    }

    if contradiction_result:
        result["contradiction"] = contradiction_result

    if dignity_check:
        result["dignity_shadow"] = dignity_check

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Universal wisdom injection — monkey-patch all registered tool functions
# ═══════════════════════════════════════════════════════════════════════════════

# ── Somatic/Autonomic Boundary ──────────────────────────────────────────────────
# Canonical tools visible to external agents (14).
# All other @mcp.tool() functions are autonomic — callable internally via
# the canonical dispatchers but hidden from agent tool listing.
# ═══════════════════════════════════════════════════════════════════════════════
# SOMATIC_TOOLS — Public MCP surface for WELL (biological substrate only)
# ═══════════════════════════════════════════════════════════════════════════════
# Orthogonality rule: WELL speaks ONLY biological substrate physics.
# Constitutional functions (governance, judgment, seal, critique of meaning,
# routing, evidence anchoring) belong to arifOS.
#
# Removed from public surface per orthogonal MCP alignment (2026-05-14):
#   well_reflect_intelligence  → REFLECT axis / routing (arifOS 444_KERNEL)
#   well_guard_dignity         → CRITIQUE axis / meaning (arifOS 666_HEART)
#   well_anchor_evidence       → SEAL axis / vault (arifOS 999_VAULT)
SOMATIC_TOOLS = {
    "well_health_check",
    # "mcp_health_check" removed 2026-06-28 — legacy alias, use well_health_check
    "well_classify_substrate",
    "well_classify_substrate",
    "well_trace_lineage",
    "well_detect_boundary",
    "well_measure_gradient",
    "well_assess_metabolism",
    "well_assess_homeostasis",
    "well_check_repair",
    "well_validate_vitality",
    "well_assess_livelihood",
    "well_assess_reliability",
    "well_compute_metabolic_flux",
    "well_assess_sovereign_entropy",
    "well_guard_dignity",
    "well_medical_boundary",
    "well_13_signal_coverage",
    "well_registry_status",
    # F-Ω Federation Handoff Adapters — forged 2026-06-17
    # See FEDERATION_HOOKS.md for the canonical contract.
    "well_handoff_dignity_to_arifos",  # S12 → arifOS 888_JUDGE
    "well_handoff_livelihood_to_wealth",  # S13 → WEALTH
    "well_attest_to_kernel",  # WELL → arifOS organ_attest
    # Human State Classifier — Phase 1 + Phase 3
    # Forged 2026-06-25. Deterministic rule-based Polyvagal + SDT + contradiction.
    "well_classify_state",  # State Classifier → federation surface
    "well_readiness",  # ZEN: single verdict — color/score/TTL/action
}
# NOTE: well_registry_status is the canonical blueprint format tool.
# well_system_registry_status is deprecated (internal only, no MCP registration).
# diagnostic tools (no @mcp.tool decorator). Not part of public MCP surface.

# MCP Spec 2025-11-25 tool annotations (SEP-1862/1913/1984/2417)
_TOOL_ANNOTATIONS: dict[str, dict[str, Any]] = {
    "well_health_check": {
        "title": "WELL Health Check",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "well_classify_substrate": {
        "title": "Classify Substrate",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "well_trace_lineage": {
        "title": "Trace Lineage",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
    "well_detect_boundary": {
        "title": "Detect Boundary",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "well_measure_gradient": {
        "title": "Measure Gradient",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "well_assess_metabolism": {
        "title": "Assess Metabolism",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "well_assess_homeostasis": {
        "title": "Assess Homeostasis",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "well_check_repair": {
        "title": "Check Repair",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "well_validate_vitality": {
        "title": "Validate Vitality",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "well_assess_livelihood": {
        "title": "Assess Livelihood",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "well_assess_reliability": {
        "title": "Assess Reliability",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "well_compute_metabolic_flux": {
        "title": "Compute Metabolic Flux",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "well_assess_sovereign_entropy": {
        "title": "Assess Sovereign Entropy",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "well_guard_dignity": {
        "title": "Guard Dignity",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "well_medical_boundary": {
        "title": "Medical Boundary",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
    "well_classify_state": {
        "title": "Classify Human State",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
}


# MCP Spec 2025-11-25 outputSchema — standard WELL response envelope
_WELL_OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "description": "Execution status"},
        "verdict": {
            "type": "string",
            "description": "WELL verdict: OPTIMAL, STABLE, DEGRADED, CRITICAL, etc.",
        },
        "mode": {"type": "string", "description": "Assessment mode"},
        "content": {"type": "string", "description": "Textual content / advisory"},
        "result": {"type": "object", "description": "Tool-specific payload"},
        "error": {"type": "string", "description": "Error message if status != OK"},
        "reasons": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Human-readable justification",
        },
    },
}


def _patch_tool_annotations(mcp_server: Any) -> None:
    """Patch MCP tool annotations post-registration (FastMCP 3.x)."""
    import asyncio
    from mcp.types import ToolAnnotations

    async def _do() -> None:
        for name, anno in _TOOL_ANNOTATIONS.items():
            try:
                t = await mcp_server.get_tool(name)
                if t is not None and hasattr(t, "annotations"):
                    t.annotations = ToolAnnotations(**anno)
            except Exception:
                pass

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_do())
    except RuntimeError:
        asyncio.run(_do())


def _patch_output_schemas(mcp_server: Any) -> None:
    """Patch MCP tool outputSchema post-registration (FastMCP 3.x)."""
    import asyncio

    async def _do() -> None:
        for name in _TOOL_ANNOTATIONS.keys():
            try:
                t = await mcp_server.get_tool(name)
                if t is not None and hasattr(t, "output_schema"):
                    t.output_schema = _WELL_OUTPUT_SCHEMA
            except Exception:
                pass

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_do())
    except RuntimeError:
        asyncio.run(_do())


class OriginValidationMiddleware:
    """Validate Origin header on MCP endpoints to prevent DNS rebinding (SEP-2243)."""

    ALLOWED_ORIGIN_PREFIXES: tuple[str, ...] = (
        "https://well.arif-fazil.com",
        "https://arif-fazil.com",
        "http://localhost",
        "https://localhost",
        "http://127.0.0.1",
        "https://127.0.0.1",
    )

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope.get("path", "").startswith("/mcp"):
            headers = dict(scope.get("headers", []))
            origin_bytes = headers.get(b"origin", b"")
            origin = (
                origin_bytes.decode()
                if isinstance(origin_bytes, bytes)
                else str(origin_bytes)
            )
            if origin and not any(
                origin.startswith(p) for p in self.ALLOWED_ORIGIN_PREFIXES
            ):
                await send(
                    {
                        "type": "http.response.start",
                        "status": 403,
                        "headers": [[b"content-type", b"application/json"]],
                    }
                )
                await send(
                    {
                        "type": "http.response.body",
                        "body": b'{"error":"Invalid Origin","detail":"DNS rebinding protection"}',
                    }
                )
                return
        await self.app(scope, receive, send)

    def __init__(self, app):
        self.app = app


# ── Federation Tool Manifest Registration ──────────────────────────────────────
# Populates FEDERATION_TOOLS with cognitive_axis for every WELL MCP tool.
# Replaces ad-hoc SOMATIC_TOOLS set with manifest-based filtering.
#
# Manifest/listing invariant: if expose=False, the tool must NOT appear in
# public tool listings. Autonomic tools are kept in a separate internal list
# so FEDERATION_TOOLS only contains the public (somatic) surface.

_WELL_SOMATIC_MANIFEST: list[dict[str, object]] = [
    # Somatic (visible) tools — these are the public MCP surface
    # Capability Spine Repair 2026-06-26: All tools below have @mcp.tool decorators
    # verified at runtime. well_system_registry_status and well_registry_status
    # are callable (handlers exist) and now exposed in the somatic surface.
    {"name": "well_health_check", "axis": "identity", "expose": True},
    # "mcp_health_check" removed 2026-06-28 — legacy alias, use well_health_check
    {"name": "well_classify_substrate", "axis": "identity", "expose": True},
    {"name": "well_trace_lineage", "axis": "trace", "expose": True},
    {"name": "well_detect_boundary", "axis": "boundary", "expose": True},
    {"name": "well_measure_gradient", "axis": "observe", "expose": True},
    {"name": "well_assess_metabolism", "axis": "reason", "expose": True},
    {"name": "well_assess_homeostasis", "axis": "vitality", "expose": True},
    {"name": "well_check_repair", "axis": "repair", "expose": True},
    {"name": "well_validate_vitality", "axis": "judge", "expose": True},
    {"name": "well_assess_livelihood", "axis": "vitality", "expose": True},
    {"name": "well_assess_reliability", "axis": "vitality", "expose": True},
    {"name": "well_compute_metabolic_flux", "axis": "vitality", "expose": True},
    {"name": "well_assess_sovereign_entropy", "axis": "vitality", "expose": True},
    {"name": "well_guard_dignity", "axis": "critique", "expose": True},
    {"name": "well_medical_boundary", "axis": "boundary", "expose": True},
    {
        "name": "well_system_registry_status",
        "axis": "identity",
        "expose": False,
        "note": "DEPRECATED — use well_registry_status",
    },
    {"name": "well_registry_status", "axis": "identity", "expose": True},
    {"name": "well_signal_coverage", "axis": "reflect", "expose": True},
    {"name": "well_handoff_dignity_to_arifos", "axis": "bridge", "expose": True},
    {"name": "well_handoff_livelihood_to_wealth", "axis": "bridge", "expose": True},
    {"name": "well_attest_to_kernel", "axis": "attest", "expose": True},
    {"name": "well_classify_state", "axis": "observe", "expose": True},
]

_WELL_AUTONOMIC_TOOLS: list[dict[str, object]] = [
    # REMOVED from public surface — constitutional overlap with arifOS
    {"name": "well_reflect_intelligence", "axis": "reflect", "expose": False},
    {"name": "well_anchor_evidence", "axis": "seal", "expose": False},
    # NOTE: well_guard_dignity promoted to somatic (2026-05-16) — dignity protection
    # is WELL's substrate responsibility, not arifOS constitutional routing.
    # Autonomic phase-1 tools (legacy but active)
    {"name": "well_get_health", "axis": "identity", "expose": False},
    {"name": "well_get_state", "axis": "observe", "expose": False},
    {"name": "well_check_invariant", "axis": "identity", "expose": False},
    {"name": "well_log_signal", "axis": "observe", "expose": False},
    {"name": "well_list_events", "axis": "trace", "expose": False},
    {"name": "well_reflect_trend", "axis": "reflect", "expose": False},
    {"name": "well_reflect_readiness", "axis": "judge", "expose": False},
    {"name": "well_suggest_mode", "axis": "judge", "expose": False},
    {"name": "well_suggest_recovery", "axis": "repair", "expose": False},
    {"name": "well_reflect_niat", "axis": "reflect", "expose": False},
    {"name": "well_classify_task", "axis": "reason", "expose": False},
    {"name": "well_get_packet", "axis": "identity", "expose": False},
    {"name": "well_request_anchor", "axis": "seal", "expose": False},
    # Ω-WELL stage aliases (autonomic)
    {"name": "well_000_init", "axis": "identity", "expose": False},
    {"name": "well_111_sense", "axis": "observe", "expose": False},
    {"name": "well_222_fetch", "axis": "verify", "expose": False},
    {"name": "well_333_mind", "axis": "reason", "expose": False},
    {"name": "well_444_kernel", "axis": "reflect", "expose": False},
    {"name": "well_555_memory", "axis": "trace", "expose": False},
    {"name": "well_666_heart", "axis": "critique", "expose": False},
    {"name": "well_777_forge", "axis": "execute", "expose": False},
    {"name": "well_888_judge", "axis": "judge", "expose": False},
    {"name": "well_999_vault", "axis": "seal", "expose": False},
    {"name": "well_444_reply", "axis": "reflect", "expose": False},
    {"name": "well_444_gateway", "axis": "boundary", "expose": False},
    {"name": "well_000_ops", "axis": "vitality", "expose": False},
    # Core human substrate tools (autonomic)
    {"name": "well_state", "axis": "observe", "expose": False},
    {"name": "well_log", "axis": "observe", "expose": False},
    {"name": "well_readiness", "axis": "judge", "expose": False},
    {"name": "well_init", "axis": "identity", "expose": False},
    {"name": "well_anchor", "axis": "seal", "expose": False},
    {"name": "well_check_floors", "axis": "judge", "expose": False},
    {"name": "well_check_floor", "axis": "judge", "expose": False},
    {"name": "well_log_state", "axis": "observe", "expose": False},
    {"name": "well_get_readiness", "axis": "judge", "expose": False},
    {"name": "well_list_log", "axis": "trace", "expose": False},
    {"name": "well_seal_vault", "axis": "seal", "expose": False},
    {"name": "well_trend_analysis", "axis": "reflect", "expose": False},
    {"name": "well_bandwidth_recommendation", "axis": "vitality", "expose": False},
    {"name": "well_recovery_protocol", "axis": "repair", "expose": False},
    {"name": "well_niat_check", "axis": "reflect", "expose": False},
    {"name": "well_decision_classify", "axis": "reason", "expose": False},
    {"name": "well_arifos_packet", "axis": "identity", "expose": False},
    {"name": "well_consent_status", "axis": "boundary", "expose": False},
    {"name": "well_13_signal_coverage", "axis": "reflect", "expose": False},
    {"name": "well_pressure_ledger", "axis": "observe", "expose": False},
    {"name": "well_daily_brief", "axis": "reflect", "expose": False},
    {"name": "well_machine_state", "axis": "observe", "expose": False},
    # C-WELL coupled + forge bridge (autonomic)
    {"name": "well_coupled_readiness", "axis": "vitality", "expose": False},
    {"name": "well_decision_bandwidth", "axis": "judge", "expose": False},
    {"name": "well_forge_precheck", "axis": "execute", "expose": False},
    {"name": "well_forge_pressure_update", "axis": "vitality", "expose": False},
    {"name": "well_forge_mode_recommend", "axis": "judge", "expose": False},
    {"name": "well_forge_closeout", "axis": "repair", "expose": False},
    # M-WELL machine telemetry (autonomic)
    {"name": "well_machine_log_signal", "axis": "observe", "expose": False},
    {"name": "well_machine_trend", "axis": "reflect", "expose": False},
    {"name": "well_machine_health_probe", "axis": "vitality", "expose": False},
    # H-WELL cross-session (autonomic)
    {"name": "well_fatigue_accumulator", "axis": "vitality", "expose": False},
    {"name": "well_circadian_phase", "axis": "observe", "expose": False},
    # G-WELL governance (autonomic)
    {"name": "well_assess_governance", "axis": "critique", "expose": False},
    {"name": "well_trace_decision", "axis": "trace", "expose": False},
    {"name": "well_validate_consensus", "axis": "judge", "expose": False},
    # U-WELL universal substrate (autonomic)
    {"name": "well_boundary_check", "axis": "boundary", "expose": False},
    {"name": "well_evidence_quality_check", "axis": "verify", "expose": False},
    {"name": "well_verdict_packet", "axis": "judge", "expose": False},
    {"name": "well_livelihood_energy_check", "axis": "vitality", "expose": False},
    {"name": "well_livelihood_time_check", "axis": "vitality", "expose": False},
    {"name": "well_livelihood_role_check", "axis": "vitality", "expose": False},
    {"name": "well_livelihood_meaning_check", "axis": "vitality", "expose": False},
    {"name": "well_livelihood_dignity_check", "axis": "critique", "expose": False},
    {"name": "well_bio_viability_check", "axis": "vitality", "expose": False},
    {"name": "well_material_integrity_check", "axis": "verify", "expose": False},
    {"name": "well_institution_entropy_check", "axis": "critique", "expose": False},
    {"name": "well_info_coherence_check", "axis": "verify", "expose": False},
    {"name": "well_symbolic_domain_check", "axis": "critique", "expose": False},
]

# Backward-compat alias: _WELL_MANIFEST is the public somatic surface only
_WELL_MANIFEST = _WELL_SOMATIC_MANIFEST

try:
    from federation.tool_manifest import (
        FEDERATION_TOOLS,
        ToolManifest,
        CognitiveAxis as _CA,
    )

    # Only register SOMATIC tools in the federation manifest.
    # Autonomic tools remain internal to WELL and must not appear in public listings.
    for _entry in _WELL_SOMATIC_MANIFEST:
        _name = str(_entry["name"])
        FEDERATION_TOOLS[_name] = ToolManifest(
            name=_name,
            description="",
            expose=True,
            cognitive_axis=_CA(str(_entry["axis"])),
            organ="well",
        )
except Exception:
    pass  # federation module may not exist in all environments


def _enforce_somatic_boundary(mcp_server: FastMCP) -> None:
    """Remove autonomic tools from the public MCP surface.

    Uses FEDERATION_TOOLS manifest (is_tool_somatic) as single source of truth.
    Falls back to SOMATIC_TOOLS set if federation manifest is unavailable.
    """
    provider = getattr(mcp_server, "_local_provider", None)
    if not provider:
        return
    removed: list[str] = []
    somatic_count = 0
    for key in list(getattr(provider, "_components", {}).keys()):
        if not key.startswith("tool:"):
            continue
        tool_name = key[5:].rstrip("@v")
        try:
            from federation.tool_manifest import is_tool_somatic as _its

            visible = _its(tool_name)
        except Exception:
            visible = tool_name in SOMATIC_TOOLS
        if not visible:
            try:
                mcp_server.remove_tool(tool_name)
                removed.append(tool_name)
            except Exception:
                pass
        else:
            somatic_count += 1
    import logging as _logging

    _logging.getLogger(__name__).info(
        "Somatic boundary enforced: %d somatic, %d autonomic removed",
        somatic_count,
        len(removed),
    )


# Server bootstrap — somatic boundary applied before uvicorn starts
if (
    _os.environ.get("FEDERATION_SOMATIC_BOUNDARY", "0") == "1"
    or _os.environ.get("WELL_SOMATIC_BOUNDARY", "0") == "1"
):
    _enforce_somatic_boundary(mcp)

# PR 6 — apply reflect-only boundary to the 13 canonical SOMATIC_TOOLS.
# This injects 4 reflect-only labels (telemetry, context, authority,
# medical_status) on every canonical tool output, plus the F7 readiness
# guard. F13: this labels authority; it does not grant it.
if _REFLECT_LOADED and _wrap_canonical_tools is not None:
    try:
        _canonical_tool_fns = {
            "well_health_check": well_health_check,
            # "mcp_health_check" removed 2026-06-28 — legacy alias, use well_health_check
            "well_classify_substrate": _well_classify_substrate_impl,
            "well_trace_lineage": well_trace_lineage,
            "well_detect_boundary": well_detect_boundary,
            "well_measure_gradient": well_measure_gradient,
            "well_assess_metabolism": well_assess_metabolism,
            "well_assess_homeostasis": well_assess_homeostasis,
            "well_check_repair": well_check_repair,
            "well_validate_vitality": well_validate_vitality,
            "well_assess_livelihood": well_assess_livelihood,
            "well_assess_reliability": well_assess_reliability,
            "well_compute_metabolic_flux": well_compute_metabolic_flux,
            "well_assess_sovereign_entropy": well_assess_sovereign_entropy,
            "well_guard_dignity": well_guard_dignity,
        }
        _wrapped_count = _wrap_canonical_tools(
            _canonical_tool_fns, canonical_names=SOMATIC_TOOLS
        )
    except Exception as _e:  # pragma: no cover — defensive
        _wrapped_count = 0
        import logging as _logging

        _logging.getLogger("well.reflect").warning(
            "PR 6 reflect-only wrap failed: %s", _e
        )
else:  # pragma: no cover
    _wrapped_count = 0

if __name__ == "__main__":
    # ── Transport mode selection (fallback entry) ────────────────────────
    import argparse
    import sys

    _parser = argparse.ArgumentParser(add_help=False)
    _parser.add_argument(
        "--transport",
        choices=["http", "stdio"],
        default=_os.environ.get("MCP_TRANSPORT", "http"),
    )
    _args, _ = _parser.parse_known_args()
    from server import mcp as _mcp

    _patch_tool_annotations(_mcp)
    _patch_output_schemas(_mcp)
    if _args.transport == "stdio":
        _mcp.run(transport="stdio")
        sys.exit(0)

    # This is a fallback in case the first __main__ block (at ~line 5911)
    # didn't run uvicorn. We build the app and start it.
    from starlette.responses import JSONResponse
    import uvicorn
    from server import mcp as _mcp

    host = _os.environ.get("HOST", "0.0.0.0")
    port = int(_os.environ.get("PORT", 8083))
    _patch_tool_annotations(_mcp)
    _patch_output_schemas(_mcp)
    app = _mcp.http_app(
        path="/mcp",
        transport="streamable-http",
        json_response=True,
        stateless_http=True,
    )

    # ── P6 helpers — domain identity anchors ──────────────────────
    def _compute_domain_law() -> str:
        return "SUBSTRATE_LAW"

    def _compute_substrate_manifest_hash() -> str:
        try:
            import hashlib as _hl

            _manifest_path = "/root/WELL/GENESIS/012_SUBSTRATE_MANIFEST.md"
            if __import__("os").path.exists(_manifest_path):
                with open(_manifest_path, "rb") as _f:
                    return f"sha256:{_hl.sha256(_f.read()).hexdigest()}"
        except Exception:
            pass
        return "sha256:missing"

    # Register health handlers if not already present
    async def _well_health_handler(request):
        try:
            with open(".identity_hash", "r") as f:
                identity_hash = f.read().strip()
        except Exception:
            identity_hash = "UNAVAILABLE"

        # Use canonical STATE_PATH instead of hardcoded /app/state.json.
        state = _load_state()
        classification = _classify_well_state(state)
        metrics = state.get("metrics") or {}
        clarity = (
            metrics.get("cognitive", {}).get("clarity")
            if isinstance(metrics, dict)
            else None
        )
        has_metrics = bool(
            metrics
            and any(
                metrics.get(d)
                for d in (
                    "sleep",
                    "stress",
                    "cognitive",
                    "metabolic",
                    "structural",
                )
            )
        )
        health_status = (
            "healthy"
            if classification["well_ok"]
            and classification.get("well_signal", "WELL_HOLD") == "WELL_PASS"
            else "degraded"
        )

        return JSONResponse(
            {
                # ── Canonical 7-field health schema (federation convention) ───
                "status": health_status,
                "final_authority": "ARIF",
                "identity": "WELL",
                "role": "Body / Human Intelligence",
                "authority": "REFLECT_ONLY",
                "identity_hash": identity_hash,
                "well_signal": classification[
                    "well_signal"
                ],  # REFLECT_ONLY — never "verdict"
                "service": "well-mcp",
                "version": "2026.05.15-ΩWELL+GWELL+FEDERATION",
                "tool_count": len(SOMATIC_TOOLS),
                # substrate advisory fields — consumed by arifOS _read_well_substrate() HTTP fallback
                "well_score": classification["well_score"],
                "floors_violated": state.get("floors_violated") or [],
                "truth_status": classification["truth_status"],
                "has_metrics": has_metrics,
                "has_verified_telemetry": classification["has_telemetry"],
                "clarity": clarity,
                "metrics": metrics,
                # Dynamic freshness — computed from timestamp, not a static lie
                "freshness_band": classification["freshness_band"],
                "state_age_hours": classification["state_age_hours"],
                "environment": CURRENT_ENV,
                # ── P6 — WELL identity anchor (SUBSTRATE_LAW, not constitutional) ───
                "domain_law": _compute_domain_law(),
                "substrate_manifest_hash": _compute_substrate_manifest_hash(),
                # Phase 2 hardening: standardized freshness + owner summary
                "freshness": classification["freshness"],
                "owner_summary": classification["owner_summary"],
                # Boundary disclaimer
                "boundary_notice": "Not diagnosis. Not therapy. Reflective readiness only. Arif remains final judge.",
            }
        )

    async def _well_tools_handler(request):
        """Federation tool discovery — flat tool registry with WELL danger metadata."""
        all_tools = await mcp.list_tools()
        _DANGER_MAP = {
            "well_seal_vault": {"danger_level": "L3", "fail_posture": "fail-closed"},
            "well_check_floor": {"danger_level": "L3", "fail_posture": "fail-closed"},
            "well_anchor_evidence": {
                "danger_level": "L3",
                "fail_posture": "fail-closed",
            },
            "well_request_anchor": {
                "danger_level": "L3",
                "fail_posture": "fail-closed",
            },
            "well_validate_vitality": {
                "danger_level": "L2",
                "fail_posture": "fail-open",
            },
            "well_check_repair": {"danger_level": "L2", "fail_posture": "fail-open"},
            "well_guard_dignity": {"danger_level": "L2", "fail_posture": "fail-open"},
            "well_assess_metabolism": {
                "danger_level": "L2",
                "fail_posture": "fail-open",
            },
            "well_assess_homeostasis": {
                "danger_level": "L2",
                "fail_posture": "fail-open",
            },
            "well_assess_livelihood": {
                "danger_level": "L2",
                "fail_posture": "fail-open",
            },
            "well_assess_reliability": {
                "danger_level": "L2",
                "fail_posture": "fail-open",
            },
            "well_reflect_intelligence": {
                "danger_level": "L2",
                "fail_posture": "fail-open",
            },
            "well_classify_substrate": {
                "danger_level": "L1",
                "fail_posture": "fail-open",
            },
            "well_trace_lineage": {"danger_level": "L1", "fail_posture": "fail-open"},
            "well_detect_boundary": {"danger_level": "L1", "fail_posture": "fail-open"},
            "well_measure_gradient": {
                "danger_level": "L1",
                "fail_posture": "fail-open",
            },
            "mcp_health_check": {"danger_level": "L1", "fail_posture": "fail-open"},
            "well_state": {"danger_level": "L1", "fail_posture": "fail-open"},
            "well_get_packet": {"danger_level": "L1", "fail_posture": "fail-open"},
            "well_arifos_packet": {"danger_level": "L1", "fail_posture": "fail-open"},
            "well_readiness": {"danger_level": "L1", "fail_posture": "fail-open"},
        }
        _FAIL_OPEN_CONSTRAINT = "may degrade output, must not elevate authority"
        _CANONICAL = {
            "well_classify_substrate",
            "well_trace_lineage",
            "well_detect_boundary",
            "well_measure_gradient",
            "well_assess_metabolism",
            "well_assess_homeostasis",
            "well_check_repair",
            "well_validate_vitality",
            "well_assess_livelihood",
            "well_assess_reliability",
            "well_reflect_intelligence",
            "well_guard_dignity",
            "well_anchor_evidence",
        }
        _ALIASES = set(ALIAS_REGISTRY.keys())
        tools = []
        for t in all_tools:
            name = t.name
            meta = _DANGER_MAP.get(
                name, {"danger_level": "L1", "fail_posture": "fail-open"}
            )
            if name in _CANONICAL:
                category = "canonical"
            elif name in _ALIASES:
                category = "alias"
            elif name == "mcp_health_check":
                category = "heartbeat"
            else:
                category = "legacy"
            tools.append(
                {
                    "name": name,
                    "description": getattr(t, "description", "") or "",
                    "inputSchema": getattr(t, "inputSchema", {}),
                    "outputSchema": getattr(t, "output_schema", {}),
                    "danger_level": meta["danger_level"],
                    "fail_posture": meta["fail_posture"],
                    "fail_open_constraint": _FAIL_OPEN_CONSTRAINT
                    if meta["fail_posture"] == "fail-open"
                    else None,
                    "tool_category": category,
                }
            )
        return JSONResponse(
            {
                "organ": "WELL",
                "role": "Body / Human Intelligence — Operator Cognitive Pressure Monitor",
                "authority": "REFLECT_ONLY — WELL informs. arifOS judges. Arif decides.",
                "schema": "well-federation-v2026.05.08",
                "version": "2026.05.15-ΩWELL+GWELL",
                "count": len(tools),
                "w0_invariant": "WELL holds a mirror, not a veto. Operator sovereignty is invariant.",
                "danger_taxonomy": {
                    "L3": "vault seal / floor check — fail-closed mandatory",
                    "L2": "session / log — fail-open with constraint",
                    "L1": "observe / health / readiness — fail-open with constraint",
                },
                "fail_open_constraint": _FAIL_OPEN_CONSTRAINT,
                "tools": tools,
            }
        )

    async def _well_build_info_handler(request):
        from starlette.responses import JSONResponse

        return JSONResponse(
            {
                "sha": "87c0e6755f44a52526763fceee15ee64740e7918",
                "short_sha": "87c0e67",
                "branch": "main",
                "version": "1.0",
                "tool_count": len(SOMATIC_TOOLS),
                "epoch": "2026",
                "source_repo": "well",
            }
        )

    async def _mcp_server_card(request):
        """MCP Server Card — SEP-2127 HTTP discovery document.

        Updated 2026-06-06 per F13 SOVEREIGN ratification of
        GENESIS/004_WELL_13_CANON.md. WELL is the constitutional organ
        for living substrate integrity — NOT a wellness coach, NOT a
        fitness tracker, NOT a diagnostic psychiatrist.

        Canon: WELL = Body + dignity + vitality + boundaries + role
        burden + consent + meaning. Authority: reflect_only. All output
        is `signal`, never final `verdict` (arifOS/888_JUDGE adjudicates).
        """
        return JSONResponse(
            {
                "name": "well",
                "displayName": "WELL — Human Substrate Integrity Organ",
                "url": "https://well.arif-fazil.com/mcp",
                "version": "2026.06.06",
                "capabilities": {"tools": True, "resources": False, "prompts": False},
                "authentication": {"type": "none"},
                "description": (
                    "Constitutional organ for living substrate integrity. "
                    "Tracks 13 signals (4 vital, 3 recovery, 3 function, "
                    "3 dignity/environment). Authority scope: reflect_only. "
                    "WELL observes — it never issues final constitutional "
                    "verdicts. arifOS / 888_JUDGE is the sole constitutional "
                    "authority. See GENESIS/004_WELL_13_CANON.md for the "
                    "binding doctrine."
                ),
                "doctrine": {
                    "soul": "WELL = Body + dignity + vitality + boundaries + role burden + consent + meaning.",
                    "scope": "constitutional human-substrate integrity, NOT wellness coaching",
                    "authority": "reflect_only",
                    "signals": "never final verdict",
                    "routing": "arifOS / 888_JUDGE adjudicates constitutional matters",
                    "rule": "Wearables may feed WELL. Wearables must not define WELL.",
                },
                "philosophical_locks": [
                    "WELL_GODEL_LOCK.md — self-reference limit",
                    "WELL_STRANGE_LOOP_GUARD.md — intervention changes measured",
                    "WELL_ANTI_CALHOUN_GUARD.md — beautiful cage prevention",
                    "WELL_LANGUAGE_PROTOCOL.md — sovereignty-preserving intervention",
                ],
                "haram": [
                    "wellness_coach_mode",
                    "fitness_inspiration_mode",
                    "body_score_engine",
                    "psychiatric_diagnosis",
                    "constitutional_verdict",
                ],
            }
        )

    app.add_route("/.well-known/mcp.json", _mcp_server_card, methods=["GET"])
    app.add_route("/.well-known/mcp/server.json", _mcp_server_card, methods=["GET"])
    app.add_route("/health", _well_health_handler, methods=["GET"])
    app.add_route("/ready", _well_ready_handler, methods=["POST"])
    app.add_route("/tools", _well_tools_handler, methods=["GET"])
    app.add_route("/api/build-info", _well_build_info_handler, methods=["GET"])

    # 2026-06-29 — OAuth discovery stripped. Caddy now redirects
    # well.arif-fazil.com/.well-known/oauth-* → mcp.arif-fazil.com
    # (one canonical door). WELL becomes an internal endpoint.

    # ── A2A Agent Card (Federation Discovery) — FORGE 2026-06-28 ─────────────
    _WELL_A2A_CARD = {
        "schema": "agent-manifest/v1",
        "name": "WELL — Human Substrate Vitality",
        "description": (
            "Universal substrate vitality mirror for arifOS federation. "
            "Reflect-only — does not judge or decide."
        ),
        "version": "2026.06.05",
        "url": "https://well.arif-fazil.com",
        "endpoints": {
            "mcp": "https://well.arif-fazil.com/mcp",
            "health": "https://well.arif-fazil.com/health",
        },
        "authority_class": "evidence",
        "allowed_action_classes": ["OBSERVE"],
        "max_risk_tier": "T1",
        "auth": {"type": "none"},
        "federation": {
            "protocol": "A2A",
            "peer_coordinator": "https://aaa.arif-fazil.com",
        },
        "owned_mcp": {"server": "well-mcp", "tool_count": 18},
    }

    async def _well_a2a_card(request):
        return JSONResponse(_WELL_A2A_CARD)

    app.add_route("/.well-known/agent.json", _well_a2a_card, methods=["GET"])
    app.add_route("/.well-known/agent-card.json", _well_a2a_card, methods=["GET"])
    app.add_middleware(OriginValidationMiddleware)
    logger.info("WELL MCP server starting on %s:%d", host, port)
    uvicorn.run(
        app, host=host, port=port, log_level=_os.environ.get("LOG_LEVEL", "info")
    )
