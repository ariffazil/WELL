"""WELL::OBSERVATION_CONTRACT::v1 — Subject-bound, provenance-carrying observations.

Forged 2026-10-15 (AUTHORITY: ARIF). Additive; first consumer is
well_assess_homeostasis(mode="readiness", readiness_inputs.observations=[...]).

Design rules (from external audit acceptance gates, verified 2026-10-15):
  - No observation may be interpreted without identity, provenance and time.
  - Absent data must carry an explicit missing_reason — never a default value.
  - provenance ∈ {measured, self_reported} — a self-report is never rendered
    as a sensor reading downstream.
  - Subject binding: an observation belongs to exactly one subject_id; readiness
    responses echo the subject so cross-person inheritance is visible.

Pure functions; no I/O; no state.json. FHIR Observation used as shape
reference (subject, effectiveDateTime, dataAbsentReason), not as a dependency.
"""

from __future__ import annotations

import datetime as _dt
import re as _re
from typing import Any

REQUIRED_FIELDS = (
    "subject_id",
    "measurement",
    "unit",
    "observed_at",
    "source",
    "provenance",
)
VALID_PROVENANCE = ("measured", "self_reported")
_ISO_RE = _re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}")


def _parse_ts(value: Any) -> _dt.datetime | None:
    if not isinstance(value, str) or not _ISO_RE.match(value):
        return None
    try:
        return _dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def validate_observation(obs: Any, expected_subject: str | None = None) -> dict[str, Any]:
    """Validate one observation dict. Returns {valid, errors, ...} — never raises."""
    if not isinstance(obs, dict):
        return {"valid": False, "errors": ["not_a_dict"]}
    errors: list[str] = []

    missing = [f for f in REQUIRED_FIELDS if obs.get(f) in (None, "")]
    if missing:
        errors.append(f"missing_fields:{','.join(missing)}")

    subject_id = obs.get("subject_id")
    if expected_subject and subject_id and subject_id != expected_subject:
        errors.append(f"subject_mismatch:{subject_id}!={expected_subject}")

    prov = obs.get("provenance")
    if prov is not None and prov not in VALID_PROVENANCE:
        errors.append(f"provenance_invalid:{prov}")

    value = obs.get("value")
    if value is None:
        # Absent data is legal ONLY with an explicit reason (FHIR dataAbsentReason).
        if not obs.get("missing_reason"):
            errors.append("absent_value_needs_missing_reason")
    elif not isinstance(value, (int, float)) or isinstance(value, bool):
        errors.append("value_not_numeric")

    ts = _parse_ts(obs.get("observed_at"))
    if obs.get("observed_at") and ts is None:
        errors.append("observed_at_not_iso")

    quality = obs.get("quality")
    if quality is not None:
        if isinstance(quality, bool) or not isinstance(quality, (int, float)) or not (0.0 <= float(quality) <= 1.0):
            errors.append("quality_not_0_1")

    result: dict[str, Any] = {"valid": not errors, "errors": errors}
    if ts is not None:
        age_h = (_dt.datetime.now(_dt.timezone.utc) - ts).total_seconds() / 3600.0
        result["age_hours"] = round(age_h, 2)
        result["stale"] = age_h > 24.0  # WELL freshness law: >24h = STALE_MIRROR
    return result


def validate_batch(observations: Any, expected_subject: str | None = None) -> dict[str, Any]:
    """Validate a list. Returns accepted/rejected split with per-item reasons.
    Invalid observations are NEVER silently dropped — they are reported."""
    if observations is None:
        return {"accepted": [], "rejected": [], "n_total": 0}
    if not isinstance(observations, list):
        return {
            "accepted": [],
            "rejected": [{"error": "observations_not_a_list"}],
            "n_total": 0,
        }
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for obs in observations:
        check = validate_observation(obs, expected_subject)
        if check["valid"]:
            accepted.append({**obs, "_contract": check})
        else:
            rejected.append({
                "measurement": obs.get("measurement") if isinstance(obs, dict) else None,
                "errors": check["errors"],
            })
    return {"accepted": accepted, "rejected": rejected, "n_total": len(observations)}


def observations_summary(batch_result: dict[str, Any]) -> dict[str, Any]:
    """Compact summary for embedding in a readiness response. Provenance-aware:
    measured vs self_reported are counted separately and never merged."""
    acc = batch_result.get("accepted", [])
    measured = [a for a in acc if a.get("provenance") == "measured"]
    self_reported = [a for a in acc if a.get("provenance") == "self_reported"]
    stale = [a for a in acc if a.get("_contract", {}).get("stale")]
    return {
        "n_accepted": len(acc),
        "n_rejected": len(batch_result.get("rejected", [])),
        "n_measured": len(measured),
        "n_self_reported": len(self_reported),
        "n_stale_gt24h": len(stale),
        "rejected_detail": batch_result.get("rejected", []),
        "subject_ids": sorted({a.get("subject_id") for a in acc if a.get("subject_id")}),
    }
