# Feature Request: ChainMap Serialization in SimpleRedisCheckpointer

**Status: ✅ IMPLEMENTED in v0.3.17 (ChainMap) + v0.3.18 (Functions) + v0.3.19 (Tuple Keys)**

## Solution

Added ChainMap, function, and tuple key handling to `simple_redis.py`:

### v0.3.17 - ChainMap
- ChainMap serialized as `{"__type__": "chainmap", "value": dict(obj)}`
- Deserialized back to `ChainMap` instance
- 2 unit tests added

### v0.3.18 - Functions
- Functions/callables serialized as `{"__type__": "function", "value": null}`
- Allows LangGraph internals with callables to be checkpointed
- 3 unit tests added

### v0.3.19 - Tuple Dict Keys
- Tuple dict keys serialized as `"__tuple__:[json_array]"`
- Restored to tuple on deserialization
- `_stringify_keys()` and `_unstringify_keys()` process entire checkpoint
- 4 unit tests added

---

## Original Problem

When using `SimpleRedisCheckpointer` with graphs that have `ChainMap` in their state, serialization fails:

```
TypeError: Cannot serialize <class 'collections.ChainMap'>
TypeError: Type is not JSON serializable: ChainMap
```

This happens because `_serialize_value()` in `simple_redis.py` doesn't handle `ChainMap`.

## Context

- Questionnaire-api uses yamlgraph with `redis-simple` checkpointer
- LangGraph state contains `ChainMap` objects (possibly from channel defaults)
- Works fine with `MemorySaver` but fails with `SimpleRedisCheckpointer`

## Proposed Solution

Add ChainMap handling to `_serialize_value()` and `_deserialize_value()` in `simple_redis.py`:

1. Add import: `from collections import ChainMap`

2. In `_serialize_value()`, add before the raise:
```python
if isinstance(obj, ChainMap):
    return {"__type__": "chainmap", "value": dict(obj)}
```

3. In `_deserialize_value()`, add:
```python
if type_name == "chainmap":
    return ChainMap(value)
```

## Priority

High - blocks production Redis usage for questionnaire-api

## Related

- `yamlgraph/storage/simple_redis.py` lines 40-48

---

## Additional Issue: Function Serialization

After fixing ChainMap, another serialization error occurs:

```
TypeError: Cannot serialize <class 'function'>
TypeError: Type is not JSON serializable: function
```

This appears to be from LangGraph internals storing callables in the checkpoint.

### Proposed Solution

Add function handling to skip/ignore non-serializable callables:

```python
if callable(obj) and not isinstance(obj, type):
    # Skip functions - they can't be serialized and are likely LangGraph internals
    return None  # or {"__type__": "function", "value": None}
```

Or investigate if these functions should not be in the state at all.

---

## Additional Issue: Non-String Dict Keys

After fixing function serialization, orjson fails with:

```
TypeError: Dict key must be str
```

LangGraph checkpoints use tuple keys like `(node_name, task_id)` in `channel_versions` and `versions_seen`.

### Proposed Solution

Pre-process the checkpoint data to convert non-string keys to strings before orjson serialization:

```python
def _stringify_keys(obj):
    """Convert non-string dict keys to JSON-safe strings."""
    if isinstance(obj, dict):
        return {
            (json.dumps(k) if not isinstance(k, str) else k): _stringify_keys(v)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_stringify_keys(item) for item in obj]
    return obj
```

And reverse on deserialization.


---

## Test Case

Minimal test to verify Redis checkpointer works with yamlgraph:

```python
"""Test SimpleRedisCheckpointer with LangGraph interrupt pattern."""
import asyncio
import os
from yamlgraph.graph_loader import load_graph_config, compile_graph
from yamlgraph.storage.checkpointer_factory import get_checkpointer_async

async def test_redis_checkpointer():
    """Test checkpoint save/restore across interrupt."""
    # Requires: REDIS_URL=redis://localhost:6379
    # Requires: A graph.yaml with an interrupt node
    
    config_dict = {
        "type": "redis-simple",
        "url": os.environ.get("REDIS_URL", "redis://localhost:6379"),
        "key_prefix": "test:",
    }
    
    checkpointer = await get_checkpointer_async(config_dict)
    assert checkpointer is not None, "Failed to create checkpointer"
    
    # Load a simple graph with interrupt
    graph_config = load_graph_config("path/to/graph.yaml")
    graph = compile_graph(graph_config)
    app = graph.compile(checkpointer=checkpointer)
    
    thread_config = {"configurable": {"thread_id": "test-123"}}
    
    # First invoke - should hit interrupt
    result1 = await app.ainvoke({"user_message": ""}, thread_config)
    assert "assistant_response" in result1
    
    # Second invoke - resume with user input
    result2 = await app.ainvoke({"user_message": "test response"}, thread_config)
    
    # State should persist across invokes
    print("SUCCESS: Redis checkpointer working with interrupts")

if __name__ == "__main__":
    asyncio.run(test_redis_checkpointer())
```

### Key serialization requirements:
1. `ChainMap` - from LangGraph channel defaults
2. Functions/callables - from LangGraph internals (should be skipped)
3. Tuple dict keys - from `channel_versions`, `versions_seen`
4. `UUID`, `datetime`, `bytes` - already handled
