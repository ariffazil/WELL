"""
F6 MARUAH instrument — v0 (modular target ONLY)
═══════════════════════════════════════════════════════════════════
Floor F6 (MARUAH) is the last unmeasured kernel floor (12/13 measured).
This module is the WELL-side instrument v0: an HONEST coverage-first
measurement. It returns null-unless-covered and NEVER invents a dignity
score (F9 ANTI-HANTU; WELL AGENTS.md Freshness Law: stale >24h is
STALE_MIRROR, never extrapolated).

Cutting-over discipline (H1_MONOLITH_CUTOVER.md + WELL-A4-FIX 2026-08-08):
  - Modular target ONLY. Production canonical surface (:18083, server.py)
    does NOT expose this tool until cutover green (OS-1 / P1-5).
  - Aggregators must NOT route this before cutover — the A4 scar
    (byte-identical replies from a duplicated stub) is the reason stubs
    raise loudly. This module is a NEW capability, not a duplicate; keep
    it un-routed until parity.

Kernel wiring: floor producer -> this instrument is the arifOS-side
follow-up (pending OS-1). Envelope is designed kernel-consumable.

Authority: REFLECT_ONLY · Sovereign: Muhammad Arif bin Fazil (F13)
DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

WELL_STATE_PATH_DEFAULT = "/var/lib/well/state.json"
INTAKE_LOG_DEFAULT = "/var/log/well/intake.log"
STATE_MAX_AGE_S = 4 * 3600  # WELL freshness band: stale after 4h
INTAKE_MAX_AGE_S = 24 * 3600  # Freshness Law ceiling: >24h = STALE_MIRROR
INSTRUMENT_VERSION = "v0"

_INSTRUMENT_NOTE = (
    "v0-partial: coverage-first instrument. f6_index is null unless all "
    "evidence classes are covered; when covered it is a conservative partial "
    "signal, not a dignity score. Kernel floor-producer wiring pending OS-1."
)


def _read_state(state_path: Optional[str]) -> dict:
    p = Path(state_path or os.environ.get("WELL_STATE_PATH", WELL_STATE_PATH_DEFAULT))
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}


def _last_intake_age_s(
    log_path: Optional[str], now: Optional[float]
) -> Optional[float]:
    """Age (seconds) of the newest structured receipt in the intake log.

    Returns None when the log is unreadable or contains no parseable ts
    (honest None — never a fabricated age).
    """
    p = Path(log_path or INTAKE_LOG_DEFAULT)
    try:
        lines = p.read_text(errors="replace").strip().splitlines()
    except Exception:
        return None
    now = now if now is not None else time.time()
    for line in reversed(lines):
        try:
            ts = json.loads(line).get("ts")
            if not ts:
                continue
            dt = datetime.fromisoformat(str(ts))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return max(0.0, now - dt.timestamp())
        except Exception:
            continue
    return None


def _canonical_dignity_surface(server_py: Optional[str]) -> bool:
    """Positive-evidence check: the canonical surface still owns the
    dignity guard (Ω-WELL-12). Static structural check, no HTTP."""
    p = Path(server_py or Path(__file__).resolve().parents[2] / "server.py")
    try:
        return "well_guard_dignity" in p.read_text(errors="replace")
    except Exception:
        return False


async def well_measure_floor_f6(
    ctx: Any = None,
    state_path: Optional[str] = None,
    intake_log: Optional[str] = None,
    server_py: Optional[str] = None,
    now: Optional[float] = None,
) -> dict:
    """F6 MARUAH floor instrument v0 — coverage-first, null-unless-covered.

    Evidence classes (all must be covered for a non-null index):
      1. human_substrate  — live WELL state carries a sovereign-truth status
                            (OPERATOR_VERBAL / OPERATOR_REPORTED), fresh
                            (<= STATE_MAX_AGE_S), uncontaminated.
      2. consequence_flow — intake pipeline produced a receipt within the
                            Freshness-Law ceiling (<= INTAKE_MAX_AGE_S).
      3. dignity_surface  — canonical dignity guard (Ω-WELL-12) present on
                            the production surface (static structural check).

    REFLECT_ONLY: this reflects evidence coverage; it never commands and
    never fabricates. null is the correct answer when coverage is short.
    """
    now = now if now is not None else time.time()
    state = _read_state(state_path)
    age_s: Optional[float] = None
    ts = state.get("timestamp")
    if ts:
        try:
            dt = datetime.fromisoformat(str(ts))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            age_s = max(0.0, now - dt.timestamp())
        except Exception:
            age_s = None

    truth = str(state.get("truth_status", "")).upper()
    # "NO" (string) is truthy — parse contamination semantically, never bool() it
    _contam_raw = str(state.get("test_contamination", "")).strip().upper()
    contaminated = (
        _contam_raw in {"YES", "TRUE", "1", "QUARANTINED", "TEST"}
        or state.get("environment", "").upper() == "TEST"
    )

    # 1. human_substrate
    substrate_ok = (
        truth in {"OPERATOR_VERBAL", "OPERATOR_REPORTED"}
        and not contaminated
        and age_s is not None
        and age_s <= STATE_MAX_AGE_S
    )
    # 2. consequence_flow
    intake_age = _last_intake_age_s(intake_log, now)
    flow_ok = intake_age is not None and intake_age <= INTAKE_MAX_AGE_S
    # 3. dignity_surface
    surface_ok = _canonical_dignity_surface(server_py)

    coverage = {
        "human_substrate": {
            "covered": substrate_ok,
            "truth_status": truth or None,
            "state_age_s": None if age_s is None else round(age_s, 1),
            "contaminated": contaminated,
        },
        "consequence_flow": {
            "covered": flow_ok,
            "last_receipt_age_s": None if intake_age is None else round(intake_age, 1),
        },
        "dignity_surface": {
            "covered": surface_ok,
            "guard": "Ω-WELL-12 well_guard_dignity (canonical server.py)",
        },
    }

    null_reasons = []
    if not substrate_ok:
        null_reasons.append(
            f"human_substrate: truth={truth or 'NONE'} "
            f"age={'UNKNOWN' if age_s is None else f'{age_s:.0f}s'} "
            f"contaminated={contaminated}"
        )
    if not flow_ok:
        null_reasons.append(
            "consequence_flow: no intake receipt within 24h "
            f"(last={'NONE' if intake_age is None else f'{intake_age:.0f}s'})"
        )
    if not surface_ok:
        null_reasons.append("dignity_surface: canonical guard not found in server.py")

    covered_all = substrate_ok and flow_ok and surface_ok
    if not covered_all:
        f6_index: Optional[float] = None
        verdict = "INSTRUMENTED_COVERAGE_INSUFFICIENT"
    else:
        flow_factor = max(0.0, 1.0 - (intake_age or 0.0) / INTAKE_MAX_AGE_S)
        f6_index = round(0.5 + 0.5 * flow_factor, 3)
        verdict = "MEASURED_V0_PARTIAL"

    return {
        "floor": "F6",
        "name": "MARUAH",
        "instrument": "well_measure_floor_f6",
        "version": INSTRUMENT_VERSION,
        "authority": "REFLECT_ONLY",
        "f6_index": f6_index,
        "verdict": verdict,
        "null_reasons": null_reasons,
        "coverage": coverage,
        "instrument_note": _INSTRUMENT_NOTE,
        "kernel_wiring": "pending OS-1 (arifOS lane floor producer)",
        "cutover": "modular target only; :18083 does not serve this until H1 parity",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
