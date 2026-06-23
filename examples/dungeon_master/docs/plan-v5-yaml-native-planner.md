# Plan: v5 YAML-Native Planner

**Status:** Target design.
**Created:** 2026-06-23
**Predecessor:** [`plan-v4-layered-planner.md`](plan-v4-layered-planner.md) (the
layered pipeline concept), [`plan-v3-planner.md`](plan-v3-planner.md) (the formal
language).
**Evidence base:**
- PT1 [`paper-test-10030-bc-synopsis-to-plan.md`](paper-test-10030-bc-synopsis-to-plan.md)
  — DM schema, vocabulary insufficiency
- PT2 [`paper-test-10030-bc-spine-encoding.md`](paper-test-10030-bc-spine-encoding.md)
  — spine encoding, gloss as pivot
- v4 genre plots [`v4/genre-plots/`](v4/genre-plots/) — 4 genres as JSON-in-markdown (design docs)
- v5 genre plots [`v5/genre-plots/`](v5/genre-plots/) — same 4 genres as YAML plan files (machine-readable)
- Genre synopses [`v5/*.txt`](v5/) — prose inputs for pipeline testing
- v4 review §11 — concrete defects and design tensions
- Diary [`diary-2026-06-23-the-lens-and-the-prose.md`](../../docs/diary/diary-2026-06-23-the-lens-and-the-prose.md)
  — gloss round-trip insight, review-the-machine heuristic

---

## 0. What v5 changes

v4 was the right *idea* with the wrong *format* and three unresolved design
tensions. v5 keeps the layered decomposition and fixes what broke:

| v4 problem | v5 fix | Section |
|-----------|--------|---------|
| JSON-in-markdown output (fragile for LLMs, inconsistent with framework) | **YAML-native output** — every layer emits YAML, the final plan is a `.yaml` file | §1 |
| All layers write `state_key: functions` → small model must echo entire accreting object (v4 §11.3.1) | **Per-layer state keys + deterministic merge** — each layer writes its own slice; Python nodes stitch | §3 |
| Freeze vs. re-open unresolved (v4 §11.3.2 / OQ3) | **Decided: bounded re-open with backtrack budget** | §4 |
| Pivot framing inconsistent (v4 §11.3.3) — L1/L2 are formal extraction, not prose→prose | **Three phases, not seven equal layers** — Extraction (L1–L2), Pivot (L3), Formalization (L4–L7) | §2 |
| `loop_limit`/`loop_exit` placed on wrong nodes (v4 §11.2.1) | **Corrected YAML sketch** — loop limits on re-entered validators, exits to `report_failure` node | §6 |
| No `report_failure` node — loop exhaustion routes to END with no diagnostic (v4 §11.2.2) | **Added `report_failure` Python node** — assembles diagnostic JSON with partial plan | §6 |
| No v5-specific acceptance gate (v4 §11.4) | **Two gates: fault-injection recovery + first-pass yield** | §8 |
| Single-genre evidence (v4 §11.5) | **Four genre synopses as test corpus** — saga, thriller, quest, horror/sci-fi | §8 |
| §7–§8 missing, §5/§9 duplicate (v4 §11.6) | **Clean numbering, no duplicates** | throughout |

---

## 1. YAML as native format

### 1a. Why not JSON

The genre plots exposed the problem. Each function is a mix of:
- **Controlled vocabulary** (`kind: villainy`, `pred: alive`)
- **Natural language** (`gloss: "Hilde leads a dawn raid..."`)
- **Nested structure** (typed beliefs, affect deltas, causal links)

JSON handles structure well but is hostile to natural language (escaped quotes,
no multi-line) and fragile for LLM generation (missing commas, unclosed brackets).
The PT1 paper test documented JSON fence errors (§8b). Asking a small model to
produce nested JSON arrays with typed objects is the wrong bet.

### 1b. Why YAML

YAML is:
- **Indentation-based** — no commas, no brackets, no braces to miscount
- **Multi-line native** — `>` (folded) and `|` (literal) for glosses
- **The framework's own language** — YAMLGraph graphs, prompts, and schemas are all YAML
- **Familiar to the target model** — LLMs see more YAML in training data than structured JSON with typed arrays

### 1c. The plan file format

The pipeline's output is a single `.yaml` file:

