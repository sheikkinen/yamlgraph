# Cache Demo (FR-032)

Demonstrates per-node result caching via LangGraph `CachePolicy`.

## YAML Syntax

```yaml
nodes:
  # Cache indefinitely (same inputs → same output, no re-call)
  summarize:
    cache: true

  # Cache with TTL (expires after 60 seconds)
  expand:
    cache:
      ttl: 60
```

## Run

```bash
yamlgraph graph lint examples/demos/cache/graph.yaml
yamlgraph graph run examples/demos/cache/graph.yaml --var topic="quantum computing" --full
```

Re-running with the same `topic` skips cached nodes when a checkpointer is configured.
