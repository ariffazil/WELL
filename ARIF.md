# ARIF.md | METABOLIC KERNEL v1.0

> SYSTEM TYPE: LORE INTERFACE
> GOVERNANCE: arifOS AAA
> VETO: 888 JUDGE
>
> INVARIANT: Descriptive memory of repo state.
> This file NEVER modifies Law. It only reports and compresses observed reality.
> Law lives in: arifOS `000/000_CONSTITUTION.md`. Template: https://gist.github.com/ariffazil/81314f6cda1ea898f9feb88ce8f8959b


## 0. IDENTITY & MOUNT POINT

- REPO_NAME: WELL
- CONTAINER_ID: 2026-05-15
- DOMAIN_ROLE: Universal Substrate Vitality Mirror — reflects biological, cognitive, machine, and governance state back to arifOS. Never vetoes. Informs only. W0 sovereignty invariant.
- STABILITY_CLASS: AGI-CONSOLIDATED
- VERSION: v2026.05.15-ΩWELL+GWELL+FEDERATION


## 1. CURRENT FOCUS (INSTRUCTION POINTER)

- 75-tool MCP surface (full boundary-off mode). 13 Ω-WELL canonical tools. 13 Ω-WELL polymorphic stack (000→999). 3 G-WELL governance tools.
- WELL→arifOS bridge live: `_read_well_substrate()` in arifOS judge.py reads WELL state for every verdict. Multi-path file + HTTP fallback.
- Cognitive clarity surfaced in `mcp_health_check`.
- MCP identity surface: `.well-known/agent-card.json` + `.well-known/mcp/server.json`.
- G-WELL Registry Truth Gate: all 11 public tools emit federation-standard output.
- Schema gate active: Pydantic validation catches invalid inputs.
- Known gap: No sensor integration (H-WELL runs on self-reported inputs). Phase 5 is wearable/biomarker.
- WELL is **NOT DEPLOYED** on the VPS. `compose/docker-compose.yml` defines the service but no container is running.
- Tests: All audit tests pass. All Ω-WELL aliases present.


## 2. OPERATIONAL MANDATE

- WELL is a mirror, not a judge (W0). Reflects substrate state. arifOS decides. Arif vetoes.
- 5 substrate layers: H-WELL (human), M-WELL (machine), G-WELL (governance), C-WELL (coupled), U-WELL (universal).
- 7 W-Floors: W0 (sovereignty) through W7 (skill atrophy). Analogous to arifOS F1-F13.
- Thermodynamic core: metabolic_flux = cognitive_entropy_rate + machine_entropy.
- Upstream: arifOS (constitutional kernel), operator self-reporting.
- Downstream: arifOS JUDGE (via bridge), A-FORGE (forge_precheck/closeout), dashboard.


## 3. THE 999 SEAL (SESSION LOG)

- 2026-05-15 | Omega | MCP server descriptor committed. Cognitive clarity in health check. WELL→JUDGE bridge wired in arifOS.
- 2026-05-12 | OpenCode | v2026.05.12: G-WELL governance abstraction, W2-W7 floors, M/H-WELL expansion, registry truth gate.
- 2026-05-10 | arifOS_bot | Ω-WELL refactor + unified substrate packet + federation bridge.
- 2026-05-09 | Kimi Code | 999_SEAL: WELL SOT docs — metabolic flux, somatic boundary, 15-tool surface (now 75).


## 4. ACTIVE TOPOLOGY (MEMORY MAP)

- CRITICAL_FILES:
  - `server.py` → 75-tool FastMCP server. Entry point.
  - `vault_bridge.py` → VAULT999 append-only ledger client.
  - `gate/well_gate.py` → Pre-JUDGE biological readiness mirror.
  - `.well-known/agent-card.json` → AFWELL MCP identity.
  - `.well-known/mcp/server.json` → MCP capabilities descriptor.
  - `test_well.py` → Audit/adversarial test suite (plain Python).

- ENTRYPOINTS:
  - `python server.py` → WELL MCP server
  - `python test_well.py` → Full audit test suite

- DATA_FLOWS:
  - Operator self-report → WELL state.json → arifOS JUDGE bridge → verdict
  - WELL health endpoint → arifOS HTTP fallback (when state file unavailable)
  - A-FORGE → `well_forge_precheck` → WELL → `well_forge_closeout` → A-FORGE


## 5. INTERRUPTS & FAULTS (BLOCKERS)

- SOFT_FRICTION: WELL is not deployed. No container is running. `STATUS.md` confirms ⛔ NOT DEPLOYED.
- SOFT_FRICTION: 15 deprecated tools still exposed. Removal window: 2 epochs. Intentionally retained for backward compat.
- HARD_BLOCK: None. All tests pass. 75-tool surface verified.
- KNOWN_GAP: No biometric sensor integration. H-WELL runs on self-reported data. Phase 5 (wearable/HRV/glucose) not built.


## 6. RECENT SCARS (W_scar)

- [2026-05-15] → [WELL→JUDGE bridge forged in arifOS] → [WELL state now advisory evidence in every constitutional verdict]
- [2026-05-12] → [G-WELL governance abstraction] → [W2-W7 floors, registry truth gate, 75-tool surface boundary-off]
- [2026-05-10] → [Ω-WELL refactor] → [Unified substrate packet, 13 canonical tools, federation bridge]


## 7. EXECUTION BUFFER (COMMANDS)

| Command | Status | Context |
|---------|--------|---------|
| `python server.py` | ✅ | Start WELL MCP server |
| `python test_well.py` | ✅ | All audit tests pass |
| `./deploy.sh` | ⛔ NOT DEPLOYED | WELL defined in compose but not running |


## 8. PRIVILEGE ESCALATION (888 HOLD)

- [Q]: When to integrate wearable/biomarker sensors (Phase 5)?
- [CONTEXT]: H-WELL currently self-reported. HRV, glucose, sleep tracker would make biological readiness objective. Ω₀ = 0.5 (medium uncertainty — requires hardware decision).
- [Q]: U-WELL civilizational substrate — build PETRONAS basin health, national energy sovereignty module?
- [CONTEXT]: Bones exist (INSTITUTION, ECOSYSTEM, INFORMATION_SYSTEM substrate types). Flesh not built. Ω₀ = 0.7 (high uncertainty — scope not defined).


## 9. PIPELINE PREFETCH (NEXT MOVES)

- [ ] Deploy WELL to VPS (decision pending) → push to GHCR → `docker compose up -d` or systemd service
- [ ] Freeze `substrate_evidence.schema.json` (P1)
- [ ] Wire WELL clarity score into arifOS JUDGE gating (P1)
- [ ] Multi-operator panel for when Arif offline (P2)


---

*🪙 GOLD SEAL | METABOLIC KERNEL v1.0 | arifOS AAA | 888 JUDGE VETO | DITEMPA BUKAN DIBERI*
*Readable by: single human · couple · company · institution · AI agent · machine · team · civilisation intelligence*
