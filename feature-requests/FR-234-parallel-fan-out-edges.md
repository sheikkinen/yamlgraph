# Feature Request: FR-234 Parallel Fan-Out Edge Syntax

**Priority:** MEDIUM
**Type:** Feature
**Status:** Approved
**Effort:** 2 days
**Requested:** 2026-04-18

## Summary

Add `type: parallel` edge syntax so that `from: A, to: [B, C], type: parallel` fans out to all targets concurrently, with natural fan-in convergence at a downstream barrier node.

## Value Statement

Graph authors can express concurrent task execution (e.g., parallel analysis branches, concurrent API calls to different services) entirely in YAML without writing custom Python orchestration or misusing map nodes for non-data-parallel workloads.

## Problem

YAMLGraph currently offers two forms of concurrency:

1. **Map nodes** (`type: map`): Data-parallel — the *same* operation on each item in a list. Requires `over`, `as`, `collect` fields. Cannot express "run node B and node C in parallel with different prompts."

2. **Race nodes** (`type: race`, FR-232): Provider-parallel — the *same* prompt to multiple LLMs. Returns first success only. Not for task parallelism.

Neither supports **task parallelism**: running *different* nodes concurrently from a common predecessor.

Today, the `to: [B, C, D]` syntax exists but only with `type: conditional`, which routes to *one* target based on router logic. To run B and C in parallel, a graph author must:

1. Write a custom Python node with `concurrent.futures` or `asyncio`
2. Manually handle state merging and error propagation
3. Lose the declarative YAML advantage

LangGraph natively supports fan-out via multiple `add_edge()` calls from the same source node, with automatic barrier convergence at join nodes. The framework infrastructure is ready — only the YAML syntax and edge compiler dispatch are missing.

### Motivating examples

```yaml
# ❌ Today: Must be sequential or use custom Python
edges:
  - from: extract
    to: analyze_sentiment    # runs first
  - from: analyze_sentiment
    to: analyze_topics       # runs second (wasted time)
  - from: analyze_topics
    to: synthesize

# ✅ Proposed: Both analyses run concurrently
edges:
  - from: extract
    to: [analyze_sentiment, analyze_topics]
    type: parallel
  - from: analyze_sentiment
    to: synthesize
  - from: analyze_topics
    to: synthesize           # LangGraph waits for both before running synthesize
```

## Proposed Solution

### YAML Syntax

```yaml
edges:
  - from: A
    to: [B, C, D]
    type: parallel
```

**Semantics:**
- Node A executes
- On completion, nodes B, C, and D execute **concurrently**
- Each branch writes to its own `state_key`
- A downstream **barrier node** (a node with incoming edges from all branches) runs only after all branches complete
- This is LangGraph's native fan-out/fan-in behavior

### START Fan-Out

```yaml
edges:
  - from: START
    to: [init_cache, init_config, init_logging]
    type: parallel
  - from: init_cache
    to: main_pipeline
  - from: init_config
    to: main_pipeline
  - from: init_logging
    to: main_pipeline
```

### Mixed with Other Edge Types

```yaml
edges:
  - from: START
    to: preprocess
  - from: preprocess
    to: [analyze_text, analyze_images, analyze_metadata]
    type: parallel
  - from: analyze_text
    to: merge_results
  - from: analyze_images
    to: merge_results
  - from: analyze_metadata
    to: merge_results
  - from: merge_results
    to: END
```

### Implementation

#### 1. Edge Compiler (`yamlgraph/edge_compiler.py`)

Add `_handle_parallel_edge()` and `_handle_parallel_start_edge()` handlers, then extend `_process_edge()` dispatch (after map handlers, before conditional check at line 101):

```python
def _handle_parallel_edge(
    graph: StateGraph, from_node: str, to_nodes: list[str],
    interrupt_nodes: set[str] | None = None,
) -> None:
    """Handle parallel fan-out: source → [target1, target2, ...] concurrently."""
    for target in to_nodes:
        resolved = f"{target}_prepare" if interrupt_nodes and target in interrupt_nodes else target
        graph.add_edge(from_node, END if resolved == "END" else resolved)


def _handle_parallel_start_edge(
    graph: StateGraph, to_nodes: list[str]
) -> None:
    """Handle START → [target1, target2, ...] concurrent entry."""
    from langgraph.graph import START
    for target in to_nodes:
        graph.add_edge(START, target)
```

In `_process_edge()`, insert **before** the START handler (line 88) — not after it — because the START handler returns early and would intercept parallel START edges before the parallel dispatch:

```python
# Handle parallel fan-out edges (FR-234)
if edge_type == "parallel" and isinstance(to_node, list):
    if from_node == "START":
        _handle_parallel_start_edge(graph, to_node)
    else:
        _handle_parallel_edge(graph, from_node, to_node, interrupt_nodes)
    return
```

**Note:** `_handle_start_edge()` (line 14) currently accepts `to_node: str` — the new parallel START handler bypasses it entirely, calling `graph.add_edge(START, target)` directly instead of `graph.set_entry_point()`, since `set_entry_point` only accepts a single node.

**Note:** `_handle_parallel_edge()` must accept `interrupt_nodes` and redirect any target that is an interrupt node to `{target}_prepare` (FR-060 contract). START fan-out does not need this — interrupt nodes cannot be entry points.

#### 2. Edge Schema (`yamlgraph/schemas/graph-v1.json`)

Add `type` field to `EdgeConfig` properties. Currently only `from`, `to`, and `condition` are declared — the `type` field is used in code (line 81) but not validated by schema:

