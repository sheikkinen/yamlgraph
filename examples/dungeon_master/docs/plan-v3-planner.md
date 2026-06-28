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

| Sort | What it is | As-built |
|------|-----------|----------|
| `Character` | A named agent who can act, observe, believe, feel | `CharacterId = str` |
| `Place` | A named location | *(aspirational — untyped `str` in args)* |
| `Object` | A named thing that can be held or placed | *(aspirational — untyped `str` in args)* |
| `Fact` | A named atomic proposition | *(aspirational — untyped `str` in args)* |

`Place`, `Object`, and `Fact` are destination-language sorts. In the current build all
entity arguments are untyped strings; grounding (Rule 1) treats every argument as an
entity reference regardless of sort. Introducing typed sorts is a future phase, not
required by any FR in this plan.

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

**Actions** (closed alphabet, derived from Propp's 31 functions):

Propp's 31 functions (Propp 1928, *Morphology of the Folktale*; cross-referenced
against Grokipedia primary-source summary) organize into **five narrative
spheres**: preparatory (β–θ, functions 1–7), complication (A–B, 8–10), donor
(C–G, 11–16), heroic (H–J, 17–19), and resolution (K–W, 20–31). Our action
alphabet selects from these spheres, not arbitrarily — each kind maps to one or
more Propp functions, and the selection is driven by what the DM's premise genres
require.

| Action | Propp # | Propp designation | Sphere | Signature | Meaning |
|--------|---------|-------------------|--------|-----------|---------|
| `villainy` | 8 | A — Villainy | Complication | `(subject, target)` | Antagonistic act: harm, abduction, theft |
| `lack` | 9 | a — Lack | Complication | `(subject, object)` | Discovery that something is missing or needed |
| `departure` | 12 | ↑ — Departure | Donor | `(subject, from, to)` | Hero leaves home / current location |
| `donor_test` | 13–14 | D/E — Donor test / Hero's reaction | Donor | `(subject, donor)` | Hero is tested and responds |
| `provision` | 15 | F — Receipt of magical agent | Donor | `(subject, object)` | Hero acquires aid, tool, or knowledge |
| `struggle` | 17 | H — Struggle | Heroic | `(subject, target)` | Direct conflict: combat, contest, debate |
| `victory` | 18 | I — Victory | Heroic | `(subject, target)` | Conflict resolved: defeat, banishment, submission |
| `liquidation` | 20 | K — Liquidation of lack | Resolution | `(subject, target)` | Initial misfortune or lack is resolved |
| `return` | 21 | ↓ — Return | Resolution | `(subject, to)` | Hero returns home or to community |
| `pursuit` | 22 | Pr — Pursuit | Resolution | `(subject, target)` | Chase, hunt, tracking |
| `rescue` | 23 | Rs — Rescue | Resolution | `(subject, target)` | Escape from pursuit or captivity |
| `recognition` | 28 | Q — Recognition | Resolution | `(subject, observers)` | Hero acknowledged; truth disclosed |
| `exposure` | 29 | Ex — Exposure | Resolution | `(subject, observers)` | False hero or villain unmasked |
| `punishment` | 30 | U — Punishment | Resolution | `(subject, target)` | Villain faces consequences |
| `reconciliation` | 31 | W — Wedding | Resolution | `(subject, target)` | Union, reward, relational resolution |
| `death` | — | *(no Propp equivalent)* | — | `(subject)` | Permanent removal (world-truth) |

**16 kinds** (up from 10). Changes from previous version:

- **Added 6 kinds:** `lack` (Propp 9), `donor_test` (Propp 13–14), `provision`
  (Propp 15), `liquidation` (Propp 20), `exposure` (Propp 29), `punishment`
  (Propp 30). Each addresses a genre gap identified in the §7 reflection.
- **Split `reveal` into `recognition` + `exposure`:** Propp distinguishes hero-
  acknowledged (28/Q) from villain-unmasked (29/Ex). The distinction matters for
  detective/thriller (the detective is *recognized* as right; the culprit is
  *exposed*). The previous `reveal` conflated both.
