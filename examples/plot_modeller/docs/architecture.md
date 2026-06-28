# Architecture: Plot Modeller

**Date:** 2026-06-23
**Companion:** [vision.md](vision.md) (what and why), [plan-implementation-phases.md](plan-implementation-phases.md) (when)

---

## System boundary

The Plot Modeller has one job: **synopsis in, validated plan out.** It does not
write prose, run turn engines, or know its consumers. The plan file is the
contract — everything upstream produces it, everything downstream reads it.

```
                    ┌─────────────────────────────────┐
                    │         Plot Modeller            │
                    │                                  │
  Synopsis ───────▶ │  Pipeline  →  Merge  →  Validate │ ──────▶  Plan (.yaml)
  (prose seed)      │                                  │          (the contract)
                    └─────────────────────────────────┘
                                                            │
                                              ┌─────────────┼──────────────┐
                                              ▼             ▼              ▼
                                        Chapter writer  Turn engine   Outline view
                                        (or any consumer that reads the plan format)
```

## Three-layer decomposition

### Layer 1: Schema (the type system)

Pydantic models that define the plan's vocabulary and structure. Everything that
appears in a plan file has a typed representation here.

```
schema/                # all built — FR-571 (Enforced)
├── kinds.py          # FunctionKind enum (17 kinds)
├── affects.py        # AffectKind enum (6 kinds), AffectDelta model
├── predicates.py     # Fluent, Belief (with typed held: bool | str)
├── functions.py      # Function model (kind, gloss, pre/eff, causal, roles)
├── plan.py           # PlotPlan model (meta, agents, world, beliefs, goals, functions, policy)
├── vocab.py          # StoryVocab (FR-593): {locations, objects, aliases} naming dictionary
└── __init__.py       # Public API: PlotPlan, Function, Belief, etc.
```

**Design rules:**
- All fields have defaults — the schema grows additively, never breaks
- Enums are closed vocabularies — the validator catches anything outside them
- `held: bool | str` on Belief — supports both binary and typed beliefs
- `toward: str | None` on AffectDelta — optional relational dimension

### Layer 2: Validators (the rules)

Pure functions that check plan consistency. Each validator takes a plan (or plan
fragment) and returns a list of flaws. Validators are composable — the merge
node runs all of them; individual pipeline layers run the subset relevant to
their output.

```
validators/
├── lifecycle.py      # exists (FR-571) — Monotonic: alive → dead is one-way
├── grounding.py      # exists (FR-571) — Ungrounded reveals: can't reveal what no one was wrong about
├── affects.py        # exists (FR-571) — Affect closure: threads close (or policy says they needn't)
├── causality.py      # planned (Phase 4) — Open conditions: every precondition must be satisfiable
├── reachability.py   # planned (Phase 4) — Goal reachability: at least one path reaches each goal
├── motivation.py     # planned (Phase 4) — Motivated action: every function has a reason (Rule 8)
└── __init__.py       # validate_plan(plan) → list[Flaw]
```

**Design rules:**
- Validators are stateless — they take data, return flaws
- Validators don't fix problems — they report them
- Each validator tests one rule — composability over monoliths
- The affect validator respects `affect_policy` — genre-aware, not genre-blind

### Layer 3: Pipeline (the builder)

YAMLGraph graphs that produce the plan from a synopsis. Each layer is a separate
graph (or a subgraph) with its own prompt, validator, and retry logic.

```
graphs/
├── extract_agents.yaml       # L1: agents + initial world/beliefs (exists — FR-573)
├── extract_goals.yaml        # L2: goals (exists — FR-574, REVISE)
├── extract_glosses.yaml      # L3: beat decomposition (exists — FR-575, GO)
├── classify_kinds.yaml       # L4: kind + subject + roles (exists — FR-570/572, GO)
├── assign_pre_eff.yaml       # L5: preconditions + effects (exists — FR-576, REVISE)
├── assign_causality.yaml     # L6: enables + motivation + threatens (planned — Phase 3)
├── assign_affects.yaml       # L7: affect open/close operations (planned — Phase 3)
├── merge_plan.yaml           # Merge: join per-layer slices → plan file (planned — Phase 4)
└── pipeline.yaml             # Orchestrator: L1 → L2 → L3 → L4–L7 → merge (planned — Phase 4)
```

**Design rules:**
- Each graph writes to its own state key — no layer echoes another's output
- Each graph has a validator node — bad output is caught before propagation
- Retry is bounded (max 3 per layer) — the pipeline fails explicitly, never loops
- No hardcoded provider/model — resolved from `PROVIDER` at run time

## Data flow

### Per-layer state keys

Each pipeline layer writes only the fields it owns. The merge node joins them
by function `id`:

| Layer | State key | Fields written |
|-------|----------|---------------|
| L1 | `agents` | agents, initial_world, initial_belief |
| L2 | `goals` | goals |
| L3 | `glosses` | id, gloss, chapter |
| L4 | `kinds` | id, kind, subject, roles |
| L5 | `pre_eff` | id, pre_world, eff_world, pre_belief, eff_belief |
| L6 | `causality` | id, enables, motivation, threatens |
| L7 | `affects` | id, eff_affect |

