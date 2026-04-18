# Diary: FR-235 Compile-Time Pipeline Templates

**Date:** 2026-04-18
**FR:** FR-235
**Author:** Copilot

## Cognitive Process

The pipeline template feature required careful boundary thinking: the expansion
must happen at compile time (graph_loader), not at runtime (executor). This
distinction kept the implementation clean — pipeline nodes never exist at
execution time, only their expanded concrete nodes do.

## Trap Encountered: framework_costume

Initial instinct was to implement pipeline as a runtime node type that
iterates internally. Recognizing this as "FSM wearing DAG costume" — the
sequential nature of pipelines maps naturally to LangGraph's edge system.
Expanding at compile time leverages the existing graph infrastructure rather
than reimplementing sequencing logic inside a node function.

## Insight

Compile-time expansion is the cleanest form of the "normalize at the boundary"
principle. The pipeline YAML is the external input; `expand_pipelines()` is the
boundary function; everything downstream sees only standard nodes and edges.

## Heuristic

**Meta-node expansion > runtime orchestration**: When a new "node type" is
really a pattern over existing node types, expand it at compile time rather
than adding runtime complexity. The expansion function is easier to test,
debug, and lint than a runtime orchestrator.

## Seed

Could other meta-node patterns (fan-out/fan-in, retry chains, A/B splits)
follow the same compile-time expansion model? A `type: sequence` or
`type: chain` could be syntactic sugar for common multi-node patterns,
all resolved before the graph reaches LangGraph.
