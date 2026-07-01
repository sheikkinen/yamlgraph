# Tool Call Demo

Demonstrates dynamic tool dispatch from graph state.

## Usage

```bash
yamlgraph graph run examples/demos/tool-call/graph.yaml --var text="hello world" --full
```

## Key Concepts

- **`type: tool_call`** — Dispatches to a tool identified by state variable
- **`type: python`** — Executes a Python function as a graph node
- **Dynamic dispatch** — Tool name resolved from `{state.task.tool}` at runtime
