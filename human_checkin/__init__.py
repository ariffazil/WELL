"""WELL::HUMAN_CHECKIN::v1 — Sovereign presence intake (P0).

Ratified by F13 (Arif) 2026-11-19: three-field check-in as event-based
intake. NOT a shortcut to well_score. NOT biometric_inject.sh.

Rules (F13 design, 2026-11-19):
  - Three inputs only: sleep_hours, energy (1-10), load (1-10).
  - No clarity field. Clarity stays UNKNOWN until Arif states it.
    Never derive clarity from energy or load.
  - Every field is its own observation: own timestamp, own provenance
    (SELF_REPORT), own freshness, own missing_reason.
  - No synthesis of well_score. No derivation of missing variables.
  - Append-only event log; atomic projection; NO service restart.
  - Idempotent on duplicate submissions.
  - A check-in can NEVER set has_verified_telemetry=true.
"""
