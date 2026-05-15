# Reflection: FR-392 — payload_keys forwarding

**Date:** 2026-05-15
**FR:** FR-392
**Scope:** `yamlgraph.utils.fsm.graph_runner`

## Cognitive Process

The bug was a classic boundary-normalization failure: `SnapshotParams.payload_keys`
was declared in the typed contract (`snapshot.py`) but never wired into the dispatch
path in `graph_runner.py`. The contract existed; the implementation did not honour it.

## Trap Encountered

**downstream_fix avoidance.** The temptation was to patch consumers to extract
payload keys themselves via `pre_dispatch` hooks. That would have pushed the fix
downstream and duplicated logic. Instead, the fix belongs at the boundary where
checkpoint state is already available — inside `_build_payload`.

## Insight

Extracting `_build_payload` as a pure function made the fix trivially testable:
input → output with no side effects. The five acceptance tests map 1:1 to the
acceptance criteria, and each exercises the function through the full
`run_and_dispatch` integration path.

## Seed:

Could `_build_payload` become the single canonical payload-assembly point for
all dispatch paths (success, error, interrupt), unifying the currently separate
payload construction scattered across handler functions?
