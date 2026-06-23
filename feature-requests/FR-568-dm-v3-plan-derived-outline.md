# Feature Request: FR-568 DM v3 — plan-derived outline

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed (2026-06-22)
**Effort:** 5–7 days
**Requested:** 2026-06-22
**Plan:** [`plan-v3-planner.md`](../examples/dungeon_master/docs/plan-v3-planner.md) Phase 3

## Summary

The outline becomes a projection of the plan, not an independent LLM generation. The
plan's functions at each chapter become the chapter's beats. Cast, entry/exit state
are projected from the plan. The LLM authors only `title` and `summary` per chapter
(prose, not structure).

## Value Statement

DM maintainers get `derive_outline(plan, synopsis) → list[ChapterOutline]` — a
function that derives the structural fields of the chapter outline (beats, cast,
entry/exit state) from the plan. The outline gates (`reversal_pack`, `unplayable_beat`,
`composition`) remain as validation but their failure rate decreases because
plan-derived beats are structured rather than LLM-improvised. The LLM's role shrinks
from "design the chapter structure" to "name and summarize each chapter."

## Problem

Today the plan and the outline are co-authored independently from the same synopsis.
The plan's functions have `chapter` ordinals that may or may not align with the
outline's actual chapter structure. The outline's beats are LLM-authored, not
plan-derived. The outline gates check structural properties that the plan's
well-formedness rules already guarantee — but the two artifacts don't talk to each
other.

This means:
- Beats can contradict the plan (the plan says "reveal at ch3" but the outline's ch3
  beats don't include a reveal).
- Cast can be inconsistent (the plan excludes a dead character but the outline includes
  them in the cast).
- The outline gates can fail even when the plan is well-formed (because the outline
  was independently authored).

## Proposed Solution

### 1. `derive_outline(plan, synopsis) → list[ChapterOutline]`

A pure projection function:
- `beats` = plan functions at chapter, rendered as prose directives
- `cast` = `chapter_cast(plan, ch)` (characters active in the chapter's functions)
- `entry_state` = `project_chapter_state(plan, ch - 1)` formatted as prose
- `exit_state` = `project_chapter_state(plan, ch)` formatted as prose

### 2. LLM role reduction

The LLM authors only `title` and `summary` per chapter — prose metadata, not
structural decisions. The chapter count, beat assignment, cast, and state contracts
are plan-derived.

### 3. Outline gate reduction (not retirement)

The outline gates (`reversal_pack`, `unplayable_beat`, `composition`) **remain as
validation** but their failure rate should decrease because plan-derived beats are
structured rather than LLM-improvised. The gates cannot be retired because their
semantics don't map cleanly to plan rules:
- `reversal_pack`: detects removal-AND-return of same actor in one chapter — a
  chapter-level beat-ordering concern, not a causal-closure property. A well-formed
  plan could legally have belief-revival in the same chapter as a death.
- `unplayable_beat`: detects time-skip epilogues ("By autumn...") — a *prose pattern*
  check. No plan rule prevents a function whose rendering sounds like a time-skip.
- `composition`: checks adjacent-chapter narrative flow — a prose-level concern, not
  a structural property of the plan.

The gates are a safety net for the prose rendering of plan-derived beats, not
redundant checks on plan structure.

### 4. Integration and chapter-count sequencing

`generate_story` calls `derive_outline` instead of `outline_chapters` when a plan
is attached. The strangler-fig posture continues: `--no-plot-plan` reverts to the
existing `outline_chapters` path.

**Sequencing change (load-bearing).** Today the plan is authored *after*
`expand_chapters` (generate.py:76 — after cast accept, after chapters are derived).
If the plan dictates the chapter count, it must be authored *before* or *instead of*
`expand_chapters`, and the chapter count must flow from the plan to the outline. Two
options:
- **(a)** Author the plan before `expand_chapters`; feed the plan's max chapter
  ordinal as a constraint to `expand_chapters`, which becomes a no-op structurally
  (it just creates the chapter cards at the plan's ordinals).
- **(b)** Author the plan after `expand_chapters` but feed the actual chapter count
  as a constraint to the plan authoring prompt (the current outline-unaware approach,
  improved). The plan's chapter ordinals align with the outline's actual count.

Option **(b)** is lower-risk: it doesn't change the generation pipeline's sequencing,
only adds a parameter to the authoring prompt. Option **(a)** is the destination
architecture but requires a larger integration change. The FR should implement **(b)**
first, with **(a)** as a future refinement.

## Acceptance Criteria

1. **`derive_outline` returns correct structure.** For the floodmark fixture, beats
   match plan functions, cast matches active characters, state contracts match
   `project_chapter_state`.
2. **LLM authors only prose.** The outline's `title` and `summary` come from the LLM;
   `beats`, `cast`, `entry_state`, `exit_state` are plan-derived (deterministic test
   with mocked LLM).
3. **Outline gates remain as validation.** For a plan-derived outline (floodmark +
   variants), the outline gates still run but failure rate is reduced. Gates are not
   retired.
4. **Strangler-fig.** Without a plan, `outline_chapters` is called unchanged.
5. **Regression.** All existing outline and plot tests pass unchanged.

**Test exemptions (FR-474 J3):** example tests are requirement-exempt — no
`@pytest.mark.req`, no capability YAML. Diary reflection required for the feat PR
(diary-gate).

## Dependencies

- **FR-567 (Phase 2):** `project_chapter_state` — the projection function.
- **FR-566 (Phase 1):** complete grammar — the projection is only guaranteed consistent
  if all 7 rules are enforced.

## Risks

- **Integration complexity.** Replacing `outline_chapters` with `derive_outline` means
  rewriting the outline pipeline's integration point in `doc_ops.py` and `generate.py`.
  The outline's card structure (chapter cards with beats, cast, summaries) has specific
  shape expectations downstream. The effort estimate (5–7 days) accounts for this.
- **Chapter count alignment.** The plan's chapter ordinals and the outline's actual
  chapter count must agree. Option (b) in §4 mitigates this by feeding the count to
  the plan prompt, but mismatches are still possible if the plan's ordinals don't
  span the full chapter range.

## Out of Scope

- Forward-carry integration — that is FR-569 (Phase 4).
- Outline editing / interactive refinement — the derived outline is immutable.
- Pipeline sequencing change (option (a) in §4) — plan-before-outline is a future
  refinement, not in scope for this FR.