```yaml
# plot-plan.yaml — machine-readable, validator-checkable, beat-writer-consumable
meta:
  title: The Vanished Witness
  genre: detective-thriller
  synopsis_hash: sha256:abc123  # ties plan to its source synopsis

agents:
  - Marren
  - Lydia
  - Hagen
  - Consul Drey
  - Witness Pell

initial_world:
  - pred: alive
    args: [Marren]
    value: true
  - pred: alive
    args: [Witness Pell]
    value: true
  - pred: at
    args: [Witness Pell, Safe house]
    value: true
  - pred: holds
    args: [Witness Pell, ledger]
    value: true
  - pred: rel
    args: [Hagen, Consul Drey]
    value: co-conspirator
  # ... remaining fluents

initial_belief:
  - observer: Marren
    fluent:
      pred: rel
      args: [Hagen, Consul Drey]
    held: neutral
  # ... remaining beliefs

goals:
  - pred: alive
    args: [Witness Pell]
    value: true
  - pred: at
    args: [Witness Pell, Court]
    value: true
  - pred: holds
    args: [Marren, ledger]
    value: true

functions:
  - id: F1
    kind: villainy
    gloss: >
      The night before trial, Hagen's hired men abduct Witness Pell
      from the court safe house and burn the building.
    subject: Hagen
    roles:
      villain: Hagen
      victim: Witness Pell
    chapter: 1
    observers: [Marren]
    motivation:
      agent: Hagen
      goal: protect_Drey
    threatens:
      agent: Marren
      goal: deliver_witness
    enables: [F2]
    pre_world:
      - pred: at
        args: [Witness Pell, Safe house]
        value: true
    eff_world:
      - pred: at
        args: [Witness Pell, Safe house]
        value: false
      - pred: at
        args: [Witness Pell, Warehouse]
        value: true
    eff_belief:
      - observer: Marren
        fluent:
          pred: alive
          args: [Witness Pell]
        held: unknown
    eff_affect:
      - op: open
        char: Marren
        kind: loss
  # ... remaining functions

order:  # derived from enables — transitive closure
  - [F1, F2]
  - [F2, F3]
  # ...

affect_policy:
  unclosed_is_error: true  # false for horror genre
```

**What this gains over JSON-in-markdown:**

| Property | JSON-in-markdown | YAML plan file |
|----------|-----------------|----------------|
| Parseable by validator | Extract from fences, parse JSON | `yaml.safe_load()` — one call |
| Parseable by beat-writer | Same extraction dance | Direct state key access |
| Generable by small model | Fragile (syntax errors) | Tolerant (indentation, no delimiters) |
| Human-readable | Good (markdown context helps) | Good (reads like a form) |
| Diffable in git | JSON blocks are opaque | Line-level diffs |
| YAMLGraph-native | Alien format inside native framework | Same format as graphs and prompts |

### 1d. What stays in markdown

The genre plots (`genre-plots/*.md`) are **design documents for humans** — they
contain rationale, observations, vocabulary coverage analysis, and v4 planner
notes. These stay as markdown. The plan file is what the pipeline *produces*
and the downstream pipeline *consumes*. The two artifacts serve different audiences.

---

## 2. Three phases, not seven equal layers

v4 presented seven layers as a uniform sequence. The v4 review (§11.3.3) noted
this is factually wrong: L1–L2 are formal extraction (prose → predicates), L3 is
the prose pivot (prose → prose), and L4–L7 are formalization (prose → controlled
vocabulary). v5 names the phases:

```
Synopsis (unstructured prose, ~500 words)
    │
    │  PHASE A: Extraction (2 layers)
    │  └─ L1: agents + initial world/beliefs
    │  └─ L2: goals
    ▼
Scaffolding (agents, world-state, goals — formal, validated)
    │
    │  PHASE B: Pivot (1 layer)
    │  └─ L3: glosses (one-sentence beat decomposition)
    ▼
Glosses (structured prose, ~7 sentences — the intermediate representation)
    │
    │  PHASE C: Formalization (4 layers)
    │  └─ L4: classify kinds + assign roles
    │  └─ L5: pre/eff (world + belief preconditions and effects)
    │  └─ L6: enables + motivation + threatens (causal + intentional)
    │  └─ L7: affects (open/close emotional threads)
    ▼
Plan (YAML file — validated, complete)
```

**Why the phases matter for retry (§4):** Re-opening works differently across
phase boundaries than within a phase. A Phase C failure can re-open Phase C
layers. A Phase C failure that proves a Phase B gloss is bad requires a
cross-phase backtrack, which is more expensive and bounded separately.

---

## 3. Per-layer state keys + deterministic merge

### 3a. The v4 problem

v4 layers L4–L7 all wrote `state_key: functions`. Each call's output **replaced**
the entire functions list. This meant every small-model call had to echo all fields
from all prior layers verbatim — the exact thing v4 argued a small model cannot do
reliably (§6a). The plan argued against itself (v4 §11.3.1).

