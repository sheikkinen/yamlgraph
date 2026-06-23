# Plan: v4 Layered Planner

**Status:** Target design.
**Created:** 2026-06-23
**Predecessor:** [`plan-v3-planner.md`](plan-v3-planner.md) (the grammar + forward-carry
plan), [`plan-generative-plot-model.md`](plan-generative-plot-model.md) (the spine
decision).
**Evidence base:** [`paper-test-10030-bc-synopsis-to-plan.md`](paper-test-10030-bc-synopsis-to-plan.md)
(PT1 — DM schema, vocabulary insufficiency), [`paper-test-10030-bc-spine-encoding.md`](paper-test-10030-bc-spine-encoding.md)
(PT2 — spine encoding, gloss as pivot).

---

## 0. The reframe this plan introduces

v3 said: *author the plot as a closed formal specification before prose; prove it
consistent; demote the LLM to a constrained realizer.*

The paper tests revealed a gap in "author the plot." The synopsis IS prose. The
conversion from synopsis to plan IS recognition — the exact problem v3 was
supposed to escape. We have not eliminated the recognition problem; we have
**moved it to the authoring boundary**: one-shot, on a short text, with a
validation gate.

The move is still a win. But the current architecture attempts the conversion in
a single LLM call (synopsis → full plan JSON). The paper test showed this is
fragile: the LLM produces well-structured plans but breaks at schema boundaries
(typed beliefs rejected, JSON fences, silent total-plan-drop). A single failure
at any point loses everything.

**v4 replaces the one-shot conversion with a layered pipeline.** Each layer
extracts one facet of the plan, is independently validated, and can retry without
losing prior layers. The gloss — the one-sentence natural-language beat
description — is the **pivot** between the synopsis (unstructured prose) and the
formal plan (controlled vocabulary).

**Design constraint: small language model.** The pipeline targets a small, fast
model (Haiku-class or equivalent). Each layer's prompt must be simple and focused
— one task, one output schema, minimal context. A small model cannot hold the
full synopsis + full vocabulary + all prior layer outputs in a single call and
reason about all of them simultaneously. The layered design is not a refinement
of the one-shot approach; it is **required** by the model's capacity.

**Implementation: YAMLGraph example.** The pipeline is implemented as a YAML
graph using the framework's own primitives: LLM nodes for each layer, Python tool
nodes for validation gates, conditional edges for retry routing. This serves as a
showcase of YAMLGraph's capabilities for multi-step LLM pipelines with
deterministic validation interludes.

---

## 1. The recognition admission

v2 reconstructed plot state from generated prose (per-chapter, unvalidated,
repeated). v3 moved this to the authoring boundary (one-shot, validated, pre-
prose). v4 names it honestly:

| | v2 | v3 (one-shot) | v4 (layered) |
|---|---|---|---|
| **What** | Recognize plot from generated prose | Recognize plan from synopsis | Recognize plan from synopsis |
| **When** | Per chapter, post-generation | Once, pre-generation | Once, pre-generation |
| **Input** | Full chapter prose (~2000 words) | Full synopsis (~500 words) | Synopsis, decomposed into layers |
| **Validation** | None (accepted on faith) | SAT check on complete plan | Per-layer validation gates |
| **Failure mode** | Silent corruption propagates | Total-plan-drop on any error | Layer-local retry; prior layers preserved |
| **Repair** | None | Full plan regeneration | Layer-specific retry |

The v4 pipeline does not pretend the conversion is "generation." It is
**structured recognition** — reading prose through a controlled vocabulary lens,
with gates at each step.

---

## 2. The seven layers

The conversion flows through seven layers. Each layer takes the synopsis plus
the outputs of prior layers, produces a typed artifact, and passes a validation
gate before the next layer begins.

```
Synopsis
  │
  ▼
Layer 1: Agents + World-State ──→ validate(grounding)
  │
  ▼
Layer 2: Goals ──→ validate(well-typed, refers to known agents)
  │
  ▼
Layer 3: Glosses ──→ validate(count, coverage, no gaps)
  │                          ◄── THE PIVOT
  ▼
Layer 4: Kinds ──→ validate(vocabulary membership)
  │
  ▼
Layer 5: Pre/Eff ──→ validate(Rules 1, 2, 3)
  │
  ▼
Layer 6: Enables + Motivation ──→ validate(Rules 7, 8)
  │
  ▼
Layer 7: Beliefs + Affects ──→ validate(Rules 4, 5)
  │
  ▼
Complete Plan ──→ full SAT check (all 8 rules)
```

