# Feature Request: Subgraph State Exposure During Interrupts

**ID:** 006  
**Priority:** P2 - Nice to Have  
**Status:** ✅ Implemented (v0.3.7)  
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

```python
# yamlgraph/subgraph_node.py

def create_subgraph_node(node_name: str, node_config: dict) -> Callable:
    subgraph = load_subgraph(node_config["graph"])
    output_mapping = node_config.get("output_mapping", {})
    interrupt_mapping = node_config.get("interrupt_output_mapping", {})
    
    def subgraph_fn(state: dict) -> dict:
        result = run_subgraph(subgraph, state, node_config.get("input_mapping"))
        
        if result.get("__interrupt__"):
            # Apply interrupt mapping
            return apply_mapping(result, interrupt_mapping)
        else:
            # Apply completion mapping
            return apply_mapping(result, output_mapping)
    
    return subgraph_fn
```

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
