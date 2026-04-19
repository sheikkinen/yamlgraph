# Map Timeout Demo

Demonstrates `timeout` on map nodes (FR-069).

## What This Shows

- Per-branch timeout enforcement on `type: map` nodes
- Fast and medium tasks complete normally
- Slow task (5s delay) is terminated after 1s timeout
- Timed-out branches return structured error results with `_error_type: TimeoutError`

## Usage

```bash
yamlgraph graph run examples/demos/map-timeout/graph.yaml --full
```

## Key Pattern

```yaml
nodes:
  process:
    type: map
    over: "{state.workload.tasks}"
    as: task
    collect: results
    timeout: 1.0          # <-- branches killed after 1 second
    node:
      type: python
      tool: slow_task
      state_key: result
```
