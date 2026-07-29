---
name: author-graph
description: "Author YAMLGraph graph YAML files. Use when: creating or editing graph YAML, adding nodes or edges, configuring routing and conditions, setting up state keys, variables, data_files, tools, loop limits, error handling, or verification gates. Syntax reference only — for end-to-end creation of a complete new graph artifact, use the graph-authoring skill."
argument-hint: "node type, field name, or graph structure question"
---

# Author Graph YAML

Create and configure YAMLGraph graph files. Canonical source: `reference/graph-yaml.md` and `reference/expressions.md`.

> **Scope boundary:** this is the graph YAML *syntax reference*. For the
> end-to-end workflow of creating a complete new graph artifact
> (precedent search, validation, delegation via `scripts/author.sh`), use
> the `graph-authoring` skill — it composes this one.

## File Structure

```yaml
version: "1.0"
name: my-pipeline
description: What this graph does
defaults: { provider: mistral, temperature: 0.7 }
data_files: { schema: schema.yaml }  # Load external YAML into state
tools: { tool_name: { ... } }
nodes: { node_name: { ... } }       # Required
edges:                                # Required
  - from: START
    to: node_name
loop_limits: { node_name: 3 }
```

## Defaults

```yaml
defaults:
  provider: anthropic         # LLM provider (priority: node > defaults > env > anthropic)
  temperature: 0.7
  thinking_budget: 8000       # Extended thinking (anthropic: ≥1024, google: any int or -1)
  prompts_relative: true      # Resolve prompts relative to graph file
```

## Tools

```yaml
tools:
  my_shell_tool:
    type: shell
    command: git -C {repo_path} log --since={since}
    parse: text

  my_python_tool:
    type: python
    path: tools.py          # GRAPH-RELATIVE file — use for graph-local tools
    function: my_function

  my_module_tool:
    type: python
    module: examples.pkg.nodes.mod   # dotted IMPORT — needs importable package
    function: my_function
```

**`path:` vs `module:` for python tools:** graphs with a sibling
`tools.py` (chaplain graphs, standalone graph dirs) must use
`path: tools.py`; `module:` requires the module on `sys.path` and
fails from graph directories as
`Cannot import module 'tools': No module named 'tools'` (strict
mode names the tool, not the fix). Field incident: FR-744 enforce,
2026-07-17 — the philosopher precedent (`path:`) is the working form.

## Node Types

### Common Properties
| Property | Default | Description |
|----------|---------|-------------|
| `type` | `"llm"` | `llm`, `router`, `agent`, `tool`, `python`, `map`, `interrupt`, `passthrough`, `tool_call`, `subgraph`, `copilot`, `pipeline`, `race`, `interactive_tool` |
| `prompt` | — | Prompt file path (without `.yaml`) |
| `variables` | `{}` | Template variable mappings |
| `state_key` | node name | State key for result |
| `requires` | `[]` | Required state keys |
| `skip_if_exists` | `true` | Skip if truthy (`[]`, `""`, `None` do NOT skip) |
| `on_error` | `"fail"` | `skip`, `retry`, `fail`, `fallback` |
| `timeout` | `null` | Per-node timeout in seconds |

### `type: llm` — Standard LLM

```yaml
generate:
  type: llm
  prompt: generate
  temperature: 0.8
  variables:
    topic: "{state.topic}"
  state_key: generated
  parse_json: true            # Extract JSON from markdown blocks
  stream: true                # Token-by-token streaming
```

### `type: router` — Conditional Routing

```yaml
classify:
  type: router
  prompt: classify_tone
  route_field: tone           # Required: schema field to route on
  routes:
    positive: respond_positive
    negative: respond_negative
  default_route: respond_neutral
```

### `type: agent` — Tool-Using Agent

```yaml
analyze:
  type: agent
  prompt: analyzer
  tools: [run_ruff, run_tests]  # From graph's tools section
  max_iterations: 8
  state_key: analysis
```

### `type: map` — Parallel Fan-Out

```yaml
animate:
  type: map
  over: "{state.panels}"     # List to iterate
  as: panel                   # Variable name per item
  node:
    type: llm
    prompt: animate_panel
  collect: animated_panels    # Results collected here
```

### `type: passthrough` — State Transformation

```yaml
increment:
  type: passthrough
  output:
    counter: "{state.counter + 1}"
    history: "{state.history + [state.current]}"
```

### `type: interrupt` — Human-in-the-Loop

```yaml
ask_name:
  type: interrupt
  message: "What is your name?"
  resume_key: user_name
```

Requires `checkpointer:` in graph config.

### Other Node Types

| Type | Key Properties | See |
|------|---------------|-----|
| `copilot` | `cli_flags`, `backend: cli\|api`, `timeout`, session `resume` | `reference/graph-yaml.md` |
| `race` | `candidates: [{provider, model}]`, first successful response wins | `reference/graph-yaml.md` |
| `subgraph` | `graph`, `input_mapping`, `output_mapping` | `reference/subgraph-nodes.md` |
| `pipeline` | `items` (with `name`), `stages`, `{item.field}` interpolation | `reference/graph-yaml.md` |
| `tool_call` | `tool_name: "{state.x}"`, `tool_args: "{state.y}"` | `reference/tool-call-nodes.md` |
| `interactive_tool` | `start`, `step`, `end`, `loop_until` | `reference/graph-yaml.md` |

## Edges

```yaml
edges:
  - from: START
    to: generate                          # Entry point
  - from: generate
    to: analyze                           # Linear
  - from: analyze
    to: END                               # Terminal
  - from: critique                        # Conditional
    to: refine
    condition: critique.score < 0.8
  - from: classify                        # Router
    to: [positive, negative, neutral]
    type: conditional
  - from: generate                        # Parallel fan-out
    to: [analyze, summarize, translate]
```

`to: [list]` + `type: conditional` = pick ONE. Without `type: conditional` = run ALL concurrently.

## Expressions Quick Reference

### Value Expressions (in `variables:`, `output:`)

`state.` prefix **required**. Operators: `+`, `-`, `*`, `/`.

```yaml
variables:
  name: "{state.name}"                         # Simple path
  score: "{state.critique.score}"              # Nested
output:
  counter: "{state.counter + 1}"               # Arithmetic
  history: "{state.history + [state.item]}"    # List append
  log: "{state.log + {'key': state.val}}"      # Dict append
```

### Condition Expressions (in edge `condition:`)

No braces, no `state.` prefix. Strings must be quoted. No `eval()`.

```yaml
condition: score < 0.8
condition: status == 'done'
condition: a.b >= threshold
```

Operators: `<`, `<=`, `>`, `>=`, `==`, `!=`. Full reference: `reference/expressions.md`.

## Error Handling & Guards

```yaml
on_error: fallback
fallback: { provider: anthropic }

verification:
  question: "Will return 3-10 items about {topic}"
  on_fail: warn    # warn | halt | retry

guards:
  pre:
    - check: "state.fr_path | file_exists"
      on_fail: halt
```

Full reference: `reference/graph-yaml.md`.

## Smoke Test

```bash
yamlgraph graph lint examples/demos/hello/graph.yaml
yamlgraph graph run examples/demos/hello/graph.yaml --var name="World" --var style="casual" --full
```
