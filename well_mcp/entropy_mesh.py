"""Canonical resolver for the Entropy Integrity Mesh tree.

Root cause (2026-11-05, systematic-debugging): server.py loaders
(commit 9728806, 2026-07-12) resolved the mesh relative to parent(WELL)
= /root/entropy-integrity. The tree was absorbed into WEALTH git
(ad88f6f1, 2026-07-28) at /root/WEALTH/entropy-integrity and the old
path vanished — 5 H-WELL tools died with ENOENT (sabar_latency,
trust_compression, correction_capacity, regulation_recovery,
niat_impact_mirror). Runtime stopgap: symlink /root/entropy-integrity
-> /root/WEALTH/entropy-integrity (see tools_sot.yaml audit_2026_11_05).
This module makes the CODE canonical so the symlink stops being
load-bearing after the next well.service restart.

Authority: WELL REFLECT_ONLY — read-only path resolution, no mutation.
"""

from __future__ import annotations

import os

DEFAULT_MESH_DIR = "/root/WEALTH/entropy-integrity"
ENV_OVERRIDE = "WELL_ENTROPY_MESH_DIR"


def mesh_dir() -> str:
    """Return the canonical entropy-integrity mesh directory.

    Order: WELL_ENTROPY_MESH_DIR env override, else the canonical
    WEALTH tree. Pure function of the environment — no I/O.
    """
    return os.environ.get(ENV_OVERRIDE, DEFAULT_MESH_DIR)
