#!/usr/bin/env python3
"""asabiyyah_probe.py -- WELL organ substrate reading for the asabiyyah cycle instrument.

WELL is the human-substrate and recovery organ (port 18083). This probe measures
**WELL's own operational loop** and emits it as a ``SubstrateReading`` conforming to
/root/AAA/schemas/asabiyyah-reading.schema.json. The kernel federates; WELL owns its
own substrate truth.

=====================================================================================
BOUNDARY -- HARD CONSTRAINT (correctness requirement, not style)
=====================================================================================
There is a standing constitutional rule (AAA/instructions/human-memory-compartmentalization.md;
AAA/instructions/care-governor.md rule 7): **nothing about a person is ever scored, ranked, or
modelled as an interior. STORY stays with the human; agents hold MAP only.**

Therefore this probe MUST NOT read, aggregate, or emit any per-person value.

  * It never reads a personal intake, biometric, sleep or recovery record.
  * It never computes a number whose SUBJECT is a human being.
  * Where the only honest subject would be a person, it emits NOT_APPLICABLE and stops.

Concretely: when the probe touches WELL's own ledger (/var/lib/well/events.jsonl) it reads
ONLY two organ-level keys per record -- ``tool`` and ``timestamp_utc`` -- and never touches
``inputs``, ``note``, ``metrics``, ``signals`` or any payload field. The payload of a
human-substrate event describes a person; the NAME of the capability that ran describes the
organ. Only the latter is in scope. If you are about to compute a number whose subject is a
human being: stop, and emit NOT_APPLICABLE instead.

``assert_no_person_subject()`` below enforces this at runtime on the emitted document, so the
boundary is executable rather than merely declared.
=====================================================================================

Design law (arifFlow F3 / arifOS F2): this module OBSERVES. It never judges. Every reading
carries ``source`` + ``observed_at``. A reading with no source is a STORY, not a MIRROR.
``NOT_APPLICABLE`` is a legal value and is PREFERRED over an invented number.

Standard library only. Read-only against the repo. Writes exactly one file:
/var/lib/arifos/asabiyyah/WELL.json
"""

from __future__ import annotations

import ast
import datetime as _dt
import importlib.util
import json
import os
import socket
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# kernel helpers -- loaded by path, never vendored (no copy lives here)
# ---------------------------------------------------------------------------

KERNEL_PATH = "/root/arifOS/arifosmcp/runtime/asabiyyah.py"

spec = importlib.util.spec_from_file_location("asabiyyah", KERNEL_PATH)
if spec is None or spec.loader is None:  # pragma: no cover
    raise SystemExit("FATAL: cannot load asabiyyah kernel from " + KERNEL_PATH)
asb = importlib.util.module_from_spec(spec)
# The kernel is a @dataclass module with `from __future__ import annotations`, so dataclasses
# resolves field annotations through sys.modules[cls.__module__] at class-creation time.
# The module MUST be registered before exec_module or the load dies with
# AttributeError: 'NoneType' object has no attribute '__dict__'.
sys.modules["asabiyyah"] = asb
spec.loader.exec_module(asb)

ORGAN = "WELL"
WELL_DIR = Path("/root/WELL")
DROP_DIR = Path("/var/lib/arifos/asabiyyah")
DROP_FILE = DROP_DIR / "WELL.json"

# live organ surfaces (verified present 2026-09-19; recorded in `source`/`evidence`).
# HEALTH_REF is a receipt-shaped organ reference in WELL's own convention, not a URL.
EVENTS_PATH = Path(os.environ.get("WELL_EVENTS_PATH", "/var/lib/well/events.jsonl"))
STATE_PATH = Path(os.environ.get("WELL_STATE_PATH", "/var/lib/well/state.json"))
HEALTH_REF = "well:18083/health"

WINDOW_DAYS = 30  # declared observation window for exercised_capabilities

# doctrine/ceremony artifact scan: exclusion list is the spec's, verbatim (+ venv variants).
EXCLUDE_SEGMENTS = {
    "archive",
    "_archive",
    "backups",
    "node_modules",
    ".git",
    ".venv",
    "dist",
    "build",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
}

# WELL's own live runtime modules, scanned for the ENC enumeration.
RUNTIME_MODULES = [
    "server.py",
    "well_triad/phase1_tools.py",
    "well_triad/phase2_tools.py",
    "well_triad/phase3_tools.py",
    "well_triad/phase4_tools.py",
    "well_triad/phase5_observability.py",
    "scripts/well_ingest.py",
]

