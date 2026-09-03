---
id: well-consent-registry
name: WELL Consent Registry Protocol
version: 1.0.0
description: WELL consent scope registry protocol — sovereign's exclusive read + Hermes-gated write. USE WHEN: 'consent audit', 'grant scope', 'revoke scope', 'biometric consent', 'which scopes are active'. Covers: well_consent_audit (read scope registry — sovereign's right, no F11 gate, include_revoked flag) -> well_consent_set_scope (grant/revoke — Hermes ONLY via HERMES_HERMETIC_TOKEN, mutates ONLY F11 scope registry in state.json, NEVER verdict/floor state) -> scope ids used by well_inject_biometric (biometric.full, default OFF), well_log_intake (intake.basic / intake.location), well_log_recovery_event (recovery.basic), well_log_substance (substance.full, default OFF). Iron rules: consent scopes default OFF — operator must opt in via Hermes; scope changes are F11-governed and logged; WELL never infers consent from silence; revoked scopes must appear in audit history (include_revoked=true), never silently forgotten.
owner: 333-AGI
risk_tier: medium
floor_scope: [F1, F4, F11, F13]
autonomy_tier: T1
organ_domain: well
forged: 2026-09-04
---

# WELL Consent Registry Protocol

WELL consent scope registry protocol — sovereign's exclusive read + Hermes-gated write. USE WHEN: 'consent audit', 'grant scope', 'revoke scope', 'biometric consent', 'which scopes are active'. Covers: well_consent_audit (read scope registry — sovereign's right, no F11 gate, include_revoked flag) -> well_consent_set_scope (grant/revoke — Hermes ONLY via HERMES_HERMETIC_TOKEN, mutates ONLY F11 scope registry in state.json, NEVER verdict/floor state) -> scope ids used by well_inject_biometric (biometric.full, default OFF), well_log_intake (intake.basic / intake.location), well_log_recovery_event (recovery.basic), well_log_substance (substance.full, default OFF). Iron rules: consent scopes default OFF — operator must opt in via Hermes; scope changes are F11-governed and logged; WELL never infers consent from silence; revoked scopes must appear in audit history (include_revoked=true), never silently forgotten.

## Provenance

Forged 2026-09-04 by 333-AGI (session SEAL-83defc585b5a4296) per 888-APEX priority-gap verdict. When skill and tool surface disagree, the tool surface wins.
