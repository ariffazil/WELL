"""well_mcp.tools — Tool documentation only.

NO NEW TOOLS NEEDED. Existing well_* tools in server.py cover the
machine-intelligence surface:
  - well_assess_reliability       → machine state
  - well_machine_state            → machine state
  - well_compute_metabolic_flux   → flux
  - well_coupled_readiness        → human × machine
  - well_assess_homeostasis       → human state
  - well_assess_metabolism        → metabolism
  - well_assess_livelihood        → livelihood

This module documents how existing tools map to the new canon
surface (well://). It does NOT add new MCP tool functions.
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
}


def register_tools(mcp: Any) -> List[str]:
    """Register tool documentation resource with FastMCP.

    No new tools are added. This registers a single canon resource
    that documents how existing tools map to the canon surface.
    """

    @mcp.resource("well://tools/canon_map")
    def tools_canon_map() -> str:
        """Map of canon surface (well://) ↔ existing canonical tools."""
        lines = [
            "well_mcp.tools — Canon Map (NO new tools added)",
            "=" * 50,
            "",
        ]
        for canon, tools in sorted(TOOL_CANON_MAP.items()):
            lines.append(f"  {canon}")
            for t in tools:
                lines.append(f"    - {t}")
            lines.append("")
        lines.extend(
            [
                "Why no new tools?",
                "  - Existing 17+ tools cover the surface",
                "  - New canon resources DOCUMENT the existing surface",
                "  - Canon documentation is the binding, not new tools",
                "  - New tools would duplicate; canon references them instead",
                "",
                "If a new well_* tool IS needed in the future:",
                "  - Add it to server.py with arifOS register path",
                "  - Add a canon entry here for documentation",
                "  - Update well://registry to surface it",
            ]
        )
        return "\n".join(lines)

    return ["well://tools/canon_map"]


__all__ = ["register_tools", "TOOL_CANON_MAP"]
