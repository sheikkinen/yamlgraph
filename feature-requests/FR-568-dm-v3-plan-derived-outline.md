# Feature Request: FR-568 DM v3 — plan-derived outline

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed (2026-06-22)
**Effort:** 3–4 days
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
`composition`) hold by construction for any well-formed plan — Rules 2–6 imply them.
The LLM's role shrinks from "design the chapter structure" to "name and summarize
each chapter."

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

### 3. Outline gate retirement

The outline gates (`reversal_pack`, `unplayable_beat`, `composition`) are validated
against the plan. For a well-formed plan, they should hold by construction:
- `reversal_pack`: causal closure (Rule 2) ensures no dangling preconditions
- `unplayable_beat`: grounding (Rule 1) ensures all terms exist
- `composition`: goal reachability (Rule 6) ensures the finale delivers

### 4. Integration

`generate_story` calls `derive_outline` instead of `outline_chapters` when a plan
is attached. The strangler-fig posture continues: `--no-plot-plan` reverts to the
existing `outline_chapters` path.

## Acceptance Criteria

1. **`derive_outline` returns correct structure.** For the floodmark fixture, beats
   match plan functions, cast matches active characters, state contracts match
   `project_chapter_state`.
2. **LLM authors only prose.** The outline's `title` and `summary` come from the LLM;
   `beats`, `cast`, `entry_state`, `exit_state` are plan-derived (deterministic test
   with mocked LLM).
3. **Outline gates hold by construction.** For any well-formed plan (floodmark +
   variants), the outline gates pass without explicit checking.
4. **Strangler-fig.** Without a plan, `outline_chapters` is called unchanged.
5. **Regression.** All existing outline and plot tests pass unchanged.

## Dependencies

- **FR-567 (Phase 2):** `project_chapter_state` — the projection function.
- **FR-566 (Phase 1):** complete grammar — gates hold by construction only if all 7
  rules are enforced.

## Out of Scope

- Forward-carry integration — that is FR-569 (Phase 4).
- Outline editing / interactive refinement — the derived outline is immutable.
- Chapter count negotiation — the plan dictates the chapter count; the outline follows.
