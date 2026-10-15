"""P0 EVIDENCE HONESTY — acceptance + regression tests (F13 STAGE A, 2026-10-15).

Covers the P0 contract acceptance list:
- delta_S / evidence_quality return null + method=unmeasured (source guard)
- UNMEASURED never serializes as 0
- UNKNOWN never contributes as PASS
- aggregator preserves measurement coverage (None is not zero)
- readiness requires task_id or task_class
- recovery_verified cannot be set by executor response
- missing / malformed / stale / wrong-target receipt keeps recovery_verified false
- existing envelope keys preserved (versioned contract, consumer compatible)

Run: cd /root/WELL && PYTHONPATH=. .venv/bin/python3 -m pytest tests/test_p0_evidence_honesty.py -q
"""

from __future__ import annotations

import json
from pathlib import Path

from evidence_honesty import (
    CONTRACT_VERSION,
    aggregate_values,
    task_scoped_readiness,
    unmeasured_metric,
    verify_recovery_receipt,
)

ROOT = Path(__file__).resolve().parent.parent

NOW = "2026-10-15T12:00:00+00:00"


def _receipt(**over):
    receipt = {
        "receipt_id": "rcpt-001",
        "observer": "FRAME",
        "observer_role": "observer",
        "executor": "A-FORGE",
        "observed_target": "svc:well",
        "observed_state_digest": "sha256:abc",
        "observed_at": "2026-10-15T11:00:00+00:00",
    }
    receipt.update(over)
    return receipt


# ── 1. UNMEASURED must never serialize as 0 ──────────────────────────────────


def test_unmeasured_metric_value_is_null_not_zero():
    m = unmeasured_metric("delta_S", "No operational measurement method.")
    assert m["value"] is None
    assert m["value"] != 0
    assert m["method"] == "unmeasured"
    assert m["status"] == "UNKNOWN"
    assert m["contract"] == CONTRACT_VERSION


def test_unmeasured_metric_survives_json_roundtrip_as_null():
    m = unmeasured_metric("evidence_quality", "No calibrated model.")
    roundtrip = json.loads(json.dumps(m))
    assert roundtrip["value"] is None
    assert roundtrip["value"] != 0


# ── 2. Aggregator: None is not zero; coverage always exposed ─────────────────


def test_aggregate_none_is_not_zero():
    agg = aggregate_values([None, 0.8])
    assert agg["aggregate"] != 0.4  # the critical regression
    assert agg["coverage"] == 0.5
    assert agg["measured_dimensions"] == 1
    assert agg["total_dimensions"] == 2
    assert agg["status"] == "PARTIAL"


def test_aggregate_all_none_is_unknown():
    agg = aggregate_values([None, None])
    assert agg["aggregate"] is None
    assert agg["status"] == "UNKNOWN"
    assert agg["coverage"] == 0.0


def test_aggregate_complete_and_mean():
    agg = aggregate_values({"a": 1.0, "b": 2.0})
    assert agg["aggregate"] == 1.5
    assert agg["status"] == "COMPLETE"
    assert agg["coverage"] == 1.0


def test_missing_evidence_never_inherits_prior_score():
    agg = aggregate_values({"a": None, "b": None})
    assert agg["aggregate"] is None
    assert agg["aggregate"] != 0.0


# ── 3. Readiness is task-scoped ──────────────────────────────────────────────


def test_readiness_requires_task_scope():
    r = task_scoped_readiness()
    assert r["status"] == "UNKNOWN"
    assert r["task_id"] is None and r["task_class"] is None
    assert "task" in (r["reason"] or "").lower()


def test_readiness_with_task_scope():
    r = task_scoped_readiness("recovery:well", checks={"checks_passed": ["svc_up"]})
    assert r["task_id"] == "recovery:well"
    assert r["status"] == "READY"
    assert r["method"] == "task_scoped_checklist"


def test_readiness_failed_check_is_not_ready():
    r = task_scoped_readiness(
        task_class="inference",
        checks={"checks_failed": ["vram"], "checks_passed": ["cpu"]},
    )
    assert r["status"] == "NOT_READY"


def test_readiness_unknown_checks_do_not_pass():
    r = task_scoped_readiness(
        "job-1", checks={"checks_unknown": ["workload_limits_not_supplied"]}
    )
    # UNKNOWN must never contribute as PASS
    assert r["status"] != "READY"
    assert r["status"] == "UNKNOWN"


def test_readiness_partial_when_mixed():
    r = task_scoped_readiness(
        "job-2", checks={"checks_passed": ["cpu"], "checks_unknown": ["disk"]}
    )
    assert r["status"] == "PARTIAL"