### Layer 1: Agents + Initial World-State

**Input:** Synopsis.
**Output:** `agents: list[CharacterId]`, `initial_world: list[Fluent]`.
**Task:** Extract who exists, what relationships hold, what predicates are true at
the start. This is ground-truth extraction — the easiest layer.

**Prompt frame:** "Read the synopsis. List every named character and named group.
For each, state what is true about them at the start of the story using these
predicates: alive, at, holds, faction, rel."

**Validation gate:**
- Every `Fluent.args` entry refers to a named agent (Rule 1 partial).
- Every predicate is in the `WorldPred` alphabet.
- No duplicate agents.

**Failure mode:** LLM invents characters not in the synopsis, or uses predicates
outside the vocabulary. Retry with the specific error.

**Why this layer is first:** Everything downstream depends on the agent list and
initial state. Getting this wrong poisons all later layers. It is also the layer
the LLM is most reliable at — entity extraction from prose is a solved problem.

### Layer 2: Goals

**Input:** Synopsis + Layer 1 output.
**Output:** `goals: list[Fluent]`.
**Task:** Extract what must be true at the finale. Read the synopsis's ending and
express it as predicates over known agents.

**Prompt frame:** "Read how the story ends. What must be true at the finale? Use
only the agents from Layer 1 and the predicates: alive, at, holds, faction, rel.
Express each goal as a predicate with a value."

**Validation gate:**
- Every goal predicate is well-typed.
- Every goal refers to agents in Layer 1.
- No goal contradicts initial state unless a function will change it (deferred to
  Layer 5).

**Failure mode:** LLM states goals about characters not in the agent list, or uses
natural-language goals ("Hilde finds peace") instead of predicate goals
(`holds(Aschenwulf, feud) = false`). Retry with vocabulary constraint.

### Layer 3: Glosses (THE PIVOT)

**Input:** Synopsis + Layer 1 output + Layer 2 output.
**Output:** `glosses: list[{chapter: int, gloss: str}]` — ordered list of one-
sentence beat descriptions.
**Task:** Decompose the synopsis into structural turning points. Each gloss is one
sentence describing one beat — one thing that happens that changes the state of
the story.

**Prompt frame:** "Read the synopsis. Break it into the smallest set of turning
points — moments where something changes (a relationship shifts, a character
learns something, someone acts, someone is harmed, someone arrives or departs).
Write each as one sentence. Assign each to a chapter number. Use only characters
from the agent list."

**Validation gate:**
- Every gloss mentions at least one agent from Layer 1.
- Glosses cover the synopsis's major events (coverage check — compare gloss set
  against synopsis paragraphs; flag gaps).
- No gloss is vacuous ("things happen") — must contain a subject and an action.
- Chapter numbers are monotonically non-decreasing.

**Failure mode:** LLM produces too many glosses (micro-events) or too few (skips
arcs). Too many → "merge glosses that describe the same state change." Too few →
"the synopsis describes [X] but no gloss covers it."

**Why this is the pivot:** Layers 1–3 are **synopsis → prose** (decomposition into
shorter prose). Layers 4–7 are **prose → formal** (classification of each gloss
into the controlled vocabulary). The gloss is the intermediate representation —
short enough for accurate classification, specific enough to preserve narrative
meaning. The paper test (PT2) proved the gloss is load-bearing: it carries the
story that the structural fields cannot.

### Layer 4: Kinds

**Input:** Glosses (Layer 3) + vocabulary (16 function kinds).
**Output:** `functions: list[{id, kind, gloss, subject, chapter}]` — each gloss
classified into a function kind with a subject identified.
**Task:** For each one-sentence gloss, classify it into the closed action alphabet.

**Prompt frame:** "For each gloss, choose the function kind that best describes
it from this list: villainy, lack, departure, donor_test, provision, struggle,
victory, liquidation, return, pursuit, rescue, recognition, exposure, punishment,
reconciliation, death. Also identify the subject (who performs the action)."

**Validation gate:**
- Every kind is in `FunctionKind`.
- Every subject is in the agent list (Layer 1).
- No gloss is unclassified.

**Failure mode:** LLM chooses a kind not in the vocabulary, or assigns a kind that
doesn't match the gloss semantics. The latter is not mechanically checkable (this
is where the recognition problem lives — the vocabulary is a lens, and the LLM
may look through it differently than a human would). The SAT check at the end
catches structural consequences of misclassification.

