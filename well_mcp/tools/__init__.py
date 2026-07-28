"""well_mcp.tools — Tool canon documentation.

Maps the canon surface (well://) to existing canonical well_* tools.
NO DUPLICATE TOOLS. Where a new advisory capability emerges from
the canon (e.g., interaction substrate readiness), it is documented
as an ADVISORY COMPOSITION — a named logical surface that references
existing tools rather than a new MCP tool function.

ADVISORY COMPOSITIONS (logical, not new MCP tools):
  - well_assess_substrate_readiness   → compose homeo + machine + interaction
  - well_assess_information_asymmetry → compose sovereign_entropy + asymmetries
  - well_assess_consent_integrity     → compose dignity_guard + fatigue + urgency
  - well_trigger_resource_reallocation → compose substrate + bridge/wealth

These are canonical NAMES for surfaces, not implementations. The
implementation lives in the bridge contracts and the existing tool
surface.
"""

from __future__ import annotations

from typing import Any, Dict, List


# Map of canon surface ↔ existing canonical tools.
TOOL_CANON_MAP: Dict[str, List[str]] = {
    # Human substrate
    "well://human/substrate": [
        "well_assess_homeostasis",
        "well_assess_metabolism",
        "well_assess_livelihood",
        "well_validate_vitality",
        "well_guard_dignity",
        "well_classify_substrate",
    ],
    # Machine substrate
    "well://machine/substrate": [
        "well_assess_reliability",
        "well_machine_state",
        "well_registry_status",
    ],
    # Interaction substrate (third concern)
    "well://substrate/interaction": [
        "well_assess_substrate_readiness",  # ADVISORY COMPOSITION
        "well_assess_sovereign_entropy",
        "well_assess_homeostasis",
        "well_assess_reliability",
    ],
    # Information asymmetry (new signal)
    "well://signals/information-asymmetry": [
        "well_assess_information_asymmetry",  # ADVISORY COMPOSITION
        "well_assess_sovereign_entropy",
        "well_measure_gradient",
    ],
    # Consent integrity (F13 protection layer)
    "well://signals/consent-integrity": [
        "well_assess_consent_integrity",  # ADVISORY COMPOSITION
        "well_guard_dignity",
        "well_validate_vitality",
    ],
    # Flux
    "well://metabolic/flux": [
        "well_compute_metabolic_flux",
        "well_measure_gradient",
    ],
    # Coupling
    "well://coupling": [
        "well_couple_human_machine",
        "well_detect_boundary",
    ],
    # Decision routing
    "well://decision/classes": [
        "well_validate_vitality",
        "well_assess_homeostasis",  # for fatigue-aware C-class gating
    ],
    # Doctrine
    "well://doctrine": [
        "well_guard_dignity",
        "well_medical_boundary",
        "well_assess_sovereign_entropy",
    ],
    # Transport loop (5-stage reaction)
    "well://transport/loop": [
        "well_trace_lineage",  # read-only audit
        "well_check_repair",
    ],
    # Federation bridges (cross-organ)
    "well://bridge/wealth": [
        "well_trigger_resource_reallocation",  # ADVISORY COMPOSITION
        "wealth_arifos_judge_handoff",  # cross-organ (WEALTH organ)
    ],
    "well://bridge/geox": [
        "geox_surface_status",  # cross-organ (GEOX organ)
        "well_assess_reliability",
    ],
    "well://bridge/arifos-kernel": [
        "well_attest_to_kernel",  # cross-organ (arifOS organ)
        "arif_judge",  # cross-organ
        "arif_seal",  # cross-organ
    ],
}


