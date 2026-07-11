# The Witness That Only Passed in Company

**Date:** 2026-07-11
**FR:** FR-713 Part A (persistent bridge loop)
**Trap encountered:** hidden test-order dependence masquerading as green; instrument rot arriving in triplicate

## What happened

Enforcing FR-713 Part A, the FR-707 drain-WARNING witness failed. First
hypothesis: my change broke the drain. Wrong — `git stash` and a solo run
proved the witness fails **on unmodified main** when run in isolation. The
`yamlgraph` logger has `propagate=False`; caplog captures via the root
logger; the assertion only ever passed when some earlier test in the
session left propagation enabled. The suite's green was a group
photograph — the witness could not stand alone. The repo even had the
antidote on file (`test_state_builder_reducers.py` toggles propagation
explicitly); the pattern just hadn't propagated. A propagation bug about
propagation.

Then the FR's own prophecy fired twice more: FR-706's thread-accounting
assertion and FR-709's survivor assertion both encoded the retired
fresh-loop topology ("population returns to baseline" assumes teardown;
the persistent loop and its executor pool are architecture, not leakage).
The judgement had pre-named this class (F4: instrument rot) for FR-709 —
but only FR-709. FR-706 was the same organ, unnamed.

## The insight

A witness that passes only in company is not a witness — it is a
correlation. And when a substrate changes, EVERY witness that asserts on
the substrate's residue (thread names, thread counts, teardown timing)
rots at once, not just the ones the judgement listed. The judged FR named
one rotting instrument; enforcement found three. The search key for the
sweep was not "which tests fail" but "which assertions mention threads".

## Heuristic

Before enforcing a substrate change, grep the test suite for assertions on
the substrate's OBSERVABLES (thread names/counts, loop identity, teardown
order) — that list, not the failing-test list, is the instrument-rot
blast radius. And when a caplog assertion fails mysteriously: check
`propagate` before checking your change; run the witness ALONE before
believing it ever worked.

**Seed:** The suite passed while one of its witnesses could not pass
alone — should CI run each `test_fr*` witness file in isolation
(pytest-per-file shard) so that order-dependent green is structurally
impossible, the way the RED gate makes untested fixes impossible?
