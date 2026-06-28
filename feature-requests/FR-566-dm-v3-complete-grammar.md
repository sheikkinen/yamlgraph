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
def _extract_terms(obj: Fluent | Belief | AffectDelta) -> set[str]:
    """Extract entity names from typed pre/eff objects."""
    if isinstance(obj, Fluent):
        return set(obj.args)  # e.g. ("Arnulf",) for alive, ("Arnulf", "Mountain") for at
    if isinstance(obj, Belief):
        return {obj.observer} | set(obj.fluent.args)
    if isinstance(obj, AffectDelta):
        return {obj.char}
    return set()

def _check_grounding(plan: PlotPlan, order: list[Function]) -> list[PlanFlaw]:
    """Rule 1: every term in every predicate refers to a declared entity."""
    known: set[str] = set(plan.agents)
    # Add entities introduced by initial state
    for f in plan.initial_world:
        known.update(f.args)
    for b in plan.initial_belief:
        known.add(b.observer)
        known.update(b.fluent.args)
    flaws: list[PlanFlaw] = []
    for fn in order:
        for obj in fn.pre_world + fn.eff_world:  # Fluent
            for term in obj.args:
                if term not in known:
                    flaws.append(PlanFlaw(
                        code="ungrounded_term", function_id=fn.id,
                        detail=f"{fn.id} references {term!r} not in agents or initial state.",
                    ))
        for obj in fn.pre_belief + fn.eff_belief:  # Belief
            for term in _extract_terms(obj):
                if term not in known:
                    flaws.append(PlanFlaw(
                        code="ungrounded_term", function_id=fn.id,
                        detail=f"{fn.id} references {term!r} not in agents or initial state.",
                    ))
        for obj in fn.eff_affect:  # AffectDelta
            if obj.char not in known:
                flaws.append(PlanFlaw(
                    code="ungrounded_term", function_id=fn.id,
                    detail=f"{fn.id} references {obj.char!r} not in agents or initial state.",
                ))
    for g in plan.goals:
        for term in g.args:
            if term not in known:
                flaws.append(PlanFlaw(
                    code="ungrounded_term", function_id="(goal)",
                    detail=f"goal references {term!r} not in agents or initial state.",
                ))
    return flaws
```

**Note on `_extract_terms`:** The helper handles the three object shapes in `pre`/`eff`
lists: `Fluent` (uses `.args`), `Belief` (uses `.observer` + `.fluent.args`),
`AffectDelta` (uses `.char`). All entity arguments are untyped strings — grounding
treats every arg as an entity reference regardless of sort.

### 2. `_check_goal_reachability(plan)` — Rule 6

Every predicate in `G` is either (a) in `I` and never negated by any `F.eff`, or
(b) established by some `F.eff` and never negated by a later `F'.eff`.

```python
def _check_goal_reachability(plan: PlotPlan, order: list[Function]) -> list[PlanFlaw]:
    """Rule 6: every goal predicate is reachable — in I (never negated) or established by F.eff (never negated later)."""
    flaws: list[PlanFlaw] = []
    for g in plan.goals:
        g_key = g.key()
        # Case (a): in initial_world and never negated by any function
        in_initial = any(f.key() == g_key and f.value == g.value for f in plan.initial_world)
        negated_after_initial = any(
            e.key() == g_key and e.value != g.value
            for fn in order for e in fn.eff_world
        )
        if in_initial and not negated_after_initial:
            continue
        # Case (b): established by some function and never negated by a later one
        last_producer_idx = None
        for i, fn in enumerate(order):
            for e in fn.eff_world:
                if e.key() == g_key and e.value == g.value:
                    last_producer_idx = i
        if last_producer_idx is not None:
            negated_later = any(
                e.key() == g_key and e.value != g.value
                for fn in order[last_producer_idx + 1:] for e in fn.eff_world
            )
            if not negated_later:
                continue
        flaws.append(PlanFlaw(
            code="unreachable_goal", function_id="(goal)",
            detail=f"goal {g.pred}({', '.join(g.args)})={g.value!r} is not reachable.",
        ))
    return flaws
```

**Note on temporal validity:** Rule 6's "never negated by a later F'.eff" is an
*existence-based* forward scan over the ordered functions, not a temporal-validity
proof. It checks whether the last producer of the goal predicate is followed by a
contradicting effect. This is consistent with Rule 2's existence-based posture —
temporal validity (a goal's producer is negated by an intermediate function and
later re-established) is a solver concern, permanently owned by `unified-planning`.

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
4. **New flaw codes.** `FlawCode` grows by two: `"ungrounded_term"` (Rule 1) and
   `"unreachable_goal"` (Rule 6). Doctrine: no code without an emitter (FR-560 J4b).
5. **New kinds exercised.** At least one fixture uses a new `FunctionKind` and one uses
   a new `AffectKind`, exercising the full parse→validate→project pipeline (not just
   schema construction).
6. **Prompt updated.** `author_plot_plan.yaml` lists all 10 action kinds and 5 affect
   kinds.
7. **Regression.** All existing `test_plot_*.py` tests pass unchanged.

**Test exemptions (FR-474 J3):** example tests are requirement-exempt — no
`@pytest.mark.req`, no capability YAML. Diary reflection required for the feat PR
(diary-gate).

## Dependencies

- **FR-565 (Enforced):** producer integration (the pipeline that fires validation).
- **FR-563 (Enforced):** `schema.py`, `validate.py`, `author.py` (the validation infrastructure).

## Risks

- **Prompt expansion changes LLM behavior.** Adding 6 new `FunctionKind` values means
  the authoring LLM may author plans using `death`, `pursuit`, etc. The existing
  `parse_plot_plan` drops off-alphabet kinds — after expansion, the alphabet is wider,
  so more kinds survive parsing. New action signatures (e.g., `departure(subject, from,
  to)` where `from`/`to` are Places) introduce args that are untyped strings. Grounding
  must treat all args as entity references. Mitigated by AC5 (fixture exercises full
  pipeline with new kinds).
- **`FlawCode` growth.** Two new codes widen the `Literal` type. Downstream consumers
  that pattern-match on `FlawCode` (e.g., repair-loop feedback) must handle the new
  codes. Mitigated by AC4 (new codes have emitters and fixtures).

## Out of Scope

- Rule 2 (causal closure) temporal validity strengthening — existence-based check is
  the permanent pure-check posture; temporal validity is the `unified-planning`
  solver's concern.
- Sort typing (Place, Object as first-class types) — strings are sufficient for the
  current vocabulary.
- `unified-planning` solver integration — the seven pure checks make it optional.
