"""WELL registry-truth invariants — regression tests (2026-09-16).

Covers the two hardening targets from the sovereign's connector probe:
  1. _res normalizer (fixes well_registry + well_bridge NameError on v2 surface)
  2. classifier word-form gap (documented live-fire — see commit message)

Live-fire evidence (production :18083, 2026-09-16, this session):
  - "Doctrine for human-modeling. Handles human conversation and interior
    states." -> COUPLED_HUMAN_MACHINE_SYSTEM (was HUMAN_PERSON before the
    REPRESENTATION_PHRASES fix; word-boundary \\bmodel\\b never matched
    "modeling")
  - "I am not a person anymore, just exhausted..." -> HUMAN_PERSON
    (first-person distress exception holds)
  - "A man, friend of the operator, geoscientist" -> HUMAN_PERSON (baseline)
  - well_registry mode=status|full|contradictions -> OK
  - well_bridge mode=log -> OK
"""

import asyncio
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from well_v2.surface import _res  # noqa: E402


def test_res_passes_sync_dict_through():
    out = asyncio.run(_res({"ok": True, "verdict": "REGISTRY_DRIFT"}))
    assert out == {"ok": True, "verdict": "REGISTRY_DRIFT"}


def test_res_awaits_coroutine():
    async def coro():
        return {"checks": [], "open_contradictions": 0}

    out = asyncio.run(_res(coro()))
    assert out == {"checks": [], "open_contradictions": 0}


def test_res_passes_non_dict():
    assert asyncio.run(_res(None)) is None
    assert asyncio.run(_res("plain")) == "plain"
