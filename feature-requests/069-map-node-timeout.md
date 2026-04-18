# Feature Request: FR-069 Per-Node Timeout for Map Branches

**Priority:** MEDIUM
**Type:** Feature
**Status:** Approved
**Effort:** 2 days
**Requested:** 2026-02-21

## Summary

Add an optional `timeout: float | None` field (seconds) to `NodeConfig` so that individual map branches — and any node — can be bounded. A stalled map branch currently blocks aggregation indefinitely; the global `config.timeout` is too coarse to handle per-item slowness gracefully.

## Value Statement

Graph authors gain per-branch deadline control so one slow LLM call cannot stall the entire map aggregation, enabling graceful degradation via the existing `on_error` policy.

## Problem

Map nodes fan out via LangGraph's `Send()` API. Every branch runs concurrently, but there is no per-branch deadline:

- A single slow LLM call (e.g. a large agent sub-node) stalls the entire `collect` step.
- The global `config.timeout` kills the whole graph, discarding results from already-completed branches.
- `on_error: skip` cannot catch a timeout that never raises — the branch just hangs.

Concrete failure mode:

```yaml
nodes:
  analyze_all:
    type: map
    over: "{state.articles}"   # 20 items
    as: article
    node:
      type: agent              # May hang on tool calls
      prompt: deep_analysis
      state_key: analysis
    collect: analyses
    on_error: skip
```

If one agent branch hangs for 5 minutes the graph waits regardless of `on_error: skip`.

## Proposed Solution

Generalize the existing `NodeConfig.timeout` field (currently scoped to copilot nodes only, `int | None`) to `float | None` and apply it to all node types. When present:

1. The node's execution is wrapped via `concurrent.futures.Future.result(timeout=node.timeout)`, using a one-shot `ThreadPoolExecutor`. This primitive is chosen because all node functions produced by `node_factory/` are synchronous (`node_fn(state: dict) -> dict`) and run the same way on both the sync (`invoke`) and async (`ainvoke`) paths — there is no coroutine to wrap.
2. On `concurrent.futures.TimeoutError`, a dedicated `except concurrent.futures.TimeoutError` clause (placed **before** `except Exception`) catches it and raises `PipelineError` constructed via `PipelineError.from_exception(e, node="map_subnode", error_type=ErrorType.TIMEOUT_ERROR)`. Passing `error_type` explicitly bypasses the `from_exception` inference chain, which would otherwise classify this as `LLM_ERROR` because `"timeout"` appears in `TimeoutError.__name__.lower()`.
3. The existing `on_error` policy (`skip`, `retry`, `fail`, `fallback`) applies uniformly.

### YAML interface

```yaml
nodes:
  analyze_all:
    type: map
    over: "{state.articles}"
    as: article
    timeout: 30.0             # Each branch must complete in 30 s
    on_error: skip            # Timed-out branches are skipped, not fatal
    node:
      type: agent
      prompt: deep_analysis
      state_key: analysis
    collect: analyses
```

```yaml
nodes:
  slow_call:
    type: llm
    prompt: big_summary
    state_key: summary
    timeout: 60.0             # Works on any node type, not only map
```

### Implementation

#### Step 1 — `models/graph_schema.py`

Widen the existing `timeout` field from `int | None` (copilot-only) to `float | None` with a `@field_validator` asserting `timeout > 0`. Update the description to reflect general-purpose use. The copilot node path (`node_factory/copilot_node.py`) already reads `config.get("timeout")` and will continue to work unchanged.

#### Step 2 — `models/schemas.py`

Add `TIMEOUT_ERROR = "timeout_error"` to `ErrorType`. Do **not** modify `from_exception` classification logic; transient LLM API timeouts (`ReadTimeout`, `ConnectTimeout`, `httpx.TimeoutException`) must continue to be classified as `LLM_ERROR` so retry logic is unaffected. Callers must pass `error_type=ErrorType.TIMEOUT_ERROR` explicitly when catching `concurrent.futures.TimeoutError`.

#### Step 3 — `map_compiler.py` — `wrap_for_reducer` + call site

Accept optional `timeout: float | None = None` parameter in `wrap_for_reducer`. When set, execute `node_fn(state)` via a one-shot `ThreadPoolExecutor`. The `except concurrent.futures.TimeoutError` clause must appear **before** `except Exception` to prevent the general handler from silently reclassifying it as `LLM_ERROR`:

```python
def wrap_for_reducer(
    node_fn, collect_key, state_key, flatten_output=False, timeout=None
):
    def wrapped(state):
        try:
            if timeout is not None:
                with ThreadPoolExecutor(max_workers=1) as pool:
                    result = pool.submit(node_fn, state).result(timeout=timeout)
            else:
                result = node_fn(state)
        except concurrent.futures.TimeoutError as e:
            from yamlgraph.models import PipelineError
            error_result = {
                "_map_index": state.get("_map_index", 0),
                "_error": f"Branch timed out after {timeout}s",
                "_error_type": "TimeoutError",
            }
            return {
                collect_key: [error_result],
                "errors": [PipelineError.from_exception(
                    e, node="map_subnode",
                    error_type=ErrorType.TIMEOUT_ERROR,
                )],
            }
        except Exception as e:
            # existing handler unchanged
            ...
        ...
    return wrapped
```

Update the call site in `compile_map_node` (currently line ~267):

