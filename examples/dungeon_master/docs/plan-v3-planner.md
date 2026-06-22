# Plan: v3 Stand-Alone Planner

**Status:** Target design. The architectural plan for completing the v3 plot model
so the plan owns the forward-carry, not prose.
**Created:** 2026-06-22
**Predecessor:** [`plan-generative-plot-model.md`](plan-generative-plot-model.md) (the
representation decision), [`design-v3-plot-model-implementation.md`](design-v3-plot-model-implementation.md)
(the M0–M4b build spec, all milestones enforced).
**Companion:** [`architecture.md`](architecture.md) §5c (v3 as-built),
[`plot-plan.md`](plot-plan.md) (user-facing reference).

---

## 0. The gap this plan closes

The research concluded: *author the plot as a closed formal specification before
prose; prove it consistent; demote the LLM to a constrained realizer.*

The M0–M4b milestones built the typed vocabulary, the validator, and two additive
runtime seams (exclusion + realize). But the generation pipeline still
**reconstructs** load-bearing state from prose at chapter close. The plan steers
generation but does not **own** the forward-carry. Two parallel truth sources run:
the `PlotPlan` (authored, static) and the `world_state` ledger (prose-derived,
per-chapter). Neither reads the other.

**The reframe:** the current build is *a type system without a complete grammar*.
The types are defined (schema.py), some rules are checked (validate.py), and some
facts are projected (project.py). But the grammar is incomplete, the vocabulary is
partial, and the plan doesn't own the derived facts its grammar would guarantee.

The fix: **complete the grammar, then the plan's well-formedness guarantees
replace prose-derived reconstruction**.

---

## 1. The formal language

A plot plan is a well-formed expression in a closed formal language. The language
has two artifacts: a **vocabulary** (finite symbols) and a **syntax** (formation
rules). The semantics follow.

### 1a. Vocabulary

**Sorts** (types of things):

| Sort | What it is |
|------|-----------|
| `Character` | A named agent who can act, observe, believe, feel |
| `Place` | A named location |
| `Object` | A named thing that can be held or placed |
| `Fact` | A named atomic proposition |

**Predicates** (properties of things):

| Predicate | Signature | Domain |
|-----------|-----------|--------|
| `alive` | `(Character) → bool` | Existence |
| `at` | `(Character, Place) → bool` | Location |
| `holds` | `(Character, Object) → bool` | Possession |
| `faction` | `(Character, Fact) → bool` | Allegiance |
| `rel` | `(Character, Character, Fact) → bool` | Relationship |
| `believes` | `(Character, Predicate) → bool` | Epistemic (meta-predicate) |

`believes` wraps any other predicate. `alive(Arnulf) = true` AND
`believes(Clan, alive(Arnulf)) = false` is a well-formed state.

**Actions** (closed Propp-like alphabet):

| Action | Signature | Meaning |
|--------|-----------|---------|
| `villainy` | `(subject, target)` | Antagonistic act |
| `departure` | `(subject, from, to)` | Leaving a place |
| `struggle` | `(subject, target)` | Conflict |
| `victory` | `(subject, target)` | Conflict resolved |
| `death` | `(subject)` | Permanent removal (world-truth) |
| `reveal` | `(subject, observers)` | Truth disclosed |
| `return` | `(subject, to)` | Re-entry |
| `reconciliation` | `(subject, target)` | Relational resolution |
| `pursuit` | `(subject, target)` | Chase / hunt |
| `rescue` | `(subject, target)` | Extraction |

**Affect tokens** (emotional arc units, Lehnert Plot Units):

| Token | Meaning |
|-------|---------|
| `loss` | Grief, mourning |
| `guilt` | Remorse |
| `betrayal` | Trust broken |
| `retaliation` | Vengeance sought |
| `hidden_blessing` | Unrecognized good fortune |

Each has two operations: `open` and `close`.

### 1b. Syntax (formation rules)

A **plan** is a tuple `⟨I, A, G, F, O⟩`:

| Part | What | Type |
|------|------|------|
| `I` | Initial state | Set of ground predicates (world-truth + beliefs) |
| `A` | Agents | Set of Characters |
| `G` | Goals | Predicates that must hold at the finale |
| `F` | Functions | Sequence of actions with typed pre/eff/affect |
| `O` | Ordering | Partial order over F (DAG edges) |

Each **function** is a production rule:

