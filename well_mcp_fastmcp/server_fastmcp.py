"""
WELL MCP Server — FastMCP v1.1.0

Governed constitutional organ for arifOS Federation.
Domain Law: SUBSTRATE_LAW
Authority: REFLECT_ONLY — mirror, never judge

Sovereign: Muhammad Arif bin Fazil (F13)
Date: 2026-07-25 (updated — 12 prompts, somatic boundary, outputSchema stubs)
License: AGPL-3.0

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

from fastmcp import FastMCP
from typing import Any

# ============================================================
# 1. ORGAN IDENTITY
# ============================================================

mcp = FastMCP(
    name="well-mcp",
    version="1.1.0",
    instructions=(
        "WELL — Human Readiness Organ for arifOS Federation. "
        "Domain Law: SUBSTRATE_LAW. Authority: REFLECT_ONLY. "
        "8 public tools discoverable, 19 internal tools callable, "
        "12 prompts, 29 resources."
    ),
)

# ============================================================
# 2. SOMATIC TOOL SET — canonical 8 public tools
# ============================================================

SOMATIC_TOOLS = frozenset(
    {
        "well_classify_substrate",
        "well_trace_lineage",
        "well_assess_homeostasis",
        "well_check_repair",
        "well_validate_vitality",
        "well_assess_reliability",
        "well_guard_dignity",
        "well_registry_status",
    }
)

# ============================================================
# 3. IMPORT TOOLS FROM MODULAR STRUCTURE
# ============================================================

from .tools.h_well import (
    well_assess_homeostasis,
    well_assess_livelihood,
    well_assess_sovereign_entropy,
    well_guard_dignity,
    well_validate_vitality,
    well_medical_boundary,
    well_classify_state,
    well_dark_geometry_mirror,
    well_sabar_latency,
    well_trust_compression,
    well_niat_impact_mirror,
    well_correction_capacity,
)

from .tools.m_well import (
    well_assess_reliability,
    well_check_repair,
)

from .tools.c_well import (
    well_assess_metabolism,
    well_compute_metabolic_flux,
    well_trace_lineage,
    well_measure_gradient,
)

from .tools.g_well import (
    well_classify_substrate,
    well_detect_boundary,
)

from .tools.federation import (
    well_attest_to_kernel,
    well_handoff_dignity_to_arifos,
    well_handoff_livelihood_to_wealth,
    well_registry_status,
    well_signal_coverage,
)

# ============================================================
# 4. IMPORT RESOURCES (29 Canonical)
# ============================================================

from .resources.definitions import (
    well_identity,
    well_doctrine,
    well_bio_signals,
    well_flux,
    well_decision_classes,
    well_coupling,
    well_physics_laws,
    well_human_substrate,
    well_machine_substrate,
    well_interaction_substrate,
    well_info_asymmetry,
    well_consent_integrity,
    well_transport_loop,
    well_chemistry_glue,
    well_bridge_wealth,
    well_bridge_geox,
    well_bridge_arifos_kernel,
    well_registry,
    well_afwell_schema,
    well_afwell_state_arif,
    well_afwell_events_recent,
    well_afwell_floors,
    well_afwell_vitals_arif,
    well_afwell_substrate_registry,
    well_afwell_telemetry,
    well_afwell_readiness,
    well_afwell_sovereign_entropy,
    well_afwell_causal_dag,
)

# ============================================================
# 5. IMPORT PROMPTS (12: 3 legacy + 9 production)
# ============================================================

from .prompts.definitions import (
    # Legacy refactored prompts (3)
    well_sense,
    well_qc,
    well_interpret,
    # Production prompts (9) — merged 2026-07-25
    prompt_daily_reflection,
    prompt_recovery_protocol,
    prompt_readiness_brief,
    prompt_substrate_classify,
    prompt_niat_check,
    prompt_fatigue_boundary_review,
    prompt_energy_assessment,
    prompt_shadow_check,
    prompt_individuation_readiness,
)

# ============================================================
# 6. REGISTER TOOLS (27 Canonical)
# ============================================================

# H-WELL Tools
mcp.tool()(well_assess_homeostasis)
mcp.tool()(well_assess_livelihood)
mcp.tool()(well_assess_sovereign_entropy)
mcp.tool()(well_guard_dignity)
mcp.tool()(well_validate_vitality)
mcp.tool()(well_medical_boundary)
mcp.tool()(well_classify_state)
mcp.tool()(well_dark_geometry_mirror)
mcp.tool()(well_sabar_latency)
mcp.tool()(well_trust_compression)
mcp.tool()(well_niat_impact_mirror)
mcp.tool()(well_correction_capacity)

# M-WELL Tools
mcp.tool()(well_assess_reliability)
mcp.tool()(well_check_repair)

# C-WELL Tools
mcp.tool()(well_assess_metabolism)
mcp.tool()(well_compute_metabolic_flux)
mcp.tool()(well_trace_lineage)
mcp.tool()(well_measure_gradient)

# G-WELL Tools
mcp.tool()(well_classify_substrate)
mcp.tool()(well_detect_boundary)

# Federation Tools
mcp.tool()(well_attest_to_kernel)
mcp.tool()(well_handoff_dignity_to_arifos)
mcp.tool()(well_handoff_livelihood_to_wealth)
mcp.tool()(well_registry_status)
mcp.tool()(well_signal_coverage)

# ============================================================
# 7. REGISTER RESOURCES (29 Canonical)
# ============================================================

mcp.resource("well://identity")(well_identity)
mcp.resource("well://doctrine")(well_doctrine)
mcp.resource("well://bio_signals")(well_bio_signals)
mcp.resource("well://flux")(well_flux)
mcp.resource("well://decision_classes")(well_decision_classes)
mcp.resource("well://coupling")(well_coupling)
mcp.resource("well://physics_laws")(well_physics_laws)
mcp.resource("well://human_substrate")(well_human_substrate)
mcp.resource("well://machine_substrate")(well_machine_substrate)
mcp.resource("well://interaction_substrate")(well_interaction_substrate)
mcp.resource("well://info_asymmetry")(well_info_asymmetry)
mcp.resource("well://consent_integrity")(well_consent_integrity)
mcp.resource("well://transport_loop")(well_transport_loop)
mcp.resource("well://chemistry_glue")(well_chemistry_glue)
mcp.resource("well://bridge_wealth")(well_bridge_wealth)
mcp.resource("well://bridge_geox")(well_bridge_geox)
mcp.resource("well://bridge_arifos_kernel")(well_bridge_arifos_kernel)
mcp.resource("well://registry")(well_registry)
mcp.resource("well://afwell_schema")(well_afwell_schema)
mcp.resource("well://afwell_state_arif")(well_afwell_state_arif)
mcp.resource("well://afwell_events_recent")(well_afwell_events_recent)
mcp.resource("well://afwell_floors")(well_afwell_floors)
mcp.resource("well://afwell_vitals_arif")(well_afwell_vitals_arif)
mcp.resource("well://afwell_substrate_registry")(well_afwell_substrate_registry)
mcp.resource("well://afwell_telemetry")(well_afwell_telemetry)
mcp.resource("well://afwell_readiness")(well_afwell_readiness)
mcp.resource("well://afwell_sovereign_entropy")(well_afwell_sovereign_entropy)
mcp.resource("well://afwell_causal_dag")(well_afwell_causal_dag)

# ============================================================
# 8. REGISTER PROMPTS (12 Canonical)
# ============================================================

# Legacy refactored prompts
mcp.prompt()(well_sense)
mcp.prompt()(well_qc)
mcp.prompt()(well_interpret)

# Production prompts — merged 2026-07-25
mcp.prompt()(prompt_daily_reflection)
mcp.prompt()(prompt_recovery_protocol)
mcp.prompt()(prompt_readiness_brief)
mcp.prompt()(prompt_substrate_classify)
mcp.prompt()(prompt_niat_check)
mcp.prompt()(prompt_fatigue_boundary_review)
mcp.prompt()(prompt_energy_assessment)
mcp.prompt()(prompt_shadow_check)
mcp.prompt()(prompt_individuation_readiness)

# ============================================================
# 9. ENFORCE SOMATIC BOUNDARY
# ============================================================
# Hide internal tools from MCP tools/list while keeping them callable.
# Production server.py does this via _enforce_somatic_boundary().
# This mirrors that behavior for the refactored server.


def _enforce_somatic_boundary(mcp_server: FastMCP) -> None:
    """Filter autonomic tools from public MCP tools/list response."""
    somatic = SOMATIC_TOOLS
    provider = getattr(mcp_server, "_local_provider", None)
    if not provider:
        return
    original_list = getattr(provider, "list_tools", None)
    if original_list is None:
        return

    async def _filtered_list_tools(*args: Any, **kwargs: Any) -> list[Any]:
        result = await original_list(*args, **kwargs)
        return [t for t in result if getattr(t, "name", "") in somatic]

    provider.list_tools = _filtered_list_tools


_enforce_somatic_boundary(mcp)

# ============================================================
# 10. ENTRY POINT
# ============================================================

if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=18083)
