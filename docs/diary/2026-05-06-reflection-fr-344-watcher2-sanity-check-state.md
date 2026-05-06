# Watcher2 Sanity Check: FR-344 Deterministic Node Guards

**Date:** 2026-05-06
**FR:** FR-344 — Deterministic node guards (`guards.pre` / `guards.post`)
**Reviewer:** watcher2 (post-validate, independent review)

## Proportionality

1627 additions / 245 deletions across 28 files for a 3-day feat. Scope matches the
FR acceptance criteria exactly. New modules are single-responsibility:

- `guard_evaluator.py` (222 lines) — AST evaluator, no eval/Jinja2
- `guard_runtime.py` (134 lines) — shared pre/post guard evaluation loop
- `llm_execution.py` (147 lines) — extracted from the previously monolithic `llm_nodes.py`

The `llm_nodes.py` net change is a refactor + guard integration; module length stays
within the 450-line limit. No speculative abstractions or scope creep detected.

## Test Quality

All 7 FR-specified acceptance tests exist and pass. Tests probe behavioral boundaries:

| Test | What it checks |
|------|----------------|
| `test_pre_guard_halt_prevents_execute_prompt` | `execute_prompt` not called on halt |
| `test_post_guard_retry_reexecutes_until_pass_or_exhausted` | call count (2), success path AND exhaustion path |
| `test_pre_guard_skip_returns_explicit_skipped_metadata` | `_skipped`, `_skip_reason`, `state_key=None` |
| `test_copilot_pre_guard_halt_prevents_subprocess_run` | `subprocess.run` not called |
| `test_guard_expression_supports_filters_and_membership` | all filters + `in`, `and`, `>=`, `| keys` |
| `test_guard_evaluator_rejects_unsafe_or_unknown_syntax` | `__import__`, unknown filter, syntax error |
| `test_w025_invalid_guard_expression_warning` | lint code `W025` + message substring |

No assertions check internal state counters or implementation details. Assertions are
at the external contract boundary. The retry exhaustion test covers both the success
re-entry path and the budget-exhausted path in a single test — good density.

Broader suite: 3628 passed, 0 failed, 119 skipped, 1 xfailed (pre-existing).

## FR / Code Alignment

Every acceptance criterion maps to a test and a production file:

| AC | File | Test |
|----|------|------|
| Schema validation | `models/graph_schema.py` | `test_node_config_guards_pre_post_validation` |
| Safe evaluator | `utils/guard_evaluator.py` | `test_guard_expression_supports_filters_and_membership`, `test_guard_evaluator_rejects_unsafe_or_unknown_syntax` |
| Pre halt — llm/router | `node_factory/llm_execution.py` + `llm_nodes.py` | `test_pre_guard_halt_prevents_execute_prompt` |
| Pre halt — copilot | `node_factory/copilot_node.py` | `test_copilot_pre_guard_halt_prevents_subprocess_run` |
| Pre skip metadata | `node_factory/llm_execution.py` | `test_pre_guard_skip_returns_explicit_skipped_metadata` |
| Post retry | `node_factory/guard_runtime.py` + `llm_execution.py` | `test_post_guard_retry_reexecutes_until_pass_or_exhausted` |
| `GuardViolation` + `GUARD_ERROR` | `models/schemas.py` | multiple test assertions |
| `W025` linter | `linter/checks_contracts.py` | `test_w025_invalid_guard_expression_warning` |
| `reference/graph-yaml.md` docs | diff confirmed | — |
| `examples/demos/guards/` demo | demo-output.log present | — |

No criterion is unimplemented. No code exists outside the AC scope.

## Trap

### `infrastructure_self_exempt` (near-miss)

The linter `check_guard_expressions` function uses the same `validate_guard_expression`
parser path as the runtime evaluator. The risk was implementing a separate syntax check
in the linter that could diverge from the runtime. Using the shared path eliminates
that drift point.

## Pipeline Log Evidence

No FSM pipeline log found for this run (`logs/` directory empty). Review is based on
diff, test output, and direct code inspection.

## Seed

Guard `pre` and `post` rules are evaluated independently per-node. If a graph has many
guarded nodes with overlapping expression predicates, the same expression may be
evaluated redundantly. Could the evaluator be made composable enough to support a
shared guard predicate registry at graph-compile time, caching parsed AST trees for
reuse across nodes without changing the determinism guarantee?
