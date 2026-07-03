# Graph-Tool Demo — FR-658

Demonstrates `type: graph` tool — an agent uses a full YAMLGraph pipeline as an opaque tool.

## What it shows

- **Parent graph**: An agent node that writes marketing copy
- **Child graph**: A tone classifier pipeline (LLM node)
- **Graph-tool binding**: The agent calls `tone_check` without knowing it's a pipeline

## Run

```bash
yamlgraph graph run examples/demos/graph-tool/graph.yaml \
  --var topic="cloud computing" --var target_tone="casual" --full
```

## Flow

1. Agent drafts marketing copy about the topic
2. Agent calls `tone_check(text=<draft>)` — this invokes the child pipeline
3. Child pipeline classifies the tone (formal/casual/technical)
4. If tone ≠ target, agent rewrites and checks again
5. Agent returns final copy when tone matches
