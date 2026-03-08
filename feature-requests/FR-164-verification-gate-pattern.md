# Feature Request: Verification Gate Pattern

**Priority:** MEDIUM
**Type:** Feature
**Status:** Approved
**Effort:** 3 days
**Requested:** 2026-03-08

## Summary

Add an optional `verification` field to node definitions that requires the LLM to state a falsifiable prediction before acting, then compares the prediction against the actual output at runtime.

## Value Statement

Graph authors gain automatic detection of silent failures — nodes that produce plausible but wrong results — by comparing stated expectations against actual outputs, turning invisible drift into observable discrepancies.

## Problem

Agents fail silently. When a filter yields nothing, they substitute defaults. When an LLM hallucinates, the output passes type validation because the shape is correct even when the content is wrong. Observability tools (LangSmith) show *what happened* but not *what was supposed to happen*. Without explicit expectations, you cannot distinguish correct behavior from lucky coincidence, or intentional fallback from silent failure.

From recurring diary seeds (Mar 2–8): "You don't know what your agent will do until it's in production."

Scripture: "A plausible wrong answer is harder to catch than a crash."

## Proposed Solution

### 1. Schema: `verification` field on nodes

Add an optional `verification` field to `NodeConfig` with three sub-fields:

```yaml
nodes:
  search:
    type: llm
    prompt: find_relevant_docs
    state_key: docs
    verification:
      question: "Will return 3-10 documents about {topic}"
      on_fail: warn  # warn | halt | retry
```

| Sub-field | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `question` | `str` | yes | — | Falsifiable prediction about the node's output. Supports `{var}` interpolation from state. |
| `on_fail` | `str` | no | `warn` | Action when prediction is violated: `warn` (log + continue), `halt` (raise), `retry` (re-execute node). |
| `max_retries` | `int` | no | `1` | Maximum retry attempts when `on_fail: retry`. Ignored for other modes. Falls through to `warn` after exhaustion. |

The `question` is a natural-language assertion. At runtime, after the node executes, the framework evaluates it against the actual output using deterministic checks (see §2).

### 2. Runtime: Deterministic verification

Verification happens **after** the node's `execute_prompt()` call returns, **before** the state update is committed. The evaluator extracts testable claims from the `question`:

| Claim pattern | Extraction | Check |
|---------------|-----------|-------|
| `"Will return N-M items"` | min/max from regex | `min <= len(result) <= max` |
| `"Will return non-empty"` | truthiness | `bool(result)` |
| `"Will contain {keyword}"` | substring | `keyword in str(result)` |
| Custom (no pattern match) | — | Always passes with info log |

When no deterministic pattern matches, the verification degrades to a logged annotation (the question is still recorded in the trace for human review). This avoids requiring an extra LLM call for evaluation.

### 3. Violation handling

On violation, behavior depends on `on_fail`:

- **`warn`** (default): Append a `VerificationViolation` to `state["errors"]`, log warning, continue execution.
- **`halt`**: Raise `VerificationError` (subclass of `PipelineError`). Graph stops.
- **`retry`**: Re-execute the node (up to `max_retries`, default 1). If retry also violates, fall through to `warn`.

```python
# New in yamlgraph/models/errors.py
class VerificationViolation(PipelineError):
    """A node's output violated its stated verification question."""
    prediction: str      # The original question
    actual: str          # String repr of actual output
    check_type: str      # "count_range" | "non_empty" | "contains" | "annotation"
```

### 4. Lint rule: W022 — `on_error: skip` without verification

A new lint rule warns when a node uses `on_error: skip` but has no `verification` field. Silent skips without stated expectations are the primary source of invisible failures.

```
W022: Node 'search' uses on_error: skip without verification question.
      Add verification.question to make skip behavior observable.
```

### Example

```yaml
nodes:
  fetch_articles:
    type: llm
    prompt: search_articles
    state_key: articles
    on_error: skip
    verification:
      question: "Will return non-empty list of articles about {topic}"
      on_fail: warn

  summarize:
    type: llm
    prompt: summarize_articles
    state_key: summary
    verification:
      question: "Will contain at least 100 characters"
      on_fail: halt
```

When `fetch_articles` returns `[]`, the trace logs:

```
⚠ Verification violated [fetch_articles]: predicted "Will return non-empty list of articles about AI",
  got [] (check: non_empty, on_fail: warn)
```

## Acceptance Criteria

