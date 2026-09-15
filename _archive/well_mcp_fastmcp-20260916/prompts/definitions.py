"""
WELL MCP Prompts — Canonical prompt definitions (12 total: 3 refactored + 9 production).

Domain Law: SUBSTRATE_LAW
Authority: REFLECT_ONLY — mirror, never judge

Sovereign: Muhammad Arif bin Fazil (F13)
Date: 2026-07-25 (updated — merged 9 production prompts)
License: AGPL-3.0

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from datetime import datetime, timezone

# ── Legacy Refactored Prompts (3) ─────────────────────────────────────────


def well_sense() -> str:
    """Vitality observation — 4-dimension cycle."""
    return """HOMEOSTASIS → METABOLISM → GRADIENT → LIVELIHOOD

Assessment: OBSERVED / DEGRADED / UNRELIABLE

Observe the substrate. Do not judge. Reflect only."""


def well_qc() -> str:
    """Substrate verification — 5-stage pipeline."""
    return """CLASSIFY → BOUNDARY → METABOLIC_FLUX → RELIABILITY → TRACE

Assessment: VERIFIED / DEGRADED / CRITICAL

Verify the substrate. Do not prescribe. Signal only."""


def well_interpret() -> str:
    """Readiness synthesis — 5-step ladder."""
    return """VALIDATE → FATIGUE_GUARD → DIGNITY_GUARD → REPAIR_CHECK → SYNTHESIZE

Assessment: READY / DEGRADED / CRITICAL

Synthesize readiness. Do not decide. Yield to arifOS."""


# ── Production Prompts (9) — merged 2026-07-25 ───────────────────────────


def prompt_daily_reflection(date: str | None = None) -> str:
    """Guided morning/evening check-in for operator Arif."""
    date_str = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"""# AFWELL Daily Reflection — {date_str}

## Current Vitals
Check `/health` for live vitals. Key dimensions:
- WELL Score (from state.json)
- Sleep Debt (accumulated hours)
- Cognitive Clarity (0.0-1.0)
- Decision Fatigue (0.0-1.0)
- Active Floor Violations

## Reflection Questions
1. **Sleep**: Did you sleep enough? If debt > 0, what is the recovery plan?
2. **Cognitive Load**: Is your clarity where it needs to be for today's decisions?
3. **Pressure**: What is the primary source of load right now?
4. **Niat**: Is your intent clear for the most important task today?
5. **Boundary**: Do you feel any coercion, or is your sovereignty intact?

> W0: WELL holds a mirror, not a veto. Arif decides."""


def prompt_recovery_protocol(
    severity: str = "moderate",
    domain: str = "general",
) -> str:
    """Structured recovery protocol. severity: mild|moderate|severe. domain: general|sleep|cognitive|stress|metabolic."""
    return f"""# {"⚠️" if severity == "moderate" else "🚨" if severity == "severe" else "ℹ️"} {severity.upper()} Recovery Protocol

## Domain: {domain}

## Actions
1. **Hydrate first** — biological substrate needs water
2. **Step away** — 15 minute screen break minimum
3. **Physical reset** — one small task (tidy, walk, stretch)
4. **Sleep debt check** — if > 2 days, prioritize sleep tonight
5. **Decision freeze** — no irreversible actions during recovery

> WELL does not diagnose. These are operational recovery suggestions.
> W0: WELL holds a mirror, not a veto. Arif decides."""


def prompt_readiness_brief(
    task_type: str = "general",
    urgency: str = "normal",
) -> str:
    """Pre-task readiness briefing. task_type: general|coding|public_writing|financial|legal|irreversible."""
    tiers = {
        "general": "T1",
        "coding": "T1",
        "public_writing": "T2",
        "financial": "T3",
        "legal": "T3",
        "irreversible": "T4",
    }
    tier = tiers.get(task_type, "T1")
    return f"""# AFWELL Readiness Brief

## Task Profile
- Type: {task_type}
- Urgency: {urgency}
- Risk Tier: {tier}

## Pre-Task Checklist
1. **Sleep**: Recent sleep quality and debt level
2. **Clarity**: Cognitive clarity above decision threshold
3. **Fatigue**: Decision fatigue not elevated
4. **Stress**: Stress load within operational band
5. **Dignity**: No coercion signals detected
6. **Sovereignty**: psi_SE within SOVEREIGN band (>0.70)

> For irreversible actions (T4): requries 888_JUDGE constitutional verdict.
> W0: WELL holds a mirror, not a veto. Arif decides."""


def prompt_substrate_classify(subject: str = "") -> str:
    """Universal substrate classification prompt."""
    return f"""# Substrate Classification

Subject: {subject or "[provide subject]"}

## Classification Ladder
1. **H-WELL** — Human biological/cognitive substrate
2. **M-WELL** — Machine computational/operational substrate
3. **G-WELL** — Governance/institutional substrate
4. **C-WELL** — Coupled human-machine system
5. **U-WELL** — Universal substrate (no category error)

Use `well_classify_substrate(mode="classification")` for automated classification.