# ADVISORY COMPOSITIONS — canonical names for logical surfaces that
# DO NOT have dedicated MCP tool implementations. These names appear
# in canon documents and are bound to existing tools via composition.
ADVISORY_COMPOSITIONS: Dict[str, Dict[str, Any]] = {
    "well_assess_substrate_readiness": {
        "canonical_name": "well_assess_substrate_readiness",
        "composes": [
            "well_assess_homeostasis",
            "well_assess_reliability",
            "well_assess_information_asymmetry",
            "well_assess_consent_integrity",
        ],
        "output": "OPTIMAL | STABLE | WARNING | DEGRADED | CRITICAL | CAPTURED",
        "first_class": True,
        "rationale": (
            "Interaction substrate readiness is a first-class concern; "
            "currently composed from existing substrate tools. If usage "
            "shows hot path, may be promoted to dedicated MCP tool."
        ),
    },
    "well_assess_information_asymmetry": {
        "canonical_name": "well_assess_information_asymmetry",
        "composes": [
            "well_assess_sovereign_entropy",
            "well_measure_gradient",
        ],
        "output": "LOW | MEDIUM | HIGH | EXTRACTION_RISK",
        "first_class": True,
        "rationale": (
            "Asymmetry is a substrate signal, not just a doctrine check. "
            "Currently composed; can be promoted if hot path."
        ),
    },
    "well_assess_consent_integrity": {
        "canonical_name": "well_assess_consent_integrity",
        "composes": [
            "well_guard_dignity",
            "well_validate_vitality",
            "well_assess_homeostasis",
        ],
        "output": "INTACT | PRESSURED | DEGRADED | INVALID",
        "first_class": True,
        "rationale": (
            "Consent integrity is the F13 protection layer above dignity "
            "floor. Distinct from dignity check; specifically gates "
            "irreversible actions."
        ),
    },
    "well_trigger_resource_reallocation": {
        "canonical_name": "well_trigger_resource_reallocation",
        "composes": [
            "well_trigger_resource_reallocation_signal",  # internal
            "wealth_arifos_judge_handoff",  # WEALTH bridge
        ],
        "output": "NONE | WATCH | REALLOCATE | FREEZE",
        "first_class": True,
        "rationale": (
            "Reallocation trigger when substrate degrades. Bridges to "
            "WEALTH via bridge/wealth contract. Always informational; "
            "never auto-executes."
        ),
    },
}


def register_tools(mcp: Any) -> List[str]:
    """Register tool documentation resource with FastMCP.

    No new MCP tools are added. This registers a single canon resource
    that documents how existing tools map to the canon surface, plus
    the 4 ADVISORY COMPOSITIONS for the interaction substrate signals.
    """

    @mcp.resource("well://tools/canon_map")
    def tools_canon_map() -> str:
        """Map of canon surface (well://) ↔ existing canonical tools."""
        lines = [
            "well_mcp.tools — Canon Map (NO new MCP tools)",
            "=" * 50,
            "",
            "ADVISORY COMPOSITIONS are canonical NAMES for logical",
            "surfaces. They reference existing tools, not new MCP",
            "implementations. Promotion to first-class MCP tool is",
            "possible if usage shows a hot path.",
            "",
        ]
        for canon, tools in sorted(TOOL_CANON_MAP.items()):
            lines.append(f"  {canon}")
            for t in tools:
                lines.append(f"    - {t}")
            lines.append("")
        lines.extend(
            [
                "ADVISORY COMPOSITIONS (canonical names, composed):",
                "",
            ]
        )
        for name, spec in sorted(ADVISORY_COMPOSITIONS.items()):
            lines.append(f"  {name}")
            lines.append(f"    output: {spec['output']}")
            lines.append(f"    composes: {', '.join(spec['composes'])}")
            lines.append("")
        lines.extend(
            [
                "Why no new MCP tools?",
                "  - Existing 17+ well_* tools cover the substrate surface",
                "  - 4 advisory compositions cover interaction-substrate signals",
                "  - Canon documents the names; existing tools provide the logic",
                "  - New tools would duplicate; composition references instead",
                "",
                "When an advisory composition becomes hot path:",
                "  - Promote to dedicated MCP tool in server.py",
                "  - Keep the canonical name (it is now the tool name)",
                "  - Add to well://registry for surface visibility",
            ]
        )
        return "\n".join(lines)

    return ["well://tools/canon_map"]


__all__ = ["register_tools", "TOOL_CANON_MAP", "ADVISORY_COMPOSITIONS"]
