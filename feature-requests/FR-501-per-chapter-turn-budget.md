# Feature Request: FR-501 — Per-chapter turn budget (runaway-chapter safety valve)

**Priority:** HIGH
**Type:** Bug fix
**Status:** Enforced (2026-06-16)
**Effort:** < 1 day
**Requested:** 2026-06-16

## Summary

The DM v2 headless play loop closes a chapter **only** when its director emits
`scene_complete: true`. There is no per-chapter turn budget, so a director that
never declares the scene resolved plays the chapter unboundedly until the
whole-book `turn_cap` is exhausted — and the book gate never opens.

## Problem

A live Floodmark regeneration on the `inception`/`mercury` provider raised:

```
RuntimeError: book gate did not open within turn_cap=96; chapters played:
[('1', True), ('2', False), ('3', False), ('4', False), ('5', False)]
```

Inspecting the generated `story.json`:

| Chapter | turns | phases | scene_complete |
|---|---|---|---|
| 1 | 6  | opening 1, rising 3, climax 1, resolved 1 | 1 |
| 2 | 91 | opening 1, **rising 90** | **0** |
| 3–5 | 0 | — | — |

Chapter 1 resolved naturally in 6 turns. Chapter 2's director stayed in
`"rising"` for 91 turns and never escalated to `climax`/`resolved`, so
`scene_complete` never fired — and chapter 2 ate the entire remaining budget,
starving chapters 3–5.

This is the architectural defect, **not** a provider defect: the loop delegates
chapter termination entirely to the model's judgement with no deterministic
floor (Scripture: `working_system_inertia` — vertex happened to resolve quickly,
hiding the missing safety valve; inception merely exposed it; and `the_one_law` /
"trust no provider's type" — the boundary must bound the chapter, not assume the
provider eventually closes it).

## Proposed Solution

Add a per-chapter turn budget — a deterministic backstop that force-closes a
chapter once it has played `CHAPTER_TURN_CAP` turns without the director
resolving. The two play-loop gate sites that branch on `scene_complete`
(`navigation.accept_target` and `session.accept`) call a single predicate:

```python
CHAPTER_TURN_CAP = 16  # generous above the ~6-turn natural length

def chapter_should_close(doc, cid, n) -> bool:
    if turn_direction(doc, cid, n).get("scene_complete"):
        return True
    return n >= CHAPTER_TURN_CAP
```

The cap is generous (≈2.7× the observed natural chapter length) so a well-behaved
director still closes on `scene_complete`; the budget only triggers on a runaway.
With ≤16 turns per chapter, the book is bounded by `chapters × 16` turns
regardless of provider, with the existing whole-book `turn_cap` as the outer net.

## Acceptance Criteria

- [x] `chapter_should_close` returns True on `scene_complete`, True at the budget
      without `scene_complete`, False below the budget.
- [x] `navigation.accept_target` advances to the next chapter's first turn when a
      chapter hits the budget without `scene_complete` (force-close), and keeps
      advancing turns below the budget.
- [x] `session.accept` closes the chapter (derives end-of-chapter `world_state`,
      marks reviewed) on the budget backstop, identically to `scene_complete`.
- [x] Full DM suite green; the change touches only `examples/dungeon_master/`.
- [x] Diary + changelog fragment.

## Alternatives Considered

- **Switch back to vertex, leave the loop unbounded.** Treats the symptom (a weak
  provider) and leaves the latent runaway defect; any provider, including vertex
  on an unlucky chapter, can still hang. Rejected as the *only* action — vertex
  remains the quality default, but the cap is the root-cause fix.
- **Force `scene_complete` into the prompt harder.** The director is already told
  to be strict; prompt-tuning cannot give a deterministic termination guarantee.
- **Derive the cap from `turn_cap / len(order)`.** Couples the pure navigation
  module to the book-level budget; a fixed safety-valve constant is simpler and
  clearer in intent. Rejected.

## Regime

Prototype-only under FR-474 J3: touches only `examples/dungeon_master/`, no CAP
file, no `@pytest.mark.req` markers, committed with an honest
`fix(dungeon-master): FR-501 …` plus the `FR-474 J3` trailer.

## Implementation Status — Enforced

- **Predicate (AC1).** `turn_ops.CHAPTER_TURN_CAP = 16` and
  `turn_ops.chapter_should_close(doc, cid, n)` added.
- **Wiring (AC2, AC3).** `navigation.accept_target` and `session.accept` both
  branch on `chapter_should_close` instead of the raw
  `turn_direction(...).get("scene_complete")`. `apply_chapter_close` already
  tolerates a non-`scene_complete` chapter (its `climax_turn` falls back to the
  last played turn), so the forced close derives a sensible end-of-chapter ledger.
- **Tests.** 5 new pure tests in `tests/test_navigation.py` (predicate truth
  table + force-close advance + below-budget advance). Full DM suite: **114
  passed**.
- **Regime (FR-474 J3).** No CAP, no req markers; honest commit + trailer.

## Related

- FR-499A — the structured ledger this safety valve protects (an unbounded
  chapter never closes, so the ledger never carries forward)
- FR-491 / FR-479 — the scene-complete play-loop contract this bounds
- `examples/dungeon_master/api/turn_ops.py`, `navigation.py`, `session.py`
- `outputs/dungeon-master/10002-BC/story/story.json` (live evidence)
