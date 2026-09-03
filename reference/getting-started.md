# YAMLGraph - AI Context Summary

> Quick reference for AI coding assistants (Copilot, Cursor, Claude) working with this codebase.
> For human developers, start with [quickstart.md](quickstart.md).

## What This Is

YAML-first framework for LLM pipelines. Graphs and prompts are declared in YAML, executed via LangGraph with Pydantic-validated outputs.

## Core Files

| File | Purpose |
|------|---------|
| `yamlgraph/graph_loader.py` | Compiles YAML → LangGraph StateGraph |
| `yamlgraph/executor.py` | `execute_prompt()` - unified LLM call interface |
| `yamlgraph/graph_cache.py` | Process-global `GRAPH_CACHE` for compiled graphs (FR-111) |
| `yamlgraph/node_factory.py` | Creates node functions from YAML config |
| `yamlgraph/utils/llm_factory.py` | Multi-provider LLM factory (12 providers) |
| `yamlgraph/models/state_builder.py` | Dynamic state class generation |
| `yamlgraph/contrib/utils.py` | Shared utilities (`to_serializable`) |

## Key Patterns

### 1. YAML Prompts (Never Hardcode)
```yaml
# prompts/greet.yaml
system: You are a friendly assistant.
user: Say hello to {name} in a {style} way.
```

### 2. YAML Graphs
```yaml
# graphs/example.yaml
version: "1.0"
name: example

nodes:
  step1:
    type: llm           # or: router, agent, tool, map, python
    prompt: greet       # references prompts/greet.yaml
    variables:                    # see expressions.md for syntax
      name: "{state.name}"
    state_key: output   # where result is stored

edges:
  - from: START
    to: step1
  - from: step1
    to: END
```

### 3. Pydantic Outputs
```yaml
# In prompt YAML
schema:
  name: Greeting
  fields:
    message:
      type: str
      description: The greeting message
```

Or define in `yamlgraph/models/schemas.py`.

### 4. LLM Factory
```python
from yamlgraph.utils.llm_factory import create_llm

llm = create_llm(provider="anthropic", temperature=0.7)
# Provider selection: parameter > YAML metadata > PROVIDER env > "anthropic"
```

### 5. Execute Prompt
```python
from yamlgraph.executor import execute_prompt

result = execute_prompt(
    prompt_name="greet",
    variables={"name": "World", "style": "casual"},
    schema=GreetingSchema,  # Optional Pydantic model
)
```

## Node Types

| Type | Purpose |
|------|---------|
| `llm` | Single LLM call with prompt |
| `router` | Classify → route to different nodes |
| `agent` | ReAct agent with tools |
| `tool` | Execute a registered tool |
| `tool_call` | Dynamic tool from state |
| `map` | Parallel execution over list |
| `python` | Custom Python function |
| `interrupt` | Human-in-the-loop pause/resume |
| `passthrough` | State transformation without LLM |
| `subgraph` | Nested graph execution |
| `interactive_tool` | Multi-turn conversation loop (start→ask→step↺→end) |
| `race` | Race multiple providers, return fastest |
| `pipeline` | Compile-time items × stages expansion |
| `copilot` | Delegate task to Copilot CLI or Claude Code CLI (`backend: claude`) |

## CLI Usage

```bash
# Run a graph with variables
yamlgraph graph run examples/demos/yamlgraph/graph.yaml --var topic=AI --var style=casual

# Show token usage summary after execution
yamlgraph graph run graph.yaml --var name=World --token-usage

# Show wall-clock LLM call timing summary after execution
yamlgraph graph run graph.yaml --var name=World --timing

# Inspect, validate, lint graphs
yamlgraph graph info examples/demos/router/graph.yaml
yamlgraph graph lint examples/demos/*/graph.yaml

# Visualize: authored Mermaid map; overlay an executed route (FR-723)
yamlgraph graph export examples/demos/reflexion/graph.yaml --mermaid
YAMLGRAPH_ROUTE_LOG=route.jsonl yamlgraph graph run examples/demos/reflexion/graph.yaml --var topic=AI
yamlgraph graph export examples/demos/reflexion/graph.yaml --mermaid --overlay route.jsonl
```

