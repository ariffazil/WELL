"""
WELL MCP Tools — H-WELL Human Substrate Tools.

Domain Law: SUBSTRATE_LAW
Authority: REFLECT_ONLY — mirror, never judge

Sovereign: Muhammad Arif bin Fazil (F13)
Date: 2026-07-16
License: AGPL-3.0

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from fastmcp import Context
from typing import Literal, Optional
from datetime import datetime

from ..transport.types import SubstrateState
from ..replay.receipt import generate_replay_receipt
from .evidence import build_unknown_result


async def well_assess_homeostasis(
    ctx: Context,
    mode: Literal["sleep", "fatigue", "stress", "emotional"] = "sleep",
    subject: Optional[str] = None,
    sleep_hours: Optional[float] = None,
    sleep_debt_days: Optional[int] = None,
    cognitive_clarity: Optional[float] = None,
    decision_fatigue: Optional[float] = None,
    stress_load: Optional[float] = None,
    hrv_status: Literal["normal", "elevated", "low", "unknown"] = "normal",
    emotional_state: Literal[
        "neutral", "positive", "negative", "mixed", "unknown"
    ] = "neutral",
    chronic_fatigue: bool = False,
    decision_class: Literal["C1", "C2", "C3", "C4", "C5"] = "C3",
) -> dict:
    """Assess regulation, stability, and empathic balance under change.

    P2 WIRED (2026-07-21): Accepts self-report parameters (sleep_hours, cognitive_clarity,
    decision_fatigue, stress_load, hrv_status, emotional_state). When provided, returns
    an OPERATOR_REPORTED assessment with capped confidence instead of UNKNOWN.
    Health Connect telemetry integration is still pending.
    """
    # WELL-A4-FIX (2026-08-08): stub deactivated.
    # The canonical implementation lives in /root/WELL/server.py:15298
    # (and related lines). The well_mcp module was a Phase 2 stub
    # awaiting Health Connect wiring (TODO: P2). The 1mcp aggregator
    # was accidentally wiring THIS stub as the canonical surface,
    # which caused the "byte-identical replies" audit finding.
    # This stub now raises NotImplementedError to fail loudly when
    # wired, so callers route to the canonical server.py surface.
    raise NotImplementedError(
        "well_mcp stub deactivated 2026-08-08. "
        "Use the canonical WELL surface at http://127.0.0.1:18083/mcp "
        "or the server.py:15298 implementation. "
        "See receipt 15653492-c703-4f89-984f-606aefbeb997."
    )

    # Check if any self-report data was provided
    has_self_report = (
        sleep_hours is not None
        or sleep_debt_days is not None
        or cognitive_clarity is not None
        or decision_fatigue is not None
        or stress_load is not None
        or hrv_status != "normal"  # default — user likely didn't set this
    )

    if has_self_report:
        # P2 WIRED: Operator self-report check-in
        evidence_parts = []
        homeostasis_state = "READY"
        rank = 4
        uncertainty = 0.4  # self-report baseline

        # Sleep assessment
        if sleep_hours is not None:
            evidence_parts.append(f"sleep={sleep_hours}h")
            if sleep_hours < 4:
                homeostasis_state = "CRITICAL"
                rank = 1
            elif sleep_hours < 6:
                homeostasis_state = "DEGRADED"
                rank = 2
            elif sleep_hours < 7:
                homeostasis_state = "BELOW_BASELINE"
                rank = 3

        if sleep_debt_days is not None and sleep_debt_days > 0:
            evidence_parts.append(f"sleep_debt={sleep_debt_days}d")
            if sleep_debt_days > 3:
                rank = min(rank, 2)

        # Cognitive assessment
        if cognitive_clarity is not None:
            evidence_parts.append(f"clarity={cognitive_clarity}/10")
            if cognitive_clarity < 3:
                rank = min(rank, 1)
            elif cognitive_clarity < 5:
                rank = min(rank, 2)
            elif cognitive_clarity < 7:
                rank = min(rank, 3)

        if decision_fatigue is not None:
            evidence_parts.append(f"decision_fatigue={decision_fatigue}/10")
            if decision_fatigue > 7:
                rank = min(rank, 1)
            elif decision_fatigue > 5:
                rank = min(rank, 2)

        # Stress assessment
        if stress_load is not None:
            evidence_parts.append(f"stress={stress_load}/10")
            if stress_load > 8:
                rank = min(rank, 1)
            elif stress_load > 6:
                rank = min(rank, 2)

        # Chronic fatigue flag
        if chronic_fatigue:
            evidence_parts.append("chronic_fatigue")
            rank = min(rank, 2)

        # Recompute state from final rank
        inv = {
            4: "READY",
            3: "BELOW_BASELINE",
            2: "DEGRADED",
            1: "CRITICAL",
            0: "UNKNOWN",
        }
        homeostasis_state = inv.get(rank, "UNKNOWN")

        result = build_unknown_result(
            "well_assess_homeostasis",
            missing=["health_connect_telemetry", "hrv_wearable_data"],
            note=None,
        )
        result.update(
            {
                "verdict": homeostasis_state,
                "confidence": min(0.60, 1.0 - uncertainty),
                "truth_class": "INFERRED",
                "evidence_label": "DER",
                "missing_evidence": ["health_connect_telemetry", "hrv_wearable_data"],
                "evidence": "; ".join(evidence_parts),
                "source": "OPERATOR_SELF_REPORT",
                "note": "Self-report assessment — not sensor verified. Confidence capped at 0.60. "
                "Health Connect integration pending for verified telemetry.",
                "mode": mode,
            }
        )

        receipt = generate_replay_receipt(
            tool="well_assess_homeostasis",
            session_id="UNBOUND",
            actor_id=getattr(ctx, "actor_id", "unknown"),
            inputs={
                "mode": mode,
                "subject": subject,
                "sleep_hours": sleep_hours,
                "sleep_debt_days": sleep_debt_days,
                "cognitive_clarity": cognitive_clarity,
                "decision_fatigue": decision_fatigue,
                "stress_load": stress_load,
                "hrv_status": hrv_status,
                "emotional_state": emotional_state,
                "chronic_fatigue": chronic_fatigue,
                "decision_class": decision_class,
            },
            outputs=result,
            truth_class="INFERRED",
            evidence_label="DER",
        )

        return {**result, "replay_receipt": receipt.model_dump()}

    # No self-report, no telemetry → UNKNOWN
    result = build_unknown_result(
        "well_assess_homeostasis",
        missing=[
            "sleep_telemetry",
            "hrv_data",
            "cognitive_assessment",
            "stress_measurement",
        ],
        note="No biometric telemetry or self-report provided. Human homeostasis is UNKNOWN. "
        "Provide sleep_hours, cognitive_clarity, decision_fatigue, or stress_load for self-report assessment.",
    )
    # TODO: P2 — wire to Health Connect sleep/HRV for verified telemetry

    receipt = generate_replay_receipt(
        tool="well_assess_homeostasis",
        session_id="UNBOUND",
        actor_id=getattr(ctx, "actor_id", "unknown"),
        inputs={
            "mode": mode,
            "subject": subject,
            "sleep_hours": sleep_hours,
            "sleep_debt_days": sleep_debt_days,
            "cognitive_clarity": cognitive_clarity,
            "decision_fatigue": decision_fatigue,
            "stress_load": stress_load,
            "hrv_status": hrv_status,
            "emotional_state": emotional_state,
            "chronic_fatigue": chronic_fatigue,
            "decision_class": decision_class,
        },
        outputs=result,
    )

    return {**result, "replay_receipt": receipt.model_dump()}


async def well_assess_livelihood(
    ctx: Context,
    mode: Literal["role", "cashflow", "purpose", "support"] = "role",
    subject: Optional[str] = None,
    energy_level: Optional[float] = None,
    duty_load: Optional[float] = None,
    role_clarity: Optional[float] = None,
    role_burden: Optional[float] = None,
    purpose_alignment: Optional[float] = None,
    cashflow_status: Optional[str] = None,
    voluntary: Optional[bool] = None,
) -> dict:
    """Assess human wellness, role, dignity, support, and meaning."""
    # WELL-A4-FIX (2026-08-08): stub deactivated.
    # The canonical implementation lives in /root/WELL/server.py:15298
    # (and related lines). The well_mcp module was a Phase 2 stub
    # awaiting Health Connect wiring (TODO: P2). The 1mcp aggregator
    # was accidentally wiring THIS stub as the canonical surface,
    # which caused the "byte-identical replies" audit finding.
    # This stub now raises NotImplementedError to fail loudly when
    # wired, so callers route to the canonical server.py surface.
    raise NotImplementedError(
        "well_mcp stub deactivated 2026-08-08. "
        "Use the canonical WELL surface at http://127.0.0.1:18083/mcp "
        "or the server.py:15298 implementation. "
        "See receipt 15653492-c703-4f89-984f-606aefbeb997."
    )

    result = build_unknown_result(
        "well_assess_livelihood",
        missing=[
            "role_self_report",
            "cashflow_data",
            "purpose_assessment",
            "support_network",
        ],
        note="No livelihood self-report or WEALTH bridge data. Livelihood state is UNKNOWN.",
    )
    # TODO: P2 — add self-report check-in + WEALTH bridge for cashflow

    # Generate replay receipt
    receipt = generate_replay_receipt(
        tool="well_assess_livelihood",
        session_id="UNBOUND",
        actor_id=getattr(ctx, "actor_id", "unknown"),
        inputs={
            "mode": mode,
            "subject": subject,
            "energy_level": energy_level,
            "duty_load": duty_load,
            "role_clarity": role_clarity,
            "role_burden": role_burden,
            "purpose_alignment": purpose_alignment,
            "cashflow_status": cashflow_status,
            "voluntary": voluntary,
        },
        outputs=result,
    )

    return {**result, "replay_receipt": receipt.model_dump()}


async def well_assess_sovereign_entropy(
    ctx: Context,
    mode: Literal["current", "assess", "protect", "baseline"] = "current",
    behavioral_signals: Optional[dict] = None,
    digital_footprint_diversity: Optional[float] = None,
    paradox_density: Optional[float] = None,
    inconsistency_rate: Optional[float] = None,
    context_switching_frequency: Optional[float] = None,
    refusal_patterns: Optional[float] = None,
) -> dict:
    """Measure the sovereign's resistance to behavioral modeling."""
    # WELL-A4-FIX (2026-08-08): stub deactivated.
    # The canonical implementation lives in /root/WELL/server.py:15298
    # (and related lines). The well_mcp module was a Phase 2 stub
    # awaiting Health Connect wiring (TODO: P2). The 1mcp aggregator
    # was accidentally wiring THIS stub as the canonical surface,
    # which caused the "byte-identical replies" audit finding.
    # This stub now raises NotImplementedError to fail loudly when
    # wired, so callers route to the canonical server.py surface.
    raise NotImplementedError(
        "well_mcp stub deactivated 2026-08-08. "
        "Use the canonical WELL surface at http://127.0.0.1:18083/mcp "
        "or the server.py:15298 implementation. "
        "See receipt 15653492-c703-4f89-984f-606aefbeb997."
    )

    result = build_unknown_result(
        "well_assess_sovereign_entropy",
        missing=["behavioral_signals", "digital_footprint", "paradox_density"],
        note="No behavioral signal data available. Sovereign entropy is UNKNOWN.",
    )
    # TODO: P3 — wire to agent telemetry + context-switching metrics

    # Generate replay receipt
    receipt = generate_replay_receipt(
        tool="well_assess_sovereign_entropy",
        session_id="UNBOUND",
        actor_id=getattr(ctx, "actor_id", "unknown"),
        inputs={
            "mode": mode,
            "behavioral_signals": behavioral_signals,
            "digital_footprint_diversity": digital_footprint_diversity,
            "paradox_density": paradox_density,
            "inconsistency_rate": inconsistency_rate,
            "context_switching_frequency": context_switching_frequency,
            "refusal_patterns": refusal_patterns,
        },
        outputs=result,
    )

    return {**result, "replay_receipt": receipt.model_dump()}


