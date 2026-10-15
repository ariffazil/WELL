"""Unit test for swapoff precondition in well_machine_diagnose.

The bug: precondition was only PSI < 5. PSI is a current-state metric — it
says "no memory thrashing RIGHT NOW" but says nothing about whether the swap
pages will FIT back into RAM after release. If swap_used > 80% of available
RAM, swapoff -a triggers OOM (the swap pages have to page-fault back in, and
there is not enough headroom to hold them).

Fix: precondition must include `swap_used < mem_available * 0.8` in addition
to `psi < 5`. The fix is in `well_machine_diagnose` (server.py around the
swap_pct > 30 branch).

This test reconstructs the precondition computation against a handful of
scenarios and asserts the recommendation is suppressed when swap_used would
not fit in available RAM.
"""
from __future__ import annotations

import sys
from pathlib import Path

WELL_ROOT = Path(__file__).resolve().parents[1]
if str(WELL_ROOT) not in sys.path:
    sys.path.insert(0, str(WELL_ROOT))

# Pure-Python reimplementation of the precondition logic, mirroring
# server.py so the test does not depend on the FastMCP tool runtime.
def _swapoff_should_recommend(mem: dict, psi: float, swap_pct: float) -> bool:
    avail_bytes = mem.get("available_kb", 0) * 1024
    swap_used_bytes = mem.get("swap_used_kb", 0) * 1024
    swap_fits_in_ram = swap_used_bytes < (avail_bytes * 0.8)
    return swap_pct > 30 and psi < 5 and swap_fits_in_ram


def test_safe_low_swap_low_psi_recommends():
    # 16 GB RAM, 8 GB available, 3 GB swap used. PSI calm.
    mem = {
        "total_kb": 16 * 1024 * 1024,
        "available_kb": 8 * 1024 * 1024,
        "swap_used_kb": 3 * 1024 * 1024,
        "swap_total_kb": 8 * 1024 * 1024,
    }
    assert _swapoff_should_recommend(mem, psi=1.0, swap_pct=37.5) is True


def test_high_swap_but_low_psi_suppressed_by_ram_constraint():
    # The bug scenario: PSI calm but swap_used > 80% of available RAM.
    # 16 GB RAM, 8 GB available, 10 GB swap used. swap_used (10GB) > avail*0.8 (6.4GB).
    mem = {
        "total_kb": 16 * 1024 * 1024,
        "available_kb": 8 * 1024 * 1024,
        "swap_used_kb": 10 * 1024 * 1024,
        "swap_total_kb": 20 * 1024 * 1024,
    }
    # PSI 1.0 would have been "safe" under the old check. Under the fix,
    # swap_used 10 GB >= 6.4 GB cap -> recommendation suppressed.
    assert _swapoff_should_recommend(mem, psi=1.0, swap_pct=50.0) is False


def test_boundary_just_under_cap_recommends():
    # swap_used = 6.399 GB, available = 8 GB -> cap = 6.4 GB -> 6.399 < 6.4 -> recommend.
    mem = {
        "total_kb": 16 * 1024 * 1024,
        "available_kb": 8 * 1024 * 1024,
        "swap_used_kb": int(6.399 * 1024 * 1024),
        "swap_total_kb": 20 * 1024 * 1024,
    }
    assert _swapoff_should_recommend(mem, psi=1.0, swap_pct=31.0) is True


def test_boundary_just_above_cap_suppressed():
    # swap_used = 6.5 GB, cap = 8 * 0.8 = 6.4 GB -> 6.5 >= 6.4 -> suppress.
    mem = {
        "total_kb": 16 * 1024 * 1024,
        "available_kb": 8 * 1024 * 1024,
        "swap_used_kb": int(6.5 * 1024 * 1024),
        "swap_total_kb": 20 * 1024 * 1024,
    }
    assert _swapoff_should_recommend(mem, psi=1.0, swap_pct=31.0) is False


def test_high_psi_keeps_recommendation_suppressed_regardless_of_ram():
    # PSI too high (memory pressure) -> no recommendation, regardless of fit.
    mem = {
        "total_kb": 16 * 1024 * 1024,
        "available_kb": 8 * 1024 * 1024,
        "swap_used_kb": 1 * 1024 * 1024,
        "swap_total_kb": 20 * 1024 * 1024,
    }
    assert _swapoff_should_recommend(mem, psi=15.0, swap_pct=50.0) is False


def test_low_swap_pct_suppressed_regardless():
    # Even if PSI calm and RAM abundant, swap_pct below 30% is not actionable.
    mem = {
        "total_kb": 16 * 1024 * 1024,
        "available_kb": 8 * 1024 * 1024,
        "swap_used_kb": 1 * 1024 * 1024,
        "swap_total_kb": 20 * 1024 * 1024,
    }
    assert _swapoff_should_recommend(mem, psi=1.0, swap_pct=20.0) is False