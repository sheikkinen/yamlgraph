# Feature Request: FR-716 Pre-emptive Splits — graph_schema + executor_async

**Priority:** MEDIUM
**Type:** Enhancement (refactor — module splits at chosen seams)
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-07-12
**Spawned by:** docs/2026-07-12-review-refactoring.md P2.3 (five modules within 15 lines of the 450 gate) + P2.4 (`run_graph_streaming_native` C 17)
**Related:** file-size pre-commit gate (>450 error), `models/graph_schema.py` (448), `executor_async.py` (435), streaming diary arc FR-057–060

## Summary

Split the two size-gate-pressured modules with obvious fault lines NOW,
while the seams can be chosen calmly — the alternative is an unplanned
split under deadline pressure the next time a feature touches them
(the worst time to pick module boundaries).

## Problem

- `models/graph_schema.py` at 448/450: the next validator added to any
  node model breaches the gate mid-feature.
- `executor_async.py` at 435 AND containing the C(17)
  `run_graph_streaming_native` — the fattest module holds the most
  complex function; one extraction fixes both findings.
- (`checks_contracts.py` 441, `node_compiler.py` 440, `state_builder.py`
  438 are also near the gate but lack clean fault lines today —
  explicitly OUT of scope; splitting without a seam creates coupling,
  not relief.)

## Proposed Solution

- `graph_schema.py` → `models/graph_schema.py` (graph-level: GraphConfig,
  edges, defaults) + `models/node_schema.py` (per-node-type config
  models). Pure move; `models/__init__` re-exports keep every import
  site working (public names unchanged — not a compat shim, the package
  namespace IS the API).
- `executor_async.py`: extract the stream-event translation loop from
  `run_graph_streaming_native` into `streaming_events.py` (pure
  functions: LangGraph event → yamlgraph event). The streaming X-ray
  arc (FR-057–060) lives in that loop — isolating it makes the next
  streaming incident's blast radius one small module.

## Deletion Ledger

Net zero lines (moves), minus the C(17) grade: the translation loop as
pure functions decomposes below CC 10 naturally (dispatch table replaces
the if-chain — `regex_fourth_exclusion` cousin: fourth event type
special-case → table).

## Acceptance Criteria

- [ ] AC-01 Both new modules < 300 lines; no module touched by this FR
      above 400
- [ ] AC-02 `run_graph_streaming_native` CC < 10; extracted translation
      functions individually < 10
- [ ] AC-03 All imports resolve unchanged (`lint-imports` green; full
      unit suite green unmodified — pure-move witness)
- [ ] AC-04 Streaming integration tests (subgraph/interrupt event
      shapes) green unmodified — the translation loop's behavior is
      pinned before the move (assert_path_not_destination: event
      SEQUENCE asserted, not final state)
- [ ] Changelog fragment; diary entry

## Alternatives Considered

- Wait for the gate to force it — rejected: that is exactly the
  deadline-pressure seam-picking this FR pre-empts.
- Split all five near-gate modules — rejected: three lack fault lines;
  forced splits create import cycles (the llm_nodes ↔ router_race lazy
  import is the standing warning).
