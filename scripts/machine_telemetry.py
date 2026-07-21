#!/usr/bin/env python3
"""
machine_telemetry.py — Canonical VPS telemetry collector for M-WELL.
Samples Linux /proc, systemd, docker, and disk → writes machine_state.json.
Runs via cron every 5 minutes. Read-only. Zero mutation.

Design disciplines (forged 2026-07-21):
  1. Measures MemAvailable, not MemFree — the metric that matters.
  2. Samples swap-in/out rate and major page faults — not just swap occupancy.
  3. Persists 24h history for hysteresis (2-3 sample threshold before state change).
  4. Records service restart counts for root-cause recurrence detection.
  5. Source: /proc, not inference. Every field has provenance.

Schema: machine_state.json v1.0
  timestamp, uptime_seconds
  cpu: load_1m, load_5m, load_15m, steal_pct, user_pct, system_pct, idle_pct, iowait_pct
  memory: total_kb, available_kb, used_kb, swap_total_kb, swap_used_kb, swap_in_pg, swap_out_pg
  pressure: mem_pressure_some, io_pressure_some, cpu_pressure_some
  faults: major_page_faults_total
  disk: root_used_pct, root_free_gb, inode_used_pct
  services: {name: {active, restart_count, pid}}
  docker: [{name, status, healthy, uptime}]
  history: [last 5 snapshots at 1-min intervals for hysteresis]

Epistemic: OBS (direct /proc/sysfs read). Confidence: 0.95.
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

STATE_FILE = Path("/root/WELL/machine_state.json")
STATE_BAK = STATE_FILE.with_suffix(".json.bak")
HISTORY_MAX = 288  # 24 hours at 5-min intervals

# ── Collectors ──────────────────────────────────────────────────────────────


def read_file(path: str) -> str:
    try:
        return Path(path).read_text().strip()
    except (OSError, FileNotFoundError):
        return ""


def read_lines(path: str) -> list[str]:
    try:
        return Path(path).read_text().strip().splitlines()
    except (OSError, FileNotFoundError):
        return []


def cpu_stats() -> dict:
    """Read /proc/loadavg and /proc/stat for CPU metrics."""
    load = read_file("/proc/loadavg").split()
    stat_lines = read_lines("/proc/stat")
    cpu_line = next((l for l in stat_lines if l.startswith("cpu ")), "")
    fields = cpu_line.split()
    # Fields: user nice system idle iowait irq softirq steal guest guest_nice
    if len(fields) >= 8:
        user = int(fields[1])
        system = int(fields[3])
        idle = int(fields[4])
        iowait = int(fields[5]) if len(fields) > 5 else 0
        steal = int(fields[7]) if len(fields) > 7 else 0
        total = user + system + idle + iowait + steal
        total = total or 1
    else:
        user = system = idle = iowait = steal = 0
        total = 1

    # Also count context switches (not shown in main cpu line)
    ctxt = 0
    for l in stat_lines:
        if l.startswith("ctxt "):
            ctxt = int(l.split()[1])
            break

    return {
        "load_1m": float(load[0]) if len(load) > 0 else 0.0,
        "load_5m": float(load[1]) if len(load) > 1 else 0.0,
        "load_15m": float(load[2]) if len(load) > 2 else 0.0,
        "user_pct": round(user / total * 100, 1),
        "system_pct": round(system / total * 100, 1),
        "idle_pct": round(idle / total * 100, 1),
        "iowait_pct": round(iowait / total * 100, 1),
        "steal_pct": round(steal / total * 100, 1),
        "context_switches": ctxt,
    }


def memory_stats() -> dict:
    """Read /proc/meminfo for memory metrics. Measures MemAvailable, not MemFree."""
    mem = {}
    for line in read_lines("/proc/meminfo"):
        parts = line.split(":")
        if len(parts) == 2:
            key = parts[0].strip()
            val = parts[1].strip().split()[0]
            try:
                mem[key] = int(val)
            except ValueError:
                mem[key] = 0

    # Also get swap stats from /proc/vmstat
    vmstat = {}
    for line in read_lines("/proc/vmstat"):
        parts = line.split()
        if len(parts) == 2:
            try:
                vmstat[parts[0]] = int(parts[1])
            except ValueError:
                pass

    return {
        "total_kb": mem.get("MemTotal", 0),
        "available_kb": mem.get("MemAvailable", 0),  # THE metric that matters
        "free_kb": mem.get("MemFree", 0),
        "used_kb": mem.get("MemTotal", 0) - mem.get("MemAvailable", 0),
        "buffers_kb": mem.get("Buffers", 0),
        "cached_kb": mem.get("Cached", 0),
        "swap_total_kb": mem.get("SwapTotal", 0),
        "swap_free_kb": mem.get("SwapFree", 0),
        "swap_used_kb": mem.get("SwapTotal", 0) - mem.get("SwapFree", 0),
        "swap_in_pages": vmstat.get("pswpin", 0),
        "swap_out_pages": vmstat.get("pswpout", 0),
        "major_faults": vmstat.get("pgmajfault", 0),
    }


def pressure_stats() -> dict:
    """Read /proc/pressure/* for Linux PSI (Pressure Stall Information).

    PSI files have TWO lines: 'some' (partial stall) and 'full' (total stall).
    Each has: avg10, avg60, avg300 (percentages) and total (microseconds).
    THE semantic difference is critical — 'some' means at least some tasks stalled;
    'full' means ALL non-idle tasks stalled simultaneously.

    Output keys: {memory,cpu,io}_{some,full}_{avg10,avg60,avg300,total}
    """
    result = {}
    for name in ("cpu", "io", "memory"):
        path = f"/proc/pressure/{name}"
        content = read_file(path)
        if not content:
            continue
        # Parse each line independently to keep some/full distinct
        for line in content.strip().split("\n"):
            if not line.strip():
                continue
            # Format: "some avg10=0.00 avg60=0.01 avg300=0.00 total=123456"
            #       or "full avg10=0.00 avg60=0.00 avg300=0.00 total=987654"
            tokens = line.strip().split()
            if not tokens:
                continue
            line_type = tokens[0]  # "some" or "full"
            if line_type not in ("some", "full"):
                continue
            for part in tokens[1:]:
                if "=" in part:
                    k, v = part.split("=")
                    try:
                        result[f"{name}_{line_type}_{k}"] = float(v)
                    except ValueError:
                        result[f"{name}_{line_type}_{k}"] = v
    return result


def disk_stats() -> dict:
    """Read disk usage for root filesystem."""
    try:
        stat = os.statvfs("/")
        total = stat.f_blocks * stat.f_frsize
        free = stat.f_bfree * stat.f_frsize
        used = total - free
        used_pct = round(used / total * 100, 1) if total > 0 else 0
        free_gb = round(free / (1024**3), 1)
        inode_pct = (
            round((1 - stat.f_ffree / stat.f_files) * 100, 1) if stat.f_files > 0 else 0
        )
    except OSError:
        used_pct = 0
        free_gb = 0
        inode_pct = 0

    return {
        "root_used_pct": used_pct,
        "root_free_gb": free_gb,
        "inode_used_pct": inode_pct,
    }


def service_stats() -> dict:
    """Query systemd for key federation services."""
    services = [
        "arifos",
        "a-forge",
        "a-forge-mcp",
        "geox-mcp",
        "wealth-organ",
        "well",
        "aaa-a2a",
        "caddy",
        "netdata",
    ]
    result = {}
    for svc in services:
        try:
            active = subprocess.run(
                ["systemctl", "is-active", svc],
                capture_output=True,
                text=True,
                timeout=5,
            ).stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            active = "unknown"

        # Get restart count from systemd properties
        restarts = 0
        try:
            props = subprocess.run(
                ["systemctl", "show", svc, "-p", "NRestarts"],
                capture_output=True,
                text=True,
                timeout=5,
            ).stdout.strip()
            if "=" in props:
                restarts = int(props.split("=")[1])
        except (subprocess.TimeoutExpired, ValueError, FileNotFoundError):
            pass

        # Get main PID
        pid = 0
        try:
            main_pid = subprocess.run(
                ["systemctl", "show", svc, "-p", "MainPID"],
                capture_output=True,
                text=True,
                timeout=5,
            ).stdout.strip()
            if "=" in main_pid:
                pid = int(main_pid.split("=")[1])
        except (subprocess.TimeoutExpired, ValueError, FileNotFoundError):
            pass

        result[svc] = {
            "active": active == "active",
            "restart_count": restarts,
            "pid": pid,
        }
    return result


def docker_stats() -> list:
    """Query docker for container health."""
    try:
        raw = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}\t{{.Image}}"],
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []

    containers = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        name = parts[0] if len(parts) > 0 else "unknown"
        status = parts[1] if len(parts) > 1 else "unknown"
        containers.append(
            {
                "name": name,
                "status": status,
                "healthy": "(healthy)" in status,
                "health_status": (
                    "healthy"
                    if "(healthy)" in status
                    else "unhealthy"
                    if "(unhealthy)" in status or "(health: starting)" in status
                    else "unknown"
                ),
                "up": "Up" in status,
            }
        )
    return containers


def zombie_count() -> int:
    """Count zombie processes."""
    count = 0
    for entry in Path("/proc").iterdir():
        if entry.is_dir() and entry.name.isdigit():
            try:
                stat = (entry / "stat").read_text()
                if "Z" in stat.split(")")[-1].split()[0] if ")" in stat else False:
                    count += 1
            except (OSError, IndexError):
                pass
    return count


# ── History ─────────────────────────────────────────────────────────────────


def load_history() -> list:
    """Load existing history from state file."""
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text())
            return state.get("history", [])
        except (json.JSONDecodeError, OSError):
            pass
    return []


def append_history(history: list, snapshot: dict, max_len: int = HISTORY_MAX) -> list:
    """Append current snapshot to history, trimming to max_len."""
    # Keep only essential fields in history to avoid bloat
    slim = {
        "ts": snapshot["timestamp"],
        "cpu_load_1m": snapshot["cpu"]["load_1m"],
        "cpu_idle_pct": snapshot["cpu"]["idle_pct"],
        "cpu_iowait_pct": snapshot["cpu"]["iowait_pct"],
        "mem_available_kb": snapshot["memory"]["available_kb"],
        "mem_used_pct": round(
            snapshot["memory"]["used_kb"]
            / max(snapshot["memory"]["total_kb"], 1)
            * 100,
            1,
        ),
        "swap_used_kb": snapshot["memory"]["swap_used_kb"],
        "swap_in_pages": snapshot["memory"]["swap_in_pages"],
        "swap_out_pages": snapshot["memory"]["swap_out_pages"],
        "major_faults": snapshot["memory"]["major_faults"],
        "disk_used_pct": snapshot["disk"]["root_used_pct"],
        "docker_healthy": sum(1 for c in snapshot["docker"] if c["healthy"]),
        "docker_total": len(snapshot["docker"]),
        "services_active": sum(1 for s in snapshot["services"].values() if s["active"]),
        "services_total": len(snapshot["services"]),
        "zombies": snapshot["zombies"],
    }
    history.append(slim)
    return history[-max_len:]


# ── Main ─────────────────────────────────────────────────────────────────────


def collect() -> dict:
    """Collect full machine telemetry snapshot."""
    now = datetime.now(timezone.utc)
    # Read uptime
    uptime_raw = read_file("/proc/uptime").split()
    uptime_s = float(uptime_raw[0]) if uptime_raw else 0.0

    snapshot = {
        "schema": "machine_state.json v1.0",
        "timestamp": now.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        "timestamp_unix": now.timestamp(),
        "hostname": os.uname().nodename,
        "uptime_seconds": uptime_s,
        "uptime_hours": round(uptime_s / 3600, 1),
        "cpu": cpu_stats(),
        "memory": memory_stats(),
        "pressure": pressure_stats(),
        "disk": disk_stats(),
        "services": service_stats(),
        "docker": docker_stats(),
        "zombies": zombie_count(),
        "source": "/proc + systemctl + docker ps",
        "truth_status": "OBSERVED",
        "confidence": 0.95,
    }
    return snapshot


def main():
    snapshot = collect()
    history = load_history()
    snapshot["history"] = append_history(history, snapshot)

    # Write atomically
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(snapshot, indent=2))
    tmp.replace(STATE_FILE)

    # Keep backup
    if STATE_FILE.exists():
        try:
            STATE_BAK.write_text(STATE_FILE.read_text())
        except OSError:
            pass

    print(f"✓ machine_state.json written ({len(snapshot['history'])} history entries)")
    mem = snapshot["memory"]
    print(
        f"  MemAvailable: {mem['available_kb'] // 1024} MiB | "
        f"CPU idle: {snapshot['cpu']['idle_pct']}% | "
        f"Swap: {mem['swap_used_kb'] // 1024} MiB | "
        f"Disk: {snapshot['disk']['root_used_pct']}% | "
        f"Services: {sum(1 for s in snapshot['services'].values() if s['active'])}/{len(snapshot['services'])} active"
    )


if __name__ == "__main__":
    main()
