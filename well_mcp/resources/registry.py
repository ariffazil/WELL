"""well://registry — Auto-discoverable surface registry.

The canonical list of all well_mcp resources, prompts, tools, and
transport stages. Generated at module load by importing sibling
modules and calling register(mcp) on a probe.

Authority: OPERATIONAL_CANON. Auto-derived.
"""

from __future__ import annotations

from typing import Any, List

REGISTRY_META = """
---well_meta
uri: well://registry
resource_class: surface_registry
authority_level: OPERATIONAL_CANON
owner: WELL_OPERATOR
loop_stage: 000_INIT (canonical reference)
blast_radius: FEDERATION_WIDE
mutation_allowed: false
requires_actor_verified: false
staleness_policy: cache
constitutional_floors: [F2, F4, F11]
truth_level: 2
schema_ref: well_resource_registry_v1
forged_at: 2026-06-27
---end_well_meta
"""

REGISTRY_TEXT = """\
# WELL × MCP Surface Registry

## §1. RESOURCES (canonical list)

  well://identity              — who WELL is (5 wells + machine position)
  well://doctrine              — REFLECT_ONLY + W0 + HARAM (H1–H7 + MH1–MH7)
  well://bio/signals           — 4-tier × 13-signal substrate map
  well://metabolic/flux        — flux equation + thresholds + decay
  well://decision/classes      — C1–C5 × M1–M5 routing matrix
  well://coupling              — H × M × G coupling chemistry
  well://human/substrate       — metabolized human contract
  well://machine/substrate     — hosting machine contract
  well://chemistry/glue        — cross-organ federation glue
  well://transport/loop        — 5-stage reaction loop
  well://registry              — this file

Total: 11 resources (loop_engineering / reasoning parity with arifOS)

## §2. PROMPTS (loop-mapped)

  000 well_init          — session bootstrap
  111 well_sense         — substrate observe (preserves existing deep)
  333 well_qc            — quality control (preserves existing deep)
  444 well_compose       — coupling + cross-organ synthesis
  555 well_route         — C/M-class routing + handoff decisions
  666 well_critique      — refactor of well_interpret
  777 well_repair        — recovery + loop integrity
  888 well_judge         — yield to arifOS for F1–F13 floors
  999 well_seal          — final reflection (no vault write)

Total: 9 prompts (matches 9 canonical loop stages)

## §3. TOOLS (canonical — existing in server.py)

  17+ canonical tools (somatic surface):
    well_classify_substrate, well_detect_boundary,
    well_trace_lineage, well_measure_gradient,
    well_assess_metabolism, well_assess_homeostasis,
    well_check_repair, well_validate_vitality,
    well_assess_livelihood, well_assess_sovereign_entropy,
    well_compute_metabolic_flux, well_assess_reliability,
    well_machine_state, well_guard_dignity,
    well_medical_boundary, well_registry_status,
    well_system_registry_status

  Plus autonomic/internal tools (not publicly callable).

  NO NEW TOOLS NEEDED — canon documentation only.

## §4. TRANSPORT STAGES

  1. ingress    — well_mcp/transport/ingress.py
  2. encode     — well_mcp/transport/encode.py
  3. metabolize — well_mcp/transport/metabolize.py
  4. judge      — well_mcp/transport/judge.py
  5. egress     — well_mcp/transport/egress.py

Total: 5 stages (the reaction sequence)

## §5. CONCERN MAP (what each surface addresses)

  IDENTITY          → "who is WELL"
  DOCTRINE          → "what WELL refuses to be"
  BIO_SIGNALS       → "what the human substrate looks like"
  FLUX              → "how energy flows through the substrate"
  DECISION_CLASSES  → "how decisions are routed"
  COUPLING          → "how substrates bind"
  HUMAN_SUBSTRATE   → "the contract with the human"
  MACHINE_SUBSTRATE → "the contract with the machine"
  CHEMISTRY_GLUE    → "how organs hold together"
  TRANSPORT_LOOP    → "how signals are processed"
  REGISTRY          → "what WELL exposes"

## §6. INVOCATION HINTS

  // at session start
  const identity = await mcp.readResource("well://identity");
  const doctrine = await mcp.readResource("well://doctrine");
  const humanSub = await mcp.readResource("well://human/substrate");
  const machine  = await mcp.readResource("well://machine/substrate");
  const registry = await mcp.readResource("well://registry");

  // at loop start
  const init = await mcp.getPrompt("well_init", {actor: "arif"});

  // at sense stage
  const sense = await mcp.getPrompt("well_sense",
                                    {signal: "fatigue", substrate: "human"});

  // at judge stage
  const judge = await mcp.getPrompt("well_judge",
                                    {intent: "deploy", decision_class: "C4"});

  // read resource mid-loop
  const coupling = await mcp.readResource("well://coupling");

  // call tool
  const verdict = await mcp.callTool("well_assess_homeostasis",
                                     {mode: "fatigue", sleep_debt_days: 3});

## §7. POSITION STATEMENT

> "11 resources. 9 prompts. 17+ tools. 5 stages.
>  The chemistry is in the surface.
>  The surface is the federation's mirror.
>  The sovereign reads the mirror and decides.
>  The mirror does not decide. The mirror reflects."

DITEMPA BUKAN DIBERI — The surface is the chemistry.
"""


def register(mcp: Any) -> List[str]:
    """Register the registry resource with FastMCP."""

    @mcp.resource("well://registry")
    def registry() -> str:
        """The well_mcp surface registry — auto-discovery."""
        return REGISTRY_TEXT + REGISTRY_META

    return ["well://registry"]