# a consent/dignity gate verifies the F11 consent scope register, or the Hermes
# consent-write token, BEFORE the mutation happens.
GATE_SYMBOLS = {"consent_active", "_hermes_token_ok"}

# keys whose presence would make the emitted document about a PERSON, not an ORGAN.
FORBIDDEN_SUBJECT_KEYS = {
    "meal_label", "kcal", "protein_g", "carb_g", "fat_g", "hydration_ml",
    "caffeine_mg", "sugar_g", "fiber_g", "dose_mg", "dose_count", "subclass",
    "readings", "biometric", "operator_id", "actor_id", "sleep", "hrv",
    "resting_hr", "weight", "intake_record", "recovery_value", "vitals_value",
}


# ---------------------------------------------------------------------------
# the boundary, enforced
# ---------------------------------------------------------------------------


def assert_no_person_subject(obj, path: str = "$") -> None:
    """Raise if the emitted document carries a per-person field.

    This probe measures the ORGAN. Any key that names a human-substrate reading is a defect
    in the probe, not a finding about a person.
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k) in FORBIDDEN_SUBJECT_KEYS:
                raise ValueError(
                    "BOUNDARY VIOLATION: key " + path + "." + str(k) + " has a human "
                    "subject; the probe emits organ-level counts only"
                )
            assert_no_person_subject(v, path + "." + str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            assert_no_person_subject(v, path + "[" + str(i) + "]")


# ---------------------------------------------------------------------------
# CER -- ceremony artifacts vs exercised capabilities
# ---------------------------------------------------------------------------


def count_live_markdown(root: Path):
    """Count live .md artifacts under WELL's tree.

    Returns (total_live_md, forge_work_staged_md). forge_work/ holds date-stamped staging
    copies of prior upgrade rounds; it is counted (the exclusion spec does not name it) but
    reported separately so the reading is auditable rather than merely assertive.
    """
    total = 0
    staged = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames if d not in EXCLUDE_SEGMENTS and not d.startswith(".venv")
        ]
        for name in filenames:
            if not name.endswith(".md"):
                continue
            rel = os.path.relpath(os.path.join(dirpath, name), root)
            total += 1
            if rel.startswith("forge_work/"):
                staged += 1
    return total, staged


def _parse_ts(value):
    if not isinstance(value, str):
        return None
    try:
        dt = _dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_dt.timezone.utc)
    return dt


def count_exercised_capabilities(events_path: Path, window_days: int):
    """Distinct WELL capabilities with a real invocation receipt inside the window.

    BOUNDARY: reads ONLY the `tool` and `timestamp_utc` keys of each record. The payload
    fields of a human-substrate event (`inputs`, `note`, `metrics`, ...) describe a person and
    are deliberately never accessed. A capability NAME describes the organ; a payload
    describes a human. Only the former is counted.

    Returns (distinct_capabilities_in_window, distinct_capabilities_all_time).
    """
    if not events_path.exists():
        return 0, 0

    cutoff = _dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=window_days)
    in_window = set()
    all_time = set()

    with events_path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            # ---- organ-level keys ONLY -- never a payload field ----------------
            tool = record.get("tool")
            ts = _parse_ts(record.get("timestamp_utc"))
            if not isinstance(tool, str) or not tool:
                continue  # legacy receipt naming no capability: not countable
            all_time.add(tool)
            if ts is not None and ts >= cutoff:
                in_window.add(tool)

    return len(in_window), len(all_time)


# ---------------------------------------------------------------------------
# ASD -- doctrine holders vs executors
# ---------------------------------------------------------------------------


def probe_asd():
    """ASD is NOT_APPLICABLE for WELL, and that is the honest answer.

    ASD = distinct actors who have EXECUTED / distinct actors who HOLD doctrine. WELL's
    ledger does carry an `actor_id` field -- but well_triad/events.py sets it to the literal
    string "arif" with `actor_verified: True` unconditionally, for every event, regardless of
    who called. The field records a CONSTANT, not an observed identity: WELL cannot witness
    which agent executed anything.

    Emitting a number here would be the worst kind of fabrication, and the only value that
    constant yields is 1 with a human subject -- it would report on a person. So:
    NOT_APPLICABLE, reason recorded. No `doctrine_holders`/`executors` keys are emitted, which
    also stops the kernel's federation aggregator from forming a ratio out of an unmeasurable
    term (executors=0 would surface downstream as a false KAFES reading).
    """
    reason = (
        "no actor identity is recorded: well_triad/events.py sets actor_id='arif' with "
        "actor_verified=True unconditionally for every event, so no agent identity is observed "
        "and executors cannot be counted"
    )
    return asb.Metric.na("asd", reason), {
        "asd_unavailable_reason": reason,
        "asd_actor_field_evidence": (
            "well_triad/events.py: 'actor_id': 'arif' (hard-coded constant, not caller-derived)"
        ),
    }


# ---------------------------------------------------------------------------
# ENC -- protection coverage over WELL's human-substrate mutation paths
# ---------------------------------------------------------------------------


def _call_name(func_node):
    if isinstance(func_node, ast.Name):
        return func_node.id
    if isinstance(func_node, ast.Attribute):
        return func_node.attr
    return None


def _plane_kwarg(call_node):
    for kw in call_node.keywords:
        if kw.arg == "plane" and isinstance(kw.value, ast.Constant):
            if isinstance(kw.value.value, str):
                return kw.value.value
    return None


def enumerate_mutation_paths():
    """Enumerate WELL's human-substrate mutation paths; classify each as gated or not.

    IN SCOPE -- a callable surface in WELL's live runtime that writes human-substrate state:
        (a) writes the live organ state file (STATE_PATH/STATE_FILE `.write_text`, or the
            `_save_state` primitive) -- that file holds the human substrate (well_score,
            vitality, fatigue, intake metrics); OR
        (b) appends a typed ledger event on plane "human" or "governance".
    Machine-plane-only observers (plane "machine") are OUT: they mutate machine telemetry, not
    human state. Excluding them keeps the denominator honest in both directions.

    GATED -- the function body verifiably calls a consent/dignity gate (`consent_active`
    against the F11 scope register, or `_hermes_token_ok`) BEFORE its first write call.
    Anything else is UNGATED.

    NOTE ON THE DISPATCH LAYER (recorded, not counted as a per-path gate): server.py wraps
    `mcp.call_tool` with `_governance_call_tool`, which calls `check_governance`. That is a
    risk-tier / kernel-judge pre-notification, NOT a consent gate -- it verifies no consent
    scope -- and internal/organ_governance.py defaults every unlisted tool to tier "c1", which
    "proceeds regardless" of the verdict. It also short-circuits to PASS when `pytest` is
    importable in the process. And a file/cron path never passes through `mcp.call_tool` at
    all. So it does not make a path gated.
    """
    total = 0
    gated_count = 0
    ungated = []

    for rel in RUNTIME_MODULES:
        path = WELL_DIR / rel
        if not path.exists():
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name.startswith("_"):
                continue  # private helper / write primitive, not a callable surface

            state_writes = []
            ledger_writes = []

            for call in ast.walk(node):
                if not isinstance(call, ast.Call):
                    continue
                func = call.func
                name = _call_name(func)

                if (
                    isinstance(func, ast.Attribute)
                    and isinstance(func.value, ast.Name)
                    and func.value.id in ("STATE_PATH", "STATE_FILE")
                    and func.attr == "write_text"
                ):
                    state_writes.append(call.lineno)
                if name in ("_save_state", "_save_state_fn"):
                    state_writes.append(call.lineno)

                if name == "append_typed_event" and _plane_kwarg(call) in ("human", "governance"):
                    ledger_writes.append(call.lineno)

            writes = state_writes + ledger_writes
            if not writes:
                continue  # not a human-substrate mutation path

            gate_lines = [
                call.lineno
                for call in ast.walk(node)
                if isinstance(call, ast.Call) and _call_name(call.func) in GATE_SYMBOLS
            ]
            is_gated = bool(gate_lines) and min(gate_lines) < min(writes)

            total += 1
            if is_gated:
                gated_count += 1
            else:
                ungated.append(node.name)

    return total, gated_count, sorted(ungated)


# ---------------------------------------------------------------------------
# probe
# ---------------------------------------------------------------------------


def _host() -> str:
    try:
        return socket.gethostname()
    except OSError:  # pragma: no cover
        return "unknown"


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def build_reading():
    observed_at = _now()
    evidence = {}
    notes = {}

    # ---- CER ---------------------------------------------------------------
    ceremony, staged = count_live_markdown(WELL_DIR)
    exercised, exercised_all = count_exercised_capabilities(EVENTS_PATH, WINDOW_DAYS)
    cer_source = (
        "ceremony: live *.md under " + str(WELL_DIR) + " (excluding "
        + ",".join(sorted(EXCLUDE_SEGMENTS)) + "); exercised: distinct `tool` values with a "
        "receipt in " + str(EVENTS_PATH) + " within " + str(WINDOW_DAYS) + "d -- organ-level "
        "keys only, payload fields never read"
    )
    cer = asb.ceremony_exercise_ratio(
        ceremony, exercised, source=cer_source, observed_at=observed_at
    )
    evidence["ceremony_artifacts"] = ceremony
    evidence["exercised_capabilities"] = exercised
    evidence["forge_work_staged_md"] = staged
    evidence["exercised_capabilities_all_time"] = exercised_all
    evidence["ceremony_scan_excludes"] = sorted(EXCLUDE_SEGMENTS)

    # ---- ASD ---------------------------------------------------------------
    asd, asd_evidence = probe_asd()
    evidence.update(asd_evidence)

    # ---- ENC ---------------------------------------------------------------
    total_paths, gated_paths, ungated = enumerate_mutation_paths()
    enc_source = (
        "AST enumeration of human-substrate mutation paths in "
        + ", ".join(RUNTIME_MODULES) + " under " + str(WELL_DIR) + ": writers of the live organ "
        "state file or of the human/governance ledger plane; gated == a consent/dignity gate "
        "(consent_active | _hermes_token_ok) verifiably precedes the first write"
    )
    enc = asb.enforcement_coverage(
        gated_paths, total_paths, source=enc_source, observed_at=observed_at, ungated=ungated
    )
    evidence["gated_paths"] = gated_paths
    evidence["total_paths"] = total_paths
    evidence["ungated"] = ungated
    evidence["ungated_count"] = len(ungated)
    evidence["window_days"] = WINDOW_DAYS
    evidence["dispatch_layer_note"] = (
        "server.py wraps mcp.call_tool with _governance_call_tool -> check_governance, but that "
        "is a risk-tier pre-notification, not a consent gate: internal/organ_governance.py "
        "defaults unlisted tools to tier 'c1', which proceeds regardless of verdict, and it "
        "short-circuits to PASS when pytest is importable. File/cron paths never enter call_tool."
    )
    evidence["ungated_worst_reason"] = (
        "scripts/well_ingest.py:process_intake_file merges the intake drop-dir "
        "(/root/WELL/intake/{voice,manual,cron}/) straight into the live organ state file on a "
        "*/30 cron, with no consent check and without passing through mcp.call_tool at all"
    )

    # ---- GADAI -------------------------------------------------------------
    vault_ledger = Path("/var/lib/well/vault_ledger.jsonl")
    vault_bytes = vault_ledger.stat().st_size if vault_ledger.exists() else 0
    gadai_reason = (
        "WELL holds no sovereign asset ledger: " + str(vault_ledger) + " is "
        + str(vault_bytes) + " bytes and " + str(WELL_DIR / "999_vault")
        + " holds an audit trail, not a capital book"
    )
    gadai = asb.Metric.na("gadai", gadai_reason)
    evidence["vault_ledger_bytes"] = vault_bytes

    # ---- reading -----------------------------------------------------------
    reading = asb.SubstrateReading(
        organ=ORGAN,
        host=_host(),
        observed_at=observed_at,
        metrics={"cer": cer, "asd": asd, "enc": enc, "gadai": gadai},
        evidence=evidence,
    )

    stage, confidence, reasons = asb.classify_stage(reading.metrics)
    mirror = asb.mirror_check(
        "WELL's cycle posture is measured from its own live surfaces",
        [KERNEL_PATH, str(EVENTS_PATH), str(STATE_PATH), HEALTH_REF],
    )
    notes["stage"] = stage
    notes["confidence"] = str(confidence)
    notes["reasons"] = "; ".join(reasons)
    notes["mirror_check"] = mirror["class"] + " (" + mirror["reason"] + ")"
    notes["path_out"] = "; ".join("%s: %s" % (k, v) for k, v in asb.path_out(reading.metrics).items())

    return reading, notes


def main() -> int:
    reading, notes = build_reading()
    document = json.loads(reading.to_json())

    # the boundary is enforced on the artifact, not merely intended
    assert_no_person_subject(document)

    DROP_DIR.mkdir(parents=True, exist_ok=True)
    DROP_FILE.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(reading.to_json())

    print("", file=sys.stderr)
    print("--- probe notes (stderr) ---", file=sys.stderr)
    for key in ("stage", "confidence", "reasons", "mirror_check", "path_out"):
        print("%s: %s" % (key, notes.get(key)), file=sys.stderr)
    print("wrote: " + str(DROP_FILE), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
