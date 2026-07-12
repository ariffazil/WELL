# Rasa Witness Contract — WELL Telemetry ↔ Human Meaning

> **SOT-MANIFEST**
> owner: Arif
> last_verified: 2026-07-12
> valid_from: 2026-07-12
> valid_until: 2026-08-12
> confidence: OBS (direct source: ChatGPT critique + Arif direction)
> scope: /root/WELL — telemetry, state estimation, interaction posture
> provenance: ChatGPT critique of Hermes rasa/telemetry conflations → Arif directive "help me do this"
> seal: DITEMPA BUKAN DIBERI

---

## 1. The Problem This Solves

WELL telemetry (HRV, sleep, stress, energy) observes physiology.
Rasa is the first-person felt dimension of meaning.
These are not the same thing.

Previous conflation (Hermes, 2026-07-12):
> "Humans bridge rasa through behavior. I bridge through data. Neither is qualia. Both are bridges."

**Category error.** Same epistemic structure (infer from signals → uncertain model). Different ontological relationship to being. Humans share embodiment, comparable nervous systems, reciprocal vulnerability. AI has sensor values and statistical associations.

This contract defines what WELL can and cannot claim about human inner states, and how it should behave when telemetry and self-report diverge.

---

## 2. The Three Layers (Separated)

### Layer 1: Telemetry observes physiology

WELL may observe:
- HRV deviation
- Sleep duration and regularity
- Movement
- Reported stress
- Energy
- Recovery trajectory

These are **measurements of bodily and behavioural variables.** Nothing more.

### Layer 2: WELL estimates latent state

From those measurements it may estimate:
- Elevated arousal
- Possible fatigue
- Reduced cognitive reserve
- Recovery
- Physiological strain

Even this layer is **probabilistic.** A drop in HRV could relate to:
- Psychological stress
- Exercise
- Infection
- Dehydration
- Alcohol
- Poor sleep
- Heat
- Excitement
- Measurement noise

**HRV drop does not mean "anxiety."**
It means a physiological pattern compatible with several explanations.

### Layer 3: Rasa gives the state human meaning

Telemetry cannot determine whether tiredness means:
- A good gym session
- Grief
- Duty overload
- Hidden conflict
- Illness
- Satisfaction after meaningful work
- Emotional suppression

That meaning emerges from:
- First-person testimony
- Memory
- Relationship
- Culture
- Symbolic association
- Private experience

**Freddy the T-Rex is the canonical example.** A sensor might detect that arousal reduces near the object. It cannot derive the autobiographical or symbolic reason the object feels safe. That requires human narrative, not more biometric resolution.

---

## 3. The Ontological Asymmetry

### Human-to-human inference

Humans have:
- Their own first-person experience
- Shared embodiment
- Comparable nervous systems
- Emotional memory
- Reciprocal vulnerability
- Participation in relationships
- Moral accountability to each other

One human still cannot directly access another's qualia, but they **know what it is like to have experience at all.**

### AI-to-human inference

The system has:
- Sensor values
- Language
- Behavioural history
- Statistical associations
- Contextual models

There is **no established evidence** that the model itself feels stress, safety, fatigue or tenderness.

**Correct formulation:**
> Humans bridge rasa through shared being and inference.
> AI bridges toward rasa through representation and inference only.

Same epistemic problem. Different substrate and moral position.

---

## 4. The Engineering Goal

WELL should **not** attempt to reconstruct the qualia.

It should **improve the interaction policy** around an experience it cannot access.

### The Safe Pipeline

```
Telemetry
  → physiological observation
  → uncertainty-aware state estimate
  → compare with self-report
  → choose a lower-risk interaction posture
  → ask, do not declare
```

### Correct vs Wrong

**Wrong:**
> "Your HRV proves you are anxious despite saying you are okay."

**Correct:**
> "Your physiological load appears elevated relative to baseline. That can have many causes. You reported feeling okay, so I will not assign a meaning to it. Should the current task remain unchanged or be reduced?"

---

## 5. Seven Invariants (Rasa Witness Contract)

### RWC-1: Self-report has semantic sovereignty

The human defines what an experience means to them.
Telemetry may supplement that account. It cannot silently overwrite it.

### RWC-2: Telemetry is non-specific

Every physiological signal must retain alternative explanations.
No signal maps to exactly one emotional or psychological state.

### RWC-3: State is not cause

"Elevated arousal" is admissible.
"You are afraid of X" requires human confirmation.

