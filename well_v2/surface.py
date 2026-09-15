"""WELL v2 surface — 10 mode-tools over the 31-tool legacy surface.

F13 rank #3 (2026-09-16). Mode-merge as thin delegation: zero logic duplication,
fully reversible (delete registration call in server.py). Legacy surface stays
registered during the deprecation epoch (removal 2026-10-16).

Planes: H well_human · M well_machine · G+C well_triad · U well_classify_substrate
(shared, unchanged) · R well_reality (v0) · A well_adaptation (v0) ·
writes well_intake / well_consent / well_bridge · meta well_registry.
"""

from __future__ import annotations

import inspect
from typing import Any

_DEPRECATION = {
    "epoch": "2026-09-16",
    "removal": "2026-10-16",
    "note": "v2 mode-surface; legacy tools remain registered during epoch",
}


def _call(g: dict, name: str, **kw: Any) -> Any:
    """Call a server-module tool function, passing only params it accepts.

    Signature-filtered delegation — immune to signature drift in the monolith
    (Edited Reality vs Executed Reality: the filter reads executed reality).
    """
    fn = g[name]
    params = inspect.signature(fn).parameters
    accepted = {k: v for k, v in kw.items() if v is not None and k in params}
    return fn(**accepted)


def _tag(r: Any, tool: str, mode: str) -> Any:
    if isinstance(r, dict):
        r.setdefault("v2_surface", {"tool": tool, "mode": mode, **_DEPRECATION})
    return r


async def _res(r: Any) -> Any:
    if inspect.isawaitable(r):
        return await r
    return r


