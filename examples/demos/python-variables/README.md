# Python Node Variables Demo

Demonstrates `variables:` expression resolution on `type: python` nodes (FR-252).

## Usage

```bash
# Validate the graph
yamlgraph graph lint examples/demos/python-variables/graph.yaml

# Run the graph
yamlgraph graph run examples/demos/python-variables/graph.yaml \
  --var user_name="Captain Hook" --var greeting_style="pirate" --full
```

## What It Does

1. Takes `user_name` and `greeting_style` as input
2. Resolves `{state.user_name}` and `{state.greeting_style}` into `name` and `style`
3. Python function receives pre-resolved variables — no manual state extraction

## Key Concepts

- **`variables:` on python nodes** — Declarative mapping from state to function arguments
- **Consistency** — Same `{state.field}` syntax as llm, router, and streaming nodes
- **No LLM required** — Pure Python execution with expression resolution

## Files

```
python-variables/
├── graph.yaml   # Graph with variables: mapping
├── tools.py     # Python function receiving resolved vars
└── README.md
```
