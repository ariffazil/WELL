#!/usr/bin/env python3
"""
well_witness.py — Independent substrate observer for WELL.

Reads /proc and Prometheus independently. Cross-references against WELL's
machine_state.json. Reports consensus or divergence. Hash-chains observations.

Design (forged 2026-07-21):
  - Separate process — not inside WELL's runtime
  - Reads /proc directly — does not trust WELL's collector
  - Cross-references Prometheus — independent telemetry source
  - Hash-chains observations — tamper-evident ledger
  - Adversarial stance: assumes substrate may try to appear healthy

Usage:
  python3 well_witness.py              # single observation
  python3 well_witness.py --daemon 60  # observe every 60 seconds
  python3 well_witness.py --json       # JSON output

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import json
import hashlib
import os
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Configuration ────────────────────────────────────────────────────────────
WITNESS_DIR = Path("/var/witness")
LEDGER_PATH = WITNESS_DIR / "ledger.jsonl"
WELL_MACHINE_STATE = Path("/root/WELL/machine_state.json")
PROMETHEUS_URL = "http://127.0.0.1:9090"
WELL_HEALTH_URL = "http://127.0.0.1:18083/health"
QUERY_TIMEOUT_S = 3.0
HISTORY_SIZE = 1000


def ensure_dir() -> None:
    WITNESS_DIR.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════════════════════
# INDEPENDENT SENSORS (direct /proc reads — do NOT trust WELL)
# ═══════════════════════════════════════════════════════════════════════════════


def read_proc_meminfo() -> dict[str, int]:
    """Read /proc/meminfo independently."""
    result = {}
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip().split()[0]  # strip " kB" suffix
                result[key] = int(val)
    except (OSError, ValueError):
        pass
    return result


def read_proc_pressure(resource: str) -> dict[str, float]:
    """Read /proc/pressure/{cpu,io,memory} independently."""
    result: dict[str, float] = {}
    try:
        content = Path(f"/proc/pressure/{resource}").read_text()
        for line in content.strip().split("\n"):
            tokens = line.strip().split()
            if not tokens or tokens[0] not in ("some", "full"):
                continue
            line_type = tokens[0]
            for part in tokens[1:]:
                if "=" in part:
                    k, v = part.split("=")
                    result[f"{line_type}_{k}"] = float(v)
    except (OSError, ValueError):
        pass
    return result


def read_proc_loadavg() -> dict[str, float]:
    """Read /proc/loadavg independently."""
    try:
        parts = Path("/proc/loadavg").read_text().strip().split()
        return {
            "load_1m": float(parts[0]),
            "load_5m": float(parts[1]),
            "load_15m": float(parts[2]),
        }
    except (OSError, ValueError, IndexError):
        return {}


def read_disk() -> dict[str, float]:
    """Read disk usage independently via statvfs."""
    try:
        stat = os.statvfs("/")
        total = stat.f_blocks * stat.f_frsize
        free = stat.f_bfree * stat.f_frsize
        return {
            "root_used_pct": round((1 - free / total) * 100, 1) if total > 0 else 0,
            "root_free_gb": round(free / (1024**3), 1),
        }
    except OSError:
        return {}


def witness_read_machine() -> dict[str, Any]:
    """Read machine state directly from /proc — independent of WELL."""
    meminfo = read_proc_meminfo()
    mem_pressure = read_proc_pressure("memory")

    total_kb = meminfo.get("MemTotal", 0)
    available_kb = meminfo.get("MemAvailable", 0)

    return {
        "source": "witness_direct_proc",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "memory": {
            "total_kb": total_kb,
            "available_kb": available_kb,
            "available_pct": round(available_kb / max(total_kb, 1) * 100, 1),
            "swap_total_kb": meminfo.get("SwapTotal", 0),
            "swap_free_kb": meminfo.get("SwapFree", 0),
        },
        "pressure": {
            "memory_some_avg10": mem_pressure.get("some_avg10"),
            "memory_full_avg10": mem_pressure.get("full_avg10"),
        },
        "load": read_proc_loadavg(),
        "disk": read_disk(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PROMETHEUS CROSS-REFERENCE (independent telemetry source)
# ═══════════════════════════════════════════════════════════════════════════════


def prometheus_query(query: str) -> float | None:
    """Query Prometheus instant API."""
    url = f"{PROMETHEUS_URL}/api/v1/query?query={urllib.parse.quote(query)}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=QUERY_TIMEOUT_S) as resp:
            data = json.loads(resp.read().decode())
            results = data.get("data", {}).get("result", [])
            if results:
                return float(results[0]["value"][1])
    except Exception:
        pass
    return None


def witness_read_prometheus() -> dict[str, Any]:
    """Read machine metrics from Prometheus node_exporter."""
    return {
        "source": "witness_prometheus",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "memory_available_bytes": prometheus_query("node_memory_MemAvailable_bytes"),
        "memory_total_bytes": prometheus_query("node_memory_MemTotal_bytes"),
        "load_1m": prometheus_query("node_load1"),
        "disk_free_bytes": prometheus_query(
            'node_filesystem_avail_bytes{mountpoint="/"}'
        ),
        "disk_total_bytes": prometheus_query(
            'node_filesystem_size_bytes{mountpoint="/"}'
        ),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# WELL CROSS-REFERENCE (read WELL's own output — but don't trust it)
# ═══════════════════════════════════════════════════════════════════════════════


def witness_read_well_machine_state() -> dict[str, Any] | None:
    """Read WELL's machine_state.json (untrusted source)."""
    try:
        if WELL_MACHINE_STATE.exists():
            return json.loads(WELL_MACHINE_STATE.read_text())
    except (json.JSONDecodeError, OSError):
        pass
    return None


