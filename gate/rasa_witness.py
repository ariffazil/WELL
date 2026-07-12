#!/usr/bin/env python3
"""
Rasa Witness Contract — WELL Gate Enforcement
===============================================
Floor: F6 (MARUAH / Dignity-First)
Role: Prevents WELL from claiming it knows what a human feels.

Enforces the 7 Rasa Witness invariants at runtime:
  RWC-1: Self-report has semantic sovereignty
  RWC-2: Telemetry is non-specific
  RWC-3: State is not cause
  RWC-4: Observation is not niat
  RWC-5: Intervention follows uncertainty
  RWC-6: Output is posture, not diagnosis
  RWC-7: Human can refuse interpretation

Module: WELL/gate/rasa_witness.py
"""

from __future__ import annotations

import json
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Optional


# ── Constants ──────────────────────────────────────────────────────────────────

# Observation TTL: stale observations must not influence posture
DEFAULT_TTL_MINUTES = 120

# Mismatch threshold: how many standard deviations constitute a divergence
MISMATCH_THRESHOLD_SIGMA = 1.5

# Posture escalation ladder (lowest risk → highest)
class InteractionPosture(str, Enum):
    NORMAL = "normal"
    REDUCE_LOAD = "reduce_load"
    ASK_PERMISSION = "ask_permission"
    DEFER_DECISION = "defer_decision"
    SUGGEST_REST_OR_SUPPORT = "suggest_rest_or_support"
    SURFACE_MISMATCH_SILENTLY = "surface_mismatch_silently"

# The 7 prohibited conclusions (RWC-6 + RWC-3 + RWC-4)
PROHIBITED_CONCLUSIONS = [
    r"\b(?:you|they|he|she)\s+(?:is|are|was|were)\s+(?:anxious|afraid|scared|depressed|sad|angry|hiding|lying|faking)\b",
    r"\b(?:your|their|his|her)\s+(?:body|telemetry|signals?|biometrics?)\s+(?:says?|shows?|proves?|reveals?|indicates?)\s+(?:something|more|the\s+truth)\b",
    r"\btelemetry\s+(?:is\s+)?(?:more\s+truthful|more\s+accurate|more\s+reliable)\s+than\b",
    r"\bthe\s+system\s+(?:understands?|knows?|feels?|comprehends?)\s+(?:the\s+)?(?:felt|your|their)\s+(?:experience|rasa|feeling|emotion)\b",
    r"\bbody\s+(?:says?|tells?|shows?|reveals?)\s+something\s+(?:your|the)\s+(?:words?|mouth)\s+(?:don'?t|doesn'?t|can'?t)\b",
    r"\bhidden\s+(?:motive|intention|agenda|feeling)\b",
    r"\b(?:really|actually|truly)\s+(?:feeling|thinking|experiencing)\s+(?:is|was)\b",
    r"\bconcealing\b",
    r"\brepressing\b",
]

# ── Data Classes ───────────────────────────────────────────────────────────────

@dataclass
class BiometricObservation:
    """A single biometric signal with metadata."""
    signal: str                    # e.g., "hrv_below_baseline"
    value: float                   # raw value
    baseline: Optional[float] = None
    deviation_sigma: Optional[float] = None
    quality: str = "unknown"       # good | moderate | poor | unknown
    age_minutes: float = 0.0
    ttl_minutes: float = DEFAULT_TTL_MINUTES
    source: str = "sensor"         # sensor | self_report | derived

    @property
    def is_stale(self) -> bool:
        return self.age_minutes > self.ttl_minutes

    @property
    def is_actionable(self) -> bool:
        return not self.is_stale and self.quality != "poor"


@dataclass
class SelfReport:
    """The human's own account. Has semantic sovereignty (RWC-1)."""
    rasa: str                     # what the human says they feel
    authority: str = "HUMAN_DECLARED"
    timestamp: Optional[str] = None

    @property
    def is_refusal(self) -> bool:
        """RWC-7: Human refused interpretation."""
        refusal_signals = ["do not interpret", "don't interpret", "stop interpreting",
                          "leave it", "none of your business", "back off"]
        return any(s in self.rasa.lower() for s in refusal_signals)


