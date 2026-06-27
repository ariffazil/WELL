"""well_mcp.prompts — loop-mapped prompt registry.

9 prompts mapped to the canonical 9-stage loop:
  000 well_init → 111 well_sense → 333 well_qc → 444 well_compose →
  555 well_route → 666 well_critique → 777 well_repair →
  888 well_judge → 999 well_seal
"""

from __future__ import annotations

from typing import Any, List

# Import all loop-mapped prompts.
from . import (
    well_init,
    well_sense,
    well_qc,
    well_compose,
    well_route,
    well_critique,
    well_repair,
    well_judge,
    well_seal,
)


PROMPT_MODULES = [
    well_init,  # 000
    well_sense,  # 111
    well_qc,  # 333
    well_compose,  # 444
    well_route,  # 555
    well_critique,  # 666
    well_repair,  # 777
    well_judge,  # 888
    well_seal,  # 999
]


LOOP_MAP = {
    "well_init": "000_INIT",
    "well_sense": "111_SENSE",
    "well_qc": "333_REASON",
    "well_compose": "444_COMPOSE",
    "well_route": "555_ROUTE",
    "well_critique": "666_CRITIQUE",
    "well_repair": "777_REPAIR",
    "well_judge": "888_JUDGE",
    "well_seal": "999_SEAL",
}


def register_prompts(mcp: Any) -> List[str]:
    """Register all well_mcp loop-mapped prompts with FastMCP.

    Returns list of prompt names registered. Best-effort: any module
    that fails to register is logged but does not abort the others.
    """
    registered: List[str] = []
    for module in PROMPT_MODULES:
        try:
            names = module.register(mcp)
            registered.extend(names)
        except Exception as e:
            import sys

            print(f"[well_mcp.prompts] {module.__name__} failed: {e}", file=sys.stderr)
    return registered


__all__ = ["register_prompts", "PROMPT_MODULES", "LOOP_MAP"]
