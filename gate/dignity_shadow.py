# WELL Dignity Shadow Gate
# Role: Pre-JUDGE boundary check for human-pattern inference.
# Axiom: W0 — WELL holds no veto. It flags risk. arifOS adjudicates.
# Floor: F05 (PEACE) + F06 (EMPATHY)

import json
import sys
import re
from pathlib import Path
from typing import Any

# Risk tiers
SAFE = "SAFE"
GUARDED = "GUARDED"
HOLD = "HOLD"

# Fatal dignity violations — diagnostic language that reduces human to label
FATAL_PATTERNS = [
    r"\bis\s+(?:a\s+)?(?:narcissist|toxic|insecure|broken|traumatized|clumsy|stupid|lazy)",
    r"\bhas\s+trauma\b",
    r"\bis\s+projecting\b",
    r"\bis\s+avoidant\b",
    r"\bis\s+anxious\b",
]

# Guarded patterns — over-certainty in interpretation
GUARDED_PATTERNS = [
    r"\bbecause\s+(?:they|she|he)\s+(?:is|has|was)",
    r"\bdue\s+to\s+(?:their|her|his)\b",
    r"\bobviously\b",
    r"\bclearly\b",
    r"\bdefinitely\b",
]


def assess_dignity_risk(text: str, confidence: float = 0.5) -> dict[str, Any]:
    """Assess dignity risk of a shadow hypothesis or scar-vector description.

    Returns dict with:
        - tier: SAFE | GUARDED | HOLD
        - violations: list of matched patterns
        - notes: list of constitutional notes
        - safe_rephrase_hint: str or None
    """
    text_lower = text.lower()
    violations = []
    notes = []

    for pat in FATAL_PATTERNS:
        if re.search(pat, text_lower):
            violations.append(f"FATAL:{pat}")

    if violations:
        notes.append("F05 PEACE: Diagnostic language detected. Human reduced to label.")
        notes.append("F06 EMPATHY: Shadow maps may not be used as accusation.")
        return {
            "tier": HOLD,
            "violations": violations,
            "notes": notes,
            "safe_rephrase_hint": (
                "Rephrase as pattern observation: 'Behaviour consistent with X under Y conditions.'"
            ),
        }

    for pat in GUARDED_PATTERNS:
        if re.search(pat, text_lower):
            violations.append(f"GUARDED:{pat}")

    if violations:
        notes.append("F07 HUMILITY: Over-certainty in causal claim.")
        notes.append("F02 TRUTH: Confidence must match evidence band.")

    if confidence > 0.7:
        violations.append("GUARDED:confidence>0.7")
        notes.append("F05: High-confidence scar-vector risks dehumanising inference.")

    if violations:
        return {
            "tier": GUARDED,
            "violations": violations,
            "notes": notes,
            "safe_rephrase_hint": (
                "Downgrade confidence or add uncertainty band: 'Low-confidence hypothesis...'"
            ),
        }

    notes.append("F05: Language preserves dignity.")
    notes.append("F07: Confidence band appropriate for evidence strength.")
    return {
        "tier": SAFE,
        "violations": [],
        "notes": notes,
        "safe_rephrase_hint": None,
    }


def main() -> None:
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python dignity_shadow.py '<text>' [confidence]"}))
        sys.exit(0)

    text = sys.argv[1]
    confidence = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5
    result = assess_dignity_risk(text, confidence)
    print(json.dumps(result, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
