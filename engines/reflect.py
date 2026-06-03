# WELL MCP — Reflect-Only Boundary Module
# PR 6: Enforce reflect-only language across all 13 canonical SOMATIC_TOOLS.
#
# Doctrine (F1 AMANAH, F2 TRUTH, F7 STEWARDSHIP, F9/F10 ONTOLOGY, F13 SOVEREIGN):
#   - WELL reflects. arifOS arbitrates. Never the reverse.
#   - Every WELL output carries 4 labels: telemetry, context, authority, medical_status.
#   - WELL never diagnoses. medical_status is always "not_diagnosis".
#   - WELL never authorizes action. authority is always "advisory_only".
#   - No readiness score without a context tag sufficient to ground it.
#
# Floor map:
#   F1 AMANAH     — state.json is sovereign biometric data; every label is
#                   computed from observable state, not inferred beyond what
#                   the data shows.
#   F2 TRUTH      — disclaimers are facts. "not_diagnosis" is a fact.
#   F7 STEWARDSHIP — never emit a readiness score on insufficient context.
#   F9 SOFT→HARD  — no consciousness claims. The body is a substrate, not a mind.
#   F10 ONTOLOGY  — biometric data is observation, not the person. WELL observes.
#   F13 SOVEREIGN  — this module labels authority; it does not grant it.
#
# SPEAR: DITEMPA BUKAN DIBERI — Forged, Not Given.

from __future__ import annotations

import functools
import inspect
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

log = logging.getLogger("well.reflect")

# ─── AUTHORITY CONSTANTS ─────────────────────────────────────────────────
# These are the only two authority values a WELL tool may emit. arifOS
# alone holds EXECUTION_AUTHORITY; WELL holds only REFLECT_ONLY.

AUTHORITY_REFLECT_ONLY: str = "advisory_only"
"""WELL is REFLECT_ONLY. Every output bears this label. WELL never grants
execution authority. arifOS 888_JUDGE holds the only execution authorization
that a decision can be acted on."""

MEDICAL_NOT_DIAGNOSIS: str = "not_diagnosis"
"""WELL is not a medical authority. Every output bears this label. WELL
never diagnoses, prescribes, or substitutes for a licensed professional."""

# ─── VALID VALUE SETS ────────────────────────────────────────────────────

TELEMETRY_VALUES: tuple = ("live", "manual", "synthetic", "unavailable")
"""Source of the biometric signal:
- live: verified telemetry with fresh timestamp (< 1h)
- manual: self-reported metrics (no sensor) — H-WELL default today
- synthetic: state explicitly marked synthetic (test/seed data)
- unavailable: state is empty, expired, or absent
"""

CONTEXT_VALUES: tuple = ("sufficient", "insufficient")
"""Whether the state carries enough information to ground a view:
- sufficient: state has metrics + timestamp + identity
- insufficient: any of those missing or stale beyond 168h ceiling
"""

MEDICAL_VALUES: tuple = (MEDICAL_NOT_DIAGNOSIS, "diagnostic_suggestion")
"""WELL only ever emits 'not_diagnosis'. 'diagnostic_suggestion' is reserved
for future clinical-integration work and is NEVER emitted by canonical
WELL tools in this forge. Existence of the constant is for completeness
of the value set; the canonical path always returns 'not_diagnosis'."""


# ─── DETECTION HELPERS ───────────────────────────────────────────────────

# Thresholds in hours. The 168h (7-day) hard ceiling is the existing
# WELL readiness ceiling. Anything older is insufficient.
_FRESH_HOURS: float = 1.0
_STALE_HOURS: float = 168.0