### 3b. The v5 solution: write slices, merge mechanically

Each layer writes only the fields it owns to its own state key. A deterministic
Python merge node joins them by function `id`:

| Layer | State key | Fields written |
|-------|----------|---------------|
| L3 | `glosses` | `id`, `gloss`, `chapter` |
| L4 | `kinds` | `id`, `kind`, `subject`, `roles` |
| L5 | `pre_eff` | `id`, `pre_world`, `eff_world`, `pre_belief`, `eff_belief` |
| L6 | `causality` | `id`, `enables`, `motivation`, `threatens` |
| L7 | `affects` | `id`, `eff_affect` |

The merge node (`merge_functions`) runs after all Phase C layers complete and
joins by `id`:

```python
def merge_functions(state):
    """Deterministic merge — no LLM, no information loss."""
    by_id = {}
    for g in state["glosses"]:
        by_id[g["id"]] = dict(g)
    for source_key in ["kinds", "pre_eff", "causality", "affects"]:
        for item in state[source_key]:
            by_id[item["id"]].update(item)
    return {"functions": list(by_id.values())}
```

**What this gains:**
- Each LLM call emits **only ~3–5 fields per function**, not the full 15-field object
- No echoing of prior layers' fields — eliminates the silent field-drop risk
- Merge is mechanical and lossless — a Python function, not an LLM task
- Each layer's validator checks a smaller, well-scoped artifact

### 3c. What each layer's LLM output looks like (YAML)

**L4 output (kinds):**

```yaml
- id: F1
  kind: villainy
  subject: Hagen
  roles:
    villain: Hagen
    victim: Witness Pell

- id: F2
  kind: lack
  subject: Marren
  roles:
    hero: Marren
```

**L6 output (causality):**

```yaml
- id: F1
  enables: [F2]
  motivation:
    agent: Hagen
    goal: protect_Drey
  threatens:
    agent: Marren
    goal: deliver_witness

- id: F2
  enables: [F3]
  motivation:
    agent: Marren
    goal: deliver_witness
  threatens: null
```

Each output is short, focused, and easy for a small model to produce correctly.
The model never sees the full accreting plan — only its slice.

---

## 4. Backtrack policy (the freeze vs. re-open decision)

v4 left this as Open Question 3. v5 decides:

### 4a. The decision

**Bounded re-open with a backtrack budget.**

Within a phase: retry the failed layer (up to 3 attempts). Across phases: if
Phase C exhausts retries and the validation error points to a Phase B artifact
(e.g., "gloss F3 is unclassifiable into any kind"), the pipeline may backtrack to
Phase B and re-open L3, **but only once per Phase C attempt, and only with the
specific error as context.**

### 4b. The backtrack budget

```
Phase A (extraction):     3 retries per layer, no backtrack (no prior phase)
Phase B (pivot):          3 retries for L3, no backtrack into Phase A
Phase C (formalization):  3 retries per layer
  └─ If L4 exhausts → backtrack to L3 with error (1 backtrack allowed)
  └─ If L5 exhausts → backtrack to L3 with error (1 backtrack allowed)
  └─ If L6/L7 exhausts → report failure (too far from pivot to re-open usefully)
```

**Total call budget (worst case):**
- Phase A: 2 layers × 4 attempts = 8 calls
- Phase B: 1 layer × 4 attempts = 4 calls
- Phase C: 4 layers × 4 attempts = 16 calls + 1 backtrack to L3 (4 attempts) = 20 calls
- **Maximum: 32 calls** (realistic worst case: ~12–15)

### 4c. The backtrack prompt

When L4 exhausts and backtracks to L3:

```yaml
system: >
  You decompose a story synopsis into one-sentence beat descriptions.
  A downstream classifier could not match one of your beats to any
  known action type. Revise that beat so it clearly maps to one action.

user: |
  Your previous beat:
  {backtrack_error.failed_gloss}

  The classifier said:
  {backtrack_error.detail}

  The allowed action types are:
  villainy, lack, departure, donor_test, provision, struggle, victory,
  liquidation, return, pursuit, rescue, recognition, exposure,
  punishment, reconciliation, death

  Revise ONLY the failed beat. Keep all other beats unchanged.
  Output all beats as YAML.
```

### 4d. Why not unlimited backtrack

Unlimited backtrack turns the pipeline into a search algorithm with exponential
branching. The budget (1 backtrack per Phase C exhaustion) keeps the pipeline
predictable: it either converges in ~10 calls or reports failure in ~32. The
failure report includes the specific error, the partial plan, and the offending
gloss — enough for a human to fix the synopsis or adjust the vocabulary.

