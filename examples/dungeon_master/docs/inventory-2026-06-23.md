# Inventory: DM Plot Model — 2026-06-23

A snapshot of everything we have, what state it's in, and what to do next.

---

## 1. Running code (1361 lines, 48 tests)

The v3 plot model has a working typed core, built across FR-560 → FR-565:

| Module | Lines | What it does | FR |
|--------|-------|-------------|-----|
| `schema.py` | 123 | `PlotPlan`, `Function`, `Fluent`, `Belief`, `AffectDelta`, `PlanFlaw` | FR-560 |
| `validate.py` | 249 | Monotonic lifecycle, ungrounded reveal, SAT check via unified-planning | FR-560 |
| `project.py` | 118 | Ordered functions, projected state at any chapter point | FR-560 |
| `floodmark.py` | 324 | Canonical test fixtures (10030-BC) + falsification variants | FR-560 |
| `up_model.py` | 174 | Compile PlotPlan → unified-planning problem for causal check | FR-560 |
| `author.py` | 122 | Tolerant JSON boundary parse (LLM output → PlotPlan) | FR-563 |
| `realize.py` | 87 | Beat-driven turn instruction (PlotPlan → prose directive) | FR-564 |
| `report.py` | 116 | Human-readable projection table | FR-560 |

**Tests:** 48 test functions across 7 test files covering belief grounding,
causal trio, affect closure, projection, author boundary, realization, and
exclusion seam.