**This is the hardest layer.** The LLM must map free-form events onto a closed
alphabet. The 16-kind vocabulary (§1a of plan-v3-planner) is designed to cover
the major genres, but edge cases will always exist. When a gloss doesn't fit any
kind well, the LLM must choose the closest match and trust the gloss to carry the
specifics. This is the designed-in lossy step — the vocabulary encodes the *type*
of event, the gloss encodes the *specific* event.

### Layer 5: Pre/Eff (Preconditions and Effects)

**Input:** Functions (Layer 4) + initial state (Layer 1) + goals (Layer 2).
**Output:** Each function gains `pre_world`, `eff_world`, `observers`, `roles`.
**Task:** For each classified function, determine what must be true before it can
happen (preconditions) and what it makes true (effects).

**Prompt frame:** "For each function, determine: (1) What must be true in the
world before this can happen? (2) What does this change in the world? Use only the
predicates and agents from earlier layers. Also list who observes this event and
assign Propp roles (villain, hero, helper, donor, victim)."

**Validation gate:**
- Rule 1 (grounding): every term in every predicate refers to a known entity.
- Rule 2 (causal closure): every precondition is either in the initial state or
  produced by an earlier function's effects.
- Rule 3 (monotonic lifecycle): no function resurrects a dead character in
  world-truth.

**Failure mode:** Dangling preconditions (a function requires a state that nothing
establishes). The validator identifies the specific precondition and the function.
Retry: "Function F3 requires rel(Hilde, Gunnar) = allies, but no prior function
or initial state establishes this. Which function should produce it, or should the
precondition be removed?"

### Layer 6: Enables + Motivation

**Input:** Functions with pre/eff (Layer 5) + glosses.
**Output:** Each function gains `enables`, `motivation`, `threatens`.
**Task:** Determine causal links (which function's effects satisfy which other's
preconditions) and intentionality (why each agent acts).

**Prompt frame:** "For each function: (1) Which later functions does it enable?
A function enables another if its effects establish that function's preconditions.
(2) What is the acting agent's goal? (3) Whose goal does this threaten?"

**Validation gate:**
- Rule 7 (acyclicity): the `enables` graph is a DAG.
- Rule 8 (motivated action): every function with an intentional subject has a
  non-null motivation.
- `enables` edges are consistent with pre/eff (if Fa enables Fb, then Fa.eff ∩
  Fb.pre is non-empty, OR the causal link is narrative rather than formal — in
  which case the gloss must explain the connection).

**Failure mode:** Cycles in enables graph (validator detects and names the cycle).
Unmotivated actions (validator names the function and subject). Both are
straightforward retries.

**Partially mechanical:** The enables graph can be *seeded* by computing which
function's eff_world/eff_belief satisfies which other's pre_world/pre_belief.
The LLM then adds narrative causal links that the formal preconditions don't
capture (e.g., F1 enables F3 because the raid causes the stranding — no formal
precondition says this, but the gloss does).

### Layer 7: Beliefs + Affects

**Input:** Functions with pre/eff/enables (Layers 5–6) + initial belief (Layer 1).
**Output:** Each function gains `pre_belief`, `eff_belief`, `eff_affect`.
Also: `initial_belief: list[Belief]`, `intentional_open: list[AffectDelta]`.
**Task:** Determine who knows what at each point, when beliefs change, and which
emotional threads open and close.

**Prompt frame:** "For each function: (1) What must observers believe before this
can happen? (2) What beliefs change as a result? (3) What emotional thread opens
or closes? Use the belief format: observer believes predicate = value. Use affect
kinds: loss, guilt, betrayal, retaliation, hidden_blessing."

**Validation gate:**
- Rule 4 (grounded reveal): every belief-flip from false to true has a prior
  concealment.
- Rule 5 (affect closure): every opened affect thread has a later close, unless
  in `intentional_open`.
- Typed beliefs accepted: `held: bool | str` (the PT1 fix).

**Failure mode:** Ungrounded reveals (a function reveals something no one was wrong
about). Unclosed affect threads (an emotion opens but never resolves). Both are
specific, retryable errors.

