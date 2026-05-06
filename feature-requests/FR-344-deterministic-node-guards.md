# Feature Request: Deterministic Node Guards (FR-344)

**Priority:** HIGH
**Type:** Enhancement
**Status:** Implemented
**Effort:** 3 days
**Requested:** 2026-05-06

## Summary

Add a `guards:` field to node config so graphs can enforce deterministic pre/post assertions without extra LLM calls. This extends the current `requires:` and `verification:` model with expression-based checks that can halt, warn, skip, or retry based on explicit policy.

## Value Statement

Graph authors get fast, deterministic failure signals before expensive node execution and stronger post-execution correctness checks, reducing wasted runtime and plausible-wrong outputs.

## Problem

Current guard surfaces are partial and split:

1. `requires:` only checks key presence (`state.get(key) is not None`) and cannot assert value constraints such as path existence, length, or threshold checks (`yamlgraph/error_handlers.py`).
2. `verification:` is post-execution only and supports only three deterministic patterns (`count_range`, `non_empty`, `contains`), so checks like `output.score >= 0.7` are not expressible (`yamlgraph/verification.py`).
3. Safe expression evaluation already exists for edge routing (`evaluate_condition`) but is not available as a node-level guard contract (`yamlgraph/utils/conditions.py`, `yamlgraph/routing.py`).
4. Runtime fallback paths can still produce low-signal outcomes (e.g., router default routing and map empty fan-out) without a first-class node-guard contract.

This leaves a gap between "node can run" and "node should run / output is valid."

## Proposed Solution

Introduce a typed `guards:` field on nodes with deterministic evaluation at runtime.

```yaml
nodes:
  enforce:
    type: copilot
    guards:
      pre:
        - check: "state.fr_path | file_exists"
          on_fail: halt
          message: "FR file not found: {state.fr_path}"
      post:
        - check: "output.summary | length < 500"
          on_fail: warn
          message: "Summary too long"
```

### 1. Schema

Add to `NodeConfig`:

- `guards.pre`: list of guard rules (optional)
- `guards.post`: list of guard rules (optional)

Guard rule shape:

- `check: str` (required)
- `on_fail: str` (required, phase-constrained)
- `message: str | None` (optional)
- `max_retries: int` (optional, only for `post` + `retry`, default `1`)

Phase/action rules:

- Pre: `warn | halt | skip`
- Post: `warn | halt | retry`

Invalid combinations are schema errors (not runtime warnings).

### 2. Guard expression language (deterministic, no eval/Jinja2)

Supported:

- References: `state.<path>`, `output`, `output.<path>`
- Comparisons: `==`, `!=`, `<`, `>`, `<=`, `>=`, `in`, `not in`
- Logic: `and`, `or`, `not`
- Filters: `| length`, `| file_exists`, `| dir_exists`, `| type`, `| keys`
- Literals: `str`, `int`, `float`, `bool`, `None`, list literals

Implementation constraint: evaluator must be deterministic and safe (AST walk or equivalent parser), reusing existing boundary helpers where possible (`resolve_state_path`, literal parsing helpers).

### 3. Runtime integration

In scope for FR-344:

- `llm`/`router` execution path (`yamlgraph/node_factory/llm_nodes.py`)
- `copilot` node execution path (`yamlgraph/node_factory/copilot_node.py`)

Execution order:

1. Evaluate pre-guards
2. If pre passes, execute node
3. Evaluate post-guards on normalized `output`
4. Apply policy (`warn`/`halt`/`skip`/`retry`)
5. Return explicit state updates/errors (no silent fallbacks)

`retry` re-executes node and re-evaluates post-guards until pass or retries exhausted.

### 4. Error model

Add `GuardViolation` model (extends `PipelineError`) with fields:

- `phase` (`pre`/`post`)
- `check`
- `actual`
- `on_fail`
- `message`

Add `GUARD_ERROR` to `ErrorType`.

### 5. Linting

Add lint warning `W025` for guard configs that parse in YAML but are not executable as guard expressions (invalid syntax, unknown filter, invalid phase/action pairing if not blocked earlier).

**Note**: Originally planned as `W024` but conflicts with existing planning in `.chaplain/done/gh-320.md` for unused context variables. Using `W025` to avoid collision.

### 6. Documentation and demo

- Update `reference/graph-yaml.md` with `guards` schema and examples.
- Add demo at `examples/demos/guards/` for pre and post guard patterns.

### Scope boundaries

Out of scope (follow-up FR): runtime guard execution for `map`, `tool`, `python`, `agent`, `subgraph`, and `interrupt` node types.

## Acceptance Criteria

- [x] `NodeConfig` accepts `guards.pre`/`guards.post` with strict validation of phase/action combinations.
- [x] Deterministic guard evaluator supports listed operators, logic, and filters without using `eval()`/Jinja2.
- [x] Pre-guard `halt` blocks node execution in both `llm/router` and `copilot` paths.
- [x] Pre-guard `skip` returns explicit skipped state metadata (no external call is made).
- [x] Post-guard `retry` re-executes node until pass or retry budget exhaustion, then surfaces violation.
- [x] Guard failures produce `GuardViolation` with `ErrorType.GUARD_ERROR`.
- [x] Linter emits `W025` for invalid guard expressions/config and includes actionable fix text.
- [x] `reference/graph-yaml.md` documents `guards` and includes at least one pre + one post example.
- [x] `examples/demos/guards/` added with runnable graph and expected behavior.

### Failing acceptance tests (RED first)

These tests must be written first and fail on current main before implementation.

**Note**: Create `tests/unit/test_guard_evaluator.py` infrastructure file first to avoid import errors.

- [x] `tests/unit/test_graph_schema.py::test_node_config_guards_pre_post_validation`
- [x] `tests/unit/test_guard_evaluator.py::test_guard_expression_supports_filters_and_membership`
- [x] `tests/unit/test_guard_evaluator.py::test_guard_evaluator_rejects_unsafe_or_unknown_syntax`
- [x] `tests/unit/test_llm_node_phases.py::test_pre_guard_halt_prevents_execute_prompt`
- [x] `tests/unit/test_llm_node_phases.py::test_post_guard_retry_reexecutes_until_pass_or_exhausted`
- [x] `tests/unit/test_copilot_node.py::test_copilot_pre_guard_halt_prevents_subprocess_run`
- [x] `tests/unit/test_linter_contracts.py::test_w025_invalid_guard_expression_warning`

## Alternatives Considered

1. **Extend `requires:` only**
   Rejected: still only pre-check semantics and no post-output assertions.

2. **Extend `verification:` with more regex patterns**
   Rejected: keeps natural-language parsing fragility and does not provide pre-execution checks.

3. **Use LLM-as-judge for guard evaluation**
   Rejected: adds cost/latency and non-determinism in the guard layer.

4. **Reuse routing `evaluate_condition` unchanged**
   Rejected: useful baseline, but current grammar lacks output context and pipe-filter semantics needed for guard use cases.

## Related

- Issue: https://github.com/sheikkinen/yamlgraph/issues/344
- `feature-requests/FR-164-verification-gate-pattern.md`
- `feature-requests/027-execution-safety-guards.md`
- `yamlgraph/error_handlers.py` (`check_requirements`)
- `yamlgraph/verification.py` (`evaluate_verification`)
- `yamlgraph/utils/conditions.py` (`evaluate_condition`)
- `yamlgraph/node_factory/llm_nodes.py`
- `yamlgraph/node_factory/copilot_node.py`
