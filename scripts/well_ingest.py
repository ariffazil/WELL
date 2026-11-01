#!/usr/bin/env python3
"""well_ingest.py — Phase 1 WELL pipeline (Day 1, F13-ratified 2026-09-08).

Reads intake files from /root/WELL/intake/{voice,manual,cron}/,
validates per SCHEMA.md, applies freshest-signal-wins merge into the
LIVE organ state at /var/lib/well/state.json (additive fields only —
never destructive). Repointed from the repo-dir fixture file to the
live organ state by F13 directive 2026-09-12 — the kernel L13 gate and
the organ both read/write this file.

Merge targets the live organ path; environment stays PROD after a
successful merge (a TEST label here stranded honest ingests in quarantine).
into state.json's "metrics" + "signals_meta" fields.

Honesty contract (F13 order 2026-09-29, trace_id HRFID-20260929):
- D2  test_contamination is computed FROM THE RECORD. A contaminated record is kept
      as evidence and may not touch derived.*, metrics.*, metabolic_flux or well_score.
- D3  compute_well_score never substitutes a default for a missing input; absent
      inputs produce None (= INSUFFICIENT_DATA), not a plausible-looking number.
- D4  every human-plane field written carries `producer` + `source_class`, and an
      AGENT_INFERRED / INJECTED_DEFAULT value may not be written into a field whose
      name claims to be the operator's self-report.

Authority:
- Reads: live organ state.json (current), intake files
- Writes: live organ state.json (merged), intake_log.jsonl (audit), moves
  processed files to intake/processed/

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
import os
import shutil
import sys
import hashlib
import fcntl
import re
import contextlib
from datetime import datetime, timezone
from pathlib import Path

STATE_FILE = Path(os.environ.get("WELL_STATE_PATH", "/var/lib/well/state.json"))


@contextlib.contextmanager
def state_lock():
    """Shared exclusive lock with well_auto_keepalive (both run at the same */30
    tick, both are read-modify-write on STATE_FILE; the split decoy path used to
    hide the collision — 2026-09-29 reconciliation)."""
    fh = open(str(STATE_FILE) + ".lock", "w")
    fcntl.flock(fh, fcntl.LOCK_EX)
    try:
        yield
    finally:
        fcntl.flock(fh, fcntl.LOCK_UN)
        fh.close()

INTAKE_DIR = Path("/root/WELL/intake")
PROCESSED_DIR = INTAKE_DIR / "processed"
AUDIT_LOG = Path("/root/WELL/data/intake_log.jsonl")
SOURCES = ("voice", "manual", "cron", "verbal")

REQUIRED_FIELDS = {"ts", "source", "operator_id", "signals", "confidence"}

# ── Provenance contract (D4, HRFID-20260929) ─────────────────────────────────
SOURCE_CLASSES = {"SELF_REPORT", "SENSOR", "AGENT_INFERRED", "EXTERNAL", "INJECTED_DEFAULT"}
DEFAULTABLE_CLASSES = {"AGENT_INFERRED", "INJECTED_DEFAULT"}

# The organ id is always `cron:well_ingest`; these name the upstream producer whose
# words/measurements the record is carrying, so a reader can tell who spoke.
INGEST_PRODUCER = "cron:well_ingest"
PRODUCER_BY_SOURCE = {
    "verbal": "hermes:verbal-intake",
    "voice": "hermes:voice-intake",
    "manual": "operator:biometric_inject",
    "cron": "cron:well_synth",
}
# What the lane's own words/features are made of. Numbers DERIVED from those words
# are always an inference by the classifier (see DERIVED_SOURCE_CLASS), never a report.
LANE_SOURCE_CLASS = {
    "verbal": "SELF_REPORT",
    "voice": "SENSOR",
    "manual": "SELF_REPORT",
    "cron": "AGENT_INFERRED",
}
DERIVED_SOURCE_CLASS = "AGENT_INFERRED"

# Field names that claim to be the operator's own report about their own state —
# same set WELL already guards (server._HUMAN_DATUM_FIELDS).
SELF_REPORT_FIELDS = ("delta_s", "peace2", "kappa_r", "rasa", "amanah")

# A test string must not become a governance verdict about a human. Standalone tokens
# only, so "latest"/"protest"/"container" cannot trip it.
_TEST_MARKER_RE = re.compile(r"(?<![\w./-])(test|probe|ping|canary|AUTO-OK)(?![\w-])", re.IGNORECASE)
_PROBE_NAME_RE = re.compile(r"(test|probe|ping|canary|auto-ok|synthetic|mock|fixture)", re.IGNORECASE)

AGENT_TEST_RECORD = "AGENT_TEST_RECORD"


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


# ── D2 — contamination is read off the record, not off a flag someone set ─────
def _record_text_slots(payload: dict) -> list[tuple[str, str]]:
    """Every free-text slot a record carries, as (field_path, text)."""
    slots: list[tuple[str, str]] = []
    signals = payload.get("signals") if isinstance(payload.get("signals"), dict) else {}
    for key in ("quote", "text", "body", "utterance", "transcript"):
        for holder, label in ((signals, "signals"), (payload, "")):
            value = holder.get(key)
            if isinstance(value, str) and value.strip():
                slots.append((f"{label}.{key}" if label else key, value))
    for key in ("tokens", "categories"):
        value = signals.get(key)
        if isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, str) and item.strip():
                    slots.append((f"signals.{key}[{i}]", item))
    return slots


def _channel_receipt(payload: dict) -> str | None:
    """A receipt tying the record to a message actually delivered on a named channel.

    The verbal lane stamps channel + capture + the hash of the Telegram message it
    read; that is traceable to the human. A LOW-confidence record with nothing like
    this cannot be traced to anyone at all.
    """
    provenance = payload.get("provenance") if isinstance(payload.get("provenance"), dict) else {}
    explicit = (
        provenance.get("receipt_id")
        or provenance.get("message_id")
        or provenance.get("update_id")
    )
    if explicit:
        return str(explicit)
    channel = provenance.get("channel") or payload.get("channel")
    capture = provenance.get("capture") or provenance.get("capture_mode")
    if channel and capture and payload.get("raw_hash"):
        return f"{channel}:{payload['raw_hash']}"
    return None


def detect_test_contamination(payload: dict) -> tuple[bool, list[str]]:
    """Return (contaminated, reasons) for one intake record.

    Contaminated when the record's own text carries a test marker, or a source /
    capture field names a probe, or it claims LOW confidence with no channel receipt
    that could trace it back to the human. Reasons are kept so the quarantine is
    auditable — a bare YES is the same Boolean collapse this federation forbids.
    """
    reasons: list[str] = []
    for path, text in _record_text_slots(payload):
        found = _TEST_MARKER_RE.search(text)
        if found:
            reasons.append(f"test_marker:{path}:{found.group(0)!r} in {text[:60]!r}")

    provenance = payload.get("provenance") if isinstance(payload.get("provenance"), dict) else {}
    for key in ("source", "capture", "capture_mode", "channel"):
        value = payload.get("source") if key == "source" else provenance.get(key)
        if isinstance(value, str) and _PROBE_NAME_RE.search(value):
            reasons.append(f"probe_named_field:{key}={value!r}")

    if str(payload.get("confidence", "")).upper() == "LOW" and not _channel_receipt(payload):
        reasons.append("low_confidence_without_channel_receipt")

    return bool(reasons), reasons


# ── D4 — producer + source_class on everything human-plane ───────────────────
def _stamp_provenance(
    state: dict, field_path: str, producer: str, source_class: str
) -> None:
    """Record who wrote a field and what kind of evidence it is.

    Lives inside the `signals_meta` block the schema already carries — WELL does not
    need a second ledger to say where a number came from.
    """
    if source_class not in SOURCE_CLASSES:
        source_class = "EXTERNAL"
    entry = state.setdefault("signals_meta", {}).setdefault("field_provenance", {}).setdefault(
        field_path, {}
    )
    entry["producer"] = producer
    entry["source_class"] = source_class
    entry["stamped_at"] = datetime.now(timezone.utc).isoformat()


def _is_self_report_field(field_path: str) -> bool:
    """Does this field's NAME claim to be the operator reporting on themselves?"""
    segments = field_path.split(".")
    leaf = segments[-1]
    if leaf in SELF_REPORT_FIELDS or "self_report" in leaf.lower():
        return True
    return any(segment in SELF_REPORT_FIELDS for segment in segments)