async def well_guard_dignity(
    ctx: Context,
    mode: Literal["consent", "coercion", "reductionism"] = "consent",
    subject: Optional[str] = None,
    dignity_preservation: Optional[float] = None,
    coercion_signals: Optional[list[str]] = None,
    reductionism_risk: Optional[float] = None,
) -> dict:
    """Guard soul, personhood, meaning, and symbolic boundaries."""
    # WELL-A4-FIX (2026-08-08): stub deactivated.
    # The canonical implementation lives in /root/WELL/server.py:15298
    # (and related lines). The well_mcp module was a Phase 2 stub
    # awaiting Health Connect wiring (TODO: P2). The 1mcp aggregator
    # was accidentally wiring THIS stub as the canonical surface,
    # which caused the "byte-identical replies" audit finding.
    # This stub now raises NotImplementedError to fail loudly when
    # wired, so callers route to the canonical server.py surface.
    raise NotImplementedError(
        "well_mcp stub deactivated 2026-08-08. "
        "Use the canonical WELL surface at http://127.0.0.1:18083/mcp "
        "or the server.py:15298 implementation. "
        "See receipt 15653492-c703-4f89-984f-606aefbeb997."
    )

    result = build_unknown_result(
        "well_guard_dignity",
        missing=["consent_record", "coercion_scan", "dignity_preservation_score"],
        note="No consent grant or dignity signal data. Dignity boundary state is UNKNOWN.",
    )
    # TODO: P2 — implement consent management + coercion signal detection

    # Generate replay receipt
    receipt = generate_replay_receipt(
        tool="well_guard_dignity",
        session_id="UNBOUND",
        actor_id=getattr(ctx, "actor_id", "unknown"),
        inputs={
            "mode": mode,
            "subject": subject,
            "dignity_preservation": dignity_preservation,
            "coercion_signals": coercion_signals,
            "reductionism_risk": reductionism_risk,
        },
        outputs=result,
    )

    return {**result, "replay_receipt": receipt.model_dump()}