### Bench Command

Compare multiple provider/model combinations on the same graph:

```bash
# Run against two models and display comparison table
yamlgraph graph bench graph.yaml \
    --models anthropic/claude-haiku-4-5 openai/gpt-4o-mini \
    --var name=World

# Repeat each model 3 times and report mean/min/max duration
yamlgraph graph bench graph.yaml \
    --models anthropic/claude-haiku-4-5 openai/gpt-4o-mini \
    --runs 3

# Include full per-model output and export results to JSON
yamlgraph graph bench graph.yaml \
    --models anthropic/claude-haiku-4-5 openai/gpt-4o-mini \
    --full --export results.json
```

Model specs use `provider/model` format (e.g. `anthropic/claude-haiku-4-5`, `openai/gpt-4o-mini`). Per-model errors are captured gracefully without aborting the remaining models.

## Directory Structure

```
examples/         # Example applications and demos
  demos/          # Standalone demos (hello, router, reflexion, etc.)
prompts/          # Shared YAML prompt templates
yamlgraph/        # Core framework (~9,400 lines)
  cli/            # CLI commands
  models/         # Pydantic schemas, state builder
  node_factory/   # Node function creation (subpackage)
  tools/          # Agent tools (shell, python)
  utils/          # LLM factory, prompts, templates
  storage/        # Checkpointer factory, export
  linter/         # Graph linting
tests/
  unit/           # 1,100+ tests
  integration/    # Provider tests (need API keys)
reference/        # Documentation
```

## Error Handling

```python
from yamlgraph.models import PipelineError

try:
    result = execute_prompt(...)
except Exception as e:
    error = PipelineError.from_exception(e, node="node_name")
    return {"errors": [error], "current_step": "node_name"}
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Anthropic auth |
| `GOOGLE_API_KEY` | Google/Gemini auth |
| `INCEPTION_API_KEY` | Inception Labs Mercury auth |
| `MISTRAL_API_KEY` | Mistral auth |
| `OPENAI_API_KEY` | OpenAI auth |
| `REPLICATE_API_TOKEN` | Replicate auth |
| `DEEPSEEK_API_KEY` | DeepSeek auth |
| `XAI_API_KEY` | xAI Grok auth |
| `LMSTUDIO_BASE_URL` | LM Studio local URL |
| `PROVIDER` | Default provider |
| `LANGCHAIN_TRACING_V2=true` | Enable LangSmith |
| `YAMLGRAPH_OTEL_EXPORT=otlp` | OpenTelemetry spans ([otel-observability.md](otel-observability.md)) |

## LLM Providers

| Provider | Model Examples | Notes |
|----------|----------------|-------|
| `anthropic` | claude-sonnet-4-20250514 | Default. Best for complex reasoning |
| `google` | gemini-2.0-flash | Fastest mainstream |
| `inception` | mercury-2 | Diffusion LLM, 660 t/s, best for structured output |
| `mistral` | mistral-large-latest | Good cost/quality balance |
| `openai` | gpt-4.1 | Widely supported |
| `deepseek` | deepseek-chat, deepseek-reasoner | Reasoning models |
| `replicate` | meta/llama-* | Open model hosting |
| `xai` | grok-beta | Alternative |
| `lmstudio` | local | Local inference |

## Code Guidelines

- **< 400 lines** per module (max 500)
- **Type hints** on all functions
- **TDD**: Red-Green-Refactor
- **Python 3.11+**: Use `|` for unions
- **Deprecation**: Use `DeprecationError` to mark old APIs

## Anti-Patterns

❌ Hardcoded prompts → ✅ YAML in `prompts/`
❌ Untyped dicts → ✅ Pydantic models
❌ Direct state mutation → ✅ Return update dict
❌ `import os.getenv` spread → ✅ Use `yamlgraph.config`

## Quick Test

```bash
source .venv/bin/activate
pytest tests/unit/ -q --no-cov  # Fast unit tests
pytest tests/ -q                 # Full suite with coverage
```

## Status

- **Tests**: 886 pass, 87% coverage
- **Lint**: ruff clean
- **Python**: 3.11-3.13
