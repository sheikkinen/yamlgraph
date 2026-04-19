# Feature Request: FR-255 Extract Shared invoke_graph

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-04-19

## Summary

Extract the duplicated `_invoke_graph()` function from `mcp_server.py` and `a2a_server.py` into a shared `invoke_graph()` in `graph_loader.py`.

## Value Statement

Framework consumers get a single, tested entry point for synchronous graph invocation, eliminating duplicated code and centralizing bug fixes.

## Problem

`mcp_server.py:56-72` and `a2a_server.py:64-80` contain **identical** `_invoke_graph()` functions:

```python
def _invoke_graph(graph_path: str, variables: dict[str, Any]) -> dict[str, Any]:
    from yamlgraph.graph_loader import compile_graph, load_graph_config
    config = load_graph_config(graph_path)
    sg = compile_graph(config)
    compiled = sg.compile()
    result = compiled.invoke(variables)
    return result
```

Any bug fix or enhancement (e.g., adding checkpointer support) must be applied in both locations. The CLI's `_invoke_graph` is different (takes pre-compiled app) and is out of scope.

## Proposed Solution

Add a public `invoke_graph()` function to `graph_loader.py`:

```python
def invoke_graph(
    path: str | Path,
    variables: dict[str, Any],
    *,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Load, compile, and invoke a graph synchronously.

    Convenience function combining load_graph_config, compile_graph,
    and compiled graph invocation.

    Args:
        path: Path to graph YAML file.
        variables: Input variables / initial state.
        config: Optional LangGraph run config (thread_id, etc.).

    Returns:
        Result dict from graph invocation.
    """
    graph_config = load_graph_config(path)
    sg = compile_graph(graph_config)
    compiled = sg.compile()
    return compiled.invoke(variables, config=config or {})
```

Update `mcp_server.py` and `a2a_server.py` to import and delegate to this shared function.

## Acceptance Criteria

- [x] `invoke_graph()` function exists in `graph_loader.py`
- [x] `mcp_server.py` uses `invoke_graph` from `graph_loader` (no local copy)
- [x] `a2a_server.py` uses `invoke_graph` from `graph_loader` (no local copy)
- [x] Unit test verifies `invoke_graph` calls load → compile → invoke pipeline
- [x] Existing MCP and A2A tests still pass
- [x] REQ-YG-257 traced in ARCHITECTURE.md
- [x] CAP-110 capability registered
- [x] Changelog fragment added

## Alternatives Considered

1. **Leave as-is**: Low risk but perpetuates duplication — rejected.
2. **Create new module**: Over-engineering for a single function — rejected.
3. **Add to executor.py**: Wrong layer; graph_loader owns compilation — rejected.

## Related

- `yamlgraph/graph_loader.py` — existing `load_and_compile()` convenience function
- `yamlgraph/mcp_server.py:56-72` — current duplicate
- `yamlgraph/a2a_server.py:64-80` — current duplicate
- CAP-19: MCP Server Interface (REQ-YG-068)