# ── 4. recovery_verified requires a valid independent receipt ────────────────


def test_recovery_missing_receipt():
    r = verify_recovery_receipt(None, target="svc:well", now_ts=NOW)
    assert r["recovery_verified"] is False
    assert r["reason"] == "missing_receipt"
    assert r["recovery_receipt_ref"] is None


def test_executor_success_cannot_set_recovery():
    # An executor "success" payload has no observer/digest -> never verifies.
    r = verify_recovery_receipt(
        {"status": "success", "executor": "A-FORGE"}, target="svc:well", now_ts=NOW
    )
    assert r["recovery_verified"] is False
    assert r["reason"] == "malformed_receipt"


def test_malformed_receipt():
    r = verify_recovery_receipt(
        {"receipt_id": "x", "observer": "FRAME"},  # missing target/digest/time
        target="svc:well",
        now_ts=NOW,
    )
    assert r["recovery_verified"] is False
    assert r["reason"] == "malformed_receipt"


def test_stale_receipt():
    r = verify_recovery_receipt(
        _receipt(observed_at="2026-10-13T10:00:00+00:00"),  # 49h old
        target="svc:well",
        now_ts=NOW,
    )
    assert r["recovery_verified"] is False
    assert r["reason"] == "stale_receipt"


def test_wrong_target_receipt():
    r = verify_recovery_receipt(
        _receipt(observed_target="svc:geox"), target="svc:well", now_ts=NOW
    )
    assert r["recovery_verified"] is False
    assert r["reason"] == "wrong_target"


def test_executor_self_witness_rejected():
    r = verify_recovery_receipt(
        _receipt(observer="A-FORGE"), target="svc:well", now_ts=NOW
    )
    assert r["recovery_verified"] is False
    assert r["reason"] == "executor_self_witness"

    r2 = verify_recovery_receipt(
        _receipt(observer="someone", observer_role="executor"),
        target="svc:well",
        now_ts=NOW,
    )
    assert r2["recovery_verified"] is False
    assert r2["reason"] == "executor_self_witness"


def test_digest_mismatch():
    r = verify_recovery_receipt(
        _receipt(), target="svc:well", now_ts=NOW, expected_digest="sha256:zzz"
    )
    assert r["recovery_verified"] is False
    assert r["reason"] == "digest_mismatch"


def test_valid_independent_receipt_verifies():
    r = verify_recovery_receipt(_receipt(), target="svc:well", now_ts=NOW)
    assert r["recovery_verified"] is True
    assert r["recovery_receipt_ref"] == "rcpt-001"
    assert r["verified_by"] == "FRAME"
    assert r["observed_state_digest"] == "sha256:abc"


# ── 5. Source regression guards (fabrication must not return) ────────────────


def test_no_fake_delta_s_formula_in_server():
    src = (ROOT / "server.py").read_text()
    assert "0.05 * float(has_error)" not in src
    assert "# delta_S: heuristic" not in src
    assert "delta_S" in src  # key preserved for consumers
    assert '"delta_S": None' in src or '"delta_S": delta_s' in src


def test_no_fake_evidence_quality_scalar_in_server():
    src = (ROOT / "server.py").read_text()
    assert "quality = max(0.05, 1.0 - uncertainty)" not in src
    assert 'conformance_version": "v1.1' in src
    # The ENVELOPE (the fabricated site) must emit null, not a scalar.
    # The rubric-based categorical in well_evidence_quality_check is allowed.
    anchor = src.index('"epistemic_tag": tag,')
    region = src[anchor : anchor + 1200]
    assert '"evidence_quality": None' in region
    assert '"evidence_quality": quality' not in region


def test_no_confidence_mislabelled_as_evidence_quality():
    src = (ROOT / "loop" / "readiness_envelope.py").read_text()
    # The old default mislabelled confidence as evidence_quality. Gone.
    assert 'evidence_quality":evidence_quality' not in src.replace(" ", "")
    assert '"evidence_quality": None' in src
    assert '"evidence_quality_metric"' in src
    assert "well-evidence-honesty/v1" in src


# ── 6. Backward compatibility: envelope keys preserved, contract versioned ──


def test_envelope_keys_preserved_for_consumers():
    src = (ROOT / "server.py").read_text()
    # Consumers still find the keys (now null-valued) and can read the contract.
    assert '"evidence_quality_metric"' in src
    assert '"delta_S_metric"' in src
    assert '"evidence_contract": "well-evidence-honesty/v1"' in src