---

## 5. The formal language (inherited from v3)

Unchanged. The 16-kind alphabet, 6 predicates, 5 affect kinds, 8 well-formedness
rules, and plan tuple `⟨I, A, G, F, O⟩` carry forward exactly as specified in
[`plan-v3-planner.md`](plan-v3-planner.md) §1.

The only addition: the plan file includes a **`meta.genre`** field and an
**`affect_policy`** section that parameterizes genre-sensitive validation:

```yaml
affect_policy:
  unclosed_is_error: true   # saga, thriller, quest: affect threads must close
  # unclosed_is_error: false  # horror: open threads are genre-appropriate
  partial_goal_failure: false  # saga, quest: all goals must be achieved
  # partial_goal_failure: true  # horror: death-caused goal failure is legitimate
```

This addresses the genre-diagnostic findings from the horror and sci-fi genre
plots: Rule 5 (affect closure) and Rule 6 (goal reachability) need genre
relaxation.

---

## 6. YAMLGraph implementation

### 6a. Graph topology

```
START
  │
  ▼
┌─── PHASE A: Extraction ────────────────────────────────┐
│                                                         │
│  extract_agents (LLM) → validate_agents (Py)           │
│       ↑                     │         │                 │
│       └── repair_agents ←───┘(errors) │(ok)            │
│                                       ▼                 │
│  extract_goals (LLM) → validate_goals (Py)             │
│       ↑                     │         │                 │
│       └── repair_goals ←────┘(errors) │(ok)            │
│                                       ▼                 │
└─────────────────────────────────────────────────────────┘
  │
  ▼
┌─── PHASE B: Pivot ─────────────────────────────────────┐
│                                                         │
│  extract_glosses (LLM) → validate_glosses (Py)         │
│       ↑                       │         │               │
│       └── repair_glosses ←────┘(errors) │(ok)          │
│                                         ▼               │
└─────────────────────────────────────────────────────────┘
  │
  ▼
┌─── PHASE C: Formalization ─────────────────────────────┐
│                                                         │
│  classify_kinds (LLM) → validate_kinds (Py)            │
│       ↑                      │        │                 │
│       └── repair_kinds ←─────┘(err)   │(ok)            │
│              │(exhausted)             ▼                 │
│              └──→ backtrack_glosses ──→ validate_glosses│
│                                                         │
│  assign_pre_eff (LLM) → validate_pre_eff (Py)         │
│       ↑                       │          │              │
│       └── repair_pre_eff ←────┘(err)     │(ok)         │
│              │(exhausted)               ▼              │
│              └──→ backtrack_glosses ──→ validate_glosses│
│                                                         │
│  assign_causality (LLM) → validate_causality (Py)     │
│       ↑                        │            │           │
│       └── repair_causality ←───┘(err)       │(ok)      │
│                                              ▼          │
│  assign_affects (LLM) → validate_affects (Py)          │
│       ↑                       │          │              │
│       └── repair_affects ←────┘(err)     │(ok)         │
│                                          ▼              │
└──────────────────────────────────────────────────────────┘
  │
  ▼
merge_functions (Py)  ← deterministic join by function id
  │
  ▼
validate_plan (Py)  ← full SAT check, all 8 rules
  │
  ├──(ok)──→ emit_plan (Py)  ← write final .yaml file → END
  │
  └──(errors)──→ report_failure (Py)  ← diagnostic + partial plan → END
```

**Node count:** 11 LLM nodes (7 extract/classify/assign + 4 repair) + 10 Python
nodes (7 validators + merge + emit + report). Repair nodes are shared by the
extract and repair paths (the repair prompt includes the error; the extract prompt
does not — same node, different prompt selected by state).

Wait — let me reconsider. The v4 had 14 LLM nodes (7 + 7 repair). But if we use
per-layer state keys, the repair node for each layer is essentially a re-prompt of
the same layer with the error attached. YAMLGraph's conditional edges + loop
already handle this: the validator routes back to the original extract node with
the error in state. The repair prompt can be the same prompt file with a Jinja2
conditional:

```yaml
# prompts/plot/classify_kinds.yaml
system: >
  You classify story beats into action types.
user: |
  {% if validation.flaws %}
  Your previous classification had errors:
  {% for flaw in validation.flaws %}
  - {{ flaw }}
  {% endfor %}
  Fix only the errors. Keep correct classifications unchanged.
  {% endif %}

  Classify each beat into exactly one action type.
  ...
```