def _merge_guarded(
    state: dict,
    container: dict,
    incoming: dict,
    prefix: str,
    producer: str,
    source_class: str,
    skipped: list[str],
) -> None:
    """Merge values into `container`, refusing an inferred or injected default into a
    self-report-named field (D4). Skipped paths are collected for the audit log."""
    for key, value in (incoming or {}).items():
        path = f"{prefix}.{key}" if prefix else key
        if source_class in DEFAULTABLE_CLASSES and _is_self_report_field(path):
            skipped.append(path)
            continue
        if isinstance(value, dict):
            # one level deeper (e.g. metrics.cognitive.*) — merge, never clobber
            node = container.get(key)
            if not isinstance(node, dict):
                node = {}
                container[key] = node
            _merge_guarded(state, node, value, path, producer, source_class, skipped)
            continue
        container[key] = value
        _stamp_provenance(state, path, producer, source_class)


# ── D3 — absent inputs stay absent ───────────────────────────────────────────
SCORE_INPUTS = (
    ("cognitive.clarity", ("cognitive", "clarity")),
    ("cognitive.decision_fatigue", ("cognitive", "decision_fatigue")),
    ("derived.energy", ("derived", "energy")),
    ("derived.fatigue", ("derived", "fatigue")),
    ("derived.calm", ("derived", "calm")),
)