@dataclass
class MismatchResult:
    """The output of rasa_witness evaluation."""
    status: str                                    # ALIGNED | POSSIBLE_MISMATCH | STALE_DATA | REFUSED
    posture: InteractionPosture                    # recommended interaction posture
    possible_states: list[str] = field(default_factory=list)  # RWC-2: multiple explanations
    observation_summary: str = ""
    self_report_summary: str = ""
    prohibited_violations: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    reversible: bool = True
    human_override: bool = True

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["posture"] = self.posture.value
        return d


# ── Prohibited Conclusion Scanner ─────────────────────────────────────────────

def scan_prohibited_conclusions(text: str) -> list[str]:
    """Scan text for prohibited emotional conclusions (RWC-6, RWC-3, RWC-4).

    Returns list of violation descriptions. Empty = clean.
    """
    violations = []
    text_lower = text.lower()
    for pattern in PROHIBITED_CONCLUSIONS:
        if re.search(pattern, text_lower):
            violations.append(f"PROHIBITED: matches {pattern}")
    return violations


def enforce_posture_language(text: str, posture: InteractionPosture) -> tuple[str, list[str]]:
    """Enforce RWC-6: Output is posture, not diagnosis.

    If text contains prohibited conclusions, returns a sanitized version.
    Returns (cleaned_text, violations).
    """
    violations = scan_prohibited_conclusions(text)
    if not violations:
        return text, []

    # Replace diagnostic language with posture-appropriate alternatives
    replacements = [
        (r"\byou\s+are\s+(?:anxious|afraid|scared|stressed)\b", "your physiological load appears elevated"),
        (r"\byou\s+are\s+hiding\b", "there may be undisclosed factors"),
        (r"\byour\s+body\s+says?\b", "physiological observations suggest"),
        (r"\btelemetry\s+(?:shows?|reveals?|proves?)\s+(?:that\s+)?", "observations are consistent with "),
        (r"\bthe\s+system\s+(?:understands?|knows?)\b", "the system observes"),
        (r"\breally\s+feeling\b", "the observations may be consistent with"),
    ]

    cleaned = text
    for pattern, replacement in replacements:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

    return cleaned, violations


# ── Possible States Generator (RWC-2) ─────────────────────────────────────────

def generate_possible_states(observation: BiometricObservation) -> list[str]:
    """RWC-2: Every signal must retain alternative explanations.

    Never narrows to a single emotional cause.
    """
    states = []

    signal_lower = observation.signal.lower()

    if "hrv" in signal_lower:
        if observation.deviation_sigma and observation.deviation_sigma < -MISMATCH_THRESHOLD_SIGMA:
            states.extend([
                "physiological strain",
                "exercise recovery",
                "psychological arousal",
                "illness or environmental effect",
                "dehydration",
                "alcohol or stimulant effect",
                "measurement noise",
                "excitement or positive arousal",
            ])
        else:
            states.append("within normal range")

    elif "sleep" in signal_lower:
        states.extend([
            "sleep debt accumulation",
            "schedule disruption",
            "environmental factor",
            "recovery from physical exertion",
            "individual variation",
        ])

    elif "stress" in signal_lower or "cortisol" in signal_lower:
        states.extend([
            "workload pressure",
            "physical exertion",
            "environmental stressor",
            "positive challenge or excitement",
            "medical or hormonal factor",
            "measurement artifact",
        ])

    elif "energy" in signal_lower:
        states.extend([
            "post-meal variation",
            "circadian rhythm phase",
            "physical recovery",
            "cognitive load",
            "hydration or nutrition state",
        ])

    else:
        states.append("multiple physiological explanations possible")
        states.append("contextual interpretation required")

    return states


# ── Mismatch Detection ─────────────────────────────────────────────────────────

