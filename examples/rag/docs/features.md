# YAMLGraph Features

## Core Features

### YAML-First Design

All pipelines are defined in YAML. Prompts, state, edges - everything is declarative.

### Multi-Provider Support

Switch between LLM providers with a single line:

```yaml
nodes:
  analyze:
    prompt: analyze
    provider: anthropic  # or openai, mistral
```

### Structured Outputs

Define output schemas inline or in separate files:

```yaml
nodes:
  extract:
    prompt: extract
    output_schema:
      name: str
      age: int
```

### Map Nodes

Process lists in parallel:

```yaml
nodes:
  process_all:
    type: map
    over: "{state.items}"
    node:
      prompt: process_item
```

### Router Nodes

Conditional branching based on LLM decisions:

```yaml
nodes:
  route:
    type: router
    prompt: classify
    routes:
      simple: handle_simple
      complex: handle_complex
```

### Tool Integration

Call Python functions or shell commands:

```yaml
nodes:
  search:
    type: tool
    tool: yamlgraph.tools.rag_retrieve
    args:
      collection: my_docs
      query: "{state.question}"
```

## Advanced Features

### Checkpointing

Persist state across runs with SQLite or Redis.

### Memory

Conversation memory for chat applications.

### Subgraphs

Compose pipelines from reusable components.

### Streaming

Stream LLM outputs for real-time feedback.