The merge node reads all state keys, joins by `id`, assembles the full
`PlotPlan`, and runs `validate_plan()`. The output is a single `.yaml` file.

### The LLM-validator-retry pattern

Every pipeline layer follows the same pattern:

```
         ┌──────────┐
         │ LLM node │ ── writes → state_key_raw (text)
         └────┬─────┘
              │
         ┌────▼──────┐
         │ Validator  │ ── reads state_key_raw
         │            │    on success: writes state_key (parsed) + validation
         │            │    on failure: writes validation only
         └────┬──────┘
              │
        ┌─────┴─────┐
        │            │
   ok=true      ok=false (+ retry < 3)
        │            │
       END      back to LLM (errors in prompt)
```

This pattern is identical for all 7 layers. The prompts, validators, and state
keys differ; the graph shape does not.

### Backtrack

Phase C (L4–L7) failures can trigger a cross-phase backtrack to L3 (re-generate
glosses). This happens at most once. If the re-generated glosses also fail Phase
C, the pipeline stops and reports which layer failed and why.

```
L3 (glosses) → L4 → L5 → L6 → L7 → merge
                │              │
                ▼              ▼
            L4 fail?       L6 fail?
                │              │
         retry (×3)      retry (×3)
                │              │
            exhausted?     exhausted?
                │              │
         backtrack → L3    report failure
         (once only)
```

## The plan contract

The plan file is the interface between the Plot Modeller and its consumers.
The contract is defined by the schema layer (Pydantic models) and documented
as a YAML specification.

### Contract guarantees (what a consumer can rely on)

1. **Parseable:** `yaml.safe_load()` succeeds — the file is valid YAML
2. **Typed:** every field matches the Pydantic schema — no surprise types
3. **Lifecycle-sound:** dead characters stay dead
4. **Causally satisfiable:** every precondition has a producer earlier in order
5. **Affect-tracked:** every open affect has a closer (or the policy permits it)
6. **Goal-aware:** goals are stated; reachability is checked (but partial failure
   is genre-dependent — horror plans may not reach all goals)

### Contract non-guarantees (what a consumer must handle)

1. **Narrative quality:** the plan is structurally valid, not necessarily good
2. **Prose fidelity:** the gloss is a compression; the prose generator must
   expand, not copy
3. **Completeness:** the plan may have 7 functions or 20 — the consumer adapts
4. **Ordering stability:** function order may change between pipeline runs on
   the same synopsis (the causal links are stable; the sequence is not)

## Predicate vocabulary

The world-state model uses a small, closed predicate set:

| Predicate | Args | Value type | What it tracks |
|-----------|------|-----------|----------------|
| `alive` | [character] | bool | Existence (death is permanent) |
| `at` | [character, location] | bool | Location |
| `holds` | [character, object] | bool | Possession |
| `rel` | [character, character] | str | Relationship (lovers, colleagues, entrained, ...) |
| `faction` | [character, group] | bool | Group membership |

This vocabulary is deliberately minimal. The STRIPS/PDDL tradition shows that
5 predicates suffice for narrative causal reasoning across genres. New predicates
can be added, but the bar is high — the gloss carries the detail that predicates
cannot.

## Dependency map

```
vision.md                        ← what and why
    │
architecture.md (this file)      ← how the pieces fit
    │
plan-implementation-phases.md    ← when to build what
    │
    ├── schema/                  ← Layer 1: types
    │     └── all 5 modules built (FR-571, Enforced)
    │
    ├── validators/              ← Layer 2: rules
    │     └── lifecycle/grounding/affects built (FR-571); causality/reachability/motivation planned (Phase 4)
    │
    ├── graphs/                  ← Layer 3: pipeline
    │     └── L1–L5 built (FR-570/572/573/574/575/576); L6/L7/merge/pipeline planned
    │
    ├── prompts/                 ← Layer 3: prompts
    │     └── L1–L5 built (FR-570/573/574/575/576)
    │
    ├── nodes/                   ← Layer 3: tool functions
    │     └── tools.py — validators for L1–L5 (FR-570/573/574/575/576)
    │
    ├── fixtures/                ← Test corpus
    │     └── 5 synopses + ground-truth plans (FR-570/572)
    │
    └── evaluate.py              ← Spike evaluator (L3/L4/L5 scoring — FR-570/575/576)
```

## Technology choices

| Choice | Rationale |
|--------|-----------|
| **YAMLGraph** | Framework for LLM pipeline graphs — the project's own tool |
| **Pydantic** | Schema validation with defaults, additive schema evolution |
| **YAML output** | LLM-friendly (indentation, no delimiters), framework-native |
| **STRIPS-style predicates** | Minimal, sufficient for causal reasoning, proven in narrative planning |
| **Per-layer state keys** | Small model can write a slice; no layer echoes prior layers |
| **unified-planning (optional)** | SAT check for causal satisfiability — existing integration in DM |
