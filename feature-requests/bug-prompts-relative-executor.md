# Bug: prompts_relative Not Working in Executor

**Priority:** HIGH  
**Type:** Bug  
**Version:** 0.3.4  
**Component:** executor.py, utils/prompts.py  
**Status:** ✅ FIXED in v0.3.5

## Summary

The `prompts_relative` feature works during graph compilation (node_factory) but fails at runtime (executor) because the executor doesn't receive `graph_path` when loading prompts.

## Expected Behavior

When `prompts_relative: true` is set in graph defaults:
```yaml
defaults:
  prompts_relative: true
  prompts_dir: prompts

nodes:
  generate_opening:
    type: llm
    prompt: opening  # Should resolve to {graph_dir}/prompts/opening.yaml
```

Prompts should resolve relative to the graph file at runtime.

## Actual Behavior

```
Prompt not found: /path/to/project/prompts/opening.yaml
```

The executor falls back to global `PROMPTS_DIR` because it doesn't have access to `graph_path`.

## Root Cause

In `executor.py` line 241:
```python
prompt_config = load_prompt(prompt_name)  # Missing graph_path, prompts_relative
```

The `load_prompt()` call doesn't pass:
- `graph_path` 
- `prompts_dir`
- `prompts_relative`

Meanwhile, `node_factory.py` correctly passes these to `resolve_prompt_path()` (line 182).

## Reproduction

```python
# graph at questionnaires/audit/graph.yaml
# prompts at questionnaires/audit/prompts/opening.yaml

from yamlgraph.graph_loader import load_graph_config, compile_graph

config = load_graph_config("questionnaires/audit/graph.yaml")
# config.prompts_relative = True  ✓ Parsed correctly
# config.source_path = ".../questionnaires/audit/graph.yaml"  ✓ Set correctly

graph = compile_graph(config)
app = graph.compile()
result = await app.ainvoke(...)  # ❌ Prompt not found
```

## Proposed Fix

### Option A: Pass config through node closure

In `node_factory.py`, capture the prompts config in the node function closure:

```python
def create_node_function(..., graph_path, ...):
    prompts_relative = defaults.get("prompts_relative", False)
    prompts_dir = defaults.get("prompts_dir")
    
    async def node_fn(state):
        # Pass to executor
        result = await executor.run_prompt(
            prompt_name,
            ...,
            graph_path=graph_path,
            prompts_dir=prompts_dir,
            prompts_relative=prompts_relative,
        )
```

### Option B: Resolve prompts at compile time

Load and cache prompt content during graph compilation instead of at runtime:

```python
def create_node_function(...):
    # Resolve prompt path at compile time
    prompt_path = resolve_prompt_path(
        prompt_name,
        graph_path=graph_path,
        prompts_relative=prompts_relative,
    )
    prompt_config = load_prompt_from_path(prompt_path)
    
    async def node_fn(state):
        # Use pre-loaded prompt
        ...
```

## Workaround

Use global `PROMPTS_DIR` and organize prompts by questionnaire:

```python
# In session.py
import yamlgraph.config
yamlgraph.config.PROMPTS_DIR = Path("prompts")
```

```yaml
# In graph.yaml
nodes:
  generate_opening:
    prompt: audit/opening  # Resolves to prompts/audit/opening.yaml
```

## Impact

- Graph-relative prompts (FR-A) partially broken
- Cannot create fully self-contained questionnaire folders
- Workaround requires global config and non-colocated prompts

## Related

- FR-A: Graph-Relative Prompts (feature-requests/graph-relative-prompts.md)