**What the code can do today:**
- Parse an LLM-authored JSON plan into typed Pydantic models
- Validate monotonic lifecycle (alive → dead is one-way)
- Validate ungrounded reveals (can't reveal what no one was wrong about)
- Validate open conditions (preconditions must be satisfiable)
- Validate affect closure (emotional threads must close, unless intentional)
- Project world-state and belief-state at any chapter point
- Compile to unified-planning for causal satisfiability check
- Generate beat-driven turn instructions for the prose realizer

### Schema gaps (v3 → v5)

The running schema has **4 kinds** (`villainy`, `reveal`, `reconciliation`,
`return`) and **2 affect kinds** (`loss`, `guilt`). The v5 plan specifies
**16 kinds** and **5 affect kinds**. The schema also lacks:

| v5 field | Current schema | Gap |
|----------|---------------|-----|
| `gloss` | Not present | The pivot field — load-bearing for beat-writer |
| `motivation` | Not present | Intentionality — Rule 8 (motivated action) |
| `threatens` | Not present | Conflict tracking |
| `enables` | Not present | Causal links (replaces flat `order`) |
| `roles` | Not present | Per-function role assignments |
| `FunctionKind` (16) | 4 kinds | 12 kinds to add |
| `AffectKind` (5) | 2 kinds | 3 kinds to add (`betrayal`, `retaliation`, `hidden_blessing`) |
| `held: bool \| str` | `held: bool` only | Typed beliefs (PT1 finding) |
| `affect_policy` | `intentional_open` list | Genre-aware policy struct |

These are **additive** — existing code continues to work. The schema grows, it
doesn't break.

---

## 2. Design documents (chronological lineage)

### Research arc (the "why")

| Document | Status | What it established |
|----------|--------|-------------------|
| `Generative Plot Model Research.md` | Complete | First argument: generate plot, don't recognize it from prose |
| `research-plan-modeling-plot.md` | Complete | Research plan scoping the generative approach |
| `research-results-modeling-plot.md` | Complete | Literature + spike confirming closed-vocab authoring |
| `plan-generative-plot-model.md` | Complete | ADR: spine model (IPOCL-style partial-order causal-link) |

### Build arc (the "how" — v2 → v3)

| Document | Status | What it established |
|----------|--------|-------------------|
| `architecture.md` | Current | DM v2 architecture reference (stage tree, seams) |
| `refactoring-plan.md` | Current | FR-474 → FR-555 refactoring path |
| `v3-rewrite-guidance.md` | Current | Design doctrine for v3 from v2 learnings |
| `context.md` | Stale | Session context from 2026-06-18 — overtaken by events |
| `continuity-issues.md` | Current | Standing record of why continuity breaks (the problem v3 solves) |
| `continuity-projection-plan.md` | Current | Design synthesis: projected vs reconstructed facts |
| `continuity-calibration-labels.yaml` | Current | Human-labeled calibration data for continuity classifier |
| `design-v3-plot-model-implementation.md` | Complete | M0–M4b build spec (all milestones enforced) |
| `plot-plan.md` | Current | User-facing reference for the plot plan feature |

### Plan evolution arc (the "next")

| Document | Status | What it established |
|----------|--------|-------------------|
| `plan-v3-planner.md` | Updated 2026-06-23 | Phase 0 + 16-kind vocab + Propp cross-refs + genre-bias reflection |
| `plan-v4-layered-planner.md` | Superseded by v5 | Layered pipeline concept; review in §11 identified defects |
| `plan-v5-yaml-native-planner.md` | **Current target** | YAML-native output, per-layer keys + merge, bounded backtrack |

### Evidence arc (the "proof")

| Document | Status | What it proved |
|----------|--------|---------------|
| `paper-test-10030-bc-synopsis-to-plan.md` | Complete (PT1) | DM schema vocabulary cannot carry narrative meaning |
| `paper-test-10030-bc-plan-output.json` | Artifact | LLM-authored plan JSON from PT1 |
| `paper-test-10030-bc-spine-encoding.md` | Complete (PT2) | Spine encoding recovers narrative (7/7 with gloss); gloss is load-bearing |
| `grokipedia_propp.md` | Reference | Propp's 31 functions (cross-reference for 16-kind alphabet) |

### Genre corpus (the "test harness")

| Artifact | Format | Count |
|----------|--------|-------|
| `v4/genre-plots/*.md` | JSON-in-markdown (design docs) | 4 (thriller, quest, horror, sci-fi) |
| `v4/genre-synopses/*.txt` | Prose (archive) | 4 |
| `v5/genre-plots/*.yaml` | YAML plan files (machine-readable) | 4 |
| `v5/*.txt` | Prose synopses (pipeline inputs) | 4 |

**Combined kind coverage:** 15 of 16 kinds exercised across the 4 genres.

---

## 3. Feature requests (the pipeline)

| FR | Title | Status | Dependency |
|----|-------|--------|-----------|
| FR-564 | M4b — realize (beat instruction) | **Enforced** | — |
| FR-565 | Producer integration (default-on) | **Enforced** | FR-564 |
| FR-566 | Complete the grammar (16 kinds, 5 affects, Rules 1+6) | Proposed | Phase 0 schema changes |
| FR-567 | Plan-projected state | Proposed | FR-566 |
| FR-568 | Plan-derived outline | Proposed | FR-567 |
| FR-569 | Plan-projected forward-carry | Proposed | FR-568 |

FR-560 → FR-565 are built and enforced. FR-566 → FR-569 are the v3 planner plan's
Phase 1–4. The v5 planner plan is **orthogonal** — it's about how the plan is
*authored* (synopsis → plan), while FR-566–569 are about how the plan is *used*
(plan → prose).

---

## 4. The gap map

```
AUTHORING                           CONSUMPTION
(how plans are produced)            (how plans drive prose)

v5 planner pipeline ──────┐    ┌──── FR-566 complete grammar
  L1: extract agents      │    │     (16 kinds, 5 affects)
  L2: extract goals       │    │
  L3: extract glosses     │    │──── FR-567 projected state
  L4: classify kinds      ├──→ │     (world + belief at any point)
  L5: assign pre/eff      │    │
  L6: assign causality    │    │──── FR-568 plan-derived outline
  L7: assign affects      │    │     (chapters from function order)
  merge + validate        │    │
                          │    │──── FR-569 forward-carry
                          │    │     (plan owns chapter-close state)
         ┌────────────────┘    └────┐
         ▼                          ▼
    plot-plan.yaml              schema.py
    (the plan file)             (the typed contract)
```

**The two tracks share `schema.py`.** The schema must grow (Phase 0 / FR-566)
before either track can advance beyond what exists today. This is the
**convergence point** — both authoring and consumption need the same schema
extensions.

---

## 5. What to do next

### Priority 0: Schema extensions (Phase 0 — unblocks both tracks)

Add to `schema.py`:
- `gloss: str` on `Function`
- `motivation: Motivation | None` on `Function`
- `threatens: Motivation | None` on `Function`
- `enables: list[str]` on `Function`
- `roles: dict[str, str]` on `Function`
- Extend `FunctionKind` from 4 to 16
- Extend `AffectKind` from 2 to 5
- `held: bool | str` on `Belief` (currently `bool` only)
- `affect_policy` on `PlotPlan`
- Rule 8 check in `validate.py` (motivated action)

**This is additive.** Existing tests pass unchanged — new fields have defaults.
New tests cover the new kinds, affects, and Rule 8. The floodmark fixtures don't
need to change (they use the original 4 kinds).

**Estimated size:** ~80 lines of schema changes, ~60 lines of new validation,
~100 lines of new tests. One PR.

### Priority 1: L4 spike (proves or kills the v5 pipeline)

After schema extensions, run the **classify kinds** spike:
1. Extract glosses from the 4 YAML plans (already in `v5/genre-plots/`)
2. Write one prompt (v5 §6d sketch is nearly ready)
3. Call Haiku once per synopsis
4. Compare output kinds to ground truth

If L4 works (≥75% accuracy across 4 genres), proceed to build the full pipeline.
If it doesn't, the vocabulary or prompt design needs revision before building
anything.

### Priority 2: Build authoring pipeline (v5 §12, steps 2–8)

Phase A → Phase B → Phase C → merge → validate → emit. The 4 synopses are the
test corpus throughout.

### Priority 3: Build consumption pipeline (FR-566 → FR-569)

Complete the grammar, projected state, plan-derived outline, forward-carry. This
is the path from plan to prose — it can proceed in parallel with authoring once
the schema is shared.

---

## 6. What to retire

| Document | Action | Reason |
|----------|--------|--------|
| `context.md` | Delete | Session context from 2026-06-18, fully overtaken |
| `plan-v4-layered-planner.md` | Keep as archive | Superseded by v5, but §11 review is referenced |
| `v4/genre-synopses/` | Delete (copies in v5/) | Redundant — v5 has identical synopses |

Everything else stays. The research arc documents are historical record. The v3
planner plan is the formal language spec. The paper tests are evidence.
