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
    # Keyed by Fluent.key() → (WorldPred, tuple[str, ...]); value is bool | str
    world_truths: dict[tuple[WorldPred, tuple[str, ...]], bool | str]
    # observer → Fluent.key() → held (bool)
    beliefs: dict[CharacterId, dict[tuple[WorldPred, tuple[str, ...]], bool]]
    # (char, kind) pairs with open but no close
    open_affects: list[tuple[CharacterId, AffectKind]]
```

**Note on key types:** `Fluent.key()` returns `(pred, args)` — a hashable tuple.
`world_truths` maps these keys to `bool | str` values (bool for `alive`/`holds`,
str for `at`/`faction`/`rel`). Using the existing `Fluent.key()` method avoids
inventing a string serialization. Pydantic may require a custom serializer for
tuple keys — the implementation should handle this.

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
   satisfies all predicates in `G`. This is a post-FR-566 invariant: it depends on
   Rule 6 (`_check_goal_reachability`) having verified the plan. For plans validated
   only by the current 4-check validator, this AC is a best-effort check, not a
   guarantee.
5. **Pure function.** No side effects, no LLM calls, no file I/O. Deterministic
   given the same plan and chapter.
6. **Regression.** All existing `test_plot_*.py` tests pass unchanged.

**Test exemptions (FR-474 J3):** example tests are requirement-exempt — no
`@pytest.mark.req`, no capability YAML. Diary reflection required for the feat PR
(diary-gate).

## Dependencies

- **FR-566 (Phase 1):** soft dependency. The projection logic (`project_chapter_state`)
  is independent of the grammar completeness — it walks `ordered_functions` and
  accumulates state without calling `validate_plan`. FR-566 provides the *guarantee*
  that projected state is consistent (all 7 rules enforced), but FR-567 can be built
  and tested against the current 4-check validator. Projections of invalid plans may
  be inconsistent — FR-566 is the guarantee, not the prerequisite.
- **FR-563 (Enforced):** `schema.py` types (`PlotPlan`, `Function`, `Fluent`, `Belief`,
  `AffectDelta`).

## Out of Scope

- Outline derivation — that is FR-568 (Phase 3).
- Forward-carry integration — that is FR-569 (Phase 4).
- Physical micro-state projection (location detail, inventory) — stays prose-derived.