def compute_well_score(metrics: dict) -> float | None:
    """Compute well_score from merged metrics. 0-100 scale, or None.

    Higher = better. Derived from:
    - cognitive.clarity (0-10)
    - cognitive.decision_fatigue (0-10, lower is better)
    - derived.energy (0-10)
    - derived.fatigue (0-10, lower is better)
    - derived.calm (0-10)

    D3 (HRFID-20260929): every input must have a real producer. The old shape
    defaulted `calm` to 5 (and every other input too), so a state with no calm
    reading still printed 63.6 — a mid-range number that read as "Arif is okay" and
    fed a governance verdict. Absent inputs now return None: the organ says
    INSUFFICIENT_DATA out loud instead of inventing a human.
    """
    metrics = metrics if isinstance(metrics, dict) else {}
    values: list[float] = []
    for label, (block, field) in SCORE_INPUTS:
        node = metrics.get(block) if isinstance(metrics.get(block), dict) else {}
        raw = node.get(field)
        if raw is None:
            return None  # absent, not zero, not five, not a guess
        try:
            value = float(raw)
        except (TypeError, ValueError):
            return None
        if not 0.0 <= value <= 10.0:
            return None  # out-of-range cannot be scored honestly either
        values.append(value)

    clarity, decision_fatigue, energy, phys_fatigue, calm = values
    score = (
        clarity * 4
        + (10 - decision_fatigue) * 2
        + energy * 2
        + (10 - phys_fatigue) * 1
        + calm * 1
    )
    # 0-10 -> 0-100 scale (max 100)
    return round(min(100, max(0, score)), 2)


# Configured freshness thresholds — the same arithmetic the health endpoint advertises
# (server.WELL_MAX_FRESH_AGE_SECONDS / WELL_STALE_AFTER_SECONDS). An ingest lane that
# keeps its own 12h "FRESH" window is how the organ ends up with two answers.
MAX_FRESH_AGE_SECONDS = 3600
STALE_AFTER_SECONDS = 14400


def compute_freshness(state: dict) -> str:
    """FRESH / STALE / EXPIRED from the age of the last real observation.

    Measured against `last_successful_read` (the observation clock), never against a
    keepalive or file-write tick: presence is not measurement (D1, HRFID-20260929).
    """
    ts_str = state.get("last_successful_read")
    if not ts_str:
        return "UNKNOWN"
    try:
        ts = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - ts).total_seconds()
    except (ValueError, TypeError):
        return "UNKNOWN"
    if age < 0:
        return "EXPIRED"  # clock skew is not evidence of freshness
    if age <= MAX_FRESH_AGE_SECONDS:
        return "FRESH"
    if age <= STALE_AFTER_SECONDS:
        return "STALE"
    return "EXPIRED"


