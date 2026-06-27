"""well_mcp.resources — canonical canon resource registry.

Each module exposes register(mcp) returning list of URIs registered.
"""

from __future__ import annotations

from typing import Any, List

# Import all canon resources; import is import-safe (no mcp side-effect).
from . import identity, doctrine, bio_signals, flux
from . import decision_classes, coupling, human_substrate, machine_substrate
from . import chemistry_glue, transport_loop, registry, physics_laws


RESOURCE_MODULES = [
    identity,
    doctrine,
    bio_signals,
    flux,
    decision_classes,
    coupling,
    human_substrate,
    machine_substrate,
    chemistry_glue,
    transport_loop,
    registry,
    physics_laws,
]


def register_resources(mcp: Any) -> List[str]:
    """Register all well_mcp canon resources with FastMCP.

    Returns list of URIs registered. Best-effort: any module that
    fails to register is logged but does not abort the others.
    """
    registered: List[str] = []
    for module in RESOURCE_MODULES:
        try:
            uris = module.register(mcp)
            registered.extend(uris)
        except Exception as e:
            # Log but don't fail the whole canon surface.
            # well://errors/<module> would be a self-reference;
            # log to stderr for operator observability.
            import sys

            print(
                f"[well_mcp.resources] {module.__name__} failed: {e}", file=sys.stderr
            )
    return registered


__all__ = ["register_resources", "RESOURCE_MODULES"]
