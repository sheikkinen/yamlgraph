# Feature Request: FR-067 Extract Edge Compiler Module

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 day
**Requested:** 2026-02-21
**Depends on:** FR-066 (CC distribution creates the handlers to extract)

## Summary

Extract edge handling functions from `graph_loader.py` (460 lines, over 450 max) to a new `edge_compiler.py` module (~133 lines). Pure module extraction — no behavioral change.

## Requirements Covered

| Function | REQ | Description |
|----------|-----|-------------|
| `_process_edge` | REQ-YG-008 | Compile full graph configuration |
| `_handle_*` helpers | REQ-YG-008 | Individual edge type handlers |
| `_add_conditional_edges` | REQ-YG-008 | Router and expression edge compilation |

## Problem

`graph_loader.py` is 460 lines, exceeding the 450-line maximum defined in CLAUDE.md:
> **Module size**: Target < 400 lines, max 450 (split into submodules if exceeded)

Current structure:
```
graph_loader.py (460 lines)
├── Loop detection           ~95 lines
├── GraphConfig class        ~50 lines
├── Config loading           ~50 lines
├── Tool parsing             ~33 lines
├── Edge handlers           ~133 lines ← EXTRACT THIS
├── compile_graph            ~52 lines
└── checkpointer             ~15 lines
```

## Proposed Solution

Create `yamlgraph/edge_compiler.py` with these functions:

```python
"""Edge compilation for StateGraph construction.

Handles START edges, map node edges, conditional/router edges,
and expression-based routing.
"""

from langgraph.graph import END, StateGraph

# Extracted from graph_loader.py:

def _handle_start_edge(graph: StateGraph, to_node: str, map_nodes: dict) -> None:
    """Handle START -> node edge."""
    ...

def _handle_map_to_map_edge(graph: StateGraph, from_node: str, to_node: str, map_nodes: dict) -> bool:
    """Handle map_node -> map_node edge. Returns True if handled."""
    ...

def _handle_to_map_edge(graph: StateGraph, from_node: str, to_node: str, map_nodes: dict) -> bool:
    """Handle regular -> map_node edge. Returns True if handled."""
    ...

def _handle_from_map_edge(graph: StateGraph, from_node: str, to_node: str, map_nodes: dict) -> bool:
    """Handle map_node -> regular edge (fan-in). Returns True if handled."""
    ...

def _process_edge(
    edge: dict,
    graph: StateGraph,
    map_nodes: dict,
    router_edges: dict,
    expression_edges: dict,
    interrupt_nodes: set | None = None,
) -> None:
    """Process single edge. Delegates to type-specific handlers."""
    ...

def _add_conditional_edges(
    graph: StateGraph,
    router_edges: dict,
    expression_edges: dict,
) -> None:
    """Add router and expression conditional edges to graph."""
    ...

__all__ = ["_process_edge", "_add_conditional_edges"]
```

Update `graph_loader.py`:
```python
from yamlgraph.edge_compiler import _process_edge, _add_conditional_edges
```

## Acceptance Criteria

### File Size Targets
- [ ] `graph_loader.py` ≤ 340 lines (460 - 133 + imports)
- [ ] `edge_compiler.py` ~140 lines (handlers + docstrings)

### Existing Tests Pass
- [ ] `tests/unit/test_graph_loader.py` — all edge compilation tests
- [ ] `tests/integration/` — graphs with map nodes, routers, expressions

### New Tests (from FR-066)
- [ ] `test_handle_start_edge` — @pytest.mark.req("REQ-YG-008")
- [ ] `test_handle_map_to_map_edge` — @pytest.mark.req("REQ-YG-008")
- [ ] `test_handle_to_map_edge` — @pytest.mark.req("REQ-YG-008")
- [ ] `test_handle_from_map_edge` — @pytest.mark.req("REQ-YG-008")

### Verification
- [ ] `wc -l yamlgraph/graph_loader.py` shows ≤ 340
- [ ] `wc -l yamlgraph/edge_compiler.py` shows ~140
- [ ] `ruff check yamlgraph/edge_compiler.py` passes
- [ ] `radon cc yamlgraph/edge_compiler.py -s` shows distributed CC

## Implementation Steps

1. Create `yamlgraph/edge_compiler.py` with module docstring
2. Move functions (lines 260-393 from graph_loader.py):
   - `_handle_start_edge`
   - `_handle_map_to_map_edge`
   - `_handle_to_map_edge`
   - `_handle_from_map_edge`
   - `_process_edge`
   - `_add_conditional_edges`
3. Add required imports to edge_compiler.py
4. Add import statement to graph_loader.py
5. Run tests: `pytest tests/unit/test_graph_loader.py -v`
6. Run integration: `pytest tests/integration/ -v -k "map or router"`

## Alternatives Considered

1. **Keep in graph_loader.py** — Rejected: exceeds 450-line max
2. **Merge with node_compiler.py** — Rejected: different concern (nodes vs edges)
3. **Create `graph_loader/` package** — Overkill for one extraction

## Related

- FR-066: CC distribution (creates the handlers this FR extracts)
- REQ-YG-008: Compile full graph configuration
- CLAUDE.md: Module size limits
