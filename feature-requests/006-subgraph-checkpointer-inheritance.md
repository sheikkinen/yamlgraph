# Feature Request: Subgraph Should Use Parent Checkpointer

**Priority:** HIGH  
**Type:** Bug  
**Status:** ✅ FIXED  
**Effort:** 0.5 day  
**Requested:** 2026-01-26

## Status Update (2026-01-26) - FIXED

**Root Cause:** The issue was NOT in checkpointer inheritance (LangGraph handles that via `__pregel_checkpointer` runtime propagation). The actual bug was in `SimpleRedisCheckpointer` serialization failing on LangGraph internal objects.

**Fix Applied:** Updated `yamlgraph/storage/serializers.py` to skip serialization of LangGraph/LangChain internal runtime objects:
- `CallbackManager`, `BaseCallbackManager`, `AsyncCallbackManager`
- `BaseCheckpointSaver`, `MemorySaver`, `RedisSaver`, `SimpleRedisCheckpointer`
- Other runtime objects that can't be meaningfully serialized

**Verification:**
```bash
REDIS_URL=redis://localhost:6379 python scripts/test_subgraph_interrupt.py --all
# ✅ Scenario A: PASS (child without checkpointer)
# ✅ Scenario B: PASS (child with memory checkpointer)
# ✅ Scenario C: PASS (child with redis-simple checkpointer)
```

All 51 Redis tests pass, all 27 subgraph tests pass.

## Summary

When a graph with its own checkpointer config is used as a subgraph, it should use the parent's checkpointer instead of its own. Currently the subgraph's checkpointer config is ignored and `parent_checkpointer=None` results in no persistence.

## Problem

Navigator graph uses interrai-ca as a subgraph. Both define their own checkpointer:

```yaml
# navigator/graph.yaml
checkpointer:
  type: redis-simple
  key_prefix: "navigator:"

# interrai-ca/graph.yaml  
checkpointer:
  type: redis-simple
  key_prefix: "interrai-ca:"
```

When interrai-ca is invoked as a subgraph and hits an interrupt, state is not persisted. On resume, the subgraph restarts from `init` instead of continuing.

The TDD test `scripts/test_subgraph_interrupt.py` passes because the child graph has NO checkpointer config - it correctly inherits from parent. The bug occurs when the child HAS its own checkpointer config.

## Root Cause

In `subgraph_nodes.py`, the subgraph is compiled with:

```python
compiled = state_graph.compile(checkpointer=parent_checkpointer)
```

Since `parent_checkpointer=None` (not passed from node_compiler), the subgraph has no checkpointer. The subgraph's own config (`interrai-ca`'s redis-simple) is never instantiated because `get_checkpointer_for_graph()` is not called for subgraphs.

## Proposed Solution

Pass the parent's checkpointer through the compilation chain so subgraphs always use it:

```python
# node_compiler.py - compile_nodes()
def compile_nodes(..., *, checkpointer=None):
    ...
    result = compile_node(..., checkpointer=checkpointer)

# node_compiler.py - compile_node()  
def compile_node(..., *, checkpointer=None):
    if node_type == NodeType.SUBGRAPH:
        node_fn = create_subgraph_node(
            node_name,
            enriched_config,
            parent_graph_path=config.source_path,
            parent_checkpointer=checkpointer,  # Pass parent's checkpointer
        )
```

The subgraph's own checkpointer config is intentionally ignored when used as a subgraph - the parent controls persistence.

## Acceptance Criteria

- [ ] Subgraphs use parent checkpointer (ignore their own config)
- [ ] Warning logged when child's checkpointer config is ignored
- [ ] TDD test continues to pass: `python scripts/test_subgraph_interrupt.py`
- [ ] Navigator -> interrai-ca flow works without restart loop
- [ ] Backward compatible (checkpointer param optional, defaults to None)

## Notes

### Why it works now (without the fix)

LangGraph propagates checkpointer at runtime via `config["configurable"]["__pregel_checkpointer"]`. The `get_state()` call in `subgraph_nodes.py:182` succeeds because:

1. Parent compiles with checkpointer → stored in runtime config
2. `_build_child_config()` spreads `**parent_config` to child
3. Child's `get_state()` uses runtime checkpointer, not compile-time

This is convenient but relies on undocumented internals.

### What the fix would do

1. Explicitly pass `parent_checkpointer` to `create_subgraph_node()`
2. Child compiles with `checkpointer=parent_checkpointer`
3. Child's own checkpointer config is ignored (with warning)
4. No reliance on LangGraph internals

## Related

- `scripts/test_subgraph_interrupt.py` - TDD test (both scenarios pass)
- `yamlgraph/node_factory/subgraph_nodes.py:149` - compile with checkpointer
- `yamlgraph/node_compiler.py:117` - where parent_checkpointer needs to be passed
- questionnaire-api navigator/interrai-ca subgraph usage