This eliminates the separate repair nodes entirely. **Revised node count:**
7 LLM nodes + 10 Python nodes = **17 nodes** (down from v4's 22).

### 6b. Corrected YAML graph sketch

```yaml
metadata:
  name: plot_plan_v5
  description: >
    YAML-native layered plot-plan authoring pipeline. Converts a synopsis
    into a validated formal plan through 3 phases (extraction, pivot,
    formalization) with per-layer validation, deterministic merge, and
    bounded backtrack. Designed for small language models.
  provider: anthropic
  model: claude-haiku-4-5

state:
  # --- Input ---
  premise:
    type: str
    description: The input synopsis
  genre:
    type: str
    description: Genre tag for affect/goal policy

  # --- Phase A outputs ---
  agents:
    type: list
    description: Extracted agent names
  initial_world:
    type: list
    description: Initial world-state fluents
  initial_belief:
    type: list
    description: Initial belief state
  goals:
    type: list
    description: Goal predicates

  # --- Phase B output ---
  glosses:
    type: list
    description: Beat glosses with id and chapter

  # --- Phase C outputs (per-layer slices) ---
  kinds:
    type: list
    description: "Function kind + subject + roles (by id)"
  pre_eff:
    type: list
    description: "Preconditions and effects (by id)"
  causality:
    type: list
    description: "Enables + motivation + threatens (by id)"
  affects:
    type: list
    description: "Affect open/close deltas (by id)"

  # --- Merged output ---
  functions:
    type: list
    description: Fully merged function list

  # --- Validation ---
  validation:
    type: dict
    description: Current layer validation result
  backtrack_count:
    type: int
    description: Cross-phase backtracks used (budget = 1)
  errors:
    type: list
    description: Pipeline errors

nodes:
  # --- Phase A: Extraction ---
  extract_agents:
    type: llm
    prompt: prompts/plot/extract_agents.yaml
    state_key: agents
    parse_yaml: true

  validate_agents:
    type: python
    tool: plot_validate_agents

  extract_goals:
    type: llm
    prompt: prompts/plot/extract_goals.yaml
    state_key: goals
    parse_yaml: true

  validate_goals:
    type: python
    tool: plot_validate_goals

  # --- Phase B: Pivot ---
  extract_glosses:
    type: llm
    prompt: prompts/plot/extract_glosses.yaml
    state_key: glosses
    parse_yaml: true

  validate_glosses:
    type: python
    tool: plot_validate_glosses

  # --- Phase C: Formalization ---
  classify_kinds:
    type: llm
    prompt: prompts/plot/classify_kinds.yaml
    state_key: kinds
    parse_yaml: true

  validate_kinds:
    type: python
    tool: plot_validate_kinds

  assign_pre_eff:
    type: llm
    prompt: prompts/plot/assign_pre_eff.yaml
    state_key: pre_eff
    parse_yaml: true

  validate_pre_eff:
    type: python
    tool: plot_validate_pre_eff

  assign_causality:
    type: llm
    prompt: prompts/plot/assign_causality.yaml
    state_key: causality
    parse_yaml: true

  validate_causality:
    type: python
    tool: plot_validate_causality

  assign_affects:
    type: llm
    prompt: prompts/plot/assign_affects.yaml
    state_key: affects
    parse_yaml: true

  validate_affects:
    type: python
    tool: plot_validate_affects

  # --- Merge + Final ---
  merge_functions:
    type: python
    tool: plot_merge_functions

  validate_plan:
    type: python
    tool: plot_validate_plan

  emit_plan:
    type: python
    tool: plot_emit_plan

  report_failure:
    type: python
    tool: plot_report_failure

edges:
  # Phase A
  - from: START
    to: extract_agents
  - from: extract_agents
    to: validate_agents
  - from: validate_agents
    to: extract_agents
    condition: "validation.ok == false"
  - from: validate_agents
    to: extract_goals
    condition: "validation.ok == true"
  - from: extract_goals
    to: validate_goals
  - from: validate_goals
    to: extract_goals
    condition: "validation.ok == false"
  - from: validate_goals
    to: extract_glosses
    condition: "validation.ok == true"

  # Phase B
  - from: extract_glosses
    to: validate_glosses
  - from: validate_glosses
    to: extract_glosses
    condition: "validation.ok == false"
  - from: validate_glosses
    to: classify_kinds
    condition: "validation.ok == true"

  # Phase C
  - from: classify_kinds
    to: validate_kinds
  - from: validate_kinds
    to: classify_kinds
    condition: "validation.ok == false"
  - from: validate_kinds
    to: assign_pre_eff
    condition: "validation.ok == true"

  - from: assign_pre_eff
    to: validate_pre_eff
  - from: validate_pre_eff
    to: assign_pre_eff
    condition: "validation.ok == false"
  - from: validate_pre_eff
    to: assign_causality
    condition: "validation.ok == true"

  - from: assign_causality
    to: validate_causality
  - from: validate_causality
    to: assign_causality
    condition: "validation.ok == false"
  - from: validate_causality
    to: assign_affects
    condition: "validation.ok == true"

  - from: assign_affects
    to: validate_affects
  - from: validate_affects
    to: assign_affects
    condition: "validation.ok == false"
  - from: validate_affects
    to: merge_functions
    condition: "validation.ok == true"

  # Merge + Final
  - from: merge_functions
    to: validate_plan
  - from: validate_plan
    to: emit_plan
    condition: "validation.ok == true"
  - from: validate_plan
    to: report_failure
    condition: "validation.ok == false"
  - from: emit_plan
    to: END
  - from: report_failure
    to: END

# Loop limits on the re-entered nodes (validators route back to extractors)
loop_limits:
  extract_agents: 3
  extract_goals: 3
  extract_glosses: 4   # +1 for potential backtrack re-entry
  classify_kinds: 3
  assign_pre_eff: 3
  assign_causality: 3
  assign_affects: 3

loop_exits:
  extract_agents: report_failure
  extract_goals: report_failure
  extract_glosses: report_failure
  classify_kinds: extract_glosses    # backtrack to Phase B
  assign_pre_eff: extract_glosses    # backtrack to Phase B
  assign_causality: report_failure   # too far from pivot
  assign_affects: report_failure     # too far from pivot
```

### 6c. Key differences from v4 sketch

| Change | Why |
|--------|-----|
| `parse_yaml: true` instead of `parse_json: true` | YAML-native output (§1) |
| Per-layer state keys (`kinds`, `pre_eff`, `causality`, `affects`) | Eliminates echo-the-whole-object problem (§3) |
| `merge_functions` Python node before final validation | Deterministic merge, no LLM involvement |
| `report_failure` node as `loop_exit` target | Assembles diagnostic instead of silent END (v4 §11.2.2) |
| `loop_limits` on extractor nodes, not repair nodes | Correct placement per framework semantics (v4 §11.2.1) |
| `loop_exits` for L4/L5 point to `extract_glosses` | Bounded backtrack (§4) |
| Repair logic inside extract prompts via Jinja2 conditional | Eliminates 7 separate repair nodes → 17 nodes total |
| `emit_plan` Python node | Writes the final `.yaml` file to disk |
| Validator return contract: `{ok: bool, flaws: list[str]}` | Prevents dangling route from missing `ok` key (v4 §11.2.3) |

### 6d. Prompt design (revised for YAML output)

Each prompt follows a strict pattern. The key change from v4: the output format
is YAML, and the model is shown a concrete YAML example, not a JSON schema.

```yaml
# prompts/plot/classify_kinds.yaml
system: >
  You classify story beats into action types. Output YAML only.
user: |
  {% if validation.flaws %}
  Your previous output had errors:
  {% for flaw in validation.flaws %}
  - {{ flaw }}
  {% endfor %}
  Fix the errors. Keep correct entries unchanged.

  {% endif %}
  Classify each beat into exactly one action type.

  Allowed types:
  villainy, lack, departure, donor_test, provision, struggle, victory,
  liquidation, return, pursuit, rescue, recognition, exposure,
  punishment, reconciliation, death

  For each beat, also identify the subject (who acts) and roles.
  Roles use these keys: hero, villain, helper, donor, dispatcher,
  false_hero, victim.

  Beats:
  {% for g in glosses %}
  - id: {{ g.id }}
    gloss: {{ g.gloss }}
    chapter: {{ g.chapter }}
  {% endfor %}

  Output format (YAML list):
  - id: F1
    kind: villainy
    subject: CharacterName
    roles:
      villain: CharacterName
      victim: CharacterName
  - id: F2
    kind: lack
    subject: CharacterName
    roles:
      hero: CharacterName
```

**Principles (carried from v4, updated):**

1. **One task per prompt.** Unchanged.
2. **Enumerate vocabulary in-prompt.** Unchanged.
3. **Show output as YAML example, not schema description.** A small model
   imitates a concrete example more reliably than it interprets an abstract spec.
4. **Repair is a conditional block in the same prompt.** No separate repair node.
   If `validation.flaws` is non-empty, the error block appears; otherwise it
   doesn't. The model sees only what it needs.
5. **No cross-layer reasoning.** Unchanged.
6. **Cumulative context is additive.** Each layer adds a small YAML fragment.
   By L7, total prior output: agents (~30 tokens), goals (~30 tokens), glosses
   (~150 tokens), kinds (~100 tokens), pre_eff (~250 tokens), causality (~80
   tokens). Total: ~640 tokens of prior output + ~200 tokens of prompt + synopsis
   (~500 tokens) = **~1340 tokens**. Well within small-model capacity.

---

## 7. Validator contract

Every Python validator node returns the same shape:

```python
def plot_validate_kinds(state: dict) -> dict:
    """Validate Layer 4 output: kinds classification."""
    flaws = []
    valid_kinds = {
        "villainy", "lack", "departure", "donor_test", "provision",
        "struggle", "victory", "liquidation", "return", "pursuit",
        "rescue", "recognition", "exposure", "punishment",
        "reconciliation", "death",
    }
    for item in state["kinds"]:
        if item.get("kind") not in valid_kinds:
            flaws.append(f"{item['id']}: unknown kind '{item.get('kind')}'")
        if not item.get("subject"):
            flaws.append(f"{item['id']}: missing subject")
        # ... additional checks
    return {
        "validation": {
            "ok": len(flaws) == 0,
            "flaws": flaws,
            "layer": "kinds",
        }
    }
```

**Contract:**
- Returns `{"validation": {"ok": bool, "flaws": list[str], "layer": str}}`
- `ok = True` → next layer. `ok = False` → retry or backtrack.
- `flaws` contains human-readable error strings (also consumed by repair prompts).
- `layer` identifies which layer failed (for diagnostics and backtrack routing).

**The final validator** (`plot_validate_plan`) runs all 8 well-formedness rules
on the merged plan:

| Rule | Check |
|------|-------|
| 1. Grounded terms | Every entity in pre/eff/goals appears in agents or initial_world |
| 2. Lifecycle monotonicity | `alive → dead` is one-way; no resurrection without explicit kind |
| 3. Causal closure | Every pre has a producer (initial_world or prior eff) |
| 4. Grounded reveal | Every belief flip `false → true` has a prior concealment |
| 5. Affect closure | Every opened thread closes (unless `affect_policy.unclosed_is_error = false`) |
| 6. Goal reachability | Every goal predicate is achievable from initial_world + effects (modulo `affect_policy.partial_goal_failure`) |
| 7. DAG ordering | Enables graph is acyclic |
| 8. Motivated action | Intentional subjects have non-null motivation |

---

## 8. Acceptance gates

### 8a. Fault-injection recovery (proves isolation + backtrack)

Inject a dangling precondition into L5 input (manually corrupt one `pre_world`
entry to reference a non-existent agent). Assert:
- L5 validator catches the error
- L5 retries with the error in prompt
- L1–L4 outputs are **not** regenerated
- The pipeline either repairs or reports failure with the specific flaw

### 8b. First-pass yield (proves small-model feasibility)

Run all 4 genre synopses (`v5/*.txt`) through the pipeline with the
target small model. Measure:
- **Per-layer first-pass rate:** % of layers that pass validation on first attempt
- **Pipeline completion rate:** % of synopses that produce a valid plan
- **Total calls:** average and worst-case across the 4 synopses

**Target:** ≥ 75% per-layer first-pass rate, 4/4 synopses produce valid plans
(with retries), average total calls ≤ 12.

### 8c. Genre coverage (proves vocabulary)

For each completed plan, check:
- Every gloss maps to a valid kind (L4 passes)
- The genre's expected kinds appear (thriller uses exposure+recognition, quest
  uses departure+provision, etc.)
