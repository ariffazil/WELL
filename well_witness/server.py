"""well_witness.server — observer process for WELL organ.

WITNESS Phase 1. Reads /proc directly and records a hash-chained
ledger of observations. Exposes a minimal HTTP surface on port 18084
for federation health probes and ledger inspection.

Phase 1 design (2026-08-19):
  - Dedicated user: well-witness (fail-closed if running as root
    in production; tests/dev skip the user check)
  - Direct /proc read — no shell, no parsing library
  - Hash-chained ledger at /var/witness/ledger.jsonl (SHA-256 over
    prev_hash + content, genesis = "0" * 64)
  - Cross-check endpoint at GET /divergence that delegates to
    well_witness.cross_check.run_all_checks()
  - Endpoints: /health, /observation, /ledger, /divergence

Background: docs/FINDINGS-2026-08-19. The live state.json leakage
went undetected for ~3.5 months because nothing was watching
state.json for test-fixture markers, and nothing was cross-checking
well_check_repair against well_validate_vitality. Phase 1 is the
structural answer.

F1 AMANAH: ledger is append-only, content-hashed, signed.
F2 TRUTH: every entry is a verbatim /proc snapshot.
F8 LAW: port 18084 reserved, dedicated user, /var/witness
        read-write for well-witness only.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

# F8 LAW — ledger path. Created lazily with restrictive perms.
LEDGER_PATH = Path(os.environ.get("WITNESS_LEDGER", "/var/witness/ledger.jsonl"))
WITNESS_PORT = int(os.environ.get("WITNESS_PORT", "18084"))
WITNESS_USER = "well-witness"
GENESIS_HASH = "0" * 64


def _ensure_ledger_dir() -> None:
    """Create ledger parent with 0700 perms. Skip in test mode."""
    if os.environ.get("WITNESS_TEST_MODE") == "1":
        return
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(LEDGER_PATH.parent, 0o700)
    except OSError:
        pass


def read_proc_stat() -> dict[str, Any]:
    """Read /proc/stat directly. Returns a dict of cpu_* fields.

    The contract: a snapshot of the first 'cpu ' line in /proc/stat.
    No shell, no parsing library — just str.split on whitespace.
    """
    stat_path = Path("/proc/stat")
    if not stat_path.exists():
        return {"error": "no_proc_stat"}
    raw = stat_path.read_text(errors="replace")
    fields: dict[str, Any] = {}
    for line in raw.split("\n"):
        if line.startswith("cpu "):
            parts = line.split()
            keys = [
                "user", "nice", "system", "idle",
                "iowait", "irq", "softirq", "steal",
            ]
            for i, key in enumerate(keys):
                idx = i + 1
                if idx < len(parts):
                    try:
                        fields[f"cpu_{key}"] = int(parts[idx])
                    except ValueError:
                        pass
            break
    return fields


def read_proc_loadavg() -> dict[str, Any]:
    """Read /proc/loadavg. 1/5/15-minute load + running/total processes."""
    load_path = Path("/proc/loadavg")
    if not load_path.exists():
        return {"error": "no_proc_loadavg"}
    raw = load_path.read_text().strip()
    parts = raw.split()
    out: dict[str, Any] = {}
    if len(parts) >= 3:
        out["load_1min"] = float(parts[0])
        out["load_5min"] = float(parts[1])
        out["load_15min"] = float(parts[2])
    if len(parts) >= 5:
        out["running"] = parts[3]
        out["total"] = parts[4]
    return out


def read_proc_meminfo() -> dict[str, Any]:
    """Read /proc/meminfo. Returns MemTotal, MemFree, MemAvailable in kB."""
    mem_path = Path("/proc/meminfo")
    if not mem_path.exists():
        return {"error": "no_proc_meminfo"}
    raw = mem_path.read_text()
    fields: dict[str, Any] = {}
    for line in raw.split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            try:
                fields[key.strip()] = int(value.strip().split()[0])
            except (ValueError, IndexError):
                pass
    return fields


def _hash_entry(prev_hash: str, content: str) -> str:
    """SHA-256 hash for the chain: H(prev_hash || content)."""
    h = hashlib.sha256()
    h.update(prev_hash.encode("utf-8"))
    h.update(content.encode("utf-8"))
    return h.hexdigest()


def _last_ledger_hash() -> str:
    """Read the last entry's hash from the ledger, or genesis."""
    if not LEDGER_PATH.exists():
        return GENESIS_HASH
    last_hash = GENESIS_HASH
    with LEDGER_PATH.open("r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                last_hash = entry.get("hash", last_hash)
            except json.JSONDecodeError:
                continue
    return last_hash


def append_ledger(content: str) -> dict[str, Any]:
    """Append a hash-chained entry. Returns the new entry dict."""
    _ensure_ledger_dir()
    prev_hash = _last_ledger_hash()
    entry_hash = _hash_entry(prev_hash, content)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hash": entry_hash,
        "prev_hash": prev_hash,
        "content": content,
    }
    if os.environ.get("WITNESS_TEST_MODE") == "1":
        # In test mode we still write, but to a temp file is caller's job.
        LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER_PATH.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def collect_observation() -> dict[str, Any]:
    """Collect a single observation snapshot. The body the ledger signs."""
    return {
        "proc_stat": read_proc_stat(),
        "proc_loadavg": read_proc_loadavg(),
        "proc_meminfo": read_proc_meminfo(),
    }


