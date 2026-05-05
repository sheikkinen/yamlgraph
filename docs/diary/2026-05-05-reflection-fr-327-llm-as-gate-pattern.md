# Reflection: FR-327 LLM-as-gate Pattern Reference

**Date:** 2026-05-05
**FR:** FR-327 reference doc for LLM-as-gate pattern
**Reviewer:** watcher2 (post-validate)

## Trap

`framework_costume` — There was an initial impulse to introduce a first-class
`semantic_gate` primitive. Closer inspection showed the framework already
provides the full composition via `type: router` + structured schema +
`pass`/`fail` routing edges. Introducing a new primitive would have been a
FSM wearing a DAG costume: the right answer was already there, just undiscovered.

## What Happened

GitHub issue #327 requested a dedicated reference for the "LLM-as-gate" pattern.
The gap was documentation and discoverability, not runtime capability. The
implementation stayed strictly in scope:

- Created `reference/patterns/llm-as-gate.md` with problem framing, YAML
  graph snippet, prompt schema snippet, semantic-vs-deterministic guidance,
  and composition guidance (chaining, fallback, retry).
- Added a link from `reference/README.md`.
- Added unit tests (`test_fr327_llm_as_gate_pattern_docs.py`) that enforce
  all eight acceptance criteria mechanically.

No new node types, action types, or runtime behavior were added.

## Root Cause

The documentation gap arose because existing pattern docs (`reference/patterns.md`)
covered conditional routing and map-output quality gates separately, but never
isolated the binary semantic verdict (`pass|fail` + `reason`) pattern as a
reusable building block. Without a dedicated page, graph authors searching for
"semantic gate" had no single reference to anchor on.

## What Worked

- Treating this as a documentation task from the start prevented scope creep.
- Acceptance tests as the contract (not advisory) ensured the doc contains the
  required tokens before the PR can merge.
- The `spec_kill` principle applied cleanly: the cheapest gate is the one in the spec.

## Heuristic

*When a proposed primitive duplicates existing composition, write the pattern
doc first. If the doc requires no new runtime, the primitive is never needed.*

## Seed

Could the pattern library (`reference/patterns/`) benefit from a machine-readable
index (e.g., `patterns/index.yaml`) that tags each pattern by category, primitives
used, and applicable problem classes — enabling `yamlgraph pattern search semantic`
as a future CLI subcommand?
