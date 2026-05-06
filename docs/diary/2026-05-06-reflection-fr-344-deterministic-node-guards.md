# Reflection: FR-344 Deterministic Node Guards

**Date:** 2026-05-06
**FR:** FR-344 — Deterministic node guards with pre/post assertion support
**Reviewer:** watcher2 (post-validate remediation)

## What Happened

FR-344 introduced a `guards:` field on `NodeConfig` with `pre` and `post` guard lists.
Each guard rule carries a `check` expression, an `on_fail` policy (`warn | halt | skip`
for pre; `warn | halt | retry` for post), an optional `message`, and an optional
`max_retries` for `post` + `retry` rules. A new safe AST-based evaluator
(`yamlgraph/utils/guard_evaluator.py`) handles expression parsing without `eval()`.
Runtime integration covers the `llm/router` path (via the new `llm_execution.py`
helper) and the `copilot` node. The linter gained `W025` to flag invalid guard
expressions before graph execution.

## Traps Encountered

### `framework_costume`

The initial instinct was to reuse `evaluate_condition` from `yamlgraph/utils/conditions.py`
unchanged. That function handles edge-routing expressions but has no concept of `output`
context or pipe-filter semantics (`| file_exists`, `| length`). Trying to graft guard
semantics on top would have made the routing evaluator carry dual responsibility. The
correct move was a dedicated evaluator at the same boundary — same safe-AST discipline,
different input context.

### `intent_drift`

The FR specified `W025` explicitly (noting the W024 collision risk with FR-320 unused
context variables). An early draft of `checks_contracts.py` used `W024`, which would
have caused a lint code collision. Re-reading the FR specification before merging
caught this before it reached CI.

### `symptom_patch` risk

Post-guard `retry` is bounded by `max_retries` (default 1). The original spec was
silent on what happens when retries are exhausted: raise `GuardViolation` and surface
it in the `errors` list, not silently return the last output. Verifying against the
error model spec before writing the runtime prevented a plausible-wrong-answer outcome.

## What Worked

- Writing acceptance tests RED before implementation kept scope contained. The seven
  specified tests acted as precise contracts throughout.
- Separating `llm_execution.py` from `llm_nodes.py` improved the cohesion of both
  modules and made the guard integration point explicit and testable in isolation.
- The linter `W025` check reuses the same `parse_guard_expression()` path the runtime
  uses, so lint and runtime stay in sync automatically.

## Seed

Guard expressions currently support a fixed set of pipe-filters (`length`, `file_exists`,
`dir_exists`, `type`, `keys`). Could the evaluator support user-registered filter
functions injected at graph-compile time, enabling domain-specific predicates without
broadening the attack surface? This would let graph authors define project-level
invariants (e.g., `| valid_fr_path`) without modifying framework code.
