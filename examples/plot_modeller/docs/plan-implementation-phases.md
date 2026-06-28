# Implementation Phases: Plot Modeller

**Date:** 2026-06-23
**Companion:** [vision.md](vision.md) (what and why), [architecture.md](architecture.md) (how)

---

## Guiding principles

1. **Spike before build.** Every layer gets a measured accuracy number before
   it becomes part of the pipeline. L4 proved this works (FR-570).
2. **Schema first, pipeline second.** The typed models and validators are the
   foundation. The pipeline layers produce data that the schema validates.
3. **One layer at a time.** Each phase delivers a working, tested increment.
   No phase depends on a future phase being complete.
4. **Fail explicitly.** Every phase has a go/no-go gate. A KILL at any gate
   stops the build and redirects — it doesn't invalidate prior phases.
5. **The kill gate runs before the expensive build.** Phase 1b (blind-corpus
   re-test) is the project's KILL gate. No pipeline construction (Phase 2+)
   begins until the blind test returns GO. Planning depth must not outrun
   evidence depth.

**Conditionality:** Phases 2–5 are conditional on the Phase 1b blind-corpus
GO. They are written here to guide the build *if* the vocabulary generalises,
not as committed scope. If Phase 1b KILLs, the vocabulary or prompt is revised
and re-tested before any pipeline code is written.

---

## Phase 0 — Foundation

**Goal:** Extract the schema and validators from the DM, grow them to the
refined vocabulary, and establish the Plot Modeller's own typed core.

**Why first:** Every subsequent phase writes data that the schema must validate.
The schema must exist before the pipeline can produce validated output. Currently
the schema lives in `examples/dungeon_master/api/plot/` with 4 kinds and 2
affects. It needs to grow to 17 kinds, 6 affects, relational `toward`, and the
full function fields (gloss, motivation, threatens, enables, roles).

### Deliverables

| File | What | Size est. |
|------|------|-----------|
| `schema/kinds.py` | `FunctionKind` enum — 17 kinds | ~30 lines |
| `schema/affects.py` | `AffectKind` enum — 6 kinds, `AffectDelta` with `toward` | ~40 lines |
| `schema/predicates.py` | `Fluent`, `Belief` with `held: bool \| str` | ~40 lines |
| `schema/functions.py` | `Function` model — full fields | ~60 lines |
| `schema/plan.py` | `PlotPlan` model — meta, agents, world, beliefs, goals, functions, policy | ~50 lines |
| `validators/lifecycle.py` | Monotonic lifecycle (alive → dead one-way) | ~30 lines |
| `validators/affects.py` | Affect closure with policy awareness | ~50 lines |
| `validators/grounding.py` | Ungrounded reveals | ~40 lines |
| `tests/test_schema.py` | Schema round-trip, defaults, enum membership | ~80 lines |
| `tests/test_validators.py` | Lifecycle, affect closure, grounding | ~100 lines |

**Estimated total:** ~520 lines of code + tests.

### Gate

- All 4 existing genre plans parse into the new schema without error
- All existing DM tests continue to pass (the schema is additive)
- New tests cover 17 kinds, 6 affects, `toward`, `held: bool | str`

### Risk

Low. This is mechanical extraction + additive growth. The DM code is proven
(48 tests, 1361 lines as of the [2026-06-23 inventory](../../dungeon_master/docs/inventory-2026-06-23.md)).
The risk is in the extraction boundaries, not in the logic.

---

## Phase 1 — Vocabulary validation

**Goal:** Confirm the refined vocabulary (17 kinds + `mediation`, 6 affects +
`hope`, relational `toward`) works empirically. Two sub-phases:

### Phase 1a — Update ground truth

Retrofit the 4 hand-authored YAML plans with:
- `mediation` beats (where `lack` currently absorbs "hero commits to act")
- `hope` affect threads (where provision/rescue opens positive anticipation)
- Relational `toward` on existing affect operations

This updates the test corpus to match the refined vocabulary.

### Phase 1b — Blind-corpus re-test

