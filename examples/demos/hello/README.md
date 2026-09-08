# Hello World Demo

Minimal YAMLGraph example demonstrating basic LLM call with variable substitution
and inline-schema structured output, then submitting the greeting as a desktop
notification.

> **Side effect:** running this graph raises a real system notification
> (FR-1030). On a host with no notifier it still completes — the `notify` node
> declares `on_error: skip`, so the failure is recorded in `state.notified`
> instead of stopping the run.

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
2. Generates a structured greeting with:
   - `greeting` (message text)
   - `emoji` (tone marker)
   - `formality_level` (style classification)
3. Submits the greeting as a desktop notification via the shared
   [`send_toast`](../../shared/README.md#notify_toastpy---desktop-notification-fr-1030)
   tool, and records the outcome in `state.notified`

## Pipeline

```
START → greet → notify → END
```

## Key Concepts

- **`type: llm`** - Basic LLM node
- **Variable substitution** - `{state.name}` syntax
- **Prompt files** - Prompts in `prompts/` directory
- **`prompts_relative: true`** - Prompts relative to graph file
- **`type: tool_call` + `manifest:`** - Calling a shared Python tool declared
  by an FR-768 manifest, with no Python in this demo at all
- **`on_error: skip`** - Tolerance declared in the graph, not hidden in the
  tool: `send_toast` always raises, and the graph decides that a host without
  a notifier should still reach `END` with a visible failure envelope

## Files

```
hello/
├── graph.yaml          # Graph definition
└── prompts/
    └── greet.yaml      # Greeting prompt
```

## Learning Path

This is the **first demo** to try. Next: [router](../router/) for conditional logic.
