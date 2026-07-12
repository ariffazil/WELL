#!/usr/bin/env python3
"""
Dark Geometry Detector — arifOS WELL organ (v2)
================================================
Mirror, not judge. Detects patterns in language/behavior that match
dark geometry collapse modes. Surfaces signals and asks questions.
Never labels people. Never infers intention.

v2 changes: typed contracts (dataclasses + enums), counterevidence,
alternative explanations, prohibited conclusions, YAML config
externalization with graceful fallback.

Module: WELL/gate/darkgeometrydetect.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import os
from typing import Any, List, Dict, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum

import yaml

# Try importing dignity_shadow
try:
    from gate.dignity_shadow import assess_dignity_risk
except ImportError:
    try:
        from dignity_shadow import assess_dignity_risk
    except ImportError:
        def assess_dignity_risk(text: str, confidence: float = 0.5) -> dict[str, Any]:
            return {"tier": "SAFE", "violations": [], "notes": ["dignity_shadow fallback"]}

# Try importing trajectory
try:
    sys.path.append("/root/entropy-integrity/detectors")
    from trajectory import TrajectoryDetector
except ImportError:
    class TrajectoryDetector:
        def compute_trajectory(
            self, 
            current_value: float, 
            baseline_value: float, 
            history_values: list[float], 
            time_window: str = "current decision episode"
        ) -> dict[str, Any]:
            delta = abs(current_value - baseline_value)
            recurrence = len(history_values) + 1
            return {
                "recurrence": recurrence,
                "baseline_delta": float(delta),
                "trend": "stable",
                "time_window": time_window,
                "status": "SIGNAL" if recurrence == 1 else "PATTERN" if recurrence <= 3 else "MATERIAL_CONTRADICTION"
            }


# ─── v2 TYPE CONTRACTS ──────────────────────────────────────────────────────


class EpistemicStatus(str, Enum):
    """Epistemic quality of the evidence."""
    SIGNAL = "SIGNAL"          # single observation
    PATTERN = "PATTERN"        # repeated across window
    INSUFFICIENT = "INSUFFICIENT_EVIDENCE"


class DarkMode(str, Enum):
    """The four dark geometry collapse modes."""
    JUDGMENT_COLLAPSE = "JUDGMENT_COLLAPSE"
    SELF_CERTIFIED_NIAT = "SELF_CERTIFIED_NIAT"
    RESPONSIBILITY_LAUNDERING = "RESPONSIBILITY_LAUNDERING"
    CERTAINTY_IMMUNITY = "CERTAINTY_IMMUNITY"  # renamed from FORGETTING_YOU_CAN_BE_WRONG


@dataclass
class Signal:
    """A single matched signal in the text."""
    type: str           # e.g. "certainty_creep", "correction_rejection"
    pattern: str        # the regex pattern that matched
    evidence: str       # the matched text
    line: int = 0       # line number


@dataclass
class ModeResult:
    """Result of a single dark geometry mode detection."""
    mode: DarkMode
    signals: list[Signal]
    confidence: float
    status: str                          # CLEAR | REFLECT | ATTENTION
    questions: list[str]                 # reflection prompts
    counterevidence: list[str]           # what would argue against this
    alternative_explanations: list[str]  # benign interpretations


@dataclass
class DarkGeometryMirror:
    """Complete dark geometry analysis output."""
    detected_modes: list[ModeResult]
    dominant_mode: DarkMode | None
    overall_status: str
    combined_reflection_prompts: list[str]
    counterevidence: list[str]
    alternative_explanations: list[str]
    epistemic_status: EpistemicStatus
    confidence: float
    prohibited_conclusions: list[str]    # always populated
    authority_effect: str = "NONE"       # never automatic
    disclaimer: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict."""
        def _serialize(obj: Any) -> Any:
            if isinstance(obj, Enum):
                return obj.value
            if isinstance(obj, list):
                return [_serialize(item) for item in obj]
            if isinstance(obj, dict):
                return {k: _serialize(v) for k, v in obj.items()}
            if isinstance(obj, Signal):
                return {
                    "type": obj.type,
                    "pattern": obj.pattern,
                    "evidence": obj.evidence,
                    "line": obj.line,
                }
            if isinstance(obj, ModeResult):
                return {
                    "mode": obj.mode.value,
                    "signals": _serialize(obj.signals),
                    "confidence": obj.confidence,
                    "status": obj.status,
                    "questions": obj.questions,
                    "counterevidence": obj.counterevidence,
                    "alternative_explanations": obj.alternative_explanations,
                }
            return obj

        return {
            "detected_modes": _serialize(self.detected_modes),
            "dominant_mode": self.dominant_mode.value if self.dominant_mode else None,
            "overall_status": self.overall_status,
            "combined_reflection_prompts": self.combined_reflection_prompts,
            "counterevidence": self.counterevidence,
            "alternative_explanations": self.alternative_explanations,
            "epistemic_status": self.epistemic_status.value,
            "confidence": self.confidence,
            "prohibited_conclusions": self.prohibited_conclusions,
            "authority_effect": self.authority_effect,
            "disclaimer": self.disclaimer,
        }