**Why beliefs and affects are last:** They depend on the causal structure (Layer
6) to determine ordering, and on the pre/eff (Layer 5) to determine what's true.
Beliefs are also the hardest layer — they require the LLM to reason about who
knows what, which is a theory-of-mind task. Isolating it to the final layer means
all structural scaffolding is in place before the LLM attempts epistemic
reasoning.

---

## 3. The gloss as intermediate representation

The gloss is not an annotation on the plan — it is the **intermediate
representation** between synopsis and formal structure. The conversion flows
*through* the gloss, not around it.

```
Synopsis (unstructured prose, ~500 words)
    │
    │  Layer 3: decompose
    ▼
Glosses (structured prose, ~7 sentences)
    │
    │  Layers 4–7: classify + formalize
    ▼
Plan (controlled vocabulary, ~200 predicates)
```

This has three consequences:

**C1: The gloss must be preserved in the plan.** It is not a build artifact to be
discarded after classification. It is the beat-writer's primary input — the
one-sentence description of what happens in this beat. Without it, the beat-writer
has only "villainy by Hilde" and no idea what the villainy IS (PT1 §10).

**C2: The gloss is the only field the validator cannot strongly check.** The
structural fields are closed-vocabulary and mechanically verifiable. The gloss is
open-vocabulary and only weakly verifiable (entity mentions checkable, semantics
not). This is the designed-in recognition residue — the one place where the
plan's prose layer escapes formal verification.

**C3: Gloss-structure consistency is a weak invariant, not a strong one.** A
validator can check that the gloss mentions the function's subject and that the
kind is compatible with the gloss's verb ("raids" ≈ villainy, "returns" ≈ return).
It cannot check that "dawn raid on the Bärenschädel camp" is faithful to the
synopsis. Strong consistency would require the validator to understand the
synopsis — which is the full recognition problem.

---

## 4. Layer retry semantics

Each layer has independent retry. A retry re-prompts the LLM with:
- The synopsis (always available)
- All prior layer outputs (frozen — never re-generated on a downstream retry)
- The specific validation error from the failed gate
- The failed layer's previous output (for context)

```
Layer N fails validation
  │
  ├── retry count < limit?
  │     YES → re-prompt Layer N with error context
  │     NO  → escalate: report which rule failed, offer manual override
  │
  └── prior layers (1..N-1) are NEVER re-generated
```

**Why this matters:** The one-shot approach (v3) regenerates everything on failure.
The layered approach preserves correct work. If Layer 5 (pre/eff) fails Rule 2
(dangling precondition), only Layer 5 retries — Layers 1–4 (agents, goals,
glosses, kinds) are preserved. The retry prompt includes the specific error: "F3
requires rel(Hilde, Gunnar) = allies but nothing establishes this."

**Layer retry limits:** Each layer gets 3 retries (configurable). If a layer
exhausts retries, the pipeline halts with a diagnostic:

```json
{
  "status": "failed",
  "failed_layer": 5,
  "failed_rule": "causal_closure",
  "detail": "F3.pre_world: rel(Hilde, Gunnar) = allies has no producer",
  "completed_layers": [1, 2, 3, 4],
  "partial_plan": { ... }
}
```

The partial plan is usable for debugging. A human can inspect the glosses, kinds,
and pre/eff, identify the issue, and either fix it manually or adjust the synopsis.

---

## 5. What v4 inherits from v3

v4 replaces the **authoring pipeline** (how the plan is produced). It does NOT
replace the plan's **formal language** or **downstream use**. Everything from
plan-v3-planner.md that is not about one-shot authoring carries forward:

| v3 artifact | v4 status |
|-------------|-----------|
| Formal language (§1 — vocabulary, syntax, grammar) | **Inherited.** The 16-kind alphabet, 5 predicates, 5 affect kinds, 8 rules. |
| Plan tuple `⟨I, A, G, F, O⟩` | **Inherited.** Layers 1–7 produce the same tuple. |
| Validation (§5 of plan-generative-plot-model) | **Inherited + layered.** Per-layer gates during authoring; full SAT check on completion. |
| Phase 0: Schema fixes (FR-564) | **Inherited.** Typed beliefs, gloss, motivation, enables, Rule 8. These are prerequisites for v4 layers. |
| Phase 1: Complete grammar (FR-566) | **Inherited.** 16 kinds, 5 affects, Rules 1 + 6. Layer gates use these rules. |
| Phase 2: Projected state (FR-567) | **Inherited.** Layer 5 validation uses projected state for Rule 2 checking. |
| Phase 3: Plan-derived outline (FR-568) | **Inherited.** The outline derives from the completed plan, same as v3. |
| Phase 4: Forward-carry (FR-569) | **Inherited.** The plan owns lifecycle/belief/affect at chapter close. |
| The acceptance litmus | **Inherited.** Two chapters generable without reading each other's prose. |

