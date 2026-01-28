# FR-012-0: Fix CLI Graph Run to Use Checkpointer

**Priority:** HIGH  
**Status:** ✅ IMPLEMENTED  
**Blocks:** FR-012-1 (Deprecate Legacy Resume)

## Summary

`yamlgraph graph run --thread <id>` is broken. The `--thread` flag passes a thread_id to config, but `cmd_graph_run` doesn't use the graph's configured checkpointer, so the thread_id does nothing.

## Problem

### Current Implementation (BROKEN)

```python
# yamlgraph/cli/graph_commands.py
def cmd_graph_run(args: Namespace) -> None:
    graph = load_and_compile(str(graph_path))
    app = graph.compile()  # ❌ No checkpointer!
    
    config = {}
    if args.thread:
        config["configurable"] = {"thread_id": args.thread}  # Useless without checkpointer
    
    result = app.invoke(initial_state, config=config if config else None)
```

### What Should Happen

```python
from yamlgraph.graph_loader import load_graph_config, compile_graph, get_checkpointer_for_graph

config = load_graph_config(str(graph_path))
graph = compile_graph(config)
checkpointer = get_checkpointer_for_graph(config)  # ✅ Get from YAML
app = graph.compile(checkpointer=checkpointer)     # ✅ Pass to compile

run_config = {}
if args.thread:
    run_config["configurable"] = {"thread_id": args.thread}

result = app.invoke(initial_state, config=run_config)
```

## Impact

### Currently Broken

```bash
# This does NOT resume - thread_id is ignored without checkpointer
yamlgraph graph run graphs/interview.yaml --thread session-123
yamlgraph graph run graphs/interview.yaml --thread session-123  # Starts fresh!
```

### After Fix

```bash
# Graph has: checkpointer: { type: sqlite, path: ./sessions.db }
yamlgraph graph run graphs/interview.yaml --thread session-123 --var input=start
# ... hits interrupt ...
yamlgraph graph run graphs/interview.yaml --thread session-123  # ✅ Resumes!
```

## Proposed Fix

### Option A: Always Use Graph's Checkpointer

```python
def cmd_graph_run(args: Namespace) -> None:
    from yamlgraph.graph_loader import (
        load_graph_config,
        compile_graph,
        get_checkpointer_for_graph,
    )
    
    config = load_graph_config(str(graph_path))
    graph = compile_graph(config)
    checkpointer = get_checkpointer_for_graph(config)
    
    app = graph.compile(checkpointer=checkpointer)
    
    run_config = {}
    if args.thread:
        run_config["configurable"] = {"thread_id": args.thread}
    elif checkpointer:
        # Auto-generate thread_id if checkpointer configured but no --thread
        import uuid
        run_config["configurable"] = {"thread_id": str(uuid.uuid4())}
    
    result = app.invoke(initial_state, config=run_config if run_config else None)
```

### Option B: Only Use Checkpointer When --thread Provided

```python
def cmd_graph_run(args: Namespace) -> None:
    from yamlgraph.graph_loader import (
        load_graph_config,
        compile_graph,
        get_checkpointer_for_graph,
    )
    
    config = load_graph_config(str(graph_path))
    graph = compile_graph(config)
    
    # Only use checkpointer if --thread provided
    checkpointer = None
    run_config = {}
    if args.thread:
        checkpointer = get_checkpointer_for_graph(config)
        run_config["configurable"] = {"thread_id": args.thread}
    
    app = graph.compile(checkpointer=checkpointer)
    result = app.invoke(initial_state, config=run_config if run_config else None)
```

**Recommendation:** Option A - if graph defines a checkpointer, always use it. This matches Python API behavior and ensures interrupt nodes work correctly.

## Edge Cases

### Graph Without Checkpointer + --thread Flag

```yaml
# No checkpointer defined
version: "1.0"
name: simple-graph
nodes: ...
```

```bash
yamlgraph graph run graphs/simple.yaml --thread session-123
# Should warn: "⚠️ --thread ignored: graph has no checkpointer configured"
```

### Graph With Checkpointer + No --thread Flag

```yaml
checkpointer:
  type: sqlite
  path: ./sessions.db
```

```bash
yamlgraph graph run graphs/interview.yaml --var input=start
# Auto-generate thread_id, print it:
# "📝 Session: a1b2c3d4 (use --thread a1b2c3d4 to resume)"
```

## Validation

- [ ] `--thread` with checkpointer enables resume
- [ ] `--thread` without checkpointer shows warning
- [ ] Interrupt nodes work when checkpointer configured
- [ ] Auto-generated thread_id printed for discovery

## Files to Change

| File | Change |
|------|--------|
| `yamlgraph/cli/graph_commands.py` | Use `get_checkpointer_for_graph()` |
| `reference/cli.md` | Document `--thread` behavior |

## Tests to Add

```python
def test_graph_run_uses_checkpointer():
    """Graph run with --thread should use checkpointer from YAML."""
    # Create graph with sqlite checkpointer
    # Run with --thread, hit interrupt
    # Run again with same --thread, verify resume
    
def test_graph_run_warns_no_checkpointer():
    """Graph run with --thread but no checkpointer should warn."""
    # Graph without checkpointer
    # Run with --thread
    # Verify warning printed
```

## Timeline

| Version | Action |
|---------|--------|
| v0.3.34 | Fix `cmd_graph_run` to use checkpointer |
| v0.4.0 | Deprecate legacy resume (FR-012-1) |