> U-WELL: classify without category error, authority overreach, or false equivalence."""


def prompt_niat_check(task: str = "") -> str:
    """NIAT (Intent) check for Arif."""
    return f"""# NIAT Check

Task: {task or "[describe the task or intent]"}

## NIAT Dimensions
1. **Niat sahih?** — Is the intent genuine and aligned with your values?
2. **Sovereignty intact?** — Are you acting freely or under coercion?
3. **Reversible?** — Can you undo this if you change your mind?
4. **Dignity preserved?** — Does this protect your dignity and others'?
5. **Energy budget?** — Do you have the metabolic resources for this?

Use `well_validate_vitality(mode="readiness")` for automated vitality check.

> W0: WELL holds a mirror, not a veto. Arif decides."""


def prompt_fatigue_boundary_review(
    fatigue_level: str = "unknown",
    pressure: str = "normal",
    days_without_break: int = 0,
) -> str:
    """Fatigue boundary review for Arif."""
    return f"""# Fatigue Boundary Review

## Current State
- Fatigue Level: {fatigue_level}
- Pressure: {pressure}
- Days Without Break: {days_without_break}

## Boundary Assessment
1. **Fatigue check**: On a 1-10 scale, where is your cognitive energy?
2. **Decision quality**: Are you making decisions you'd trust from a well-rested self?
3. **Compounding**: Is fatigue leading to errors that create more work?
4. **Recovery debt**: Are you borrowing from tomorrow's energy?
5. **Red line**: Have you crossed a boundary you set for yourself?

## Recommendation
- Days without break < 3: Monitor. Schedule recovery window.
- Days without break 3-7: Reduce decision load. Delegate where possible.
- Days without break > 7: PAUSE. Recovery is the only productive action.

> W0: WELL holds a mirror, not a veto. Arif decides."""


def prompt_energy_assessment(subject: str = "arif") -> str:
    """Energy gradient assessment."""
    return f"""# Energy Gradient Assessment — {subject}

## Context
The psyche is an open dissipative structure (Prigogine). It maintains order by
importing energy and exporting entropy. Libido = psychic energy (Jung, not Freud).
Suppression (ΔS < 0 forced) always ruptures somewhere else.

## Assessment Dimensions
1. **Gradient**: Is energy flowing toward growth or away from it?
2. **Metabolism**: Is energy being metabolized or suppressed?
3. **Direction**: Suppression → Management → Redirection → Integration
4. **Leak**: Where is energy being lost? (context switching, decision fatigue, coercion)
5. **Source**: What is generating energy? (purpose, autonomy, rest, connection)

## Action
- Suppression detected → identify what is being avoided
- Management plateau → introduce novelty
- Redirection → trace where energy is being routed

Use `well_assess_metabolism(mode="gradient")` for C-WELL metabolic analysis.

> W0: WELL holds a mirror, not a veto. Arif decides."""


def prompt_shadow_check(subject: str = "arif") -> str:
    """Shadow pattern detection."""
    return f"""# Shadow Check — {subject}

## Context
Jung's Shadow = repressed, denied, unlived psychic material. Thermodynamically:
compressed energy behind a dam. The shadow doesn't disappear when ignored — it
inflates. Shadow integration = the most negentropic act there is.

## Detection Patterns
1. **Projection**: What you criticize in others — is it unrecognized in yourself?
2. **Inflation**: What you're unusually proud of — is it compensating for its opposite?
3. **Repetition**: What keeps happening despite your best efforts?
4. **Avoidance**: What topic or person makes you reflexively change the subject?
5. **Fascination**: What draws obsessive attention? (often shadow in disguise)

## States
- **Integrated**: Shadow material recognized and metabolized
- **Repressed**: Shadow material denied — high entropy pressure
- **Projected**: Shadow material attributed to others — interpersonal friction

Use `well_dark_geometry_mirror()` for automated shadow pattern detection.

> W0: WELL holds a mirror, not a veto. Arif decides."""


def prompt_individuation_readiness(subject: str = "arif") -> str:
    """Individuation readiness assessment."""
    return f"""# Individuation Readiness — {subject}

## Context
Individuation = the Self's drive toward wholeness through integration of opposites.
APEX Theory: intelligence = knowing WHEN/WHERE/WHAT to look. Not computational power.
Combined: individuation is the most cognitively demanding act — it requires holding
paradox without collapsing into either pole.

## Readiness Stages
1. **Pre-Individuation**: Operating from persona. Unquestioned roles and habits.
2. **Crisis**: Persona cracks. Shadow material emerges. Disorientation.
3. **Integration**: Shadow metabolized. Opposites held in tension. New synthesis.
4. **Post-Individuation**: Integrated self operating with expanded capacity.

## Assessment
- Where are you on this ladder right now?
- What paradox are you currently holding?
- What shadow material is pressing for recognition?
- Is your energy budget sufficient for integration work?

Use `well_sabar_latency()` to measure pause capacity before reaction.

> W0: WELL holds a mirror, not a veto. Arif decides."""
