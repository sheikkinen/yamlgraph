# Watcher2 Sanity Check: FR-392 — FSM Runner payload_keys Forwarding

**Date:** 2026-05-15
**FR:** FR-392
**Reviewer:** watcher2 post-validate
**Verdict:** PASS

## What Was Reviewed

`yamlgraph/utils/fsm/graph_runner.py` — payload assembly path in `run_and_dispatch()`.
Five acceptance tests in `tests/unit/test_fr392_fsm_payload_keys_red.py`.

## Trap: Boundary Contract Existed, Wiring Did Not

`SnapshotParams.payload_keys` was declared in the typed contract (`snapshot.py`) since
FR-369, but the runner never read it. The fix belongs at the single boundary where
checkpoint state is already available — not patched into consumers downstream.
This is a textbook instance of `downstream_fix` avoidance: the right cure was
`_build_payload` at the boundary, not a `pre_dispatch` workaround at each callsite.

## What Happened

- `_build_payload` extracted as a pure function: receives `result`, `output_key`,
  `snapshot`, and `after_values`; returns payload dict with no side effects.
- `_extract_completion_state` isolated the checkpoint-state parsing that was already
  present but inlined; this refactor had zero behavior change for existing paths.
- `after_values` stays `None` on the legacy (no `thread_id`) path, so `_build_payload`
  silently skips the payload-key merge — AC-05 confirmed.

## Root Cause

Missing wiring: `snapshot.payload_keys` was populated by `snapshot_params()` but
`run_and_dispatch()` never iterated it. The bug was silent — no exception, just
missing context in dispatched events.

## Test Quality

- 5 tests map 1:1 to AC-01..AC-05.
- Each test exercises the full `run_and_dispatch` integration path via mocked
  `load_fn`/`run_fn`/`aget_state`.
- Assertions target dispatched payload contents (behavior), not internal state.
- All 5 pass; regression suite (17 tests across bridge + FR-391) passes clean.
- No pipeline logs available; test evidence is sufficient for a boundary-wiring fix.

## Proportionality

48 lines of production code change (two extracted helpers + call-site update),
204 lines of acceptance tests, supporting changelog/FR/diary artifacts.
Scope is tightly bounded to the payload-assembly boundary. No cascade/routing
changes. Proportional to the declared 0.5-day effort.

## Seed:

Could `_build_payload` become the authoritative payload-assembly contract for all
`run_and_dispatch` dispatch paths (success, error, interrupt), eliminating any
remaining per-path payload construction scattered across the function?