- Affect policy is respected (horror plans may have open threads)

The v5 genre plots (`v5/genre-plots/*.yaml`) serve as ground-truth for comparison.

### 8d. Gloss round-trip (proves the pivot)

*From diary-2026-06-23-the-lens-and-the-prose.md — the diary's seed, promoted to
an acceptance gate.*

The genre synopses were created by converting structured plots back into prose.
This means we have a **golden-pair corpus**: each synopsis is the input, each
structured plot is the expected output. The round-trip test:

1. Feed synopsis into the pipeline → produces a plan with glosses
2. Concatenate the plan's glosses in order → produces a recovered synopsis
3. Compare recovered synopsis to the original synopsis

**Metric:** semantic overlap — do the recovered glosses cover the same events as
the original synopsis? This is not exact-match (the glosses will differ in
wording) but a structural comparison: same agents, same events, same causal order.

This is the only test that evaluates **gloss quality** rather than structural
correctness. A plan can pass all 8 well-formedness rules and still have bad
glosses (too vague, wrong emphasis, missing a key event). The round-trip catches
this: if the recovered synopsis is recognizably the same story, the glosses
captured the narrative; if not, the pivot is lossy.

**Why this matters (from the diary):** "The glosses ARE the story. I reconstructed
each synopsis almost entirely from the ordered function glosses — the predicates,
kinds, and JSON scaffolding contributed nothing to the prose." The round-trip
formalizes this observation into a falsifiable test.

