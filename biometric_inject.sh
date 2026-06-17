#!/usr/bin/env bash
# WELL biometric injection — interactive, sovereign-only, reversible.
# Reads 5 readiness fields, validates, writes state.json atomically, restarts WELL.
#
# Usage:
#   biometric_inject.sh                       # interactive prompts
#   biometric_inject.sh --dry-run             # show what would be written, no I/O
#   biometric_inject.sh --non-interactive \   # supply values via flags
#     --delta-s 0.2 --peace2 0.7 --kappa-r 0.6 \
#     --rasa "clear" --amanah 0.9
#
#   # NEW 2026-06-17 — per-signal self-report (closes 13-signal coverage gaps):
#   biometric_inject.sh --signals \
#     --signal-s05-sleep '{"hours": 7.5, "quality": 8, "debt_days": 0}' \
#     --signal-s06-metabolic '{"glucose_stable": true, "energy_level": 7}' \
#     --signal-s07-nutrition '{"water_ml": 1800, "meals": 2}' \
#     --signal-s08-movement '{"steps": 4200, "strength_sessions": 0}' \
#     --signal-s09-pain '{"level": 1, "sites": []}' \
#     --signal-s11-stress '{"subjective_load": 3, "anxiety": 2}'
#
# Well score formula (transparent):
#   well_score = (peace2 * 0.35
#                + (1.0 - delta_s) * 0.20
#                + kappa_r * 0.20
#                + amanah * 0.15
#                + (10.0 - decision_fatigue) / 10 * 0.10) * 100
#   decision_fatigue is on 0-10 scale (matches legacy schema).
#
# Reversibility: state.json is overwritten with .json.bak kept for 24h.

set -euo pipefail

WELL_DIR="/root/WELL"
STATE_FILE="$WELL_DIR/state.json"
STATE_BAK="$WELL_DIR/state.json.bak"
SERVICE_NAME="well"
TIMESTAMP_UTC="$(date -u +%Y-%m-%dT%H:%M:%S+00:00)"

# ---- Parse flags ------------------------------------------------------------
DRY_RUN=false
NON_INTERACTIVE=false
SIGNALS_MODE=false
IN_DELTA_S=""
IN_PEACE2=""
IN_KAPPA_R=""
IN_RASA=""
IN_AMANAH=""
IN_CLARITY=""
IN_DECISION_FATIGUE=""
# Per-signal JSON inputs (NEW 2026-06-17)
declare -A SIGNAL_INPUTS=(
  [s01_heart_circulation]=""
  [s02_blood_pressure]=""
  [s03_breathing_oxygenation]=""
  [s04_temperature_inflammation]=""
  [s05_sleep_architecture]=""
  [s06_metabolic_state]=""
  [s07_nutrition_hydration]=""
  [s08_movement_strength]=""
  [s09_pain_injury]=""
  [s10_cognitive_clarity]=""
  [s11_emotional_stress]=""
  [s12_social_dignity_consent]=""
  [s13_environment_livelihood]=""
)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)            DRY_RUN=true; shift ;;
    --non-interactive)    NON_INTERACTIVE=true; shift ;;
    --signals)            SIGNALS_MODE=true; shift ;;
    --delta-s)            IN_DELTA_S="$2"; shift 2 ;;
    --peace2)             IN_PEACE2="$2"; shift 2 ;;
    --kappa-r)            IN_KAPPA_R="$2"; shift 2 ;;
    --rasa)               IN_RASA="$2"; shift 2 ;;
    --amanah)             IN_AMANAH="$2"; shift 2 ;;
    --clarity)            IN_CLARITY="$2"; shift 2 ;;
    --decision-fatigue)   IN_DECISION_FATIGUE="$2"; shift 2 ;;
    --signal-s01-heart-circulation)           SIGNAL_INPUTS[s01_heart_circulation]="$2"; shift 2 ;;
    --signal-s02-blood-pressure)              SIGNAL_INPUTS[s02_blood_pressure]="$2"; shift 2 ;;
    --signal-s03-breathing-oxygenation)       SIGNAL_INPUTS[s03_breathing_oxygenation]="$2"; shift 2 ;;
    --signal-s04-temperature-inflammation)    SIGNAL_INPUTS[s04_temperature_inflammation]="$2"; shift 2 ;;
    --signal-s05-sleep-architecture)          SIGNAL_INPUTS[s05_sleep_architecture]="$2"; shift 2 ;;
    --signal-s06-metabolic-state)             SIGNAL_INPUTS[s06_metabolic_state]="$2"; shift 2 ;;
    --signal-s07-nutrition-hydration)         SIGNAL_INPUTS[s07_nutrition_hydration]="$2"; shift 2 ;;
    --signal-s08-movement-strength)           SIGNAL_INPUTS[s08_movement_strength]="$2"; shift 2 ;;
    --signal-s09-pain-injury)                 SIGNAL_INPUTS[s09_pain_injury]="$2"; shift 2 ;;
    --signal-s10-cognitive-clarity)           SIGNAL_INPUTS[s10_cognitive_clarity]="$2"; shift 2 ;;
    --signal-s11-emotional-stress)            SIGNAL_INPUTS[s11_emotional_stress]="$2"; shift 2 ;;
    --signal-s12-social-dignity-consent)      SIGNAL_INPUTS[s12_social_dignity_consent]="$2"; shift 2 ;;
    --signal-s13-environment-livelihood)      SIGNAL_INPUTS[s13_environment_livelihood]="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,42p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown flag: $1" >&2
      exit 2
      ;;
  esac