```json
"type": {
  "anyOf": [
    { "enum": ["conditional", "parallel"] },
    { "type": "null" }
  ],
  "default": null,
  "description": "Edge type: conditional (router dispatch) or parallel (concurrent fan-out)",
  "title": "Type"
}
```

This formalizes the existing implicit contract for `type: conditional` while adding `parallel`.

#### 3. Linter Rules (`yamlgraph/linter/checks_semantic.py`)

Extend `check_edge_types()` (line 306) with parallel edge validation. New lint codes in the E8xx edge semantic namespace:

| Code | Severity | Rule |
|------|----------|------|
| E803 | error | `type: parallel` with `to:` as string (must be list) |
| E804 | error | `type: parallel` with `to:` containing < 2 targets |
| W802 | warning | Parallel targets with no common convergence node (possible dangling branches) |
| E805 | error | `type: parallel` combined with `condition:` (mutually exclusive) |

#### 4. State Management

No changes needed. The `last_value` reducer in `models/state_builder.py` (lines 14-28) already handles concurrent writes safely:

```python
def last_value(_existing: Any, new: Any) -> Any:
    """Reducer that keeps the last written value (last-write-wins).
    Safe for concurrent fan-in: when multiple parallel nodes write to
    the same key, LangGraph calls the reducer instead of raising
    INVALID_CONCURRENT_GRAPH_UPDATE."""
    return new
```

Each parallel branch should write to a **distinct** `state_key`. If branches must write to the same key, `last_value` applies (last-write-wins). This is documented but not enforced.

#### 5. Integration Points

| Component | Change |
|-----------|--------|
| `yamlgraph/edge_compiler.py` | `_handle_parallel_edge()`, `_handle_parallel_start_edge()`, dispatch in `_process_edge()` |
| `yamlgraph/schemas/graph-v1.json` | Add `type` field to `EdgeConfig` |
| `yamlgraph/linter/checks_semantic.py` | E803, E804, W802, E805 lint rules in `check_edge_types()` |
| `reference/graph-yaml.md` | Document `type: parallel` syntax (after line 912, before Security) |
| `tests/unit/test_edge_compiler.py` | Fan-out wiring tests (**new file**) |
| `tests/unit/test_linter.py` | Lint rule tests for parallel edges |

## Acceptance Criteria

- [ ] `type: parallel` edge with `to: [B, C]` emits `graph.add_edge(A, B)` and `graph.add_edge(A, C)`
- [ ] `from: START, to: [B, C], type: parallel` creates concurrent entry points via `add_edge(START, ...)`
- [ ] Downstream barrier node (receiving edges from all branches) executes only after all branches complete
- [ ] Parallel branches writing to distinct `state_key` values preserve all results
- [ ] `last_value` reducer handles concurrent writes to same key without `INVALID_CONCURRENT_GRAPH_UPDATE`
- [ ] Lint E803: `type: parallel` with scalar `to:` is an error
- [ ] Lint E804: `type: parallel` with < 2 targets is an error
- [ ] Lint W802: parallel targets without common downstream convergence emits warning
- [ ] Lint E805: `type: parallel` with `condition:` is an error
- [ ] `yamlgraph graph lint` passes on valid parallel fan-out graphs
- [ ] `yamlgraph graph run` executes parallel branches concurrently (wall-clock < sum of branch durations)
- [ ] Existing `type: conditional` edge behavior unchanged
- [ ] Existing graphs without `type: parallel` compile identically (no regression)
- [ ] Unit tests with `@pytest.mark.req` linking to next available REQ-YG-XXX (assigned at implementation time)
- [ ] `reference/graph-yaml.md` updated with parallel edge documentation
- [ ] Example graph demonstrating parallel fan-out pattern
- [ ] Parallel branch errors follow individual node `on_error` semantics; LangGraph propagates errors to barrier node
- [ ] Interrupt node targets in parallel `to:` list are redirected to `{target}_prepare` (FR-060 contract)

## Alternatives Considered

### 1. Implicit fan-out from duplicate `from:` edges

```yaml
edges:
  - from: A
    to: B
  - from: A
    to: C
```

Multiple edges from the same source could implicitly fan out. **Rejected**: Ambiguous — today these resolve as sequential simple edges or would conflict. Explicit `type: parallel` communicates intent and avoids silent behavior changes for existing graphs.

### 2. New `parallel:` top-level block

```yaml
parallel:
  - [analyze_text, analyze_images]
```

**Rejected**: Couples fan-out to top-level config instead of edge-level control. Cannot express partial parallelism within a larger graph. Inconsistent with edge-centric design.

### 3. Extend map nodes with `static_targets:`

```yaml
fan_out:
  type: map
  static_targets: [analyze_text, analyze_images]
```

**Rejected**: Map semantics are data-parallel (same operation, different data). Overloading map for task-parallel confuses the mental model (same issue identified in FR-232's alternatives).

### 4. Use `Send()` directly via a Python shim node

**Rejected**: Defeats YAML-first philosophy. The purpose of this feature is to avoid writing Python for a pattern that LangGraph supports natively via `add_edge()`.

## Related

- **FR-067** (`edge_compiler.py`): Edge compiler module where handlers will be added
- **FR-033** (Sequence Syntax): Complementary ergonomic edge syntax (linear chains)
- **FR-232** (Race Node): Provider-parallel (concurrent LLMs); this FR is task-parallel (concurrent nodes)
- **Map Compiler** (`map_compiler.py`): Data-parallel via `Send()`; this FR is static fan-out via `add_edge()`
- **State Builder** (`models/state_builder.py`): `last_value` reducer already handles concurrent fan-in
- **REQ-YG-008**: Compile full graph configuration (extended by this FR)
- **Capability 6**: Routing & Flow Control (REQ-YG-021–023, 214)
