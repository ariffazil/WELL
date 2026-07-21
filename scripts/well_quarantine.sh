#!/usr/bin/env bash
# well_quarantine.sh — F1 AMANAH quarantine discipline for WELL/A-FORGE.
# Never rm. Always mv to quarantine with 7-day TTL cooling.
# Deletion is two-step: quarantine → expire (7 days) → archive or purge.
#
# Usage:
#   quarantine <file> [--reason "why"] [--actor "who"]     → mv to quarantine
#   quarantine --list                                       → list quarantined items
#   quarantine --restore <quarantine_id>                    → restore from quarantine
#   quarantine --expire [--force]                           → purge items older than 7 days
#
# Forged 2026-07-21. DITEMPA BUKAN DIBERI.

set -euo pipefail

QUARANTINE_DIR="/root/WELL/quarantine"
LOG_FILE="$QUARANTINE_DIR/quarantine.jsonl"
TTL_DAYS=7
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%S+00:00)

# ── Helpers ──────────────────────────────────────────────────────────────────
_quarantine_id() {
    local src="$1"
    local ts="$2"
    local hash=$(echo -n "$src-$ts" | sha256sum | cut -c1-12)
    echo "q-$(date -u +%Y%m%d-%H%M%S)-$hash"
}

_log() {
    local entry="$1"
    echo "$entry" >> "$LOG_FILE"
}

# ── Quarantine ───────────────────────────────────────────────────────────────
do_quarantine() {
    local src="$1"
    local reason="${2:-unspecified}"
    local actor="${3:-unknown}"

    if [[ ! -e "$src" ]]; then
        echo "ERROR: $src does not exist" >&2
        return 1
    fi

    local qid=$(_quarantine_id "$src" "$TIMESTAMP")
    local dest="$QUARANTINE_DIR/$qid"
    local basename=$(basename "$src")

    # Move atomically within same filesystem (mv is fast, no copy needed)
    mv "$src" "$dest" 2>/dev/null || {
        # Cross-filesystem: copy then remove
        cp -a "$src" "$dest" && rm -rf "$src"
    }

    # Record metadata
    local sha=$(sha256sum "$dest" 2>/dev/null | cut -c1-64 || echo "unknown")
    local size=$(stat -c%s "$dest" 2>/dev/null || echo "0")

    _log $(python3 -c "
import json
print(json.dumps({
    'quarantine_id': '$qid',
    'original_path': '$src',
    'quarantined_at': '$TIMESTAMP',
    'reason': '$reason',
    'actor': '$actor',
    'basename': '$basename',
    'sha256': '$sha',
    'size_bytes': $size,
    'ttl_days': $TTL_DAYS,
    'expires_at': '$TIMESTAMP',  # computed by expire logic
    'action': 'quarantine',
}))
")

    echo "QUARANTINED: $src → $qid"
    echo "  ID:    $qid"
    echo "  Path:  $dest"
    echo "  TTL:   $TTL_DAYS days"
    echo "  SHA:   $sha"
    echo "  Reason: $reason"
}

# ── List ─────────────────────────────────────────────────────────────────────
do_list() {
    if [[ ! -f "$LOG_FILE" ]]; then
        echo "No quarantine entries."
        return
    fi
    echo "Quarantined items:"
    echo ""
    while IFS= read -r line; do
        echo "$line" | python3 -c "
import json,sys
d=json.loads(sys.stdin.readline())
ts=d.get('quarantined_at','?')[:19]
print(f\"  {d['quarantine_id']}  |  {ts}  |  {d['basename']}  |  {d['reason'][:40]}\")
" 2>/dev/null
    done < "$LOG_FILE"
}

# ── Restore ──────────────────────────────────────────────────────────────────
do_restore() {
    local qid="$1"
    local src="$QUARANTINE_DIR/$qid"

    if [[ ! -f "$src" ]] && [[ ! -d "$src" ]]; then
        echo "ERROR: $qid not found in quarantine" >&2
        return 1
    fi

    # Find original path from log
    local original=$(python3 -c "
import json
with open('$LOG_FILE') as f:
    for line in f:
        d = json.loads(line.strip())
        if d.get('quarantine_id') == '$qid':
            print(d['original_path'])
            break
" 2>/dev/null)

    if [[ -z "$original" ]]; then
        echo "ERROR: original path not found in quarantine log" >&2
        return 1
    fi

    mv "$src" "$original"
    _log $(python3 -c "
import json
print(json.dumps({
    'quarantine_id': '$qid',
    'restored_at': '$TIMESTAMP',
    'restored_to': '$original',
    'action': 'restore',
}))
")
    echo "RESTORED: $qid → $original"
}

# ── Expire ───────────────────────────────────────────────────────────────────
do_expire() {
    local force="${1:-false}"
    local expired=0
    local kept=0

    while IFS= read -r line; do
        local qid=$(echo "$line" | python3 -c "import json,sys; print(json.loads(sys.stdin.readline())['quarantine_id'])" 2>/dev/null)
        local ts=$(echo "$line" | python3 -c "import json,sys; print(json.loads(sys.stdin.readline())['quarantined_at'])" 2>/dev/null)
        local src="$QUARANTINE_DIR/$qid"

        if [[ -z "$qid" ]] || [[ ! -e "$src" ]]; then
            continue
        fi

        # Check age
        local age_days=$(python3 -c "
from datetime import datetime, timezone
ts = datetime.fromisoformat('${ts}'.replace('Z','+00:00'))
now = datetime.now(timezone.utc)
print(f'{(now-ts).total_seconds()/86400:.1f}')
" 2>/dev/null)

        if (( $(echo "$age_days > $TTL_DAYS" | bc -l 2>/dev/null || echo 0) )); then
            if [[ "$force" == "true" ]]; then
                rm -rf "$src"
                echo "  EXPIRED: $qid (age: ${age_days}d)"
            else
                echo "  EXPIRY CANDIDATE: $qid (age: ${age_days}d) — use --force to purge"
            fi
            expired=$((expired + 1))
        else
            kept=$((kept + 1))
        fi
    done < <(grep '"action": "quarantine"' "$LOG_FILE" 2>/dev/null || true)

    echo ""
    echo "Expiry candidates: $expired | Active: $kept"
}

# ── Main ─────────────────────────────────────────────────────────────────────
mkdir -p "$QUARANTINE_DIR"

case "${1:-}" in
    --list|-l)
        do_list
        ;;
    --restore|-r)
        do_restore "${2:-}"
        ;;
    --expire|-e)
        do_expire "${2:-false}"
        ;;
    -h|--help)
        sed -n '2,15p' "$0"
        ;;
    *)
        if [[ -z "${1:-}" ]]; then
            echo "Usage: quarantine <file> [--reason ...] [--actor ...]"
            exit 1
        fi
        SRC="$1"
        REASON="unspecified"
        ACTOR="unknown"
        shift
        while [[ $# -gt 0 ]]; do
            case "$1" in
                --reason) REASON="$2"; shift 2 ;;
                --actor)  ACTOR="$2"; shift 2 ;;
                *) shift ;;
            esac
        done
        do_quarantine "$SRC" "$REASON" "$ACTOR"
        ;;
esac