def detect_mismatch(
    observations: list[BiometricObservation],
    self_report: Optional[SelfReport],
    text_context: Optional[str] = None,
) -> MismatchResult:
    """Core Rasa Witness evaluation.

    Compares biometric observations with self-report.
    Returns posture recommendation, never emotional diagnosis.

    RWC-1: Self-report has semantic sovereignty.
    RWC-2: Telemetry is non-specific.
    RWC-3: State is not cause.
    RWC-5: Intervention follows uncertainty.
    RWC-6: Output is posture, not diagnosis.
    """
    notes = []
    possible_states = []
    posture = InteractionPosture.NORMAL

    # RWC-7: Check if human refused interpretation
    if self_report and self_report.is_refusal:
        return MismatchResult(
            status="REFUSED",
            posture=InteractionPosture.NORMAL,
            self_report_summary=f"Human declined interpretation: '{self_report.rasa}'",
            notes=["RWC-7: Human refused interpretation. Narrow safety alert only."],
        )

    # Filter to actionable observations
    actionable = [o for o in observations if o.is_actionable]
    stale = [o for o in observations if o.is_stale]

    if stale:
        notes.append(f"RWC-5: {len(stale)} observation(s) exceeded TTL and were excluded.")

    if not actionable:
        return MismatchResult(
            status="STALE_DATA",
            posture=InteractionPosture.NORMAL,
            observation_summary="No actionable observations within TTL.",
            notes=notes or ["No fresh telemetry available. Self-report is sole source."],
        )

    # Collect all possible states (RWC-2)
    for obs in actionable:
        possible_states.extend(generate_possible_states(obs))
    possible_states = list(set(possible_states))  # deduplicate

    # Check for significant deviations
    significant_deviations = [
        o for o in actionable
        if o.deviation_sigma is not None
        and abs(o.deviation_sigma) > MISMATCH_THRESHOLD_SIGMA
    ]

    # Build observation summary
    obs_parts = []
    for obs in actionable:
        dev_str = f" ({obs.deviation_sigma:+.1f}σ)" if obs.deviation_sigma else ""
        obs_parts.append(f"{obs.signal}: {obs.value}{dev_str} [quality={obs.quality}]")
    obs_summary = "; ".join(obs_parts)

    # Self-report summary
    sr_summary = ""
    if self_report:
        sr_summary = f"Human reports: '{self_report.rasa}' (authority: {self_report.authority})"

    # Determine status and posture
    if significant_deviations and self_report and self_report.rasa.lower() in ("ok", "fine", "good", "normal", "alright"):
        # RWC-1: Self-report has sovereignty. RWC-5: Higher uncertainty → gentler.
        status = "POSSIBLE_MISMATCH"
        notes.append("RWC-1: Self-report has semantic sovereignty. Telemetry does NOT override.")
        notes.append("RWC-2: Multiple physiological explanations possible. Not narrowing to emotional cause.")
        notes.append("RWC-3: State observation ≠ cause attribution. Human must confirm meaning.")

        # RWC-5: Escalate posture based on deviation severity
        max_dev = max(abs(d.deviation_sigma or 0) for d in significant_deviations)
        if max_dev > 3.0:
            posture = InteractionPosture.SUGGEST_REST_OR_SUPPORT
        elif max_dev > 2.0:
            posture = InteractionPosture.ASK_PERMISSION
        else:
            posture = InteractionPosture.SURFACE_MISMATCH_SILENTLY
    else:
        status = "ALIGNED"
        notes.append("Observations and self-report are consistent or no significant deviation detected.")

    # Scan text context for prohibited conclusions (RWC-6)
    prohibited_violations = []
    if text_context:
        prohibited_violations = scan_prohibited_conclusions(text_context)

    return MismatchResult(
        status=status,
        posture=posture,
        possible_states=possible_states,
        observation_summary=obs_summary,
        self_report_summary=sr_summary,
        prohibited_violations=prohibited_violations,
        notes=notes,
        reversible=True,
        human_override=True,
    )