- **`death` has no Propp equivalent.** In Propp, death is a *consequence* of
  villainy or punishment, not a standalone function. We keep it because the DM
  needs an explicit lifecycle terminator for world-truth (Rule 3 — monotonic
  lifecycle). It is the only kind outside the Propp inventory.

**Propp spheres we deliberately omit:**

| Omitted sphere | Propp functions | Why omitted |
|---------------|-----------------|-------------|
| Preparatory (1–7) | Absentation, interdiction, violation, reconnaissance, delivery, trickery, complicity | These are the villain's *preparation* — in the DM, the LLM realizes these as prose within a `villainy` beat's interior. The plan does not schedule villain prep as separate structural beats; it schedules the villainy itself. If a premise requires the preparation arc to be structurally load-bearing (e.g., a heist where the "complicity" must be tracked), the kind can be added later. |
| Mediation (10) / Counteraction (11) | Hero learns of problem; hero decides to act | These are the hero's *reaction* to complication — realized as prose within the beat following villainy. The `motivation` field on the next function carries the same structural information ("this function exists because the hero decided to act"). |
| Guidance (16) / Translocation | Hero transported to location | Subsumed by `departure` (the structural fact is "hero moves"); the distinction between self-directed and guided travel is a prose-level detail carried by `gloss`. |
| Branding (19) / Transfiguration (30) | Hero marked; hero transformed | These are physical-state changes on the hero — handled by the world-fluent lane (`holds(hero, mark)`, `rel(hero, appearance, changed)`) rather than by a dedicated function kind. |
| Difficult task (26) / Solution (27) | Trial proposed; trial completed | Subsumed by `donor_test` + `victory` (a trial *is* a test followed by success). If the distinction matters (the task-giver is not a donor), it can be added. |
| Unfounded claims (25) | False hero claims credit | Rare in DM premise genres. Can be added if a premise requires a false-hero arc. |

**Genre coverage with 16 kinds:**

| Genre | Covered functions | Coverage |
|-------|------------------|----------|
| Clan saga / romance | villainy, reconciliation, return, recognition | ~90% |
| Detective thriller | villainy, pursuit, exposure, recognition, punishment, lack | ~70% |
| Quest / adventure | departure, donor_test, provision, struggle, victory, return | ~80% |
| Horror / survival | villainy, pursuit, struggle, death | ~65% |
| Heist / caper | villainy, departure, struggle, victory, rescue, exposure | ~70% |

The 4-kind → 16-kind expansion roughly triples coverage for non-saga genres.
The remaining gaps are prose-level (realized within beats via `gloss`) rather than
structural (needing dedicated function kinds).

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

| Part | What | Type | As-built field(s) |
|------|------|------|-------------------|
| `I` | Initial state | Set of ground predicates (world-truth + beliefs) | `initial_world: list[Fluent]`, `initial_belief: list[Belief]` |
| `A` | Agents | Set of Characters | `agents: list[CharacterId]` |
| `G` | Goals | Predicates that must hold at the finale | `goals: list[Fluent]` |
| `F` | Functions | Sequence of actions with typed pre/eff/affect | `functions: list[Function]` |
| `O` | Ordering | Partial order over F (DAG edges) | `order: list[tuple[str, str]]` |

Each **function** is a production rule:

```
function F:
    action:   symbol from the action alphabet     → kind: FunctionKind
    args:     ground terms matching the signature  → subject, target, observers
    chapter:  int (scheduling ordinal)             → chapter: int
    grain:    book | chapter | turn                → grain: Grain

    gloss:    one-sentence natural-language summary → gloss: str
    motivation: whose goal this serves             → motivation: Motivation | None
    threatens:  whose goal this thwarts            → threatens: Motivation | None
    enables:  functions this causally enables      → enables: list[str]

    pre:      set of predicates that must hold     → pre_world: list[Fluent], pre_belief: list[Belief]
    eff:      set of predicates F makes true       → eff_world: list[Fluent], eff_belief: list[Belief]
    affect:   set of (open|close, token) pairs     → eff_affect: list[AffectDelta]
```

The four fields added by the spine paper test (2026-06-23):

