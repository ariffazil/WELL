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
import subprocess
import sys
import time
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Optional: NATS publish support (graceful fallback if lib missing)
try:
    import nats as _nats_lib  # type: ignore
    NATS_LIB_AVAILABLE = True
except Exception:  # pragma: no cover
    _nats_lib = None
    NATS_LIB_AVAILABLE = False

# ── Configuration ────────────────────────────────────────────────────────────
WITNESS_DIR = Path("/var/witness")
LEDGER_PATH = WITNESS_DIR / "ledger.jsonl"
SIGNALS_PATH = WITNESS_DIR / "signals.jsonl"  # append-only 888_HOLD ring buffer
WELL_DIR = Path("/root/WELL")
WELL_MACHINE_STATE = Path(  # FIX 2026-11-01: env-var resolution; writer uses /var/lib/well
    os.environ.get("WELL_MACHINE_STATE_PATH", "/var/lib/well/machine_state.json")
)
PROMETHEUS_URL = "http://127.0.0.1:9090"
WELL_HEALTH_URL = "http://127.0.0.1:18083/health"
QUERY_TIMEOUT_S = 3.0
HISTORY_SIZE = 1000

# Files whose working-tree contents WITNESS verifies against git HEAD.
# These are the surfaces a substrate that rewrites WELL or its witness could touch.
SOURCE_INTEGRITY_FILES = [
    "well_witness.py",
    "well_witness_http.py",
    "server.py",  # canonical WELL server.py used by well.service ExecStart
]

# Federation systemd units WITNESS probes independently. Domain organs must all be
# active for substrate governance to function; WITNESS itself is local (excluded from
# its own escalation set so its own restart doesn't trigger HOLD against itself).
FEDERATION_SERVICES = [
    ("arifOS",    "arifos.service",         True),   # critical: kernel + judge
    ("A-FORGE",   "a-forge.service",        True),   # critical: executor
    ("A-FORGE-MCP", "a-forge-mcp.service",  True),   # MCP transport
    ("GEOX",      "geox-mcp.service",       True),
    ("WEALTH",    "wealth-organ.service",   True),
    ("WELL",      "well.service",           True),   # the substrate WITNESS observes
    ("AAA",       "aaa-a2a.service",        True),
]

# Telemetry freshness — matches WELL watchdog cadence (8am/8pm MYT) with buffer.
TELEMETRY_MAX_AGE_S = 900  # 15 minutes

# NATS — for sovereign signal escalation when WITNESS detects divergence.
NATS_URL = "nats://127.0.0.1:4222"
NATS_HOLD_SUBJECT = "witness.888_hold"


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
# COMPONENT 1: SOURCE INTEGRITY HASHING
# Adversarial posture: assume a hostile substrate may rewrite well_witness.py,
# well_witness_http.py, or server.py to make them appear healthy. Git is the
# independent source of truth. WITNESS computes the working-tree blob hash via
# `git hash-object` and compares it against the blob SHA git has recorded at HEAD.
# Any mismatch is a tampering signal — not a numeric, but a constitutional one.
# ═══════════════════════════════════════════════════════════════════════════════


def _run_git(args: list[str], timeout: int = 5) -> str:
    """Run a git command inside WELL_DIR. Returns stdout, '' on error."""
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=str(WELL_DIR),
            stderr=subprocess.PIPE,
            timeout=timeout,
        ).decode().strip()
    except Exception:
        return ""


