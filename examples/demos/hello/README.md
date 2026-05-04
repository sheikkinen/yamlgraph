# Hello World Demo

Minimal YAMLGraph example demonstrating basic LLM call with variable substitution.

## Usage

```bash
# Validate the graph
yamlgraph graph lint examples/demos/hello/graph.yaml

# Run the graph
yamlgraph graph run examples/demos/hello/graph.yaml \
  --var name="World" --var style="enthusiastic"
```

### Vertex Gemini 3.1 smoke (Express mode)

Use environment-level provider/model selection (the CLI does not expose direct
`--provider` / `--model` flags):

```bash
export VERTEX_API_KEY="your-key"
export PROVIDER="vertex"
export VERTEX_MODEL="gemini-3.1-pro"
yamlgraph graph run examples/demos/hello/graph.yaml \
  --var name="World" --var style="holy see of code" --full
```

Verified model identifiers for project `scp-tenant-dps-dev`:

- Pro: `gemini-3.1-pro` (if region/project catalog requires pinned ID, use `gemini-3.1-pro-001`)
- Flash: `gemini-3.1-flash` (if region/project catalog requires pinned ID, use `gemini-3.1-flash-001`)

## What It Does

1. Takes `name` and `style` as input
2. Generates a personalized greeting

## Pipeline

```
START → greet → END
```

## Key Concepts

- **`type: llm`** - Basic LLM node
- **Variable substitution** - `{state.name}` syntax
- **Prompt files** - Prompts in `prompts/` directory
- **`prompts_relative: true`** - Prompts relative to graph file

## Files

```
hello/
├── graph.yaml          # Graph definition
└── prompts/
    └── greet.yaml      # Greeting prompt
```

## Learning Path

This is the **first demo** to try. Next: [router](../router/) for conditional logic.
