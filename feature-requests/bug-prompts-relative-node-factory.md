# Bug: prompts_relative Not Passed to execute_prompt in node_factory

**Priority:** HIGH  
**Type:** Bug  
**Version:** 0.3.5  
**Component:** node_factory.py  
**Related:** bug-prompts-relative-executor.md (partially fixed)

## Summary

The 0.3.5 fix added `graph_path`, `prompts_dir`, and `prompts_relative` parameters to `execute_prompt()` and `PromptExecutor.execute()`, but `node_factory.py` doesn't pass these captured values when calling `execute_prompt()`.

## Expected Behavior

When graph is compiled with `prompts_relative: true`:
```yaml
defaults:
  prompts_relative: true
  prompts_dir: prompts

nodes:
  generate_opening:
    type: llm
    prompt: opening  # Should resolve to {graph_dir}/prompts/opening.yaml
```

The runtime should resolve prompts relative to the graph file.

## Actual Behavior

```
Prompt not found: /path/to/project/prompts/opening.yaml
```

Still falls back to global `PROMPTS_DIR` because `execute_prompt()` is called without the prompts_relative params.

## Root Cause

In `node_factory.py`, the values are captured in the closure but not passed:

```python
# Line 218: Captured correctly
prompts_relative = defaults.get("prompts_relative", False)

# Line 303-310: NOT passed to execute_prompt
result = execute_prompt(
    prompt_name=prompt_name,
    variables=variables,
    output_model=output_model,
    temperature=temperature,
    provider=use_provider,
    # MISSING: graph_path=graph_path,
    # MISSING: prompts_dir=prompts_dir,
    # MISSING: prompts_relative=prompts_relative,
)
```

The executor.py signature was updated (lines 106-108, 238-240) but the call site in node_factory.py wasn't.

## Fix

Update `node_factory.py` line ~303:

```python
result = execute_prompt(
    prompt_name=prompt_name,
    variables=variables,
    output_model=output_model,
    temperature=temperature,
    provider=use_provider,
    graph_path=graph_path,
    prompts_dir=prompts_dir,
    prompts_relative=prompts_relative,
)
```

Also need to capture `prompts_dir` from defaults (currently only `prompts_relative` is captured):

```python
prompts_relative = defaults.get("prompts_relative", False)
prompts_dir = defaults.get("prompts_dir")  # ADD THIS
```

## Verification

```python
# With fix applied:
from yamlgraph.graph_loader import load_graph_config, compile_graph

config = load_graph_config("questionnaires/audit/graph.yaml")
# config.prompts_relative = True  ✓
# config.prompts_dir = "prompts"  ✓

graph = compile_graph(config)
app = graph.compile()
result = await app.ainvoke(...)  # Should work now
```

## Changelog Entry

```markdown
## [0.3.6] - 2026-01-XX

### Fixed
- **prompts_relative passthrough** - node_factory now passes graph_path, 
  prompts_dir, and prompts_relative to execute_prompt() calls
  - Completes the fix started in 0.3.5
```