- **`gloss`** carries the *story* (physical setting, mechanism, social texture) that
  the structural fields cannot encode. The plan factorizes into a verifiable
  structural layer (plot) and a weakly-verifiable prose layer (story). See paper
  test §11–§13 for the fabula/syuzhet analysis.
- **`motivation`/`threatens`** encode intentionality — *why* a function exists and
  *whose goal* it opposes. Enables unmotivated-action detection (the only "strong
  gain" the spine adds over the DM schema). `Motivation = {agent: CharacterId,
  goal: str}`. Null for non-intentional subjects (e.g., Flood).
- **`enables`** replaces the flat `order` chain with per-function causal links. The
  paper test found the LLM's linear F5→F6 was a false dependency — they are
  actually independent threads joined at F7. The `O` partial order is derivable
  from the transitive closure of `enables` edges.

The formal notation uses compact names (`I`, `pre`, `eff`); the as-built schema splits
world and belief into separate typed lists. The mapping is shown above so a reader does
not mistake the formal language for a proposed schema change.

### 1c. Grammar (well-formedness rules)

A plan is well-formed iff all seven rules hold:

**Rule 1 — Grounding.** Every term in every predicate in `I`, `G`, `F.pre`,
`F.eff` refers to a named entity in `A` or introduced in `I` or `F`.

**Rule 2 — Causal closure.** For every predicate `p` in any `F.pre`: either
`p ∈ I`, or there exists an earlier function `F'` (per `O`) where `p ∈ F'.eff`.
No dangling preconditions. The pure check (`_check_causal_antecedent`) is
existence-based: it verifies a producer exists, not that the value still holds at
the point of use. Temporal validity (a precondition whose producer is later negated
by an intermediate function) is a solver concern — permanently owned by
`unified-planning`, not by the pure grammar checks.

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

**Rule 7 — Acyclicity.** `O` is a DAG. (When `O` is derived from `enables`
edges, this means the `enables` graph is acyclic.)

**Rule 8 — Motivated action.** Every function with an intentional subject
(a `Character` in `A`) must have a non-null `motivation`. Functions with
non-intentional subjects (natural events, e.g., `Flood`) may have
`motivation = null`. The paper test found this is the highest-value structural
check the spine adds — the only defect class the DM schema cannot detect at all.

---

## 2. Current state vs complete language

| Artifact | Current (M0–M4b) | Complete language | Gap | Paper test evidence |
|----------|-------------------|-------------------|-----|---------------------|
| Sorts | `CharacterId = str`; no typed Place/Object | Typed sorts | Sorts are untyped strings | LLM used `Flood` as agent — sort typing would help but is not urgent |
| Actions | 4 kinds: villainy, reveal, reconciliation, return | 16 kinds (Propp cross-ref) | 12 missing | LLM stayed within 4 kinds for saga genre (PT1 §9) — but **genre-dependent**: saga ~90% with 16, thriller ~70% (§7 reflection, §1a Propp cross-ref) |
| Affects | 2 kinds: loss, guilt | 5 kinds | 3 missing | LLM did not attempt `betrayal` despite synopsis describing it — compressed to `guilt` (PT2 §10c) |
| Predicates | 5 `WorldPred` members + `Belief` model (epistemic); only `alive` exercised in fixtures/projections | All 5 `WorldPred` + `Belief` actively exercised | `at`/`holds`/`faction`/`rel` defined but dormant in fixtures; `believes` is already active via `Belief`/`eff_belief` | **LLM used `rel`, `faction`, `holds` extensively** — not dormant in practice (PT1 §7b) |
| Belief typing | `Belief.held: bool` | `held: bool \| str` | `held` rejects string values | **Total-plan-drop bug** — LLM naturally wrote `held: "enemy"`, parser rejected it. Zero-cost fix (PT1 §7c, PT2 H4) |
| `gloss` | Not present | `gloss: str` per function | Missing | **Load-bearing for story recovery** — all 7 narrative statements require it (PT2 §9). Weakly verifiable only (PT2 §11b) |
| `motivation`/`threatens` | Not present | `Motivation` per function | Missing | **Highest-value structural addition** — enables unmotivated-action check, contributes to 4/7 narrative statements (PT2 §10e, §9) |
| `enables` | Flat `order` chain | Per-function causal links | Missing | Reveals false dependencies (F5↔F6 independent, not sequential). Primary value is parallel-safety (PT2 §8, H3) |
| Rule 1 | Not checked | `_check_grounding` | Missing | |
| Rule 2 | `_check_causal_antecedent` (existence only) | Existence (pure check) | Partial — temporal validity permanently deferred to `unified-planning` solver | |
| Rule 3 | `_check_monotonic_lifecycle` | Complete | — | |
| Rule 4 | `_check_belief_grounding` | Complete | — | |
| Rule 5 | `_check_affect_closure` | Complete | — | |
| Rule 6 | Not checked (deferred to UP solver) | `_check_goal_reachability` | Missing | |
| Rule 7 | `ordered_functions` raises `ValueError` on cycle (implicit in topological sort) | Complete | — | |
| Rule 8 | Not present | `_check_motivated_action` | Missing | **Only "strong gain"** over DM schema — no other check adds new detection power (PT2 §10e) |
| Plan → outline | Independent (plan and outline are co-authored separately) | Outline derived from plan | Gap | |
| Forward-carry | Prose-derived at chapter close | Plan-projected | Gap | |
| Close validation | Close re-derives state from prose | Close validates against plan projection | Gap | |

> **PT1** = paper-test-10030-bc-synopsis-to-plan.md (LLM-authored plan via DM schema).
> **PT2** = paper-test-10030-bc-spine-encoding.md (hand-encoded spine plan).

---

## 3. Build sequence (phased FRs)

Each phase is a separately-judgeable FR. Each phase is testable in isolation and
does not require later phases to deliver value. The strangler-fig posture
continues: `--no-plot-plan` reverts to full v2.

### Phase 0: Zero-cost schema fixes (FR-564)

Immediate fixes validated by the paper tests that require no architectural
changes. Ship independently before Phase 1.

**Deliverables:**
- `Belief.held: bool | str` — accept typed belief values. The LLM naturally
  writes `held: "enemy"` for relationship beliefs; the current `bool`-only
  schema causes a total-plan-drop at the parse boundary (PT1 §7c). Zero-cost:
  widen the type, update `_is_grounded_belief` to check pred membership regardless
  of held type.
- `Function.gloss: str | None` — optional prose annotation per function. Not
  validated by the grammar (weakly verifiable at best), but load-bearing for
  downstream beat generation: the beat-writer needs to know *what happens*, not
  just *what kind* of thing happens (PT2 §11b Q2).
- `Function.motivation: Motivation | None` and `Function.threatens: Motivation | None`
  — intentionality fields. `Motivation = {agent: CharacterId, goal: str}`.
- `Function.enables: list[str]` — per-function causal links replacing flat `order`.
  The `order` field becomes derivable from the transitive closure of `enables`.
- `_check_motivated_action(plan)` — Rule 8. Flag functions with intentional
  subjects but null motivation.
- Fixtures: 10030-BC plan as a fixture exercising `rel`, `faction`, `holds`,
  typed beliefs, gloss, motivation, enables.

**Acceptance:** The 10030-BC LLM-authored plan (PT1 plan-output.json) parses
without coercion. The spine-encoded plan (PT2 §8) validates with all checks
including Rule 8.

### Phase 1: Complete the grammar (FR-566)

Add the two missing well-formedness checks (Rules 1, 6) and expand the vocabulary
to the destination alphabets. With this, all eight rules are complete and
`validate_plan` is a full grammar check — `unified-planning` becomes truly
optional.

**Deliverables:**
- `_check_grounding(plan)` — Rule 1
- `_check_goal_reachability(plan)` — Rule 6
- `FunctionKind` expanded to 16 kinds *(Propp cross-referenced — see §1a; required
  for genre diversity: saga ~90%, thriller ~70%, quest ~80% coverage)*
- `AffectKind` expanded to 5 kinds *(the LLM compressed betrayal into guilt for
  the saga; richer kinds are needed for precise emotional tracking across genres)*
- Fixture variants exercising the new kinds and checks, **including at least one
  non-saga premise** (e.g., detective thriller) to validate genre coverage
- Prompt updated with the full alphabets

**Acceptance:** `validate_plan` implements all 8 rules. Every rule has a fixture
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
- Outline gates (`reversal_pack`, `unplayable_beat`, `composition`) remain as
  validation but failure rate should decrease — plan-derived beats are structured,
  reducing (not eliminating) gate violations. Prose-pattern gates like
  `unplayable_beat` cannot be retired by plan rules alone
- Integration: `generate_story` calls `derive_outline` instead of
  `outline_chapters` when a plan is attached

**Acceptance:** The outline's structural fields (beats, cast, state contracts) are
plan-derived. The outline gates remain as validation; plan-derived structure
reduces but does not eliminate gate failures.

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
| Total-plan-drop on typed beliefs | `held: bool \| str` accepts LLM's natural output | **P0** |
| Parse boundary drops entire plan silently | Per-function validation + typed beliefs | **P0** |
| Unmotivated actions undetectable | `_check_motivated_action` (Rule 8) | **P0** |
| Beat-writer has no scene context | `gloss` field carries the *what* alongside the *kind* | **P0** |
| Flat order imposes false dependencies | `enables` causal links reveal true partial order | **P0** |
| Outline gates as independent checks | Plan grammar reduces gate failure rate; gates remain as validation (prose-pattern gates like `unplayable_beat` cannot be retired by plan rules alone) | P1 + P3 |
| `exclusion_set` scope reduced | Plan-derived outline excludes dead characters at outline time; `exclusion_set` remains for mid-plan deaths (characters alive at outline but dead by chapter N) | P3 |
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
generate concurrently *for plot-load-bearing state* — the plan provides the
lifecycle, belief, and affect each chapter needs. The prose-derived physical lane
(location, inventory, relationships) still serializes chapters, so full
parallelism is not yet achieved. The litmus is satisfied for the plan-owned
lanes; the physical lane remains a serialization boundary.

Full parallel-safety requires the physical lane to also be plan-projected
(expanding `at`/`holds` usage) — a future phase, not in scope here.

---

## 7. Paper test findings (2026-06-23)

Two paper tests against the 10030-BC premise (Hilde/Gunnar flood story) validated
the spine decision and reshaped the build sequence. Full results in the companion
documents; key findings summarized here.

### PT1: Synopsis → DM schema (LLM-authored plan)

[`paper-test-10030-bc-synopsis-to-plan.md`](paper-test-10030-bc-synopsis-to-plan.md)

Ran the 10030-BC synopsis through the LLM planner using the M0–M4b DM schema.
The LLM authored a well-structured 7-function plan. Findings:

1. **The LLM stayed within the 4-kind action alphabet.** It compressed an
   8-chapter story into 3 of 4 kinds (villainy, reconciliation, return — no
   reveal). Vocabulary expansion to 10 kinds is destination, not prerequisite.
2. **The LLM used dormant predicates extensively** — `rel`, `faction`, `holds`
   appeared naturally and correctly. These predicates need fixture coverage.
3. **`Belief.held: bool` caused a total-plan-drop.** The LLM wrote
   `held: "enemy"` and `held: "lovers"` for relationship beliefs. Pydantic
   rejected the plan; `parse_plot_plan` returned an empty plan silently.
4. **The plan's vocabulary is completely insufficient for narrative recovery.**
   A reader of the plan JSON alone cannot reconstruct what happens in the story.
   The formal language encodes *types of events*, not *specific events*. Every
   sentence of the plot narration required the synopsis as external context (§10).

### PT2: Spine encoding (hand-encoded plan)

[`paper-test-10030-bc-spine-encoding.md`](paper-test-10030-bc-spine-encoding.md)

Re-encoded the same 7 functions using the full spine vocabulary (gloss,
motivation, threatens, enables, typed beliefs, roles). Findings:

1. **Narrative recoverability: 7/7 with gloss, ~3/7 without.** The `gloss` field
   is the only field that carries all 7 statements. Motivation contributes to
   4/7; no other non-gloss field exceeds 2/7.
2. **The plan factorizes into two layers:**
   - **Structural layer** (kind, motivation, threatens, enables, pre/eff, affect):
     closed vocabulary, mechanically verifiable, carries the **plot** (fabula).
   - **Prose layer** (gloss): open vocabulary, weakly verifiable, carries the
     **story** (syuzhet).
3. **Intentionality is the highest-value structural addition.** Unmotivated-action
   detection (Rule 8) is the only check the spine adds that the DM schema cannot
   perform. Motivation also contributes the most narrative information of any
   non-gloss field.
4. **Causal links (`enables`) revealed a false dependency.** The LLM's linear
   F5→F6 chain was wrong — they are independent threads (Svala's challenge and
   Arnulf's return) joined at F7 (feud resolution). Partial-order value confirmed
   even for a nominally linear story.
5. **Typed beliefs are a zero-cost fix.** `held: bool | str` eliminates the
   parse-boundary failure with no information loss.
6. **The gloss reopens the recognition problem** — but confines it to one field
   per function, where it is more tractable than whole-document recognition. The
   gloss is weakly verifiable (entity mentions checkable) but not strongly
   verifiable (scene content unconstrained).

### Reflection: vocabulary expansion priority is genre-dependent

The initial assessment — "vocabulary expansion is nice-to-have, not urgent" — was
based on a single paper test against a single genre. **The assessment is wrong as
a general claim.** It holds for saga/romance premises; it fails catastrophically
for other genres.

The 10030-BC story is a **clan saga**: feud → truce → love → peace. This genre
maps naturally onto reconciliation (3 of 7 functions), villainy (3), and return
(1). The 4-kind alphabet covers the genre because the genre *is* reconciliation.
The LLM "staying within the alphabet" is not evidence of sufficiency — it is
evidence that **the LLM is obedient**. It compressed rather than pushed back. The
compression was tolerable for a saga; it would be destructive for other genres.

**Genre coverage analysis of the current 4-kind alphabet:**

| Genre | Dominant function kinds needed | Current 4 covers |
|-------|-------------------------------|-------------------|
| Clan saga / romance | villainy, reconciliation, return | ~85% |
| Detective thriller | death, departure, pursuit, struggle, victory, reveal | ~15% |
| Quest / adventure | departure, pursuit, struggle, victory, rescue, return | ~17% |
| Horror / survival | villainy, pursuit, struggle, death | ~25% |
| Heist / caper | departure, villainy, struggle, victory, rescue | ~20% |

For a **detective thriller**, the current alphabet forces:
- Murder → `villainy` (ok)
- Detective departs for crime scene → `villainy`? (wrong)
- Following clues / tracking suspect → `villainy`? (meaningless)
- Confrontation with suspect → `villainy`? (indistinguishable from murder)
- Solving the case → `reconciliation`? (semantically wrong)
- Saving the victim → `return`? (wrong)

The structural layer collapses: every beat is "villainy" with only the `gloss`
distinguishing them. The `kind` field carries no information. The grammar checks
that depend on `kind` (e.g., action-specific precondition patterns) become
vacuous. **The plan degenerates into glosses with metadata — the recognition
problem returns through the front door.**

**Corrected assessment:** Vocabulary expansion to 10 kinds is **required for
genre diversity**. It is low-priority only if the DM is permanently restricted
to saga/romance premises. Since the system is designed for arbitrary premise
genres, the expansion is **Phase 1 priority**, not a nice-to-have.

**The error pattern to name:** generalizing from a single favorable data point.
The paper test tested one genre where the alphabet happened to fit. Drawing a
priority conclusion from that is survivorship bias — the genres where the
alphabet fails were never tested.

### Impact on build sequence

The paper tests motivate a **Phase 0** (FR-564) before the grammar-completion
work. Phase 0 ships the zero-cost schema fixes (typed beliefs, gloss, motivation,
threatens, enables, Rule 8) that directly address observed failures. Phase 1
(FR-566) completes the grammar with the remaining rules and vocabulary expansion.
The vocabulary expansion is **required for genre diversity** — the initial
"nice-to-have" assessment was based on a single genre and does not generalize.
