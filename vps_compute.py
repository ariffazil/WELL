#!/usr/bin/env python3
"""
VITALITY PEACE SCORE (VPS) — Multi-dimensional readiness index.

VPS = 0.40H + 0.20M + 0.25G + 0.15C

NOT health, happiness, productivity, obedience, or moral worth.
Decision-readiness index with visible causes, not a wellness oracle.

Constitutional hard rules:
  HR1: No biometric inference from VPS data alone
  HR2: No diagnosis from prompt tone
  HR3: Human self-report can override weak behavioural inference
  HR4: Low score reduces machine authority, not human dignity
  HR5: Agent may pause dangerous tools, not control human choices
  HR6: Raw biometrics remain local; derived states only
  HR7: Weakest critical dimension overrides the average

Owner: F13 SOVEREIGN
Schema: /root/WELL/WELL_STATE_SCHEMA.json (v2.0.0)
"""

import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── WEIGHTS ─────────────────────────────────────────────────────────────
WEIGHTS = {"H": 0.40, "M": 0.20, "G": 0.25, "C": 0.15}

# ── SCORE BANDS ─────────────────────────────────────────────────────────
BANDS = [
    (85, 100, "KUKUH", "Suitable for normal and consequential work"),
    (70, 84, "STABLE", "Proceed, but monitor emerging strain"),
    (50, 69, "STRAINED", "Reduce mutation; favour review and consolidation"),
    (30, 49, "DEGRADED", "No irreversible decisions; enter cooling mode"),
    (0, 29, "CRITICAL", "Stop high-risk execution; prioritise recovery"),
]

# ── STATE RANKS (for weakest-dimension override) ────────────────────────
STATE_RANK = {
    "READY": 4,
    "STABLE": 4,
    "COHERENT": 4,
    "LOW_RISK": 4,
    "BELOW_BASELINE": 3,
    "STRAINED": 3,
    "UNCERTAIN": 3,
    "MEDIUM_RISK": 3,
    "DEGRADED": 2,
    "DRIFTING": 2,
    "HIGH_RISK": 2,
    "RECOVERY": 2,
    "CRITICAL": 1,
    "COMPROMISED": 1,
    "HOLD": 1,
    "UNKNOWN": 0,
}

VERDICT_MAP = {
    4: ("PROCEED", "Normal + consequential work allowed"),
    3: ("REDUCE_LOAD", "Proceed, monitor strain"),
    2: ("RECOVER", "No irreversible decisions; consolidate"),
    1: ("HOLD", "Stop high-risk execution; recover"),
    0: ("INSUFFICIENT_DATA", "Do not manufacture a score"),
}


def get_band(score: int) -> tuple:
    """Return (band_name, meaning) for a numeric score."""
    if score is None:
        return "UNKNOWN", "Evidence is insufficient; do not manufacture a score"
    for lo, hi, name, meaning in BANDS:
        if lo <= score <= hi:
            return name, meaning
    return "UNKNOWN", "Score out of range"


def probe_machine() -> dict:
    """M-WELL: Probe VPS health. Returns {score, state, signals}."""
    signals = {}
    score = 100

    # CPU
    try:
        load = float(
            subprocess.check_output(["cat", "/proc/loadavg"], text=True).split()[0]
        )
        cpus = int(subprocess.check_output(["nproc"], text=True))
        cpu_pct = min(100, (load / cpus) * 100)
        signals["cpu_pct"] = round(cpu_pct, 1)
        if cpu_pct > 70:
            score -= 15
        if cpu_pct > 90:
            score -= 20
    except Exception:
        signals["cpu_pct"] = "UNKNOWN"

    # Memory
    try:
        mem = subprocess.check_output(["free"], text=True)
        parts = mem.split("\n")[1].split()
        used, total = int(parts[2]), int(parts[1])
        mem_pct = (used / total) * 100
        signals["memory_pct"] = round(mem_pct, 1)
        if mem_pct > 80:
            score -= 15
        if mem_pct > 95:
            score -= 20
    except Exception:
        signals["memory_pct"] = "UNKNOWN"

    # Disk
    try:
        disk = subprocess.check_output(["df", "/"], text=True).split("\n")[1].split()
        disk_pct = int(disk[4].rstrip("%"))
        signals["disk_pct"] = disk_pct
        if disk_pct > 80:
            score -= 15
        if disk_pct > 95:
            score -= 20
    except Exception:
        signals["disk_pct"] = "UNKNOWN"

    # Organ health
    organs = {
        "arifos": 8088,
        "aforge": 7071,
        "aaa": 3001,
        "geox": 8081,
        "wealth": 18082,
        "well": 18083,
    }
    organs_up = 0
    for name, port in organs.items():
        try:
            r = subprocess.run(
                ["curl", "-sf", f"http://127.0.0.1:{port}/health"],
                capture_output=True,
                timeout=5,
            )
            if r.returncode == 0:
                organs_up += 1
        except Exception:
            pass
    signals["organs_up"] = f"{organs_up}/6"
    if organs_up < 6:
        score -= 10
    if organs_up < 4:
        score -= 20

    score = max(0, min(100, score))

    # Determine state
    if score >= 80:
        state = "STABLE"
    elif score >= 60:
        state = "STRAINED"
    elif score >= 40:
        state = "DEGRADED"
    else:
        state = "CRITICAL"

    return {"score": score, "state": state, "signals": signals}


