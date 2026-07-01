# The Unwitnessed Garden

**Date:** 2026-07-01
**Context:** Examples analysis session — discovered test coverage exists but demo coverage does not.

## Observation

The project has:
- `pytest --cov` for source code (80% threshold enforced by CI)
- `demo-gate` requiring `demo-output.log` to prove a demo ran
- `vulture` for dead code in `yamlgraph/`

But nothing that detects **unreachable yet valid-looking code in examples**:
- A demo's `graph.yaml` could reference a prompt that doesn't exist (caught by `lint`)
- A demo's `graph.yaml` could reference a Python tool module that imports fine but whose function signature drifted
- A demo's Python node could contain logic branches that no variable combination ever exercises
- A top-level example's `nodes/*.py` could contain functions that no graph.yaml references anymore

The `demo-output.log` gate checks "did it run?" — but not "did all of it run?" A graph with 5 nodes where only 3 execute still produces output and passes the gate.

## The Gap

| What | Source coverage | Example coverage |
|------|----------------|-----------------|
| Dead functions | vulture | nothing |
| Unreachable branches | pytest + coverage | nothing |
| Unused prompts | nothing | nothing |
| Orphan tool modules | nothing | nothing |
| Nodes never reached by any edge path | graph lint (partial) | nothing |

The 46k LOC in examples has zero coverage instrumentation. Valid-looking code accumulates because nothing proves it executes.

## Trap

**`detection_without_enforcement`** — Unit tests prove code compiles in isolation. But `create_streaming_node()` passed all its unit tests while being unreachable from any real execution path. The missing detection: no demo exercises it, therefore no integration path proves it works. The demo garden IS the integration coverage — and we weren't measuring it.

## Heuristic

**Demo coverage = lint + execution + path coverage.** Currently we have lint (partial) and execution (presence of output). Path coverage — "did every node in graph.yaml get visited at least once across all demo runs?" — is missing entirely.

## The Real Finding

The demo garden's purpose isn't just teaching users — it's **the integration test suite for the framework itself**. Every framework feature that lacks a demo is untested at the integration level.

`create_streaming_node()` survived for months as dead code because no demo exercised it. If there had been a demo requiring `stream: true` to work, the breakage would have surfaced immediately. The demos are — or should be — **executable proof that core code is reachable**.

The correct framing: **every public API surface and node type in `yamlgraph/` must have at least one demo that exercises it.** The gap isn't "demos lack coverage" — it's "framework code lacks demo witnesses." Unit tests mock; demos prove the real path works end-to-end.

Missing demos = undetected dead core code:
- `stream: true` → dead (no demo, no consumer)
- `passthrough` node type → no demo (is it dead?)
- `tool_call` node type → no demo (is it dead?)
- `pipeline` node type → no demo (is it dead?)

## Heuristic

**A framework feature without a demo is a hypothesis, not a feature.** Unit tests prove the code compiles. Demos prove it works. The demo garden is the integration coverage report — gaps in the garden are gaps in the proof.

## Seed

**Could `vulture` be extended (or a sibling script created) to cross-reference `NodeType` enum members against `examples/demos/*/graph.yaml` node types — and fail CI when a node type has zero demo coverage?**
