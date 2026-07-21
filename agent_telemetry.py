#!/usr/bin/env python3
"""
agent_telemetry.py — C-WELL Agent Intelligence Telemetry Collector.

Collects agent cognitive, tool, context, and compute telemetry from
systemd journal logs and Prometheus query API. Feeds the C-WELL
coupled intelligence assessment.

Design (forged 2026-07-21):
  - Reads journalctl for agent session events (forge_*, arif_* tool calls)
  - Queries Prometheus for compute metrics (API latency, token counts)
  - Computes: context pressure, tool success rate, looping detection,
    epistemic discipline, planning stability, surprise rate
  - Output conforms to well://schemas/agent-state

Epistemic: DER (inferred from journal + metrics). Confidence: 0.70.
DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import json
import re
import subprocess
import urllib.request
import urllib.parse
import urllib.error
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

# ── Configuration ────────────────────────────────────────────────────────────
JOURNAL_WINDOW_MINUTES = 60  # Look back for agent activity
PROMETHEUS_URL = "http://127.0.0.1:9090"
QUERY_TIMEOUT_S = 3.0
OUTPUT_PATH = Path("/root/WELL/agent_telemetry.json")

# ── Agent session patterns (from journalctl) ──────────────────────────────
AGENT_PATTERNS = [
    r"forge_execute",
    r"forge_shell",
    r"forge_filesystem",
    r"forge_git",
    r"arif_judge",
    r"arif_seal",
    r"arif_observe",
    r"arif_think",
    r"Error:",
    r"FAILED",
    r"rollback",
    r"HOLD",
    r"BLOCKED",
    r"UNKNOWN",
    r"confidence",
    r"tool_call",
]


def _promql(query: str) -> float | None:
    """Execute instant PromQL query."""
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


def collect_journal_telemetry() -> dict[str, Any]:
    """Parse journalctl for agent activity patterns."""
    since = (
        datetime.now(timezone.utc) - timedelta(minutes=JOURNAL_WINDOW_MINUTES)
    ).isoformat()

    try:
        result = subprocess.run(
            [
                "journalctl",
                f"--since={since}",
                "--no-pager",
                "-o",
                "cat",
                "-u",
                "a-forge",
                "-u",
                "a-forge-mcp",
                "-u",
                "opencode*",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        lines = result.stdout.split("\n") if result.returncode == 0 else []
        # Also try system logs for agent activity
        result2 = subprocess.run(
            [
                "journalctl",
                f"--since={since}",
                "--no-pager",
                "-o",
                "cat",
                "-p",
                "warning",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        lines += result2.stdout.split("\n") if result2.returncode == 0 else []
    except (subprocess.TimeoutExpired, FileNotFoundError):
        lines = []

    pattern_counts: dict[str, int] = defaultdict(int)
    for line in lines:
        for pat in AGENT_PATTERNS:
            if re.search(pat, line, re.IGNORECASE):
                pattern_counts[pat] += 1

    total = sum(pattern_counts.values())

    # Classify
    tool_calls = (
        pattern_counts.get("tool_call", 0)
        + pattern_counts.get("forge_execute", 0)
        + pattern_counts.get("forge_shell", 0)
    )
    errors = pattern_counts.get("Error:", 0) + pattern_counts.get("FAILED", 0)
    holds = pattern_counts.get("HOLD", 0) + pattern_counts.get("BLOCKED", 0)
    unknowns = pattern_counts.get("UNKNOWN", 0)
    rollbacks = pattern_counts.get("rollback", 0)
    seals = pattern_counts.get("arif_seal", 0)
    judges = pattern_counts.get("arif_judge", 0)

    return {
        "source": "journalctl",
        "window_minutes": JOURNAL_WINDOW_MINUTES,
        "total_events": total,
        "tool_calls": tool_calls,
        "errors": errors,
        "holds": holds,
        "unknowns": unknowns,
        "rollbacks": rollbacks,
        "seals": seals,
        "judges": judges,
        "tool_error_rate": round(errors / max(tool_calls, 1), 3),
        "pattern_counts": dict(pattern_counts),
    }


def collect_prometheus_telemetry() -> dict[str, Any]:
    """Collect compute metrics from Prometheus."""
    return {
        "source": "prometheus",
        "cpu_idle_pct": _promql(
            '100 - (avg(rate(node_cpu_seconds_total{mode!="idle"}[5m])) * 100)'
        ),
        "mem_available_bytes": _promql("node_memory_MemAvailable_bytes"),
        "load_1m": _promql("node_load1"),
        "disk_free_bytes": _promql('node_filesystem_avail_bytes{mountpoint="/"}'),
        "context_switches_rate": _promql("rate(node_context_switches_total[1m])"),
    }


def assess_agent_state(journal: dict, prom: dict) -> dict[str, Any]:
    """Synthesize agent state from telemetry sources."""
    # Context pressure: tool calls / window
    tool_rate = journal.get("tool_calls", 0) / max(JOURNAL_WINDOW_MINUTES, 1)
    context_pressure = 0.0
    if tool_rate > 10:
        context_pressure = 0.9
    elif tool_rate > 5:
        context_pressure = 0.7
    elif tool_rate > 2:
        context_pressure = 0.5
    elif tool_rate > 0:
        context_pressure = 0.3

    # Epistemic discipline: UNKNOWN ratio
    unknowns_ratio = journal.get("unknowns", 0) / max(journal.get("total_events", 1), 1)

    # Planning stability: rollback ratio
    rollback_ratio = journal.get("rollbacks", 0) / max(
        journal.get("total_events", 1), 1
    )

    # Execution quality: error rate
    error_rate = journal.get("tool_error_rate", 0)

    # Surprise: errors + holds ratio
    surprise_ratio = (journal.get("errors", 0) + journal.get("holds", 0)) / max(
        journal.get("total_events", 1), 1
    )

    # Looping detection: high retry rate (>30% errors indicates possible loops)
    looping_detected = error_rate > 0.30

    # Compute pressure: from Prometheus
    cpu_pressure = 1.0 - ((prom.get("cpu_idle_pct") or 100) / 100)
    mem_avail = prom.get("mem_available_bytes") or 0
    mem_pressure = (
        1.0 - (mem_avail / (32 * 1024**3)) if mem_avail else 0.0
    )  # relative to ~32GB

    return {
        "context": {
            "events_per_minute": round(tool_rate, 1),
            "pressure": round(context_pressure, 2),
        },
        "epistemic": {
            "unknowns_ratio": round(unknowns_ratio, 3),
            "discipline": "GOOD"
            if unknowns_ratio > 0.05
            else ("OK" if unknowns_ratio > 0 else "LOW"),
        },
        "planning": {
            "rollback_ratio": round(rollback_ratio, 3),
            "stability": "UNSTABLE"
            if rollback_ratio > 0.1
            else ("STABLE" if rollback_ratio < 0.05 else "MODERATE"),
        },
        "execution": {
            "tool_error_rate": round(error_rate, 3),
            "quality": "DEGRADED"
            if error_rate > 0.2
            else ("OK" if error_rate < 0.1 else "STRAINED"),
        },
        "looping": {
            "detected": looping_detected,
            "error_rate_threshold": 0.30,
        },
        "surprise": {
            "ratio": round(surprise_ratio, 3),
        },
        "compute": {
            "cpu_pressure": round(cpu_pressure, 2),
            "mem_pressure": round(mem_pressure, 2),
            "load_1m": prom.get("load_1m"),
        },
    }


def collect() -> dict[str, Any]:
    """Run full agent telemetry collection cycle."""
    ts = datetime.now(timezone.utc)

    journal = collect_journal_telemetry()
    prom = collect_prometheus_telemetry()
    agent = assess_agent_state(journal, prom)

    result = {
        "schema": "agent-state v1.0",
        "timestamp": ts.isoformat(),
        "source": "agent_telemetry.py",
        "confidence": 0.70,
        "epistemic_label": "DER",
        "journal": journal,
        "prometheus": prom,
        "agent": agent,
    }

    # Persist
    try:
        OUTPUT_PATH.write_text(json.dumps(result, indent=2, default=str))
    except OSError:
        pass

    return result


def main():
    """CLI entry point."""
    import sys

    data = collect()

    if "--json" in sys.argv:
        print(json.dumps(data, indent=2, default=str))
    else:
        a = data["agent"]
        j = data["journal"]
        print("═══ C-WELL Agent Telemetry ═══")
        print(f"Window:     {j['window_minutes']}min")
        print(
            f"Events:     {j['total_events']} total ({j['tool_calls']} tools, {j['errors']} errors)"
        )
        print(
            f"Context:    {a['context']['events_per_minute']}/min (pressure={a['context']['pressure']})"
        )
        print(
            f"Execution:  {a['execution']['quality']} (error_rate={a['execution']['tool_error_rate']})"
        )
        print(
            f"Epistemic:  {a['epistemic']['discipline']} (unknowns={a['epistemic']['unknowns_ratio']})"
        )
        print(
            f"Planning:   {a['planning']['stability']} (rollbacks={a['planning']['rollback_ratio']})"
        )
        print(f"Looping:    {'⚠️  DETECTED' if a['looping']['detected'] else 'OK'}")
        print(
            f"Compute:    cpu={a['compute']['cpu_pressure']} mem={a['compute']['mem_pressure']} load={a['compute']['load_1m']}"
        )


if __name__ == "__main__":
    main()
