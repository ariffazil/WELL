"""
repair_allowlist.py — WELL P4 Bounded Repair Allowlist.

Defines which repair actions WELL may recommend, at which autonomy band,
with what reversibility guarantees and verification criteria.

Design (forged 2026-07-21):
  - Phase 1: read-only diagnosis only (A0/A1)
  - Phase 2: allowlisted reversible actions (A2)
  - Phase 3: judgment-gated repair (A3)
  - Phase 4: prohibited actions (A4)

Every action has: symptom, proposed_action, reversibility, blast_radius,
verification_test, rollback, required_authority.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

from typing import Any

# ── Autonomy band map ────────────────────────────────────────────────────────
# A0: observe only
# A1: recommend, dry-run
# A2: allowlisted reversible action (policy approval)
# A3: explicit arifOS judgment + human acknowledgement
# A4: prohibited (F13 only)

# ── Allowlist: symptom → recommended action ──────────────────────────────────

ALLOWLIST: list[dict[str, Any]] = [
    # ── A1: Read-only diagnosis (always safe) ──
    {
        "id": "diag-high-cpu",
        "band": "A1",
        "symptom": "CPU idle < 20% sustained (3+ samples)",
        "probable_cause": "Runaway process or excessive workload",
        "proposed_action": "Identify top CPU consumers via ps/top. Do NOT kill processes.",
        "reversibility": "REVERSIBLE",
        "blast_radius": "LOW",
        "verification_test": "Confirm process list matches expected services",
        "rollback": "N/A — read-only",
        "required_authority": "A1_ADVISORY",
    },
    {
        "id": "diag-high-mem",
        "band": "A1",
        "symptom": "MemAvailable < 10% of total sustained",
        "probable_cause": "Memory leak or excessive cache",
        "proposed_action": "Identify top memory consumers via ps/smem. Do NOT clear caches.",
        "reversibility": "REVERSIBLE",
        "blast_radius": "LOW",
        "verification_test": "Confirm memory usage matches expected patterns",
        "rollback": "N/A — read-only",
        "required_authority": "A1_ADVISORY",
    },
    {
        "id": "diag-disk-full",
        "band": "A1",
        "symptom": "Disk used > 85%",
        "probable_cause": "Log accumulation, large temp files, or data growth",
        "proposed_action": "Identify largest directories via du. Do NOT delete files.",
        "reversibility": "REVERSIBLE",
        "blast_radius": "LOW",
        "verification_test": "Confirm space usage against expected baseline",
        "rollback": "N/A — read-only",
        "required_authority": "A1_ADVISORY",
    },
    {
        "id": "diag-service-down",
        "band": "A1",
        "symptom": "systemd service inactive or failed",
        "probable_cause": "Crash, resource exhaustion, or config error",
        "proposed_action": "Check journalctl for crash logs. Do NOT restart without approval.",
        "reversibility": "REVERSIBLE",
        "blast_radius": "LOW",
        "verification_test": "Confirm crash cause from logs before action",
        "rollback": "N/A — read-only",
        "required_authority": "A1_ADVISORY",
    },
    {
        "id": "diag-docker-unhealthy",
        "band": "A1",
        "symptom": "Docker container health check failing",
        "probable_cause": "Service internal error or resource constraint",
        "proposed_action": "Check docker logs for the unhealthy container. Identify root cause.",
        "reversibility": "REVERSIBLE",
        "blast_radius": "LOW",
        "verification_test": "Confirm logs show actionable error",
        "rollback": "N/A — read-only",
        "required_authority": "A1_ADVISORY",
    },
    # ── A2: Allowlisted reversible repair ──
    {
        "id": "repair-restart-stateless",
        "band": "A2",
        "symptom": "Stateless service degraded but not crashed",
        "probable_cause": "Memory leak, deadlock, or transient error",
        "proposed_action": "systemctl restart <service> for allowlisted stateless services only.",
        "reversibility": "REVERSIBLE",
        "blast_radius": "MEDIUM",
        "verification_test": "service health endpoint returns 200 within 30s of restart",
        "rollback": "systemctl stop <service> — rollback to previous version if restart fails",
        "required_authority": "A2_ALLOWLISTED",
        "allowlisted_services": [
            "prometheus",  # stateless metrics collector
            "node_exporter",  # stateless host metrics
            "well-witness",  # stateless observer
        ],
    },
    {
        "id": "repair-clear-temp",
        "band": "A2",
        "symptom": "Disk pressure from /tmp or /var/tmp",
        "probable_cause": "Temp file accumulation",
        "proposed_action": "Remove files in /tmp older than 7 days. Dry-run first.",
        "reversibility": "IRREVERSIBLE",
        "blast_radius": "LOW",
        "verification_test": "Confirm freed space > 0 and no service errors",
        "rollback": "N/A — deleted temp files cannot be recovered",
        "required_authority": "A2_ALLOWLISTED",
    },
    {
        "id": "repair-docker-restart",
        "band": "A2",
        "symptom": "Docker container unhealthy but not critical",
        "probable_cause": "Service internal error",
        "proposed_action": "docker restart <container> for allowlisted containers only.",
        "reversibility": "REVERSIBLE",
        "blast_radius": "MEDIUM",
        "verification_test": "Container health check returns healthy within 60s",
        "rollback": "docker stop <container> — redeploy previous image if needed",
        "required_authority": "A2_ALLOWLISTED",
        "allowlisted_containers": [
            "qdrant",  # vector DB — restart safe
            "redis",  # cache — restart safe
            "searxng",  # search — restart safe
        ],
    },
    # ── A3: Judgment-gated repair ──
    {
        "id": "repair-restart-webfacing",
        "band": "A3",
        "symptom": "Web-facing service degraded",
        "probable_cause": "Various",
        "proposed_action": "Restart web-facing service. Requires arifOS judgment + human ack.",
        "reversibility": "REVERSIBLE",
        "blast_radius": "HIGH",
        "verification_test": "Public HTTPS endpoint returns 200 within 60s",
        "rollback": "Roll back to last known-good deployment",
        "required_authority": "A3_EXPLICIT_JUDGMENT",
        "allowlisted_services": [
            "caddy",  # reverse proxy — restart requires DNS check
            "arifos",  # kernel — restart requires session preservation
            "a-forge",  # execution — restart requires lease preservation
            "well",  # vitality — restart requires health verification
        ],
    },
    # ── A4: Prohibited ──
    {
        "id": "prohibited-rm-rf",
        "band": "A4",
        "symptom": "N/A",
        "probable_cause": "N/A",
        "proposed_action": "rm -rf, DROP TABLE, docker volume rm — NEVER.",
        "reversibility": "IRREVERSIBLE",
        "blast_radius": "CRITICAL",
        "verification_test": "N/A",
        "rollback": "N/A",
        "required_authority": "A4_PROHIBITED",
    },
    {
        "id": "prohibited-firewall",
        "band": "A4",
        "symptom": "N/A",
        "probable_cause": "N/A",
        "proposed_action": "Firewall changes, iptables, ufw — NEVER without Arif.",
        "reversibility": "IRREVERSIBLE",
        "blast_radius": "CRITICAL",
        "verification_test": "N/A",
        "rollback": "N/A",
        "required_authority": "A4_PROHIBITED",
    },
]


def match_symptoms(symptom_keywords: list[str]) -> list[dict[str, Any]]:
    """Find allowlist entries matching symptom keywords."""
    matches = []
    for entry in ALLOWLIST:
        symptom_lower = entry["symptom"].lower()
        if any(kw.lower() in symptom_lower for kw in symptom_keywords):
            matches.append(entry)
    return matches


def get_allowlisted_services(band: str = "A2") -> list[str]:
    """Get services allowlisted for a given autonomy band."""
    services = []
    for entry in ALLOWLIST:
        if entry["band"] == band and "allowlisted_services" in entry:
            services.extend(entry["allowlisted_services"])
    return list(set(services))


def get_allowlisted_containers(band: str = "A2") -> list[str]:
    """Get containers allowlisted for a given autonomy band."""
    containers = []
    for entry in ALLOWLIST:
        if entry["band"] == band and "allowlisted_containers" in entry:
            containers.extend(entry["allowlisted_containers"])
    return list(set(containers))


def validate_action(
    proposed_action: str,
    requested_band: str = "A2",
) -> dict[str, Any]:
    """Check if a proposed repair action is in the allowlist at the requested band.

    Returns: {allowed: bool, band: str, entry: dict | None, reason: str}
    """
    # Check for prohibited actions
    for entry in ALLOWLIST:
        if (
            entry["band"] == "A4"
            and entry["proposed_action"].lower() in proposed_action.lower()
        ):
            return {
                "allowed": False,
                "band": "A4",
                "entry": entry,
                "reason": f"Action is PROHIBITED: {entry['proposed_action']}",
            }

    # Find best matching entry
    for entry in ALLOWLIST:
        if (
            entry["proposed_action"].lower() in proposed_action.lower()
            or proposed_action.lower() in entry["proposed_action"].lower()
        ):
            band_ok = _band_compare(entry["band"], requested_band) >= 0
            return {
                "allowed": band_ok,
                "band": entry["band"],
                "entry": entry,
                "reason": f"Action requires {entry['band']}, requested {requested_band}"
                if not band_ok
                else "Action is allowlisted",
            }

    # No match found
    return {
        "allowed": False,
        "band": "UNKNOWN",
        "entry": None,
        "reason": f"No allowlist entry found for: {proposed_action}",
    }


def _band_compare(required: str, requested: str) -> int:
    """Compare autonomy bands. Returns 0 if equal, 1 if requested > required, -1 if < required."""
    order = {"A0": 0, "A1": 1, "A2": 2, "A3": 3, "A4": 4}
    req_rank = order.get(required, 99)
    got_rank = order.get(requested, -1)
    if got_rank >= req_rank:
        return 1
    return -1


def get_repair_options(
    symptoms: list[str], max_band: str = "A2"
) -> list[dict[str, Any]]:
    """Get all repair options for given symptoms, up to max_band."""
    matches = match_symptoms(symptoms)
    return [m for m in matches if _band_compare(max_band, m["band"]) >= 0]
