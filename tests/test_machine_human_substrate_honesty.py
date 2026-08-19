"""Honesty fields must not contradict the banner."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sensors.machine_human_substrate import collect_substrate_signals


def test_undeployed_pipeline_is_not_verified_or_fresh():
    signals = collect_substrate_signals()
    honesty = signals["honesty"]
    banner = str(honesty.get("banner", ""))
    assert "not deployed" in banner.lower() or "UNKNOWN" in banner
    assert honesty["is_sensor_verified"] is False
    assert honesty["is_stale"] is True
    assert honesty["source_type"] == "MACHINE_PATTERN_INFERENCE"