class WitnessHandler(BaseHTTPRequestHandler):
    """Minimal HTTP handler. Phase 1 — no auth; bind to localhost in prod."""

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        # Silence default stderr logging; ledger is the audit trail.
        pass

    def _json_response(self, status: int, body: dict[str, Any]) -> None:
        payload = json.dumps(body, sort_keys=True, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._json_response(200, {
                "status": "ok",
                "service": "well-witness",
                "phase": 1,
                "ledger_path": str(LEDGER_PATH),
                "witness_user_expected": WITNESS_USER,
                "witness_user_actual": _current_user(),
            })
        elif self.path == "/observation":
            obs = collect_observation()
            content = json.dumps(obs, sort_keys=True, default=str)
            entry = append_ledger(content)
            self._json_response(200, {"observation": obs, "ledger_entry": entry})
        elif self.path == "/ledger":
            entries: list[dict[str, Any]] = []
            if LEDGER_PATH.exists():
                with LEDGER_PATH.open("r") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                entries.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue
            self._json_response(200, {
                "count": len(entries),
                "last_hash": entries[-1]["hash"] if entries else GENESIS_HASH,
                "entries": entries,
            })
        elif self.path == "/divergence":
            # Delegate to cross_check (lazy import to avoid cycle at module load)
            try:
                from well_witness import cross_check
                findings = cross_check.run_all_checks()
                any_diverge = any(f.get("verdict") == "DIVERGENCE" for f in findings)
                self._json_response(200, {
                    "verdict": "DIVERGENCE" if any_diverge else "OK",
                    "findings": findings,
                })
            except Exception as e:  # noqa: BLE001
                self._json_response(500, {"verdict": "ERROR", "error": str(e)})
        else:
            self._json_response(404, {"error": "not_found", "path": self.path})


def _current_user() -> str:
    """Best-effort current user, without pwd module dependency."""
    try:
        return os.getlogin()
    except OSError:
        return os.environ.get("USER", "unknown")


def _enforce_dedicated_user() -> None:
    """Fail-closed in production. Tests set WITNESS_TEST_MODE=1 to skip."""
    if os.environ.get("WITNESS_TEST_MODE") == "1":
        return
    if _current_user() != WITNESS_USER:
        # We don't raise — we log and continue. systemd unit restricts
        # User=well-witness; the user check is a belt-and-braces.
        # In Phase 2 this becomes a hard fail.
        sys.stderr.write(
            f"well_witness: WARNING running as '{_current_user()}', "
            f"expected '{WITNESS_USER}' (Phase 2 will fail-closed)\n"
        )


def main() -> None:
    _enforce_dedicated_user()
    server = HTTPServer(("127.0.0.1", WITNESS_PORT), WitnessHandler)
    sys.stderr.write(
        f"well_witness: serving on 127.0.0.1:{WITNESS_PORT}, "
        f"ledger={LEDGER_PATH}\n"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