def probe_governance() -> dict:
    """G-WELL: Check governance integrity. Returns {score, state, signals}."""
    signals = {}
    score = 100

    # Identity drift
    cf = Path("/root/.local/share/arifos/carry_forward.json")
    if cf.exists():
        try:
            data = json.loads(cf.read_text())
            if data.get("identity_drift") == "DRIFT":
                score -= 25
                signals["identity_drift"] = "DRIFT"
            else:
                signals["identity_drift"] = "PASS"
        except Exception:
            signals["identity_drift"] = "UNKNOWN"
    else:
        signals["identity_drift"] = "UNKNOWN"

    # Seal chain integrity
    chain = Path("/root/.local/share/arifos/vault999/seal_chain.jsonl")
    if chain.exists():
        try:
            lines = chain.read_text().strip().split("\n")
            last = json.loads(lines[-1])
            signals["seal_chain"] = f"{len(lines)} entries, seq={last.get('seq', '?')}"
        except Exception:
            signals["seal_chain"] = "ERROR"
            score -= 10
    else:
        signals["seal_chain"] = "MISSING"
        score -= 20

    # Git drift (arifOS)
    try:
        src = subprocess.check_output(
            ["git", "-C", "/root/arifOS", "rev-parse", "--short=7", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        runtime = Path("/opt/arifos/app/.git_commit").read_text().strip()[:7]
        if src != runtime:
            score -= 15
            signals["arifos_drift"] = f"src={src} runtime={runtime}"
        else:
            signals["arifos_drift"] = "ALIGNED"
    except Exception:
        signals["arifos_drift"] = "UNKNOWN"

    score = max(0, min(100, score))

    if score >= 80:
        state = "COHERENT"
    elif score >= 60:
        state = "UNCERTAIN"
    elif score >= 40:
        state = "DRIFTING"
    else:
        state = "COMPROMISED"

    return {"score": score, "state": state, "signals": signals}


def compute_coupling(h_state: str, m_state: str, g_state: str) -> dict:
    """C-WELL: Compute coupling safety from H, M, G states."""
    h_rank = STATE_RANK.get(h_state, 0)
    m_rank = STATE_RANK.get(m_state, 0)
    g_rank = STATE_RANK.get(g_state, 0)

    min_rank = min(h_rank, m_rank, g_rank)

    # Coupling score based on interaction risk
    if min_rank >= 4:
        state = "LOW_RISK"
        score = 90
    elif min_rank >= 3:
        state = "MEDIUM_RISK"
        score = 65
    elif min_rank >= 2:
        state = "HIGH_RISK"
        score = 40
    elif min_rank >= 1:
        state = "HOLD"
        score = 15
    else:
        state = "UNKNOWN"
        score = None

    signals = {
        "h_rank": h_rank,
        "m_rank": m_rank,
        "g_rank": g_rank,
        "min_rank": min_rank,
    }

    return {"score": score, "state": state, "signals": signals}


def compute_vps(
    h_score, m_score, g_score, c_score, h_state, m_state, g_state, c_state
) -> dict:
    """Compute VPS with weakest-dimension override."""

    # If any dimension is UNKNOWN, VPS is UNKNOWN
    if any(s is None for s in [h_score, m_score, g_score, c_score]):
        return {
            "score": None,
            "band": "UNKNOWN",
            "verdict": "INSUFFICIENT_DATA",
            "verdict_meaning": "Do not manufacture a score",
            "dimensions": {
                "human": {"score": h_score, "state": h_state},
                "machine": {"score": m_score, "state": m_state},
                "governance": {"score": g_score, "state": g_state},
                "coupling": {"score": c_score, "state": c_state},
            },
            "primary_cause": "Insufficient evidence — H_WELL is UNKNOWN",
            "evidence_confidence": "Low",
        }

    # Weighted average
    vps = round(
        WEIGHTS["H"] * h_score
        + WEIGHTS["M"] * m_score
        + WEIGHTS["G"] * g_score
        + WEIGHTS["C"] * c_score
    )

    # Weakest-dimension override (HR7)
    h_rank = STATE_RANK.get(h_state, 0)
    m_rank = STATE_RANK.get(m_state, 0)
    g_rank = STATE_RANK.get(g_state, 0)
    c_rank = STATE_RANK.get(c_state, 0)
    min_rank = min(h_rank, m_rank, g_rank, c_rank)

    # Find which dimension is weakest
    weakest = []
    if h_rank == min_rank:
        weakest.append("Human")
    if m_rank == min_rank:
        weakest.append("Machine")
    if g_rank == min_rank:
        weakest.append("Governance")
    if c_rank == min_rank:
        weakest.append("Coupling")

    # Override verdict by weakest dimension
    verdict, verdict_meaning = VERDICT_MAP.get(min_rank, ("UNKNOWN", "No verdict"))

    # Band from VPS score (but verdict from weakest dimension)
    band, band_meaning = get_band(vps)

    # If weakest dimension is worse than band suggests, override
    if min_rank <= 2 and vps >= 70:
        # Override: VPS says STABLE but weakest says RECOVER/HOLD
        band = "STRAINED"  # Force downgrade
        band_meaning = (
            f"Weakest dimension ({', '.join(weakest)}) overrides weighted average"
        )

    # Determine primary cause
    causes = []
    if h_rank <= 2:
        causes.append("Human recovery compromised")
    if m_rank <= 2:
        causes.append("Machine instability")
    if g_rank <= 2:
        causes.append("Governance drift or violation")
    if c_rank <= 2:
        causes.append("Coupling risk elevated")
    primary_cause = "; ".join(causes) if causes else "No critical dimension"

    return {
        "score": vps,
        "band": band,
        "band_meaning": band_meaning,
        "verdict": verdict,
        "verdict_meaning": verdict_meaning,
        "weakest_dimensions": weakest,
        "dimensions": {
            "human": {
                "score": h_score,
                "state": h_state,
                "rank": h_rank,
                "weight": WEIGHTS["H"],
            },
            "machine": {
                "score": m_score,
                "state": m_state,
                "rank": m_rank,
                "weight": WEIGHTS["M"],
            },
            "governance": {
                "score": g_score,
                "state": g_state,
                "rank": g_rank,
                "weight": WEIGHTS["G"],
            },
            "coupling": {
                "score": c_score,
                "state": c_state,
                "rank": c_rank,
                "weight": WEIGHTS["C"],
            },
        },
        "primary_cause": primary_cause,
        "recommended_posture": verdict_meaning,
        "evidence_confidence": "Medium" if h_state == "UNKNOWN" else "High",
    }


def format_morning_brief(vps: dict) -> str:
    """Format VPS for morning brief display."""
    d = vps["dimensions"]
    lines = [
        f"VITALITY PEACE: {vps.get('score', '—')} — {vps['band']}",
        f"  Human:      {d['human'].get('score') or '—'} — {d['human']['state']}",
        f"  Machine:    {d['machine'].get('score') or '—'} — {d['machine']['state']}",
        f"  Governance: {d['governance'].get('score') or '—'} — {d['governance']['state']}",
        f"  Coupling:   {d['coupling'].get('score') or '—'} — {d['coupling']['state']}",
        "",
        f"Verdict: {vps.get('verdict', 'UNKNOWN')}",
        f"Primary cause: {vps.get('primary_cause', 'Insufficient evidence')}",
        f"Recommended posture: {vps.get('recommended_posture') or vps.get('verdict_meaning', 'Wait for evidence')}",
        f"Evidence confidence: {vps.get('evidence_confidence', 'Low')}",
    ]
    return "\n".join(lines)


def main():
    """Compute VPS and output as JSON + formatted brief."""
    # HR1: H = UNKNOWN until real human evidence exists
    # No biometric data available → H is UNKNOWN
    h_score = None
    h_state = "UNKNOWN"

    # M-WELL: Probe machine
    m = probe_machine()
    m_score = m["score"]
    m_state = m["state"]

    # G-WELL: Probe governance
    g = probe_governance()
    g_score = g["score"]
    g_state = g["state"]

    # C-WELL: Compute coupling
    c = compute_coupling(h_state, m_state, g_state)
    c_score = c["score"]
    c_state = c["state"]

    # VPS
    vps = compute_vps(
        h_score, m_score, g_score, c_score, h_state, m_state, g_state, c_state
    )

    # Add raw signals
    vps["machine_signals"] = m["signals"]
    vps["governance_signals"] = g["signals"]
    vps["coupling_signals"] = c["signals"]
    vps["computed_at"] = datetime.now(timezone(timedelta(hours=8))).isoformat()

    # Output
    if "--brief" in sys.argv:
        print(format_morning_brief(vps))
    elif "--json" in sys.argv:
        print(json.dumps(vps, indent=2))
    else:
        print(format_morning_brief(vps))
        print("\n--- JSON ---")
        print(json.dumps(vps, indent=2))


if __name__ == "__main__":
    main()
