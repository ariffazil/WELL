"""
WELL MCP Server — FastMCP v1.0.0

Governed constitutional organ for arifOS Federation.
Domain Law: SUBSTRATE_LAW
Authority: REFLECT_ONLY — mirror, never judge

Sovereign: Muhammad Arif bin Fazil (F13)
Date: 2026-07-16
License: AGPL-3.0

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from fastmcp import FastMCP, Context
from typing import Literal, Optional
import json

# ============================================================
# 1. ORGAN IDENTITY
# ============================================================

mcp = FastMCP(
    name="well-mcp",
    version="1.0.0",
    instructions="WELL — Human Readiness Organ for arifOS Federation. Domain Law: SUBSTRATE_LAW. Authority: REFLECT_ONLY.",
)

# ============================================================
# 2. IMPORT TOOLS FROM MODULAR STRUCTURE
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

# F6 MARUAH floor instrument (v0 — modular target only, cutover-first; see
# tools/f6_maruah.py docstring: NOT served by :18083 until H1 parity, OS-1)
from .tools.f6_maruah import well_measure_floor_f6


# ── P0-B (sovereign 2026-07-18): legacy alias for well_system_registry_status ─
# The audit's tooling called well_system_registry_status but the modern
# canonical name is well_registry_status. Re-bind the legacy name as an
# alias so the advertised surface matches what the connector can dispatch.
async def well_system_registry_status(ctx: Context, mode: str = "status") -> dict:
    """Legacy alias: delegates to well_registry_status."""
    return await well_registry_status(ctx, mode=mode)  # type: ignore[arg-type]


# ============================================================
# 3. IMPORT RESOURCES FROM MODULAR STRUCTURE
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

from .prompts.definitions import (
    well_sense,
    well_qc,
    well_interpret,
)

# ============================================================
# 4. REGISTER TOOLS (27 Canonical)
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
# Legacy alias (P0-B audit fix): keep well_system_registry_status available
mcp.tool()(well_system_registry_status)

# Floor F6 MARUAH instrument (v0 — modular target only; kernel wiring pending OS-1)
mcp.tool()(well_measure_floor_f6)

# ============================================================
# 5. REGISTER RESOURCES (29 Canonical)
# ============================================================

# Identity Resources
mcp.resource("well://identity")(well_identity)
mcp.resource("well://doctrine")(well_doctrine)

# Signal Resources
mcp.resource("well://bio_signals")(well_bio_signals)
mcp.resource("well://flux")(well_flux)
mcp.resource("well://decision_classes")(well_decision_classes)
mcp.resource("well://coupling")(well_coupling)
mcp.resource("well://physics_laws")(well_physics_laws)

# Contract Resources
mcp.resource("well://human_substrate")(well_human_substrate)
mcp.resource("well://machine_substrate")(well_machine_substrate)
mcp.resource("well://interaction_substrate")(well_interaction_substrate)
mcp.resource("well://info_asymmetry")(well_info_asymmetry)
mcp.resource("well://consent_integrity")(well_consent_integrity)

# Transport Resources
mcp.resource("well://transport_loop")(well_transport_loop)
mcp.resource("well://chemistry_glue")(well_chemistry_glue)

# Bridge Resources
mcp.resource("well://bridge_wealth")(well_bridge_wealth)
mcp.resource("well://bridge_geox")(well_bridge_geox)
mcp.resource("well://bridge_arifos_kernel")(well_bridge_arifos_kernel)

# State Resources
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
# 6. REGISTER PROMPTS (3 Canonical)
# ============================================================

mcp.prompt()(well_sense)
mcp.prompt()(well_qc)
mcp.prompt()(well_interpret)

# ============================================================
# 7. ENTRY POINT
# ============================================================

if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=18083)