```
function F:
    action:   symbol from the action alphabet
    args:     ground terms matching the action's signature
    chapter:  int (scheduling ordinal)
    grain:    book | chapter | turn

    pre:      set of predicates that must hold when F fires
    eff:      set of predicates F makes true after firing
    affect:   set of (open|close, token) pairs
```

### 1c. Grammar (well-formedness rules)

A plan is well-formed iff all seven rules hold:

**Rule 1 — Grounding.** Every term in every predicate in `I`, `G`, `F.pre`,
`F.eff` refers to a named entity in `A` or introduced in `I` or `F`.

**Rule 2 — Causal closure.** For every predicate `p` in any `F.pre`: either
`p ∈ I`, or there exists an earlier function `F'` (per `O`) where `p ∈ F'.eff`.
No dangling preconditions.

**Rule 3 — Monotonic lifecycle.** `alive(c) = false` in `F.eff` is permanent in
world-truth. No later `F'.eff` may assert `alive(c) = true`. Belief revival
(`believes(obs, alive(c)) = true`) is allowed.

**Rule 4 — Grounded reveal.** `believes(obs, p) = true` in `F.eff` requires a
prior state where `believes(obs, p) = false` was established by some function or
initial state. No reveal without concealment.

**Rule 5 — Affect closure.** Every `open(token)` has a later `close(token)` per
`O`, unless `token ∈ intentional_open`.

**Rule 6 — Goal reachability.** Every predicate in `G` is either (a) in `I` and
never negated by any `F.eff`, or (b) established by some `F.eff` and never
negated by a later `F'.eff`.

**Rule 7 — Acyclicity.** `O` is a DAG.

---

## 2. Current state vs complete language

| Artifact | Current (M0–M4b) | Complete language | Gap |
|----------|-------------------|-------------------|-----|
| Sorts | `CharacterId = str`; no typed Place/Object | Typed sorts | Sorts are untyped strings |
| Actions | 4 kinds: villainy, reveal, reconciliation, return | 10 kinds | 6 missing |
| Affects | 2 kinds: loss, guilt | 5 kinds | 3 missing |
| Predicates | 5 defined; only `alive` used in fixtures/projections | 6 (incl. `believes`) actively used | `at`/`holds`/`faction`/`rel` defined but dormant |
| Rule 1 | Not checked | `_check_grounding` | Missing |
| Rule 2 | `_check_causal_antecedent` (existence only) | Existence + temporal validity | Partial |
| Rule 3 | `_check_monotonic_lifecycle` | Complete | — |
| Rule 4 | `_check_belief_grounding` | Complete | — |
| Rule 5 | `_check_affect_closure` | Complete | — |
| Rule 6 | Not checked (deferred to UP solver) | `_check_goal_reachability` | Missing |
| Rule 7 | `ordered_functions` raises on cycle | Complete | — |
| Plan → outline | Independent (plan and outline are co-authored separately) | Outline derived from plan | Gap |
| Forward-carry | Prose-derived at chapter close | Plan-projected | Gap |
| Close validation | Close re-derives state from prose | Close validates against plan projection | Gap |

---

## 3. Build sequence (phased FRs)

Each phase is a separately-judgeable FR. Each phase is testable in isolation and
does not require later phases to deliver value. The strangler-fig posture
continues: `--no-plot-plan` reverts to full v2.

### Phase 1: Complete the grammar (FR-566)

Add the two missing well-formedness checks (Rules 1, 6) and expand the vocabulary
to the destination alphabets. With this, the seven rules are complete and
`validate_plan` is a full grammar check — `unified-planning` becomes truly
optional.

**Deliverables:**
- `_check_grounding(plan)` — Rule 1
- `_check_goal_reachability(plan)` — Rule 6
- `FunctionKind` expanded to 10 kinds
- `AffectKind` expanded to 5 kinds
- Fixture variants exercising the new kinds and checks
- Prompt updated with the full alphabets

**Acceptance:** `validate_plan` implements all 7 rules. Every rule has a fixture
that triggers it and a fixture that passes.

### Phase 2: Plan-projected state (FR-567)

A pure projection function that computes cumulative world+belief+affect state at
any chapter, derived from the plan alone. This is the foundation the forward-carry
and outline derivation build on.

**Deliverables:**
- `project_chapter_state(plan, chapter) → ChapterState` — cumulative
  `eff_world` + `eff_belief` + `eff_affect` through chapter N
