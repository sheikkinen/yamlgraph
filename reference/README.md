# YAMLGraph Reference Documentation

Complete reference documentation for YAMLGraph v0.4.x.

See [CHANGELOG.md](../CHANGELOG.md) for version history.

## Index

### Getting Started

| Document | Description |
|----------|-------------|
| [Quick Start](quickstart.md) | Create your first pipeline in 5 minutes |
| [AI Context](getting-started.md) | Quick reference for AI coding assistants |

### Core References

| Document | Description |
|----------|-------------|
| [Graph YAML](graph-yaml.md) | Graph configuration: nodes, edges, tools, state |
| [Prompt YAML](prompt-yaml.md) | Prompt templates: schemas, messages, Jinja2 |
| [CLI Reference](cli.md) | Command-line interface: run, lint, validate, export diagrams |
| [Common Patterns](patterns.md) | Copy-paste patterns for pipelines |
| [Expressions](expressions.md) | Value and condition expression syntax |

### Node Types

| Node Type | In graph-yaml.md | Dedicated Reference |
|-----------|------------------|---------------------|
| `llm` | [§ LLM nodes](graph-yaml.md#type-llm---standard-llm-node) | - |
| `router` | [§ Router nodes](graph-yaml.md#type-router---conditional-routing) | - |
| `agent` | [§ Agent nodes](graph-yaml.md#type-agent---tool-using-agent) | [impl-agent.md](impl-agent.md) |
| `tool` | [§ Tool nodes](graph-yaml.md#type-tool---shell-tool-node) | - |
| `python` | [§ Python nodes](graph-yaml.md#type-python---python-function-node) | - |
| `map` | [§ Map nodes](graph-yaml.md#type-map---parallel-fan-out-node) | [map-nodes.md](map-nodes.md) |
| `interrupt` | [§ Interrupt nodes](graph-yaml.md#type-interrupt---human-in-the-loop) | [interrupt-nodes.md](interrupt-nodes.md) |
| `passthrough` | [§ Passthrough nodes](graph-yaml.md#type-passthrough---state-transformation) | [passthrough-nodes.md](passthrough-nodes.md) |
| `tool_call` | [§ Tool call nodes](graph-yaml.md#type-tool_call---dynamic-tool-execution) | [tool-call-nodes.md](tool-call-nodes.md) |
| `subgraph` | [§ Subgraph nodes](graph-yaml.md#type-subgraph---nested-graph) | [subgraph-nodes.md](subgraph-nodes.md) |
| `copilot` | [§ Copilot nodes](graph-yaml.md#type-copilot---copilot-cli-delegation) | - |
| `interactive_tool` | [§ Interactive tool](graph-yaml.md#type-interactive_tool---multi-turn-conversation-loop) | - |

### Advanced Features

| Document | Description |
|----------|-------------|
| [Streaming](streaming.md) | Token-by-token LLM output |
| [Async Usage](async-usage.md) | FastAPI integration & concurrent pipelines |
| [Checkpointers](checkpointers.md) | State persistence (Memory, SQLite, Redis) |
| [LangSmith Tools & Tracing](langsmith-tools.md) | Trace URLs, public sharing, and observability tools |
| [Prompt Deployment](prompt-deployment.md) | Patterns for updating prompts without rebuild |
| [Contrib Utilities](contrib.md) | Shared utilities for map results and serialization |
| [Scheduling Agents](scheduling-agents.md) | Run graphs on schedule (launchd, cron, CI) |

### Testing & Evaluation

| Document | Description |
|----------|-------------|
| [Promptfoo Evaluation](promptfoo-eval.md) | Systematic LLM prompt evaluation: deterministic assertions, LLM-as-judge, prompt isolation vs. graph evaluation |

### Examples & Guides

| Document | Description |
|----------|-------------|
| [Code Analysis](code-analysis.md) | Automated code quality analysis |
| [Implementation Agent](impl-agent.md) | 14-tool agent for codebase analysis |
| [Web UI & API](web-ui-api.md) | Serving graphs as web applications |
| [Intent + Questionnaire](intent-questionnaire-pattern.md) | Multi-graph routing with session registry |
| [FSM-as-Conductor](patterns/fsm-as-conductor.md) | statemachine-engine orchestrates lifecycle; YAMLGraph handles LLM |
| [LLM-as-Gate Pattern](patterns/llm-as-gate.md) | Semantic pass/fail gating with router edges |
| [Coded-Classification Pattern](patterns/coded-classification.md) | Classify free text against a controlled vocabulary: cluster fan-out, claim-reconciliation reducer, junk-drawer caps, labeled crosscheck harness |
| [Batch-Runner Pattern](patterns/batch-runner.md) | Run a graph over runtime-selected input files; transform on load, collect per-input results |
| [Corpus Map-Reduce Pattern](patterns/corpus-map-reduce.md) | Exhaustive bounded corpus analysis: freeze, typed map, deterministic reconciliation, hierarchical reduce, cited artifact |
| [Schema-Driven Extraction Pattern](patterns/schema-driven-extraction.md) | Declarative convergence loop for collecting structured data through conversation: schema, extract, detect gaps, probe, recap |

### Example Architectures

| Example | Description | Key Patterns |
|---------|-------------|--------------|
| [NPC Encounter](../examples/npc/architecture.md) | D&D encounter with web UI | Session adapter, HTMX, human-in-loop |
| [Cost Router](../examples/cost-router/) | LLM routing by complexity | Multi-provider, cost optimization |
| [Storyboard](../examples/storyboard/) | Animated story generation | Map nodes, image generation |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Graph YAML                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ nodes    │  │ edges    │  │ tools    │  │ defaults │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
└───────┼─────────────┼─────────────┼─────────────┼───────────────┘
        │             │             │             │
        ▼             ▼             ▼             ▼
┌───────────────┐ ┌─────────────┐ ┌───────────┐ ┌─────────────────┐
│ node_factory  │ │graph_loader │ │shell tools│ │ LLM settings    │
│ creates nodes │ │builds edges │ │for agents │ │ provider, temp  │
└───────┬───────┘ └──────┬──────┘ └─────┬─────┘ └────────┬────────┘
        │                │              │               │
        ▼                ▼              ▼               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LangGraph StateGraph                       │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Prompt YAML                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────────────┐  │
│  │ schema   │  │ system   │  │ user / template              │  │
│  │ (output) │  │ (persona)│  │ (with variables)             │  │
│  └────┬─────┘  └────┬─────┘  └────────────┬─────────────────┘  │
└───────┼─────────────┼──────────────────────┼────────────────────┘
        │             │                      │
        ▼             ▼                      ▼
┌───────────────┐ ┌─────────────┐ ┌─────────────────────────────┐
│schema_loader  │ │SystemMessage│ │ format_prompt               │
│→ Pydantic     │ │             │ │ (simple or Jinja2)          │
└───────────────┘ └─────────────┘ └─────────────────────────────┘
```

---

## File Locations

| Type | Location | Example |
|------|----------|---------|
| Graphs | `examples/demos/*/graph.yaml` | `examples/demos/yamlgraph/graph.yaml` |
| Prompts | `prompts/*.yaml` | `prompts/generate.yaml` |
| Grouped prompts | `prompts/group/*.yaml` | `prompts/router-demo/classify.yaml` |
| State classes | Auto-generated from YAML | `build_state_class(config)` |
| Output schemas | Inline in prompt YAML | `schema:` block |

---

## Key Concepts

### State
A TypedDict that flows through the pipeline. State is **automatically generated** from your graph configuration based on:
- Node `state_key` fields
- Node types (agent adds `messages`, router adds `_route`)
- Common input fields (`topic`, `style`, `input`, etc.)

```yaml
# State is auto-generated from graph config
nodes:
  generate:
    state_key: generated  # ← Auto-added to state
  analyze:
    state_key: analysis   # ← Auto-added to state
```

### Nodes
Processing steps. Each node:
1. Reads variables from state
2. Executes a prompt
3. Writes result to state

### Edges
Define flow between nodes. Can be:
- Linear: `from: A, to: B`
- Conditional: Based on state values
- Terminal: `to: END`

### Prompts
Self-contained YAML files with:
- Output schema (optional)
- System message
- User message with variables