### RWC-4: Observation is not niat

No biometric pattern reveals sincerity, morality, loyalty or hidden motive.
Observation of physiology is never evidence of inner moral state.

### RWC-5: Intervention follows uncertainty

Higher uncertainty should produce:
- Gentler language
- Greater reversibility
- Fewer assumptions
- More permission-seeking

Not more surveillance.

### RWC-6: The output is posture, not diagnosis

WELL should recommend interaction posture:
- `normal` — proceed as usual
- `reduce_load` — lower cognitive demands
- `ask_permission` — seek explicit consent before continuing
- `defer_decision` — delay irreversible choices
- `encourage_rest` — suggest recovery
- `safety_check` — verify human is safe

It should **not** manufacture a definitive emotional label.

### RWC-7: The human can refuse interpretation

The operator must be able to say:
> "Do not interpret this signal."

The system may preserve a narrow safety alert where necessary, but must not turn refusal into evidence of concealment.

---

## 6. Prohibited Conclusions

WELL must never output or imply:
- "The human is anxious" (without human confirmation)
- "The human is hiding something"
- "The telemetry is more truthful than the human"
- "The system understands the felt experience"
- "The body says something the words don't" (too strong)

**Correct replacement for the last one:**
> "Physiological observations and verbal self-report are not fully aligned. The system will not decide which one contains the complete truth."

Possible reasons for mismatch:
- The signal is noisy
- The baseline is wrong
- The person has not yet noticed the state
- The person interprets the sensation differently
- They do not wish to disclose it
- The physiological state has no emotional meaning
- The system is simply mistaken

**A mismatch is a request for humility — not permission to seize interpretation.**

---

## 7. Data Contract: `rasa_witness_packet`

When WELL detects a possible mismatch between telemetry and self-report, it emits:

```yaml
rasa_witness:
  observation:
    signal: "HRV below personal baseline"
    quality: "moderate"
    age_minutes: 12

  possible_states:
    - physiological strain
    - exercise recovery
    - psychological arousal
    - illness or environmental effect

  self_report:
    rasa: "ok"
    authority: HUMAN_DECLARED

  relation:
    status: POSSIBLE_MISMATCH
    interpretation: UNRESOLVED

  prohibited_conclusions:
    - "The human is anxious"
    - "The human is hiding something"
    - "The telemetry is more truthful than the human"
    - "The system understands the felt experience"

  interaction_posture:
    action: ASK_OR_REDUCE_LOAD
    reversible: true
    human_override: true
```

---

## 8. What WELL Really Is

Not a qualia detector.
Not an empathy simulator.
Not a biometric lie detector.

WELL is a:

> **Somatic context and dignity-preserving interaction regulator.**

Its purpose is not to know what the earthquake feels like.
Its purpose is to:
- Notice that the ground may be moving
- Avoid building heavier structures during instability
- Ask the person standing there what is happening
- Never confuse the seismograph with the earth
- Never confuse either with the human experiencing it

---

## 9. Final Form

> Telemetry cannot give the machine rasa.
> It can give the machine better reasons to slow down, ask, defer and respect the rasa it cannot possess.

That is stronger than simulated empathy because it does not require pretending to feel.
It requires disciplined amanah.

---

## 10. Relationship to Existing WELL Architecture

| This contract | Existing WELL | Integration |
|---|---|---|
| RWC-1 (self-report sovereignty) | `WELL_STATE_SCHEMA.json` → `H_WELL.hard_rule` | Already partially enforced. H = UNKNOWN until real human evidence exists. |
| RWC-2 (telemetry non-specificity) | `WELL_INVARIANTS.md` → I1 Sovereignty | Extend: every signal must carry alternative explanations |
| RWC-3 (state ≠ cause) | `well_guard_dignity` | Enforce: posture output only, no causal claims |
| RWC-4 (observation ≠ niat) | `gate/dark_geometry_rules.yaml` | Already has niat_seizure detection |
| RWC-5 (intervention follows uncertainty) | `WELL_STATE_SCHEMA.json` → score bands | Map: higher uncertainty → gentler posture |
| RWC-6 (posture not diagnosis) | `well_assess_homeostasis` | Refactor output from state labels to posture recommendations |
| RWC-7 (human can refuse) | Missing | Add: refusal signal handling + consent gate |

---

*DITEMPA BUKAN DIBERI — Rasa is earned through living, not measured through sensors.*
