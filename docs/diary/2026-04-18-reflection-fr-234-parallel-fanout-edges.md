# Diary: FR-234 Parallel Fan-Out Edges

**Date:** 2026-04-18
**FR:** FR-234

## Cognitive Process

Parallel fan-out (`to: [a, b, c]` without `type: conditional`) required careful handling of four distinct edge cases in the compiler: regular nodes, interrupt nodes (redirect to `_prepare`), map node targets (already conditional), and START fan-out (conditional entry point). Each case had a different existing mechanism that had to be preserved while threading through the new list-to-multiple-edges expansion.

## Trap Avoided: False Duplicate

`to: [a, b, c]` syntactically resembles `type: conditional` routing (both involve lists of targets). The semantic difference is total: conditional routing picks one branch; parallel fan-out fires all. The implementation explicitly guards against treating one as the other via the `type: conditional` check.

## Insight

**Edge compilation is a boundary.** The graph YAML's `to:` field enters as a string or list; the compiled LangGraph must emit multiple `add_edge()` calls. The normalization must happen here, not in validation or execution.

## Heuristic

When extending an edge compiler, enumerate all existing edge cases upfront (regular, interrupt, map, START) and write a test for each before touching production code. Missing one case produces a silent wrong graph, not a crash.

## Seed

Could parallel fan-out edges support a `wait_all: true` flag to create a synchronization barrier — fanning out and then joining at a downstream node — without requiring a map node?
