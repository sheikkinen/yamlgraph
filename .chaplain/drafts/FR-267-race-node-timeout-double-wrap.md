# Feature Request: FR-267 Fix race node timeout: silent state loss from double ThreadPoolExecutor wrap

**Priority:** HIGH
**Type:** Bug
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-04-21

## Summary

Race nodes with `timeout:` in YAML silently lose their entire return value. The race node logs a winner, but all state updates (`state_key`, `_race_winner`, `current_step`, `_loop_counts`) are lost — downstream nodes see `None` or default values. No exception is raised.

## Value Statement

Graph authors using race nodes with `timeout:` get correct state propagation instead of silent data loss that masquerades as LLM/provider issues.

## Problem

`_compile_race_node` in `node_compiler.py` (line 277) wraps the race node function in `_maybe_wrap_timeout`, which creates an outer `ThreadPoolExecutor(max_workers=1)`. The race node _already_ uses its own `ThreadPoolExecutor` with `as_completed(timeout=...)` internally (lines 148–156 in `race_node.py`). This creates nested thread pools.

The nested-pool interaction silently discards the return value: the race node executes correctly, logs its winner, but LangGraph never receives the state update dict.

The `timeout` config key has **two distinct meanings** for race nodes:
1. **Intended (race-internal):** total race deadline via `as_completed(timeout=...)` — bounds how long to wait for candidates.
2. **Accidental (outer wrap):** wall-clock guard via `_maybe_wrap_timeout` — redundant because the race already bounds its own time.

Additionally, `race_node.py` does not catch `TimeoutError` from `as_completed`. The `for future in as_completed(futures, timeout=timeout)` loop raises `TimeoutError` when the deadline expires before all futures complete. This exception propagates _outside_ the `try/except Exception` block (which only wraps `future.result()`). Currently masked by the outer wrapper (which itself is broken for race nodes), this gap must be fixed when the outer wrapper is removed.

### Verification matrix

| `timeout:` on race node | Race logs winner | Downstream sees state | Result |
|--------------------------|:----------------:|:---------------------:|:------:|
| Present (current)        | ✓                | ✗ (`None`)            | **BUG** |
| Removed                  | ✓                | ✓                     | PASS   |

## Proposed Solution

Two changes, both in service of race-node timeout correctness:

### Change 1: Remove outer wrapper (`node_compiler.py`)

Remove the `_maybe_wrap_timeout` call from `_compile_race_node`. The race node's native `as_completed(timeout=...)` already enforces the timeout contract.

**Before (buggy):**

```python
def _compile_race_node(ctx: NodeCompileContext) -> None:
    node_fn = create_race_node(...)
    node_fn = _maybe_wrap_timeout(node_fn, ctx.node_config, ctx.node_name)  # ← bug
    ctx.graph.add_node(ctx.node_name, node_fn, cache_policy=ctx.cache_policy)
```

**After:**

```python
def _compile_race_node(ctx: NodeCompileContext) -> None:
    node_fn = create_race_node(...)
    # Race owns `timeout` natively via as_completed(timeout=...);
    # do NOT wrap in _maybe_wrap_timeout (nested pools drop return value).
    ctx.graph.add_node(ctx.node_name, node_fn, cache_policy=ctx.cache_policy)
```

### Change 2: Handle TimeoutError in race node (`race_node.py`)

Wrap the `for future in as_completed(...)` loop in a `try/except TimeoutError` block. On timeout expiry, cancel remaining futures and fall through to the all-failed handler:

```python
try:
    for future in as_completed(futures, timeout=timeout):
        candidate = futures[future]
        try:
            result = future.result()
            # ... existing winner logic ...
        except Exception as e:
            errors.append((candidate, e))
except TimeoutError:
    for f in futures:
        f.cancel()
    errors.append(({}, TimeoutError(f"Race {node_name} timed out after {timeout}s")))
```

This ensures timeout expiry produces a structured `PipelineError(TIMEOUT_ERROR)` via the existing `on_error` path, not a raw exception.

### Timeout semantics clarification

The race node `timeout` is a **total race deadline** — it bounds the maximum wall-clock time waiting for any candidate to succeed. This matches the `as_completed(timeout=...)` behavior. It is NOT a per-candidate timeout.

## Acceptance Criteria

