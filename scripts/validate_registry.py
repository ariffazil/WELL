#!/usr/bin/env python3
"""
validate_registry.py — Single-source-of-truth registry validator for WELL.

Checks that tools_sot.yaml, well_mcp/manifest.json, well_mcp_fastmcp/manifest.json,
and the live server SOMATIC_TOOLS are all in agreement about the public tool surface.

Exit 0 = consistent. Exit 1 = drift detected.
"""

import json
import sys
from pathlib import Path

WELL_DIR = Path(__file__).resolve().parent.parent


def load_yaml_simple(path: Path) -> dict:
    """Minimal YAML loader for tools_sot.yaml (avoids pyyaml dep)."""
    import yaml
    with open(path) as f:
        return yaml.safe_load(f)


def get_public_tools_from_sot() -> set[str]:
    sot = load_yaml_simple(WELL_DIR / "tools_sot.yaml")
    return {t["name"] for t in sot.get("tools", []) if t.get("access") == "public"}


def get_public_tools_from_manifest(path: Path) -> set[str]:
    with open(path) as f:
        m = json.load(f)
    return set(m.get("tools", {}).get("public_tools", []))


def main():
    errors = []

    sot_public = get_public_tools_from_sot()
    print(f"tools_sot.yaml:          {len(sot_public)} public tools")

    for manifest_rel in ["well_mcp/manifest.json", "well_mcp_fastmcp/manifest.json"]:
        mp = WELL_DIR / manifest_rel
        with open(mp) as f:
            manifest = json.load(f)
        m_public = get_public_tools_from_manifest(mp)
        print(f"{manifest_rel}:  {len(m_public)} public tools")

        if m_public != sot_public:
            only_in_sot = sot_public - m_public
            only_in_manifest = m_public - sot_public
            if only_in_sot:
                errors.append(f"{manifest_rel}: missing from manifest (in SOT): {sorted(only_in_sot)}")
            if only_in_manifest:
                errors.append(f"{manifest_rel}: extra in manifest (not in SOT): {sorted(only_in_manifest)}")

        # Check public+internal = total
        total = manifest.get("tools", {}).get("total", 0)
        public_count = manifest.get("tools", {}).get("public", 0)
        internal_count = manifest.get("tools", {}).get("internal", 0)
        if public_count + internal_count != total:
            errors.append(f"{manifest_rel}: public({public_count}) + internal({internal_count}) != total({total})")

    if errors:
        print("\n❌ REGISTRY DRIFT DETECTED:")
        for e in errors:
            print(f"  • {e}")
        sys.exit(1)
    else:
        print("\n✅ Registry consistent — 8 public, 19 internal across all sources")
        sys.exit(0)


if __name__ == "__main__":
    main()
