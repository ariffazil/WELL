"""Swap-cycle physics: PSI-quiet is not enough.

Live scar 2026-08-19: SwapUsed 8.0GB, MemAvailable 5.1GB, PSI=0.0.
WELL marked swapoff safe. Physics HOLDs. Deficit ~3.1GB + 1GB margin.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from well_machine_physics import (
    SWAP_CYCLE_MARGIN_KB,
    assess_swap_cycle,
    parse_tmpfs_mounts,
)


def test_psi_quiet_does_not_make_swapoff_safe_when_ram_short():
    # Live af-forge numbers (KB)
    result = assess_swap_cycle(
        available_kb=int(5.1 * 1024**2),
        swap_used_kb=int(8.0 * 1024**2),
        mem_psi_avg10=0.0,
    )
    assert result["safe"] is False
    assert result["psi_quiet"] is True
    assert result["ram_fits"] is False
    assert result["action"] == "HOLD_SWAPOFF"
    assert result["reason"] == "swap_does_not_fit_in_available_ram"
    assert result["deficit_gb"] > 3.0


def test_swapoff_safe_only_when_ram_covers_swap_plus_margin():
    swap = 2 * 1024**2  # 2 GiB
    avail = swap + SWAP_CYCLE_MARGIN_KB + 1024
    result = assess_swap_cycle(avail, swap, mem_psi_avg10=0.4)
    assert result["safe"] is True
    assert result["action"] == "swapoff -a && swapon -a"
    assert result["risk"] == "LOW"


def test_high_psi_blocks_even_when_ram_fits():
    swap = 1 * 1024**2
    avail = swap + SWAP_CYCLE_MARGIN_KB + 1024
    result = assess_swap_cycle(avail, swap, mem_psi_avg10=12.0)
    assert result["safe"] is False
    assert result["action"] == "HOLD_SWAPOFF_UNTIL_PSI_QUIET"


def test_zero_swap_not_applicable():
    result = assess_swap_cycle(8 * 1024**2, 0, 0.0)
    assert result["applicable"] is False
    assert result["safe"] is False
    assert result["action"] == "none"


def test_parse_tmpfs_includes_tmp():
    mounts = parse_tmpfs_mounts(
        "tmpfs /tmp tmpfs rw,nosuid,nodev 0 0\n"
        "/dev/sda1 / ext4 rw 0 0\n"
    )
    assert mounts == [{"source": "tmpfs", "dest": "/tmp", "fstype": "tmpfs"}]
