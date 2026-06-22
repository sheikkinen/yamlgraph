# Feature Request: FR-566 DM v3 — Stand-alone planner (synopsis → projected plan → generation)

**Priority:** HIGH
**Type:** Feature (architectural milestone)
**Status:** Draft (2026-06-22)
**Effort:** 3–5 days (phased)
**Requested:** 2026-06-22
**Depends on:** FR-559–565 (the M0–M4b arc, all Enforced)

## Problem statement

The research (`plan-generative-plot-model.md`, both research passes) concluded:

> Author the plot as a small, typed, machine-checkable specification *before*
> any prose is written, prove it logically consistent, then use the language
> model only to *render* a plan that is already guaranteed correct.

The M0–M4b milestones built the typed vocabulary, the validator, the projections,
and two additive runtime seams (exclusion + realize). But the generation pipeline
still **reconstructs** the forward-carry from prose:

```
synopsis → outline → [PlotPlan authored, attached]
                          ↓
    per chapter:  turn engine generates prose
                          ↓
                  chapter_close LLM reads prose → derives world_state delta
                          ↓
                  next chapter inherits the prose-derived state
```

The plan steers generation (via exclusion and beat instruction) but does **not
own the forward-carry**. The chapter close re-derives `world_state`,
`seam_packet`, and `chapter_memory` from the generated prose — exactly the
inverse problem the research said to stop solving. The `PlotPlan`'s `eff_world`
and `eff_belief` effects are validated at attach time but **never projected into
the chapter-close state**. Two parallel truth sources run simultaneously:

1. The `PlotPlan` (authored, validated, static) — knows "Clan believes Arnulf dead
   after Ch1"
2. The `world_state` ledger (prose-derived, per-chapter) — knows "Hilde is at the
   gorge with a hand-axe"

Neither reads the other. The plan cannot prevent a chapter close from
contradicting an authored effect, and the ledger carries no typed belief lane.

**The v3 rewrite guidance (§2) names this precisely:** "the ledger as the
direction of truth, not prose as the direction of truth." The acceptance litmus:
*two chapters' prose are generable without one reading the other's prose*. The
current pipeline fails this litmus — each chapter reads the prior chapter's
**prose-derived** `world_state`.

## Proposed solution: the stand-alone planner

A stand-alone planner that takes a synopsis and produces a **complete,
chapter-indexed projection** the generation loop consumes as the sole source of
truth for load-bearing plot state. The planner is a **pre-generation pass**, not
a strangler-fig additive seam — it replaces the prose-derived forward-carry for
the plan-covered lanes.

### Phase 1: Expand the plan to cover the outline

The current pipeline: `synopsis → outline_chapters (LLM) → expand_chapters`.
The plan is authored **after** the outline, from the synopsis alone. The outline
and the plan are independent — the plan's chapter numbers may not match the
outline's chapter order, and the plan knows nothing about beats, cast, or
entry/exit state.

**Change:** The planner authors the plan and the outline together, or the plan
is authored first and the outline is **derived from it**.

Option A — **Plan first, outline derived:**

```
synopsis → author_plot_plan (LLM → validate → repair)
               ↓
           PlotPlan (validated)
               ↓
           derive_outline(plan, synopsis)  ← NEW
               ↓
           chapters: [{title, summary, beats, cast, entry_state, exit_state}]
```