**What v4 adds:**
- The 7-layer authoring pipeline (§2)
- Per-layer validation and retry (§4)
- The gloss as a first-class intermediate representation (§3)
- Honest naming: the conversion is structured recognition, not generation (§1)

---

## 6. YAMLGraph implementation

The pipeline is a YAML graph — a YAMLGraph example showcasing multi-step LLM
orchestration with deterministic validation interludes. Each layer is an LLM node
with a focused prompt. Each validation gate is a Python tool node. Retry is
handled by the framework's conditional edge + loop mechanism.

### 6a. Why 7 calls, not 2 or 1

A small model (Haiku-class) cannot hold the full synopsis + full vocabulary + all
prior outputs and reason about all of them simultaneously. The one-shot approach
(v3) asks the model to extract agents, classify events, assign preconditions,
determine beliefs, and track affects — all in one call. The paper test showed this
is fragile even for a large model (PT1 §8b–§8c). For a small model, it is
unworkable.

The 7-layer split gives each call a **single focused task**:

| Layer | Task complexity | Context needed | Small-model feasible? |
|-------|----------------|---------------|----------------------|
| L1: Agents + world | Entity extraction | Synopsis only | Yes — solved problem |
| L2: Goals | End-state extraction | Synopsis + agent list | Yes — short context |
| L3: Glosses | Beat decomposition | Synopsis + agent list | Yes — prose-to-prose |
| L4: Kinds | Classification (16 categories) | Glosses + vocabulary list | Yes — each gloss is one sentence |
| L5: Pre/eff | Predicate assignment | Functions + initial state + vocabulary | Moderate — needs world-state reasoning |
| L6: Enables + motivation | Causal + intentional reasoning | Functions + glosses | Moderate — needs causal reasoning |
| L7: Beliefs + affects | Theory-of-mind + emotion tracking | Functions + initial belief + affect vocabulary | Hardest — but scaffolded by L1–L6 |

Each prompt is short (~200–400 tokens of instruction + the layer's specific
input). The model never sees the full plan in construction — only the slice it
needs for its task.

### 6b. Graph topology

```
START
  │
  ▼
extract_agents (LLM)
  │
  ▼
validate_agents (Python) ──condition: errors──→ repair_agents (LLM) ──→ validate_agents
  │
  │ condition: ok
  ▼
extract_goals (LLM)
  │
  ▼
validate_goals (Python) ──condition: errors──→ repair_goals (LLM) ──→ validate_goals
  │
  │ condition: ok
  ▼
extract_glosses (LLM)
  │
  ▼
validate_glosses (Python) ──condition: errors──→ repair_glosses (LLM) ──→ validate_glosses
  │
  │ condition: ok
  ▼
classify_kinds (LLM)
  │
  ▼
validate_kinds (Python) ──condition: errors──→ repair_kinds (LLM) ──→ validate_kinds
  │
  │ condition: ok
  ▼
assign_pre_eff (LLM)
  │
  ▼
validate_pre_eff (Python) ──condition: errors──→ repair_pre_eff (LLM) ──→ validate_pre_eff
  │
  │ condition: ok
  ▼
assign_enables (LLM)
  │
  ▼
validate_enables (Python) ──condition: errors──→ repair_enables (LLM) ──→ validate_enables
  │
  │ condition: ok
  ▼
assign_beliefs_affects (LLM)
  │
  ▼
validate_beliefs_affects (Python) ──condition: errors──→ repair_beliefs_affects (LLM) ──→ validate_beliefs_affects
  │
  │ condition: ok
  ▼
validate_plan (Python)  ← full SAT check, all 8 rules
  │
  ▼
END
```

**14 LLM nodes** (7 extract/classify/assign + 7 repair) and **8 Python nodes**
(7 layer gates + 1 final SAT check). Each repair node receives the validation
errors and the previous attempt; it re-prompts with the specific failure. The
loop limit on each repair edge is 3 (configurable via `loop_limit`).

### 6c. YAML graph sketch

