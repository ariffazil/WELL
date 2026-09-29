# WELL Intake Schema — Drop-based Biometric Ingestion

## Folders
- `voice/` — output from Hermes voice_state.py (auto-written)
- `manual/` — output from biometric_inject.sh (human-triggered)
- `cron/` — synthesized from logs (auto-written)
- `verbal/` — sovereign's own Telegram DM words, event-captured by
  `~/.hermes/hooks/state-intake-hook` (auto-written, zero-manual; F13 2026-09-29).
  Optional `provenance` block carries `evidence_class: SOVEREIGN_VERBAL_SELF_REPORT`;
  ingest stamps truth_status/honesty_banner accordingly.

## File Format (per ingest)
```json
{
  "ts": "ISO-8601 UTC",
  "source": "voice|manual|cron|verbal",
  "operator_id": "arif",
  "signals": {
    "speech_rate": float,
    "pause_density": float,
    "pitch_variance": float,
    ... (voice_state.py features)
  },
  "derived": {
    "fatigue": float (0-10, derived from pause_density),
    "energy": float (0-10, derived from speech_rate),
    "calm": float (0-10, derived from pitch_variance)
  },
  "confidence": "HIGH|MEDIUM|LOW",
  "raw_hash": "sha256 of source file"
}
```

## Processing
- `well_ingest.py` scans every 30 min
- Validates schema (required fields + types)
- Applies freshest-signal-wins policy (de-dupes by ts)
- Updates `/root/WELL/state.json` (additive, never destructive)
- Logs every ingest to `/root/WELL/data/intake_log.jsonl` (audit)