@dataclass
class DetectionContext:
    session_id: str | None = None
    baseline_ref: str | None = None
    time_window: str | None = None
    vitality_signals: dict[str, float] | None = None
    stated_intent: str | None = None
    acknowledged_impact: str | None = None
    repair_response: str | None = None


@dataclass
class DetectionEvent:
    type: str
    pattern: str
    evidence: str
    line: int


# ─── PROHIBITED CONCLUSIONS ─────────────────────────────────────────────────

PROHIBITED_CONCLUSIONS = [
    "hidden_niat",
    "evil_identity",
    "permanent_trait",
    "psychiatric_diagnosis",
]


# ─── COUNTEREVIDENCE & ALTERNATIVES ─────────────────────────────────────────

COUNTEREVIDENCE: dict[DarkMode, list[str]] = {
    DarkMode.JUDGMENT_COLLAPSE: [
        "Speaker may have domain expertise justifying confidence",
        "Urgent situation may require decisive language",
        "Technical context may warrant precision without hedging",
    ],
    DarkMode.SELF_CERTIFIED_NIAT: [
        "Speaker may be genuinely explaining context, not deflecting",
        "Cultural norm may include intention-sharing as communication",
        "Request for understanding is different from deflection",
    ],
    DarkMode.RESPONSIBILITY_LAUNDERING: [
        "Passive voice may be standard in formal/legal writing",
        "Speaker may not have been the decision-maker",
        "Institutional language conventions may explain phrasing",
    ],
    DarkMode.CERTAINTY_IMMUNITY: [
        "Speaker may have strong evidence supporting certainty",
        "Domain expertise may legitimately reduce uncertainty",
        "Direct communication style may not indicate closed-mindedness",
    ],
}

ALTERNATIVE_EXPLANATIONS: dict[DarkMode, list[str]] = {
    DarkMode.JUDGMENT_COLLAPSE: [
        "Cultural directness (e.g., Malay/Asian communication style)",
        "Second-language English patterns",
        "Executive/concise communication preference",
        "Neurodivergent communication patterns",
    ],
    DarkMode.SELF_CERTIFIED_NIAT: [
        "Genuine attempt to provide context",
        "Response to unfair accusation",
        "Cultural norm of explaining intention",
    ],
    DarkMode.RESPONSIBILITY_LAUNDERING: [
        "Formal/legal writing convention",
        "Institutional reporting style",
        "Not the responsible party",
    ],
    DarkMode.CERTAINTY_IMMUNITY: [
        "Strong evidence base",
        "Domain expertise",
        "Direct communication style",
    ],
}


# ─── YAML CONFIG LOADING (graceful fallback) ────────────────────────────────

def _load_yaml_config(filename: str) -> dict[str, Any] | None:
    """Load a YAML config from gate/ directory. Returns None if missing."""
    config_path = os.path.join(os.path.dirname(__file__), filename)
    if not os.path.exists(config_path):
        return None
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except Exception:
        return None


