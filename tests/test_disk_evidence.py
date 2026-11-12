"""Disk evidence: bounded scan, reconciliation guard, shared action table."""

import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import disk_evidence as de  # noqa: E402

GB = de.GB


def _ev(paths, used_gb=337, timed_out=(), age_h=0, docker_reclaim=0, backups=()):
    return {
        "schema": de.SCHEMA,
        "measured_at": (datetime.now(timezone.utc) - timedelta(hours=age_h)).isoformat(),
        "status": "partial" if timed_out else "complete",
        "timed_out_paths": list(timed_out),
        "filesystem": {"used_bytes": used_gb * GB, "inodes_used_pct": 11.0},
        "top_level_file_bytes": 0,
        "paths": [
            {"path": p, "status": "partial" if p in timed_out else "complete",
             "confirmed_bytes": int(g * GB), "children": ch}
            for p, g, ch in paths
        ],
        "deleted_open": {"bytes": 0},
        "docker": {"status": "ok", "types": {
            "Images": {"reclaimable_bytes": docker_reclaim},
            "Build Cache": {"reclaimable_bytes": 0},
            "Containers": {"reclaimable_bytes": 0},
            "Local Volumes": {"reclaimable_bytes": int(0.26 * GB)},
        }},
        "journal": {"bytes": int(1.3 * GB)},
        "backups_same_disk": list(backups),
    }


def test_unexplained_space_means_low_confidence_and_no_root_cause():
    # The 2026-11-12 failure: scan saw /var 39 GB of 337 GB, /root timed out.
    ev = _ev([("/var", 39, [{"path": "/var/lib/docker", "bytes": 10 * GB}])],
             timed_out=["/root"])
    r = de.reconcile(ev)
    assert r["confidence"] == "low"
    assert r["root_cause"] is None
    assert "/root" in r["timed_out_paths"]
    assert "39.0 GB of 337.0 GB" in r["message"]


def test_reconciled_scan_names_root_cause():
    ev = _ev([("/root", 210, [{"path": "/root/backups", "bytes": 27 * GB}]),
              ("/usr", 70, []), ("/var", 39, []), ("/home", 16, [])])
    r = de.reconcile(ev)
    assert r["confidence"] == "high"
    assert r["root_cause"].startswith("/root holds 210.0 GB")


def test_stale_evidence_is_low_confidence():
    ev = _ev([("/root", 330, [])], age_h=10)
    r = de.reconcile(ev)
    assert r["confidence"] == "low" and r["root_cause"] is None
    assert "evidence stale" in r["low_confidence_reasons"]


def test_no_evidence_never_claims_cause():
    r = de.reconcile(None)
    assert r["status"] == "no_evidence" and r["root_cause"] is None


def test_docker_prune_scored_by_measured_reclaimable():
    acts = {a["recommendation_id"]: a for a in de.disk_actions(_ev([("/root", 330, [])]))}
    assert acts["disk.docker.prune_images"]["expected_recovery_gb"] == 0.0
    assert acts["disk.docker.prune_images"]["worth_it"] is False
    assert acts["disk.docker.prune_volumes"]["risk"] == "HIGH"


def test_same_disk_backup_warns_move_offsite_first():
    ev = _ev([("/root", 330, [])], backups=[
        {"path": "/root/backups/restic-repo", "bytes": 24 * GB, "kind": "restic",
         "same_filesystem_as_root": True}])
    acts = de.disk_actions(ev)
    top = acts[0]
    assert top["recommendation_id"] == "disk.backup.move_offsite"
    assert top["requires_approval"] and "off-server" in top["warning"]
    assert top["expected_recovery_gb"] == 24.0


def test_every_action_has_contract_fields():
    for a in de.disk_actions(_ev([("/root", 330, [])])):
        for k in ("recommendation_id", "risk", "reversible", "requires_approval"):
            assert k in a, (a, k)


def test_forced_partial_scan_keeps_partial_result(monkeypatch):
    def fake_run(cmd, **kw):
        raise subprocess.TimeoutExpired(
            cmd, kw.get("timeout"),
            output=f"{3 * GB}\t/x/a\n{2 * GB}\t/x/b\n{5 * GB}\t/x/a/deep\n".encode())
    monkeypatch.setattr(de.subprocess, "run", fake_run)
    r = de.scan_path("/x", timeout_s=0.01)
    assert r["status"] == "partial"
    assert r["bytes"] is None
    assert r["confirmed_bytes"] == 5 * GB  # depth-1 only: /x/a + /x/b


def test_real_bounded_scan_on_tmpdir(tmp_path):
    (tmp_path / "d").mkdir()
    (tmp_path / "d" / "f").write_bytes(b"x" * 4096)
    r = de.scan_path(str(tmp_path), timeout_s=30)
    assert r["status"] == "complete" and r["bytes"] >= 4096


def test_inodes_reported():
    fs = de.fs_usage("/")
    assert fs["inodes_used_pct"] is not None and fs["used_bytes"] > 0