```yaml
metadata:
  name: plot_plan_v4
  description: >
    Layered plot-plan authoring pipeline. Converts a synopsis into a
    validated formal plan through 7 extraction layers with per-layer
    validation gates. Designed for small language models.
  provider: anthropic
  model: claude-haiku-4-5

state:
  premise:
    type: str
    description: The input synopsis
  agents:
    type: list
    description: Extracted agent list
  initial_world:
    type: list
    description: Initial world-state fluents
  initial_belief:
    type: list
    description: Initial belief state
  goals:
    type: list
    description: Goal predicates
  glosses:
    type: list
    description: One-sentence beat descriptions
  functions:
    type: list
    description: Classified functions with pre/eff/enables/beliefs/affects
  validation:
    type: dict
    description: Current validation result
  errors:
    type: list
    description: Pipeline errors

nodes:
  # --- Layer 1: Agents + World-State ---
  extract_agents:
    type: llm
    prompt: prompts/plot/extract_agents.yaml
    state_key: agents
    parse_json: true

  validate_agents:
    type: python
    tool: plot_validate_agents

  repair_agents:
    type: llm
    prompt: prompts/plot/repair_agents.yaml
    state_key: agents
    parse_json: true
    loop_limit: 3
    loop_exit: END

  # --- Layer 2: Goals ---
  extract_goals:
    type: llm
    prompt: prompts/plot/extract_goals.yaml
    state_key: goals
    parse_json: true

  validate_goals:
    type: python
    tool: plot_validate_goals

  repair_goals:
    type: llm
    prompt: prompts/plot/repair_goals.yaml
    state_key: goals
    parse_json: true
    loop_limit: 3
    loop_exit: END

  # --- Layer 3: Glosses (the pivot) ---
  extract_glosses:
    type: llm
    prompt: prompts/plot/extract_glosses.yaml
    state_key: glosses
    parse_json: true

  validate_glosses:
    type: python
    tool: plot_validate_glosses

  repair_glosses:
    type: llm
    prompt: prompts/plot/repair_glosses.yaml
    state_key: glosses
    parse_json: true
    loop_limit: 3
    loop_exit: END

  # --- Layer 4: Kinds ---
  classify_kinds:
    type: llm
    prompt: prompts/plot/classify_kinds.yaml
    state_key: functions
    parse_json: true

  validate_kinds:
    type: python
    tool: plot_validate_kinds

  repair_kinds:
    type: llm
    prompt: prompts/plot/repair_kinds.yaml
    state_key: functions
    parse_json: true
    loop_limit: 3
    loop_exit: END

  # --- Layer 5: Pre/Eff ---
  assign_pre_eff:
    type: llm
    prompt: prompts/plot/assign_pre_eff.yaml
    state_key: functions
    parse_json: true

  validate_pre_eff:
    type: python
    tool: plot_validate_pre_eff

  repair_pre_eff:
    type: llm
    prompt: prompts/plot/repair_pre_eff.yaml
    state_key: functions
    parse_json: true
    loop_limit: 3
    loop_exit: END

  # --- Layer 6: Enables + Motivation ---
  assign_enables:
    type: llm
    prompt: prompts/plot/assign_enables.yaml
    state_key: functions
    parse_json: true

  validate_enables:
    type: python
    tool: plot_validate_enables

  repair_enables:
    type: llm
    prompt: prompts/plot/repair_enables.yaml
    state_key: functions
    parse_json: true
    loop_limit: 3
    loop_exit: END

  # --- Layer 7: Beliefs + Affects ---
  assign_beliefs_affects:
    type: llm
    prompt: prompts/plot/assign_beliefs_affects.yaml
    state_key: functions
    parse_json: true

  validate_beliefs_affects:
    type: python
    tool: plot_validate_beliefs_affects

  repair_beliefs_affects:
    type: llm
    prompt: prompts/plot/repair_beliefs_affects.yaml
    state_key: functions
    parse_json: true
    loop_limit: 3
    loop_exit: END

  # --- Final validation ---
  validate_plan:
    type: python
    tool: plot_validate_plan

edges:
  - from: START
    to: extract_agents
  # Layer 1
  - from: extract_agents
    to: validate_agents
  - from: validate_agents
    to: repair_agents
    condition: "validation.ok == false"
  - from: validate_agents
    to: extract_goals
    condition: "validation.ok == true"
  - from: repair_agents
    to: validate_agents
  # Layer 2
  - from: extract_goals
    to: validate_goals
  - from: validate_goals
    to: repair_goals
    condition: "validation.ok == false"
  - from: validate_goals
    to: extract_glosses
    condition: "validation.ok == true"
  - from: repair_goals
    to: validate_goals
  # Layer 3
  - from: extract_glosses
    to: validate_glosses
  - from: validate_glosses
    to: repair_glosses
    condition: "validation.ok == false"
  - from: validate_glosses
    to: classify_kinds
    condition: "validation.ok == true"
  - from: repair_glosses
    to: validate_glosses
  # Layer 4
  - from: classify_kinds
    to: validate_kinds
  - from: validate_kinds
    to: repair_kinds
    condition: "validation.ok == false"
  - from: validate_kinds
    to: assign_pre_eff
    condition: "validation.ok == true"
  - from: repair_kinds
    to: validate_kinds
  # Layer 5
  - from: assign_pre_eff
    to: validate_pre_eff
  - from: validate_pre_eff
    to: repair_pre_eff
    condition: "validation.ok == false"
  - from: validate_pre_eff
    to: assign_enables
    condition: "validation.ok == true"
  - from: repair_pre_eff
    to: validate_pre_eff
  # Layer 6
  - from: assign_enables
    to: validate_enables
  - from: validate_enables
    to: repair_enables
    condition: "validation.ok == false"
  - from: validate_enables
    to: assign_beliefs_affects
    condition: "validation.ok == true"
  - from: repair_enables
    to: validate_enables
  # Layer 7
  - from: assign_beliefs_affects
    to: validate_beliefs_affects
  - from: validate_beliefs_affects
    to: repair_beliefs_affects
    condition: "validation.ok == false"
  - from: validate_beliefs_affects
    to: validate_plan
    condition: "validation.ok == true"
  - from: repair_beliefs_affects
    to: validate_beliefs_affects
  # Final
  - from: validate_plan
    to: END
```