def check_source_integrity() -> dict[str, Any]:
    """Verify witness+witness_http+server.py match git HEAD blobs.

    Returns per-file: actual git blob SHA (git hash-object) vs HEAD blob SHA
    (git rev-parse HEAD:<path>). Mismatch ⇒ tampering evidence.
    """
    files = SOURCE_INTEGRITY_FILES
    head = _run_git(["rev-parse", "HEAD"])
    head_short = head[:12] if head else "unknown"

    results: list[dict[str, Any]] = []
    any_violation = False
    git_unavailable = head == ""

    for relpath in files:
        full_path = WELL_DIR / relpath
        if not full_path.exists():
            results.append({
                "file": relpath,
                "exists": False,
                "matches": False,
                "violation": "MISSING",
            })
            any_violation = True
            continue

        # Working-tree blob SHA (independent of index/HEAD).
        actual = _run_git(["hash-object", relpath])
        # HEAD-recorded blob SHA.
        expected = _run_git(["rev-parse", f"HEAD:{relpath}"])

        matches = bool(actual) and bool(expected) and actual == expected
        if not matches:
            any_violation = True

        results.append({
            "file": relpath,
            "exists": True,
            "matches": matches,
            "actual_blob_sha": actual[:12] if actual else "unreadable",
            "head_blob_sha": expected[:12] if expected else "missing",
            "violation": None if matches else (
                "git_unavailable" if not actual or not expected
                else "TAMPER_DETECTED"
            ),
        })

    return {
        "head_commit": head_short,
        "files": results,
        "files_total": len(results),
        "files_intact": sum(1 for r in results if r.get("matches")),
        "any_violation": any_violation,
        "git_unavailable": git_unavailable,
        "verdict": "TAMPER_DETECTED" if any_violation and not git_unavailable
                    else "GIT_UNAVAILABLE" if git_unavailable
                    else "INTACT",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENT 2: INDEPENDENT SERVICE PROBES (systemd)
# Adversarial posture: WELL's status view of other organs might lie. WITNESS
# asks systemd directly via `systemctl is-active`. If a critical organ is
# inactive AND the consensus is divergent, escalate to 888_HOLD.
# ═══════════════════════════════════════════════════════════════════════════════


def _systemd_active(unit: str) -> str:
    """Return systemd is-active result. '' on error."""
    try:
        return subprocess.check_output(
            ["systemctl", "is-active", unit],
            stderr=subprocess.PIPE,
            timeout=3,
        ).decode().strip()
    except Exception:
        return ""


def check_service_probes() -> dict[str, Any]:
    """Probe each federation service independently via systemd.

    Critical organs (kernel, executor, substrate layer) feed substrate governance.
    If any are inactive, WITNESS escalates severity.
    """
    probes = []
    inactive_critical: list[str] = []

    for name, unit, critical in FEDERATION_SERVICES:
        state = _systemd_active(unit)
        active = state == "active"
        probes.append({
            "organ": name,
            "unit": unit,
            "state": state or "unknown",
            "active": active,
            "critical": critical,
        })
        if critical and not active:
            inactive_critical.append(name)

    return {
        "probes": probes,
        "total": len(probes),
        "active": sum(1 for p in probes if p["active"]),
        "inactive_critical": inactive_critical,
        "any_critical_down": bool(inactive_critical),
        "verdict": "CRITICAL_DOWN" if inactive_critical else "OK",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENT 3: TELEMETRY FRESHNESS CHECK
# Adversarial posture: a stale machine_state.json means WITNESS cannot validate
# WELL's claims. Freshness is itself a witness signal.
# ═══════════════════════════════════════════════════════════════════════════════


def check_telemetry_freshness(max_age_s: int = TELEMETRY_MAX_AGE_S) -> dict[str, Any]:
    """mtime check on WELL's machine_state.json.

    The WELL watchdog writes machine_state.json twice daily. If it's stale, WITNESS
    cannot cross-validate WELL's claims against /proc — so the consensus is
    degraded (not held), but operators must know.
    """
    p = WELL_MACHINE_STATE
    if not p.exists():
        return {
            "fresh": False,
            "exists": False,
            "age_seconds": None,
            "max_age_seconds": max_age_s,
            "mtime": None,
            "violation": "MISSING",
            "verdict": "MISSING",
        }

    try:
        mtime_ts = p.stat().st_mtime
        mtime_utc = datetime.fromtimestamp(mtime_ts, tz=timezone.utc)
        age_s = (datetime.now(timezone.utc) - mtime_utc).total_seconds()
    except OSError:
        return {
            "fresh": False,
            "exists": True,
            "age_seconds": None,
            "max_age_seconds": max_age_s,
            "mtime": None,
            "violation": "STAT_ERROR",
            "verdict": "STAT_ERROR",
        }

    fresh = age_s <= max_age_s
    return {
        "fresh": fresh,
        "exists": True,
        "age_seconds": age_s,
        "max_age_seconds": max_age_s,
        "mtime": mtime_utc.isoformat(),
        "violation": None if fresh else "STALE",
        "verdict": "FRESH" if fresh else "STALE",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENT 4: 888_HOLD NATS SIGNALLING
# The sovereign signal channel. When consensus crosses into 888_HOLD severity
# we publish on NATS subject witness.888_hold so that arifOS and AAA can react
# without polling WITNESS. Publish failures fall back to a local signals.jsonl
# ring buffer + stderr, so the signal never silently disappears.
# ═══════════════════════════════════════════════════════════════════════════════


def _publish_nats_sync(subject: str, payload: bytes, timeout_s: float = 1.0) -> bool:
    """Synchronous NATS publish. True on success, False on any failure."""
    if not NATS_LIB_AVAILABLE:
        return False
    try:
        # nats-py 2.x publish is a coroutine. Run it inline in our own loop.
        import asyncio

        async def _do() -> bool:
            nc = await _nats_lib.connect(NATS_URL, connect_timeout=timeout_s)
            try:
                await nc.publish(subject, payload)
                await nc.drain()
                return True
            finally:
                try:
                    await nc.close()
                except Exception:
                    pass

        loop = asyncio.new_event_loop()
        try:
            return bool(loop.run_until_complete(asyncio.wait_for(_do(), timeout=timeout_s + 1)))
        finally:
            loop.close()
    except Exception:
        return False


def signal_888_hold(severity: str, observation: dict[str, Any]) -> dict[str, Any]:
    """If severity is 888_HOLD, publish to NATS. Always log to signals ring buffer.

    Returns a small audit dict: nats_published(bool), nats_attempted(bool),
    logged_path(str). Never raises.
    """
    audit = {
        "nats_published": False,
        "nats_attempted": False,
        "logged_path": str(SIGNALS_PATH),
    }

    if severity != "888_HOLD":
        return audit

    payload = {
        "signal": "witness_888_hold",
        "ts": observation.get("timestamp"),
        "seq": observation.get("seq"),
        "prev_hash": observation.get("prev_hash"),
        "hash": observation.get("hash"),
        "well_self_reported": observation.get("well_self_reported"),
        "consensus": observation.get("consensus", {}).get("verdict"),
        "severity": severity,
        "divergent": observation.get("consensus", {}).get("divergent_details", []),
        "advanced": observation.get("advanced", {}),
    }
    blob = json.dumps(payload, default=str).encode()

    # 1) Try NATS publish.
    if NATS_LIB_AVAILABLE:
        audit["nats_attempted"] = True
        audit["nats_published"] = _publish_nats_sync(NATS_HOLD_SUBJECT, blob)

    # 2) Always log to signals ring buffer (so the signal survives NATS outages).
    try:
        ensure_dir()
        with open(SIGNALS_PATH, "a") as f:
            f.write(
                json.dumps(
                    {**payload, "nats_published": audit["nats_published"]},
                    default=str,
                )
                + "\n"
            )
    except OSError:
        audit["logged_path"] = None

    # 3) stderr — so operators see it immediately.
    try:
        sys.stderr.write(f"[888_HOLD] seq={payload['seq']} {payload['consensus']}\n")
        sys.stderr.flush()
    except OSError:
        pass

    return audit


# ═══════════════════════════════════════════════════════════════════════════════
# COMPONENT 5: WITNESS SELF-CHECK
# Adversarial posture: a witness that cannot read its own sources is worse than
# no witness at all — it would emit blind 888_HOLD or blind OK. Run every sensor
# once during observe() and report which channels are blind.
# ═══════════════════════════════════════════════════════════════════════════════


def witness_self_check() -> dict[str, Any]:
    """Can WITNESS see its own sources? Returns a per-channel readability matrix.

    Any blind channel collapses self-trust. We mark `can_observe=False` if any
    critical channel (proc, prometheus, source integrity) is unreadable.
    """
    proc = witness_read_machine()
    prom = witness_read_prometheus()
    well_ms = witness_read_well_machine_state()
    well_health = witness_probe_well_health()
    integrity = check_source_integrity()
    services = check_service_probes()
    freshness = check_telemetry_freshness()

    channels = {
        # /proc is always readable from userspace with no extra deps. If false,
        # we are in a chroot/jail/container without /proc — report.
        "proc_meminfo": bool(proc.get("memory", {}).get("available_kb")),
        "proc_pressure": proc.get("pressure", {}).get("memory_some_avg10") is not None
                         or proc.get("pressure", {}).get("memory_full_avg10") is not None,
        # Prometheus may be down — that's degraded, not blind. Note for ops.
        "prometheus": prom.get("memory_available_bytes") is not None,
        # WELL machine_state.json may not exist yet. That's not blind — it's missing.
        "well_machine_state": well_ms is not None,
        # WELL health probe may fail if WELL itself is down. Not blind — degraded.
        "well_health": well_health is not None,
        # Source integrity requires git — that's the critical channel. If git isn't
        # there, we have no independent truth source.
        "source_integrity": integrity.get("git_unavailable") is False
                            and integrity.get("any_violation") is False,
        # NATS signalling may not be available. If it's down, our sovereign signal
        # degrades — still observable, but operators must read stderr/signals.jsonl.
        "nats_lib": NATS_LIB_AVAILABLE,
        "telemetry_fresh": freshness.get("fresh"),
        # Witness ledger must be writable — else we cannot hash-chain.
        "ledger_writable": _ledger_writable_probe(),
    }

    # Critical channels: if any of these blind, WITNESS cannot perform its role.
    critical_blind = [
        name for name in ("proc_meminfo", "source_integrity")
        if not channels[name]
    ]
    can_observe = len(critical_blind) == 0

    return {
        "channels": channels,
        "critical_blind": critical_blind,
        "degraded_blind": [
            name for name, ok in channels.items()
            if not ok and name not in critical_blind
        ],
        "can_observe": can_observe,
        "verdict": "BLIND" if not can_observe
                   else ("DEGRADED" if any(not v for v in channels.values()) else "OK"),
    }


def _ledger_writable_probe() -> bool:
    """Probe whether /var/witness/ledger.jsonl is writable. Never raises."""
    try:
        ensure_dir()
        if not LEDGER_PATH.exists():
            # Try creating empty.
            LEDGER_PATH.touch()
        # Append-only probe: read last byte's mode hint via a 0-byte stat check.
        # We deliberately do NOT write a probe entry — too noisy for hash chain.
        with open(LEDGER_PATH, "a") as f:
            pass
        return True
    except OSError:
        return False


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


def check_runtime_attestation(well_health: dict[str, Any] | None) -> dict[str, Any]:
    """P0-6: Capture WELL's runtime identity and cross-check against expected values.

    Reads WELL's self-reported identity (commit, version, identity_hash, schema_version)
    from its health endpoint and cross-checks against:
      - Git HEAD commit (independent of WELL's report)
      - WITNESS's own source integrity check

    Any mismatch in identity or digest is a tampering/attestation failure.
    """
    head = _run_git(["rev-parse", "HEAD"])
    head_short = head[:12] if head else "unknown"

    result: dict[str, Any] = {
        "git_head": head_short,
        "git_head_full": head if head else "unreadable",
        "well_self_reported": {},
        "identity_match": None,
        "verdict": "OK",
    }

    if not well_health:
        result["verdict"] = "WELL_UNREACHABLE"
        return result

    # WELL's self-reported identity from its health endpoint
    well_commit = well_health.get("source_commit", "unknown")
    well_version = well_health.get("version", "unknown")
    well_identity_hash = well_health.get("identity_hash", "unknown")
    well_schema_version = well_health.get("federation_schema_version", "unknown")
    well_tool_count = well_health.get("tool_count", 0)

    result["well_self_reported"] = {
        "commit": well_commit,
        "version": well_version,
        "identity_hash": well_identity_hash[:16] if len(well_identity_hash) > 16 else well_identity_hash,
        "schema_version": well_schema_version,
        "tool_count": well_tool_count,
    }

    # P0 acceptance test: git HEAD == deployed artifact identity == WITNESS-observed digest
    # Normalize: short hashes may have different truncation lengths (7 vs 12 chars).
    # Both should be prefixes of the same full commit SHA.
    identity_match = None
    if head and well_commit != "unknown":
        identity_match = head.startswith(well_commit) or well_commit.startswith(head_short)
    result["identity_match"] = identity_match

    if identity_match is False:
        result["verdict"] = "IDENTITY_MISMATCH"
        result["mismatch_detail"] = {
            "well_commit": well_commit,
            "witness_git_head": head_short,
        }
    elif identity_match is None:
        result["verdict"] = "GIT_UNAVAILABLE"

    return result


def observe() -> dict[str, Any]:
    """Run one full observation cycle (v1.2.0 — adds runtime attestation P0-6)."""
    ts = datetime.now(timezone.utc)

    # Independent readings (legacy /proc + Prometheus cross-reference)
    proc = witness_read_machine()
    prom = witness_read_prometheus()
    well_ms = witness_read_well_machine_state()
    well_health = witness_probe_well_health()

    # Consensus check (legacy)
    consensus = check_consensus(proc, prom, well_ms)

    # ── 6 advanced witness layers (v1.2.0) — added runtime attestation ──────
    advanced = {
        "source_integrity": check_source_integrity(),
        "service_probes": check_service_probes(),
        "telemetry_freshness": check_telemetry_freshness(),
        "self_check": witness_self_check(),
        "runtime_attestation": check_runtime_attestation(well_health),
    }
    # Component 5 (self-check) is also inside advanced for archival, but the
    # integrity/version/critical_blind signals are factored into severity below.

    advanced_severity = compute_advanced_severity(consensus, advanced)

    # WELL's self-reported state
    well_state = None
    if well_health:
        well_state = well_health.get("status")

    # Build observation — version is bumped and final severity is the advanced one.
    observation = {
        "timestamp": ts.isoformat(),
        "witness_version": "1.2.0",
        "sources": {
            "proc": "ok" if proc.get("memory", {}).get("available_kb") else "failed",
            "prometheus": "ok" if prom.get("memory_available_bytes") else "failed",
            "well_machine_state": "ok" if well_ms else "missing",
            "well_health": "ok" if well_health else "unreachable",
        },
        "well_self_reported": well_state,
        "consensus": {**consensus, "severity": advanced_severity["final"]},
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
        "advanced": advanced,
        "advanced_severity": advanced_severity,
    }

    # Hash-chain ledger
    entry_hash = ledger_append(observation)

    # Sovereign signal escalation if final severity is 888_HOLD.
    # signal_888_hold is non-blocking; failures fall back to ring buffer + stderr.
    signal_audit = signal_888_hold(advanced_severity["final"], observation)
    observation["signal"] = signal_audit

    return {**observation, "hash": entry_hash}


def compute_advanced_severity(consensus: dict, advanced: dict) -> dict[str, Any]:
    """Combine legacy consensus severity with the 5 advanced layers.

    Only escalates — never lowers. Never invents urgency the data doesn't support.

    Severity ladder: OK < DEGRADED < WARN < 888_HOLD.
    """
    order = {"OK": 0, "DEGRADED": 1, "WARN": 2, "888_HOLD": 3}
    base = consensus.get("severity", "OK")
    final = base
    reasons: list[str] = []

    def escalate_to(target: str, reason: str) -> None:
        nonlocal final
        if order[target] > order[final]:
            final = target
        if reason not in reasons:
            reasons.append(reason)

    # 1) Source integrity violation is a TAMPERING signal — escalate hard.
    si = advanced["source_integrity"]
    if si.get("any_violation") and not si.get("git_unavailable"):
        escalate_to("888_HOLD", f"source_integrity:{si.get('verdict')}")
    elif si.get("git_unavailable"):
        escalate_to("WARN", "source_integrity:git_unavailable")

    # 2) Self-check blindness — WITNESS itself is broken. Critical channels that
    #    can't be read mean we cannot perform our role. Always 888_HOLD.
    sc = advanced["self_check"]
    if not sc.get("can_observe"):
        escalate_to(
            "888_HOLD",
            f"self_check:{sc.get('verdict')}:{sc.get('critical_blind')}",
        )

    # 3) Stale telemetry — we cannot cross-validate WELL. Demote OK to DEGRADED.
    tf = advanced["telemetry_freshness"]
    if not tf.get("fresh"):
        if final == "OK":
            final = "DEGRADED"
            reasons.append(f"telemetry_freshness:{tf.get('verdict')}")
        else:
            reasons.append(f"telemetry_freshness:stale:{tf.get('verdict')}")

    # 4) Critical organ down alone isn't HOLD — but it amplifies existing warnings.
    sp = advanced["service_probes"]
    if sp.get("any_critical_down"):
        if final in ("WARN", "DEGRADED"):
            escalate_to(
                "888_HOLD",
                f"service_probes:{sp.get('inactive_critical')}",
            )
        else:
            reasons.append(f"service_probes:down:{sp.get('inactive_critical')}")

    return {
        "base": base,
        "final": final,
        "reasons": reasons,
        "order": order[final],
    }


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
                sig = obs.get("signal", {})
                nats_pub = "→NATS" if sig.get("nats_published") else (
                    "→local" if sig.get("nats_attempted") else "·"
                )
                print(
                    f"[{obs['timestamp'][:19]}] {v:15s} {s:10s} hash={obs.get('hash', '?')} {nats_pub}"
                )
                if s == "888_HOLD":
                    print(
                        f"  ⚠️  DIVERGENCE DETECTED: {obs['consensus']['divergent_details']}"
                    )
                    adv = obs.get("advanced_severity", {})
                    if adv.get("reasons"):
                        print(f"  ⚠️  REASONS: {adv['reasons']}")
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
            print("═══ WELL WITNESS v1.1.0 ═══")
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
            # Advanced layers (v1.1.0)
            adv = obs.get("advanced", {})
            adv_sev = obs.get("advanced_severity", {})
            si = adv.get("source_integrity", {})
            sp = adv.get("service_probes", {})
            tf = adv.get("telemetry_freshness", {})
            sc = adv.get("self_check", {})
            print(
                f"Source integ: {si.get('verdict', '?')} (head={si.get('head_commit', '?')}, intact={si.get('files_intact', 0)}/{si.get('files_total', 0)})"
            )
            print(
                f"Service:      {sp.get('verdict', '?')} ({sp.get('active', 0)}/{sp.get('total', 0)} active)"
            )
            print(
                f"Telemetry:    {tf.get('verdict', '?')} (age={int(tf.get('age_seconds') or 0)}s, max={tf.get('max_age_seconds')}s)"
            )
            print(
                f"Self-check:   {sc.get('verdict', '?')} (can_observe={sc.get('can_observe')})"
            )
            if adv_sev.get("reasons"):
                print(f"Escalations:  {adv_sev['reasons']}")
            sig = obs.get("signal", {})
            if sig.get("nats_attempted") or sig.get("nats_published"):
                print(
                    f"Sovereign signal: {'NATS published' if sig.get('nats_published') else 'NATS attempt failed, ring-buffered'}"
                )
            print(f"Boundary:     WITNESS observes. arifOS judges. A-FORGE executes.")
            if obs["consensus"]["divergent_details"]:
                for d in obs["consensus"]["divergent_details"]:
                    print(
                        f"  ⚠️  {d['metric']}: well={d.get('well', '?')} witness={d.get('witness', d.get('proc', '?'))} delta={d.get('delta_pct', d.get('delta_abs', '?'))}"
                    )


if __name__ == "__main__":
    main()
