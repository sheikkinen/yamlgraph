# Verification Gate Demo (FR-164)

Deterministic post-execution checks on LLM node outputs.

## What It Does

Each node declares a `verification` with a falsifiable prediction:

```yaml
nodes:
  generate_points:
    type: llm
    prompt: generate_points
    state_key: key_points
    verification:
      question: "Will return 3-5 items about {topic}"
      on_fail: warn
```

After the node executes, the framework checks the prediction against the actual output. If the check fails, the configured action fires: `warn` (log and continue), `halt` (raise), or `retry` (re-execute).

## Supported Patterns

| Prediction | Check |
|-----------|-------|
| `"Will return N-M items"` | `min <= len(result) <= max` |
| `"Will return non-empty"` | `bool(result)` |
| `"Will contain {keyword}"` | `keyword in str(result)` |

## Run

```bash
yamlgraph graph lint examples/demos/verification-gate/graph.yaml
yamlgraph graph run examples/demos/verification-gate/graph.yaml \
  --var topic="graph neural networks" --full
```

## Why

Scripture: *"A plausible wrong answer is harder to catch than a crash."*

Silent failures — nodes that produce plausible but wrong outputs — are invisible to type validation. Verification gates turn stated expectations into runtime assertions.