### 6d. Prompt design for small models

Each prompt follows a strict pattern optimized for small-model capacity:

```yaml
# prompts/plot/extract_agents.yaml
system: >
  You extract characters and world-state from story synopses.
  Output JSON only. No markdown fences.
user: |
  Read this synopsis and extract:
  1. Every named character and named group
  2. What is true about each at the START of the story

  Use ONLY these predicates:
  - alive(character) = true/false
  - at(character, place) = true/false
  - holds(character, object) = true/false
  - faction(character, group) = true/false
  - rel(character, character) = value (e.g. "enemy", "sibling", "ally")

  Synopsis:
  {premise}

  Output format:
  {
    "agents": ["Name1", "Name2", ...],
    "initial_world": [{"pred": "alive", "args": ["Name1"], "value": true}, ...],
    "initial_belief": [{"observer": "X", "fluent": {"pred": "...", "args": [...]}, "held": ...}, ...]
  }
schema:
  name: AgentExtraction
  fields:
    agents: {type: list[str], description: "Named characters and groups"}
    initial_world: {type: list, description: "World-state fluents"}
    initial_belief: {type: list, description: "Initial belief state"}
```

**Key principles for small-model prompts:**

1. **One task per prompt.** Never ask for agents AND goals AND glosses in one
   call. The model's attention budget is limited; splitting tasks ensures each
   gets full attention.

2. **Enumerate the vocabulary in-prompt.** The model cannot remember a vocabulary
   from a prior call. Each prompt includes the specific vocabulary it needs
   (predicates for L1/L2/L5, function kinds for L4, affect kinds for L7).

3. **Show the output schema explicitly.** Small models are more reliable with
   concrete JSON examples than with abstract descriptions. Each prompt includes
   a literal output format with field names and types.

4. **Repair prompts include the error.** The repair node's prompt includes both
   the previous output and the specific validation error:
   ```
   Your previous output had this error:
   {validation.flaws}

   Fix the error. Keep everything else unchanged. Output the corrected JSON.
   ```

5. **No cross-layer reasoning.** Layer 4 (classify kinds) does not need to think
   about Layer 7 (beliefs). Each prompt is self-contained with its layer's task
   and the prior layers' outputs as read-only context.

6. **Cumulative context is additive, not exponential.** Each layer adds a small
   typed artifact to state. By Layer 7, the model sees: agents (~50 tokens),
   goals (~50 tokens), glosses (~200 tokens), classified functions (~300 tokens),
   pre/eff (~400 tokens), enables (~100 tokens). Total context: ~1100 tokens of
   prior output + ~200 tokens of prompt + synopsis (~500 tokens). This is well
   within a small model's window.

