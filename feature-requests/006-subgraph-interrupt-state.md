# Feature Request: Subgraph State Exposure During Interrupts

**ID:** 006  
**Priority:** P2 - Nice to Have  
**Status:** ✅ Implemented (v0.3.8)  
**Effort:** 2-3 days  
**Requested:** 2026-01-20  
**Implemented:** 2026-01-20  

## Summary

Expose selected subgraph state to the parent graph when a subgraph hits an interrupt node. Currently, `output_mapping` only applies when the subgraph completes (reaches END).

## Motivation

When building multi-part questionnaire flows with subgraphs, the parent graph has no visibility into the current subgraph's progress during interrupts. This makes debugging and monitoring difficult:

**Current behavior:**
```python
result = parent_graph.invoke({"user_message": ""}, config)
# result contains only parent state, subgraph state is hidden
print(result.get("phase"))      # None
print(result.get("extracted"))  # None
print(result.get("gaps"))       # None
```

**Use cases:**
- CLI debug output showing extraction progress
- API response including current phase and extracted fields
- Monitoring dashboards tracking conversation state
- Logging for troubleshooting stuck conversations

## Proposed Solution

### Option A: `interrupt_output_mapping`

Add a separate mapping that applies during interrupts:

```yaml
nodes:
  run_demographics:
    type: subgraph
    graph: demographics/graph.yaml
    input_mapping:
      user_message: user_message
    output_mapping:            # Applied on subgraph completion
      demographics_complete: complete
      demographics_extracted: extracted
    interrupt_output_mapping:  # Applied on subgraph interrupt
      current_phase: phase
      current_extracted: extracted
      current_gaps: gaps
```

### Option B: Unified mapping with `on_interrupt` flag

```yaml
nodes:
  run_demographics:
    type: subgraph
    graph: demographics/graph.yaml
    output_mapping:
      demographics_complete: 
        from: complete
        on: complete           # Only on completion
      demographics_extracted:
        from: extracted
        on: complete
      current_phase:
        from: phase
        on: interrupt          # During interrupts
      current_extracted:
        from: extracted
        on: [interrupt, complete]  # Both
```

### Option C: Auto-prefix subgraph state

Automatically expose subgraph state with a prefix:

```yaml
nodes:
  run_demographics:
    type: subgraph
    graph: demographics/graph.yaml
    expose_state: true         # or: expose_state: "demographics_"
```

Result would include:
```python
{
    "demographics_phase": "probing",
    "demographics_extracted": {...},
    "demographics_gaps": ["gender", "living_arrangement"]
}
```

## Recommendation

**Option A** is cleanest - explicit separate mapping for interrupt vs completion. It's easy to understand and doesn't change existing behavior.

## Implementation Notes

### Initial Approach (Failed)

The naive approach assumed `compiled.invoke()` returns a dict with `__interrupt__`:

```python
child_output = compiled.invoke(child_input, child_config)
if "__interrupt__" in child_output:
    return apply_mapping(child_output, interrupt_mapping)
```

**Problem:** When invoked from within a parent node, `compiled.invoke()` raises `GraphInterrupt` exception instead of returning. The exception propagates up, bypassing any mapping code.

### Working Solution: Pregel Internal API

LangGraph's execution engine is called **Pregel** (named after [Google's Pregel paper](https://research.google/pubs/pub36726/) for distributed graph processing).

The Pregel runtime passes internal mechanisms via `config["configurable"]`:

```python
config = {
    "configurable": {
        "thread_id": "...",
        "__pregel_send": <deque.extend>,      # Inject state updates
        "__pregel_checkpointer": <Saver>,     # Checkpoint access
        "__pregel_task_id": "...",            # Current task ID
        # ... more internal plumbing
    }
}
```

**Solution:** Use `__pregel_send` to inject mapped child state **before** re-raising the interrupt:

```python
except GraphInterrupt as e:
    if interrupt_output_mapping:
        # Get child state from checkpointer
        child_state = compiled.get_state(child_config)
        parent_updates = _map_output_state(child_state.values, interrupt_output_mapping)
        
        # Use Pregel's internal send to inject updates
        send = config.get("configurable", {}).get("__pregel_send")
        if send:
            send([(k, v) for k, v in parent_updates.items()])
    
    raise  # Re-raise to pause the graph
```

### Caveats

⚠️ **`__pregel_send` is an internal, undocumented API.** It may change in future LangGraph versions.

There is no official way to update state when a node raises an exception. This solution was discovered by inspecting the config passed to nodes and testing behavior.

### References

- [Google Pregel Paper](https://research.google/pubs/pub36726/) - Original distributed graph processing model
- [LangGraph Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) - Official interrupt documentation
- [LangGraph Subgraphs with Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts#using-with-subgraphs-called-as-functions) - Subgraph interrupt behavior
- [LangGraph Errors Reference](https://reference.langchain.com/python/langgraph/errors/) - `GraphInterrupt` exception docs
- [LangGraph Types Reference](https://reference.langchain.com/python/langgraph/types/) - `interrupt()` function docs

## Alternatives Considered

### 1. Access subgraph state via checkpointer
**Rejected:** Requires knowing subgraph thread_id structure, not portable.

### 2. Return full subgraph state nested
**Rejected:** Pollutes parent state, hard to work with.

### 3. Debug mode that logs subgraph state
**Partial:** Useful for logging but doesn't help API responses.

## Acceptance Criteria

- [x] `interrupt_output_mapping` recognized in subgraph node config
- [x] Mapping applies when subgraph returns with `__interrupt__`
- [x] Original `output_mapping` still only applies on completion
- [x] Works with nested subgraphs
- [x] Schema validation for new config key
- [x] Documentation updated
- [x] Test with multi-turn subgraph flow

## Example Use Case

questionnaire-api parent orchestrator:

```yaml
nodes:
  run_demographics:
    type: subgraph
    graph: demographics/graph.yaml
    input_mapping:
      user_message: user_message
    output_mapping:
      demographics_complete: complete
      demographics_extracted: extracted
    interrupt_output_mapping:
      active_subgraph: "'demographics'"  # Literal
      current_phase: phase
      current_extracted: extracted
      current_gaps: gaps
```

CLI can then show:
```
🤖 What year were you born?
----------------------------------------
Subgraph: demographics
Phase: probing
Extracted: {birth_year: 1956, gender: 2}
Gaps: [primary_language, marital_status, living_arrangement, residence_type, referral_source]
```

## Related

- Feature #001: Interrupt Node (dependency - this extends interrupt behavior)
- LangGraph subgraph docs: https://langchain-ai.github.io/langgraph/how-tos/subgraph/
