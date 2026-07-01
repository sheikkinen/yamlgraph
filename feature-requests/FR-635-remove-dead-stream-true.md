# Feature Request: Remove Dead Per-Node stream:true Code

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Enforced
**Effort:** 0.5 days
**Requested:** 2026-07-01
**Depends on:** FR-633, FR-634

## Summary

Delete `yamlgraph/node_factory/streaming.py` and the `stream: true` early-return path in `llm_nodes.py`. This code creates async generator nodes that no execution path can consume.

## Value Statement

Framework authors and contributors stop encountering dead code that implies per-node streaming works, when it doesn't — reducing confusion and maintenance surface.

## Problem

`create_streaming_node()` exists in the node factory and is triggered when a YAML node declares `stream: true`. It creates an async generator function. However:

1. **No graph in the codebase uses `stream: true`** — zero hits across all examples, demos, and projects.
2. **LangGraph's `app.invoke()` cannot consume async generators from nodes** — the node returns an async iterator, but invoke expects a dict. The result is either an error or silent data loss.
3. **The correct streaming approach is graph-level** — `run_graph_streaming_native()` wraps `app.astream(stream_mode="messages")`, which transparently streams ALL LLM nodes without any per-node annotation.
4. **The streaming demo README documents `stream: true`** — teaching users a pattern that doesn't work.
5. **ninchat_voice (production consumer) doesn't use it** — uses `run_graph_async()` (batch) and would use `run_graph_streaming_native()` for future NC-222.

The code is a false idol (Commandment 8: kill all entropy).

## Proposed Solution

### Delete

- `yamlgraph/node_factory/streaming.py` (71 lines)
- Import in `yamlgraph/node_factory/__init__.py`
- Export in `__all__`

### Remove early-return in `llm_nodes.py`

```python
# DELETE this block (llm_nodes.py ~line 420-435):
from yamlgraph.node_factory.streaming import create_streaming_node

if node_config.get("stream", False):
    return create_streaming_node(
        node_name,
        node_config,
        graph_path=graph_path,
        prompts_dir=prompts_dir,
        prompts_relative=prompts_relative,
    )
```

### Update documentation

- `reference/streaming.md` — remove per-node `stream: true` section, document only CLI `--stream` and Python API
- Remove any references to `stream: true` in YAML schema docs

### Keep

- `yamlgraph/models/streaming.py` (`StreamEvent`) — actively used by `run_graph_streaming_native()`
- `yamlgraph/executor_async.py` streaming functions — working and tested
- All streaming tests that test `run_graph_streaming_native()`

## Acceptance Criteria

- [ ] `yamlgraph/node_factory/streaming.py` deleted
- [ ] `create_streaming_node` removed from `__init__.py` imports and `__all__`
- [ ] `stream: true` early-return removed from `llm_nodes.py`
- [ ] `tests/unit/test_streaming_resolution.py` removed or rewritten to test graph-level streaming
- [ ] `reference/streaming.md` updated — no mention of per-node `stream: true`
- [ ] `ruff check` passes
- [ ] `vulture` doesn't flag new dead code
- [ ] All remaining streaming tests pass (`test_streaming_chaos.py`, integration tests)
- [ ] `yamlgraph graph lint` still works on all existing graphs (no graph uses `stream: true`)

## Alternatives Considered

1. **Make `stream: true` actually work** — Would require rewriting the LangGraph execution path to handle async generator nodes specially. This fights against LangGraph's architecture where streaming is a graph execution mode, not a node property. The framework already has the correct approach (`astream(stream_mode="messages")`).

2. **Deprecation warning instead of deletion** — The code has zero consumers. Deprecation warnings are for code with users. This has none.

3. **Keep as "planned feature"** — It's been in the codebase since early development with zero adoption. The graph-level streaming approach (FR-633) makes it permanently unnecessary.

## Related

- FR-633 (prerequisite — proves graph-level streaming is the correct paradigm)
- FR-634 (prerequisite — demo no longer references `stream: true`)
- `yamlgraph/node_factory/streaming.py` — file to delete
- `yamlgraph/node_factory/llm_nodes.py:420-435` — early-return to remove
- `tests/unit/test_streaming_resolution.py` — tests the dead path
- Commandment 8: "Kill all entropy and false idols"
