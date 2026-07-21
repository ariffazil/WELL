"""
WELL Vitality Gate — Constitutional Fusion Layer (v2.0.0 · PHASE 1 · 2026-07-21)
═══════════════════════════════════════════════════════════════════════════════

Four mirrors → one gate. Weakest substrate determines response.
Same pattern as ART → Kernel → ACT, but for substrate readiness.

The gate does NOT diagnose. It reads four states and applies
floor dominance: the weakest dimension decides.

PHASE 1 (2026-07-21): Split M_WELL/H_WELL category error.
  - M_WELL now reads machine_state.json (silicon-law: /proc telemetry)
  - H_WELL enriched with machine_human_substrate (carbon-law: session/circadian)
  - Hysteresis gate: 2+ consecutive samples before state degradation
  - Safety lock: ALL verdicts route to observe-only (Phase 2 will unlock)

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

WELL_DIR = Path(__file__).parent
MACHINE_STATE_PATH = WELL_DIR / "machine_state.json"
STATE_PATH = WELL_DIR / "state.json"
SCHEMA_PATH = WELL_DIR / "WELL_STATE_SCHEMA.json"

# ── Rank map: state → numeric rank (higher = healthier) ──────────────────────
_RANK_MAP = {
    # H-WELL
    "READY": 4,
    "BELOW_BASELINE": 3,
    "DEGRADED": 2,
    "CRITICAL": 1,
    "UNKNOWN": 0,
    # M-WELL
    "STABLE": 4,
    "STRAINED": 3,
    "DEGRADED": 2,
    "CRITICAL": 1,
    # G-WELL
    "COHERENT": 4,
    "UNCERTAIN": 3,
    "DRIFTING": 2,
    "COMPROMISED": 1,
    "HOLD": 1,
    # C-WELL
    "LOW_RISK": 4,
    "MEDIUM_RISK": 3,
    "HIGH_RISK": 2,
    "RECOVERY": 2,
}

_VERDICT_MAP = {
    4: "PROCEED",
    3: "REDUCE_LOAD",
    2: "RECOVER",
    1: "HOLD",
    0: "INSUFFICIENT_DATA",
}

# ── Hysteresis constants ──────────────────────────────────────────────────────
HYSTERESIS_MIN_SAMPLES = 2  # consecutive samples required before degrading
HYSTERESIS_SEVERE_MIN = 3  # consecutive for 2+ step degradation
HYSTERESIS_WINDOW = 5  # lookback window in history entries


def _rank(state: str) -> int:
    return _RANK_MAP.get(state, 0)


# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOADERS
# ═══════════════════════════════════════════════════════════════════════════════


def _load_machine_state() -> dict[str, Any] | None:
    """Read cron-collected machine_state.json (silicon-law telemetry)."""
    try:
        if MACHINE_STATE_PATH.exists():
            return json.loads(MACHINE_STATE_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        pass
    return None


def _load_machine_sensor() -> dict[str, Any] | None:
    """Auto-collect machine_human_substrate signals (carbon-law inference)."""
    try:
        from sensors.machine_human_substrate import collect_substrate_signals

        return collect_substrate_signals()
    except Exception as exc:
        return {"_sensor_error": str(exc)}


# ═══════════════════════════════════════════════════════════════════════════════
# M-WELL: Machine Substrate (Silicon Law) — reads machine_state.json
# ═══════════════════════════════════════════════════════════════════════════════


def _assess_machine_telemetry(ms: dict[str, Any]) -> tuple[int, list[str], float]:
    """
    Assess raw machine telemetry → rank + evidence.

    Reads MemAvailable (not MemFree), PSI pressure, swap rate,
    service restart counts, Docker health, disk, CPU load.

    Returns: (rank, evidence_parts, uncertainty)
    """
    ranks: list[int] = []
    evidence: list[str] = []
    uncertainty = 0.05  # /proc is high-confidence

    cpu = ms.get("cpu", {})
    mem = ms.get("memory", {})
    pressure = ms.get("pressure", {})
    disk = ms.get("disk", {})
    services = ms.get("services", {})
    docker = ms.get("docker", [])
    history = ms.get("history", [])

    # 1. Memory: MemAvailable ratio (THE metric that matters)
    total_kb = max(mem.get("total_kb", 1), 1)
    avail_kb = mem.get("available_kb", 0)
    avail_pct = avail_kb / total_kb * 100
    evidence.append(f"MemAvailable={avail_pct:.0f}%")

    if avail_pct < 5:
        ranks.append(1)
        evidence[-1] += " CRITICAL"
    elif avail_pct < 10:
        ranks.append(2)
        evidence[-1] += " LOW"
    elif avail_pct < 20:
        ranks.append(3)
        evidence[-1] += " STRAINED"
    else:
        ranks.append(4)

    # 2. Memory PSI (Pressure Stall Information) — the wall predictor.
    # Linux PSI has two lines: 'some' (partial stall) and 'full' (total stall).
    # 'some' means at least some tasks stalled; 'full' means ALL non-idle tasks stalled.
    # Use explicit fields: memory_some_avg10, memory_full_avg10, etc.
    mem_psi_some = pressure.get("memory_some_avg10", 0)
    mem_psi_full = pressure.get("memory_full_avg10", 0)
    evidence.append(f"mem_psi_some10={mem_psi_some:.1f} full10={mem_psi_full:.1f}")

    # Assess the worse of 'some' and 'full' for floor dominance
    mem_psi = max(mem_psi_some, mem_psi_full)
    if mem_psi > 50:
        ranks.append(1)
    elif mem_psi > 25:
        ranks.append(2)
    elif mem_psi > 10:
        ranks.append(3)
    else:
        ranks.append(4)

    # 3. Swap thrashing: check delta from history.
    # /proc/vmstat counters are CUMULATIVE since boot — raw values are misleading.
    # Always compute delta from last sample before assessing.
    swap_out = mem.get("swap_out_pages", 0)
    swap_in = mem.get("swap_in_pages", 0)

    if history and len(history) >= 2:
        prev = history[-2]
        swap_out_delta = max(0, swap_out - prev.get("swap_out_pages", swap_out))
        swap_in_delta = max(0, swap_in - prev.get("swap_in_pages", swap_in))
        evidence.append(f"swap_delta=+{swap_out_delta}out/+{swap_in_delta}in")
        if swap_out_delta > 100000:
            ranks.append(2)
            evidence[-1] += " THRASHING"
        elif swap_out_delta > 10000:
            ranks.append(3)
        else:
            ranks.append(4)
    else:
        # No history — use absolute swap occupancy as fallback
        swap_total = max(mem.get("swap_total_kb", 1), 1)
        swap_used = mem.get("swap_used_kb", 0)
        swap_pct = swap_used / swap_total * 100
        evidence.append(f"swap_used={swap_pct:.0f}%")
        if swap_pct > 80:
            ranks.append(2)
        elif swap_pct > 50:
            ranks.append(3)
        else:
            ranks.append(4)

    # 4. Disk headroom
    disk_pct = disk.get("root_used_pct", 0)
    evidence.append(f"disk={disk_pct:.0f}%")
    if disk_pct > 95:
        ranks.append(1)
    elif disk_pct > 85:
        ranks.append(2)
    elif disk_pct > 75:
        ranks.append(3)
    else:
        ranks.append(4)

    # 5. CPU load vs core count
    load_1m = cpu.get("load_1m", 0)
    cpu_count = os.cpu_count() or 4
    load_ratio = load_1m / cpu_count
    iowait = cpu.get("iowait_pct", 0)
    steal = cpu.get("steal_pct", 0)
    evidence.append(f"load={load_1m:.1f}({load_ratio:.1f}/core) iowait={iowait:.1f}%")

    if load_ratio > 8 or steal > 10:
        ranks.append(1)
    elif load_ratio > 4 or iowait > 20:
        ranks.append(2)
    elif load_ratio > 2:
        ranks.append(3)
    else:
        ranks.append(4)

    # 6. Service health: restart counts
    svc_issues = []
    for name, svc in services.items():
        restarts = svc.get("restart_count", 0)
        active = svc.get("active", True)
        if not active:
            svc_issues.append(f"{name}=DOWN")
        elif restarts > 5:
            svc_issues.append(f"{name}={restarts}restarts")

    evidence.append(f"services={'OK' if not svc_issues else ', '.join(svc_issues)}")
    if any("DOWN" in s for s in svc_issues):
        ranks.append(1)
    elif svc_issues:
        ranks.append(2)
    else:
        ranks.append(4)

    # 7. Docker container health
    # Only penalize explicitly unhealthy containers (have HEALTHCHECK + failing).
    # Containers without HEALTHCHECK are neutral — not healthy, not unhealthy.
    # Statuses from collector: "healthy" / "unhealthy" / "unknown" (no HEALTHCHECK)
    docker_total = len(docker)
    docker_explicit_healthy = sum(
        1 for c in docker if c.get("health_status") == "healthy"
    )
    docker_explicit_unhealthy = sum(
        1 for c in docker if c.get("health_status") == "unhealthy"
    )
    docker_no_check = docker_total - docker_explicit_healthy - docker_explicit_unhealthy
    evidence.append(
        f"docker={docker_explicit_healthy}healthy/{docker_explicit_unhealthy}unhealthy/"
        f"{docker_no_check}no-check"
    )

    if docker_explicit_unhealthy > 0:
        # At least one container is explicitly failing its HEALTHCHECK
        ranks.append(2)
    else:
        ranks.append(4)

    # Floor dominance: weakest metric determines machine state
    min_rank = min(ranks) if ranks else 0

    return min_rank, evidence, uncertainty


def _hysteresis_gate(
    ms: dict[str, Any],
    current_rank: int,
) -> tuple[int, bool, str]:
    """
    Hysteresis gate: require N consecutive samples before degrading state.

    - Immediate improvement: YES (if current_rank > previous, accept now)
    - Degradation: require HYSTERESIS_MIN_SAMPLES consecutive degraded samples
    - Severe degradation (2+ steps): require HYSTERESIS_SEVERE_MIN samples

    Returns: (gated_rank, overridden, reason)
    """
    history = ms.get("history", [])
    if len(history) < HYSTERESIS_MIN_SAMPLES:
        # Not enough history — trust current assessment
        return current_rank, False, "insufficient_history"

    # Re-assess the last N-1 history entries to see if they also show degradation
    # For simplicity: use the slim history entries directly
    recent = history[-HYSTERESIS_WINDOW:]

    # Count how many of the recent samples would also rank at current_rank or worse
    degraded_count = 0
    for entry in recent[-HYSTERESIS_MIN_SAMPLES:]:
        # Approximate rank from history slim fields
        mem_pct = entry.get("mem_used_pct", 0)
        disk_pct = entry.get("disk_used_pct", 0)
        docker_healthy = entry.get(
            "docker_healthy", docker_total := entry.get("docker_total", 1)
        )
        docker_total = entry.get("docker_total", docker_healthy)
        services_active = entry.get("services_active", entry.get("services_total", 1))
        services_total = entry.get("services_total", services_active)
        zombies = entry.get("zombies", 0)

        # Simple rank approximation from slim history fields.
        # NOTE: docker_healthy counts only HEALTHCHECK-instrumented containers.
        # A low docker_healthy count usually means "no HEALTHCHECK configured,"
        # NOT "containers are failing." Omit docker check from hysteresis
        # because slim history lacks health_status granularity.
        if mem_pct >= 95 or disk_pct >= 95:
            hist_rank = 1
        elif (
            mem_pct >= 85
            or disk_pct >= 85
            or services_active < services_total
            or zombies > 10
        ):
            hist_rank = 2
        elif mem_pct >= 75:
            hist_rank = 3
        else:
            hist_rank = 4

        if hist_rank <= current_rank:
            degraded_count += 1

    rank_delta = max(0, _get_previous_rank(recent) - current_rank)

    if rank_delta >= 2:
        # Severe drop — require more samples
        required = HYSTERESIS_SEVERE_MIN
    else:
        required = HYSTERESIS_MIN_SAMPLES

    if degraded_count >= required:
        return current_rank, False, f"hysteresis_passed({degraded_count}/{required})"
    else:
        # Hold previous state
        prev_rank = _get_previous_rank(recent) if recent else current_rank
        prev_rank = max(prev_rank, current_rank + 1)  # Don't drop more than 1 step
        return prev_rank, True, f"hysteresis_held({degraded_count}/{required})"


def _get_previous_rank(recent: list[dict]) -> int:
    """Estimate previous rank from the most recent history entry."""
    if not recent:
        return 4
    entry = recent[-1]
    mem_pct = entry.get("mem_used_pct", 0)
    disk_pct = entry.get("disk_used_pct", 0)
    docker_healthy = entry.get("docker_healthy", 1)
    docker_total = entry.get("docker_total", 1)
    services_active = entry.get("services_active", 1)
    services_total = entry.get("services_total", 1)
    zombies = entry.get("zombies", 0)

    if mem_pct >= 95 or disk_pct >= 95:
        return 1
    # NOTE: docker check omitted — slim history lacks health_status field.
    if mem_pct >= 85 or disk_pct >= 85 or zombies > 10:
        return 2
    if mem_pct >= 75 or services_active < services_total:
        return 3
    return 4


def assess_m_well() -> dict[str, Any]:
    """
    Assess M-WELL (machine substrate — SILICON LAW).

    PHASE 1 (2026-07-21): Now reads machine_state.json only.
    No longer conflated with machine_human_substrate (carbon-law data).

    Sources:
      - machine_state.json (cron-collected /proc + systemd + docker telemetry)
      - MemAvailable, PSI pressure, swap rate, service restarts, Docker health
      - 24h history for hysteresis gate

    Returns: {state, rank, evidence, uncertainty, source, hysteresis}
    """
    ms = _load_machine_state()

    if ms is None:
        return {
            "state": "UNKNOWN",
            "rank": 0,
            "evidence": "machine_state.json not found or unreadable",
            "uncertainty": 0.9,
            "source": "none",
            "hysteresis": "no_data",
        }

    # Check freshness
    ts = ms.get("timestamp", "")
    age_hours = None
    if ts:
        try:
            dt = datetime.fromisoformat(str(ts).replace("+00:00", "").replace("Z", ""))
            # Handle both formats
            if "+00:00" in str(ts) or "Z" in str(ts):
                pass
            dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            age_hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
        except Exception:
            pass

    if age_hours is not None and age_hours > 1.0:
        return {
            "state": "UNKNOWN",
            "rank": 0,
            "evidence": f"machine_state.json stale ({age_hours:.1f}h old)",
            "uncertainty": 0.8,
            "source": "stale_telemetry",
            "hysteresis": "stale",
        }

    raw_rank, evidence, uncertainty = _assess_machine_telemetry(ms)

    # Hysteresis gate
    gated_rank, overridden, hysteresis_reason = _hysteresis_gate(ms, raw_rank)

    inv = {4: "STABLE", 3: "STRAINED", 2: "DEGRADED", 1: "CRITICAL", 0: "UNKNOWN"}
    m_state = inv.get(gated_rank, "UNKNOWN")

    result = {
        "state": m_state,
        "rank": gated_rank,
        "evidence": "; ".join(evidence),
        "uncertainty": uncertainty,
        "source": "machine_state.json",
        "hysteresis": hysteresis_reason,
        "_raw_rank": raw_rank,
        "_overridden": overridden,
    }

    if age_hours is not None:
        result["_age_hours"] = round(age_hours, 2)

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# H-WELL: Human Substrate (Carbon Law)
# ═══════════════════════════════════════════════════════════════════════════════


def assess_h_well(
    state: dict[str, Any],
    substrate_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Assess H-WELL (human substrate — CARBON LAW).

    PHASE 1 (2026-07-21): Now accepts optional machine_human_substrate data
    (session patterns, circadian, fatigue) as additional carbon-law evidence.
    The machine_human_substrate sensor was previously mislabeled as M-WELL;
    it is carbon-law inference from machine patterns, not machine health.

    Primary: state.json (biometric inject / operator self-report)
    Secondary: machine_human_substrate (session count, circadian, sleep gap)
    """
    ts = state.get("timestamp", "")
    truth = state.get("truth_status", "UNVERIFIED")
    well_score = state.get("well_score")

    evidence_parts: list[str] = []
    sources: list[str] = []
    combined_rank = 0

    # --- Primary: self-report / biometric inject ---
    age_hours = None
    if ts:
        try:
            dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            age_hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
        except Exception:
            pass

    if truth == "INSUFFICIENT_DATA" or age_hours is None:
        h_state = "UNKNOWN"
        h_rank = 0
        evidence_parts.append("no_biometric_data")
        uncertainty = 0.9
    elif age_hours > 48:
        h_state = "UNKNOWN"
        h_rank = 0
        evidence_parts.append(f"stale_{age_hours:.0f}h")
        uncertainty = 0.8
    elif truth == "OPERATOR_REPORTED":
        if well_score is not None:
            if well_score >= 70:
                h_state = "READY"
            elif well_score >= 50:
                h_state = "BELOW_BASELINE"
            elif well_score >= 30:
                h_state = "DEGRADED"
            else:
                h_state = "CRITICAL"
        else:
            h_state = "UNKNOWN"
        h_rank = _rank(h_state)
        evidence_parts.append(f"self_report_score={well_score}")
        uncertainty = 0.4
        sources.append("biometric_inject.sh")
    else:
        h_state = "READY"
        h_rank = 4
        evidence_parts.append("verified_telemetry")
        uncertainty = 0.1
        sources.append("wearable")

    combined_rank = h_rank

    # --- Secondary: machine_human_substrate (carbon inference) ---
    if substrate_data and not substrate_data.get("_sensor_error"):
        readiness = float(substrate_data.get("readiness_score", 0) or 0)
        fatigue = substrate_data.get("fatigue", {}) or {}
        sessions = substrate_data.get("sessions", {}) or {}
        circadian = substrate_data.get("circadian", {}) or {}
        sleep = substrate_data.get("sleep", {}) or {}

        # Carbon-law signals from machine patterns
        if readiness < 0.3:
            substrate_rank = 1
        elif readiness < 0.5:
            substrate_rank = 2
        elif readiness < 0.7:
            substrate_rank = 3
        else:
            substrate_rank = 4

        # Weighted blend: 60% self-report, 40% machine inference
        # But self-report always dominates if present (sovereign knows own state)
        if combined_rank > 0:
            # Self-report present — use substrate as enrichment only
            evidence_parts.append(
                f"substrate_readiness={readiness:.2f} "
                f"fatigue={fatigue.get('level', '?')} "
                f"sessions={sessions.get('human', 0)}/{sessions.get('agent', 0)} "
                f"circadian={circadian.get('phase', '?')}"
            )
            sources.append("machine_human_substrate")
            # Substrate can only degrade by 1 rank, not more
            if substrate_rank < combined_rank - 1:
                evidence_parts.append(
                    "substrate_divergence: machine inference much worse than self-report"
                )
            combined_rank = min(combined_rank, substrate_rank + 1)
        else:
            # No self-report — substrate is the only signal
            combined_rank = substrate_rank
            evidence_parts.append(
                f"substrate_only readiness={readiness:.2f} "
                f"circadian={circadian.get('phase', '?')} "
                f"sleeping={sleep.get('sleeping', False)}"
            )
            sources.append("machine_human_substrate")
            uncertainty = max(uncertainty, 0.5)

        if sleep.get("sleeping"):
            evidence_parts.append("sleep_detected")

    # Re-determine state from combined rank
    inv_h = {
        4: "READY",
        3: "BELOW_BASELINE",
        2: "DEGRADED",
        1: "CRITICAL",
        0: "UNKNOWN",
    }
    final_state = inv_h.get(combined_rank, "UNKNOWN")

    return {
        "state": final_state,
        "rank": combined_rank,
        "evidence": "; ".join(evidence_parts),
        "uncertainty": uncertainty,
        "source": "+".join(sources) if sources else "none",
        "note": "OPERATOR_REPORTED — not sensor verified"
        if truth == "OPERATOR_REPORTED"
        else "",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# G-WELL + C-WELL (unchanged from v1)
# ═══════════════════════════════════════════════════════════════════════════════


def assess_g_well(state: dict[str, Any]) -> dict[str, Any]:
    """
    Assess G-WELL (governance coherence) from state + carry_forward.
    Checks identity drift, seal chain, floor compliance.
    """
    carry_forward_path = Path("/root/.local/share/arifos/carry_forward.json")
    drift = "UNKNOWN"
    try:
        cf = json.loads(carry_forward_path.read_text())
        drift = cf.get("identity_drift", "UNKNOWN")
    except Exception:
        pass

    floors_violated = state.get("floors_violated", [])
    truth = state.get("truth_status", "UNVERIFIED")

    if floors_violated:
        g_state = "COMPROMISED"
    elif drift == "DRIFT":
        g_state = "DRIFTING"
    elif truth in ("VOID", "TEST"):
        g_state = "UNCERTAIN"
    else:
        g_state = "COHERENT"

    return {
        "state": g_state,
        "rank": _rank(g_state),
        "evidence": f"drift={drift}, floors_violated={len(floors_violated)}, truth={truth}",
        "uncertainty": 0.15,
        "source": "carry_forward + state.json",
    }


def assess_c_well(h: dict, m: dict, g: dict) -> dict[str, Any]:
    """
    Assess C-WELL (coupled state) from H, M, G assessments.
    Weakest substrate + interaction risk.
    """
    h_rank = h["rank"]
    m_rank = m["rank"]
    g_rank = g["rank"]

    min_rank = min(h_rank, m_rank, g_rank)
    degraded_count = sum(1 for r in [h_rank, m_rank, g_rank] if r <= 2)

    if min_rank <= 1 or degraded_count >= 2:
        c_state = "HIGH_RISK"
    elif min_rank == 2 or degraded_count == 1:
        c_state = "MEDIUM_RISK"
    elif min_rank == 0:
        c_state = "RECOVERY"
    else:
        c_state = "LOW_RISK"

    return {
        "state": c_state,
        "rank": _rank(c_state),
        "evidence": f"H={h['state']}({h_rank}) M={m['state']}({m_rank}) G={g['state']}({g_rank}), "
        f"degraded_count={degraded_count}",
        "uncertainty": max(h["uncertainty"], m["uncertainty"], g["uncertainty"]),
        "source": "coupled_analysis",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# VITALITY GATE — Four Mirrors → One Verdict
# ═══════════════════════════════════════════════════════════════════════════════


def vitality_gate(
    state: dict[str, Any] | None = None,
    sensor_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    The constitutional vitality gate.
    Four mirrors → one verdict. Weakest substrate determines response.

    PHASE 1 (2026-07-21):
      - sensor_data (machine_human_substrate) now feeds H-WELL, not M-WELL
      - M-WELL reads machine_state.json (/proc telemetry)
      - Hysteresis gate on M-WELL state transitions
      - ALL verdicts route to observe-only (safety lock)

    Returns:
        verdict: PROCEED | REDUCE_LOAD | RECOVER | HOLD | INSUFFICIENT_DATA
        H_WELL, M_WELL, G_WELL, C_WELL: individual assessments
        weakest: which substrate is the bottleneck
        tool_routing: what tools are allowed (PHASE 1: observe-only always)
        peace_condition: whether peace is achievable
        phase: "PHASE_1_OBSERVE_ONLY"
    """
    if state is None:
        if STATE_PATH.exists():
            state = json.loads(STATE_PATH.read_text())
        else:
            state = {}
    _state: dict[str, Any] = state

    # Auto-collect machine_human_substrate if not injected by caller
    if sensor_data is None:
        sensor_data = _load_machine_sensor()

    # Assess all four mirrors
    h = assess_h_well(_state, substrate_data=sensor_data)
    m = assess_m_well()  # PHASE 1: reads machine_state.json, NOT sensor_data
    g = assess_g_well(_state)
    c = assess_c_well(h, m, g)

    # Weakest substrate = gate
    all_dims = {"H_WELL": h, "M_WELL": m, "G_WELL": g, "C_WELL": c}
    weakest_name = min(all_dims, key=lambda k: all_dims[k]["rank"])
    weakest_rank = all_dims[weakest_name]["rank"]

    raw_verdict = _VERDICT_MAP.get(weakest_rank, "INSUFFICIENT_DATA")

    # ═══════════════════════════════════════════════════════════════════════
    # PHASE 1 SAFETY LOCK: ALL verdicts route to observe-only.
    # The gate reports accurate M_WELL state but does NOT authorize
    # mutations until Phase 2 guardrails (verify-after-act, coherence
    # check, root-cause, reversibility) are built.
    # ═══════════════════════════════════════════════════════════════════════
    phase1_routing = {
        "allowed": "observe only, reflection, health checks",
        "blocked": "all mutations, all seals, all deploys",
        "note": "PHASE 1 SAFETY LOCK — gate is truthful but does not authorize action. "
        "Phase 2 will unlock after verify-after-act, coherence-check, "
        "root-cause-on-recurrence, and quarantine allowlist are wired.",
    }

    # Peace condition
    peace = (
        h["rank"] >= 2
        and (m["rank"] >= 3 or m["state"] == "STRAINED")
        and g["rank"] >= 3
        and c["rank"] >= 3
    )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "verdict": raw_verdict,
        "weakest_substrate": weakest_name,
        "weakest_rank": weakest_rank,
        "H_WELL": h,
        "M_WELL": m,
        "G_WELL": g,
        "C_WELL": c,
        "tool_routing": phase1_routing,
        "peace_condition": peace,
        "peace_note": "Peace = recoverable homeostasis with preserved sovereignty. "
        "Not permanent calm. Not optimized predictability.",
        "gate_rule": "Weakest substrate determines response. Floor dominance.",
        "schema_version": "2.0.0",
        "phase": "PHASE_1_OBSERVE_ONLY",
        "phase_note": "Gate reports truthful M-WELL from machine_state.json. "
        "All verdicts locked to observe-only pending Phase 2 guardrails.",
        "_raw_verdict": raw_verdict,
        "_would_allow": _phase2_routing(raw_verdict),
    }


def _phase2_routing(verdict: str) -> dict[str, Any]:
    """What tool_routing WOULD be without Phase 1 safety lock (preview only)."""
    routing = {
        "PROCEED": {"allowed": "all", "blocked": "none"},
        "REDUCE_LOAD": {
            "allowed": "observe, plan, reflect, low-risk edits",
            "blocked": "C4 irreversible, new deps, prod deploy",
        },
        "RECOVER": {
            "allowed": "observe only, reflection, health checks",
            "blocked": "all mutations, all seals, all deploys",
        },
        "HOLD": {
            "allowed": "health probes only",
            "blocked": "everything else",
            "requires": "sovereign ack to release",
        },
        "INSUFFICIENT_DATA": {
            "allowed": "observe, inject, sensor read",
            "blocked": "mutations, seals",
            "action": "request sovereign inject or wait for sensor",
        },
    }
    return routing.get(verdict, routing["INSUFFICIENT_DATA"])


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════


def main():
    """CLI entry point — run the vitality gate."""
    import sys

    # Optionally load sensor data
    sensor_data = None
    sensor_path = WELL_DIR / "sensors" / "machine_human_substrate.py"
    if sensor_path.exists():
        try:
            import importlib.util

            spec = importlib.util.spec_from_file_location("mhs", sensor_path)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                sensor_data = mod.collect_substrate_signals()
        except Exception:
            pass

    result = vitality_gate(sensor_data=sensor_data)

    if "--json" in sys.argv:
        print(json.dumps(result, indent=2, default=str))
    else:
        print("═══ WELL VITALITY GATE v2.0.0 (PHASE 1) ═══")
        print(f"Verdict:           {result['verdict']}")
        print(
            f"Weakest substrate: {result['weakest_substrate']} (rank {result['weakest_rank']})"
        )
        print(f"Peace:             {'YES' if result['peace_condition'] else 'NO'}")
        print(f"Phase:             {result['phase']}")
        print()

        for dim in ["H_WELL", "M_WELL", "G_WELL", "C_WELL"]:
            d = result[dim]
            hyst = f"  [{d.get('hysteresis', '')}]" if d.get("hysteresis") else ""
            print(
                f"  {dim}: {d['state']:20s} rank={d['rank']}  Ω={d['uncertainty']:.2f}{hyst}"
            )
            print(f"         {d['evidence']}")
        print()
        print(f"TOOL ROUTING (PHASE 1 SAFETY LOCK):")
        print(f"  Allowed:  {result['tool_routing']['allowed']}")
        print(f"  Blocked:  {result['tool_routing']['blocked']}")
        print(f"  Note:     {result['tool_routing']['note']}")
        print()
        would = result.get("_would_allow", {})
        print(f"WOULD ALLOW (Phase 2 preview):  {would.get('allowed', '?')}")
        print(f"WOULD BLOCK (Phase 2 preview):  {would.get('blocked', '?')}")


if __name__ == "__main__":
    main()
