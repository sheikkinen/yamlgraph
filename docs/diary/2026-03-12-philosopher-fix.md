---
date: 2026-03-12
fr: null
type: reflection
---

# The Phantom Returns

## Cognitive Trap: Documented Behavior Masquerading as Bug

When `scan_diary_markers()` failed with `KeyError: "Cannot resolve 'scan_result'"`, my initial instinct was to fix the framework — wrap dict returns in `state_key` automatically. The Rite of Correction demanded I first condemn the bug with a failing test.

That condemning test revealed the truth: this behavior is documented. See diary-2026-03-02.md "Phantom State Key" trap. Python nodes that return dicts have their keys merged directly into state; `state_key` is decorative for dict returns.

The bug was in the caller, not the callee.

## Heuristic

**Fix at the callsite, not the utility.** When a utility behaves unexpectedly, first check if the behavior is documented. The cheapest fix is often adjusting the caller to work with documented behavior, not changing the system to match assumptions.

This aligns with the Prayer: "May I fix at the callsite, not the utility."

## Seed

If `state_key` is ignored for dict returns, should the linter warn when a Python node declares both `state_key` and a function that returns dict? Or is the current behavior intentional flexibility — allowing functions to populate multiple state keys?