- `ChapterState` typed model (world truths, beliefs, open affects)
- Tests against floodmark: state at ch3 = Arnulf alive (world), Clan believes
  dead (belief), loss(Hilde) open (affect)

**Acceptance:** `project_chapter_state` returns a typed, testable state for every
chapter. The state at chapter 0 equals `I`. The state at the last chapter
satisfies `G`.

### Phase 3: Plan-derived outline (FR-568)

The outline is a projection of the plan, not an independent LLM generation. The
plan's functions at each chapter become the chapter's beats. Cast, entry/exit
state are projected.

**Deliverables:**
- `derive_outline(plan, synopsis) → list[ChapterOutline]` — pure projection
  - `beats` = plan functions at chapter, rendered as prose directives
  - `cast` = `chapter_cast(plan, ch)`
  - `entry_state` = `project_chapter_state(plan, ch - 1)` formatted
  - `exit_state` = `project_chapter_state(plan, ch)` formatted
- LLM authors only `title` and `summary` per chapter (prose, not structure)
- Outline gates (`reversal_pack`, `unplayable_beat`, `composition`) validated
  against the plan — they should hold by construction (Rules 2–6 imply them)
- Integration: `generate_story` calls `derive_outline` instead of
  `outline_chapters` when a plan is attached

**Acceptance:** The outline's structural fields (beats, cast, state contracts) are
plan-derived. The outline gates pass by construction for any well-formed plan.

### Phase 4: Plan-projected forward-carry (FR-569)

The chapter close validates its proposed delta against the plan's projection
instead of re-deriving load-bearing state from prose. The plan owns lifecycle,
belief, and affect; the close owns physical detail.

**Deliverables:**
- `validate_close(plan, chapter, proposed_delta) → ValidatedDelta`
  - Plan's projected state for covered lanes is **authoritative**
  - Prose delta for uncovered lanes (location, inventory, relationships) is
    **validated**: a protected-character death is rejected
  - Merged state = plan projection + validated prose delta
- `apply_chapter_close` amended: overlays plan projection onto the close's
  physical delta
- Protected set (`goals`) fed to director AND final cut, not just realize

**Acceptance:** A chapter close that contradicts the plan's `eff_world` or
`eff_belief` is rejected. A protected-character prose death is caught before
commit. The forward-carry for lifecycle/belief/affect comes from the plan, not
prose.

---

## 4. What each phase retires

| v2 concern | Retired by | Phase |
|------------|-----------|-------|
| Outline gates as independent checks | Plan grammar (Rules 2–6) | P1 + P3 |
| `exclusion_set` as additive seam | Plan-derived outline excludes by construction | P3 |
| Close re-derives lifecycle from prose | Plan projection is authoritative | P4 |
| Close re-derives belief from prose | Plan projection is authoritative | P4 |
| Protected-character prose death accepted then logged | Protected-character prose death rejected at close | P4 |
| `character_lifecycle` parsed from prose | `project_chapter_state` projected from plan | P2 + P4 |
| Two parallel truth sources (plan + ledger) | One truth source per lane: plan for plot, ledger for physical detail | P4 |

---

## 5. What stays prose-derived (out of scope)

The plan vocabulary is deliberately too coarse for:

- **Physical micro-state** (rope config, who is above/below, climb phase) — no
  typed lane in the plan; stays in the prose-derived ledger
- **Relationships** (the FR-513–518 emotional/alliance memory) — the plan has no
  relationship lane; stays in the ledger
- **Location detail** — `at(Character, Place)` is a coarse predicate; the ledger's
  `location` field carries prose-level detail

These lanes remain prose-derived. The plan owns the **plot-load-bearing** lanes
(lifecycle, belief, affect); the ledger owns the **prose-detail** lanes. They
run in parallel but the plan's lanes are authoritative — a contradiction is
resolved in favor of the plan.

---

## 6. The acceptance litmus (from v3-rewrite-guidance §2)

> Two chapters' prose are generable without one reading the other's prose.

With P4 complete, the lifecycle/belief/affect forward-carry is plan-projected,
not prose-derived. Two chapters that share no causal link in the plan can
generate concurrently — the plan provides the state each needs. The prose-derived
physical lane still serializes chapters, but the plot-load-bearing state does not
depend on prior prose.

Full parallel-safety requires the physical lane to also be plan-projected
(expanding `at`/`holds` usage) — a future phase, not in scope here.
