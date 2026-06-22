# Feature Request: FR-566 DM v3 — complete the grammar

**Priority:** HIGH
**Type:** Feature
**Status:** Proposed (2026-06-22)
**Effort:** 2–3 days
**Requested:** 2026-06-22
**Plan:** [`plan-v3-planner.md`](../examples/dungeon_master/docs/plan-v3-planner.md) Phase 1

## Summary

Add the two missing well-formedness checks (Rules 1 and 6) and expand the vocabulary
to the destination alphabets. With this, `validate_plan` implements all seven rules
of the formal language defined in the v3 planner plan, making the plan a complete
grammar check. `unified-planning` becomes truly optional.

## Value Statement

DM maintainers get a `validate_plan` that is a **complete** grammar check — every
well-formed plan is provably consistent (grounded terms, reachable goals, causal
closure, monotonic lifecycle, grounded belief, closed affects, acyclic ordering).
A plan that passes all seven rules needs no external solver to guarantee structural
consistency.

## Problem

The current validator (`validate.py`) implements 5 of the 7 well-formedness rules:

| Rule | Status |
|------|--------|
| 1 — Grounding | **Missing** |
| 2 — Causal closure | Partial (existence only, not temporal validity) |
| 3 — Monotonic lifecycle | Complete |
| 4 — Grounded reveal | Complete |
| 5 — Affect closure | Complete |
| 6 — Goal reachability | **Missing** |
| 7 — Acyclicity | Complete |

The vocabulary is also incomplete:
- `FunctionKind` has 4 of the 10 destination kinds (missing: departure, struggle,
  victory, death, pursuit, rescue)
- `AffectKind` has 2 of the 5 destination kinds (missing: betrayal, retaliation,
  hidden_blessing)

A plan authored with the current vocabulary cannot express pursuit, rescue, departure,
or struggle — common Propp functions that real premises require. An authored plan with
ungrounded terms or unreachable goals silently passes validation.

## Proposed Solution

### 1. `_check_grounding(plan)` — Rule 1

Every term in every predicate in `I`, `G`, `F.pre`, `F.eff` must refer to a named
entity in the plan's agents set or introduced in `I` or `F`. This is a closed-world
check: no dangling references.

```python
def _check_grounding(plan: PlotPlan) -> list[str]:
    """Rule 1: every term in every predicate refers to a declared entity."""
    known = {a for a in plan.agents}
    # Add entities introduced by initial state predicates
    for f in plan.initial_state:
        known.update(_extract_terms(f))
    errors = []
    for fn in plan.functions:
        for p in fn.pre + fn.eff:
            for term in _extract_terms(p):
                if term not in known:
                    errors.append(f"ungrounded term {term!r} in {fn.id}")
    for g in plan.goals:
        for term in _extract_terms(g):
            if term not in known:
                errors.append(f"ungrounded term {term!r} in goal")
    return errors
```

### 2. `_check_goal_reachability(plan)` — Rule 6

Every predicate in `G` is either (a) in `I` and never negated by any `F.eff`, or
(b) established by some `F.eff` and never negated by a later `F'.eff`.

```python
def _check_goal_reachability(plan: PlotPlan) -> list[str]:
    """Rule 6: every goal predicate is reachable from the plan's functions."""
    errors = []
    for g in plan.goals:
        if not _is_reachable(g, plan):
            errors.append(f"unreachable goal: {g}")
    return errors
```

### 3. Vocabulary expansion

**`FunctionKind`** (schema.py): add `departure`, `struggle`, `victory`, `death`,
`pursuit`, `rescue` to the existing `villainy`, `reveal`, `reconciliation`, `return`.

**`AffectKind`** (schema.py): add `betrayal`, `retaliation`, `hidden_blessing` to
the existing `loss`, `guilt`.

### 4. Prompt update

Update `author_plot_plan.yaml` with the full action and affect alphabets so the
authoring LLM can use the complete vocabulary.

## Acceptance Criteria

1. **Rule 1 enforced.** A plan with an ungrounded term (reference to a character not
   in agents or initial state) fails `validate_plan` with a grounding error. A
   well-formed plan passes.
2. **Rule 6 enforced.** A plan with an unreachable goal (not in initial state and not
   established by any function's effects) fails `validate_plan` with a reachability
   error. A well-formed plan passes.
3. **Vocabulary complete.** `FunctionKind` has 10 members. `AffectKind` has 5 members.
   Existing fixtures and tests still pass (the 4 existing kinds are unchanged).
4. **New kinds exercised.** At least one fixture uses a new `FunctionKind` and one uses
   a new `AffectKind`, proving the expanded vocabulary is wired.
5. **Prompt updated.** `author_plot_plan.yaml` lists all 10 action kinds and 5 affect
   kinds.
6. **Regression.** All existing `test_plot_*.py` tests pass unchanged.

## Dependencies

- **FR-565 (Enforced):** producer integration (the pipeline that fires validation).
- **FR-563 (Enforced):** `schema.py`, `validate.py`, `author.py` (the validation infrastructure).

## Out of Scope

- Rule 2 (causal closure) temporal validity strengthening — partial check is sufficient
  for this phase.
- Sort typing (Place, Object as first-class types) — strings are sufficient for the
  current vocabulary.
- `unified-planning` solver integration — the seven pure checks make it optional.
