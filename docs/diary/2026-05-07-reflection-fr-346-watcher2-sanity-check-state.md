# Reflection: FR-346 Watcher2 Sanity-Check Review

**Date:** 2026-05-07
**FR:** FR-346 — Extract shared FSM bridge module (Phase 1)
**Reviewer:** watcher2 (post-validate sanity check)

## What Happened

Independent post-validate review of FR-346's `yamlgraph/utils/fsm/` extraction.
Diff: 852 insertions / 294 deletions across 16 files. The 294 deletions are the
example-local action body replaced by a thin wrapper — a textbook net-positive
refactor. All 10 acceptance tests (4 RED structural + 6 behavioral) pass. No
pipeline log was available on this branch (no FSM runtime invocation recorded).

## Trap

### `working_system_inertia` — the review version

The temptation in watcher2 is the symmetric trap: a green test suite and clean
diff can create false confidence that *review is complete*. The relevant check
is not just "do tests pass?" but "do tests exercise the contract boundary, not
just the happy path?". The `test_interrupt_continue_precedes_event_map_and_route`
test specifically checks that interrupt detection returns a `Command` to the
runner and that `on_continue` beats `on_goodbye` — this is a behavior assertion,
not a shape assertion. That distinction separates adequate tests from trivial
ones.

## What Worked

- Layer boundary was enforced structurally: `graph_runner.py` defers executor
  imports into the function body and exposes `load_fn`/`run_fn` injection points.
  This made all cascade tests runnable without a live LLM or import-linter
  violation.
- `action.py`'s `try/except ImportError` fallback for `statemachine_engine`
  satisfies the optional-dependency constraint without requiring `[fsm]` to be
  installed in CI for helper-only tests.
- The fsm-router wrapper's `GRAPH_BASE_DIR` class attribute preserves
  path-resolution behavior without duplicating any logic.
- Chaplain action file unchanged — out-of-scope boundary held.

## Root Cause (original problem)

Bridge logic in example-local code cannot be guarded by framework-level tests.
Moving the implementation into `yamlgraph/utils/` closes the testing gap.
The extraction is proportional: scope is single-responsibility, no new
dependencies, no behavior changes.

## Seed

Watcher2's current review criteria treat behavioral test coverage as binary
(present/absent). Could a lightweight mutation-style probe — running one
assertion per cascade branch and verifying exactly which branch fires —
be automated as a standard gate, surfacing which resolution steps lack an
independent test? This would turn the "adequate vs. trivial test" judgment
from a manual reviewer decision into a measurable CI signal.