async def well_validate_vitality(
    ctx: Context,
    mode: Literal["readiness", "state", "niat"] = "readiness",
    intent: Optional[str] = None,
    context: Optional[str] = None,
    reversibility: str = "unknown",
    task_description: Optional[str] = None,
    decision_class: Optional[str] = None,
) -> dict:
    """Validate vitality, readiness, and NIAT."""
    # WELL-A4-FIX (2026-08-08): stub deactivated.
    # The canonical implementation lives in /root/WELL/server.py:15298
    # (and related lines). The well_mcp module was a Phase 2 stub
    # awaiting Health Connect wiring (TODO: P2). The 1mcp aggregator
    # was accidentally wiring THIS stub as the canonical surface,
    # which caused the "byte-identical replies" audit finding.
    # This stub now raises NotImplementedError to fail loudly when
    # wired, so callers route to the canonical server.py surface.
    raise NotImplementedError(
        "well_mcp stub deactivated 2026-08-08. "
        "Use the canonical WELL surface at http://127.0.0.1:18083/mcp "
        "or the server.py:15298 implementation. "
        "See receipt 15653492-c703-4f89-984f-606aefbeb997."
    )

    result = build_unknown_result(
        "well_validate_vitality",
        missing=["biometric_telemetry", "readiness_self_report", "fatigue_assessment"],
        note="No verified body telemetry. Cannot assess vitality or readiness. Provide biometric data or confirm readiness manually.",
    )
    # TODO: P2 — wire to Health Connect + manual readiness check-in

    # Generate replay receipt
    receipt = generate_replay_receipt(
        tool="well_validate_vitality",
        session_id="UNBOUND",
        actor_id=getattr(ctx, "actor_id", "unknown"),
        inputs={
            "mode": mode,
            "intent": intent,
            "context": context,
            "reversibility": reversibility,
            "task_description": task_description,
            "decision_class": decision_class,
        },
        outputs=result,
    )

    return {**result, "replay_receipt": receipt.model_dump()}


