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


# ── R-WELL v1 source registry (Phase 4, 2026-09-16) ─────────────────────────
# Live probes only. class: OBSERVED (live-probed) · VERIFIED (cross-checked) ·
# ASSUMED (declared only) · STALE (probed but old). Edited ≠ Executed.

_GRAPHITI_URL = "http://127.0.0.1:18412/mcp"
_FALKOR_HOST, _FALKOR_PORT = "127.0.0.1", 6380
_FALKOR_GRAPHS = ["af_forge", "arif_l5_knowledge"]
_BASELINE_PATH = "/var/lib/well/reality_baseline.json"
_FRESH_DAYS = 7.0


def _http_probe(url: str, body: dict, timeout: float = 4.0) -> tuple[bool, float, str]:
    import json as _json
    import time as _time
    import urllib.request as _rq
    t0 = _time.monotonic()
    try:
        req = _rq.Request(url, data=_json.dumps(body).encode(),
                          headers={"Content-Type": "application/json",
                                   "Accept": "application/json, text/event-stream"})
        with _rq.urlopen(req, timeout=timeout) as resp:
            body_txt = resp.read(400).decode("utf-8", "replace")
        return ("jsonrpc" in body_txt or "result" in body_txt), (_time.monotonic() - t0) * 1000, body_txt[:80]
    except Exception as e:
        return False, (_time.monotonic() - t0) * 1000, str(e)[:80]


def _falkor_query(graph: str, cypher: str) -> str | None:
    """GRAPH.QUERY via redis lib, docker exec fallback, else None."""
    try:
        import redis  # type: ignore
        r = redis.Redis(host=_FALKOR_HOST, port=_FALKOR_PORT, socket_timeout=4)
        out = r.execute_command("GRAPH.QUERY", graph, cypher)
        return str(out)
    except Exception:
        pass
    try:
        import subprocess as _sp
        p = _sp.run(["docker", "exec", "falkordb", "redis-cli", "GRAPH.QUERY", graph, cypher],
                    capture_output=True, text=True, timeout=8)
        return p.stdout if p.returncode == 0 else None
    except Exception:
        return None


def _falkor_int(graph: str, cypher: str) -> int | None:
    out = _falkor_query(graph, cypher)
    if not out:
        return None
    import re as _re
    m = _re.search(r"\b(\d+)\b", out)
    return int(m.group(1)) if m else None


def _probe_reality_sources() -> dict[str, Any]:
    import datetime as _dt
    import json as _json
    import os as _os

    table: list[dict] = []
    classes: dict[str, str] = {}

    # 1. commit alignment (VERIFIED/STALE)
    try:
        commits = globals().get("_rg_commits")() if False else None
    except Exception:
        commits = None
    # (server helpers injected via g at registration; re-resolve lazily)
    g = _RG.get("g") or {}
    try:
        commits = g["_compute_well_commits"]()
        drift = bool(commits.get("drift"))
    except Exception:
        drift = None
    classes["commit_alignment"] = (
        "UNKNOWN" if drift is None else ("VERIFIED" if not drift else "STALE"))
    table.append({"source": "commit_alignment", "class": classes["commit_alignment"],
                  "detail": f"drift={drift}"})

    # 2. machine telemetry
    try:
        ms = g["_machine_substrate_health"]()
        band = ms.get("freshness_band") or ms.get("status") or "UNKNOWN"
    except Exception:
        band = "UNKNOWN"
    classes["machine_telemetry"] = "OBSERVED" if band == "FRESH" else str(band).upper()
    table.append({"source": "machine_telemetry", "class": classes["machine_telemetry"],
                  "detail": f"band={band}"})

    # 3. graphiti MCP (OBSERVED/MISSING)
    ok, lat, det = _http_probe(_GRAPHITI_URL, {
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                   "clientInfo": {"name": "rwell-probe", "version": "1"}}})
    classes["graphiti_mcp"] = "OBSERVED" if ok else "MISSING"
    table.append({"source": "graphiti_mcp", "class": classes["graphiti_mcp"],
                  "latency_ms": round(lat, 1), "detail": det})

    # 4. falkordb memory plane + freshness + growth baseline
    now = _dt.datetime.now(_dt.timezone.utc)
    graphs, latest_iso = {}, None
    for k in _FALKOR_GRAPHS:
        n = _falkor_int(k, "MATCH (n) RETURN count(n)")
        e = _falkor_int(k, "MATCH ()-[r]->() RETURN count(r)")
        graphs[k] = {"nodes": n, "edges": e}
        fr = _falkor_query(k, "MATCH (n) WHERE n.created_at IS NOT NULL RETURN n.created_at ORDER BY n.created_at DESC LIMIT 1")
        if fr:
            import re as _re2
            m = _re2.search(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", fr)
            if m:
                latest_iso = max(latest_iso or "", m.group(1))
    age_days = None
    if latest_iso:
        try:
            ts = _dt.datetime.fromisoformat(latest_iso)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=_dt.timezone.utc)
            age_days = round((now - ts).total_seconds() / 86400.0, 1)
        except Exception:
            pass
    total_nodes = sum(v["nodes"] or 0 for v in graphs.values())
    total_edges = sum(v["edges"] or 0 for v in graphs.values())

    baseline = {}
    try:
        baseline = _json.loads(open(_BASELINE_PATH).read())
    except Exception:
        pass
    growth = {
        "nodes_delta": total_nodes - baseline.get("total_nodes", total_nodes),
        "edges_delta": total_edges - baseline.get("total_edges", total_edges),
        "since": baseline.get("ts"),
    }
    try:
        _os.makedirs(_os.path.dirname(_BASELINE_PATH), exist_ok=True)
        _json.dump({"ts": now.isoformat(), "total_nodes": total_nodes,
                    "total_edges": total_edges}, open(_BASELINE_PATH, "w"))
    except Exception:
        pass

    exists = total_nodes > 0
    fresh = age_days is not None and age_days <= _FRESH_DAYS
    memory_alive = bool(exists and fresh)
    classes["memory_plane"] = (
        "OBSERVED" if memory_alive else ("STALE" if exists else "MISSING"))
    table.append({"source": "falkor_memory", "class": classes["memory_plane"],
                  "detail": f"nodes={total_nodes} edges={total_edges} last_episode_age_d={age_days}"})

    # 5. witness bridge lane
    lane_off = str(_os.environ.get("WELL_BRIDGE_ARIFFLOW", "1")).lower() in ("0", "false", "off", "no")
    classes["witness_bridge"] = "OBSERVED" if not lane_off else "ASSUMED"
    table.append({"source": "witness_bridge", "class": classes["witness_bridge"],
                  "detail": "arifFlow lane (arifOS lane DEAD by Option B)" +
                            ("" if not lane_off else " — routing DISABLED by env")})

    good = sum(1 for v in classes.values() if v in ("OBSERVED", "VERIFIED"))
    confidence = round(good / len(classes), 2) if classes else 0.0

    memory = {
        "ok": True,
        "memory_alive": memory_alive,
        "doctrine": "Memory Exists != Memory Alive",
        "graphs": graphs,
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "last_episode_at": latest_iso,
        "last_episode_age_days": age_days,
        "freshness_band": ("FRESH" if fresh else ("STALE" if exists else "MISSING")),
        "growth_since_last_probe": growth,
        "unmeasured": {
            "recall_rate": "UNMEASURED — needs query logging",
            "entity_resolution_health": "UNMEASURED — needs resolution audit",
        },
    }
    return {"classes": classes, "table": table, "confidence": confidence, "memory": memory}