- [ ] `_compile_race_node` does not call `_maybe_wrap_timeout`
- [ ] `race_node.py` catches `TimeoutError` from `as_completed` and returns structured error via `on_error` path
- [ ] Condemning test via **compile path**: race node with `timeout: N` where a candidate succeeds returns full state dict (`state_key`, `_race_winner`, `current_step`, `_loop_counts` all non-None)
- [ ] Condemning test: race node with `timeout: N` and `parse_json: true` returns parsed dict in state
- [ ] Test: race node with `timeout` where all candidates exceed deadline returns `PipelineError(TIMEOUT_ERROR)` when `on_error: skip`, raises when no `on_error`
- [ ] Regression test: race node **without** `timeout:` continues to work unchanged
- [ ] Existing race node tests pass (`tests/unit/test_race_node.py`)
- [ ] Linter tests pass (`tests/unit/test_linter_patterns_race.py`)
- [ ] `@pytest.mark.req("REQ-YG-266")` on new tests; REQ-YG-266 added to ARCHITECTURE.md, REQ-YG-233 amended
- [ ] CAP-119 capability YAML created in `capabilities/`
- [ ] `req_coverage.py` passes with `--strict`

## Requirement

**REQ-YG-266:** Race node applies exactly one timeout mechanism — its native `as_completed(timeout=...)`. The node compiler must not apply `_maybe_wrap_timeout` to race nodes. On timeout expiry (no candidate succeeds within deadline), the race node must produce a structured `PipelineError(TIMEOUT_ERROR)` and respect `on_error` configuration, not raise a raw exception.

**Amends REQ-YG-233:** Add: "Race node `timeout` is a total race deadline (not per-candidate). Timeout enforcement is internal to the race node; `_maybe_wrap_timeout` must not be applied."

**Amends REQ-YG-078 (CAP-96):** Narrow scope: "_maybe_wrap_timeout applies to non-map node types **except race**, which owns timeout natively."

## Alternatives Considered

1. **Fix `_maybe_wrap_timeout` to detect nested pools** — rejected. The outer wrapper is genuinely redundant for race nodes; adding detection complexity buys nothing. Other node types that lack native timeout handling still benefit from the wrapper.

2. **Add a `skip_timeout_wrap: true` flag to NodeCompileContext** — rejected. Over-engineering a one-off exclusion. A simple code-path skip is clearer than a metadata flag.

3. **Unwrap the race node's internal timeout and rely solely on `_maybe_wrap_timeout`** — rejected. The race node's `as_completed(timeout=...)` is semantically correct (it bounds the _race_, not the node). Replacing it with the outer wrapper would change timeout semantics and break `on_error` handling within the race.

4. **Separate FR for TimeoutError handling** — rejected. The gap is exposed directly by removing the outer wrapper. Shipping one without the other would regress timeout-expired behavior from "silently broken" to "raw exception". Both changes serve the same invariant: race node owns its timeout contract end-to-end.

## Related

