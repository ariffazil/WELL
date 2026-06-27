"""well_mcp — Canonical MCP surface for the WELL federation organ.

WELL is the substrate vitality mirror. It reflects the human substrate
(biology, cognition, dignity, livelihood) and the machine substrate
(physics, entropy, governance). It does NOT decide; it reflects.

This package exposes the canon surface (resources), loop-mapped prompts,
and the 5-stage transport reaction loop. NO new well_* tools are added;
existing tools in /root/WELL/server.py cover the somatic surface.

Authority: REFLECT_ONLY. Never writes vault. Never triggers downstream.

Authoritative loop (5 stages):
  1. ingress    well_mcp/transport/ingress.py
  2. encode     well_mcp/transport/encode.py
  3. metabolize well_mcp/transport/metabolize.py
  4. judge      well_mcp/transport/judge.py
  5. egress     well_mcp/transport/egress.py

Authoritative canon (11 resources):
  well://identity, well://doctrine, well://bio/signals,
  well://metabolic/flux, well://decision/classes, well://coupling,
  well://human/substrate, well://machine/substrate,
  well://chemistry/glue, well://transport/loop,
  well://physics/laws, well://registry

Loop-mapped prompts (9 stages):
  000 well_init → 111 well_sense → 333 well_qc → 444 well_compose →
  555 well_route → 666 well_critique → 777 well_repair →
  888 well_judge → 999 well_seal

DITEMPA BUKAN DIBERI — The chemistry is in the coupling.
"""

from __future__ import annotations

from typing import Any, Dict, List

# Sub-packages.
from . import resources, prompts, transport, tools


REGISTERED_SURFACES: Dict[str, int] = {
    "resources": 0,
    "prompts": 0,
    "transport": 0,
    "tools": 0,
}


def register_all(mcp: Any) -> Dict[str, List[str]]:
    """Register the full well_mcp canon surface with FastMCP.

    Returns a dict of category → list of URIs/prompts registered.

    Best-effort: any sub-package that fails to register is logged
    but does not abort the others.

    Authority: REFLECT_ONLY. Never mutates state.
    """
    registered: Dict[str, List[str]] = {
        "resources": [],
        "prompts": [],
        "transport": [],
        "tools": [],
    }

    # Resources.
    try:
        registered["resources"] = resources.register_resources(mcp)
        REGISTERED_SURFACES["resources"] = len(registered["resources"])
    except Exception as e:
        import sys

        print(f"[well_mcp] resources failed: {e}", file=sys.stderr)

    # Prompts.
    try:
        registered["prompts"] = prompts.register_prompts(mcp)
        REGISTERED_SURFACES["prompts"] = len(registered["prompts"])
    except Exception as e:
        import sys

        print(f"[well_mcp] prompts failed: {e}", file=sys.stderr)

    # Transport stages (register the diagnostic resource).
    try:
        registered["transport"] = transport.register_transport(mcp)
        REGISTERED_SURFACES["transport"] = len(registered["transport"])
    except Exception as e:
        import sys

        print(f"[well_mcp] transport failed: {e}", file=sys.stderr)

    # Tools (documentation only — no new tools).
    try:
        registered["tools"] = tools.register_tools(mcp)
        REGISTERED_SURFACES["tools"] = len(registered["tools"])
    except Exception as e:
        import sys

        print(f"[well_mcp] tools failed: {e}", file=sys.stderr)

    return registered


__all__ = [
    "register_all",
    "REGISTERED_SURFACES",
    "resources",
    "prompts",
    "transport",
    "tools",
]
