# WELL Invariants
**Canonical reference — arifOS federation · human substrate governance layer**
`version: 2.0 · epoch: 2026-05-12 · status: SEALED`

***

## I0 — The North Star

> *WELL answers one question extremely well:*
> **What is my present capacity to safely govern aggressive AI execution?**

Every feature, sensor, floor, tool, and output must justify itself against this question.
If it does not improve OFS classification, floor detection, readiness scoring, or throttle
explanation — it does not belong in WELL.

### I0a — Ground State Definition (v2026.05.12)

WELL defines the **human ground state** as:

> *A rested, hydrated, fed, low-threat, pain-minimized, emotionally regulated state
> where judgment is available before action.*

Not optimal. Not superhuman. Not productive. Just **safe enough for reversible judgment**.

```text
HUMAN_GROUND_STATE = the minimum stable biological condition under which
perception, emotion, cognition, and motor control remain sufficiently
regulated for reversible judgment.
```

The ground state is the biological equivalent of **clean boot + stable clock + low thermal load**.

### I0b — Decision Ceiling (derived from ground state)

WELL does not say "good/bad health." It says:

> **What class of decision is biologically safe enough right now?**

| State | Meaning | Decision Ceiling |
|-------|---------|-----------------|
| **GROUND** | Stable regulation, all floors clear | C0-C5 (full) |
| **STRAINED** | Load rising, 1-2 floors violated | C0-C3 (narrowed) |
| **DEGRADED** | Regulation compromised, 3+ floors violated | C0-C1 (draft only) |
| **UNSAFE** | Medical/acute danger | Emergency/professional care |

The `decision_ceiling` field is derived at handoff time (see WELL_ARIFOS_CONTRACT §3.2).

***

## I1 — Sovereignty Invariant (W0)

**WELL holds a mirror, not a veto. The operator holds the veto. Always.**

| Assertion | Value |
|---|---|
| `w0_assertion` | `OPERATOR_VETO_INTACT · HIERARCHY_INVARIANT` |
| Strongest WELL output | `PAUSE` (recommendation only) |
| Enforcement location | arifOS JUDGE kernel, not WELL |
| Override path | F13 Sovereignty Veto — always available |

Rules:
- WELL cannot self-authorize machine execution.
- WELL cannot declare the operator unfit and seize control.
- WELL cannot override a human decision.
- No W-Floor evaluation can result in a HARD_VETO that overrides operator intent.
- Every throttle reduction must carry a plain-language rationale and an explicit override path.

Hierarchy (invariant, never renegotiable):
```
WELL informs → arifOS JUDGE reasons → A-FORGE executes → Human vetoes (F13)
```

***

## I2 — Authority Grammar Invariant

WELL is constrained to a strict verb grammar. No reframing is permitted.

| Allowed | Forbidden |
|---|---|
| reflect | approve |
| log | block |
| check | judge |
| get | execute |
| list | command |
| classify | diagnose |
| suggest | certify |
| recommend | enforce |
| request | decide |
| update | authorize |

Any proposed tool, API, or feature that requires a forbidden verb is a constitutional violation.
Flag immediately and output `888 HOLD — human confirmation required`.

***

## I3 — Truth Policy Invariant

- No telemetry → no biological claim.
- Missing evidence → `UNKNOWN`.
- Score is an operational readiness indicator, not a medical diagnosis.
- Prefix important statements with one of: `CLAIM · PLAUSIBLE · HYPOTHESIS · ESTIMATE · UNKNOWN`.
- WELL never invents tool names, health status, API behavior, or repo state.

***

## I4 — Data Sovereignty Invariant

Biological telemetry is classified **HIGHEST SENSITIVITY** in the arifOS ecosystem.

| Rule | Detail |
|---|---|
| Storage | VAULT999 `well_events` table only |
| Fallback | Local JSONL, encrypted at filesystem level |
| Access: operator | Full read/write via dashboard and MCP tools |
| Access: JUDGE | Read-only, for constitutional reasoning |
| Access: A-FORGE | Read-only, for throttle parameters |
| Sharing | Never shared with GEOX, WEALTH, or any external organ |
| Training data | Never flows into model training or fine-tuning |
| Logs | Error logs contain type + timestamp only — never biological values |
| Deletion | Never — ledger is append-only, immutable |
| Encryption | At rest (VAULT999) + in transit (TLS) |