- **Upstream issue:** [#152](https://github.com/sheikkinen/yamlgraph/issues/152)
- **Downstream project FR:** NV-240 in `sheikkinen/ninchat-voice`
- **Race node FR:** FR-264 (`parse_json` content normalization) — independent, already merged
- **Timeout FR:** FR-069 (per-node timeout bounding via `_maybe_wrap_timeout`, CAP-96)
- **Race node CAP:** CAP-91 (race node type, REQ-YG-233)
- **Key files:** `yamlgraph/node_compiler.py:270–279`, `yamlgraph/node_factory/race_node.py:90,148–156`

## Research Brief

### Competitive Landscape

- **LangGraph** (upstream): Uses `concurrent.futures.wait(FIRST_COMPLETED)` with a single `step_timeout` deadline per superstep. Timeout is total, not per-candidate — matching FR-267's intended semantics. Crucially, LangGraph uses **one** timeout mechanism, never nests thread pools. No known silent-state-loss bugs. ([source: `langgraph/pregel/_runner.py`](https://github.com/langchain-ai/langgraph))
- **CrewAI**: Sequential task execution model. No race/first-wins pattern. No explicit timeout mechanism found.
- **Microsoft AutoGen**: Multi-agent conversation model (message-based). No `FIRST_COMPLETED` race pattern. Agent-level timeouts exist but are not globally coordinated.
- **Google ADK**: Limited public code. No evidence of parallel-candidate racing with timeout.
- **OpenAI Agents SDK**: No race pattern. Early-stage SDK focused on agent chains.

**Verdict:** Only LangGraph supports first-success-wins racing. Its design validates FR-267's approach — a single native timeout mechanism without outer wrapping. Documenting an existing solution is not applicable here; this is a bug in YAMLGraph's own compile pipeline.

### Existing Abstractions

| Abstraction | File | Relevance |
|-------------|------|-----------|
| `_maybe_wrap_timeout` | `yamlgraph/node_compiler.py:102–148` | Root cause. Creates outer `ThreadPoolExecutor(max_workers=1)`. Applied to 6 node types; already skipped by map, interrupt, passthrough, copilot, subgraph. |
| `create_race_node` | `yamlgraph/node_factory/race_node.py:67–206` | Native `as_completed(timeout=...)` at line 156. Returns full state dict (lines 171–179). `TimeoutError` not caught (gap at line 156). |
| `_compile_race_node` | `yamlgraph/node_compiler.py:270–279` | Bug site: line 277 applies `_maybe_wrap_timeout` to race node, creating nested pools. |
| `ErrorType.TIMEOUT_ERROR` | `yamlgraph/models/schemas.py:~20` | Used by `_maybe_wrap_timeout` but NOT by race node for its internal timeout. FR-267 would add this. |
| `ErrorHandler` | `yamlgraph/constants.py:41–47` | Race node already respects `on_error` at lines 192–202. TimeoutError path needs to feed into this. |

**No duplication risk.** The fix removes a wrapper call and adds missing error handling — no new abstractions created.

### Diary Precedents

| Diary Entry | Pattern/Trap | Relevance |
|-------------|-------------|-----------|
| `2026-04-18-reflection-fr-232-race-node-type.md` | **Trap Avoided: False Completion** — `FIRST_COMPLETED ≠ first successful`. ThreadPoolExecutor chosen over asyncio. | Directly relevant: race node's ThreadPoolExecutor is the correct inner mechanism; outer wrap is redundant. |
| `2026-04-19-reflection-fr-069-map-node-timeout.md` | **Trap Avoided: Partial Remediation** — `_maybe_wrap_timeout` applied uniformly to avoid leaving node types unguarded. **Seed:** "Should timeouts feed into race node's winner-selection?" | FR-069's uniform application was correct for nodes without native timeout. Race is the exception — it already owns timeout. The seed foreshadows this FR. |
| `2026-04-21-reflection-fr-264-race-node-content-normalization.md` | **Trap: `downstream_fix`** — normalize at boundary, not downstream. | Same pattern: timeout enforcement belongs at the race boundary (inside `race_node.py`), not at the compiler boundary (`_maybe_wrap_timeout`). |
| `2026-03-12-nc150-fly-monitoring-debug.md` | **Trap: Silent Data Drop** — "Never silently drop data." | Exact symptom: race node logs winner but state updates silently lost. |
| `2026-04-19-inquisitor-audit-182.md` | **Drift: CAP-96 numbering collision** between FR-069 and FR-237. | Administrative precedent: verify CAP-119 number is unoccupied before creating. |

**Recurring pattern:** The One Law — "Normalize at the boundary where external data enters." Timeout is an internal race concern; enforcing it externally via `_maybe_wrap_timeout` violates boundary ownership.

### Usage Evidence

- **Existing graphs using race nodes:** 1 (`examples/demos/race/graph.yaml`)
- **Race nodes with `timeout:` configured:** 1/1 (100%) — `timeout: 15` with 3 candidates (mistral, openai, google)
- **Real-world use cases beyond the proposal:**
  - NV-240 in `sheikkinen/ninchat-voice` (downstream project, cited in FR)
  - Race node is designed for production hedging (multi-provider latency arbitrage) — low graph count reflects recent addition (FR-232, 2026-04-18), not low demand

### Classification Signal

- **Abstraction level:** primitive — the bug is in the compile pipeline (`node_compiler.py`), affecting all race nodes with `timeout:` config
- **Recommended approach:** build — this is a bug fix, not a new feature. Two surgical changes (remove wrapper call, add TimeoutError handling). Cannot be documented away; silent state loss is a correctness defect.
- **Key risk:** Removing the outer wrapper exposes the uncaught `TimeoutError` gap in `race_node.py`. Both changes must ship together (as FR correctly notes) to avoid regressing from "silent loss" to "raw exception."
