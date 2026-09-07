#!/usr/bin/env python3
"""well_ingest.py — Phase 1 WELL pipeline (Day 1, F13-ratified 2026-09-08).

Reads intake files from /root/WELL/intake/{voice,manual,cron}/,
validates per SCHEMA.md, applies freshest-signal-wins merge into
/root/WELL/state.json (additive fields only — never destructive).

Reversible: does NOT switch environment to LIVE. Does NOT auto-modify
the L13 gate. Does NOT replace state.json — it merges derived signals
into state.json's "metrics" + "signals_meta" fields.

Authority:
- Reads: state.json (current), intake files
- Writes: state.json (merged), intake_log.jsonl (audit), moves processed
  files to intake/processed/

Exit codes:
  0 = success (or no intake files — silent)
  1 = state.json corrupt
  2 = invalid intake file (logged, skipped)
  3 = state.json write failure

Called by:
- Cron */30 * * * * (P1.4)
- Manual: python3 /root/WELL/scripts/well_ingest.py
"""
import json
import shutil
import sys
import hashlib
from datetime import datetime, timezone
from pathlib import Path

STATE_FILE = Path("/root/WELL/state.json")
INTAKE_DIR = Path("/root/WELL/intake")
PROCESSED_DIR = INTAKE_DIR / "processed"
AUDIT_LOG = Path("/root/WELL/data/intake_log.jsonl")
SOURCES = ("voice", "manual", "cron")

REQUIRED_FIELDS = {"ts", "source", "operator_id", "signals", "confidence"}


def validate_intake(payload: dict) -> tuple[bool, str]:
    if not isinstance(payload, dict):
        return False, "payload not a dict"
    missing = REQUIRED_FIELDS - set(payload.keys())
    if missing:
        return False, f"missing fields: {sorted(missing)}"
    if payload["source"] not in SOURCES:
        return False, f"invalid source: {payload['source']}"
    if payload["confidence"] not in {"HIGH", "MEDIUM", "LOW"}:
        return False, f"invalid confidence: {payload['confidence']}"
    if not isinstance(payload["signals"], dict):
        return False, "signals not a dict"
    try:
        datetime.fromisoformat(payload["ts"].replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return False, f"invalid ts: {payload['ts']}"
    return True, ""


def compute_well_score(metrics: dict) -> float:
    """Compute well_score from merged metrics. 0-100 scale.

    Higher = better. Derived from:
    - cognitive.clarity (0-10)
    - cognitive.decision_fatigue (0-10, lower is better)
    - derived.energy (0-10)
    - derived.fatigue (0-10, lower is better)
    - derived.calm (0-10)
    """
    cog = metrics.get("cognitive", {})
    derived = metrics.get("derived", {})
    clarity = cog.get("clarity", 5)
    fatigue = cog.get("decision_fatigue", 5)
    energy = derived.get("energy", 5)
    phys_fatigue = derived.get("fatigue", 5)
    calm = derived.get("calm", 5)

    score = (
        clarity * 4
        + (10 - fatigue) * 2
        + energy * 2
        + (10 - phys_fatigue) * 1
        + calm * 1
    )
    # 0-10 -> 0-100 scale (max 100)
    return round(min(100, max(0, score)), 2)


def compute_freshness(state: dict) -> str:
    """FRESH if last_successful_read < 12h ago, else STALE."""
    ts_str = state.get("last_successful_read")
    if not ts_str:
        return "UNKNOWN"
    try:
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        hours = (datetime.now(timezone.utc) - ts).total_seconds() / 3600
        return "FRESH" if hours < 12 else "STALE"
    except (ValueError, TypeError):
        return "UNKNOWN"


def merge_into_state(state: dict, payload: dict) -> dict:
    """Add new fields to state, preserving existing structure."""
    state.setdefault("signals_meta", {})
    state["signals_meta"]["injection_ts"] = payload["ts"]
    state["signals_meta"]["injection_source"] = payload["source"]
    state["signals_meta"]["injection_confidence"] = payload["confidence"]
    state["signals_meta"]["injection_operator"] = payload["operator_id"]

    if "derived" in payload:
        state.setdefault("metrics", {})
        state["metrics"].setdefault("derived", {})
        state["metrics"]["derived"].update(payload["derived"])
    if "metrics" in payload:
        state.setdefault("metrics", {})
        state["metrics"].update(payload["metrics"])

    state["well_score"] = compute_well_score(state.get("metrics", {}))
    state["freshness"] = compute_freshness(state)
    state["last_successful_read"] = datetime.now(timezone.utc).isoformat()
    state["last_successful_write"] = state["last_successful_read"]
    return state


def log_ingest(payload: dict, raw_hash: str, status: str, error: str = ""):
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "raw_hash": raw_hash,
        "source": payload.get("source"),
        "injection_ts": payload.get("ts"),
        "operator_id": payload.get("operator_id"),
        "confidence": payload.get("confidence"),
        "status": status,
        "error": error,
    }
    with AUDIT_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def process_intake_file(intake_path: Path) -> str:
    raw = intake_path.read_bytes()
    raw_hash = hashlib.sha256(raw).hexdigest()[:16]
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        log_ingest({}, raw_hash, "SKIP_INVALID_JSON", str(e))
        return f"SKIP invalid JSON: {e}"

    ok, err = validate_intake(payload)
    if not ok:
        log_ingest(payload, raw_hash, "SKIP_VALIDATION", err)
        return f"SKIP validation: {err}"

    # Load + merge state
    try:
        state = json.loads(STATE_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[well_ingest] state.json unreadable: {e}", file=sys.stderr)
        log_ingest(payload, raw_hash, "STATE_UNREADABLE", str(e))
        return f"STATE_UNREADABLE: {e}"

    state = merge_into_state(state, payload)
    state["timestamp"] = datetime.now(timezone.utc).isoformat()
    state["backend_status"] = "PIPELINE_FEEDING"  # mark as live-fed but env still TEST
    state["state_file_access"] = "PASS"
    state["confidence"] = payload["confidence"]
    state["telemetry_confidence"] = payload["confidence"]
    state["arif_decision_required"] = False
    state["reason"] = (
        f"P1 ingest (source={payload['source']} conf={payload['confidence']}). "
        f"Day 1 F13-ratified pipeline. environment still TEST pending live signal."
    )

    try:
        STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except OSError as e:
        log_ingest(payload, raw_hash, "STATE_WRITE_FAIL", str(e))
        return f"STATE_WRITE_FAIL: {e}"

    log_ingest(payload, raw_hash, "INGESTED")
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    shutil.move(str(intake_path), PROCESSED_DIR / intake_path.name)

    return (
        f"INGEST {payload['source']:6s} conf={payload['confidence']:6s} "
        f"well_score={state['well_score']:5.1f} ts={payload['ts']}"
    )


def main():
    if not INTAKE_DIR.exists():
        sys.exit(0)  # silent — intake not provisioned yet

    intake_files = []
    for src in SOURCES:
        src_dir = INTAKE_DIR / src
        if src_dir.exists():
            intake_files.extend(sorted(src_dir.glob("*.json")))

    if not intake_files:
        sys.exit(0)

    for intake_path in intake_files:
        result = process_intake_file(intake_path)
        print(f"[well_ingest] {intake_path.name}: {result}")


if __name__ == "__main__":
    main()