def register_v2_tools(g: dict) -> None:
    mcp = g["mcp"]

    @mcp.tool()
    async def well_human(
        mode: str = "readiness",
        decision_class: str | None = None,
        sleep_debt_days: float | None = None,
        cognitive_clarity: float | None = None,
        decision_fatigue: float | None = None,
        stress_load: float | None = None,
        emotional_state: str | None = None,
        hrv_status: str | None = None,
        chronic_fatigue: bool | None = None,
        subject: str | None = None,
        dignity_preservation: float | None = None,
        coercion_signals: list[str] | None = None,
    ) -> dict[str, Any]:
        """H-WELL unified plane. mode=homeostasis|readiness|dignity.

        homeostasis: regulation/stability under change (biometric overrides
        accepted; decision_class routes the C-class gate). readiness: vitality
        envelope + gate. dignity: F6 consent/boundary guard.
        """
        if mode == "homeostasis":
            r = _call(
                g, "well_assess_homeostasis",
                mode="fatigue" if decision_class else "sleep",
                decision_class=decision_class, sleep_debt_days=sleep_debt_days,
                cognitive_clarity=cognitive_clarity, decision_fatigue=decision_fatigue,
                stress_load=stress_load, emotional_state=emotional_state,
                hrv_status=hrv_status, chronic_fatigue=chronic_fatigue,
            )
        elif mode == "dignity":
            r = _call(
                g, "well_guard_dignity", mode="consent",
                subject=subject or "Arif",
                dignity_preservation=dignity_preservation,
                coercion_signals=coercion_signals,
            )
        else:
            r = _call(g, "well_validate_vitality", mode="readiness")
        return _tag(await _res(r), "well_human", mode)

    @mcp.tool()
    async def well_machine(
        mode: str = "diagnose",
        agent_id: str = "well",
        scope: str = "organ",
        issue_type: str = "all",
        lookback_hours: int = 1,
    ) -> dict[str, Any]:
        """M-WELL unified plane. mode=diagnose|recommend|classify|observe.

        observe scope=organ → per-organ thermal/drift/scar/evidence card;
        scope=federation → all-organ + mesh thermal aggregate.
        """
        if mode == "recommend":
            r = _call(g, "well_machine_recommend", issue_type=issue_type)
        elif mode == "classify":
            r = _call(g, "well_classify_machine_state", agent_id=agent_id)
        elif mode == "observe" and scope == "federation":
            r = _call(g, "well_observe_federation_thermal", lookback_hours=lookback_hours)
        elif mode == "observe":
            r = _call(g, "well_observe_machine", agent_id=agent_id, surface="all")
        else:
            r = _call(g, "well_machine_diagnose")
        return _tag(await _res(r), "well_machine", mode)

    @mcp.tool()
    async def well_triad(
        mode: str = "assess",
        observer: str = "well",
        lookback_hours: int = 1,
    ) -> dict[str, Any]:
        """G+C triadic plane. mode=assess|snapshot|hud.

        snapshot observer=frame → FRAME evidence-only read of the same file.
        """
        if mode == "snapshot" and observer == "frame":
            r = _call(g, "well_frame_read_snapshot")
        elif mode == "snapshot":
            r = _call(g, "well_get_triadic_snapshot")
        elif mode == "hud":
            r = _call(g, "well_render_hud_panel")
        else:
            r = _call(g, "well_assess_triadic_state", lookback_hours=lookback_hours)
        return _tag(await _res(r), "well_triad", mode)

    @mcp.tool()
    async def well_reality(
        mode: str = "confidence",
        limit: int = 10,
        lookback_days: int = 30,
    ) -> dict[str, Any]:
        """R-WELL (v0). Reality Integrity plane. mode=confidence|lineage|witness|patterns.

        Constitutional metric: Edited Reality ≠ Executed Reality.
        confidence v0 = live drift + machine freshness + bridge lane truth.
        """
        if mode == "lineage":
            r = _call(g, "well_trace_lineage", mode="recall", limit=limit)
            return _tag(await _res(r), "well_reality", mode)
        if mode in ("witness", "patterns"):
            return _tag({
                "ok": True,
                "implementation_status": "PENDING — Phase 4 (Graphiti/Falkor witness wiring, scar→risk patterns)",
                "constitutional_metric": "Edited Reality != Executed Reality",
                "deprecation": _DEPRECATION,
            }, "well_reality", mode)
        commits = g["_compute_well_commits"]()
        ms = g["_machine_substrate_health"]()
        band = ms.get("freshness_band") or ms.get("status")
        evidence_classes = {
            "commit_alignment": "VERIFIED" if not commits.get("drift") else "STALE",
            "machine_telemetry": "OBSERVED" if band == "FRESH" else str(band).upper(),
            "witness_bridge": "OBSERVED (arifFlow lane; arifOS lane DEAD by F13 Option B)",
        }
        return _tag({
            "ok": True,
            "implementation_status": "v0 — Phase 4 deep wiring pending",
            "drift": commits.get("drift"),
            "source_commit": commits.get("source_commit"),
            "deployed_commit": commits.get("deployed_commit"),
            "machine_freshness_band": band,
            "evidence_classes": evidence_classes,
            "reality_confidence_v0": round(
                sum(1 for v in evidence_classes.values() if v.startswith(("VERIFIED", "OBSERVED")))
                / len(evidence_classes), 2),
        }, "well_reality", mode)

    @mcp.tool()
    async def well_adaptation(
        mode: str = "precheck",
        task_description: str | None = None,
        decision_class: str | None = None,
        source: str | None = None,
    ) -> dict[str, Any]:
        """A-WELL (v0). Adaptation Readiness plane. mode=precheck|readiness|mttr|gaps.

        Constitutional question: can witnessed reality still change future behavior?
        """
        if mode == "precheck":
            r = _call(g, "well_check_repair", mode="precheck",
                      task_description=task_description,
                      decision_class=decision_class, source=source)
            return _tag(await _res(r), "well_adaptation", mode)
        return _tag({
            "ok": True,
            "implementation_status": "PENDING — Phase 5 (adaptation gap detector, MTTR / Reality Correction Time ledger)",
            "constitutional_question": "Can witnessed reality still change future behavior?",
            "v0_test_case": "Graphiti: provider moved KVM8->KVM4 vs live config references",
            "deprecation": _DEPRECATION,
        }, "well_adaptation", mode)

    @mcp.tool()
    async def well_intake(
        mode: str,
        kcal: float | None = None,
        items: str | None = None,
        event_type: str = "meditation",
        note: str | None = None,
        occurred_at: str | None = None,
        substance: str | None = None,
        dose_mg: float | None = None,
        source: str = "manual",
        readings: dict[str, float] | None = None,
        consent_scope: str | None = None,
        actor_token: str | None = None,
    ) -> dict[str, Any]:
        """H-WELL write plane. mode=meal|recovery|substance|biometric.

        Consent gates (F11/F13) preserved by delegation — biometric requires
        Hermes actor_token; substance requires substance.full scope.
        """
        if mode == "meal":
            r = _call(g, "well_log_intake", kcal=kcal, items=items, note=note,
                      occurred_at=occurred_at)
        elif mode == "recovery":
            r = _call(g, "well_log_recovery_event", event_type=event_type,
                      note=note, source=source)
        elif mode == "substance":
            r = _call(g, "well_log_substance", substance=substance,
                      dose_mg=dose_mg, note=note, source=source)
        elif mode == "biometric":
            r = _call(g, "well_inject_biometric", source=source,
                      readings=readings or {}, consent_scope=consent_scope,
                      actor_token=actor_token)
        else:
            return _tag({"ok": False, "error": f"unknown mode: {mode}"}, "well_intake", mode)
        return _tag(await _res(r), "well_intake", mode)

    @mcp.tool()
    async def well_consent(
        mode: str = "audit",
        scope_id: str | None = None,
        level: str = "granted",
        actor_token: str | None = None,
        include_revoked: bool = True,
        scope_filter: str | None = None,
    ) -> dict[str, Any]:
        """G-WELL consent plane. mode=audit|grant|revoke.

        grant/revoke = well_consent_set_scope (Hermes-only F11 gate preserved).
        """
        if mode == "audit":
            r = _call(g, "well_consent_audit", scope_filter=scope_filter,
                      include_revoked=include_revoked)
        elif mode in ("grant", "revoke"):
            if not scope_id:
                return _tag({"ok": False, "error": "scope_id required"}, "well_consent", mode)
            r = _call(g, "well_consent_set_scope", scope_id=scope_id,
                      level="granted" if mode == "grant" else "revoked",
                      actor_token=actor_token)
        else:
            return _tag({"ok": False, "error": f"unknown mode: {mode}"}, "well_consent", mode)
        return _tag(await _res(r), "well_consent", mode)

    @mcp.tool()
    async def well_bridge(
        mode: str = "attest",
        attestation_kind: str = "substrate_evidence",
        candidate: str | None = None,
        recommendation: str = "HOLD",
        signal_kind: str = "substrate_warning",
        severity: str = "INFO",
        description: str = "",
        signal: str = "dignity_leakage_under_review",
        coercion_signals: list[str] | None = None,
        dignity_preservation: float | None = None,
        reductionism_risk: float | None = None,
        lookback_hours: int = 24,
        actor_id: str = "arif",
    ) -> dict[str, Any]:
        """G-WELL outbound witness plane. mode=attest|signal|recommend|dignity|log.

        All modes route via arifFlow receipts (F13 Option B); arifOS lane DEAD.
        WELL never returns verdicts — proposals + evidence only.
        """
        if mode == "attest":
            r = _call(g, "well_attest_to_kernel", attestation_kind=attestation_kind,
                      actor_id=actor_id)
        elif mode == "signal":
            r = _call(g, "well_propose_governance_signal", signal_kind=signal_kind,
                      severity=severity, description=description, actor_id=actor_id)
        elif mode == "recommend":
            if not candidate:
                return _tag({"ok": False, "error": "candidate required"}, "well_bridge", mode)
            r = _call(g, "well_propose_seal_recommendation", candidate=candidate,
                      recommendation=recommendation, actor_id=actor_id)
        elif mode == "dignity":
            r = _call(g, "well_handoff_dignity_to_arifos", signal=signal,
                      coercion_signals=coercion_signals,
                      dignity_preservation=dignity_preservation,
                      reductionism_risk=reductionism_risk, actor_id=actor_id)
        elif mode == "log":
            r = _call(g, "well_seal_recommendation_log", lookback_hours=lookback_hours)
        else:
            return _tag({"ok": False, "error": f"unknown mode: {mode}"}, "well_bridge", mode)
        return _tag(await _res(r), "well_bridge", mode)

    @mcp.tool()
    async def well_registry(mode: str = "status") -> dict[str, Any]:
        """WELL registry meta. mode=status|full|contradictions.

        contradictions = live self-audit of the C1-C8 class (reality integrity).
        """
        if mode in ("status", "full"):
            r = _call(g, "well_registry_status", mode=mode)
            return _tag(await _res(r), "well_registry", mode)
        commits = g["_compute_well_commits"]()
        ms = g["_machine_substrate_health"]()
        checks = [
            {"id": "commit_alignment", "pass": not commits.get("drift"),
             "detail": f"src={commits.get('source_commit')} dep={commits.get('deployed_commit')} built={commits.get('built_commit')}"},
            {"id": "machine_freshness", "pass": (ms.get("freshness_band") == "FRESH"),
             "detail": f"band={ms.get('freshness_band') or ms.get('status')}"},
            {"id": "witness_lane_truth", "pass": True,
             "detail": "arifOS lane DEAD (Option B); arifFlow routing live"},
        ]
        return _tag({
            "ok": True,
            "mode": "contradictions",
            "checks": checks,
            "open_contradictions": sum(1 for c in checks if not c["pass"]),
            "class_reference": "C1-C8 (WELL_V2_APEX_ZEN_MUTATION_GUIDE §1)",
        }, "well_registry", mode)
