# Feature Request: Extract shared `invoke_graph` from MCP and A2A servers

**Priority:** LOW
**Type:** Enhancement
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-04-19

## Summary

Extract the duplicated `_invoke_graph()` function from `mcp_server.py` and `a2a_server.py` into the shared `discovery.py` module.

## Value Statement

Server maintainers get a single source of truth for graph invocation, eliminating the risk of divergent behavior when invocation semantics change.

## Problem

Both `yamlgraph/mcp_server.py` (lines 56–72) and `yamlgraph/a2a_server.py` (lines 64–80) contain identical `_invoke_graph()` functions:

```python
def _invoke_graph(graph_path: str, variables: dict[str, Any]) -> dict[str, Any]:
    from yamlgraph.graph_loader import compile_graph, load_graph_config
    config = load_graph_config(graph_path)
    sg = compile_graph(config)
    compiled = sg.compile()
    result = compiled.invoke(variables)
    return result
```

This is a DRY violation. Any change to graph invocation semantics (e.g., adding checkpointer support, error wrapping, or caching) must be made in two places. The `discovery.py` module already hosts the shared `discover_graphs()` function used by both servers, making it the natural home for shared invocation logic.

**Not in scope:** The `_invoke_graph()` in `yamlgraph/cli/graph_commands.py` has a different signature (takes a pre-compiled app, handles sync/async dispatch) and is not part of this duplication.

## Proposed Solution

Add `invoke_graph()` as a public function in `yamlgraph/discovery.py`:

```python
# yamlgraph/discovery.py (addition)
def invoke_graph(graph_path: str, variables: dict[str, Any]) -> dict[str, Any]:
    """Load, compile, and invoke a graph synchronously.

    Shared by MCP and A2A servers (REQ-YG-068).

    Args:
        graph_path: Absolute path to graph.yaml.
        variables: Input variables for the graph.

    Returns:
        Result dict from graph invocation.
    """
    from yamlgraph.graph_loader import compile_graph, load_graph_config

    config = load_graph_config(graph_path)
    sg = compile_graph(config)
    compiled = sg.compile()
    return compiled.invoke(variables)
```

Then replace the local `_invoke_graph` in both servers:

```python
# mcp_server.py
from yamlgraph.discovery import DEFAULT_GRAPH_PATTERNS, discover_graphs, invoke_graph

# a2a_server.py
from yamlgraph.discovery import discover_graphs, invoke_graph
```

### Import layer safety

All three modules (`discovery`, `mcp_server`, `a2a_server`) are in the same import layer (Layer 2) in `.importlinter`, configured as non-independent siblings (`:` separator). The lazy import of `graph_loader` inside the function body matches the existing pattern in both servers. No layer violations.

## Acceptance Criteria

- [ ] `invoke_graph()` exists as a public function in `yamlgraph/discovery.py`
- [ ] `mcp_server.py` imports and uses `invoke_graph` from `discovery` — no local `_invoke_graph`
- [ ] `a2a_server.py` imports and uses `invoke_graph` from `discovery` — no local `_invoke_graph`
- [ ] Unit test for `invoke_graph()` in `tests/unit/test_discovery.py` (mock `graph_loader`)
- [ ] Existing MCP server tests pass (`tests/unit/test_mcp_server.py`)
- [ ] Existing A2A server tests pass (`tests/unit/test_a2a_server.py`)
- [ ] `lint-imports` passes (no layer violations)
- [ ] `ruff check` passes

## Alternatives Considered

1. **Create a new `yamlgraph/graph_runner.py` module** — Rejected. Adds a new module for a single function. `discovery.py` already serves as the shared infrastructure for both servers.
2. **Move to `graph_loader.py`** — Viable but `discovery.py` is the module both servers already import from, keeping the dependency footprint unchanged.
3. **Leave as-is** — Rejected. The DRY violation is mechanical and risk-free to fix. Leaving it invites divergence on the next invocation change.

## Related

- `yamlgraph/discovery.py` — target module (already hosts shared `discover_graphs()`)
- `yamlgraph/mcp_server.py` — CAP-19 / REQ-YG-068
- `yamlgraph/a2a_server.py` — FR-208 / CAP-81
- FR-208: A2A graph support (introduced the second copy)
- FR-250: A2A server protocol gaps (streaming refactor, but `_invoke_graph` was retained)
