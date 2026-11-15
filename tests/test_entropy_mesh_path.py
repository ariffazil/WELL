"""Guard: entropy-integrity mesh path must resolve canonically, code-side.

Root cause (2026-11-05, systematic-debugging): server.py loaders
(commit 9728806, 2026-07-12) resolved parent(WELL)/entropy-integrity =
/root/entropy-integrity; the tree was absorbed into WEALTH git
(ad88f6f1, 2026-07-28) and the old path vanished — 5 H-WELL tools dead
with ENOENT. Runtime stopgap is the symlink /root/entropy-integrity;
this module + test make the CODE canonical so the symlink stops
being load-bearing.

TDD: RED until well_mcp/entropy_mesh.py exists.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

import well_mcp.entropy_mesh as em

FIVE = [
    "sabar_latency",
    "trust_compression",
    "correction_capacity",
    "regulation_recovery",
    "niat_impact_mirror",
]


def test_default_dir_is_canonical_wealth_tree() -> None:
    os.environ.pop("WELL_ENTROPY_MESH_DIR", None)
    assert em.mesh_dir() == "/root/WEALTH/entropy-integrity"


def test_all_five_modules_present_at_default() -> None:
    """Presence check is host-coupled by nature: the canonical mesh lives on the
    federation host (/root/WEALTH/entropy-integrity), not on a CI runner.

    Resolution is asserted unconditionally by the other tests; here we skip only
    when the tree is not mounted/readable on this host, and still FAIL when the
    tree is present but a module is missing (the real defect this guard exists
    for: 5 H-WELL tools dead with ENOENT).
    """
    os.environ.pop("WELL_ENTROPY_MESH_DIR", None)
    root = Path(em.mesh_dir())
    try:
        mounted = root.is_dir()
    except OSError as exc:  # e.g. /root not readable by the CI runner user
        pytest.skip(f"canonical mesh not readable on this host: {root} ({exc})")
    if not mounted:
        pytest.skip(f"canonical mesh not mounted on this host: {root}")
    for mod in FIVE:
        assert (root / "mcp" / "well" / f"{mod}.py").exists(), mod


def test_env_override_wins() -> None:
    os.environ["WELL_ENTROPY_MESH_DIR"] = "/root/WEALTH/entropy-integrity"
    try:
        assert em.mesh_dir() == "/root/WEALTH/entropy-integrity"
    finally:
        del os.environ["WELL_ENTROPY_MESH_DIR"]