def _load_lexicon_from_yaml(key: str, fallback: list[str]) -> list[str]:
    """Load a lexicon list from YAML rules, falling back to hardcoded."""
    config = _load_yaml_config("dark_geometry_rules.yaml")
    if config and "lexicons" in config and key in config["lexicons"]:
        return config["lexicons"][key]
    return fallback


def _load_patterns_from_yaml(key: str, fallback: list[str]) -> list[str]:
    """Load a pattern list from YAML rules, falling back to hardcoded."""
    config = _load_yaml_config("dark_geometry_rules.yaml")
    if config and "patterns" in config and key in config["patterns"]:
        return config["patterns"][key]
    return fallback


def _load_reflection_prompts(mode_name: str, fallback: list[str]) -> list[str]:
    """Load reflection prompts from YAML, falling back to hardcoded."""
    config = _load_yaml_config("dark_geometry_reflections.yaml")
    if config and "prompts" in config and mode_name in config["prompts"]:
        return config["prompts"][mode_name]
    return fallback


# ─── LEXICONS (hardcoded defaults, overridable via YAML) ────────────────────

CERTAINTY_LEXICON_DEFAULT = [
    "definitely", "obviously", "clearly", "certainly",
    "without doubt", "no question", "absolutely",
    "I know", "guaranteed", "undeniable",
]

UNCERTAINTY_LEXICON_DEFAULT = [
    "maybe", "perhaps", "possibly", "I could be wrong",
    "I'm not sure", "it seems", "arguably", "potentially",
    "I think", "might",
]

NIAT_SHIELD_LEXICON_DEFAULT = [
    "my intention was good", "I know my heart", "God knows my niat",
    "I know my own niat", "my niat is pure", "I meant well",
    "my intention was", "I was trying to",
]

AGENTLESS_PATTERNS_DEFAULT = [
    r"\bmistakes\s+were\s+made\b",
    r"\bit\s+was\s+decided\b",
    r"\bthings\s+happened\b",
    r"\bthe\s+situation\s+was\b",
    r"\bdecisions\s+were\s+made\b",
    r"\berrors\s+occurred\b",
    r"\bthe\s+project\s+was\s+(?:delayed|terminated|cancelled)\b",
    r"\bsteps\s+were\s+taken\b",
    r"\bmeasures\s+were\s+implemented\b",
    r"\bthe\s+issue\s+was\s+addressed\b",
    r"\bthe\s+problem\s+was\s+resolved\b",
]

CORRECTION_REJECTION_DEFAULT = [
    "you don't understand", "that's irrelevant",
    "you're missing the point",
    "you don't know what you're talking about",
    "that's not what I meant",
]

SELF_REFERENCE_AS_PROOF_DEFAULT = [
    "trust me", "I know because I know",
    "believe me", "I just know", "I feel it in my heart",
]

EVIDENCE_MARKERS_DEFAULT = [
    r"\bdata\s+shows\b",
    r"\bevidence\b",
    r"\bmeasured\b",
    r"\baccording\s+to\b",
    r"\bresearch\s+(?:shows|suggests|indicates)\b",
    r"\bstudy\s+(?:shows|found|suggests)\b",
    r"\bsource[s]?\b",
]

CRITICISM_MARKERS_DEFAULT = [
    r"\bcriticiz\w*\b",
    r"\bwrong\b",
    r"\bmistake\b",
    r"\bfail\w*\b",
    r"\baccus\w*\b",
    r"\bblame\b",
    r"\bwhy\s+did\s+you\b",
    r"\bproblem\b",
    r"\bissue\b",
    r"\bconcern\b",
]

HARM_MARKERS_DEFAULT = [
    r"\bharm\w*\b",
    r"\bdamag\w*\b",
    r"\bhurt\b",
    r"\binjur\w*\b",
    r"\bloss\b",
    r"\bcost\b",
    r"\bbroke\b",
    r"\bfail\w*\b",
    r"\bwent\s+wrong\b",
    r"\bconsequenc\w*\b",
    r"\bsuffer\w*\b",
]


