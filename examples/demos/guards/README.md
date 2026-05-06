# Deterministic Node Guards Demo

Demonstrates `guards.pre` and `guards.post` on an `llm` node.

## What it shows

- **Pre guard (`skip`)**: Prevents expensive node execution unless `run_llm=true`
- **Post guard (`warn`)**: Checks output length deterministically after execution

## Run

```bash
# Fast path: pre-guard skips LLM call (no provider key needed)
yamlgraph graph run examples/demos/guards/graph.yaml \
  --var run_llm=false \
  --var topic="deterministic guards" \
  --full
```

To execute the LLM node and exercise post-guards, run with `--var run_llm=true`.
