#!/usr/bin/env bash
# deploy-to-runtime.sh — Deploy /root/WELL source → /opt/well runtime
# DITEMPA BUKAN DIBERI — Truth is forged, not assumed.
# Parity with arifOS deploy architecture: 3-way commit alignment + release manifest.

set -euo pipefail

SRC="/root/WELL"
DST="/opt/well"
SERVICE_NAME="well.service"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"; }

# ── Sanity checks ───────────────────────────────────────────────────────────
if [[ ! -f "$SRC/server.py" ]]; then
    log "ERROR: source tree $SRC/server.py not found"; exit 1
fi
if [[ ! -d "$DST" ]]; then
    log "ERROR: runtime destination $DST not found"; exit 1
fi

GIT_COMMIT="$(git -C "$SRC" rev-parse --short=7 HEAD 2>/dev/null || echo "unknown")"
BUILD_TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

log "═══ WELL Deploy to Runtime ═══"
log "  Source:          $SRC"
log "  Destination:     $DST"
log "  Target commit:   $GIT_COMMIT"
log "  Timestamp:       $BUILD_TS"

# ── Check git status ────────────────────────────────────────────────────────
if git -C "$SRC" rev-parse --git-dir >/dev/null 2>&1; then
    if ! git -C "$SRC" diff --quiet; then
        log "WARN: /root/WELL has uncommitted changes; deploying current working tree"
    fi
fi

# ── Sync source tree to /opt/well ───────────────────────────────────────────
log "Syncing $SRC → $DST (preserving venv and runtime configs)"
rsync -a \
    --exclude='.git' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='.env' \
    --exclude='.identity_hash' \
    "$SRC/" "$DST/"

# ── Write release manifest and deployment stamp ─────────────────────────────
MANIFEST_FILE="$DST/release-manifest.json"
cat > "$MANIFEST_FILE" <<MANIFEST_EOF
{
  "release": 1,
  "name": "WELL Substrate Truth",
  "git_commit": "$GIT_COMMIT",
  "build_timestamp": "$BUILD_TS",
  "deployed_by": "FI-009",
  "deployed_path": "$DST",
  "service": "$SERVICE_NAME"
}
MANIFEST_EOF

cp "$MANIFEST_FILE" "$SRC/release-manifest.json"
echo "$GIT_COMMIT" > "$DST/.git_commit"
echo "$GIT_COMMIT" > "$SRC/.git_commit"

log "Wrote $MANIFEST_FILE"
log "Wrote $DST/.git_commit: $GIT_COMMIT"

# ── Restart service ─────────────────────────────────────────────────────────
log "Restarting $SERVICE_NAME..."
systemctl restart "$SERVICE_NAME" || { log "ERROR: failed to restart $SERVICE_NAME"; exit 1; }

# ── Health & Parity verification ────────────────────────────────────────────
log "Waiting for WELL health..."
HEALTH_OK=false
for i in {1..30}; do
    RESP=$(curl -s --noproxy '*' http://127.0.0.1:18083/health 2>/dev/null || true)
    if [[ -n "$RESP" ]] && echo "$RESP" | jq -e '.drift != null' >/dev/null 2>&1; then
        DRIFT=$(echo "$RESP" | jq -r '.drift')
        DEP_COMMIT=$(echo "$RESP" | jq -r '.deployed_commit')
        SRC_COMMIT=$(echo "$RESP" | jq -r '.source_commit')
        BLT_COMMIT=$(echo "$RESP" | jq -r '.built_commit')
        
        log "  Attempt $i: source=$SRC_COMMIT deployed=$DEP_COMMIT built=$BLT_COMMIT drift=$DRIFT"
        if [[ "$DRIFT" == "false" && "$DEP_COMMIT" == "$GIT_COMMIT" ]]; then
            HEALTH_OK=true
            break
        fi
    fi
    sleep 1
done

if [[ "$HEALTH_OK" != "true" ]]; then
    log "ERROR: WELL health parity check failed"
    exit 1
fi

log "✅ WELL deploy complete — 3-way commit parity verified (commit $GIT_COMMIT, drift: false)"
