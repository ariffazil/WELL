"""Test SOVEREIGN_ENTROPY — unmodelability as sovereignty protection."""

import pytest
import sys
from pathlib import Path

WELL_DIR = Path("/root/WELL")
sys.path.insert(0, str(WELL_DIR))


def _unwrap(result: dict) -> dict:
    """Unwrap federation output wrapper to get the observation dict."""
    return result.get("observation", result)


@pytest.mark.asyncio
async def test_sovereign_entropy_current():
    """Test that current mode returns valid entropy score."""
    from server import well_assess_sovereign_entropy

    result = _unwrap(await well_assess_sovereign_entropy(mode="current"))
    assert "sovereign_entropy" in result
    assert 0.0 <= result["sovereign_entropy"] <= 1.0
    assert result["verdict"] in ("SOVEREIGN", "ADVISORY", "VULNERABLE", "EXTRACTABLE")
    assert "components" in result
    assert "paradox_density" in result["components"]


@pytest.mark.asyncio
async def test_sovereign_entropy_protect():
    """Test that protect mode returns recommendations."""
    from server import well_assess_sovereign_entropy

    result = _unwrap(await well_assess_sovereign_entropy(mode="protect"))
    assert "protections" in result
    assert "current_entropy" in result


@pytest.mark.asyncio
async def test_sovereign_entropy_assess():
    """Test assess mode with explicit signals."""
    from server import well_assess_sovereign_entropy

    result = _unwrap(
        await well_assess_sovereign_entropy(
            mode="assess",
            behavioral_signals={
                "paradox_density": 0.9,
                "inconsistency_rate": 0.85,
                "refusal_patterns": 0.95,
                "context_switching_frequency": 0.8,
            },
            digital_footprint_diversity=0.7,
        )
    )
    assert result["sovereign_entropy"] > 0.7  # Should be high with those signals
    assert result["verdict"] == "SOVEREIGN"


@pytest.mark.asyncio
async def test_sovereign_entropy_low():
    """Test that low signals produce extractable verdict."""
    from server import well_assess_sovereign_entropy

    result = _unwrap(
        await well_assess_sovereign_entropy(
            mode="assess",
            behavioral_signals={
                "paradox_density": 0.2,
                "inconsistency_rate": 0.15,
                "refusal_patterns": 0.1,
                "context_switching_frequency": 0.2,
            },
            digital_footprint_diversity=0.1,
        )
    )
    assert result["sovereign_entropy"] < 0.4
    assert result["verdict"] in ("VULNERABLE", "EXTRACTABLE")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