Author one new synopsis **without** seeing the 17-kind list. Write a story seed
from scratch — characters, conflict, resolution — without reference to the
vocabulary. Then:

1. Hand-author its ground-truth plan (using the 17 kinds, now visible)
2. Run L4 classification against it (the blind test)
3. Compare to the self-derived corpus score (0.80)

### Deliverables

| File | What |
|------|------|
| Updated `fixtures/ground-truth/*.yaml` (4 files) | Retrofitted with mediation, hope, toward |
| `fixtures/ground-truth/<blind-synopsis>.yaml` | 5th plan — hand-authored from blind synopsis |
| `fixtures/synopses/<blind-synopsis>.txt` | 5th synopsis — authored without kind list |
| Updated `prompts/classify_kinds.yaml` | 17 kinds (add mediation) |
| `results/evaluation/blind-corpus-eval.yaml` | L4 accuracy on the blind synopsis |

### Gate

- L4 accuracy on the blind synopsis ≥ 0.75 → **GO** (the vocabulary generalises)
- L4 accuracy on the blind synopsis 0.50–0.75 → **REVISE** (prompt or vocab needs work)
- L4 accuracy on the blind synopsis < 0.50 → **KILL** (the approach doesn't generalise)

The self-derived corpus re-test (with mediation added) must also hold ≥ 0.75.

**Result (FR-572, 2026-06-24): GO.** Blind synopsis 0.90; self-derived corpus
39/48 = 0.81. The KILL gate passed — the 0.80 was not authorial leakage. Pipeline
construction (Phase 2+) authorised.

### Risk

Medium. The blind test is the real gate. If the self-derived 0.80 was inflated
by authorial leakage, the blind test will show it.

---

## Phase 2 — Extraction pipeline (L1–L3)

**Goal:** Build the first three pipeline layers: extract agents/world/beliefs
(L1), extract goals (L2), extract glosses (L3). These take a raw synopsis and
produce the structured scaffold that Phase C formalises.

### Why this order

L1–L3 are entity extraction and sentence decomposition — solved NLP tasks. They
are lower-risk than L4–L7 and produce the inputs that all formalization layers
need. Building them after Phase 1 (vocabulary validation + blind test) means the
vocabulary is confirmed before any pipeline code is written, and the schema can
validate L1–L3 output from day one.

### Deliverables

| File | What |
|------|------|
| `graphs/extract_agents.yaml` | L1 graph: synopsis → agents, initial_world, initial_belief |
| `graphs/extract_goals.yaml` | L2 graph: synopsis + agents → goals |
| `graphs/extract_glosses.yaml` | L3 graph: synopsis → glosses (id, gloss, chapter) |
| `prompts/extract_agents.yaml` | L1 prompt |
| `prompts/extract_goals.yaml` | L2 prompt |
| `prompts/extract_glosses.yaml` | L3 prompt |
| `nodes/tools.py` (extended) | `validate_agents`, `validate_goals`, `validate_glosses` |
| `tests/test_extraction.py` | Golden tests for L1–L3 validators |

### Per-layer spikes

Each layer gets its own spike-and-measure cycle before integration:

- **L1 spike:** Run against 4 synopses, compare extracted agents to ground truth.
  Gate: ≥ 90% agent recall (these are named entities — should be near-perfect).
- **L2 spike:** Run against 4 synopses with ground-truth agents provided.
  Gate: goals match ground truth structurally (predicate + args correct).
- **L3 spike:** Run against 4 synopses. This is the hardest extraction layer —
  beat decomposition is creative, not mechanical. Gate: ≥ 80% of ground-truth
  beats have a corresponding gloss (fuzzy match on narrative content).

**Results (2026-06-24):** L1 built (FR-573). L2 — **REVISE** (goal recall
13/18 = 0.72, below the structural-match bar; follow-up FR-581). L3 — **GO**
(beat recall 42/48 = 0.88, precision 0.87).

### Gate

All three layers pass their spike gates independently. Then run L1→L2→L3 as a
chain on all 5 synopses (4 original + 1 blind) and verify the output is valid
input for L4.

### Risk

Low for L1/L2 (entity extraction). Medium for L3 (beat decomposition is the
creative pivot — the model must decide where one beat ends and another begins).

---

## Phase 3 — Formalization pipeline (L4–L7)

**Goal:** Complete the formalization layers. L4 exists (FR-570). Build L5
(pre/eff), L6 (causality), L7 (affects).

### Why this order

L4 is proven. L5–L7 follow the same LLM-validator-retry pattern. Each layer
adds one formal dimension to the glosses that L3 produced and L4 classified.

### Deliverables

| File | What |
|------|------|
| `graphs/assign_pre_eff.yaml` | L5 graph: glosses + kinds → pre_world, eff_world, pre_belief, eff_belief |
| `graphs/assign_causality.yaml` | L6 graph: glosses + kinds → enables, motivation, threatens |
| `graphs/assign_affects.yaml` | L7 graph: glosses + kinds → eff_affect (with toward) |
| `prompts/assign_pre_eff.yaml` | L5 prompt (predicate vocabulary in-prompt) |
| `prompts/assign_causality.yaml` | L6 prompt |
| `prompts/assign_affects.yaml` | L7 prompt (6 affect kinds + toward in-prompt) |
| `nodes/tools.py` (extended) | `validate_pre_eff`, `validate_causality`, `validate_affects` |
| `tests/test_formalization.py` | Golden tests for L5–L7 validators |

### Per-layer spikes

- **L5 spike:** Given ground-truth glosses + kinds, can the model produce valid
  pre/eff predicates? Gate: ≥ 70% of predicates match ground truth (this is
  harder than L4 — the model must invent predicates, not just classify).
- **L6 spike:** Given glosses + kinds + pre/eff, can the model assign causal
  links? Gate: ≥ 75% of `enables` links match ground truth.
- **L7 spike:** Given glosses + kinds, can the model assign affect open/close
  operations? Gate: ≥ 70% accuracy on affect operations (including `toward`).

**Result so far (2026-06-24):** L5 — **REVISE** (combined world recall
47/85 = 0.55, below the 0.70 gate; misses are fixable prompt issues — label
synonyms, token paraphrase, dropped `=false` departures; follow-up prompt FR).
L6/L7 not yet built.

### Gate

All three layers pass their spike gates. Then run L4→L5→L6→L7 as a chain on
all 5 synopses using L3 output (not ground-truth glosses) and verify the
accumulated output is valid input for the merge node.

### Risk

Medium-high for L5 (predicate invention is creative, not classificatory).
Medium for L6 (causal links are constrained by the beat order). Low-medium for
L7 (affect assignment is similar to L4 — classify, don't invent).

---

## Phase 4 — Merge and full pipeline

**Goal:** Build the merge node and the orchestrator graph. Run the full pipeline
(L1→L2→L3→L4→L5→L6→L7→merge) end-to-end on all 5 synopses. Validate the
output plan files against the full schema.

### Deliverables

| File | What |
|------|------|
| `graphs/merge_plan.yaml` | Merge graph: join per-layer state keys → PlotPlan |
| `graphs/pipeline.yaml` | Orchestrator: L1 → L2 → L3 → L4–L7 → merge |
| `nodes/merge.py` | Deterministic join by function `id` |
| `validators/causality.py` (extended) | Full causal satisfiability check (unified-planning SAT) |
| `validators/reachability.py` | Goal reachability |
| `validators/motivation.py` | Rule 8: motivated action |
| `tests/test_merge.py` | Merge correctness, missing-id handling |
| `tests/test_pipeline.py` | End-to-end: synopsis → plan file → schema-valid |

### The merge node

The merge node is deterministic Python (not an LLM call):

1. Read all per-layer state keys (`agents`, `goals`, `glosses`, `kinds`,
   `pre_eff`, `causality`, `affects`)
2. Join L3–L7 outputs by function `id` into a list of `Function` objects
3. Assemble the `PlotPlan` (meta + agents + world + beliefs + goals + functions
   + affect_policy)
4. Run `validate_plan()` — the full validator suite
5. If valid: write the `.yaml` plan file
6. If invalid: report which validators failed and which functions are broken

### Backtrack logic

The orchestrator graph implements bounded backtrack:

- Phase C layer exhausts retries → backtrack to L3 (re-generate glosses), once
- L3 re-generation also fails Phase C → `report_failure` node with diagnostic
- Phase A/B failures never backtrack — they report and stop

### Gate

- Full pipeline produces a valid plan for ≥ 4 of 5 synopses
- All produced plans pass `validate_plan()` with zero flaws
- At least one plan has partial-order structure (two independent causal threads
  that converge — the sci-fi hybrid is the test case)

### Risk

Low for the merge node (deterministic). Medium for the orchestrator (backtrack
logic, state threading across 7+ graphs). The individual layers are proven by
this point — the risk is in composition, not in the parts.

---

## Phase 5 — Plan contract and documentation

**Goal:** Formalise the plan file as a versioned contract. Write the spec that
consumers read.

### Deliverables

| File | What |
|------|------|
| `docs/plan-contract.md` | YAML schema spec (what a plan file contains, field by field) |
| `docs/plan-contract-v1.schema.yaml` | Machine-readable JSON Schema (or YAML Schema) for the plan file |
| `schema/__init__.py` (extended) | `PlotPlan.to_yaml()` and `PlotPlan.from_yaml()` convenience methods |
| Updated `README.md` | Full usage guide: run pipeline, read plan, evaluate |

### Gate

- A consumer (e.g., the DM turn engine) can read a pipeline-produced plan file
  using only the documented contract — no knowledge of the pipeline internals
- The schema can round-trip: `PlotPlan.from_yaml(plan.to_yaml()) == plan`

---

## Phase summary

| Phase | What | Depends on | Key risk | Est. size |
|-------|------|-----------|----------|-----------|
| **0** | Schema + validators | Nothing | Low (mechanical extraction) | ~520 lines |
| **1** | Vocabulary validation + blind test | Phase 0 | Medium (blind test is the KILL gate) | ~200 lines + 1 synopsis |
| **2** | Extraction pipeline (L1–L3) | Phase 1 GO | Medium (L3 beat decomposition) | ~600 lines |
| **3** | Formalization pipeline (L5–L7) | Phase 2 | Medium-high (L5 predicate invention) | ~600 lines |
| **4** | Merge + full pipeline | Phase 3 | Medium (composition risk) | ~400 lines |
| **5** | Plan contract + docs | Phase 4 | Low (documentation) | ~200 lines |

**Total estimated:** ~2500 lines of code + tests + documentation, across 5
phases with independent gates.

### Build status (2026-06-24)

| Phase | Status | Evidence |
|-------|--------|----------|
| **0** | ✅ Done | FR-571 — schema (5 modules) + 3 validators, 22 tests green |
| **1** | ✅ GO | FR-572 — blind 0.90, self-derived 0.81; KILL gate passed |
| **2** | ⚠️ Partial | L1 built (FR-573); L2 **REVISE** 0.72 (FR-574→FR-581); L3 **GO** 0.88 (FR-575) |
| **3** | ⚠️ Partial | L5 **REVISE** 0.55 (FR-576, follow-up prompt FR); L6/L7 not built |
| **4** | ⬜ Not started | merge + orchestrator |
| **5** | ⬜ Not started | plan contract + docs |

### Dependency graph

```
Phase 0 (schema)
    │
    ▼
Phase 1 (vocab validation + blind test)   ← KILL gate
    │
    ▼
Phase 2 (L1–L3 extraction)
    │
    ▼
Phase 3 (L5–L7 formalization)
    │
    ▼
Phase 4 (merge + full pipeline)
    │
    ▼
Phase 5 (contract + docs)
```

Phases are strictly sequential. Phase 1b (the blind-corpus re-test) is the
project's KILL gate — no pipeline construction begins until it returns GO.
This is deliberate: the cheapest falsification test runs before the most
expensive build work, not in parallel with it.
