# Agent JSON Demo

Minimal agent node with structured JSON output (FR-449).
Demonstrates that agent nodes return `dict` (not `str`) when the prompt
defines an inline `schema:` block.

## Usage

```bash
# Validate the graph
yamlgraph graph lint examples/demos/agent-json/graph.yaml

# Run the graph
yamlgraph graph run examples/demos/agent-json/graph.yaml \
  --var file_path="README.md" --full
```

## What It Tests

- Agent node with a single shell tool (`wc -l` + `head -5`)
- Inline Pydantic schema in the prompt YAML (`Analysis` with `summary`, `line_count`, `verdict`)
- Structured output extraction: `extract_json` → `model_validate` → fallback `with_structured_output`
