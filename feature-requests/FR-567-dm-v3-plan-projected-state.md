# Feature Request: FR-567 DM v3 — plan-projected state

**Priority:** HIGH
**Type:** Feature
**Status:** Proposed (2026-06-22)
**Effort:** 2–3 days
**Requested:** 2026-06-22
**Plan:** [`plan-v3-planner.md`](../examples/dungeon_master/docs/plan-v3-planner.md) Phase 2

## Summary

A pure projection function that computes cumulative world + belief + affect state at
any chapter, derived from the plan alone. This is the foundation the forward-carry
and outline derivation build on.

## Value Statement

DM maintainers get `project_chapter_state(plan, chapter) → ChapterState` — a typed,
testable state snapshot at any chapter, computed purely from the plan's functions and
initial state. No LLM, no prose, no side effects. The state at chapter 0 equals `I`.
The state at the last chapter satisfies `G`. This is the single function that makes
the plan's well-formedness rules actionable at runtime.

## Problem

The current `project.py` projects individual lanes (exclusion set, belief at chapter)
but does not compute a **cumulative** state. Chapter close (`close_chapter` in
`chapter_ops.py`) re-derives load-bearing state from prose at each chapter boundary.
Two parallel truth sources run: the `PlotPlan` (authored, static) and the
`world_state` ledger (prose-derived, per-chapter). Neither reads the other.

The plan's well-formedness guarantees (Rules 1–7) should imply that the projected
state at any chapter is consistent — but no function computes it.

## Proposed Solution

### 1. `ChapterState` typed model

A Pydantic model representing the cumulative state at a chapter boundary:

```python
class ChapterState(BaseModel):
    """Cumulative plan-projected state at a chapter boundary."""
    chapter: int
    world_truths: dict[str, bool]    # ground predicates (alive, at, holds, ...)
    beliefs: dict[str, dict[str, bool]]  # observer → predicate → bool
    open_affects: list[str]          # affect tokens with open but no close
```

### 2. `project_chapter_state(plan, chapter) → ChapterState`

A pure function that walks the plan's functions up to `chapter`, accumulating:
- `eff_world` predicates into `world_truths`
- `eff_belief` predicates into `beliefs`
- `affect` open/close deltas into `open_affects`

Starting from the plan's initial state `I`.

### 3. Invariant tests

- State at chapter 0 equals `I` (the initial state).
- State at the last chapter satisfies `G` (all goal predicates hold).
- Floodmark fixture: state at ch3 = Arnulf alive (world), Clan believes dead
  (belief), loss(Hilde) open (affect).

## Acceptance Criteria

1. **`ChapterState` model exists.** Typed, serializable, testable.
2. **`project_chapter_state` returns correct state.** For the floodmark fixture,
   state at each chapter matches hand-verified expectations.
3. **Initial state invariant.** `project_chapter_state(plan, 0)` equals the plan's
   initial state `I`, formatted as a `ChapterState`.
4. **Goal satisfaction invariant.** `project_chapter_state(plan, last_chapter)`
   satisfies all predicates in `G`.
5. **Pure function.** No side effects, no LLM calls, no file I/O. Deterministic
   given the same plan and chapter.
6. **Regression.** All existing `test_plot_*.py` tests pass unchanged.

## Dependencies

- **FR-566 (Phase 1):** complete grammar — the projection relies on all 7 rules being
  enforced so the projected state is guaranteed consistent.
- **FR-563 (Enforced):** `schema.py` types (`PlotPlan`, `Function`, `Fluent`, `Belief`,
  `AffectDelta`).

## Out of Scope

- Outline derivation — that is FR-568 (Phase 3).
- Forward-carry integration — that is FR-569 (Phase 4).
- Physical micro-state projection (location detail, inventory) — stays prose-derived.
