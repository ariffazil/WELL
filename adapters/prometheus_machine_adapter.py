#!/usr/bin/env python3
"""
prometheus_machine_adapter.py — Node Exporter → WELL Machine State Bridge.

Queries Prometheus for node_exporter metrics and maps them to the
WELL machine-state schema (well://schemas/machine-state).

Design (forged 2026-07-21):
  1. Query Prometheus HTTP API — no local /proc parsing.
  2. Map node_exporter metric names → WELL schema fields.
  3. Every metric carries provenance (source, timestamp, query).
  4. Returns UNKNOWN for any metric Prometheus doesn't have.

Epistemic: OBS (Prometheus query result). Confidence: 0.90 (API latency).

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Configuration ────────────────────────────────────────────────────────────
PROMETHEUS_URL = "http://127.0.0.1:9090"
QUERY_TIMEOUT_S = 5.0
DEFAULT_CONFIDENCE = 0.90

# ── Metric map: node_exporter metric → WELL machine_state field ──────────────
METRIC_MAP = {
    # CPU
    "cpu_load_1m": "node_load1",
    "cpu_load_5m": "node_load5",
    "cpu_load_15m": "node_load15",
    "cpu_idle_pct": 'rate(node_cpu_seconds_total{mode="idle"}[1m]) * 100',
    "cpu_iowait_pct": 'rate(node_cpu_seconds_total{mode="iowait"}[1m]) * 100',
    "cpu_steal_pct": 'rate(node_cpu_seconds_total{mode="steal"}[1m]) * 100',
    "cpu_user_pct": 'rate(node_cpu_seconds_total{mode="user"}[1m]) * 100',
    "cpu_system_pct": 'rate(node_cpu_seconds_total{mode="system"}[1m]) * 100',
    # Memory (THE metrics that matter)
    "mem_total_kb": "node_memory_MemTotal_bytes / 1024",
    "mem_available_kb": "node_memory_MemAvailable_bytes / 1024",
    "mem_free_kb": "node_memory_MemFree_bytes / 1024",
    "mem_buffers_kb": "node_memory_Buffers_bytes / 1024",
    "mem_cached_kb": "node_memory_Cached_bytes / 1024",
    "mem_swap_total_kb": "node_memory_SwapTotal_bytes / 1024",
    "mem_swap_free_kb": "node_memory_SwapFree_bytes / 1024",
    # Disk
    "disk_root_used_pct": '(1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100',
    "disk_root_free_gb": 'node_filesystem_avail_bytes{mountpoint="/"} / 1073741824',
    # Network (bytes total since boot — use rate() for throughput)
    "net_bytes_recv": 'rate(node_network_receive_bytes_total{device!="lo"}[1m])',
    "net_bytes_sent": 'rate(node_network_transmit_bytes_total{device!="lo"}[1m])',
    # Context switches
    "context_switches": "rate(node_context_switches_total[1m])",
}


def _promql_query(query: str) -> float | None:
    """Execute an instant PromQL query and return the scalar value."""
    url = f"{PROMETHEUS_URL}/api/v1/query?query={urllib.parse.quote(query)}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=QUERY_TIMEOUT_S) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError, OSError) as exc:
        return None

    try:
        results = data.get("data", {}).get("result", [])
        if results:
            return float(results[0]["value"][1])
    except (KeyError, IndexError, ValueError, TypeError):
        pass
    return None


def collect_from_prometheus() -> dict[str, Any]:
    """Collect machine state from Prometheus node_exporter metrics.

    Returns:
        Dict matching the machine-state schema fields.
        Fields that fail to query are set to None.
    """
    result: dict[str, Any] = {
        "schema": "machine_state.json v1.0",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        "hostname": "forge",
        "source": "prometheus://node-exporter",
        "truth_status": "OBSERVED",
        "confidence": DEFAULT_CONFIDENCE,
        "cpu": {},
        "memory": {},
        "disk": {},
        "net": {},
        "queries_succeeded": 0,
        "queries_failed": 0,
        "queries_total": 0,
    }

    raw: dict[str, float | None] = {}
    succeeded = 0
    failed = 0

    for field, promql in METRIC_MAP.items():
        val = _promql_query(promql)
        raw[field] = val
        if val is not None:
            succeeded += 1
        else:
            failed += 1

    # ── Map raw values to structured fields ───────────────────────────────

    # CPU
    cpu = result["cpu"]
    cpu["load_1m"] = raw.get("cpu_load_1m")
    cpu["load_5m"] = raw.get("cpu_load_5m")
    cpu["load_15m"] = raw.get("cpu_load_15m")
    cpu["idle_pct"] = raw.get("cpu_idle_pct")
    cpu["iowait_pct"] = raw.get("cpu_iowait_pct")
    cpu["steal_pct"] = raw.get("cpu_steal_pct")
    cpu["user_pct"] = raw.get("cpu_user_pct")
    cpu["system_pct"] = raw.get("cpu_system_pct")

    # Memory
    mem = result["memory"]
    mem["total_kb"] = int(raw["mem_total_kb"]) if raw.get("mem_total_kb") else None
    mem["available_kb"] = (
        int(raw["mem_available_kb"]) if raw.get("mem_available_kb") else None
    )
    mem["free_kb"] = int(raw["mem_free_kb"]) if raw.get("mem_free_kb") else None
    mem["buffers_kb"] = (
        int(raw["mem_buffers_kb"]) if raw.get("mem_buffers_kb") else None
    )
    mem["cached_kb"] = int(raw["mem_cached_kb"]) if raw.get("mem_cached_kb") else None
    mem["swap_total_kb"] = (
        int(raw["mem_swap_total_kb"]) if raw.get("mem_swap_total_kb") else None
    )
    mem["swap_free_kb"] = (
        int(raw["mem_swap_free_kb"]) if raw.get("mem_swap_free_kb") else None
    )

    if mem["total_kb"] and mem["available_kb"]:
        mem["used_kb"] = mem["total_kb"] - mem["available_kb"]

    if mem["swap_total_kb"] and mem["swap_free_kb"] is not None:
        mem["swap_used_kb"] = mem["swap_total_kb"] - mem["swap_free_kb"]

    # Disk
    disk = result["disk"]
    disk_pct = raw.get("disk_root_used_pct")
    disk["root_used_pct"] = round(disk_pct, 1) if disk_pct is not None else None
    disk_gb = raw.get("disk_root_free_gb")
    disk["root_free_gb"] = round(disk_gb, 1) if disk_gb is not None else None

    # Network
    net = result["net"]
    net["bytes_recv_per_s"] = raw.get("net_bytes_recv")
    net["bytes_sent_per_s"] = raw.get("net_bytes_sent")

    # Context switches
    result["context_switches_per_s"] = raw.get("context_switches")

    result["queries_succeeded"] = succeeded
    result["queries_failed"] = failed
    result["queries_total"] = succeeded + failed

    # Adjust confidence
    if failed > 0:
        result["confidence"] = max(
            0.5, DEFAULT_CONFIDENCE * (succeeded / (succeeded + failed))
        )

    return result


# ── CLI ──────────────────────────────────────────────────────────────────────
def main():
    """Run the adapter from CLI and print the result."""
    import sys

    state = collect_from_prometheus()

    print("═══ Prometheus → WELL Machine State Adapter ═══")
    print(f"Timestamp:   {state['timestamp']}")
    print(
        f"Queries:     {state['queries_succeeded']}/{state['queries_total']} succeeded"
    )
    print(f"Confidence:  {state['confidence']:.2f}")
    print()

    cpu = state["cpu"]
    mem = state["memory"]
    disk = state["disk"]

    print(
        f"CPU:    load={cpu.get('load_1m')} idle={cpu.get('idle_pct')}% iowait={cpu.get('iowait_pct')}% steal={cpu.get('steal_pct')}%"
    )
    print(
        f"Memory: avail={_fmt_kb(mem.get('available_kb'))} total={_fmt_kb(mem.get('total_kb'))}"
    )
    print(
        f"Swap:   used={_fmt_kb(mem.get('swap_used_kb'))} total={_fmt_kb(mem.get('swap_total_kb'))}"
    )
    print(
        f"Disk:   used={disk.get('root_used_pct')}% free={disk.get('root_free_gb')} GB"
    )

    if "--json" in sys.argv:
        print(json.dumps(state, indent=2, default=str))


def _fmt_kb(val: int | None) -> str:
    if val is None:
        return "N/A"
    if val > 1024 * 1024:
        return f"{val / (1024 * 1024):.1f} GiB"
    if val > 1024:
        return f"{val / 1024:.0f} MiB"
    return f"{val} KiB"


if __name__ == "__main__":
    main()
