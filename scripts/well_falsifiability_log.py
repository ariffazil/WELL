#!/usr/bin/env python3
"""
WELL Falsifiability Log (#19)
══════════════════════════════

Append-only JSONL log of every vitality gate verdict against subsequent
outcomes. The goal: enough entries to ask whether gate verdicts predict
anything. If gate says RECOVER and the next 30 deploys succeed, RECOVER
might mean something. If RECOVER is followed by 50/50 split of success
and failure, RECOVER is ritual.

This is upgrade plan item #19 — the only item that can falsify the gate.

Usage:
    python3 scripts/well_falsifiability_log.py append \
        --gate-verdict RECOVER \
        --weakest-substrate M_WELL \
        --context "swap cleanup attempt"

    python3 scripts/well_falsifiability_log.py outcome \
        --ref <ref_id> \
        --outcome "deploy_succeeded" \
        --notes "..."

    python3 scripts/well_falsifiability_log.py report

Each entry:
    {
        "ts": ISO-8601,
        "kind": "verdict" | "outcome" | "ref",
        "actor_id": "kimi-code/FI-008",
        "ref": <12-char hex>,
        "data": {...}
    }

Log path: /root/VAULT999/well/falsifiability.jsonl
Append-only. 30 entries minimum for any falsifiability claim.

Background: see docs/FINDINGS-2026-08-19-state-leakage-and-witness-need.md
DITEMPA BUKAN DIBERI ⚒️
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path("/root/VAULT999/well/falsifiability.jsonl")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dir() -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def append_verdict(args) -> None:
    _ensure_dir()
    ref = uuid.uuid4().hex[:12]
    entry = {
        "ts": _now(),
        "kind": "verdict",
        "actor_id": args.actor_id,
        "ref": ref,
        "data": {
            "gate_verdict": args.gate_verdict,
            "weakest_substrate": args.weakest_substrate,
            "context": args.context,
        },
    }
    with LOG_PATH.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"verdict logged: ref={ref} verdict={args.gate_verdict}")


def append_outcome(args) -> None:
    if not LOG_PATH.exists():
        print(f"error: log file {LOG_PATH} does not exist", file=sys.stderr)
        sys.exit(1)
    entry = {
        "ts": _now(),
        "kind": "outcome",
        "actor_id": args.actor_id,
        "ref": args.ref,
        "data": {
            "outcome": args.outcome,
            "notes": args.notes,
        },
    }
    with LOG_PATH.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"outcome logged: ref={args.ref} outcome={args.outcome}")


def report(args) -> None:
    if not LOG_PATH.exists():
        print(f"no log file at {LOG_PATH}")
        return
    verdicts: list[dict] = []
    outcomes: dict[str, dict] = {}
    with LOG_PATH.open() as f:
        for line in f:
            if not line.strip():
                continue
            entry = json.loads(line)
            if entry["kind"] == "verdict":
                verdicts.append(entry)
            elif entry["kind"] == "outcome":
                outcomes[entry["ref"]] = entry
    if not verdicts:
        print("no verdicts logged yet")
        return
    matched = sum(1 for v in verdicts if v["ref"] in outcomes)
    unmatched = len(verdicts) - matched
    print(f"verdicts: {len(verdicts)}, matched outcomes: {matched}, unmatched: {unmatched}")
    if matched < 5:
        print("insufficient data for falsifiability analysis; need >=5 matched pairs")
        return
    by_verdict: dict[str, list[str]] = {}
    for v in verdicts:
        if v["ref"] not in outcomes:
            continue
        verdict = v["data"]["gate_verdict"]
        outcome = outcomes[v["ref"]]["data"]["outcome"]
        by_verdict.setdefault(verdict, []).append(outcome)
    for verdict, outs in sorted(by_verdict.items()):
        success = sum(1 for o in outs if "success" in o.lower() or "passed" in o.lower())
        total = len(outs)
        print(f"  {verdict}: {success}/{total} successful outcomes")


def main() -> None:
    parser = argparse.ArgumentParser(description="WELL falsifiability log (#19)")
    parser.add_argument(
        "action",
        choices=["append", "outcome", "report"],
        help="append verdict, append outcome, or generate report",
    )
    parser.add_argument("--actor-id", default="kimi-code/FI-008", help="actor id")
    # append
    parser.add_argument("--gate-verdict", help="verdict string (PROCEED/RECOVER/HOLD/...)")
    parser.add_argument("--weakest-substrate", help="weakest substrate (H_WELL/M_WELL/G_WELL/C_WELL)")
    parser.add_argument("--context", help="free-text context")
    # outcome
    parser.add_argument("--ref", help="verdict ref to attach outcome to")
    parser.add_argument("--outcome", help="outcome string (deploy_succeeded/session_scrapped/...)")
    parser.add_argument("--notes", help="free-text notes")
    args = parser.parse_args()
    if args.action == "append":
        if not args.gate_verdict:
            print("error: --gate-verdict required for append", file=sys.stderr)
            sys.exit(1)
        append_verdict(args)
    elif args.action == "outcome":
        if not args.ref or not args.outcome:
            print("error: --ref and --outcome required for outcome", file=sys.stderr)
            sys.exit(1)
        append_outcome(args)
    elif args.action == "report":
        report(args)


if __name__ == "__main__":
    main()