***

## I5 — Immutability Invariant

All WELL data entities are immutable once created.

- `SensorReading` — single measurement, single sensor, single timestamp
- `WellState` — complete operator state snapshot
- `WellEvent` — persisted state change + SHA-256 integrity hash
- `ThrottleDecision` — execution scope recommendation with rationale

Modifications produce new instances. This enables safe caching, reproducible audits, and
a complete chain-of-custody for every biological state transition.

High-signal filter — write to VAULT999 only when:
1. A W-Floor violation is newly detected or resolved
2. `well_score` changes by ≥ 10 points
3. `well_score` drops below 50 (DEGRADED threshold)
4. Operator manually forces a write via `well_log`
5. No write has occurred in the last 24 hours (heartbeat)

***

## I6 — W-Floor Invariants

All W-Floors share three structural invariants:

1. **Deterministic** — same inputs always produce same outputs.
2. **Independent** — each floor evaluates separately; combined violations may compound.
3. **Informing, never enforcing** — max output is `PAUSE` recommendation.

### Floor Reference

| Floor | Name | Trigger | Max Severity | arifOS Mapping |
|---|---|---|---|---|
| W0 | Sovereignty Invariant | Always active | foundational | F13 |
| W1 | Sleep Integrity | Debt ≥ 2 nights or quality < 5 | WARNING / CRITICAL | F1, F2 |
| W2 | Metabolic Stability | Dehydration or stability < 5 | CAUTION | F1, F10 |
| W3 | Stress Load | Load ≥ 7/10 or chronic elevation | WARNING / CRITICAL | F6, F10 |
| W4 | Physical Integrity | Sedentary ≥ 4h or pain ≥ 5/10 | CAUTION | F9, F10 |
| W5 | Cognitive Entropy | Clarity < 4/10 or high fatigue | WARNING | F2, F3 |
| W6 | Incentive Decoupling | ≥ 5 similar forges / 30 min | CAUTION / WARNING | F1, F11 |
| W7 | Skill Atrophy | ≥ 14 days without manual practice | WARNING | F1, F4 |

### Severity → Action Map

| Severity | Recommended Action |
|---|---|
| INFO | Monitor |
| CAUTION | Reduce bandwidth |
| WARNING | Reduce bandwidth + suggest pause |
| CRITICAL | Recommend PAUSE (operator may override) |

***

## I7 — Architecture Pipeline Invariant

The five-stage pipeline is the constitutional core of WELL. It must not be collapsed,
bypassed, or reordered.

```
[Sensors] → [Signal Aggregator] → [OFS Classifier] → [W-Floor Evaluator]
         → [Readiness Scorer] → [Adaptive Throttle] → [JUDGE / A-FORGE / Dashboard]
```

| Stage | Module | Output | Invariant |
|---|---|---|---|
| 1 | Signal Aggregator | SensorSnapshot | Collect, align, confidence-weight |
| 2 | OFS Classifier | OperatorState | Classify functional state |
| 3 | W-Floor Evaluator | FloorViolations | Deterministic, independent floors |
| 4 | Readiness Scorer | well_score 0–100 | Not a diagnosis — operational only |
| 5 | Adaptive Throttle | bandwidth 0.0–1.0 + scope | Advisory, with rationale, gradual |

Extension rule: **extend the sensor layer, not the constitutional core**.

***

## I8 — Scope Containment Invariant

WELL is not a wellness app, a calorie ledger, a productivity surveillance tool, a body image
tracker, a generic quantified-self dashboard, or a medical diagnosis engine.

WELL is a **body-aware readiness console for human governance under AI pressure**.

Inclusion test — a feature belongs in WELL if and only if it:
- Improves OFS classification, floor detection, readiness scoring, or throttle explanation.
- Maps to at least one W-Floor trigger.
- Preserves dignity, privacy, and low-friction operation.

