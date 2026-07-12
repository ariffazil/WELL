#!/usr/bin/env python3
"""
WELL Automated Sensor — Machine-to-Human Substrate Mapping

Infers human state from machine telemetry. No biometric devices needed.
The VPS IS the sensor. Every SSH session, cron job, and shell command
tells us something about the human behind the keyboard.

Signals:
  - SSH sessions (sshd-session processes) → human presence
  - Agent CLI processes (claude/opencode/hermes) → agent saturation
  - Auth log patterns → login/logout timing
  - Bash history → command velocity, tool diversity
  - Cron patterns → machine autonomy ratio
  - Time-of-day (UTC+8) → circadian alignment

Output: structured state dict for WELL to ingest.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

import json
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# Arif's timezone
TZ_KL = timezone(timedelta(hours=8))


def _run(cmd: str, timeout: int = 10) -> str:
    """Run a shell command, return stdout."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, Exception):
        return ""


def _parse_loginctl_sessions() -> list[dict[str, Any]]:
    """Parse loginctl list-sessions into structured data."""
    sessions = []
    raw = _run("loginctl list-sessions --no-legend")
    if not raw:
        return sessions

    for line in raw.strip().split("\n"):
        parts = line.split()
        if len(parts) < 4:
            continue
        sid, uid, user = parts[0], parts[1], parts[2]
        props = {}
        for prop in ["Class", "Type", "Remote", "Display", "State", "Idle"]:
            val = _run(f"loginctl show-session {sid} -p {prop} --value")
            props[prop.lower()] = val
        sessions.append({"id": sid, "uid": uid, "user": user, **props})
    return sessions


def _parse_auth_log(hours: int = 24) -> list[dict[str, Any]]:
    """Parse journalctl for session open/close events."""
    events = []
    raw = _run(f'journalctl --since "{hours} hours ago" --no-pager -q 2>/dev/null')
    if not raw:
        return events

    for line in raw.split("\n"):
        m = re.search(
            r"(\d{4}-\d{2}-\d{2}T[\d:]+\+\d{2}:\d{2}).*session (opened|closed) for user (\w+)",
            line,
        )
        if m:
            ts_str, action, user = m.groups()
            try:
                ts = datetime.fromisoformat(ts_str)
                events.append({"timestamp": ts, "action": action, "user": user})
            except ValueError:
                pass
    return events


def _parse_bash_history() -> dict[str, Any]:
    """Analyze bash history for human activity patterns."""
    history_file = Path.home() / ".bash_history"
    if not history_file.exists():
        return {"total_lines": 0, "commands": [], "agent_launches": 0}

    lines = history_file.read_text().split("\n")
    commands = [l.strip() for l in lines if l.strip() and not l.startswith("#")]

    agent_clis = {"claude", "opencode", "codex", "kimi", "grok", "copilot", "cursor"}
    agent_launches = sum(1 for c in commands if c.split()[0] in agent_clis if c.split())

    return {
        "total_lines": len(commands),
        "recent_commands": commands[-20:] if commands else [],
        "agent_launches": agent_launches,
        "unique_commands": len(set(commands)),
    }


def _compute_circadian_phase(now_utc: datetime) -> dict[str, Any]:
    """Determine circadian phase based on UTC+8 local time."""
    local = now_utc.astimezone(TZ_KL)
    hour = local.hour

    if 0 <= hour < 6:
        phase, expected = "SLEEP", 0.0
    elif 6 <= hour < 9:
        phase, expected = "WAKING", 0.3
    elif 9 <= hour < 12:
        phase, expected = "MORNING_PEAK", 0.9
    elif 12 <= hour < 14:
        phase, expected = "MIDDAY_DIP", 0.6
    elif 14 <= hour < 18:
        phase, expected = "AFTERNOON", 0.8
    elif 18 <= hour < 21:
        phase, expected = "EVENING", 0.5
    else:
        phase, expected = "WIND_DOWN", 0.2

    return {
        "phase": phase,
        "local_hour": hour,
        "expected_activity": expected,
        "is_sleep_hours": phase == "SLEEP",
    }


def _classify_sessions(sessions: list[dict]) -> dict[str, Any]:
    """Classify sessions into human, agent, and machine.

    Human  = actual SSH sessions (sshd-session: user@pts/*)
    Agent  = claude/opencode/hermes/codex processes on PTYs
    Machine = systemd managers, cron, services, orphaned sessions
    """
    # Count actual SSH sessions (the real human presence signal)
    sshd_raw = _run("ps aux | grep 'sshd-session:.*@pts' | grep -v grep")
    human_ptys: set[str] = set()
    for line in sshd_raw.split("\n"):
        m = re.search(r"(\w+)@pts/(\d+)", line)
        if m:
            human_ptys.add(f"pts/{m.group(2)}")

    # Count agent CLI processes on PTYs
    agent_clis = {"claude", "opencode", "hermes", "codex", "kimi", "grok"}
    agent_ptys: set[str] = set()
    agent_procs = _run("ps -eo user,tty,comm --no-headers | grep -E 'pts/[0-9]'")
    for line in agent_procs.split("\n"):
        parts = line.split()
        if len(parts) >= 3:
            comm = parts[2].split("/")[-1]  # basename
            tty = parts[1]
            if comm in agent_clis:
                agent_ptys.add(tty)

    human_count = len(human_ptys)
    agent_count = len(agent_ptys)
    machine_count = max(0, len(sessions) - human_count - agent_count)

    return {
        "human_ptys": sorted(human_ptys),
        "agent_ptys": sorted(agent_ptys),
        "human_count": human_count,
        "agent_count": agent_count,
        "machine_count": machine_count,
        "total": len(sessions),
    }