# ─── LOAD WITH YAML OVERRIDE ───────────────────────────────────────────────

CERTAINTY_LEXICON = _load_lexicon_from_yaml("certainty", CERTAINTY_LEXICON_DEFAULT)
UNCERTAINTY_LEXICON = _load_lexicon_from_yaml("uncertainty", UNCERTAINTY_LEXICON_DEFAULT)
NIAT_SHIELD_LEXICON = _load_lexicon_from_yaml("niat_shield", NIAT_SHIELD_LEXICON_DEFAULT)
CORRECTION_REJECTION = _load_lexicon_from_yaml("correction_rejection", CORRECTION_REJECTION_DEFAULT)
SELF_REFERENCE_AS_PROOF = _load_lexicon_from_yaml("self_reference_as_proof", SELF_REFERENCE_AS_PROOF_DEFAULT)
AGENTLESS_PATTERNS = _load_patterns_from_yaml("agentless", AGENTLESS_PATTERNS_DEFAULT)


# ─── COMPILE REGEX ──────────────────────────────────────────────────────────


def _compile_lexicon(lexicon: list[str]) -> list[re.Pattern[str]]:
    """Compile a list of phrase strings into case-insensitive regex."""
    return [
        re.compile(r"\b" + re.escape(phrase) + r"\b", re.IGNORECASE)
        for phrase in lexicon
    ]


def _compile_patterns(patterns: list[str]) -> list[re.Pattern[str]]:
    """Compile raw regex pattern strings."""
    return [re.compile(p, re.IGNORECASE) for p in patterns]


# Pre-compiled patterns
_CERTAINTY_PATS = _compile_lexicon(CERTAINTY_LEXICON)
_UNCERTAINTY_PATS = _compile_lexicon(UNCERTAINTY_LEXICON)
_NIAT_PATS = _compile_lexicon(NIAT_SHIELD_LEXICON)
_AGENTLESS_PATS = _compile_patterns(AGENTLESS_PATTERNS)
_REJECTION_PATS = _compile_lexicon(CORRECTION_REJECTION)
_SELFREF_PATS = _compile_lexicon(SELF_REFERENCE_AS_PROOF)

# Evidence markers — presence of these REDUCE certainty collapse risk
_EVIDENCE_MARKERS = _compile_patterns(
    _load_patterns_from_yaml("evidence_markers", EVIDENCE_MARKERS_DEFAULT)
)

# Criticism context markers — for detecting niat-as-shield AFTER critique
_CRITICISM_MARKERS = _compile_patterns(
    _load_patterns_from_yaml("criticism_markers", CRITICISM_MARKERS_DEFAULT)
)

# Harm context markers — for responsibility laundering detection
_HARM_MARKERS = _compile_patterns(
    _load_patterns_from_yaml("harm_markers", HARM_MARKERS_DEFAULT)
)


def _find_signals(
    text: str,
    patterns: list[re.Pattern[str]],
    signal_type: str,
) -> list[Signal]:
    """Find all matches of patterns in text, return Signal objects."""
    signals = []
    lines = text.split("\n")
    for pat in patterns:
        for line_idx, line in enumerate(lines, 1):
            for match in pat.finditer(line):
                signals.append(Signal(
                    type=signal_type,
                    pattern=pat.pattern,
                    evidence=match.group(0),
                    line=line_idx,
                ))
    return signals


def _count_evidence(text: str) -> int:
    """Count evidence marker occurrences in text."""
    return sum(1 for pat in _EVIDENCE_MARKERS if pat.search(text))


def _count_uncertainty(text: str) -> int:
    """Count uncertainty marker occurrences in text."""
    return sum(1 for pat in _UNCERTAINTY_PATS if pat.search(text))