---

## 9. What this plan does NOT change

- **The formal language** (v3 §1): vocabulary, syntax, grammar, 8 rules
- **The downstream pipeline**: outline derivation (FR-568), forward-carry
  (FR-569), beat realization — all consume the completed plan YAML file
- **The strangler-fig posture**: `--no-plot-plan` still reverts to v2
- **The acceptance litmus**: two chapters generable without reading each other's
  prose

---

## 10. Open questions (reduced from v4's 5 to 2)

1. **`parse_yaml` support in YAMLGraph.** The graph sketch uses `parse_yaml: true`
   on LLM nodes. **Confirmed: the framework does not have this.** Grep for
   `parse_yaml` in `yamlgraph/` returns no hits; only `parse_json` exists (in
   `graph_schema.py`, `llm_nodes.py`, `llm_execution.py`). Two paths:
   **(a)** Add `parse_yaml` as a small FR — analogous to `parse_json`, calling
   `yaml.safe_load()` instead of `json.loads()` on the LLM's text output.
   **(b)** Use `parse_json: false` on all LLM nodes and have each downstream
   Python validator call `yaml.safe_load()` as its first step — functional today,
   no framework change, but the parsing is split across 7 validators instead of
   being a declarative node property. **Recommendation:** start with (b) to
   unblock the pipeline; file (a) as an FR for later cleanup.