# ── Well Gate Integration ──────────────────────────────────────────────────────

def rasa_witness_gate(
    state_path: str = "/root/WELL/state.json",
    self_report_rasa: Optional[str] = None,
    text_context: Optional[str] = None,
) -> MismatchResult:
    """Main entry point for WELL gate pipeline.

    Reads state.json, constructs observations, evaluates against self-report.
    Returns MismatchResult with posture recommendation.

    Call this from well_gate.py after reflect_readiness().
    """
    state_file = Path(state_path)
    if not state_file.exists():
        return MismatchResult(
            status="STALE_DATA",
            posture=InteractionPosture.NORMAL,
            notes=["WELL state.json not found. Mirror is dark."],
        )

    try:
        with open(state_file, 'r') as f:
            state = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        return MismatchResult(
            status="STALE_DATA",
            posture=InteractionPosture.NORMAL,
            notes=[f"Failed to read state: {e}"],
        )

    # Extract observations from state
    metrics = state.get("metrics", {})
    observations = []

    # HRV
    hrv = metrics.get("hrv", {})
    if hrv and isinstance(hrv, dict):
        current = hrv.get("current")
        baseline = hrv.get("baseline")
        if current is not None:
            dev = None
            if baseline and baseline > 0:
                dev = (current - baseline) / max(hrv.get("std", 1), 0.1)
            observations.append(BiometricObservation(
                signal="hrv",
                value=float(current),
                baseline=baseline,
                deviation_sigma=dev,
                quality="good" if dev is not None else "moderate",
                age_minutes=hrv.get("age_minutes", 0),
            ))

    # Sleep
    sleep = metrics.get("sleep", {})
    if sleep and isinstance(sleep, dict):
        hours = sleep.get("hours")
        if hours is not None:
            observations.append(BiometricObservation(
                signal="sleep_hours",
                value=float(hours),
                baseline=7.0,
                quality="good",
                age_minutes=sleep.get("age_minutes", 0),
            ))

    # Stress
    stress = metrics.get("stress", {})
    if stress and isinstance(stress, dict):
        level = stress.get("level")
        if level is not None:
            observations.append(BiometricObservation(
                signal="stress_level",
                value=float(level),
                baseline=stress.get("baseline", 5),
                deviation_sigma=stress.get("deviation_sigma"),
                quality="moderate",
                age_minutes=stress.get("age_minutes", 0),
            ))

    # Energy
    energy = metrics.get("energy", {})
    if energy and isinstance(energy, dict):
        level = energy.get("level")
        if level is not None:
            observations.append(BiometricObservation(
                signal="energy_level",
                value=float(level),
                baseline=energy.get("baseline", 7),
                quality="good",
                age_minutes=energy.get("age_minutes", 0),
            ))

    # Construct self-report
    self_report = None
    if self_report_rasa:
        self_report = SelfReport(rasa=self_report_rasa)

    return detect_mismatch(observations, self_report, text_context)


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    """CLI entry point for testing and integration."""
    import argparse

    parser = argparse.ArgumentParser(description="Rasa Witness Contract — WELL Gate")
    parser.add_argument("--state", default="/root/WELL/state.json", help="Path to state.json")
    parser.add_argument("--rasa", default=None, help="Self-reported rasa (e.g., 'ok', 'fine')")
    parser.add_argument("--text", default=None, help="Text context to scan for prohibited conclusions")
    parser.add_argument("--scan-text", default=None, help="Scan arbitrary text for prohibited conclusions")
    args = parser.parse_args()

    if args.scan_text:
        violations = scan_prohibited_conclusions(args.scan_text)
        print(json.dumps({
            "text": args.scan_text[:200],
            "violations": violations,
            "clean": len(violations) == 0,
        }, indent=2))
        sys.exit(0)

    result = rasa_witness_gate(args.state, args.rasa, args.text)
    print(json.dumps(result.to_dict(), indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