def merge_into_state(state: dict, payload: dict) -> dict:
    """Add new fields to state, preserving existing structure.

    A test-contaminated record (D2) is retained as evidence and changes nothing about
    the human's numbers: no derived.*, no metrics.*, no well_score recomputation, and
    the observation clock is NOT advanced — a test string cannot make a stale reading
    look newly measured.
    """
    contaminated, contamination_reasons = detect_test_contamination(payload)
    lane = payload.get("source")
    producer = PRODUCER_BY_SOURCE.get(lane, INGEST_PRODUCER)
    lane_class = LANE_SOURCE_CLASS.get(lane, "EXTERNAL")

    state.setdefault("signals_meta", {})
    if contaminated:
        state["test_contamination"] = "YES"
        state["contamination_quarantined"] = True
        state["contamination_reasons"] = contamination_reasons
        # Retained as evidence of what happened, not as a reading of the human.
        state["signals_meta"]["quarantined_injection"] = {
            "ts": payload["ts"],
            "source": lane,
            "producer": producer,
            "source_class": DERIVED_SOURCE_CLASS,
            "confidence": payload["confidence"],
            "reasons": contamination_reasons,
            "excluded_from": ["metrics.derived", "metrics.cognitive", "metabolic_flux", "well_score"],
        }
        state["signals_meta"]["injection_confidence"] = payload["confidence"]
        state["signals_meta"]["injection_operator"] = payload["operator_id"]
        # Observation clock deliberately left where it was; freshness is recomputed
        # against it below, so the stale reading stays stale.
        state["well_score"] = state.get("well_score")
        state["last_successful_write"] = datetime.now(timezone.utc).isoformat()
        state["freshness"] = compute_freshness(state)
        return state

    state["test_contamination"] = "NO"
    state["signals_meta"]["injection_ts"] = payload["ts"]
    state["signals_meta"]["injection_source"] = lane
    state["signals_meta"]["injection_confidence"] = payload["confidence"]
    state["signals_meta"]["injection_operator"] = payload["operator_id"]

    skipped: list[str] = []
    if "derived" in payload:
        state.setdefault("metrics", {})
        node = state["metrics"].setdefault("derived", {})
        # Numbers derived from words are an inference, whatever the lane that supplied
        # the words — stamp them as such (D4).
        _merge_guarded(state, node, payload["derived"], "metrics.derived", producer,
                       DERIVED_SOURCE_CLASS, skipped)
    if "metrics" in payload:
        state.setdefault("metrics", {})
        _merge_guarded(state, state["metrics"], payload["metrics"], "metrics", producer,
                       lane_class, skipped)
    if skipped:
        state["signals_meta"]["provenance_refusals"] = skipped
    _stamp_provenance(state, "signals_meta.injection_confidence", INGEST_PRODUCER, lane_class)

    state["well_score"] = compute_well_score(state.get("metrics", {}))
    # Stamp read/write time FIRST, then compute freshness against it — the old order
    # measured freshness against the previous ingest, so the first live drop after a
    # long stale window was written as STALE even while fresh data merged (2026-09-29).
    state["last_successful_read"] = datetime.now(timezone.utc).isoformat()
    state["last_successful_write"] = state["last_successful_read"]
    state["freshness"] = compute_freshness(state)
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

    contaminated, contamination_reasons = detect_test_contamination(payload)
    producer = PRODUCER_BY_SOURCE.get(payload.get("source"), INGEST_PRODUCER)
    lane_class = LANE_SOURCE_CLASS.get(payload.get("source"), "EXTERNAL")
    state = merge_into_state(state, payload)
    state["timestamp"] = datetime.now(timezone.utc).isoformat()
    state["backend_status"] = "PIPELINE_FEEDING"  # mark as live-fed but env still TEST
    state["state_file_access"] = "PASS"

    if contaminated:
        # D2 — an agent-authored test string is not the sovereign speaking. Keep the
        # evidence, downgrade its class, and let the organ say it does not know.
        state["truth_status"] = "INSUFFICIENT_DATA"
        state["source_type"] = AGENT_TEST_RECORD
        state["evidence_class"] = AGENT_TEST_RECORD
        state["honesty_banner"] = (
            "AGENT TEST RECORD — a test/probe string was captured, not the sovereign's "
            "own state. Excluded from derived signals, metabolic flux and well_score. "
            "Sovereign state is INSUFFICIENT_DATA until a real report arrives."
        )
        state["arif_decision_required"] = False
        state["reason"] = (
            f"P1 ingest quarantined (source={payload['source']} "
            f"conf={payload['confidence']}). Contamination: {'; '.join(contamination_reasons)}. "
            f"No human-plane value written."
        )
        state["confidence"] = "INSUFFICIENT_DATA"
        state["telemetry_confidence"] = "INSUFFICIENT_DATA"
        _stamp_provenance(state, "truth_status", INGEST_PRODUCER, DERIVED_SOURCE_CLASS)
        _stamp_provenance(state, "evidence_class", producer, "EXTERNAL")
        try:
            STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
        except OSError as e:
            log_ingest(payload, raw_hash, "STATE_WRITE_FAIL", str(e))
            return f"STATE_WRITE_FAIL: {e}"
        log_ingest(payload, raw_hash, "QUARANTINED_TEST", "; ".join(contamination_reasons))
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        shutil.move(str(intake_path), PROCESSED_DIR / intake_path.name)
        score = state.get("well_score")
        return (
            f"QUARANTINE {payload['source']:6s} conf={payload['confidence']:6s} "
            f"evidence={AGENT_TEST_RECORD} well_score={'None' if score is None else f'{score:5.1f}'} "
            f"ts={payload['ts']}"
        )

    # Truth provenance per source — the honesty banner must name how reality entered.
    # Added 2026-09-29 (verbal lane, F13 "aku malas nak inject apa2 kat terminal").
    truth_map = {
        "verbal": "OPERATOR_VERBAL",
        "voice": "VOICE_TELEMETRY",
        "manual": "OPERATOR_REPORTED",
        "cron": "DERIVED_FROM_LOGS",
    }
    banner_map = {
        "verbal": "VERBAL — sovereign's own words, event-captured from Telegram DM. Words are signals about experience, not access to it (ε_qualia > 0). Not wearable telemetry.",
        "voice": "VOICE — prosody telemetry from voice lane.",
        "manual": "SELF-REPORT — sovereign inject, not wearable telemetry",
        "cron": "DERIVED — synthesized from logs, not sovereign-stated.",
    }
    src = payload["source"]
    state["truth_status"] = truth_map.get(src, "OPERATOR_REPORTED")
    state["environment"] = "PROD"  # FIX 2026-11-01: live-organ merge is production state
    state["source_type"] = state["truth_status"]
    state["evidence_class"] = (payload.get("provenance") or {}).get(
        "evidence_class", "SOVEREIGN_SELF_REPORT"
    )
    state["honesty_banner"] = banner_map.get(src, "UNKNOWN SOURCE — treat as UNVERIFIED")
    # Sleep-word retention: the morning mirror's sleep lane needs a data source.
    # No wearable exists (Fit bridge retired 2026-09-29), so the sovereign's own
    # sleep words are the only honest signal — keep last report with polarity,
    # never fabricate hours. (F13 consent grant 2026-09-29, biometric.full)
    sleep_cats = [c for c in (payload.get("signals") or {}).get("categories", [])
                  if c in ("sleep_pos", "sleep_neg")]
    if sleep_cats:
        state.setdefault("signals_meta", {})
        state["signals_meta"]["last_sleep_report"] = {
            "ts": payload["ts"],
            "polarity": "ok" if sleep_cats == ["sleep_pos"] else "deficit",
            "categories": sleep_cats,
            "source": src,
            "confidence": payload["confidence"],
            "class": "VERBAL_QUALITATIVE — reported word, not measured hours",
            "producer": producer,
            "source_class": lane_class,
        }
    state["confidence"] = payload["confidence"]
    state["telemetry_confidence"] = payload["confidence"]
    state["arif_decision_required"] = False
    state["reason"] = (
        f"P1 ingest (source={payload['source']} conf={payload['confidence']}). "
        f"F13-ratified pipeline; merged into live organ state "
        f"(var/lib/well) per F13 repoint 2026-09-12."
    )
    # D4 — the write itself is attributed.
    state["producer"] = INGEST_PRODUCER
    state["last_ingest"] = {
        "ts": payload["ts"],
        "source": src,
        "producer": producer,
        "source_class": lane_class,
        "confidence": payload["confidence"],
        "raw_hash": raw_hash,
    }
    _stamp_provenance(state, "truth_status", INGEST_PRODUCER, lane_class)
    _stamp_provenance(state, "confidence", INGEST_PRODUCER, lane_class)
    _stamp_provenance(state, "evidence_class", producer, lane_class)

    try:
        STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except OSError as e:
        log_ingest(payload, raw_hash, "STATE_WRITE_FAIL", str(e))
        return f"STATE_WRITE_FAIL: {e}"

    log_ingest(payload, raw_hash, "INGESTED")
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    shutil.move(str(intake_path), PROCESSED_DIR / intake_path.name)

    score = state.get("well_score")
    return (
        f"INGEST {payload['source']:6s} conf={payload['confidence']:6s} "
        f"well_score={'None' if score is None else f'{score:5.1f}'} ts={payload['ts']}"
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
        # HEARTBEAT (2026-09-16): this path used to exit with no output, which made the job
        # unwitnessable — a */30 cron that writes nothing on an empty queue is indistinguishable
        # from a cron that has been dead for days, and /var/log/well/intake.log had been quiet
        # for 11.6h with nothing able to say whether that was idleness or death. One line per
        # tick costs ~4KB/day and buys the only property the old shape could not have: the job
        # can FAIL to appear.
        print(json.dumps({
            "tool": "well_ingest", "ts": datetime.now(timezone.utc).isoformat(),
            "status": "NO_INTAKE", "state_path": str(STATE_FILE), "state_written": False,
            "note": "intake queue empty — heartbeat; live state timestamp NOT advanced",
        }))
        sys.exit(0)

    for intake_path in intake_files:
        with state_lock():
            result = process_intake_file(intake_path)
        print(f"[well_ingest] {intake_path.name}: {result}")


if __name__ == "__main__":
    main()
