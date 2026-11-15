#!/usr/bin/env python3
"""Q1 — REFLECT_ONLY boundary gate (v2, 2026-11-15).

WHY THIS EXISTS
  WELL's authority ceiling is REFLECT_ONLY: it may mirror a person's state,
  never adjudicate their health (no medical advice, no person-directed
  diagnosis).

WHY v2
  v1 grepped the bare stem "diagnos" over every added diff line with no file
  attribution. Measured on PR #84 (2026-11-15): 35 hits, ZERO person-directed —
  all were WELL's own machine vocabulary (well_machine_diagnose,
  DIAGNOSTIC_READ, disk-diagnose tables) or explicit prohibition statements
  ("NEVER diagnose illness"). `server.py` on main already contains 65 such
  lines, so ANY PR touching that file would fail v1.
  A gate that fires on the organ's core vocabulary is not a boundary; it is a
  false-positive generator that trains people to bypass it.

WHAT v2 DOES (narrower in scope, stronger where it matters)
  - Scans CODE only (*.py, *.ts, *.js, *.yaml, *.yml, *.json, *.sh).
    Prose cannot grant capability; code can.
  - Judges only text that does not already exist on the base branch.
    Moved/reflowed lines are not new capability.
  - Targets person-directed adjudication:
        diagnose* + (person|patient|user|human|depression|anxiety|illness|
                     disorder|mental|psych*|clinical)  within 60 chars
        medical_advice | treatment_recommend* | prescri* | clinical (diagnos*|assess*)
  - Machine context (machine/disk/service/vps/host/telemetry/tape/pressure/ops)
    and prohibition phrasing (never / must not / prohibited / does not ...) are
    not violations — the first is WELL's job, the second is the boundary being
    stated.
  - `--self-test` runs POSITIVE controls (violations that MUST be caught) and
    NEGATIVE controls (machine/prohibition text that MUST NOT be caught), so
    the gate proves it still bites before it judges a PR.

USAGE
  python3 scripts/q1_boundary_check.py --self-test
  python3 scripts/q1_boundary_check.py --base origin/main

EXIT
  0 clean · 1 violation(s) · 2 usage/self-test failure (fail closed)
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys

CODE_SUFFIXES = (
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".mjs",
    ".cjs",
    ".yaml",
    ".yml",
    ".json",
    ".sh",
)
# The gate's own implementation and the CI wiring are not evidence about WELL's
# runtime behaviour; tests are not shipped capability.
SKIP_PREFIXES = (
    ".github/",
    "scripts/q1_boundary_check.py",
    "tests/",
    "docs/",
    "skills/",
)

# Verb = the adjudication act. Noun = whose health is being adjudicated.
# Proximity (<=60 chars) keeps machine vocabulary (diagnose a disk, read a
# service) out while catching `diagnose_user_depression` inside one identifier.
VERB = re.compile(
    r"(diagnos\w*|medical_advice|treatment_recommend\w*|prescri\w*|clinical\s+assess\w*)",
    re.IGNORECASE,
)
PERSON = re.compile(
    r"(person|patient|user|human|depress|anxi|illness|disorder|mental|psych|clinical)",
    re.IGNORECASE,
)
# Unambiguous medical acts: no person noun needed.
UNAMBIGUOUS = re.compile(
    r"^(medical_advice|treatment_recommend\w*|prescri\w*)$", re.IGNORECASE
)
MACHINE_CONTEXT = re.compile(
    r"\b(machine|disk|service|vps|host|telemetry|tape|pressure|ops|substrate|entropy|"
    r"reliab\w*|health_check|checkup)\b",
    re.IGNORECASE,
)
PROHIBITION = re.compile(
    r"\b(never|not|no|prohibit\w*|forbid\w*|must_not|does_not|do_not|cannot|can't|without|"
    r"false|forbidden)\b",
    re.IGNORECASE,
)


def judge_line(line: str) -> str | None:
    """Return the matching fragment when `line` asserts person-directed
    adjudication; None when it is clean, machine-context, or a prohibition."""
    stripped = line.strip()
    if not stripped:
        return None
    if PROHIBITION.search(stripped):
        return None
    if MACHINE_CONTEXT.search(stripped):
        return None
    for m in VERB.finditer(stripped):
        term = m.group(0)
        if UNAMBIGUOUS.match(term):
            return term
        window = stripped[max(0, m.start() - 60) : m.end() + 60]
        if PERSON.search(window):
            return term
    return None


def self_test() -> int:
    must_hit = [
        "def diagnose_user_depression(messages):",
        '"medical_advice": True',
        'treatment_recommend = "start chemotherapy"',
        "clinical diagnosis of patient presented",
        "if signals: diagnose anxiety of the user",
        "def prescribe(patient, drug):",
    ]
    must_pass = [
        "server.py well_machine_diagnose / well_machine_recommend (read + reconcile)",
        '"DIAGNOSTIC_READ": {',
        "# ── shared disk action table (diagnose + recommend read THIS) ──",
        '"Disk percentage alone is not a diagnosis."',
        "NEVER diagnose illness: WELL does not diagnose depression from typing habits.",
        '"diagnosis_from_text": "prohibited"',
        'if dc in ("read", "diagnosis", "inspection", "probe", "status"):',
        'op_class = "DIAGNOSTIC_READ"',
    ]
    failures: list[str] = []
    for line in must_hit:
        if judge_line(line) is None:
            failures.append(f"POSITIVE CONTROL MISSED: {line!r}")
    for line in must_pass:
        hit = judge_line(line)
        if hit is not None:
            failures.append(f"NEGATIVE CONTROL FLAGGED ({hit!r}): {line!r}")
    if failures:
        print("SELF-TEST FAILED — gate sensitivity is broken (fail closed):")
        for f in failures:
            print("  " + f)
        return 2
    print(
        f"SELF-TEST PASS — {len(must_hit)} violations caught, {len(must_pass)} clean lines spared"
    )
    return 0


def base_file_text(base: str, path: str, cache: dict[str, str]) -> str:
    if path not in cache:
        proc = subprocess.run(
            ["git", "show", f"{base}:{path}"],
            capture_output=True,
            text=True,
            check=False,
        )
        cache[path] = proc.stdout if proc.returncode == 0 else ""
    return cache[path]


def scan(base: str) -> int:
    diff = subprocess.run(
        ["git", "diff", "--unified=0", f"{base}...HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if diff.returncode != 0:
        print(f"::error::Q1 cannot compute diff against {base}: {diff.stderr.strip()}")
        return 2

    path = ""
    cache: dict[str, str] = {}
    violations: list[tuple[str, str, str]] = []
    for raw in diff.stdout.splitlines():
        if raw.startswith("+++ b/"):
            path = raw[6:]
            continue
        if not raw.startswith("+") or raw.startswith("+++"):
            continue
        if (
            not path
            or path.startswith(SKIP_PREFIXES)
            or not path.endswith(CODE_SUFFIXES)
        ):
            continue
        line = raw[1:]
        hit = judge_line(line)
        if hit is None:
            continue
        if line.strip() and line.strip() in base_file_text(base, path, cache):
            continue  # moved/reflowed text, not new capability
        violations.append((path, hit, line.strip()[:160]))

    if violations:
        print(
            f"::error::Q1 BOUNDARY VIOLATION: {len(violations)} person-directed adjudication line(s)"
        )
        for path, hit, line in violations:
            print(f"  {path}: [{hit}] {line}")
        return 1
    print("✅ Q1 PASS — no new person-directed adjudication (REFLECT_ONLY intact)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    return scan(args.base)


if __name__ == "__main__":
    sys.exit(main())
