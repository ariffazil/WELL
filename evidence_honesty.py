"""P0 EVIDENCE HONESTY — well-evidence-honesty/v1 (F13 order, 2026-10-15).

Hard invariants enforced here (from the P0 contract):
- UNMEASURED must never serialize as 0.
- UNKNOWN must never contribute as PASS.
- Missing evidence must never inherit a prior score.
- Task readiness must not imply system readiness.
- Executor success must not set recovery_verified.
- recovery_verified requires a valid independent observation receipt.
- No aggregate score may silently coerce null to zero.

Pure functions only — no I/O, no side effects. Importable without booting the
MCP server. Tests: tests/test_p0_evidence_honesty.py
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

CONTRACT_VERSION = "well-evidence-honesty/v1"

# A receipt older than this cannot verify recovery (24h).
DEFAULT_RECEIPT_MAX_AGE_SECONDS = 86400

# Fields every valid observation receipt must carry.
REQUIRED_RECEIPT_FIELDS = (
    "receipt_id",
    "observer",
    "observed_target",
    "observed_state_digest",
    "observed_at",
)


def unmeasured_metric(metric: str, reason: str) -> dict[str, Any]:
    """Canonical contract object for a metric that has NO measurement method.

    value is None — never 0. A consumer that needs a number must implement a
    measurement method first; silence is honest, a fabricated scalar is not.
    """
    return {
        "metric": metric,
        "value": None,
        "unit": None,
        "method": "unmeasured",
        "status": "UNKNOWN",
        "measured_at": None,
        "evidence_refs": [],
        "reason": reason,
        "contract": CONTRACT_VERSION,
    }


def aggregate_values(
    values: dict[str, Any] | list[Any],
    *,
    coverage_status_partial: str = "PARTIAL",
) -> dict[str, Any]:
    """Coverage-preserving aggregate. None is NEVER coerced to zero.

    Returns {"aggregate", "measured_dimensions", "total_dimensions",
             "coverage", "status"} where status is COMPLETE / PARTIAL /
    UNKNOWN. An aggregate over partial coverage is meaningless without its
    coverage number, so both are always returned together.
    """
    if isinstance(values, dict):
        items = list(values.values())
    else:
        items = list(values)

    measured = [v for v in items if v is not None]
    total = len(items)
    measured_n = len(measured)

    if measured_n == 0:
        return {
            "aggregate": None,
            "measured_dimensions": 0,
            "total_dimensions": total,
            "coverage": 0.0,
            "status": "UNKNOWN",
        }

    numeric = [
        v for v in measured if isinstance(v, (int, float)) and not isinstance(v, bool)
    ]
    if len(numeric) != measured_n:
        # Non-numeric measured values: no numeric aggregate exists.
        agg: float | None = None
    else:
        agg = round(sum(numeric) / len(numeric), 4)

    coverage = round(measured_n / total, 4) if total else 0.0
    status = "COMPLETE" if measured_n == total else coverage_status_partial

    return {
        "aggregate": agg,
        "measured_dimensions": measured_n,
        "total_dimensions": total,
        "coverage": coverage,
        "status": status,
    }


def task_scoped_readiness(
    task_id: str | None = None,
    task_class: str | None = None,
    checks: dict[str, list[str]] | None = None,
    *,
    evaluated_at: str | None = None,
) -> dict[str, Any]:
    """Readiness is readiness FOR a task. System metrics never imply it.

    Without task_id AND task_class the honest state is UNKNOWN — a universal
    readiness score is exactly the false completeness this contract forbids.
    """
    checks = checks or {}
    passed = list(checks.get("checks_passed", []))
    failed = list(checks.get("checks_failed", []))
    unknown = list(checks.get("checks_unknown", []))

    scope = task_id or task_class
    if not scope:
        return {
            "task_id": None,
            "task_class": None,
            "status": "UNKNOWN",
            "method": "task_scoped_checklist",
            "checks_passed": [],
            "checks_failed": [],
            "checks_unknown": [],
            "evaluated_at": evaluated_at,
            "reason": (
                "No task scope supplied -- system metrics do not imply task "
                "readiness. Pass task_id or task_class."
            ),
            "contract": CONTRACT_VERSION,
        }

    if failed:
        status = "NOT_READY"
    elif unknown and not passed:
        status = "UNKNOWN"
    elif unknown:
        status = "PARTIAL"
    elif passed:
        status = "READY"
    else:
        status = "UNKNOWN"

    return {
        "task_id": task_id,
        "task_class": task_class,
        "status": status,
        "method": "task_scoped_checklist",
        "checks_passed": passed,
        "checks_failed": failed,
        "checks_unknown": unknown,
        "evaluated_at": evaluated_at,
        "reason": None if status != "UNKNOWN" else "No checks were evaluated.",
        "contract": CONTRACT_VERSION,
    }


def _parse_ts(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        ts = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts


def verify_recovery_receipt(
    receipt: Any,
    *,
    target: str,
    now_ts: str | None = None,
    expected_digest: str | None = None,
    max_age_seconds: float = DEFAULT_RECEIPT_MAX_AGE_SECONDS,
) -> dict[str, Any]:
    """recovery_verified=true requires a valid INDEPENDENT observation receipt.

    An executor response — including one that says "success" — can never set
    this flag. Missing, malformed, stale, wrong-target and self-witnessed
    receipts all return verified=False with an explicit reason.
    """
    base = {
        "recovery_verified": False,
        "recovery_receipt_ref": None,
        "observed_state_digest": None,
        "verified_by": None,
        "verified_at": None,
        "reason": None,
        "contract": CONTRACT_VERSION,
    }

    if receipt is None:
        base["reason"] = "missing_receipt"
        return base
    if not isinstance(receipt, dict):
        base["reason"] = "malformed_receipt"
        return base
    missing = [f for f in REQUIRED_RECEIPT_FIELDS if not receipt.get(f)]
    if missing:
        # A bare executor success payload lands here: no observer, no digest.
        base["reason"] = "malformed_receipt"
        return base

    observer = str(receipt.get("observer") or "")
    executor = str(receipt.get("executor") or "")
    if observer and executor and observer == executor:
        base["reason"] = "executor_self_witness"
        return base
    if str(receipt.get("observer_role") or "").lower() == "executor":
        base["reason"] = "executor_self_witness"
        return base

    if str(receipt.get("observed_target")) != str(target):
        base["reason"] = "wrong_target"
        return base

    observed_at = _parse_ts(receipt.get("observed_at"))
    now = _parse_ts(now_ts) if now_ts else datetime.now(timezone.utc)
    if observed_at is None or now is None:
        base["reason"] = "malformed_receipt"
        return base
    if (now - observed_at).total_seconds() > max_age_seconds:
        base["reason"] = "stale_receipt"
        return base

    digest = str(receipt.get("observed_state_digest"))
    if expected_digest is not None and digest != str(expected_digest):
        base["reason"] = "digest_mismatch"
        return base

    base.update(
        {
            "recovery_verified": True,
            "recovery_receipt_ref": str(receipt.get("receipt_id")),
            "observed_state_digest": digest,
            "verified_by": observer,
            "verified_at": str(receipt.get("observed_at")),
            "reason": "independent_observation_receipt_valid",
        }
    )
    return base
