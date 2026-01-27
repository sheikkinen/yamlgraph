# YAMLGraph

YAMLGraph is a YAML-first framework for building LLM pipelines with LangGraph.

## What is YAMLGraph?

YAMLGraph lets you define complex LLM workflows entirely in YAML. No Python boilerplate required.

## Key Benefits

- **Declarative**: Define pipelines in YAML, not Python
- **Type-Safe**: Pydantic models for structured outputs
- **Flexible**: Supports multiple LLM providers (Anthropic, OpenAI, Mistral)
- **Testable**: Built-in linting and validation

## Getting Started

Install YAMLGraph:

```bash
pip install yamlgraph
```

Create a simple pipeline:

```yaml
graph:
  name: hello-world
  nodes:
    greet:
      prompt: greet
  edges:
    - START -> greet
    - greet -> END
```