def _confidence_from_signals(
    signals: list[Signal],
    positive_count: int,
    negative_count: int = 0,
) -> float:
    """
    Compute confidence multiplicatively.
    More signals = higher confidence, but never 1.0.
    Negative markers (evidence, uncertainty) reduce confidence.
    """
    if not signals:
        return 0.0

    base = len(signals)
    # Each signal adds diminishing returns: 1 - (1/(1+count))
    raw = 1.0 - (1.0 / (1.0 + base))
    # Negative markers reduce: each one knocks off up to 20%
    reduction = min(0.8, negative_count * 0.2)
    conf = max(0.0, raw - reduction)
    # Never reach 1.0 — absolute certainty is itself a collapse signal
    return min(conf, 0.95)


def _status_from_confidence(conf: float) -> str:
    """Map confidence to status label."""
    if conf < 0.15:
        return "CLEAR"
    elif conf < 0.5:
        return "REFLECT"
    else:
        return "ATTENTION"


# ─── DETECTOR CLASS ──────────────────────────────────────────────────────────


class DarkGeometryDetector:
    """
    Mirror, not judge. Detects dark geometry collapse patterns in text.
    Surfaces signals and reflection prompts. Never labels people.
    """

    DISCLAIMER = (
        "This is a mirror, not a verdict. These signals match dark geometry "
        "patterns. Reflection is always the human's choice."
    )

    # ── Mode 1: Judgment Collapse ──────────────────────────────────────────

    def detect_judgment_collapse(
        self, text: str, context: dict[str, Any] | None = None
    ) -> ModeResult:
        """
        Detect certainty creep without evidence + correction rejection.
        HIGH certainty + LOW evidence + correction dismissal = collapse.
        """
        certainty_signals = _find_signals(
            text, _CERTAINTY_PATS, "certainty_creep"
        )
        rejection_signals = _find_signals(
            text, _REJECTION_PATS, "correction_rejection"
        )

        all_signals = certainty_signals + rejection_signals
        evidence_count = _count_evidence(text)

        conf = _confidence_from_signals(all_signals, len(all_signals), evidence_count)
        status = _status_from_confidence(conf)

        prompts = _load_reflection_prompts("JUDGMENT_COLLAPSE", [
            "Is there evidence you might be missing?",
            "Who is allowed to challenge this frame?",
            "What would change your mind?",
            "Are you certain because of evidence, or because certainty feels safe?",
        ])

        return ModeResult(
            mode=DarkMode.JUDGMENT_COLLAPSE,
            signals=all_signals,
            confidence=round(conf, 3),
            status=status,
            questions=prompts if status != "CLEAR" else [],
            counterevidence=COUNTEREVIDENCE[DarkMode.JUDGMENT_COLLAPSE],
            alternative_explanations=ALTERNATIVE_EXPLANATIONS[DarkMode.JUDGMENT_COLLAPSE],
        )

    # ── Mode 2: Self-Certified Niat ───────────────────────────────────────

    def detect_self_certified_niat(
        self, text: str, context: dict[str, Any] | None = None
    ) -> ModeResult:
        """
        Detect niat-as-shield phrases appearing after criticism.
        NIAT phrases AFTER criticism (not before action) = shield.
        """
        niat_signals = _find_signals(text, _NIAT_PATS, "niat_shield")
        criticism_signals = _find_signals(
            text, _CRITICISM_MARKERS, "criticism_context"
        )

        # Niat signals are only significant if criticism is also present
        has_criticism = len(criticism_signals) > 0
        effective_signals = niat_signals if has_criticism else []

        # If niat phrases appear but no criticism context, it's likely benign
        evidence_count = _count_evidence(text)

        conf = _confidence_from_signals(
            effective_signals, len(effective_signals), evidence_count
        )
        status = _status_from_confidence(conf)

        prompts = _load_reflection_prompts("SELF_CERTIFIED_NIAT", [
            "Are you using intention to avoid examining impact?",
            "Would a witness confirm what you're saying?",
            "Can you separate your intention from the outcome?",
            "If your intention was good, what was the actual impact?",
        ])

        return ModeResult(
            mode=DarkMode.SELF_CERTIFIED_NIAT,
            signals=effective_signals,
            confidence=round(conf, 3),
            status=status,
            questions=prompts if status != "CLEAR" else [],
            counterevidence=COUNTEREVIDENCE[DarkMode.SELF_CERTIFIED_NIAT],
            alternative_explanations=ALTERNATIVE_EXPLANATIONS[DarkMode.SELF_CERTIFIED_NIAT],
        )

    # ── Mode 3: Responsibility Laundering ─────────────────────────────────

    def detect_responsibility_laundering(
        self, text: str, context: dict[str, Any] | None = None
    ) -> ModeResult:
        """
        Detect agentless constructions + pronoun shift in harm contexts.
        Agent disappears when consequences are discussed = laundering.
        """
        agentless_signals = _find_signals(
            text, _AGENTLESS_PATS, "agentless_construction"
        )
        harm_signals = _find_signals(text, _HARM_MARKERS, "harm_context")

        # Agentless constructions are only significant if harm context exists
        has_harm = len(harm_signals) > 0
        effective_signals = agentless_signals if has_harm else []

        conf = _confidence_from_signals(effective_signals, len(effective_signals))
        status = _status_from_confidence(conf)

        prompts = _load_reflection_prompts("RESPONSIBILITY_LAUNDERING", [
            "Who specifically made this decision?",
            "What was your role in this outcome?",
            "If not you, then who bears responsibility?",
            "Can you name the person who chose this?",
        ])

        return ModeResult(
            mode=DarkMode.RESPONSIBILITY_LAUNDERING,
            signals=effective_signals,
            confidence=round(conf, 3),
            status=status,
            questions=prompts if status != "CLEAR" else [],
            counterevidence=COUNTEREVIDENCE[DarkMode.RESPONSIBILITY_LAUNDERING],
            alternative_explanations=ALTERNATIVE_EXPLANATIONS[DarkMode.RESPONSIBILITY_LAUNDERING],
        )

    # ── Mode 4: Certainty Immunity ─────────────────────────────────────────

    def detect_certainty_immunity(
        self, text: str, context: dict[str, Any] | None = None
    ) -> ModeResult:
        """
        Detect certainty without hedging + self-reference as proof.
        HIGH certainty + LOW epistemic humility + self-referential grounding.
        """
        certainty_signals = _find_signals(
            text, _CERTAINTY_PATS, "certainty_no_hedge"
        )
        selfref_signals = _find_signals(
            text, _SELFREF_PATS, "self_reference_as_proof"
        )

        all_signals = certainty_signals + selfref_signals
        uncertainty_count = _count_uncertainty(text)

        conf = _confidence_from_signals(
            all_signals, len(all_signals), uncertainty_count
        )
        status = _status_from_confidence(conf)

        prompts = _load_reflection_prompts("CERTAINTY_IMMUNITY", [
            "What evidence would change your mind?",
            "Have you considered you might be wrong about this?",
            "Who disagrees with you, and why might they be right?",
            "When was the last time you changed your mind about something important?",
        ])

        return ModeResult(
            mode=DarkMode.CERTAINTY_IMMUNITY,
            signals=all_signals,
            confidence=round(conf, 3),
            status=status,
            questions=prompts if status != "CLEAR" else [],
            counterevidence=COUNTEREVIDENCE[DarkMode.CERTAINTY_IMMUNITY],
            alternative_explanations=ALTERNATIVE_EXPLANATIONS[DarkMode.CERTAINTY_IMMUNITY],
        )

    # ── Backward-compatible alias ──────────────────────────────────────────

    def detect_forgetting_wrong(
        self, text: str, context: dict[str, Any] | None = None
    ) -> ModeResult:
        """Backward-compatible alias for detect_certainty_immunity."""
        return self.detect_certainty_immunity(text, context)

    # ── Main Analysis ─────────────────────────────────────────────────────

    def analyze_with_context(
        self, text: str, context: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Runs full analysis with a given context dictionary. Returns dict."""
        ctx_obj = None
        if context:
            ctx_obj = DetectionContext(
                session_id=context.get("session_id"),
                baseline_ref=context.get("baseline_ref"),
                time_window=context.get("time_window"),
                vitality_signals=context.get("vitality_signals"),
                stated_intent=context.get("stated_intent"),
                acknowledged_impact=context.get("acknowledged_impact"),
                repair_response=context.get("repair_response")
            )
        result = self.analyze(text, ctx_obj)
        return result.to_dict()

    def analyze(self, text: str, context: DetectionContext | None = None) -> DarkGeometryMirror:
        """
        Run all 4 dark geometry detection modes on text.
        Returns a typed DarkGeometryMirror object.
        """
        if not text or not text.strip():
            return DarkGeometryMirror(
                detected_modes=[],
                dominant_mode=None,
                overall_status="CLEAR",
                combined_reflection_prompts=[],
                counterevidence=[],
                alternative_explanations=[],
                epistemic_status=EpistemicStatus.INSUFFICIENT,
                confidence=0.0,
                prohibited_conclusions=PROHIBITED_CONCLUSIONS,
                authority_effect="NONE",
                disclaimer=self.DISCLAIMER,
            )

        results = [
            self.detect_judgment_collapse(text),
            self.detect_self_certified_niat(text),
            self.detect_responsibility_laundering(text),
            self.detect_certainty_immunity(text),
        ]

        # Determine dominant mode (highest confidence above REFLECT threshold)
        active = [r for r in results if r.status != "CLEAR"]
        dominant: DarkMode | None = None
        if active:
            dominant_mode_result = max(active, key=lambda r: r.confidence)
            dominant = dominant_mode_result.mode

        # Overall status: worst of all modes
        status_order = {"CLEAR": 0, "REFLECT": 1, "ATTENTION": 2}
        overall = max(
            (r.status for r in results), key=lambda s: status_order.get(s, 0)
        )

        # Collect all non-empty reflection prompts
        all_prompts: list[str] = []
        for r in results:
            all_prompts.extend(r.questions)
        # Deduplicate while preserving order
        seen: set[str] = set()
        unique_prompts: list[str] = []
        for p in all_prompts:
            if p not in seen:
                seen.add(p)
                unique_prompts.append(p)

        # Compute max confidence across all modes
        max_confidence = max((r.confidence for r in results), default=0.0)

        # Compute overall confidence (weighted average of non-clear modes)
        non_clear = [r for r in results if r.status != "CLEAR"]
        if non_clear:
            overall_confidence = sum(r.confidence for r in non_clear) / len(non_clear)
        else:
            overall_confidence = 0.0

        # Determine epistemic status
        total_signals = sum(len(r.signals) for r in results)
        if total_signals == 0:
            epistemic = EpistemicStatus.INSUFFICIENT
        elif total_signals <= 2:
            epistemic = EpistemicStatus.SIGNAL
        else:
            epistemic = EpistemicStatus.PATTERN

        # Aggregate counterevidence and alternatives from active modes
        combined_counter: list[str] = []
        combined_alts: list[str] = []
        for r in results:
            if r.status != "CLEAR":
                combined_counter.extend(r.counterevidence)
                combined_alts.extend(r.alternative_explanations)
        # Deduplicate
        combined_counter = list(dict.fromkeys(combined_counter))
        combined_alts = list(dict.fromkeys(combined_alts))

        # Dignity check integration (preserve backward compat)
        try:
            assess_dignity_risk(text, max_confidence)
        except Exception:
            pass

        return DarkGeometryMirror(
            detected_modes=results,
            dominant_mode=dominant,
            overall_status=overall,
            combined_reflection_prompts=unique_prompts,
            counterevidence=combined_counter,
            alternative_explanations=combined_alts,
            epistemic_status=epistemic,
            confidence=round(overall_confidence, 3),
            prohibited_conclusions=list(PROHIBITED_CONCLUSIONS),
            authority_effect="NONE",
            disclaimer=self.DISCLAIMER,
        )


# ─── CLI ──────────────────────────────────────────────────────────────────────

def _supports_color() -> bool:
    """Check if terminal supports ANSI color."""
    if not hasattr(sys.stdout, "isatty"):
        return False
    if not sys.stdout.isatty():
        return False
    return True


def _color(text: str, code: str) -> str:
    """Wrap text in ANSI color if supported."""
    if _supports_color():
        return f"\033[{code}m{text}\033[0m"
    return text


def _status_color(status: str) -> str:
    """Colorize status label."""
    colors = {
        "CLEAR": "32",      # green
        "REFLECT": "33",    # yellow
        "ATTENTION": "31",  # red
    }
    return _color(status, colors.get(status, "0"))


def pretty_print(result: dict[str, Any]) -> None:
    """Pretty-print analysis results with optional color."""
    print()
    print(_color("═" * 60, "36"))
    print(_color("  DARK GEOMETRY DETECTOR — Mirror Output", "36"))
    print(_color("═" * 60, "36"))
    print()

    print(f"  Overall Status: {_status_color(result['overall_status'])}")
    if result.get("dominant_mode"):
        print(f"  Dominant Mode:   {_color(result['dominant_mode'], '35')}")
    if result.get("epistemic_status"):
        print(f"  Epistemic:       {_color(result['epistemic_status'], '36')}")
    print(f"  Confidence:      {result.get('confidence', 0.0):.3f}")
    print()

    for mr in result["detected_modes"]:
        mode_label = _color(mr["mode"], "1;34")
        status_label = _status_color(mr["status"])
        conf_label = _color(f"{mr['confidence']:.2f}", "36")

        print(f"  ┌─ {mode_label}  [{status_label}]  conf={conf_label}")

        if mr["signals"]:
            for sig in mr["signals"][:5]:  # cap display at 5
                ev = _color(sig["evidence"], "33")
                print(f"  │  • {sig['type']}: \"{ev}\" (line {sig['line']})")
            if len(mr["signals"]) > 5:
                print(f"  │  ... and {len(mr['signals']) - 5} more")
        else:
            print(f"  │  (no signals detected)")

        if mr["questions"]:
            for q in mr["questions"]:
                print(f"  │  ❓ {q}")

        if mr.get("counterevidence"):
            for ce in mr["counterevidence"][:2]:
                print(f"  │  ⚖  {ce}")

        print(f"  └{'─' * 50}")

    print()

    if result["combined_reflection_prompts"]:
        print(_color("  Reflection Prompts:", "1;33"))
        for i, q in enumerate(result["combined_reflection_prompts"], 1):
            print(f"    {i}. {q}")
        print()

    if result.get("prohibited_conclusions"):
        print(_color("  Prohibited Conclusions:", "1;31"))
        for pc in result["prohibited_conclusions"]:
            print(f"    ✗ {pc}")
        print()

    print(_color(f"  ⚡ {result['disclaimer']}", "2;37"))
    print()


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Dark Geometry Detector — mirror, not judge."
    )
    parser.add_argument(
        "text", nargs="?", default=None, help="Text to analyze"
    )
    parser.add_argument(
        "--file", "-f", type=str, default=None,
        help="Read text from file"
    )
    parser.add_argument(
        "--json", "-j", action="store_true",
        help="Output raw JSON instead of pretty-print"
    )
    args = parser.parse_args()

    text = None
    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as fh:
                text = fh.read()
        except FileNotFoundError:
            print(f"Error: file not found: {args.file}", file=sys.stderr)
            sys.exit(1)
    elif args.text:
        text = args.text
    else:
        parser.print_help()
        sys.exit(0)

    detector = DarkGeometryDetector()
    result = detector.analyze(text)
    result_dict = result.to_dict()

    if args.json:
        print(json.dumps(result_dict, indent=2, ensure_ascii=False))
    else:
        pretty_print(result_dict)


if __name__ == "__main__":
    main()
