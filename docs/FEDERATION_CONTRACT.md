<!-- SOT-MANIFEST
owner: Arif (F13 SOVEREIGN)
last_verified: 2026-07-15
valid_from: 2026-07-15
valid_until: 2026-08-15
confidence: high
scope: /root/WELL/FEDERATION_CONTRACT.md
domain_law: SUBSTRATE_LAW
authority: REFLECT_ONLY
-->

# Federation Contract — WELL (organ local)

> **Canonical federation law:** `/root/arifOS/FEDERATION_CONTRACT.md` (ariffazil/arifos)  
> This file is the **WELL peer-edge map** — thin, live, ΔS ≤ 0. Not a second constitution.

**DITEMPA BUKAN DIBERI**

---

## 1. Identity

| Field | Value |
|-------|--------|
| Organ | WELL |
| Port | `127.0.0.1:18083` · public `https://well.arif-fazil.com` |
| MCP | `https://well.arif-fazil.com/mcp` |
| `domain_law` | `SUBSTRATE_LAW` |
| Authority | **`REFLECT_ONLY`** |
| Live tools | **27** (`tools/list` / health `tool_count`) |
| Membrane | `well_mcp/` + root `server.py` |
| Core | `engines/` · `gate/` · `sensors/` |

---

## 2. Peer edges (imports / exports)

### Imports (read / request only)

| Source | What WELL may take | Interface |
|--------|-------------------|-----------|
| **arifOS** | Session tokens, floor context, judge routing | MCP / handoff envelopes · `bridge_arifos_kernel` |
| **WEALTH** | Livelihood / cashflow **evidence** (never invented by WELL) | `well_handoff_livelihood_to_wealth` → wealth tools (**requires `session_id`**) |
| **GEOX** | Optional field-context readiness framing only | `bridge_geox` resource — no geology authority |
| **A-FORGE** | Deploy/runtime health (machine substrate) | observe only |
| **Human (Arif)** | Biometric / readiness inject | sovereign inject scripts · state.json |

### Exports (emit only)

| Consumer | What WELL emits | Interface |
|----------|-----------------|-----------|
| **arifOS** | Readiness · dignity · Peace · fitness class · INSUFFICIENT_DATA | `well_handoff_dignity_to_arifos` · `well_attest_to_kernel` · vitality envelopes |
| **WEALTH** | Duty load / livelihood **frame** (not capital math) | handoff packet S13 |
| **A-FORGE** | Intensity advisory signals (never veto of F13) | forge_well bridge if used |
| **AAA** | Cockpit display of readiness | health + agent card |

---

## 3. Hard refuses (federation)

WELL **must never**:

- diagnose, prescribe, or claim medical authority  
- emit SEAL / HOLD / VOID / SABAR as constitutional verdict  
- allocate capital or invent NPV/EMV  
- invent earth truth (rock, POS, STOIP)  
- override F13 or self-authorize mutation  
- treat `score≈100` as fresh when `freshness=STALE/EXPIRED` (F2 honesty)

---

## 4. Session / envelope contract

Every federation handoff **should** carry:

```
session_id · actor_id · trace_id · domain_law=SUBSTRATE_LAW
authority=REFLECT_ONLY · execution_authorized=false
human_final_authority=Arif
```

| Edge | Status (2026-07-15) |
|------|---------------------|
| WELL tools (local) | Session optional (observe) |
| WELL → WEALTH handoff | **Gap:** wealth may return `SESSION_REQUIRED` — propagate arifOS `session_id` |
| WELL → arifOS | Prefer bound session from `arif_init` |

---

## 5. Zen structure map (this repo)

```
WELL/
├── server.py                 # production membrane entry
├── well_mcp/                 # tools · resources · prompts · transport
├── engines/ · gate/ · sensors/   # SUBSTRATE core (no SEAL)
├── contracts/ · specs/ · envelopes/
├── adapters/ · federation-manifests/
├── BOUNDARY.md · AGENTS.md · GENESIS/
└── FEDERATION_CONTRACT.md    # this file
```

Full structure seal: `/root/AAA/docs/FEDERATED_DOMAIN_STRUCTURE_ZEN_v2026.07.15.md`

---

## 6. Verification

```bash
curl -s http://127.0.0.1:18083/health | python3 -m json.tool
# expect: domain_law=SUBSTRATE_LAW, authority=REFLECT_ONLY, tool_count=27
# freshness: STALE/EXPIRED ⇒ do not treat score as readiness GREEN
```

*One contract spine (arifOS). One peer map (this file). Mirror only.*
