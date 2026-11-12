"""WELL disk evidence — bounded scan, reconciliation, shared disk action table.

Stdlib only. Used by:
  * scripts/disk_evidence_scan.py  (hourly, nice/ionice, writes DISK_EVIDENCE_PATH)
  * server.py well_machine_diagnose / well_machine_recommend (read + reconcile)

Rules (2026-11-12, Arif "go WELL 000-999"):
  * "large" != "freeable". Two separate rankings.
  * If the scan does not account for >= 80% of df-used, or any path timed out,
    or the evidence is stale: confidence=low and NO root cause is named.
  * Docker/containerd directory size is never freeable by itself; only
    `docker system df` RECLAIMABLE counts.
  * A backup repository on the same filesystem as its source = warning:
    move off-server before any deletion.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from datetime import datetime, timezone
from typing import Any

SCHEMA = "well-disk-evidence/v1"
DISK_EVIDENCE_PATH = os.environ.get(
    "WELL_DISK_EVIDENCE_PATH", "/var/lib/well/disk_evidence.json"
)
GB = 1024**3
UNACCOUNTED_LIMIT = 0.20  # >20% of df-used unexplained -> low confidence
STALE_AFTER_S = 3 * 3600  # hourly job; 3h old evidence is stale
MIN_CHILD_BYTES = 1 * GB  # children below this are not recorded
SKIP_TOP = {"proc", "sys", "dev", "run"}
CONTAINER_RUNTIME_PATHS = ("/var/lib/docker", "/var/lib/containerd")
BACKUP_NAME = re.compile(r"(backup|restic|borg|snapshot)", re.I)
ARCHIVE_NAME = re.compile(r"(^|[/_.-])(archive|_archive|quarantine|_quarantine)", re.I)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── collection ───────────────────────────────────────────────────────────────


def fs_usage(mount: str = "/") -> dict[str, Any]:
    st = os.statvfs(mount)
    total = st.f_blocks * st.f_frsize
    used = (st.f_blocks - st.f_bfree) * st.f_frsize
    avail = st.f_bavail * st.f_frsize
    inodes_used = st.f_files - st.f_ffree
    return {
        "mount": mount,
        "total_bytes": total,
        "used_bytes": used,
        "avail_bytes": avail,
        "used_pct": round(used / total * 100, 1) if total else None,
        "inodes_total": st.f_files,
        "inodes_used": inodes_used,
        "inodes_used_pct": round(inodes_used / st.f_files * 100, 1) if st.f_files else None,
        "source": "statvfs",
    }


def _parse_du(text: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for line in (text or "").splitlines():
        parts = line.split("\t", 1)
        if len(parts) == 2 and parts[0].isdigit():
            out[parts[1]] = int(parts[0])
    return out


def scan_path(path: str, timeout_s: float, depth: int = 2) -> dict[str, Any]:
    """du one top-level path with a hard time budget. Partial output is kept."""
    cmd = ["du", "-xb", f"--max-depth={depth}", path]
    if shutil.which("stdbuf"):
        cmd = ["stdbuf", "-oL", *cmd]
    t0 = time.monotonic()
    status = "complete"
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout_s, check=False
        )
        text = proc.stdout
    except subprocess.TimeoutExpired as exc:
        status = "partial"
        raw = exc.stdout or b""
        text = raw.decode(errors="replace") if isinstance(raw, bytes) else raw
    sizes = _parse_du(text)
    total = sizes.get(path) if status == "complete" else None
    children = sorted(
        (
            {"path": p, "bytes": b}
            for p, b in sizes.items()
            if p != path and b >= MIN_CHILD_BYTES
        ),
        key=lambda c: c["bytes"],
        reverse=True,
    )
    # For a partial scan only depth-1 confirmed children may be summed.
    confirmed = (
        total
        if total is not None
        else sum(b for p, b in sizes.items() if p.count("/") == path.rstrip("/").count("/") + 1)
    )
    return {
        "path": path,
        "status": status,
        "bytes": total,
        "confirmed_bytes": confirmed,
        "elapsed_seconds": round(time.monotonic() - t0, 1),
        "children": children[:25],
        "source": "du -xb",
    }


def top_level_targets(root: str = "/") -> tuple[list[str], int]:
    """Same-filesystem top-level dirs, plus bytes of top-level regular files."""
    root_dev = os.stat(root).st_dev
    dirs, file_bytes = [], 0
    for name in sorted(os.listdir(root)):
        if name in SKIP_TOP:
            continue
        p = os.path.join(root, name)
        try:
            st = os.lstat(p)
        except OSError:
            continue
        if st.st_dev != root_dev:
            continue
        if os.path.isdir(p) and not os.path.islink(p):
            dirs.append(p)
        elif os.path.isfile(p) and not os.path.islink(p):
            file_bytes += st.st_blocks * 512
    return dirs, file_bytes


_SIZE_RE = re.compile(r"([\d.]+)\s*([kKMGT]?B)")
_UNIT = {"B": 1, "kB": 1e3, "KB": 1e3, "MB": 1e6, "GB": 1e9, "TB": 1e12}


def _size_to_bytes(s: str) -> int | None:
    m = _SIZE_RE.search(s or "")
    if not m:
        return None
    return int(float(m.group(1)) * _UNIT.get(m.group(2), 1))


def docker_storage(timeout_s: float = 60) -> dict[str, Any]:
    if not shutil.which("docker"):
        return {"status": "absent"}
    try:
        p = subprocess.run(
            ["docker", "system", "df", "--format", "{{json .}}"],
            capture_output=True, text=True, timeout=timeout_s, check=False,
        )
    except subprocess.TimeoutExpired:
        return {"status": "timeout"}
    if p.returncode != 0:
        return {"status": "error", "error": (p.stderr or "")[:200]}
    rows = {}
    for line in p.stdout.splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        rows[r.get("Type", "?")] = {
            "size_bytes": _size_to_bytes(r.get("Size", "")),
            "reclaimable_bytes": _size_to_bytes(r.get("Reclaimable", "")) or 0,
            "total": r.get("TotalCount"),
            "active": r.get("Active"),
        }
    return {
        "status": "ok",
        "source": "docker system df",
        "types": rows,
        "reclaimable_bytes": sum(v["reclaimable_bytes"] for v in rows.values()),
        "note": "containerd 'moby' namespace is Docker's store; directory sizes "
        "of /var/lib/docker + /var/lib/containerd are never added or freed "
        "directly -- only reclaimable_bytes counts.",
    }


def deleted_open_files(root: str = "/") -> dict[str, Any]:
    root_dev = os.stat(root).st_dev
    seen: set[tuple[int, int]] = set()
    total, top = 0, []
    for pid in filter(str.isdigit, os.listdir("/proc")):
        fd_dir = f"/proc/{pid}/fd"
        try:
            fds = os.listdir(fd_dir)
        except OSError:
            continue
        for fd in fds:
            link = f"{fd_dir}/{fd}"
            try:
                target = os.readlink(link)
                if not target.endswith(" (deleted)") or not target.startswith("/"):
                    continue
                st = os.stat(link)
            except OSError:
                continue
            if st.st_dev != root_dev or (st.st_dev, st.st_ino) in seen:
                continue
            seen.add((st.st_dev, st.st_ino))
            b = st.st_blocks * 512
            total += b
            top.append({"pid": int(pid), "path": target, "bytes": b})
    top.sort(key=lambda x: x["bytes"], reverse=True)
    return {"bytes": total, "count": len(seen), "top": top[:10], "source": "/proc/*/fd"}


def journal_usage() -> dict[str, Any]:
    if not shutil.which("journalctl"):
        return {"status": "absent"}
    try:
        p = subprocess.run(
            ["journalctl", "--disk-usage"], capture_output=True, text=True, timeout=30
        )
    except subprocess.TimeoutExpired:
        return {"status": "timeout"}
    m = re.search(r"([\d.]+)([KMGT])", p.stdout or "")
    b = int(float(m.group(1)) * {"K": 2**10, "M": 2**20, "G": 2**30, "T": 2**40}[m.group(2)]) if m else None
    return {"status": "ok", "bytes": b, "source": "journalctl --disk-usage"}


def is_restic_repo(path: str) -> bool:
    try:
        names = set(os.listdir(path))
    except OSError:
        return False
    return {"config", "data", "keys", "snapshots"} <= names


def collect(
    per_path_timeout_s: float = 900,
    total_budget_s: float = 2400,
    root: str = "/",
) -> dict[str, Any]:
    t0 = time.monotonic()
    fs = fs_usage(root)
    dirs, top_file_bytes = top_level_targets(root)
    paths: list[dict[str, Any]] = []
    for d in dirs:
        remaining = total_budget_s - (time.monotonic() - t0)
        if remaining <= 1:
            paths.append({"path": d, "status": "skipped", "bytes": None,
                          "confirmed_bytes": 0, "children": [], "reason": "total_budget"})
            continue
        paths.append(scan_path(d, timeout_s=min(per_path_timeout_s, remaining)))
    backups = []
    for p in paths:
        for c in p.get("children", []):
            if BACKUP_NAME.search(os.path.basename(c["path"])) or is_restic_repo(c["path"]):
                backups.append({
                    "path": c["path"],
                    "bytes": c["bytes"],
                    "kind": "restic" if is_restic_repo(c["path"]) else "backup-dir",
                    "same_filesystem_as_root": True,  # du -x guarantees same fs
                })
    # Keep the most specific hit only (no double counting /root/backups + its restic repo).
    backups = [
        b for b in backups
        if not any(o["path"].startswith(b["path"].rstrip("/") + "/") for o in backups)
    ]
    timed_out = [p["path"] for p in paths if p["status"] != "complete"]
    return {
        "schema": SCHEMA,
        "measured_at": _now_iso(),
        "collection_seconds": round(time.monotonic() - t0, 1),
        "status": "partial" if timed_out else "complete",
        "timed_out_paths": timed_out,
        "per_path_timeout_s": per_path_timeout_s,
        "filesystem": fs,
        "top_level_file_bytes": top_file_bytes,
        "paths": sorted(paths, key=lambda p: p.get("confirmed_bytes") or 0, reverse=True),
        "deleted_open": deleted_open_files(root),
        "docker": docker_storage(),
        "journal": journal_usage(),
        "backups_same_disk": sorted(backups, key=lambda b: b["bytes"], reverse=True),
    }


def write_evidence(ev: dict[str, Any], path: str = DISK_EVIDENCE_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(ev, f, indent=1)
    os.replace(tmp, path)


def load_evidence(path: str = DISK_EVIDENCE_PATH) -> dict[str, Any] | None:
    try:
        with open(path) as f:
            ev = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    return ev if ev.get("schema") == SCHEMA else None


# ── reconciliation ───────────────────────────────────────────────────────────


def _age_s(ev: dict[str, Any]) -> float | None:
    try:
        t = datetime.fromisoformat(ev["measured_at"])
        return (datetime.now(timezone.utc) - t).total_seconds()
    except (KeyError, ValueError, TypeError):
        return None


def _gb(b: int | float | None) -> float | None:
    return None if b is None else round(b / GB, 1)


def reconcile(ev: dict[str, Any] | None, live_used_bytes: int | None = None) -> dict[str, Any]:
    if not ev:
        return {
            "status": "no_evidence",
            "confidence": "low",
            "root_cause": None,
            "message": "No disk evidence on file. Run well-disk-evidence.service. "
            "Disk percentage alone is not a diagnosis.",
            "largest": [],
            "freeable": [],
        }
    age = _age_s(ev)
    fs = ev.get("filesystem", {})
    used = fs.get("used_bytes") or 0
    accounted = (
        sum(p.get("confirmed_bytes") or 0 for p in ev.get("paths", []))
        + (ev.get("top_level_file_bytes") or 0)
        + (ev.get("deleted_open", {}).get("bytes") or 0)
    )
    unaccounted = max(used - accounted, 0)
    unacc_pct = round(unaccounted / used * 100, 1) if used else None
    reasons = []
    if ev.get("timed_out_paths"):
        reasons.append(f"timed out: {', '.join(ev['timed_out_paths'])}")
    if unacc_pct is not None and unacc_pct > UNACCOUNTED_LIMIT * 100:
        reasons.append(f"{unacc_pct}% of used space unexplained")
    if age is None or age > STALE_AFTER_S:
        reasons.append("evidence stale" if age else "evidence timestamp missing")
    drift_pct = None
    if live_used_bytes and used:
        drift_pct = round((live_used_bytes - used) / used * 100, 1)
    confidence = "low" if reasons else "high"

    largest = [
        {"path": p["path"], "size_gb": _gb(p.get("confirmed_bytes")),
         "status": p["status"],
         "top_children": [{"path": c["path"], "size_gb": _gb(c["bytes"])} for c in p.get("children", [])[:5]]}
        for p in ev.get("paths", [])[:6]
        if (p.get("confirmed_bytes") or 0) >= MIN_CHILD_BYTES
    ]
    root_cause = None
    if confidence == "high" and largest:
        top = largest[0]
        root_cause = (
            f"{top['path']} holds {top['size_gb']} GB of {_gb(used)} GB used"
            + (f"; largest inside: " + ", ".join(f"{c['path']} {c['size_gb']} GB" for c in top["top_children"][:3])
               if top["top_children"] else "")
        )
    msg = (
        f"Scan accounts for {_gb(accounted)} GB of {_gb(used)} GB used. "
        + ("Root cause confidence is LOW (" + "; ".join(reasons) + "). Continue with targeted scans; do not name a cause."
           if reasons else "Totals reconcile.")
    )
    return {
        "status": ev.get("status"),
        "measured_at": ev.get("measured_at"),
        "evidence_age_seconds": None if age is None else round(age),
        "collection_seconds": ev.get("collection_seconds"),
        "filesystem_used_gb": _gb(used),
        "accounted_gb": _gb(accounted),
        "unaccounted_gb": _gb(unaccounted),
        "unaccounted_pct": unacc_pct,
        "live_drift_pct_since_scan": drift_pct,
        "inodes_used_pct": fs.get("inodes_used_pct"),
        "timed_out_paths": ev.get("timed_out_paths", []),
        "confidence": confidence,
        "low_confidence_reasons": reasons,
        "root_cause": root_cause,
        "message": msg,
        "largest": largest,
        "freeable": [
            {"recommendation_id": a["recommendation_id"], "target": a.get("target"),
             "expected_recovery_gb": a["expected_recovery_gb"], "risk": a["risk"]}
            for a in disk_actions(ev) if a.get("expected_recovery_gb")
        ],
        "source": DISK_EVIDENCE_PATH,
    }


# ── shared disk action table (diagnose + recommend read THIS) ────────────────

JOURNAL_TARGET_BYTES = 500 * 2**20

_STATIC_ACTIONS: list[dict[str, Any]] = [
    {
        "recommendation_id": "disk.journal.vacuum_500m",
        "command": "journalctl --vacuum-size=500M",
        "risk": "LOW", "reversible": False, "requires_approval": False,
        "expected_effect": "trim journal to 500 MB (one canonical retention rule)",
        "verification": ["journalctl --disk-usage"],
    },
    {
        "recommendation_id": "disk.apt.clean",
        "command": "apt-get clean",
        "risk": "LOW", "reversible": True, "requires_approval": False,
        "expected_effect": "drop downloaded .deb cache (re-downloadable)",
        "verification": ["du -sh /var/cache/apt"],
    },
    {
        "recommendation_id": "disk.snap.remove_disabled",
        "command": "snap list --all | awk '/disabled/{print $1, $3}' | while read n r; do snap remove \"$n\" --revision=\"$r\"; done",
        "risk": "MEDIUM", "reversible": False, "requires_approval": True,
        "expected_effect": "remove disabled snap revisions (deletes data)",
        "expected_recovery_gb": None,
        "verification": ["snap list --all"],
    },
    {
        "recommendation_id": "disk.apt.autoremove",
        "command": "apt-get autoremove --purge",
        "risk": "MEDIUM", "reversible": False, "requires_approval": True,
        "expected_effect": "remove packages apt thinks are unused -- review the list first",
        "expected_recovery_gb": None,
        "preconditions": ["apt-get -s autoremove reviewed by operator"],
        "verification": ["dpkg -l | wc -l"],
    },
]


def disk_actions(ev: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Every disk action with ID, measured expected recovery, risk, reversibility."""
    acts = [dict(a) for a in _STATIC_ACTIONS]
    ev = ev or {}
    j = (ev.get("journal") or {}).get("bytes")
    for a in acts:
        if a["recommendation_id"] == "disk.journal.vacuum_500m":
            a["expected_recovery_gb"] = _gb(max(j - JOURNAL_TARGET_BYTES, 0)) if j else None
        elif a["recommendation_id"] == "disk.apt.clean":
            a.setdefault("expected_recovery_gb", None)

    dk = ev.get("docker") or {}
    types = dk.get("types") or {}
    for t, rid, cmd, risk in (
        ("Images", "disk.docker.prune_images", "docker image prune -a", "MEDIUM"),
        ("Build Cache", "disk.docker.prune_build_cache", "docker builder prune", "LOW"),
        ("Containers", "disk.docker.prune_containers", "docker container prune", "MEDIUM"),
        ("Local Volumes", "disk.docker.prune_volumes", "docker volume prune", "HIGH"),
    ):
        rec = (types.get(t) or {}).get("reclaimable_bytes")
        acts.append({
            "recommendation_id": rid, "command": cmd, "risk": risk,
            "reversible": False, "requires_approval": True,
            "expected_recovery_gb": _gb(rec) if rec is not None else None,
            "expected_effect": f"remove unused docker {t.lower()} (measured reclaimable only)",
            "worth_it": bool(rec and rec >= MIN_CHILD_BYTES),
            "verification": ["docker system df"],
        })

    for b in ev.get("backups_same_disk", []):
        acts.append({
            "recommendation_id": "disk.backup.move_offsite",
            "target": b["path"], "command": None,
            "risk": "HIGH", "reversible": False, "requires_approval": True,
            "expected_recovery_gb": _gb(b["bytes"]),
            "warning": "Backup on the same disk protects against file deletion, not disk failure. "
            "Move it off-server and verify the copy BEFORE deleting locally.",
            "preconditions": ["offsite copy exists", "offsite copy verified (restic check / checksum)"],
            "verification": ["df -h /", f"test ! -e {b['path']}"],
        })

    for p in ev.get("paths", []):
        for c in p.get("children", []):
            if ARCHIVE_NAME.search(c["path"]) and not BACKUP_NAME.search(os.path.basename(c["path"])):
                acts.append({
                    "recommendation_id": "disk.appdata.review_archive",
                    "target": c["path"], "command": None,
                    "risk": "HIGH", "reversible": False, "requires_approval": True,
                    "expected_recovery_gb": _gb(c["bytes"]),
                    "expected_effect": "operator review: keep newest, remove stale archive/quarantine data",
                    "verification": [f"du -sh {c['path']}"],
                })
    rank = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
    acts.sort(key=lambda a: (-(a.get("expected_recovery_gb") or 0), rank.get(a["risk"], 3)))
    return acts