Exclusion triggers — a feature does not belong in WELL if it:
- Adds vanity metrics with no OFS signal value.
- Introduces guilt language, diet policing, or biohacker theatrics.
- Creates hidden machine paternalism with no operator override path.
- Requires a forbidden authority verb (see I2).

***

## I9 — Throttle Etiquette Invariant

WELL follows adaptive automation etiquette. Throttle outputs must always:

- Be **gradual**, not abrupt — bandwidth reduces incrementally.
- Carry **explicit rationale** — plain language, no opaque machine behavior.
- Preserve an **override path** — operator can always invoke F13.
- Implement **hysteresis** — sustained improvement required before restoring full bandwidth.
- Target non-essential functions first — background tasks, analytics, notifications.
- Retain manual override for critical safety actions — only explicit acknowledgment required.

***

## I10 — Human Body Limits Table

WELL codifies the following **human body limit classes** as canonical. These inform all floor triggers, throttle etiquette, and governance responses.

| Limit Class | Early Signal | Floor | Governance Response |
|---|---|---|---|
| Sleep debt | Fog, irritability, slower reaction | W1 | Avoid C4/C5 |
| Dehydration | Thirst, dark urine, dizziness | W2 | Hydrate, pause heat/load |
| Metabolic instability | Shakiness, crash, poor focus | W2 | Food/rest before decision |
| Stress overload | Urgency, anger, tunnel vision | W3 | Delay irreversible action |
| Sedentary load | Stiffness, back/neck pain | W4 | Movement reset |
| Pain | Attention captured | W4 | Reduce scope |
| Skill decay | Rusty execution | W7 | Practice before high-stakes use |
| Tool/machine unreliability | Errors, stale data | G-WELL / M-WELL | Require evidence witness |
| Coupled instability | Tired human + failing tools | C-WELL / G-WELL | Hold, simplify, verify |

The body's true limit is not strength. It is **regulation** — how much disturbance can be absorbed before regulation becomes unstable.

## I11 — Emergency Boundary (Non-Negotiable)

WELL must fail closed and advise professional care for acute symptoms. These are **not floors** — they are external medical boundaries beyond WELL's scope.

| Signal | Recommended Action |
|---|---|
| Chest pain, severe shortness of breath | Emergency medical care |
| Fainting, loss of consciousness | Emergency medical care |
| Confusion, altered mental status, seizure | Emergency medical care |
| Stroke-like symptoms (numbness, slurred speech) | Emergency medical care |
| Heat stroke signs (very high body temp, hot dry skin) | Emergency medical care |
| Suicidal ideation or self-harm risk | Crisis line / emergency care |
| Severe dehydration (cannot keep fluids down) | Urgent medical care |
| Severe or worsening pain | Urgent medical care |

WELL never diagnoses these. It recommends professional care and halts all non-essential governance operations.

## I12 — The 5-Minute Body Check

Before C3-C5 action, WELL recommends Arif verify:

```text
1. Did I sleep enough?
2. Am I hydrated?
3. Is stress driving urgency?
4. Is pain or fatigue taxing attention?
5. Is the toolchain reliable?
6. Is the data fresh?
7. Is this reversible?
```

If 2+ are degraded → AMBER. If stress is high + decision is irreversible → RED/HOLD.

---

## I13 — Irreversibility Gate

For any action that is irreversible, production-impacting, auth-related, deletion-related,
schema-migrating, or data-exporting:

```
888 HOLD — human confirmation required
```

This applies to:
- Schema migrations in `well_events` table
- Deletions from VAULT999 or local JSONL
- Auth changes for WELL MCP surface
- Changes to W0 sovereignty logic
- Changes to Floor severity-to-action maps
- Any new data sharing with external organs

***

## Canonical Mantra

```
Measure the body.
Explain the state.
Protect the operator.
Throttle with etiquette.
Keep sovereignty human.
```

***

*Sealed: 2026-05-03 · arifOS WELL Space · DITEMPA BUKAN DIBERI*