### 6e. Cost analysis

| | v3 (one-shot) | v4 (7-layer) |
|---|---|---|
| LLM calls (happy path) | 1 (large model) | 7 (small model) |
| LLM calls (1 retry on L5) | 2 (full regen, large) | 9 (7 + 1 repair + 1 re-validate) |
| LLM calls (worst case) | 4 (full regen ×4, large) | 28 (7 layers × 4 attempts max) |
| Per-call token input | ~2000 (everything) | ~800 avg (layer-specific) |
| Per-call token output | ~1500 (full plan) | ~200 avg (layer output) |
| Total tokens (happy path) | ~3500 (1 large call) | ~7000 (7 small calls) |
| Cost (happy path, approx) | 1× large-model call | ~0.3× (7 small calls at ~20× cheaper per token) |
| Latency (happy path) | ~10s (1 call) | ~14s (7 × ~2s per small call) |
| Retry cost | Full plan regeneration | Layer-specific, ~2s per retry |

**The small-model pipeline is cheaper than the one-shot large-model approach.**
7 small-model calls cost roughly 30% of one large-model call (Haiku is ~20×
cheaper per token than Opus). Latency is comparable. Retry is dramatically
cheaper — a failed Layer 5 costs ~2s and ~200 tokens to retry, not ~10s and
~3500 tokens.

### 6f. YAMLGraph features exercised

This graph showcases several YAMLGraph capabilities in a single example:

| Feature | Where used |
|---------|-----------|
| LLM nodes with `parse_json` | All 14 LLM nodes |
| Python tool nodes | All 8 validation nodes |
| Conditional edges | `validation.ok == true/false` routing |
| Loop/retry with `loop_limit` | All 7 repair loops |
| `loop_exit: END` | Graceful degradation on retry exhaustion |
| State accumulation | Each layer writes to its own state key; later layers read prior keys |
| Inline YAML schemas | Output schemas on LLM nodes |
| Prompt templates with state variables | `{premise}`, `{agents}`, `{glosses}`, `{functions}`, `{validation.flaws}` |

**What it does NOT use** (deliberate simplicity):
- No map nodes (each layer processes the whole plan, not per-function)
- No parallel fan-out (layers are sequential by design)
- No subgraphs (flat graph, 22 nodes)
- No agent nodes (focused extraction, not open-ended reasoning)

---

## 9. What this plan does NOT change

- **The formal language.** Vocabulary, syntax, grammar rules — all from
  plan-v3-planner.md, unchanged.
- **The downstream pipeline.** Outline derivation (FR-568), forward-carry
  (FR-569), beat realization — all consume the completed plan, unchanged.
- **The validation rules.** All 8 rules apply identically. v4 runs them
  earlier (per-layer during authoring) and later (full SAT check on completion).
- **The strangler-fig posture.** `--no-plot-plan` still reverts to full v2.

---

## 10. Open questions

1. **Gloss coverage check.** How do we validate that the glosses cover the
   synopsis? A heuristic (every synopsis paragraph should have at least one gloss
   whose entities overlap) or an LLM-as-judge ("does this set of glosses cover
   all major events in the synopsis?")?

2. **Mechanical enables seeding.** Should Layer 6 pre-compute enables links from
   eff/pre overlap and let the LLM add/remove? Or should the LLM author enables
   from scratch with the glosses as context? The former is more reliable for
   formal links; the latter captures narrative causality the formal predicates
   miss.

3. **Gloss stability.** If Call 2 fails and retries, the glosses are frozen. But
   what if the formalization failure reveals a bad gloss (e.g., a gloss that is
   unclassifiable into any kind)? Should there be an escape hatch to re-open
   Call 1? This would break the isolation guarantee.

4. **Genre-specific prompts.** The Layer 4 prompt (classify glosses into kinds) may
   need genre-specific examples. A saga gloss like "the clans merge" maps to
   `reconciliation` intuitively; a thriller gloss like "the detective examines the
   crime scene" maps to... `lack`? `recognition`? The vocabulary lens depends on
   genre conventions the LLM may not share without examples.

5. **Evaluation.** The paper tests used the 10030-BC saga. v4 should be tested
   against at least one non-saga premise (detective thriller, quest) to validate
   genre coverage of the 16-kind alphabet and the layered pipeline's robustness
   across genres.