```python
# Before
wrapped_node = wrap_for_reducer(sub_node, collect_key, state_key, flatten_output)
# After
wrapped_node = wrap_for_reducer(
    sub_node, collect_key, state_key, flatten_output,
    timeout=config.get("timeout"),
)
```

#### Step 4 — `node_factory/` base execution path (`create_node_function`)

Apply the same `ThreadPoolExecutor` wrap in `llm_nodes.py` `create_node_function` when `cfg.timeout` is set, bounding non-map nodes (llm, tool_call, python, agent). Same clause ordering: `except concurrent.futures.TimeoutError` before `except Exception`.

#### Step 5 — Lint rule

Add a W203 warning in `yamlgraph/linter/patterns/map.py` inside `check_map_node_types` (or a new helper called from `check_map_patterns`): emit a warning when a map node contains a `type: agent` sub-node but no `timeout` is set. The `check_map_patterns` function and `map.py` file already exist — no new file creation needed, just extend the existing checks.

Thread pool is created per-call (one-shot); no global pool is held.

### Known Limitations

When `Future.result(timeout=N)` raises `TimeoutError`, the submitted thread is **not** cancelled — it continues running until the callable returns naturally or the process exits. Python daemon-thread semantics prevent interpreter-shutdown blocking, but within a long-lived process a high rate of timeouts may accumulate background threads. Cancellable futures are out of scope for this FR; a follow-on FR may address this using `ctypes`-based thread interruption or structured concurrency.

## Acceptance Criteria

- [ ] `NodeConfig.timeout` widened from `int | None` (copilot-only) to `float | None` (general-purpose), validated as a positive float via `@field_validator`
- [ ] Map branch honours `timeout`; a branch exceeding it raises `PipelineError` via `PipelineError.from_exception(e, node="map_subnode", error_type=ErrorType.TIMEOUT_ERROR)`
- [ ] `on_error: skip` on a map node successfully skips timed-out branches and collects the rest
- [ ] Non-map nodes (llm, tool_call, python, agent) also respect `timeout` when set
- [ ] `TIMEOUT_ERROR = "timeout_error"` is a distinct `ErrorType` value in `models/schemas.py`
- [ ] `from_exception` classification logic is **not** modified; callers pass `error_type=ErrorType.TIMEOUT_ERROR` explicitly
- [ ] `except concurrent.futures.TimeoutError` appears **before** `except Exception` in both `wrap_for_reducer` and the non-map node execution path, preventing silent reclassification as `LLM_ERROR`
- [ ] `compile_map_node` call site updated to pass `timeout=config.get("timeout")` to `wrap_for_reducer`
- [ ] Lint warning W203 emitted when a map node contains an agent sub-node without `timeout`
- [ ] Unit tests added with a mock that simulates a hung call using `time.sleep` inside the node fn
- [ ] Integration test (marked `slow`) demonstrating skip behaviour via a `sleep`-based tool node without network I/O
- [ ] All new tests carry `@pytest.mark.req("REQ-YG-238")` referencing a new requirement added to `ARCHITECTURE.md`
- [ ] `capabilities/` registry extended with a new `CAP-96-per-node-timeout.yaml` entry mapping to `REQ-YG-238`
- [ ] Known thread-leakage limitation documented in `reference/graph-yaml.md` alongside the `timeout` field docs
- [ ] Existing copilot node timeout behaviour is unchanged (regression-free)

## Alternatives Considered

**Global timeout only (`config.timeout`)**: Too blunt — kills the entire graph and discards partial results. Rejected.

**`asyncio.wait_for(coro, timeout=…)`**: Inapplicable — node functions are synchronous on both the sync and async execution paths; there is no coroutine to wrap.

**`anyio.move_on_after(timeout)`**: Would work only inside the async path (`run_graph_async`/`ainvoke`); breaks the sync path. Rejected in favour of the portable `ThreadPoolExecutor` approach.

**`_deadline: float` in state**: Enables cross-`Send()` deadline propagation, but adds state-schema complexity. Deferred to a follow-on FR; natural cascading via the outer `Future.result(timeout=…)` is sufficient for the direct-node scope.

**`max_items` cap (FR-027)**: Limits fan-out size but does not prevent individual branches from hanging. Complementary, not a substitute.

**Thread-based `signal.alarm`**: Already used by CLI (`cli/graph_commands.py`); only works on Unix and cannot target individual branches. Not suitable here.

**Modifying `from_exception` to match `"timeout"` early**: Rejected — would silently reclassify transient LLM API timeouts (`ReadTimeout`, `ConnectTimeout`, `httpx.TimeoutException`) from retryable `LLM_ERROR` to non-retryable `TIMEOUT_ERROR`, breaking existing retry behaviour. The explicit-caller pattern is the correct fix.

## Related

- FR-027: `max_items` cap on map fan-out (`feature-requests/027-execution-safety-guards.md`)
- FR-030: Map concurrency control (Won't Fix — wrong layer)
- FR-081: Copilot node (existing per-node timeout for copilot only)
- `yamlgraph/map_compiler.py` — `compile_map_node()`, `wrap_for_reducer()`
- `yamlgraph/models/graph_schema.py` — `NodeConfig` (existing `timeout: int | None` field)
- `yamlgraph/models/schemas.py` — `ErrorType`, `PipelineError.from_exception()`
- `yamlgraph/linter/patterns/map.py` — existing `check_map_patterns()`, lint codes W201–W202
- `yamlgraph/node_factory/copilot_node.py` — reference timeout implementation
- `cli/graph_commands.py` — `_setup_timeout()` (signal-based, CLI only)