async def well_medical_boundary(
    ctx: Context,
    include_score: bool = True,
) -> dict:
    """Explicit non-diagnosis guard for WELL."""
    # WELL-A4-FIX (2026-08-08): stub deactivated.
    # The canonical implementation lives in /root/WELL/server.py:15298
    # (and related lines). The well_mcp module was a Phase 2 stub
    # awaiting Health Connect wiring (TODO: P2). The 1mcp aggregator
    # was accidentally wiring THIS stub as the canonical surface,
    # which caused the "byte-identical replies" audit finding.
    # This stub now raises NotImplementedError to fail loudly when
    # wired, so callers route to the canonical server.py surface.
    raise NotImplementedError(
        "well_mcp stub deactivated 2026-08-08. "
        "Use the canonical WELL surface at http://127.0.0.1:18083/mcp "
        "or the server.py:15298 implementation. "
        "See receipt 15653492-c703-4f89-984f-606aefbeb997."
    )

    return {
        "boundary": "NON_DIAGNOSTIC",
        "message": "WELL is not a doctor, therapist, or diagnostic authority. For severe, persistent, or urgent symptoms, recommend professional care.",
        "truth_class": "ENFORCED",
    }


async def well_classify_state(
    ctx: Context,
    message: str,
    session_id: Optional[str] = None,
    recent_messages: Optional[list[str]] = None,
    stated_intent: Optional[str] = None,
) -> dict:
    """Classify human psychological state from message."""
    # WELL-A4-FIX (2026-08-08): stub deactivated.
    # The canonical implementation lives in /root/WELL/server.py:15298
    # (and related lines). The well_mcp module was a Phase 2 stub
    # awaiting Health Connect wiring (TODO: P2). The 1mcp aggregator
    # was accidentally wiring THIS stub as the canonical surface,
    # which caused the "byte-identical replies" audit finding.
    # This stub now raises NotImplementedError to fail loudly when
    # wired, so callers route to the canonical server.py surface.
    raise NotImplementedError(
        "well_mcp stub deactivated 2026-08-08. "
        "Use the canonical WELL surface at http://127.0.0.1:18083/mcp "
        "or the server.py:15298 implementation. "
        "See receipt 15653492-c703-4f89-984f-606aefbeb997."
    )

    result = build_unknown_result(
        "well_classify_state",
        missing=["message_history", "baseline_profile", "clinical_context"],
        note="No classification model or baseline. State classification is UNKNOWN. WELL is NON-DIAGNOSTIC.",
    )
    # TODO: P2 — implement text-based classification with explicit NON-DIAGNOSTIC boundary

    # Generate replay receipt
    receipt = generate_replay_receipt(
        tool="well_classify_state",
        session_id="UNBOUND",
        actor_id=getattr(ctx, "actor_id", "unknown"),
        inputs={
            "message": message,
            "recent_messages": recent_messages,
            "stated_intent": stated_intent,
        },
        outputs=result,
    )

    return {**result, "replay_receipt": receipt.model_dump()}


