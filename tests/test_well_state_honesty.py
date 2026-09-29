"""
WELL State Honesty Tests
════════════════════════

Verify that WELL never pretends to know the sovereign's biological state
when it is reading fixtures, test data, or missing telemetry.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from server import (
    _classify_well_state,
    _state_is_insufficient,
    _assert_sovereign_presence,
    _load_state,
)


# ── 1. Mocked/test state is classified as insufficient ────────────────────────


def test_mocked_test_state_is_insufficient():
    state = {
        "timestamp": "2026-04-30T00:00:00+00:00",
        "operator_id": "arif",
        "metrics": {"cognitive": {"clarity": 10}},
        "well_score": 92.2,
        "truth_status": "TEST",
        "environment": "TEST",
        "reason": "Mocked healthy state for test session",
    }
    insufficient, reasons = _state_is_insufficient(state)
    assert insufficient is True
    assert any("truth_status:TEST" in r for r in reasons)
    assert any("environment:TEST" in r for r in reasons)
    assert any("mocked_state" in r for r in reasons)


def test_missing_identity_is_insufficient():
    state = {
        "timestamp": "2026-06-15T12:00:00+00:00",
        "metrics": {"cognitive": {"clarity": 10}},
        "truth_status": "VERIFIED",
        "environment": "PROD",
    }
    insufficient, reasons = _state_is_insufficient(state)
    assert insufficient is True
    assert any("identity_invalid" in r for r in reasons)


def test_no_telemetry_is_insufficient():
    state = {
        "timestamp": "2026-06-15T12:00:00+00:00",
        "operator_id": "arif",
        "identity": "WELL",
        "role": "Body / Human Intelligence",
        "authority": "REFLECT_ONLY",
        "metrics": {},
        "truth_status": "UNVERIFIED",
        "environment": "PROD",
    }
    insufficient, reasons = _state_is_insufficient(state)
    assert insufficient is True
    assert any("no_verified_telemetry" in r for r in reasons)


# ── 2. Classification converts insufficient state to honest health payload ────


def test_classify_mocked_state_returns_insufficient_data():
    state = {
        "timestamp": "2026-04-30T00:00:00+00:00",
        "operator_id": "arif",
        "metrics": {"cognitive": {"clarity": 10}},
        "well_score": 92.2,
        "truth_status": "TEST",
        "environment": "TEST",
        "reason": "Mocked healthy state for test session",
    }
    classification = _classify_well_state(state)
    assert classification["truth_status"] == "INSUFFICIENT_DATA"
    assert classification["well_signal"] == "WELL_HOLD"
    assert classification["well_score"] is None
    assert classification["owner_summary"]["color"] == "RED"
    assert "sovereign_state_unknown" in classification["owner_summary"]["reasons"]
    # D1 (HRFID-20260929): the band is now the configured arithmetic — fresh ≤ 3600s,
    # stale ≤ 14400s, expired beyond. A 5-month-old file write is EXPIRED, not the old
    # catch-all "STALE" name the pre-fix ladder produced for it.
    assert classification["freshness_band"] == "EXPIRED"
    assert classification["freshness"]["status"] == "expired"
    assert classification["honesty"]["is_stale"] is True


def test_classify_operator_reported_state_is_not_insufficient():
    state = {
        "timestamp": "2026-06-15T12:00:00+00:00",
        "operator_id": "arif",
        "identity": "WELL",
        "role": "Body / Human Intelligence",
        "authority": "REFLECT_ONLY",
        "delta_s": 0.0,
        "peace2": 1.0,
        "kappa_r": 0.95,
        "rasa": True,
        "amanah": "LOCK",
        "metrics": {},
        "truth_status": "OPERATOR_REPORTED",
        "environment": "PROD",
        "reason": "Sovereign presence asserted manually via /ready",
    }
    classification = _classify_well_state(state)
    assert classification["insufficient"] is False
    assert classification["truth_status"] == "OPERATOR_REPORTED"
    assert classification["well_signal"] == "WELL_OPERATOR_PRESENT"
    assert classification["owner_summary"]["color"] == "YELLOW"


# ── 3. /ready assertion writes honest OPERATOR_REPORTED state ─────────────────


def test_assert_sovereign_presence_writes_operator_reported(monkeypatch, tmp_path):
    state_path = tmp_path / "state.json"
    events_path = tmp_path / "events.jsonl"

    monkeypatch.setattr("server.STATE_PATH", state_path)
    monkeypatch.setattr("server.EVENTS_PATH", events_path)

    result = _assert_sovereign_presence(operator_id="arif")
    assert result["ok"] is True
    assert result["truth_status"] == "OPERATOR_REPORTED"

    state = json.loads(state_path.read_text())
    assert state["truth_status"] == "OPERATOR_REPORTED"
    assert state["environment"] == "PROD"
    assert state["operator_id"] == "arif"
    assert state["reason"].startswith("Sovereign presence asserted")

    # Events should be appended
    events = events_path.read_text().strip().split("\n")
    assert len(events) == 1
    event = json.loads(events[0])
    assert event["event"] == "SOVEREIGN_PRESENCE_ASSERTED"


def test_autouse_fixture_preserves_production_state():
    """A write-capable call must use the per-test paths from conftest."""
    import server

    production_state_path = ROOT / "state.json"
    if not production_state_path.exists():
        pytest.skip("production state.json not present on this host (CI / fresh clone)")
    production_events_path = ROOT / "events.jsonl"
    state_before = production_state_path.read_bytes()
    state_mtime_before = production_state_path.stat().st_mtime_ns

    assert server.STATE_PATH != production_state_path
    assert server.EVENTS_PATH != production_events_path

    result = _assert_sovereign_presence(operator_id="arif")

    assert result["ok"] is True
    assert server.STATE_PATH.exists()
    assert server.EVENTS_PATH.exists()
    assert production_state_path.read_bytes() == state_before
    assert production_state_path.stat().st_mtime_ns == state_mtime_before


# ── 4. Default missing-state payload is honest, not a fabricated score ────────


def test_load_state_default_is_honest(monkeypatch, tmp_path):
    state_path = tmp_path / "nonexistent_state.json"
    monkeypatch.setattr("server.STATE_PATH", state_path)

    state = _load_state()
    assert state["truth_status"] == "INSUFFICIENT_DATA"
    assert state["well_score"] is None
    assert state["environment"] == "PROD"
    assert state["reason"] == "No state file found. Sovereign state unknown."


# ── 5. Inject-as-VERIFIED must coerce to OPERATOR_REPORTED (T2 F2 harden) ─────


def test_inject_verified_coerces_to_self_report():
    """biometric_inject.sh historically wrote VERIFIED — that is a category error."""
    from server import _normalize_truth_status

    state = {
        "timestamp": "2026-07-09T00:55:21+00:00",
        "operator_id": "arif",
        "identity": "WELL",
        "role": "Body / Human Intelligence",
        "authority": "REFLECT_ONLY",
        # is_well() thresholds: peace2>=1.0, kappa_r>=0.95, rasa True, amanah LOCK
        "delta_s": 0.1,
        "peace2": 1.0,
        "kappa_r": 0.95,
        "rasa": True,
        "amanah": "LOCK",
        "metrics": {"cognitive": {"clarity": 9.0}},
        "well_score": 90.4,
        "truth_status": "VERIFIED",
        "environment": "PROD",
        "reason": "Sovereign biometric injection (biometric_inject.sh)",
    }
    assert _normalize_truth_status(state) == "OPERATOR_REPORTED"
    classification = _classify_well_state(state)
    assert classification["truth_status"] == "OPERATOR_REPORTED"
    assert classification["well_signal"] == "WELL_OPERATOR_PRESENT"
    assert classification["owner_summary"]["color"] == "YELLOW"
    assert classification["honesty"]["is_self_report"] is True
    assert classification["honesty"]["cockpit_banner_required"] is True
    assert "SELF-REPORT" in classification["honesty_banner"]
    assert classification["has_telemetry"] is False


def test_honesty_block_stale_banner():
    from server import _honesty_block

    h = _honesty_block("VERIFIED", source_type="SENSOR", freshness_band="STALE")
    assert h["is_stale"] is True
    assert h["code"] == "STALE"
    assert "STALE" in h["banner"]


def test_machine_substrate_health_does_not_invent_score():
    from server import _machine_substrate_health

    block = _machine_substrate_health()
    assert "well_score" not in block
    assert block["source"] == "machine_state.json"
    assert block["status"] in {"healthy", "degraded", "unavailable"}


# ── 6. well_check_repair must not carry fabricated readiness (P4 honesty) ─────


def test_well_check_repair_does_not_leak_fabricated_readiness(monkeypatch, tmp_path):
    """well_check_repair is a repair precheck (advisory). The readiness field
    is fabricated by well_777_forge → well_forge_precheck → _compose_verdict
    regardless of whether the state has biometric data. A repair tool that
    is allowed to carry a fabricated "readiness.human=OPTIMAL" verdict
    while the state has truth_status=INSUFFICIENT_DATA is the absence-
    laundering bug surfaced in docs/FINDINGS-2026-08-19.
    """
    import server as _server_mod
    from server import well_check_repair
    state_path = tmp_path / "well-state.json"
    state_path.write_text(
        '{"truth_status":"INSUFFICIENT_DATA","environment":"PROD",'
        '"well_score":null,"reason":"no production state yet"}'
    )
    monkeypatch.setattr(_server_mod, "STATE_PATH", state_path)

    result = well_check_repair(mode="precheck", task_description="probe-repair")

    # The result is wrapped by _to_federation_output. The forged readiness
    # surfaces inside result["observation"]["readiness"]. The fix is to strip
    # the readiness field from the observation before returning.
    observation = result.get("observation", {})
    if isinstance(observation, dict):
        assert "readiness" not in observation, (
            f"well_check_repair leaked fabricated readiness: {observation.get('readiness')}. "
            f"Repair precheck is advisory-only and must not carry a vitality verdict."
        )

    # Also: the top-level result must not carry a top-level "readiness" key.
    assert "readiness" not in result, (
        f"well_check_repair leaked top-level readiness: {result.get('readiness')}"
    )


# ══ D2 / D3 / D4 — trace_id HRFID-20260929 ═══════════════════════════════════
# Measured 2026-09-29: an agent-authored test string ("I'm Arif. Test. Qwen code suruh
# aku prompt. Aku penat hari ni", confidence LOW) landed in the live organ as
# derived.fatigue 7 / energy 3 and drove metabolic_flux.verdict =
# COMPULSORY_REALLOCATION (flux 0.775, decision_fatigue_contribution 0.55) — a
# governance verdict about a human, produced by a probe. Alongside it, well_score 63.6
# was partly a fabricated `calm` (no producer), and the identity boilerplate existed
# twice, contradicting itself across two planes.
from scripts import well_ingest as wi

LIVE_TEST_RECORD = {
    "ts": "2026-09-29T04:22:56.977259+00:00",
    "source": "verbal",
    "operator_id": "arif",
    "signals": {
        "categories": ["fatigue_high"],
        "tokens": ["penat"],
        "quote": "I'm Arif. Test. Qwen code suruh aku prompt. Aku penat hari ni",
    },
    "confidence": "LOW",
    "raw_hash": "d389bf4cfa515df1",
    "provenance": {
        "channel": "telegram-dm",
        "capture": "event-driven-verbal",
        "capture_mode": "reply_quote",
        "evidence_class": "SOVEREIGN_VERBAL_SELF_REPORT",
    },
    "derived": {"fatigue": 7, "energy": 3},
}


def _reported_state() -> dict:
    """A state whose numbers all have a real producer (calm 5.5 was reported)."""
    return {
        "identity": "WELL",
        "role": "Body / Human Intelligence",
        "authority": "REFLECT_ONLY",
        "operator_id": "arif",
        "environment": "PROD",
        "truth_status": "OPERATOR_VERBAL",
        "test_contamination": "NO",
        "last_successful_read": "2026-09-29T00:00:00+00:00",
        "metrics": {
            "cognitive": {"clarity": 8.5, "decision_fatigue": 2.2},
            "derived": {"energy": 6.0, "fatigue": 3.0, "calm": 5.5},
        },
        "well_score": 74.1,
    }


# ── D2 — contamination is read off the record ────────────────────────────────
def test_test_marker_in_quote_is_detected_from_the_record():
    contaminated, reasons = wi.detect_test_contamination(LIVE_TEST_RECORD)
    assert contaminated is True
    assert any(r.startswith("test_marker:signals.quote") for r in reasons), reasons
    # the flag is not hardcoded: the same record without the marker is clean
    clean = json.loads(json.dumps(LIVE_TEST_RECORD))
    clean["signals"]["quote"] = "Aku penat hari ni, tidur 4 jam saja"
    clean["confidence"] = "MEDIUM"
    assert wi.detect_test_contamination(clean) == (False, [])


def test_low_confidence_without_channel_receipt_is_contaminated():
    record = json.loads(json.dumps(LIVE_TEST_RECORD))
    record["signals"]["quote"] = "Aku penat"
    record.pop("provenance")
    record.pop("raw_hash")
    contaminated, reasons = wi.detect_test_contamination(record)
    assert contaminated is True
    assert "low_confidence_without_channel_receipt" in reasons, reasons


def test_contaminated_record_cannot_touch_derived_metrics_or_score():
    state = _reported_state()
    before = json.loads(json.dumps(state["metrics"]))
    merged = wi.merge_into_state(state, LIVE_TEST_RECORD)
    assert merged["metrics"] == before, "a test string entered the human's numbers"
    assert merged["metrics"]["derived"]["fatigue"] == 3.0
    assert merged["test_contamination"] == "YES"
    assert merged["contamination_quarantined"] is True
    assert merged["signals_meta"]["quarantined_injection"]["excluded_from"] == [
        "metrics.derived", "metrics.cognitive", "metabolic_flux", "well_score",
    ]
    # a test string may not advance the observation clock either (D1 discipline)
    assert merged["last_successful_read"] == "2026-09-29T00:00:00+00:00"


def test_quarantine_end_to_end_then_the_organ_says_it_does_not_know(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps(_reported_state()))
    intake = tmp_path / "intake" / "verbal"
    intake.mkdir(parents=True)
    record_file = intake / "1790655776977413-d389bf4c.json"
    record_file.write_text(json.dumps(LIVE_TEST_RECORD))
    monkeypatch.setattr(wi, "STATE_FILE", state_path)
    monkeypatch.setattr(wi, "AUDIT_LOG", tmp_path / "intake_log.jsonl")
    monkeypatch.setattr(wi, "PROCESSED_DIR", tmp_path / "processed")

    result = wi.process_intake_file(record_file)

    assert result.startswith("QUARANTINE"), result
    saved = json.loads(state_path.read_text())
    assert saved["test_contamination"] == "YES"
    assert saved["truth_status"] == "INSUFFICIENT_DATA"
    assert saved["evidence_class"] == "AGENT_TEST_RECORD"      # downgraded, retained
    assert saved["metrics"]["derived"]["fatigue"] == 3.0       # never 7 from the probe
    assert (tmp_path / "processed" / record_file.name).exists()  # kept as evidence
    # and the organ refuses to present a verdict about the human
    classification = _classify_well_state(saved)
    assert classification["truth_status"] == "INSUFFICIENT_DATA"
    assert classification["well_score"] is None
    assert "test_contamination:YES" in classification["insufficient_reasons"]
    assert classification["honesty"]["is_mock_or_test"] is True
    assert classification["honesty"]["source_type"] == "AGENT_TEST_RECORD"
    assert "MOCK / TEST" in classification["honesty_banner"]


def test_clean_verbal_record_still_flows_into_the_organ():
    """The gate must not silence the honest lane: real words still land, attributed."""
    record = json.loads(json.dumps(LIVE_TEST_RECORD))
    record["signals"]["quote"] = "Aku penat hari ni, tidur 4 jam saja"
    record["confidence"] = "MEDIUM"
    merged = wi.merge_into_state(_reported_state(), record)
    assert merged["test_contamination"] == "NO"
    assert merged["metrics"]["derived"]["fatigue"] == 7
    prov = merged["signals_meta"]["field_provenance"]["metrics.derived.fatigue"]
    assert prov["producer"] == "hermes:verbal-intake"
    assert prov["source_class"] == "AGENT_INFERRED"   # words -> number is an inference


# ── D3 — absent inputs stay absent ───────────────────────────────────────────
def test_missing_calm_yields_no_score_not_636():
    """Exactly the measured shape: clarity 8.5, decision_fatigue 2.2, energy 3,
    fatigue 7, and NO calm reading — yet state carried well_score 63.6, which is what
    a default of 5 produces."""
    metrics = {
        "cognitive": {"clarity": 8.5, "decision_fatigue": 2.2},
        "derived": {"energy": 3, "fatigue": 7},
    }
    assert "calm" not in metrics["derived"]
    assert wi.compute_well_score(metrics) is None


def test_636_requires_a_real_calm_reading():
    metrics = {
        "cognitive": {"clarity": 8.5, "decision_fatigue": 2.2},
        "derived": {"energy": 3, "fatigue": 7, "calm": 5.0},
    }
    assert wi.compute_well_score(metrics) == 63.6


def test_empty_metrics_is_insufficient_not_fifty_percent_human():
    assert wi.compute_well_score({}) is None
    assert wi.compute_well_score({"derived": {}}) is None
    # a non-numeric or out-of-range value cannot be scored honestly either
    assert wi.compute_well_score({
        "cognitive": {"clarity": "unknown", "decision_fatigue": 2.2},
        "derived": {"energy": 3, "fatigue": 7, "calm": 5},
    }) is None
    assert wi.compute_well_score({
        "cognitive": {"clarity": 80, "decision_fatigue": 2.2},
        "derived": {"energy": 3, "fatigue": 7, "calm": 5},
    }) is None


def test_ingest_writes_no_score_when_inputs_are_absent():
    record = json.loads(json.dumps(LIVE_TEST_RECORD))
    record["signals"]["quote"] = "Aku penat hari ni"
    record["confidence"] = "HIGH"
    record["derived"] = {"fatigue": 7, "energy": 3}   # no calm anywhere
    state = _reported_state()
    state["metrics"]["derived"].pop("calm")
    merged = wi.merge_into_state(state, record)
    assert merged["well_score"] is None


# ── D4 — producer and provenance are carried, defaults cannot speak ──────────
def test_agent_inferred_value_cannot_enter_a_self_report_field():
    state = _reported_state()
    record = {
        "ts": "2026-09-29T05:00:00+00:00",
        "source": "cron",
        "operator_id": "arif",
        "confidence": "MEDIUM",
        "signals": {},
        "metrics": {"peace2": 0.42, "cognitive": {"clarity": 9.0}},
    }
    merged = wi.merge_into_state(state, record)
    assert "peace2" not in merged["metrics"], "synthesis spoke as the operator"
    assert "metrics.peace2" in merged["signals_meta"]["provenance_refusals"]
    # an honest field from the same lane still lands, and does not clobber siblings
    assert merged["metrics"]["cognitive"]["clarity"] == 9.0
    assert merged["metrics"]["cognitive"]["decision_fatigue"] == 2.2
    prov = merged["signals_meta"]["field_provenance"]["metrics.cognitive.clarity"]
    assert prov["producer"] == "cron:well_synth"
    assert prov["source_class"] == "AGENT_INFERRED"


def test_source_class_enum_is_enforced():
    state = {}
    wi._stamp_provenance(state, "metrics.derived.mood", "cron:well_ingest", "FEELS_GOOD")
    entry = state["signals_meta"]["field_provenance"]["metrics.derived.mood"]
    assert entry["source_class"] == "EXTERNAL", entry


def test_identity_defaults_appear_once_and_cannot_be_read_as_a_report(tmp_path, monkeypatch):
    import server as _server_mod

    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps({
        "identity": "WELL",
        "role": "Body / Human Intelligence",
        "authority": "REFLECT_ONLY",
        "operator_id": "arif",
        "environment": "PROD",
        "truth_status": "INSUFFICIENT_DATA",
        "metrics": {},
    }))
    monkeypatch.setattr(_server_mod, "STATE_PATH", state_path)
    state = _server_mod._load_state()

    bio = state["biometric"]
    for key in ("delta_s", "peace2", "kappa_r", "rasa", "amanah"):
        assert bio[f"{key}__source_class"] == "INJECTED_DEFAULT", key
        assert bio[f"{key}__producer"] == "kernel:ensure_well_identity", key
        assert state[key] == bio[key], key            # mirror, never a rival value
        assert key in state["_identity_defaults_injected"], key
    datum = _server_mod._human_datum(state)
    assert datum["observed"] == {}
    assert datum["provenance"] == "NO_OPERATOR_DATUM"


def test_contradicting_planes_reconcile_to_the_authoritative_value():
    """The live-file shape measured 2026-09-29: peace2 1.0 top level vs biometric 0.9,
    rasa true vs "ready", amanah "LOCK" vs 0.95, delta_s 0.0 vs 0.1, kappa_r 0.95 vs
    0.85. One value must survive, and it is the nested block's (the documented
    precedence, and where the inject lanes actually write)."""
    import server as _server_mod

    state = _server_mod._ensure_well_identity({
        "identity": "WELL",
        "role": "Body / Human Intelligence",
        "authority": "REFLECT_ONLY",
        "operator_id": "arif",
        "environment": "PROD",
        "truth_status": "OPERATOR_VERBAL",
        "metrics": {},
        "delta_s": 0.0, "peace2": 1.0, "kappa_r": 0.95, "rasa": True, "amanah": "LOCK",
        "_identity_defaults_injected": ["delta_s", "peace2", "kappa_r", "rasa", "amanah"],
        "biometric": {"delta_s": 0.1, "peace2": 0.9, "kappa_r": 0.85,
                      "rasa": "ready", "amanah": 0.95},
    })
    for key, expected in (("delta_s", 0.1), ("peace2", 0.9), ("kappa_r", 0.85),
                          ("rasa", "ready"), ("amanah", 0.95)):
        assert state[key] == expected, key
        assert state["biometric"][key] == expected, key
        assert state["biometric"][f"{key}__source_class"] == "SELF_REPORT", key
    assert state["_identity_defaults_injected"] == []
    datum = _server_mod._human_datum(state)
    assert datum["observed"]["peace2"] == 0.9
    assert datum["observed"]["peace2__source"] == "biometric"


def test_ready_presence_cannot_mint_self_report_numbers(tmp_path, monkeypatch):
    import server as _server_mod

    state_path = tmp_path / "state.json"
    state_path.write_text(json.dumps({
        "identity": "WELL",
        "role": "Body / Human Intelligence",
        "authority": "REFLECT_ONLY",
        "operator_id": "arif",
        "environment": "PROD",
        "truth_status": "INSUFFICIENT_DATA",
        "metrics": {},
    }))
    monkeypatch.setattr(_server_mod, "STATE_PATH", state_path)
    monkeypatch.setattr(_server_mod, "EVENTS_PATH", tmp_path / "events.jsonl")

    _server_mod._assert_sovereign_presence(operator_id="arif")
    saved = json.loads(state_path.read_text())

    assert saved["truth_status"] == "OPERATOR_REPORTED"     # presence is still asserted
    assert saved["presence_only"] is True
    assert saved["producer"] == "well:ready-presence"
    assert "peace2" in saved["_identity_defaults_injected"]
    assert saved["biometric"]["peace2__source_class"] == "INJECTED_DEFAULT"
    assert _server_mod._human_datum(saved)["observed"] == {}
