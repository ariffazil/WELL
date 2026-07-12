"""
WELL Adapter for Dark Geometry Detector
========================================
Converts WELL-specific signals (vitality, stress, trust, interaction)
into DetectionEvent format for the canonical detector.

Module: WELL/gate/adapters/well_adapter.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class WELLInteractionEvent:
    """A single interaction event from WELL's observation layer."""
    timestamp: str
    speaker: str            # "human" | "agent"
    text: str
    metadata: dict[str, Any] | None = None


def events_to_text(events: list[WELLInteractionEvent]) -> str:
    """Convert WELL interaction events to analyzable text."""
    return "\n".join(
        f"[{e.speaker}] {e.text}" for e in events
    )


def build_detection_context(
    events: list[WELLInteractionEvent],
    operator_id: str = "unknown",
    vitality_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build detection context from WELL state."""
    return {
        "organ": "WELL",
        "operator_id": operator_id,
        "event_count": len(events),
        "time_window": {
            "first": events[0].timestamp if events else None,
            "last": events[-1].timestamp if events else None,
        },
        "vitality": vitality_state or {},
        "baseline_available": vitality_state is not None,
    }


def extract_vitality_signals(vitality: dict[str, Any]) -> list[str]:
    """Extract observable signals from vitality state."""
    signals = []
    if vitality.get("stress_band") in ("high", "critical"):
        signals.append("elevated_stress")
    if vitality.get("sleep_debt_days", 0) > 2:
        signals.append("sleep_debt_accumulation")
    if vitality.get("cognitive_load") == "overloaded":
        signals.append("cognitive_overload")
    if vitality.get("withdrawal_detected"):
        signals.append("withdrawal_pattern")
    return signals