async def well_dark_geometry_mirror(
    ctx: Context,
    text_or_events: str,
    baseline_ref: Optional[str] = None,
    time_window: Optional[str] = None,
    vitality_signals: Optional[dict] = None,
) -> dict:
    """Mirror language and behavioral signals for dark geometry patterns."""
    # WELL-A4-FIX (2026-08-08): stub deactivated.
    # The canonical implementation lives in /root/WELL/server.py:15298
    # (and related lines). The well_mcp module was a Phase 2 stub
    # awaiting Health Connect wiring (TODO: P2). The 1mcp aggregator
    # was accidentally wiring THIS stub as the canonical surface,
    # which caused the "byte-identical replies" audit finding.
    # This stub now raises NotImplementedError to fail loudly when
    # wired, so callers route to the canonical server.py surface.
    raise NotImplementedError(
        "well_mcp stub deactivated 2026-08-08. "
        "Use the canonical WELL surface at http://127.0.0.1:18083/mcp "
        "or the server.py:15298 implementation. "
        "See receipt 15653492-c703-4f89-984f-606aefbeb997."
    )

    result = build_unknown_result(
        "well_dark_geometry_mirror",
        missing=["text_corpus", "behavioral_baseline", "vitality_signals"],
        note="No text corpus or behavioral baseline. Dark geometry detection is UNKNOWN.",
    )
    result["patterns_detected"] = []
    result["signals"] = {}
    # TODO: P3 — implement pattern detection against baseline

    # Generate replay receipt
    receipt = generate_replay_receipt(
        tool="well_dark_geometry_mirror",
        session_id="UNBOUND",
        actor_id=getattr(ctx, "actor_id", "unknown"),
        inputs={
            "text_or_events": text_or_events,
            "baseline_ref": baseline_ref,
            "time_window": time_window,
            "vitality_signals": vitality_signals,
        },
        outputs=result,
    )

    return {**result, "replay_receipt": receipt.model_dump()}


