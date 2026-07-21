"""
WELL MCP Tools — M-WELL Machine Substrate Tools.

Domain Law: SUBSTRATE_LAW
Authority: REFLECT_ONLY — mirror, never judge

Sovereign: Muhammad Arif bin Fazil (F13)
Date: 2026-07-16 · P1 wired: 2026-07-21
License: AGPL-3.0

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from fastmcp import Context
from typing import Literal, Optional
import json

from ..replay.receipt import generate_replay_receipt
from .evidence import build_unknown_result


async def well_assess_reliability(
    ctx: Context,
    mode: Literal["health", "machine", "tools", "institutions"] = "health",
) -> dict:
    """Assess machine, tool, institution, and operational reliability.

    Modes:
      health       — Full federation machine health (Prometheus + vitality_gate)
      machine      — Raw Prometheus node_exporter telemetry (CPU, MemAvailable, PSI, disk, net)
      tools        — Tool health probe (P3 — not yet wired)
      institutions — Institutional reliability audit (P3 — not yet wired)
    """
    if mode in ("health", "machine"):
        # P1 WIRED: Prometheus node_exporter adapter → live machine telemetry
        try:
            from adapters.prometheus_machine_adapter import collect_from_prometheus
            from vitality_gate import assess_m_well

            ms = collect_from_prometheus()

            # Build result from real telemetry
            cpu = ms.get("cpu", {})
            mem = ms.get("memory", {})
            disk = ms.get("disk", {})

            avail_gib = (mem.get("available_kb") or 0) / (1024 * 1024)
            total_gib = (mem.get("total_kb") or 1) / (1024 * 1024)
            mem_pct = (
                round((1 - avail_gib / max(total_gib, 1)) * 100, 1)
                if total_gib > 0
                else None
            )

            result = build_unknown_result(
                "well_assess_reliability",
                missing=[],
                note=None,
            )
            # Override with real telemetry
            result.update(
                {
                    "verdict": "OBSERVED",
                    "confidence": ms.get("confidence", 0.90),
                    "truth_class": "LIVE",
                    "evidence_label": "OBS",
                    "missing_evidence": [],
                    "source": "prometheus://node-exporter",
                    "timestamp": ms.get("timestamp"),
                    "queries_succeeded": ms.get("queries_succeeded", 0),
                    "queries_failed": ms.get("queries_failed", 0),
                    "machine": {
                        "cpu": {
                            "load_1m": cpu.get("load_1m"),
                            "load_5m": cpu.get("load_5m"),
                            "load_15m": cpu.get("load_15m"),
                            "idle_pct": cpu.get("idle_pct"),
                            "iowait_pct": cpu.get("iowait_pct"),
                            "steal_pct": cpu.get("steal_pct"),
                        },
                        "memory": {
                            "available_gib": round(avail_gib, 1) if avail_gib else None,
                            "total_gib": round(total_gib, 1) if total_gib else None,
                            "used_pct": mem_pct,
                            "swap_used_gib": round(
                                (mem.get("swap_used_kb") or 0) / (1024 * 1024), 1
                            ),
                            "swap_total_gib": round(
                                (mem.get("swap_total_kb") or 0) / (1024 * 1024), 1
                            ),
                        },
                        "disk": {
                            "root_used_pct": disk.get("root_used_pct"),
                            "root_free_gb": disk.get("root_free_gb"),
                        },
                        "network": ms.get("net", {}),
                    },
                }
            )

            # Enrich with vitality gate assessment if available
            try:
                gate = assess_m_well()
                result["vitality_gate"] = {
                    "state": gate.get("state"),
                    "rank": gate.get("rank"),
                    "evidence": gate.get("evidence"),
                    "hysteresis": gate.get("hysteresis"),
                }
            except Exception:
                result["vitality_gate"] = {
                    "state": "UNKNOWN",
                    "note": "vitality_gate unavailable",
                }

            # Generate replay receipt
            receipt = generate_replay_receipt(
                tool="well_assess_reliability",
                session_id="UNBOUND",
                actor_id=getattr(ctx, "actor_id", "unknown"),
                inputs={"mode": mode},
                outputs=result,
                truth_class="LIVE",
                evidence_label="OBS",
            )

            return {**result, "replay_receipt": receipt.model_dump()}

        except Exception as exc:
            # Prometheus adapter failed — fall back to UNKNOWN
            result = build_unknown_result(
                "well_assess_reliability",
                missing=["prometheus_adapter_error"],
                note=f"Prometheus adapter failed: {exc}. Machine state is UNKNOWN.",
            )
            receipt = generate_replay_receipt(
                tool="well_assess_reliability",
                session_id="UNBOUND",
                actor_id=getattr(ctx, "actor_id", "unknown"),
                inputs={"mode": mode},
                outputs=result,
            )
            return {**result, "replay_receipt": receipt.model_dump()}

    # tools / institutions — not yet wired
    result = build_unknown_result(
        "well_assess_reliability",
        missing=["tool_health_probe", "institution_audit"],
        note=f"Mode '{mode}' is not yet wired to live telemetry. Machine health mode is available.",
    )

    receipt = generate_replay_receipt(
        tool="well_assess_reliability",
        session_id="UNBOUND",
        actor_id=getattr(ctx, "actor_id", "unknown"),
        inputs={"mode": mode},
        outputs=result,
    )

    return {**result, "replay_receipt": receipt.model_dump()}


async def well_check_repair(
    ctx: Context,
    mode: Literal["precheck", "postcheck", "recovery"] = "precheck",
    task_description: Optional[str] = None,
    decision_class: Optional[str] = None,
    source: Optional[str] = None,
    intensity: Optional[float] = None,
    outcome: Optional[str] = None,
) -> dict:
    """Check repair, recovery, resilience, and forge cycle integrity.

    P4 WIRED (2026-07-21): When task_description is provided, checks against
    the repair allowlist. Returns matched repair options with autonomy bands.
    Precheck/postcheck/recovery modes without task_description return the
    full allowlist for reference.
    """
    try:
        from repair_allowlist import (
            get_repair_options,
            get_allowlisted_services,
            get_allowlisted_containers,
            ALLOWLIST,
        )

        if task_description:
            # Match task description against allowlist symptoms
            options = get_repair_options([task_description])
            if options:
                result = build_unknown_result(
                    "well_check_repair",
                    missing=["arifos_judgment", "aforge_lease"],
                    note=None,
                )
                result.update(
                    {
                        "verdict": "MATCHED",
                        "confidence": 0.70,
                        "truth_class": "INFERRED",
                        "evidence_label": "DER",
                        "mode": mode,
                        "task_description": task_description,
                        "repair_options": options,
                        "recommendation": (
                            f"Found {len(options)} matching repair option(s). "
                            "All require arifOS judgment + A-FORGE lease before execution."
                        ),
                        "allowlisted_services": get_allowlisted_services(),
                        "allowlisted_containers": get_allowlisted_containers(),
                    }
                )
            else:
                result = build_unknown_result(
                    "well_check_repair",
                    missing=["matching_allowlist_entry"],
                    note=f"No allowlist entry matches: '{task_description}'. "
                    "Propose the repair action for allowlist review.",
                )
                result["verdict"] = "NO_MATCH"
                result["full_allowlist_size"] = len(ALLOWLIST)
        else:
            # No task — return full allowlist for reference
            result = build_unknown_result(
                "well_check_repair",
                missing=["task_description"],
                note="Provide task_description to check against the repair allowlist.",
            )
            result.update(
                {
                    "verdict": "ALLOWLIST_REFERENCE",
                    "total_entries": len(ALLOWLIST),
                    "entries_by_band": {
                        "A1_diagnosis": len(
                            [e for e in ALLOWLIST if e["band"] == "A1"]
                        ),
                        "A2_allowlisted": len(
                            [e for e in ALLOWLIST if e["band"] == "A2"]
                        ),
                        "A3_judgment_gated": len(
                            [e for e in ALLOWLIST if e["band"] == "A3"]
                        ),
                        "A4_prohibited": len(
                            [e for e in ALLOWLIST if e["band"] == "A4"]
                        ),
                    },
                    "allowlisted_services": get_allowlisted_services(),
                    "allowlisted_containers": get_allowlisted_containers(),
                    "phase": "P4_BOUNDED_REPAIR",
                    "note": "Phase 1: diagnosis only. Phase 2: allowlisted reversible repair. "
                    "All repairs require arifOS judgment + A-FORGE lease.",
                }
            )

        receipt = generate_replay_receipt(
            tool="well_check_repair",
            session_id="UNBOUND",
            actor_id=getattr(ctx, "actor_id", "unknown"),
            inputs={
                "mode": mode,
                "task_description": task_description,
                "decision_class": decision_class,
                "source": source,
                "intensity": intensity,
                "outcome": outcome,
            },
            outputs=result,
        )
        return {**result, "replay_receipt": receipt.model_dump()}

    except ImportError:
        pass

    # Fallback: allowlist module not available
    result = build_unknown_result(
        "well_check_repair",
        missing=["repair_allowlist", "service_state", "rollback_capability"],
        note="Repair allowlist module not available. Repair readiness is UNKNOWN.",
    )
    receipt = generate_replay_receipt(
        tool="well_check_repair",
        session_id="UNBOUND",
        actor_id=getattr(ctx, "actor_id", "unknown"),
        inputs={
            "mode": mode,
            "task_description": task_description,
            "decision_class": decision_class,
            "source": source,
            "intensity": intensity,
            "outcome": outcome,
        },
        outputs=result,
    )
    return {**result, "replay_receipt": receipt.model_dump()}