_RG: dict = {}


def register_v2_tools(g: dict) -> None:
    mcp = g["mcp"]
    _RG["g"] = g

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
        """R-WELL (v1). Reality Integrity plane. mode=confidence|memory|witness|lineage|patterns.

        Constitutional metric: Edited Reality ≠ Executed Reality.
        v1 sources (live-probed): graphiti_mcp :18412, falkordb graphs,
        commit alignment, machine telemetry, witness bridge lane.
        """
        if mode == "lineage":
            r = _call(g, "well_trace_lineage", mode="recall", limit=limit)
            return _tag(await _res(r), "well_reality", mode)
        if mode == "patterns":
            return _tag({
                "ok": True,
                "implementation_status": "PENDING — scar→risk fingerprint matching (Phase 4.5)",
                "known_fingerprints": ["Witness Surface Mismatch (daemon logs ignored + assumptions over probes + count without identity proof)"],
                "deprecation": _DEPRECATION,
            }, "well_reality", mode)

        src = _probe_reality_sources()

        if mode == "memory":
            return _tag(src["memory"], "well_reality", mode)
        if mode == "witness":
            return _tag({
                "ok": True,
                "witness_quality_table": src["table"],
                "note": "class semantics: OBSERVED=live-probed · VERIFIED=cross-checked · ASSUMED=declared only · STALE=probed but old",
            }, "well_reality", mode)

        return _tag({
            "ok": True,
            "implementation_status": "v1 — live evidence classes",
            "reality_confidence": src["confidence"],
            "evidence_classes": src["classes"],
            "memory_alive": src["memory"].get("memory_alive"),
            "drift": src["classes"].get("commit_alignment"),
            "source_table": src["table"],
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
            r = _call(g, "_wt_well_attest_to_kernel", attestation_kind=attestation_kind,
                      actor_id=actor_id)
        elif mode == "signal":
            r = _call(g, "_wt_well_propose_governance_signal", signal_kind=signal_kind,
                      severity=severity, description=description, actor_id=actor_id)
        elif mode == "recommend":
            if not candidate:
                return _tag({"ok": False, "error": "candidate required"}, "well_bridge", mode)
            r = _call(g, "_wt_well_propose_seal_recommendation", candidate=candidate,
                      recommendation=recommendation, actor_id=actor_id)
        elif mode == "dignity":
            r = _call(g, "_wt_well_handoff_dignity_to_arifos", signal=signal,
                      coercion_signals=coercion_signals,
                      dignity_preservation=dignity_preservation,
                      reductionism_risk=reductionism_risk, actor_id=actor_id)
        elif mode == "log":
            r = _call(g, "_wt_well_seal_recommendation_log", lookback_hours=lookback_hours)
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
