# The Module That Drifted Past Its Own Constraint

**Date:** 2026-06-16
**FR:** FR-493 — DM Adapter Size-Gate Split & Scene-Phase Legibility
**Regime:** FR-474 J3 (DM prototype; diary required, gates exempt)

## What happened

`turn_ops.py` and `chapter_ops.py` both open with a docstring stating they exist
*"so `session` stays under the size gate."* Yet `session.py` had quietly drifted
back to 508 lines — past the 450 max those very siblings were carved out to
defend. The authors wrote the constraint, extracted twice to honour it, and then
let the parent re-bloat anyway. The doctrine was present; the enforcement was not.

The fix had two cohesion-only halves, no behaviour change:

1. **Lift the doc cluster into `doc_ops.py`** — nine pure `(doc, …)` functions
   (`entry`, `characters`, `chapters`, `invoke_stage` + the five expansions),
   acyclic, mirroring the existing `*_ops` modules. session.py 508 → 333.
2. **Name the Scene lifecycle** — a `── Scene lifecycle ──` banner in `turn_ops`
   fencing the four play functions under one phase contract
   (`{plan, world_state_in} → turns → {final_text, world_state_out}`), with
   `chapter_ops.close_chapter` cross-referencing it as the adapter-facing entry.

## The trap

**doctrine_without_enforcement.** The size constraint existed as prose in a
docstring — *"so session stays under the gate"* — but nothing measured it. A
prose constraint is a wish; only a test is a fence. The regression was invisible
because the only witness was a human remembering to run `wc -l`. The cure was to
make the constraint a *test* (`test_session_module_under_size_gate`), committed
RED at 508 then GREEN at 333, so the next drift fails CI instead of a code review.
This is the same shape as `gate_checks_shape_not_substance` inverted: there the
gate checked presence but not meaning; here there was *no gate at all*, only a
meaning written in a comment. Both resolve to: **if you state a constraint, also
measure it — the sentence that guards nothing guards nothing.**

A second, smaller trap surfaced in the naming: the moved write-wrapper
`_close_chapter` could not become `doc_ops.close_chapter` without colliding with
the pure `chapter_ops.close_chapter` it *calls*. Renaming it `apply_chapter_close`
(the write applies what the pure read derives) kept the two seams legible. The
judgment caught this before a line was written — the cheapest bug is the one
killed in the spec.

## The heuristic

> **A constraint stated in a docstring is documentation; a constraint stated in a
> test is a fence.** When a module's reason-for-existing is "to keep X small,"
> the smallness must be a test, or X will drift back the moment attention moves
> on. Extraction relieves the symptom; the guard test prevents the recurrence.

## Seed

The DM example now has five `*_ops` modules (`turn_ops`, `chapter_ops`,
`doc_ops`, plus `story_doc`, `graph_app`) all justified by "keep session thin,"
yet only `session.py` now has a size-gate test. **Should the size gate be a
parametrised test over *every* module in `api/`, not just the one that drifted?**
A single guard catches the module that already bloated; a parametrised guard
catches the one that *will*. When is a per-module ceiling worth the test, and
when does it ossify a structure that should be free to grow before it splits?