- [ ] `NodeConfig` schema accepts optional `verification` field with `question` (str, required) and `on_fail` (str, optional, default `warn`)
- [ ] `on_fail` validated to `{"warn", "halt", "retry"}` with Pydantic validator
- [ ] Runtime evaluator extracts deterministic checks from `question` text (count range, non-empty, contains)
- [ ] Unrecognized patterns degrade to annotation (info log, no failure)
- [ ] `warn` appends `VerificationViolation` to `state["errors"]` and continues
- [ ] `halt` raises `VerificationError` (subclass of `PipelineError`)
- [ ] `retry` re-executes node up to `max_retries` times, then falls through to `warn`
- [ ] Lint rule W022 warns on `on_error: skip` without `verification`
- [ ] Variable interpolation (`{var}`) works in `question` from current state
- [ ] Tests added (unit: evaluator patterns, integration: node with verification, lint: W022)
- [ ] Documentation updated (`reference/graph-yaml.md`)

## Alternatives Considered

1. **LLM-as-judge evaluation**: Use a second LLM call to evaluate whether the prediction holds. Rejected: adds latency, cost, and non-determinism. The deterministic pattern-matching approach covers the most common cases (empty results, wrong counts) without extra calls.

2. **Dedicated `type: verification_gate` node**: A separate node type that sits after an LLM node and checks its output. Rejected: adds graph complexity (double the nodes) and separates the expectation from the node it describes. Inline `verification` keeps the contract co-located.

3. **Graph-level `verification_question`**: A single verification for the entire graph's success criteria. Rejected: too coarse — you lose per-node attribution of failures. Can be added later as a complement.

4. **Lint rule only (no runtime)**: Only warn statically about `on_error: skip` without verification. Rejected as insufficient alone: lint can flag the pattern but cannot detect runtime violations. The lint rule (W022) is included as a complement, not a replacement.

## Relationship to Existing Features

| Feature | Relationship |
|---------|-------------|
| **FR-051** (Output Shape Contracts) | Complementary. FR-051 validates output *shape* (min_length, min_items) at graph completion. Verification gates validate *execution correctness* per-node at runtime. If FR-051 is implemented, `verification` could delegate shape checks to its evaluator. |
| **FR-061** (Contract Violation Lint Rules) | Complementary. FR-061 catches bad *configs* statically. Verification gates catch bad *executions* at runtime. W022 extends FR-061's lint suite. |
| **FR-027** (Execution Safety Guards) | Complementary. FR-027 prevents *runaway* execution (timeouts, loops, fan-out). Verification gates prevent *incorrect* execution (wrong results, empty outputs). |
| **`on_error`** mechanism | Extends. Verification runs *after* successful execution (on_error handles failures). A node can succeed (no exception) but still violate its verification. |

## Implementation Notes

- Verification evaluator belongs in `yamlgraph/verification.py` (new module, <200 lines)
- Integration point: `node_factory/llm_nodes.py`, after `execute_prompt()` returns, before building state update dict
- Lint rule W022 goes in `yamlgraph/linter/checks_contracts.py` alongside W020/W021
- `VerificationViolation` extends `PipelineError` in `yamlgraph/models/errors.py`

## Judgement

**Verdict:** APPROVE — Scope frozen, authority granted.

**Reviewed:** 2026-03-08

**Findings:**

1. **Scope** — Clear and minimal. Single responsibility: per-node runtime verification with deterministic pattern matching. The lint rule (W022) is tightly coupled to the core feature and belongs here.
2. **Contradictions** — None found. `on_error` (handles execution exceptions) and `verification` (handles successful-but-wrong outputs) are cleanly orthogonal.
3. **Acceptance criteria** — All 11 criteria are specific and testable. No ambiguity in pass/fail conditions.
4. **Feasibility** — Confirmed by architectural review. `NodeConfig` is extensible, the hook location in `llm_nodes.py` (after `execute_prompt()`, before state update) is clear, lint rule follows established W020/W021 pattern, error model is extensible. 3-day effort estimate is credible.
5. **Architectural alignment** — Complements FR-051 (graph-level shape contracts), FR-061 (static config lint), and FR-027 (execution safety guards) without overlap. No breaking changes required.
6. **Amendment applied** — Added `max_retries` sub-field to the schema table (§1). It was referenced in §3 and acceptance criteria but missing from the schema definition. Default: 1, only relevant when `on_fail: retry`.

**Scope note:** Initial integration targets `llm_nodes.py`. Extension to other node types (router, map, agent) is a natural follow-up but not in scope for this FR.

## Related

- `feature-requests/051-output-shape-contracts.md` — Complementary output validation
- `feature-requests/061-contract-violation-lint-rules.md` — Existing contract lint rules (W020, W021, E012)
- `feature-requests/027-execution-safety-guards.md` — Existing execution guards
- `yamlgraph/models/graph_schema.py` — NodeConfig schema (integration point)
- `yamlgraph/node_factory/llm_nodes.py` — Node execution (integration point)
- `yamlgraph/linter/checks_contracts.py` — Lint rules (integration point)
- Scripture: "A plausible wrong answer is harder to catch than a crash"
