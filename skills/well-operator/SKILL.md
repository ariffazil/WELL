---
name: well-operator
description: ONE canonical door for the WELL organ (human + machine substrate mirror, port 18083). Read this instead of any scattered WELL skill copy. Covers the 10 live MCP tools, what their outputs actually mean, machine stewardship rules, and the known defects log. Validated against the LIVE WELL MCP, not against docs.
status: canonical
owner: WELL organ (MCP :18083)
version: validated 2026-11-15 (WELL v2026-11-15, commit 0c85730); tool surface = the same 10 tools as v2026-11-12
---

# WELL operator — the one door

WELL is a **mirror**: it reflects human readiness and machine substrate state.
It is `REFLECT_ONLY`. It never authorises, never executes, never diagnoses a person.
For any downstream logic use **`signal`**, never `verdict` (verdict is legacy/compat).

## The 10 live tools (exactly these — anything else in an old skill is stale)

| When you need | Call | Notes |
|---|---|---|
| Is the machine healthy right now? | `well_machine_diagnose` | Primary machine read. Issues + recommendations + severity. |
| What should I do about an issue? | `well_machine_recommend` | Commands with risk + `requires_approval` + `binding_constraint`. ADVISORY. |
| Is this tool/agent/service reliable? | `well_assess_reliability` | Machine/tool/institution reliability (M-lane). |
| What substrate am I looking at? | `well_classify_substrate` | Substrate classification + boundary sensing. |
| Is the human ready for this task? | `well_validate_vitality` | Readiness/NIAT. After 168h of no sovereign data → DO_NOT_INFER (correct). |
| Is the body/regulation stable? | `well_assess_homeostasis` | Regulation, stability, empathic balance. |
| Does this touch dignity/boundaries? | `well_guard_dignity` | Symbolic/personhood boundary check before human-facing output. |
| Is repair safe / what's allowlisted? | `well_check_repair` | Repair precheck/postcheck. **A HOLD from it means "unverified", not "broken".** |
| Where does this claim/packet come from? | `well_trace_lineage` | Lineage/provenance of a decision packet. |
| Is the WELL surface itself honest? | `well_registry_status` | `mode=status` or `mode=full`. `REGISTRY_PASS` = declared=live. |

Not in this list = do not call (deregistered 2026-10-16; consent/triadic phase tools are internal-only and NOT on the public surface — see KNOWN_BUGS M-WELL-008).

## Routing in one breath

- Machine question → `diagnose` first, `recommend` second. Never `reliability` to answer "VPS ok?" (it over-alarms, see MACHINE.md).
- Human question → `validate_vitality`; if `INSUFFICIENT_DATA`, say UNKNOWN — never invent vitals.
- Surface truth question → `registry_status mode=full`.
- Any destructive recommendation → `requires_approval` honoured + 888_HOLD. WELL never authorises.

## Authority

WELL proposes. arifOS judges. A-FORGE executes. Arif decides.
Outputs are advisory; the boundary notice on every payload is binding.

See: `TOOLS.md` (field meanings), `MACHINE.md` (stewardship rules), `KNOWN_BUGS.md` (defects, dated).