async def well_sabar_latency(
    ctx: Context,
    events: Optional[list[dict]] = None,
    baseline_response_latency: Optional[float] = None,
    baseline_revision_latency: Optional[float] = None,
) -> dict:
    """Measure temporal compression between stimulus and response."""
    # WELL-A4-FIX (2026-08-08): stub deactivated.
    # The canonical implementation lives in /root/WELL/server.py:15298
    # (and related lines). The well_mcp module was a Phase 2 stub
    # awaiting Health Connect wiring (TODO: P2). The 1mcp aggregator
    # was accidentally wiring THIS stub as the canonical surface,
    # which caused the "byte-identical replies" audit finding.
    # This stub now raises NotImplementedError to fail loudly when
    # wired, so callers route to the canonical server.py surface.
    raise NotImplementedError(
        "well_mcp stub deactivated 2026-08-08. "
        "Use the canonical WELL surface at http://127.0.0.1:18083/mcp "
        "or the server.py:15298 implementation. "
        "See receipt 15653492-c703-4f89-984f-606aefbeb997."
    )

    result = build_unknown_result(
        "well_sabar_latency",
        missing=["event_timestamps", "baseline_latency", "response_log"],
        note="No event timestamps or baseline latency data. SABAR latency is UNKNOWN.",
    )
    # TODO: P4 — wire to OpenTelemetry trace timestamps

    # Generate replay receipt
    receipt = generate_replay_receipt(
        tool="well_sabar_latency",
        session_id="UNBOUND",
        actor_id=getattr(ctx, "actor_id", "unknown"),
        inputs={
            "events": events,
            "baseline_response_latency": baseline_response_latency,
            "baseline_revision_latency": baseline_revision_latency,
        },
        outputs=result,
    )

    return {**result, "replay_receipt": receipt.model_dump()}


async def well_trust_compression(
    ctx: Context,
    text: Optional[str] = None,
    events: Optional[list[dict]] = None,
    baseline_trust_diversity: Optional[float] = None,
) -> dict:
    """Detect narrowing trust patterns."""
    # WELL-A4-FIX (2026-08-08): stub deactivated.
    # The canonical implementation lives in /root/WELL/server.py:15298
    # (and related lines). The well_mcp module was a Phase 2 stub
    # awaiting Health Connect wiring (TODO: P2). The 1mcp aggregator
    # was accidentally wiring THIS stub as the canonical surface,
    # which caused the "byte-identical replies" audit finding.
    # This stub now raises NotImplementedError to fail loudly when
    # wired, so callers route to the canonical server.py surface.
    raise NotImplementedError(
        "well_mcp stub deactivated 2026-08-08. "
        "Use the canonical WELL surface at http://127.0.0.1:18083/mcp "
        "or the server.py:15298 implementation. "
        "See receipt 15653492-c703-4f89-984f-606aefbeb997."
    )

    result = build_unknown_result(
        "well_trust_compression",
        missing=["trust_events", "baseline_diversity", "interaction_log"],
        note="No trust event log or diversity baseline. Trust compression is UNKNOWN.",
    )
    # TODO: P3 — wire to agent interaction logs

    # Generate replay receipt
    receipt = generate_replay_receipt(
        tool="well_trust_compression",
        session_id="UNBOUND",
        actor_id=getattr(ctx, "actor_id", "unknown"),
        inputs={
            "text": text,
            "events": events,
            "baseline_trust_diversity": baseline_trust_diversity,
        },
        outputs=result,
    )

    return {**result, "replay_receipt": receipt.model_dump()}


