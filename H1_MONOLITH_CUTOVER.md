# H1 + H6 — WELL Monolith Cutover Plan

> **Production today:** `ExecStart=.../python3 /root/WELL/server.py` (≈713 KB / 18,731 lines)  
> **Modular candidates:** `well_mcp/` (221-line FastMCP entry) · `well_mcp_fastmcp/` (duplicate FastMCP)  
> **Risk:** CRITICAL organ — no blind rewrite.  
> **Authority:** REFLECT_ONLY forever.

## H6 decision (choose one modular surface)

| Path | Role | Decision |
|------|------|----------|
| `/root/WELL/server.py` | Production monolith | **KEEP** until cutover green |
| `well_mcp/` | Modular FastMCP v1 | **CANONICAL modular target** |
| `well_mcp_fastmcp/` | Parallel FastMCP scaffold | **RETIRE after tools parity** — do not dual-run |

## Cutover gates (all required)

1. **Tool parity:** `tools/list` count + names match production surface  
2. **Health:** `curl :18083/health` identical shape  
3. **Smoke:** REFLECT_ONLY probes (no diagnose verbs)  
4. **systemd unit:** point ExecStart to modular entry only after 1–3  
5. **Rollback:** keep `server.py` one release; symlink or unit comment  

## H1 entropy path (phased)

| Phase | Action | Risk |
|-------|--------|------|
| 0 | This plan + dual-MCP decision | None |
| 1 | Extract pure helpers from monolith without behavior change | Low |
| 2 | Route systemd to `well_mcp/server.py` behind feature flag | Medium |
| 3 | Quarantine monolith to `server.monolith.py.bak` after 7d green | Medium |
| 4 | Delete bak only after F13 if irreversible | T3 |

## Forbidden

- Running two WELL MCP servers on same port  
- Adding third scaffold  
- Claiming modular is live without systemd proof  

**Status:** PLAN SEALED — execution of Phase 1+ is a separate ticket.

DITEMPA BUKAN DIBERI