2. **Mechanical enables seeding.** Should L6 pre-compute enables links from
   eff/pre overlap (Layer 5) and let the LLM add narrative causal links? Or start
   from scratch? The pre-computation is a Python tool node that runs between L5
   validation and L6 extraction. Decision deferred to implementation — try without
   seeding first, add if L6 first-pass rate is too low.

---

## 11. Cost analysis (revised)

| | v3 (one-shot) | v4 (7-layer JSON) | v5 (3-phase YAML) |
|---|---|---|---|
| LLM calls (happy path) | 1 (large) | 7 (small) | 7 (small) |
| LLM calls (1 retry on L5) | 2 (large, full regen) | 9 (small) | 8 (small, no separate repair node) |
| LLM calls (worst case) | 4 (large) | 28 (small) | 32 (small, incl. backtrack) |
| Per-call output tokens | ~1500 (full plan) | ~200 (layer, but must echo all prior fields) | ~80 (layer slice only) |
| Silent corruption risk | High (one bad field loses plan) | **High** (echo error loses prior fields) | **None** (merge is mechanical) |
| Format errors | JSON syntax (PT1 §8b) | JSON syntax | YAML indentation (more forgiving) |
| Backtrack on bad gloss | Full regen | Deterministic halt at L4 | Bounded re-open of L3 |
| Total tokens (happy path) | ~3500 | ~7000 | ~4900 (smaller per-call output) |
| Cost (happy path) | 1× large | ~0.3× large | ~0.2× large (smaller outputs) |

The per-call output reduction (from ~200 tokens echoing everything to ~80 tokens
for the slice) is the main cost improvement. Over 7 calls, this saves ~840 output
tokens — significant at small-model pricing.

---

## 12. Implementation sequence

1. **Spike: YAML parsing path** — framework lacks `parse_yaml` (confirmed).
   Use Python-node parsing (OQ1 option b) to unblock; file FR for `parse_yaml`
   as cleanup.
2. **Build Phase A (L1–L2)** — extract agents + goals. Two prompts, two
   validators. Test against 4 synopses.
3. **Build Phase B (L3)** — extract glosses. One prompt, one validator. Test
   against 4 synopses. Compare to ground-truth genre plots.
4. **Build Phase C (L4–L7)** — classify + formalize. Four prompts, four
   validators. Test per-layer first-pass rate.
5. **Build merge + final validation** — deterministic merge, full SAT check,
   emit plan, report failure.
6. **Backtrack wiring** — add `loop_exits` pointing L4/L5 to `extract_glosses`.
   Test with deliberately bad glosses.
7. **Acceptance gates** — run §8a fault-injection and §8b first-pass yield.
8. **Genre comparison** — diff pipeline output against hand-authored genre plots.

Each step is independently testable. The 4 genre synopses are the test corpus
throughout.