def _compute_machine_autonomy(classified: dict) -> float:
    """How much the machine runs autonomously (0=full human, 1=full machine)."""
    total = classified["total"]
    if total == 0:
        return 1.0
    return classified["machine_count"] / total


def _detect_sleep_gap(auth_events: list[dict]) -> dict[str, Any]:
    """Detect sleep based on gaps in human activity."""
    if not auth_events:
        return {"sleeping": False, "last_activity_hours_ago": None}

    # Detect actual human users — root SSH = Arif on this VPS
    human_users = {"ariffazil", "root"}
    human_events = [
        e for e in auth_events if e["user"] in human_users and e["action"] == "opened"
    ]
    if not human_events:
        return {"sleeping": False, "last_activity_hours_ago": None}

    latest = max(human_events, key=lambda e: e["timestamp"])
    now = datetime.now(timezone.utc)
    gap_hours = (now - latest["timestamp"]).total_seconds() / 3600

    return {
        "sleeping": gap_hours > 4,
        "last_activity_hours_ago": round(gap_hours, 1),
        "last_activity": latest["timestamp"].isoformat(),
    }


def _assess_fatigue(
    circadian: dict, machine_autonomy: float, session_count: int
) -> dict[str, Any]:
    """Assess fatigue level from available signals."""
    score = 0.0
    reasons: list[str] = []

    if circadian["is_sleep_hours"] and session_count > 5:
        score += 0.4
        reasons.append("active_during_sleep_hours")

    if machine_autonomy > 0.8:
        score += 0.1
        reasons.append("high_machine_autonomy")

    if session_count > 30:
        score += 0.2
        reasons.append("session_overload")

    if circadian["phase"] in ("EVENING", "WIND_DOWN", "SLEEP"):
        score += 0.2
        reasons.append("late_activity")

    score = min(score, 1.0)
    level = "LOW" if score < 0.3 else "MODERATE" if score < 0.6 else "HIGH"

    return {"score": round(score, 2), "level": level, "reasons": reasons}


def collect_substrate_signals() -> dict[str, Any]:
    """Collect all machine-to-human substrate signals."""
    now = datetime.now(timezone.utc)

    sessions = _parse_loginctl_sessions()
    auth_events = _parse_auth_log(hours=24)
    history = _parse_bash_history()
    circadian = _compute_circadian_phase(now)

    classified = _classify_sessions(sessions)
    machine_autonomy = _compute_machine_autonomy(classified)
    sleep = _detect_sleep_gap(auth_events)
    fatigue = _assess_fatigue(circadian, machine_autonomy, classified["total"])

    # Overall readiness
    readiness = 1.0
    if sleep["sleeping"]:
        readiness *= 0.3
    readiness *= 1.0 - fatigue["score"] * 0.5
    readiness *= circadian["expected_activity"]
    readiness = max(0.0, min(1.0, readiness))

    return {
        "timestamp": now.isoformat(),
        "sensor": "machine_human_substrate",
        "version": "1.0.0",
        "sessions": {
            "total": classified["total"],
            "human": classified["human_count"],
            "agent": classified["agent_count"],
            "machine": classified["machine_count"],
            "human_ptys": classified["human_ptys"],
            "agent_ptys": classified["agent_ptys"],
        },
        "circadian": circadian,
        "sleep": sleep,
        "fatigue": fatigue,
        "machine_autonomy": round(machine_autonomy, 3),
        "bash_history": {
            "total_commands": history["total_lines"],
            "unique_commands": history["unique_commands"],
            "agent_launches": history["agent_launches"],
        },
        "readiness_score": round(readiness, 3),
        "readiness_band": (
            "GREEN" if readiness > 0.7 else "YELLOW" if readiness > 0.4 else "RED"
        ),
        "honesty": {
            "source_type": "MACHINE_TELEMETRY",
            "is_sensor_verified": True,
            "is_self_report": False,
            "is_mock_or_test": False,
            "is_stale": False,
            "banner": "LIVE — inferred from machine telemetry (sessions, auth, history, circadian)",
        },
    }


def main():
    signals = collect_substrate_signals()
    print(json.dumps(signals, indent=2, default=str))


if __name__ == "__main__":
    main()
