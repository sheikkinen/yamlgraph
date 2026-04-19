# FR-253: A2A Consumer to Contrib — Reflection

**Date:** 2026-04-21
**FR:** FR-253 (A2A Consumer to Contrib)
**Duration:** ~2 hours

## Cognitive Process

The task was clear: demote a dedicated node type to a contrib function. The FR
was well-specified with phased approach. The main cognitive load was in the
breadth of touchpoints — not depth.

## Traps Encountered

### 1. Prerequisite Discovery (FR-252)
The FR stated FR-252 (python node `variables:`) as a dependency. Verifying this
was real — not assumed — required tracing through `python_tool.py` to confirm
`variables:` was indeed a no-op on python nodes. The W020 linter warning was the
proof. Fix was minimal (~6 lines) but without it the demo graph would silently
ignore its `variables:` config.

**Trap:** `working_system_inertia` — the linter *warned* but nobody *fixed*.
The warning existed since W020 was created, meaning the gap was known but
tolerated. FR-253 forced the cure.

### 2. Blast Radius of Removal
Removing `NodeType.A2A_CALL` touched 10+ files across 4 layers (constants,
compiler, linter, schema, factory, tests). Three tests in unrelated files
(`test_constants`, `test_node_type_registry`, `test_linter_contracts`)
referenced the deleted enum value. These were mechanical fixes, but discovering
them required running the full suite — grep alone wouldn't catch enum attribute
access patterns.

**Trap:** `partial_remediation` — easy to miss satellite tests when deleting a
cross-cutting concept.

### 3. Sync httpx vs A2A SDK Client
The FR suggested unifying on SDK `Client` for both paths. I preserved the split:
sync `httpx.post` for non-streaming (simpler, no event loop concerns) and SDK
`A2AClient` for streaming (needs async transport). The FR's suggestion would
have added unnecessary complexity for the non-streaming path.

**Cure:** `callsite_fix` — use the right tool for each path rather than
forcing uniformity.

## Insight

**Deletion is the highest-leverage refactor.** This FR deleted ~1789 net lines
while preserving identical functionality. The contrib function is ~230 lines vs
502 lines across the dedicated node type. The reduction came not from cleverer
code but from eliminating framework ceremony (enum, compiler handler, linter
patterns, schema fields) that a contrib function simply doesn't need.

## Heuristic

**framework_ceremony_ratio:** If a feature's framework glue (enum + compiler +
linter + schema) exceeds its logic by 2x, it's a contrib candidate. Measure
the ratio before promoting features to dedicated node types.

## Seed

Can we auto-detect framework ceremony ratio? A script that compares lines of
framework glue (constants, compiler registry, linter patterns, schema fields)
vs actual logic for each node type would surface promotion/demotion candidates
mechanically.
