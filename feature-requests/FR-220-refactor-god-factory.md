# Feature Request: Refactor God Factory

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 1 day
**Requested:** 2026-04-12

## Summary

Replace the 15-branch if/elif dispatch chain in `node_compiler.compile_node()` with a registry pattern.

## Value Statement

Framework contributors can add new node types by registering a single handler function instead of editing a monolithic if/elif chain.

## Problem

`node_compiler.py:compile_node()` is a "god factory" — a single function with a 15-branch if/elif chain that dispatches on `NodeType`. Each branch creates a node function via the appropriate factory, adds it to the graph, and returns metadata.

Problems:
1. **Hard to extend**: Adding a new node type requires inserting a new elif branch in the middle of a 130-line function
2. **Hard to test**: Branch coverage requires mocking through the entire function
3. **Mixed concerns**: Config enrichment, type dispatch, graph mutation, and logging are interleaved
4. **No explicit error for unknown types**: Unknown node types silently fall through to the LLM branch

The factory functions are already well-organized in `node_factory/` modules — only the dispatch mechanism itself is monolithic.

## Proposed Solution

### Registry Pattern

Replace the if/elif chain with a `NODE_TYPE_HANDLERS` dict mapping `NodeType` → handler function.

```python
# Each handler receives a NodeCompileContext and returns metadata or None
NodeTypeHandler = Callable[[NodeCompileContext], tuple[str, Any] | None]

NODE_TYPE_HANDLERS: dict[str, NodeTypeHandler] = {
    NodeType.TOOL: _compile_tool_node,
    NodeType.PYTHON: _compile_python_node,
    NodeType.AGENT: _compile_agent_node,
    NodeType.MAP: _compile_map_node,
    NodeType.TOOL_CALL: _compile_tool_call_node,
    NodeType.INTERRUPT: _compile_interrupt_node,
    NodeType.PASSTHROUGH: _compile_passthrough_node,
    NodeType.COPILOT: _compile_copilot_node,
    NodeType.SUBGRAPH: _compile_subgraph_node,
    NodeType.LLM: _compile_llm_node,
    NodeType.ROUTER: _compile_llm_node,  # routers use same factory as LLM
}
```

### NodeCompileContext

A frozen dataclass encapsulating all context needed by handlers:

```python
@dataclass(frozen=True)
class NodeCompileContext:
    node_name: str
    node_config: dict[str, Any]
    graph: StateGraph
    config: GraphConfig
    tools: dict[str, Any]
    python_tools: dict[str, Any]
    callable_registry: dict[str, Callable]
    effective_defaults: dict[str, Any]
    prompts_dir: Path | None
    prompts_relative: bool
```

### Simplified compile_node()

```python
def compile_node(...) -> tuple[str, Any] | None:
    # 1. Enrich config (common)
    enriched_config = _enrich_config(node_name, node_config, config)
    effective_defaults = _build_effective_defaults(config)

    # 2. Lookup handler (registry)
    node_type = node_config.get("type", NodeType.LLM)
    handler = NODE_TYPE_HANDLERS.get(node_type)
    if handler is None:
        raise ValueError(f"Unknown node type: {node_type!r}")

    # 3. Delegate
    ctx = NodeCompileContext(...)
    result = handler(ctx)

    # 4. Log (common)
    logger.info(f"Added node: {node_name} (type={node_type})")
    return result
```

## Acceptance Criteria

- [x] `NodeCompileContext` dataclass encapsulates compile context
- [x] `NODE_TYPE_HANDLERS` registry maps all handled node types to handler functions
- [x] `compile_node()` dispatches via registry lookup instead of if/elif
- [x] Unknown node types raise `ValueError` (not silent fallthrough)
- [x] All existing `test_node_compiler_branches.py` tests pass unchanged
- [x] New tests verify registry completeness and unknown-type error
- [x] REQ-YG-220 added to CAP-02 and ARCHITECTURE.md
- [x] No behavioral change for any existing node type

## Alternatives Considered

1. **Visitor pattern**: More OO but overkill — handlers are simple functions
2. **Plugin/decorator registration**: Good for extensibility but adds complexity; registry dict is explicit and auditable
3. **ABC with subclasses**: Each node type as a class — too much ceremony for stateless handlers

## Related

- `yamlgraph/node_compiler.py` — The god factory
- `yamlgraph/node_factory/` — Already-extracted factory functions
- `tests/unit/test_node_compiler_branches.py` — Existing branch coverage tests
- REQ-YG-007 — "Compile individual nodes" (CAP-02)
