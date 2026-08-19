"""M-WELL machine physics — RAM/swap/tmpfs gates for advisory recs.

PSI-quiet is not proof that swap pages fit in RAM. swapoff must unswap
every used page into MemAvailable. If they do not fit, swapoff is an
OOM path, not a recycle.

Forged 2026-08-19 after live falsification on af-forge:
  SwapUsed 8.0 GB vs MemAvailable 5.1 GB, PSI avg10=0.0.
  WELL marked swapoff safe because PSI < 5. Physics said HOLD.

Pure functions. No MCP, no FastMCP, no /root/WELL/server.py import.
"""

from __future__ import annotations

from typing import Any

# 1 GiB headroom so swapoff cannot consume the last reclaimable pages.
SWAP_CYCLE_MARGIN_KB = 1_048_576
PSI_QUIET_MAX = 5.0


def assess_swap_cycle(
    available_kb: int,
    swap_used_kb: int,
    mem_psi_avg10: float,
    margin_kb: int = SWAP_CYCLE_MARGIN_KB,
) -> dict[str, Any]:
    """Decide whether swapoff -a && swapon -a is physically safe.

    safe=True only when:
      1. there is swap to recover
      2. PSI is quiet (< 5)
      3. MemAvailable covers SwapUsed + margin
    """
    available_kb = max(int(available_kb or 0), 0)
    swap_used_kb = max(int(swap_used_kb or 0), 0)
    mem_psi_avg10 = float(mem_psi_avg10 or 0.0)
    margin_kb = max(int(margin_kb or 0), 0)

    need_kb = swap_used_kb + margin_kb
    deficit_kb = max(0, need_kb - available_kb)
    ram_fits = deficit_kb == 0
    psi_quiet = mem_psi_avg10 < PSI_QUIET_MAX
    applicable = swap_used_kb > 0
    safe = bool(applicable and ram_fits and psi_quiet)

    if not applicable:
        reason = "no_swap_used"
        action = "none"
        risk = "NONE"
    elif not ram_fits:
        reason = "swap_does_not_fit_in_available_ram"
        action = "HOLD_SWAPOFF"
        risk = "HIGH"
    elif not psi_quiet:
        reason = "memory_pressure_not_quiet"
        action = "HOLD_SWAPOFF_UNTIL_PSI_QUIET"
        risk = "HIGH"
    else:
        reason = "ram_fits_and_psi_quiet"
        action = "swapoff -a && swapon -a"
        risk = "LOW"

    return {
        "safe": safe,
        "applicable": applicable,
        "ram_fits": ram_fits,
        "psi_quiet": psi_quiet,
        "available_kb": available_kb,
        "swap_used_kb": swap_used_kb,
        "margin_kb": margin_kb,
        "need_kb": need_kb,
        "deficit_kb": deficit_kb,
        "deficit_gb": round(deficit_kb / 1024**2, 2),
        "available_gb": round(available_kb / 1024**2, 2),
        "swap_used_gb": round(swap_used_kb / 1024**2, 2),
        "mem_psi_avg10": mem_psi_avg10,
        "reason": reason,
        "action": action,
        "risk": risk,
        "precondition": (
            f"MemAvailable={available_kb}KB >= SwapUsed={swap_used_kb}KB "
            f"+ margin={margin_kb}KB AND mem_psi_avg10={mem_psi_avg10:.1f} < {PSI_QUIET_MAX}"
        ),
    }


def parse_tmpfs_mounts(proc_mounts_text: str) -> list[dict[str, Any]]:
    """Parse /proc/mounts text for tmpfs rows. Pure."""
    mounts: list[dict[str, Any]] = []
    for line in (proc_mounts_text or "").splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        src, dest, fstype = parts[0], parts[1], parts[2]
        if fstype != "tmpfs":
            continue
        mounts.append({"source": src, "dest": dest, "fstype": fstype})
    return mounts


def tmpfs_usage(dest: str) -> dict[str, Any] | None:
    """Live statvfs for a tmpfs mount. None if unreadable."""
    import os

    try:
        st = os.statvfs(dest)
    except OSError:
        return None
    total = st.f_blocks * st.f_frsize
    free = st.f_bfree * st.f_frsize
    used = total - free
    return {
        "dest": dest,
        "fstype": "tmpfs",
        "total_kb": total // 1024,
        "used_kb": used // 1024,
        "free_kb": free // 1024,
        "used_gb": round(used / 1024**3, 2),
        "note": "tmpfs consumes RAM, not disk",
    }


def live_tmpfs_ram(proc_mounts_text: str | None = None) -> dict[str, Any]:
    """Sum RAM held by tmpfs mounts. /tmp is the usual hotspot."""
    from pathlib import Path

    if proc_mounts_text is None:
        try:
            proc_mounts_text = Path("/proc/mounts").read_text()
        except OSError:
            proc_mounts_text = ""
    mounts = parse_tmpfs_mounts(proc_mounts_text)
    usages: list[dict[str, Any]] = []
    total_used_kb = 0
    tmp_used_kb = 0
    for m in mounts:
        u = tmpfs_usage(m["dest"])
        if not u:
            continue
        usages.append({**m, **u})
        total_used_kb += u["used_kb"]
        if m["dest"] == "/tmp":
            tmp_used_kb = u["used_kb"]
    return {
        "mounts": usages,
        "total_used_kb": total_used_kb,
        "tmp_used_kb": tmp_used_kb,
        "tmp_used_gb": round(tmp_used_kb / 1024**2, 2),
        "total_used_gb": round(total_used_kb / 1024**2, 2),
        "note": "tmpfs is RAM. Do not treat /tmp used as disk reclaim.",
    }