def _state_age_hours(state: Dict[str, Any]) -> Optional[float]:
    """Compute the age of `state` in hours from its `timestamp` field.

    F2-honest: if the timestamp is missing or unparseable, return None.
    """
    if not isinstance(state, dict):
        return None
    ts = state.get("timestamp") or state.get("ts") or state.get("updated_at")
    if not ts:
        return None
    try:
        if isinstance(ts, (int, float)):
            return max(0.0, (datetime.now(timezone.utc).timestamp() - float(ts)) / 3600.0)
        if isinstance(ts, str):
            s = ts.replace("Z", "+00:00")
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return max(0.0, (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0)
    except (ValueError, TypeError):
        return None
    return None


def detect_telemetry_status(state: Optional[Dict[str, Any]]) -> str:
    """Return the telemetry source classification.

    F1: observable only. We never claim a sensor is reading the body; we
    only report what the state object says.
    """
    if not isinstance(state, dict) or not state:
        return "unavailable"

    # Synthetic flag wins if explicitly set.
    if state.get("synthetic") is True or state.get("telemetry_source") == "synthetic":
        return "synthetic"

    # Live requires a fresh timestamp and verified_metrics marker.
    age = _state_age_hours(state)
    if age is not None and age < _FRESH_HOURS and state.get("verified_metrics"):
        return "live"

    # Manual covers self-reported (H-WELL default).
    if state.get("source") == "self_report" or state.get("telemetry_source") == "manual":
        return "manual"

    # State has a timestamp within 168h but no verified_metrics — partial,
    # classified as manual (self-reported, awaiting verification).
    if age is not None and age < _STALE_HOURS and state.get("metrics"):
        return "manual"

    # Stale or empty.
    return "unavailable"


def detect_context_status(state: Optional[Dict[str, Any]]) -> str:
    """Return the context sufficiency classification.

    F7: never emit a readiness score on insufficient context.
    """
    if not isinstance(state, dict) or not state:
        return "insufficient"

    has_metrics = bool(state.get("metrics"))
    has_timestamp = _state_age_hours(state) is not None
    has_identity = bool(state.get("identity")) or bool(state.get("subject_id"))

    if not (has_metrics and has_timestamp and has_identity):
        return "insufficient"

    age = _state_age_hours(state) or 0.0
    if age > _STALE_HOURS:
        return "insufficient"

    return "sufficient"


def detect_authority_status() -> str:
    """WELL is REFLECT_ONLY. This is a constant, not a detection.

    F13: the authority label is fixed by constitution; it does not change
    based on input. arifOS holds the only execution authorization.
    """
    return AUTHORITY_REFLECT_ONLY


def detect_medical_status() -> str:
    """WELL is not a medical authority. This is a constant, not a detection.

    F2: the medical_status label is fixed by constitution; it does not
    change based on input. Diagnosis requires a licensed human.
    """
    return MEDICAL_NOT_DIAGNOSIS


# ─── REFLECT BOUNDARY COMPUTATION ────────────────────────────────────────

REFLECT_DISCLAIMER: str = (
    "WELL output is reflect-only. authority=advisory_only. medical_status=not_diagnosis. "
    "WELL never authorizes action; arifOS arbitrates. WELL never diagnoses; "
    "consult a licensed professional for medical questions."
)


def compute_reflect_boundary(
    state: Optional[Dict[str, Any]] = None,
) -> Dict[str, str]:
    """Compute the 4 reflect-only fields that must accompany every WELL
    canonical tool output.

    Returns a dict with:
      - telemetry: live | manual | synthetic | unavailable
      - context: sufficient | insufficient
      - authority: always "advisory_only"
      - medical_status: always "not_diagnosis"
      - reflect_disclaimer: 1-line F2-honest disclaimer

    F1 AMANAH: every field is computed from observable state.
    F13 SOVEREIGN: this function labels authority; it does not grant it.
    """
    return {
        "telemetry": detect_telemetry_status(state),
        "context": detect_context_status(state),
        "authority": detect_authority_status(),
        "medical_status": detect_medical_status(),
        "reflect_disclaimer": REFLECT_DISCLAIMER,
    }


# ─── READINESS GUARD (F7) ───────────────────────────────────────────────
# If a tool emits a readiness score on insufficient context, the guard
# strips the score and replaces it with a HOLD. The honest path is to
# refuse to score what we cannot ground.

_READINESS_KEYS: tuple = (
    "readiness",
    "readiness_score",
    "readiness_band",
    "well_score",
    "score",
)


def _apply_readiness_guard(
    result: Dict[str, Any],
    context_status: str,
) -> Dict[str, Any]:
    """If context is insufficient, strip readiness scores and replace with HOLD.

    F7 STEWARDSHIP: a readiness score on insufficient context is a fabrication.
    The honest path is HOLD.
    """
    if context_status == "sufficient" or not isinstance(result, dict):
        return result

    for k in _READINESS_KEYS:
        if k in result:
            original = result[k]
            result[k] = "HOLD"
            log.info(
                "F7 readiness guard: stripped %s=%r on insufficient context, replaced with HOLD",
                k,
                original,
            )
    return result


# ─── DECORATOR ──────────────────────────────────────────────────────────


def reflect_only_boundary(
    fn: Callable[..., Any],
) -> Callable[..., Any]:
    """Decorator that wraps a WELL tool to inject the 4 reflect-only labels.

    The decorator:
      1. Calls the wrapped function.
      2. Loads the current state (if available) for telemetry/context detection.
      3. Computes the reflect boundary.
      4. Injects the 4 labels + disclaimer into the returned dict.
      5. Applies the F7 readiness guard if context is insufficient.
      6. Preserves the original return value (additive only).

    F1: state.json is sovereign biometric data. The decorator reads it
        via a lazy import of server._load_state() to avoid import cycles.
    F2: additive only. No field removed from the original return.
    F13: this decorator labels authority; it does not grant it.
    """

    @functools.wraps(fn)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        result = await fn(*args, **kwargs)
        return _inject_boundary(result)

    @functools.wraps(fn)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        result = fn(*args, **kwargs)
        return _inject_boundary(result)

    # Pick the right wrapper based on the wrapped function's coroutine-ness.
    if inspect.iscoroutinefunction(fn):
        return async_wrapper
    return sync_wrapper


def _inject_boundary(result: Any) -> Any:
    """Inject the 4 reflect-only labels into a tool result (additive)."""
    if not isinstance(result, dict):
        return result

    # Lazy state load to avoid import cycles.
    state: Optional[Dict[str, Any]] = None
    try:
        from server import _load_state  # type: ignore[import-not-found]

        state = _load_state()
    except Exception:  # pragma: no cover — defensive only
        state = None

    boundary = compute_reflect_boundary(state)
    result["telemetry"] = boundary["telemetry"]
    result["context"] = boundary["context"]
    result["authority"] = boundary["authority"]
    result["medical_status"] = boundary["medical_status"]
    result["reflect_disclaimer"] = boundary["reflect_disclaimer"]

    # F7 readiness guard: strip readiness scores on insufficient context.
    return _apply_readiness_guard(result, boundary["context"])


__all__ = [
    "AUTHORITY_REFLECT_ONLY",
    "MEDICAL_NOT_DIAGNOSIS",
    "TELEMETRY_VALUES",
    "CONTEXT_VALUES",
    "MEDICAL_VALUES",
    "REFLECT_DISCLAIMER",
    "compute_reflect_boundary",
    "detect_authority_status",
    "detect_context_status",
    "detect_medical_status",
    "detect_telemetry_status",
    "reflect_only_boundary",
    "wrap_canonical_tools",
]


# ─── CANONICAL TOOL POST-WRAP ────────────────────────────────────────────
# Helper for server.py to apply the reflect-only boundary to the 13
# canonical SOMATIC_TOOLS at module load time. Avoids 13 individual
# decorator edits.

def wrap_canonical_tools(
    tools_dict: Dict[str, Any],
    canonical_names: Any = None,
) -> int:
    """Wrap each canonical tool's function with @reflect_only_boundary.

    Parameters
    ----------
    tools_dict : dict
        Mapping of tool name → function. The WellMCP server's tool
        registry can be passed here, or any local dict of name→fn.
    canonical_names : iterable, optional
        Names to wrap. If None, the wrapping is a no-op and the caller
        is expected to pass an explicit list.

    Returns
    -------
    int
        Number of tools actually wrapped.

    F1: additive. Does not change return semantics; only injects 4 labels.
    F13: this wraps with a label-injector; it does not grant authority.
    """
    if canonical_names is None:
        return 0

    count = 0
    for name in canonical_names:
        fn = tools_dict.get(name)
        if fn is None:
            log.debug("wrap_canonical_tools: %s not in tools_dict", name)
            continue
        if getattr(fn, "_reflect_wrapped", False):
            continue  # already wrapped (idempotent)
        wrapped = reflect_only_boundary(fn)
        wrapped._reflect_wrapped = True  # type: ignore[attr-defined]
        tools_dict[name] = wrapped
        count += 1
    return count