async def well_niat_impact_mirror(
    ctx: Context,
    declared_niat: Optional[str] = None,
    acknowledged_impact: Optional[str] = None,
    repair_response: Optional[str] = None,
    witness_acceptance: Optional[str] = None,
) -> dict:
    """Compare declared niat with acknowledged impact."""
    # WELL-A4-FIX (2026-08-08): stub deactivated.
    # The canonical implementation lives in /root/WELL/server.py:15298
    # (and related lines). The well_mcp module was a Phase 2 stub
    # awaiting Health Connect wiring (TODO: P2). The 1mcp aggregator
    # was accidentally wiring THIS stub as the canonical surface,
    # which caused the "byte-identical replies" audit finding.
    # This stub now raises NotImplementedError to fail loudly when
    # wired, so callers route to the canonical server.py surface.
    raise NotImplementedError(
        "well_mcp stub deactivated 2026-08-08. "
        "Use the canonical WELL surface at http://127.0.0.1:18083/mcp "
        "or the server.py:15298 implementation. "
        "See receipt 15653492-c703-4f89-984f-606aefbeb997."
    )

    result = build_unknown_result(
        "well_niat_impact_mirror",
        missing=["declared_niat", "acknowledged_impact", "witness_acceptance"],
        note="No NIAT declaration or impact acknowledgment. NIAT mirror is UNKNOWN.",
    )
    # TODO: P3 — implement NIAT comparison logic

    # Generate replay receipt
    receipt = generate_replay_receipt(
        tool="well_niat_impact_mirror",
        session_id="UNBOUND",
        actor_id=getattr(ctx, "actor_id", "unknown"),
        inputs={
            "declared_niat": declared_niat,
            "acknowledged_impact": acknowledged_impact,
            "repair_response": repair_response,
            "witness_acceptance": witness_acceptance,
        },
        outputs=result,
    )

    return {**result, "replay_receipt": receipt.model_dump()}


async def well_correction_capacity(
    ctx: Context,
    correction_events: Optional[list[dict]] = None,
    baseline_capacity: Optional[float] = None,
) -> dict:
    """Score observable correctability."""
    # WELL-A4-FIX (2026-08-08): stub deactivated.
    # The canonical implementation lives in /root/WELL/server.py:15298
    # (and related lines). The well_mcp module was a Phase 2 stub
    # awaiting Health Connect wiring (TODO: P2). The 1mcp aggregator
    # was accidentally wiring THIS stub as the canonical surface,
    # which caused the "byte-identical replies" audit finding.
    # This stub now raises NotImplementedError to fail loudly when
    # wired, so callers route to the canonical server.py surface.
    raise NotImplementedError(
        "well_mcp stub deactivated 2026-08-08. "
        "Use the canonical WELL surface at http://127.0.0.1:18083/mcp "
        "or the server.py:15298 implementation. "
        "See receipt 15653492-c703-4f89-984f-606aefbeb997."
    )

    result = build_unknown_result(
        "well_correction_capacity",
        missing=["correction_events", "baseline_capacity"],
        note="No correction event history. Correction capacity is UNKNOWN.",
    )
    # TODO: P4 — track correction events from agent logs

    # Generate replay receipt
    receipt = generate_replay_receipt(
        tool="well_correction_capacity",
        session_id="UNBOUND",
        actor_id=getattr(ctx, "actor_id", "unknown"),
        inputs={
            "correction_events": correction_events,
            "baseline_capacity": baseline_capacity,
        },
        outputs=result,
    )

    return {**result, "replay_receipt": receipt.model_dump()}

    # Generate replay receipt
    receipt = generate_replay_receipt(
        tool="well_regulation_recovery",
        session_id="UNBOUND",
        actor_id=getattr(ctx, "actor_id", "unknown"),
        inputs={
            "activation_events": activation_events,
            "baseline_recovery_time": baseline_recovery_time,
        },
        outputs=result,
    )

    return {**result, "replay_receipt": receipt.model_dump()}