The outline is a **projection** of the plan: each chapter's beats are the plan's
`Function`s at that chapter, rendered as prose beats. The chapter cast is
`chapter_cast(plan, ch)`. Entry/exit state is projected from `eff_world` /
`eff_belief` cumulative effects. The outline gates (reversal_pack, unplayable
beat, composition) are checked against the projected outline — but they should
already hold by construction (the plan's validation implies them).

Option B — **Plan and outline co-authored:**

```
synopsis → author_plan_and_outline (LLM → validate → repair)
               ↓
           {plan: PlotPlan, outline: [{title, summary, beats, ...}]}
```

One LLM call produces both. The validator checks the plan AND the outline gates
in one pass. Simpler, but the LLM has a harder job.

**Recommendation: Option A.** The plan is the authority; the outline is its
readable projection. This keeps the validator pure (it checks the plan, not
prose-form beats) and lets the outline gates collapse into plan validity checks
as the research predicted.

### Phase 2: Project the forward-carry from the plan

The chapter close currently re-derives `world_state` from prose. With a plan,
the load-bearing lanes (lifecycle, belief, affect) are **projected**, not
derived:

```python
def project_chapter_state(plan: PlotPlan, chapter: int) -> dict:
    """The cumulative world-truth and belief state after chapter `chapter`.

    Walks ordered_functions through `chapter`, accumulating eff_world and
    eff_belief. Returns a typed state dict the next chapter inherits.
    """
```

What this replaces and what it keeps:

| Lane | Current (prose-derived) | Projected (plan-owned) |
|------|------------------------|----------------------|
| `alive` lifecycle | `character_lifecycle` in seam_packet, parsed from prose | `eff_world` cumulative: `alive(c)` fluents through chapter N |
| Belief (who knows what) | **not tracked** | `eff_belief` cumulative: `believes(obs, alive(c))` through chapter N |
| Affect (emotional arcs) | **not tracked** | `eff_affect` cumulative: open/close units through chapter N |
| Protected set | `goals` read at realize time | `protected_set(plan)` — fed to director AND final cut |
| Exclusion set | `exclusion_set` in chapter_open | Unchanged (already projected from plan) |
| Physical state (location, inventory) | Prose-derived `world_state` ledger | **Still prose-derived** — the plan's `WorldPred` (`at`, `holds`) could carry this, but the vocabulary is too coarse for the detail the ledger tracks |
| Relationships | Prose-derived ledger (FR-513–518) | **Still prose-derived** — the plan has no relationship lane |

**The key insight:** the plan owns lifecycle, belief, and affect. The ledger owns
physical detail and relationships. They run in parallel, but the plan's lanes are
**authoritative** — a chapter close cannot contradict them.

### Phase 3: The chapter close validates against the plan, not vice versa

```
chapter N plays → prose generated
    ↓
chapter_close LLM → proposes world_state delta (physical detail only)
    ↓
validate_close(plan, chapter, proposed_delta):
    - plan's eff_world for chapter N: is the proposed delta CONSISTENT?
    - a prose death of a protected character → REJECT (regenerate the prose)
    - lifecycle state from the plan is ADDED to the delta (not derived from it)
    ↓
commit: merged state = plan projection + validated prose delta
```

This is the `JUDGE → AMEND → COMMIT` pattern from `v3-rewrite-guidance.md §8`.

### Phase 4: Parallel-safety (the acceptance litmus)

With the plan owning the forward-carry for lifecycle/belief/affect, two chapters
whose plan-projected states don't overlap (no shared causal link) can in
principle generate concurrently. The prose-derived physical-detail lane still
serializes chapters, but the load-bearing plot state does not depend on prior
prose.

## Existing assets

All existing, tested, enforced:

| Asset | Location | Reuse |
|-------|----------|-------|
| `PlotPlan` schema | `api/plot/schema.py` | Unchanged |
| `validate_plan` (4 checks) | `api/plot/validate.py` | Unchanged |
| `ordered_functions` | `api/plot/project.py` | Used by the projector |
| `exclusion_set` / `belief_at` / `chapter_cast` / `protected_set` | `api/plot/project.py` | The projections already exist |
| `beat_instruction` / `merge_beat_instruction` | `api/plot/realize.py` | Unchanged |
| `parse_plot_plan` | `api/plot/author.py` | Unchanged |
| `write_plot_plan` / `attached_plot_plan` | `api/chapter_nav.py` | Unchanged |
| `author_plot_plan` | `api/doc_ops.py` | Extended to call the outline derivation |
| `plot_plan.yaml` graph | `plot_plan.yaml` | Unchanged |
| `author_plot_plan.yaml` prompt | `prompts/author_plot_plan.yaml` | May need vocabulary expansion |
| `floodmark.py` fixtures (9 variants) | `api/plot/floodmark.py` | Regression corpus |
| `outline_chapters` + 3 outline gates | `outline_ops.py` | Replaced by plan-derived outline |
| `chapter_close` + ledger apply | `chapter_ops.py` | Amended: plan projection added to close |
| `world_state.py` ledger | `api/world_state.py` | Kept for physical detail; plan projection overlaid |

## What the plan vocabulary needs to grow

The current 4-kind function alphabet (`villainy`, `reveal`, `reconciliation`,
`return`) and 5-predicate world vocabulary (`alive`, `at`, `faction`, `rel`,
`holds`) were sufficient for the floodmark arc. A stand-alone planner covering
real premises needs:

**Function kinds:** `departure`, `struggle`, `victory`, `pursuit`, `rescue`,
`death` (the design doc §2 listed these as the destination alphabet).

**World predicates:** the existing set covers identity; physical detail (`at`,
`holds`) is defined but unused. The planner should actively use `at` and `holds`
to project location and inventory, reducing the prose-derived physical lane.

**Affect kinds:** `betrayal`, `retaliation`, `hidden_blessing` (from the design
doc — Lehnert Plot Units).

**Belief observers:** currently free-form strings. May need a `"narrator"` /
`"reader"` observer for dramatic irony.

## Build sequence

| Phase | Deliverable | Acceptance test |
|-------|-------------|-----------------|
| P1 | `project.project_chapter_state(plan, chapter)` — cumulative world+belief+affect through chapter N | `project_chapter_state(floodmark, 3)` returns Arnulf alive (world), Clan believes dead (belief), loss(Hilde) open (affect) |
| P2 | `outline_from_plan(plan, synopsis)` — derive outline from validated plan | Outline beats match plan functions; outline gates pass by construction |
| P3 | `validate_close(plan, chapter, delta)` — chapter close validates against plan projection | Protected-character prose death rejected; lifecycle contradiction caught |
| P4 | Generation loop wired: plan → projected outline → play → validated close → projected forward-carry | End-to-end: a floodmark-premise book where the forward-carry is plan-projected, not prose-derived |

## Scope guards

- **Not a full IPOCL solver.** The planner is an LLM-authored, deterministically-
  validated plan. The `unified-planning` solver (`up_model.py`) remains an optional
  cross-check, not the authoring engine.
- **Not a replacement for the prose engine.** The turn engine stays; the planner
  feeds it. The LLM still writes prose; it just cannot author plot.
- **Not a typed lane for physical micro-state.** Location and inventory projection
  via `at`/`holds` is a stretch goal. The prose-derived ledger carries physical
  detail until the plan vocabulary proves sufficient.
- **The strangler-fig posture continues.** `--no-plot-plan` still works. The
  plan-projected forward-carry is the default when a plan is attached; the prose-
  derived forward-carry is the fallback when absent.

## The question the research answered, and the gap that remains

The research asked: *what is the right representation?* Answer: a closed
generative vocabulary with typed belief, causal, and affect lanes, validated
before prose.

The M0–M4b arc built that representation. This FR asks: *now that we have the
right representation, does it own the forward-carry?* The research said yes
(`v3-rewrite-guidance.md §2`: "project, not reconstruct"). The build said not
yet. This FR closes the gap.