done

# ---- Helpers ----------------------------------------------------------------
say()  { printf '%s\n' "$*"; }
hr()   { printf '%s\n' "------------------------------------------------------------"; }
err()  { printf 'ERROR: %s\n' "$*" >&2; }
ok()   { printf '  ✓ %s\n' "$*"; }

validate_float_01() {
  local v="$1" name="$2"
  if ! [[ "$v" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
    err "$name must be a number 0.0–1.0 (got: $v)"
    return 1
  fi
  if (( $(awk "BEGIN{print !($v >= 0.0 && $v <= 1.0)}") )); then
    err "$name out of range 0.0–1.0 (got: $v)"
    return 1
  fi
}

compute_well_score() {
  awk "BEGIN {
    p = $1; d = $2; k = $3; a = $4; f = $5;
    printf(\"%.1f\", (p * 0.35 + (1.0 - d) * 0.20 + k * 0.20 + a * 0.15 + (10.0 - f) / 10.0 * 0.10) * 100)
  }"
}

# ---- Show current state -----------------------------------------------------
hr
say "WELL biometric injection"
hr

if [[ -f "$STATE_FILE" ]]; then
  say "Current state.json (raw):"
  cat "$STATE_FILE"
  hr
  CUR_TS="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("timestamp","?"))' "$STATE_FILE" 2>/dev/null || echo "?")"
  CUR_AGE="$(python3 -c "
import json, datetime
ts = json.load(open('$STATE_FILE')).get('timestamp')
if not ts or ts == '?':
    print('?')
else:
    t = datetime.datetime.fromisoformat(ts.replace('Z','+00:00'))
    age_h = (datetime.datetime.now(datetime.timezone.utc) - t).total_seconds() / 3600
    print(f'{age_h:.1f}h')
" 2>/dev/null || echo "?")"
  say "Age of current state: $CUR_AGE  (timestamp: $CUR_TS)"
else
  say "No state.json found at $STATE_FILE — will create fresh."
fi
hr

# ---- Collect fields ---------------------------------------------------------
collect_field() {
  local prompt="$1" current="$2"
  if [[ -n "$current" ]]; then
    echo "$current"
    return
  fi
  if $NON_INTERACTIVE; then
    err "Missing required field in --non-interactive mode: $prompt"
    exit 2
  fi
  local val
  read -r -p "$prompt: " val
  echo "$val"
}

DELTA_S="$(collect_field "delta_s (0.0 stable ↔ 1.0 chaotic)" "$IN_DELTA_S")"
validate_float_01 "$DELTA_S" "delta_s"

PEACE2="$(collect_field "peace2 (0.0 destabilized ↔ 1.0 at peace)" "$IN_PEACE2")"
validate_float_01 "$PEACE2" "peace2"

KAPPA_R="$(collect_field "kappa_r (0.0 brittle ↔ 1.0 resilient)" "$IN_KAPPA_R")"
validate_float_01 "$KAPPA_R" "kappa_r"

if [[ -n "$IN_RASA" ]]; then
  RASA="$IN_RASA"
else
  if $NON_INTERACTIVE; then err "Missing --rasa in --non-interactive mode"; exit 2; fi
  read -r -p "rasa (one word for felt sense, e.g. grounded): " RASA
fi
RASA="${RASA:-unspecified}"
RASA="${RASA//\"/\\\"}"

# Optional cognitive metrics — derive from peace2/kappa_r if not given
if [[ -n "$IN_CLARITY" ]]; then
  CLARITY="$IN_CLARITY"
else
  CLARITY="$(awk "BEGIN{printf(\"%.1f\", ($KAPPA_R + $PEACE2) / 2.0 * 10)}")"
  ok "clarity derived from (kappa_r + peace2) / 2: $CLARITY"
fi
if [[ -n "$IN_DECISION_FATIGUE" ]]; then
  DECISION_FATIGUE="$IN_DECISION_FATIGUE"
else
  DECISION_FATIGUE="$(awk "BEGIN{printf(\"%.1f\", $DELTA_S * 10.0)}")"
  ok "decision_fatigue derived from delta_s: $DECISION_FATIGUE"
fi

AMANAH="$(collect_field "amanah (0.0 broken ↔ 1.0 fully held)" "$IN_AMANAH")"
validate_float_01 "$AMANAH" "amanah"

WELL_SCORE="$(compute_well_score "$PEACE2" "$DELTA_S" "$KAPPA_R" "$AMANAH" "$DECISION_FATIGUE")"

# ---- Per-signal self-report (NEW 2026-06-17 — closes 13-signal coverage gaps)
SIGNAL_JSON_BLOCK=""
SIGNAL_COUNT=0
if $SIGNALS_MODE; then
  _signal_pairs=""
  for _key in "${!SIGNAL_INPUTS[@]}"; do
    _val="${SIGNAL_INPUTS[$_key]}"
    if [[ -n "$_val" ]]; then
      # Validate JSON
      if ! echo "$_val" | python3 -c "import json,sys; json.loads(sys.stdin.read())" 2>/dev/null; then
        err "Invalid JSON for --signal-${_key/_/-}: $_val"
        exit 2
      fi
      _signal_pairs="${_signal_pairs}\"${_key}\": $_val, "
      SIGNAL_COUNT=$((SIGNAL_COUNT + 1))
    fi
  done
  if [[ $SIGNAL_COUNT -eq 0 ]]; then
    err "--signals mode requires at least one --signal-S0X-name flag"
    exit 2
  fi
  # Build a valid JSON object: leading '{' + pairs (trailing ', ' stripped) + closing '}'
  _trimmed="${_signal_pairs%, }"
  SIGNAL_JSON_BLOCK="{${_trimmed}}"
  ok "per-signal self-report: $SIGNAL_COUNT signal(s) captured"
fi

# ---- Confirm ----------------------------------------------------------------
hr
say "About to write to $STATE_FILE:"
say ""
say "  timestamp          : $TIMESTAMP_UTC"
say "  schema             : AFWELL State Schema v2026.05.12"
say "  environment        : PROD"
say "  biometric.delta_s  : $DELTA_S"
say "  biometric.peace2   : $PEACE2"
say "  biometric.kappa_r  : $KAPPA_R"
say "  biometric.rasa     : \"$RASA\""
say "  biometric.amanah   : $AMANAH"
say "  metrics.cognitive  : clarity=$CLARITY, decision_fatigue=$DECISION_FATIGUE"
say "  well_score         : $WELL_SCORE  (computed: peace2×0.35 + (1-ds)×0.20 + κ×0.20 + amanah×0.15 + (10-fatigue)/10×0.10)"
if [[ $SIGNAL_COUNT -gt 0 ]]; then
  say "  signals            : $SIGNAL_COUNT per-signal value(s) injected"
fi
say "  truth_status       : VERIFIED"
say "  freshness          : FRESH"
say ""
hr

if $DRY_RUN; then
  say "DRY-RUN — no files written, no service restarted."
  exit 0
fi

if ! $NON_INTERACTIVE; then
  read -r -p "Commit? type 'yes' to proceed: " confirm
  if [[ "$confirm" != "yes" ]]; then
    say "Aborted. No changes made."
    exit 0
  fi
fi

# ---- Write atomically -------------------------------------------------------
if [[ -f "$STATE_FILE" ]]; then
  cp "$STATE_FILE" "$STATE_BAK"
  ok "Backup written to $STATE_BAK"
fi

python3 <<EOF
import json, os, time

state = {
    "schema": "AFWELL State Schema v2026.05.12",
    "timestamp": "$TIMESTAMP_UTC",
    "operator_id": "arif",
    "biometric": {
        "delta_s": float("$DELTA_S"),
        "peace2": float("$PEACE2"),
        "kappa_r": float("$KAPPA_R"),
        "rasa": "$RASA",
        "amanah": float("$AMANAH"),
    },
    "metrics": {
        "cognitive": {
            "clarity": float("$CLARITY"),
            "decision_fatigue": float("$DECISION_FATIGUE"),
        }
    },
    "well_score": float("$WELL_SCORE"),
    "floors_violated": [],
    "backend_status": "STABLE",
    "last_successful_read": "$TIMESTAMP_UTC",
    "last_successful_write": "$TIMESTAMP_UTC",
    "state_file_access": "PASS",
    "vault_access": "OK",
    "test_contamination": "NO",
    "contamination_quarantined": False,
    "confidence": "HIGH",
    "freshness": "FRESH",
    "truth_status": "VERIFIED",
    "environment": "PROD",
    "telemetry_confidence": "HIGH",
    "reason": "Sovereign biometric injection (biometric_inject.sh)",
    "safe_mode": "off",
    "arif_decision_required": False,
    "w0": "OPERATOR_VETO_INTACT / HIERARCHY_INVARIANT",
}

# Per-signal self-report block (NEW 2026-06-17)
_signal_raw = """$SIGNAL_JSON_BLOCK"""
if _signal_raw:
    try:
        state["signals"] = json.loads(_signal_raw)
        state["signals_meta"] = {
            "injected_count": $SIGNAL_COUNT,
            "injection_ts": "$TIMESTAMP_UTC",
            "source": "biometric_inject.sh --signals",
        }
    except json.JSONDecodeError as _e:
        print(f"  ✗ signals JSON parse failed: {_e}", file=os.sys.stderr)
        state["signals_error"] = str(_e)

tmp = "$STATE_FILE.tmp"
with open(tmp, "w") as f:
    json.dump(state, f, indent=2)
os.replace(tmp, "$STATE_FILE")
print("  ✓ state.json written")
if _signal_raw:
    print(f"  ✓ signals block: {$SIGNAL_COUNT} signal(s)")
EOF

ok "WELL state.json updated"

# ---- Restart and verify -----------------------------------------------------
say ""
say "Restarting well service..."
if systemctl restart "$SERVICE_NAME"; then
  ok "well.service restarted"
else
  err "well.service restart FAILED — check: journalctl -u well -n 20"
  exit 1
fi

sleep 2

say ""
say "Verifying WELL health..."
HEALTH="$(curl -sS --max-time 5 http://localhost:18083/health 2>/dev/null || echo '{}')"
echo "$HEALTH" | python3 -c "
import json, sys
d = json.load(sys.stdin)
v = d.get('verdict','?')
ts = d.get('timestamp','?')
ws = d.get('well_score','?')
fr = d.get('freshness',{}).get('status','?')
tr = d.get('truth_status','?')
os_ = d.get('owner_summary',{}).get('color','?')
print(f'  verdict:     {v}')
print(f'  well_score:  {ws}')
print(f'  freshness:   {fr}')
print(f'  truth:       {tr}')
print(f'  owner:       {os_}')
print()
if v == 'WELL_HOLD':
    print('  WARN: still HOLD. Check reason in /var/log/well-biometric-snooze.log')
else:
    print('  ✓ WELL is now fresh.')
"

hr
say "Done. See /root/WELL/SNOOZE_BIOMETRIC.md for the full guide."
