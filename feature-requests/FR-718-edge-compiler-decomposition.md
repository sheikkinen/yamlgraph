# Feature Request: FR-718 Edge Compiler Decomposition — the C(20) at the Core

**Priority:** MEDIUM (highest-complexity function in the highest-blast-radius module)
**Type:** Enhancement (refactor — complexity decomposition, TDD-pinned)
**Status:** Judged (2026-07-12) — scope frozen; authority granted; note F1 (decomposition is completion, not invention)
**Effort:** 1 day
**Requested:** 2026-07-12
**Spawned by:** docs/2026-07-12-review-refactoring.md P2.4 (`_process_edge` C 20, `_add_conditional_edges` C 18 — routing is core semantics; edge bugs are graph-wide)
**Related:** `edge_compiler.py` (299 lines), FR-223 (decomposition pattern: pure resolvers + dispatch), CAP-06 routing-flow-control, `regex_fourth_exclusion` (fourth special case → proper structure)

## Summary

The two most complex functions in the codebase both live in
`edge_compiler.py` and both dispatch on edge SHAPE (plain, conditional,
map, parallel fan-out, race-router, interrupt…) via accumulated
if-chains. Decompose into a shape-dispatch table of pure per-shape
compilers, FR-223-style.

## Value Statement

Every graph feature that touches routing (fan-out FR, race-router,
interrupts) has added a branch to the same two functions — C(20) is the
fossil record of that accretion. Each next branch is written inside 20
existing decision paths; the defect class is `_process_edge` silently
mis-classifying a new edge shape as an old one (plausible_wrong_answer
at compile time — the graph builds, routes wrong).

## Problem

- `_process_edge` C(20): one function classifies AND compiles every edge
  shape.
- `_add_conditional_edges` C(18): condition-map assembly interleaved
  with LangGraph API calls — untestable without a compiled graph.
- Both are Layer-2 core: a bug here is every user's bug.

## Proposed Solution

- Classification separated from compilation: `classify_edge(edge) ->
  EdgeShape` (pure, exhaustively unit-testable) + per-shape compilers
  `_compile_<shape>(...)` registered in a dispatch dict — the same move
  that took llm_nodes below the gate in FR-223.
- `_add_conditional_edges`: extract condition-map construction as a pure
  function returning the mapping; the LangGraph `add_conditional_edges`
  call becomes a 3-line consumer.
- Unknown shape RAISES naming the edge (Commandment 6 — no silent
  default branch; today the else-branch is an implicit shape claim).

## Constraints (TDD discipline — this is core semantics)

1. BEFORE any extraction: pin current behavior with a
   shape-classification witness — every edge form in `examples/` and
   `tests/fixtures/` graphs compiled, the resulting LangGraph edge set
   snapshot-asserted (assert the PATH: which compiler fired per edge,
   not just that compilation succeeded).
2. Extraction is mechanical after the pin; any test change during
   extraction is scope violation (the pin IS the contract).

## Deletion Ledger

If-chain branches → dispatch entries (net negative); duplicated
condition-parsing between the two functions → one shared pure helper.

## Acceptance Criteria

- [ ] AC-01 RED first: shape-classification witness pinning every edge
      form currently compilable (fixtures enumerated in the test, count
      asserted so a new shape must register itself)
- [ ] AC-02 `_process_edge` and `_add_conditional_edges` CC < 10; no new
      function above CC 10
- [ ] AC-03 Unknown edge shape raises with the edge named — witnessed
- [ ] AC-04 Full unit suite + `yamlgraph graph lint/run` smoke on
      examples/demos green unmodified (after the AC-01 pin lands)
- [ ] AC-05 Net line delta ≤ 0 in edge_compiler.py
- [ ] Changelog fragment (CAP-06 REQ); diary entry

## Judgement (2026-07-12)

| # | Finding | Resolution |
|---|---------|------------|
| F1 | Source check: per-shape handlers ALREADY exist (`_handle_start_edge`, `_handle_map_to_map_edge`, `_handle_to_map_edge`, `_handle_from_map_edge`, `_add_parallel_fanout_edges`) — the C(20) is the boolean-probe classification chain ("returns True if handled"), not monolithic compilation. The FR slightly overstated the problem; the cure is right but smaller | Scope sharpened: `classify_edge(edge, context) -> EdgeShape` replaces the probe chain; existing handlers become the dispatch targets largely as-is. Effort likely 0.5 day, keep 1 day budget |
| F2 | "Unknown shape raises" — today's fall-through IS the plain-edge case, a legitimate shape, not an implicit claim | Amended: classification is exhaustive with `PLAIN` as an explicit enum member; the raise fires only for a shape the classifier cannot name (e.g. `to: list` WITH condition AND type mismatch). The witness enumerates the enum |

## Alternatives Considered

- Confess the complexity and leave it — rejected: unlike the 14 leaf
  C-grade functions (which the review explicitly leaves alone), this one
  is incident-dense core with a growth trajectory; the fourth special
  case already happened.
- Full edge-compiler rewrite — rejected: `constraint_over_code` favors
  keeping the tested behavior and re-seaming it; the spec is the
  fixtures, which stay.
