"""Shared pytest isolation for WELL's mutable state files."""

from __future__ import annotations

from pathlib import Path
import sys

WELL_ROOT = Path(__file__).resolve().parents[1]
if str(WELL_ROOT) not in sys.path:
    sys.path.insert(0, str(WELL_ROOT))

import pytest
import server


@pytest.fixture(autouse=True)
def isolate_server_state_paths(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Snapshot production inputs, then keep each test's writes in tmp_path."""
    state_path = tmp_path / "well-state.json"
    events_path = tmp_path / "well-events.jsonl"
    vault_path = tmp_path / "well-vault_ledger.jsonl"
    production_state_path = WELL_ROOT / "state.json"
    production_events_path = WELL_ROOT / "events.jsonl"
    production_vault_path = WELL_ROOT / "vault_ledger.jsonl"

    if production_state_path.exists():
        state_path.write_bytes(production_state_path.read_bytes())
    if production_events_path.exists():
        events_path.write_bytes(production_events_path.read_bytes())
    if production_vault_path.exists():
        vault_path.write_bytes(production_vault_path.read_bytes())

    monkeypatch.setattr(server, "STATE_PATH", state_path)
    monkeypatch.setattr(server, "EVENTS_PATH", events_path)
    monkeypatch.setattr(server, "VAULT_LEDGER_PATH", vault_path)