def witness_probe_well_health() -> dict[str, Any] | None:
    """Probe WELL's health endpoint."""
    try:
        req = urllib.request.Request(WELL_HEALTH_URL)
        with urllib.request.urlopen(req, timeout=QUERY_TIMEOUT_S) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# CONSENSUS CHECK
# ═══════════════════════════════════════════════════════════════════════════════


def check_consensus(
    witness_proc: dict,
    witness_prom: dict,
    well_machine: dict | None,
) -> dict[str, Any]:
    """Compare independent readings against WELL's claims."""
    checks = []

    # 1. MemAvailable: /proc vs WELL's machine_state.json
    if well_machine:
        well_avail = well_machine.get("memory", {}).get("available_kb")
        proc_avail = witness_proc.get("memory", {}).get("available_kb")
        if well_avail and proc_avail:
            delta_pct = abs(well_avail - proc_avail) / max(proc_avail, 1) * 100
            checks.append(
                {
                    "metric": "MemAvailable",
                    "well": well_avail,
                    "witness": proc_avail,
                    "delta_pct": round(delta_pct, 2),
                    "consensus": delta_pct < 5,
                }
            )

        # 2. Memory PSI
        well_psi = well_machine.get("pressure", {}).get("memory_some_avg10")
        proc_psi = witness_proc.get("pressure", {}).get("memory_some_avg10")
        if well_psi is not None and proc_psi is not None:
            delta_abs = abs(well_psi - proc_psi)
            checks.append(
                {
                    "metric": "mem_psi_some_avg10",
                    "well": well_psi,
                    "witness": proc_psi,
                    "delta_abs": round(delta_abs, 2),
                    "consensus": delta_abs < 5,
                }
            )

    # 3. MemAvailable: /proc vs Prometheus
    prom_avail_bytes = witness_prom.get("memory_available_bytes")
    proc_avail_bytes = (witness_proc.get("memory", {}).get("available_kb") or 0) * 1024
    if prom_avail_bytes and proc_avail_bytes:
        delta_pct = (
            abs(prom_avail_bytes - proc_avail_bytes) / max(proc_avail_bytes, 1) * 100
        )
        checks.append(
            {
                "metric": "MemAvailable (proc vs prom)",
                "proc": proc_avail_bytes,
                "prometheus": prom_avail_bytes,
                "delta_pct": round(delta_pct, 2),
                "consensus": delta_pct < 5,
            }
        )

    # 4. Load: /proc vs Prometheus
    prom_load = witness_prom.get("load_1m")
    proc_load = witness_proc.get("load", {}).get("load_1m")
    if prom_load is not None and proc_load is not None:
        delta_abs = abs(prom_load - proc_load)
        checks.append(
            {
                "metric": "load_1m",
                "proc": proc_load,
                "prometheus": prom_load,
                "delta_abs": round(delta_abs, 2),
                "consensus": delta_abs < 1.0,
            }
        )

    all_consensus = all(c.get("consensus", True) for c in checks) if checks else None
    divergent = [c for c in checks if not c.get("consensus", True)]

    return {
        "checks": checks,
        "checks_total": len(checks),
        "checks_consensus": sum(1 for c in checks if c.get("consensus", True)),
        "checks_divergent": len(divergent),
        "all_consensus": all_consensus,
        "divergent_details": divergent,
        "verdict": "CONSENSUS"
        if all_consensus
        else ("DIVERGENCE" if divergent else "INSUFFICIENT_DATA"),
        "severity": "OK"
        if all_consensus
        else ("WARN" if len(divergent) <= 1 else "888_HOLD"),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# HASH-CHAIN LEDGER
# ═══════════════════════════════════════════════════════════════════════════════


def ledger_append(entry: dict) -> str:
    """Append to hash-chained witness ledger. Returns the new entry hash."""
    ensure_dir()

    # Read last entry's hash for chain continuity
    prev_hash = ""
    if LEDGER_PATH.exists():
        try:
            lines = LEDGER_PATH.read_text().strip().split("\n")
            if lines:
                last = json.loads(lines[-1])
                prev_hash = last.get("hash", "")
        except (json.JSONDecodeError, IndexError):
            pass

    # Compute hash of this entry
    entry["prev_hash"] = prev_hash
    entry["seq"] = _next_seq()
    raw = json.dumps(entry, sort_keys=True, default=str)
    entry["hash"] = hashlib.sha256(raw.encode()).hexdigest()[:16]

    # Append
    with open(LEDGER_PATH, "a") as f:
        f.write(json.dumps(entry, default=str) + "\n")

    return entry["hash"]


def _next_seq() -> int:
    if not LEDGER_PATH.exists():
        return 1
    try:
        lines = LEDGER_PATH.read_text().strip().split("\n")
        if lines:
            last = json.loads(lines[-1])
            return last.get("seq", 0) + 1
    except Exception:
        pass
    return 1


def verify_chain() -> dict[str, Any]:
    """Verify hash-chain integrity."""
    if not LEDGER_PATH.exists():
        return {"valid": True, "entries": 0, "note": "no ledger yet"}

    lines = LEDGER_PATH.read_text().strip().split("\n")
    entries = []
    for line in lines:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            return {"valid": False, "error": "corrupt entry"}

    for i in range(1, len(entries)):
        expected_prev = entries[i - 1].get("hash", "")
        actual_prev = entries[i].get("prev_hash", "")
        if expected_prev != actual_prev:
            return {
                "valid": False,
                "error": f"chain break at seq {entries[i].get('seq')}",
                "expected_prev": expected_prev,
                "actual_prev": actual_prev,
            }

    return {
        "valid": True,
        "entries": len(entries),
        "last_hash": entries[-1].get("hash", "") if entries else "",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN OBSERVATION CYCLE
# ═══════════════════════════════════════════════════════════════════════════════


def observe() -> dict[str, Any]:
    """Run one full observation cycle."""
    ts = datetime.now(timezone.utc)

    # Independent readings
    proc = witness_read_machine()
    prom = witness_read_prometheus()
    well_ms = witness_read_well_machine_state()
    well_health = witness_probe_well_health()

    # Consensus check
    consensus = check_consensus(proc, prom, well_ms)

    # WELL's self-reported state
    well_state = None
    if well_health:
        well_state = well_health.get("status")

    # Build observation
    observation = {
        "timestamp": ts.isoformat(),
        "witness_version": "1.0.0",
        "sources": {
            "proc": "ok" if proc.get("memory", {}).get("available_kb") else "failed",
            "prometheus": "ok" if prom.get("memory_available_bytes") else "failed",
            "well_machine_state": "ok" if well_ms else "missing",
            "well_health": "ok" if well_health else "unreachable",
        },
        "well_self_reported": well_state,
        "consensus": consensus,
        "readings": {
            "proc": {
                "mem_avail_pct": proc.get("memory", {}).get("available_pct"),
                "psi_some_avg10": proc.get("pressure", {}).get("memory_some_avg10"),
                "load_1m": proc.get("load", {}).get("load_1m"),
            },
            "prometheus": {
                "mem_avail_bytes": prom.get("memory_available_bytes"),
                "load_1m": prom.get("load_1m"),
            },
        },
    }

    # Ledger
    entry_hash = ledger_append(observation)

    return {**observation, "hash": entry_hash}


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════


def main():
    import sys

    if "--daemon" in sys.argv:
        interval = 60
        for i, arg in enumerate(sys.argv):
            if arg == "--daemon" and i + 1 < len(sys.argv):
                try:
                    interval = int(sys.argv[i + 1])
                except ValueError:
                    pass
        print(f"WITNESS daemon — observing every {interval}s")
        print(f"Ledger: {LEDGER_PATH}")
        try:
            while True:
                obs = observe()
                v = obs["consensus"]["verdict"]
                s = obs["consensus"]["severity"]
                print(
                    f"[{obs['timestamp'][:19]}] {v:15s} {s:10s} hash={obs.get('hash', '?')}"
                )
                if s == "888_HOLD":
                    print(
                        f"  ⚠️  DIVERGENCE DETECTED: {obs['consensus']['divergent_details']}"
                    )
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nWITNESS stopped.")
            chain = verify_chain()
            print(f"Chain: {chain['entries']} entries, valid={chain['valid']}")
    else:
        obs = observe()
        if "--json" in sys.argv:
            print(json.dumps(obs, indent=2, default=str))
        else:
            print("═══ WELL WITNESS ═══")
            print(f"Timestamp:    {obs['timestamp'][:19]}")
            print(
                f"Sources:      proc={obs['sources']['proc']}, prom={obs['sources']['prometheus']}, well={obs['sources']['well_machine_state']}"
            )
            print(f"WELL says:    {obs['well_self_reported']}")
            print(
                f"Consensus:    {obs['consensus']['verdict']} ({obs['consensus']['checks_consensus']}/{obs['consensus']['checks_total']} checks agree)"
            )
            print(f"Severity:     {obs['consensus']['severity']}")
            print(f"Hash:         {obs.get('hash', '?')}")
            if obs["consensus"]["divergent_details"]:
                for d in obs["consensus"]["divergent_details"]:
                    print(
                        f"  ⚠️  {d['metric']}: well={d.get('well', '?')} witness={d.get('witness', d.get('proc', '?'))} delta={d.get('delta_pct', d.get('delta_abs', '?'))}"
                    )


if __name__ == "__main__":
    main()
