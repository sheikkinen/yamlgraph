# YAMLGraph

> **Build production AI pipelines in minutes, not days.**
> Define your entire LLM workflow in YAML — routing, loops, agents, human-in-the-loop — and run it with one command.
> No boilerplate. Multi-provider. Observable. Version-controlled.

[![PyPI version](https://badge.fury.io/py/yamlgraph.svg)](https://pypi.org/project/yamlgraph/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

```bash
pip install yamlgraph
yamlgraph graph run examples/demos/hello/graph.yaml --var name="World" --var style="enthusiastic"
```

A YAML-first framework for building LLM pipelines using:

- **YAML Graph Configuration** - Declarative pipeline definition with schema validation
- **YAML Prompts** - Declarative prompt templates with Jinja2 support
- **Pydantic Models** - Structured LLM outputs
- **Multi-Provider LLMs** - anthropic, azure, deepseek, google, inception, lmstudio, mistral, openai, replicate, vertex, xai
- **LangGraph** - Pipeline orchestration with resume support
- **Human-in-the-Loop** - Interrupt nodes for user input
- **Streaming** - Token-by-token LLM output (prompt-level and graph-level)
- **Async Support** - FastAPI-ready async execution
- **Checkpointers** - Memory, SQLite, and Redis state persistence
- **Graph-Relative Prompts** - Colocate prompts with graphs
- **JSON Extraction** - Auto-extract JSON from LLM responses
- **LangSmith** - Observability and tracing
- **JSON Export** - Result serialization
- **Contrib Utilities** - Shared helpers for map results and Pydantic serialization

## What is YAMLGraph?

**YAMLGraph** is a declarative LLM pipeline orchestration framework that lets you define complex AI workflows entirely in YAML—no Python required for 60-80% of use cases. Built on LangGraph, it provides multi-provider LLM support (`anthropic`, `azure`, `deepseek`, `google`, `inception`, `lmstudio`, `mistral`, `openai`, `replicate`, `vertex`, `xai`), parallel batch processing via map nodes (using LangGraph Send), LLM-driven conditional routing, graph-level streaming, and human-in-the-loop interrupts with checkpointing. Pipelines are version-controlled, linted, and observable via LangSmith. The key insight: by constraining the API surface to YAML + Jinja2 templates + Pydantic schemas, YAMLGraph trades some flexibility for dramatically faster prototyping, easier maintenance, and built-in best practices—making it ideal for teams who want production-ready AI pipelines without the complexity of full-code frameworks.

## When NOT to Use YAMLGraph

YAMLGraph trades flexibility for simplicity. Consider raw LangGraph or other tools when:

| Scenario | Why YAMLGraph isn't ideal |
|----------|--------------------------|
| **Dynamic graph topology** | Graph structure is compiled from YAML at load time; edges cannot be added or removed at runtime |
| **Complex state transformations** | YAML expressions support basic arithmetic and list operations; multi-step logic belongs in Python |
| **Custom node types per-invoke** | Node types are fixed at compile time (though model and provider can vary per-invoke) |
| **Native multi-modal pipelines** | Text is the only native modality; image/audio requires custom Python nodes via `type: python` |

**Rule of thumb:** If you're fighting the YAML to express your logic, use Python — either via `type: python` nodes within YAMLGraph, or raw LangGraph for full control.

## Installation

### From PyPI

```bash
pip install yamlgraph

# With Redis support for distributed checkpointing
pip install yamlgraph[redis]
```

### From Source

```bash
git clone https://github.com/sheikkinen/yamlgraph.git
cd yamlgraph
pip install -e ".[dev]"
```

## Quick Start

### 1. Create a Prompt

Create `prompts/greet.yaml`:

```yaml
system: |
  You are a friendly assistant.

user: |
  Say hello to {name} in a {style} way.
```

### 2. Create a Graph

Create `graphs/hello.yaml`:

```yaml
version: "1.0"
name: hello-world

nodes:
  greet:
    type: llm
    prompt: greet
    variables:
      name: "{state.name}"
      style: "{state.style}"
    state_key: greeting

edges:
  - from: START
    to: greet
  - from: greet
    to: END
```

### 3. Set API Key

```bash
export ANTHROPIC_API_KEY=your-key-here
# Or: export MISTRAL_API_KEY=... or OPENAI_API_KEY=...
```

### 4. Run It

```bash
yamlgraph graph run graphs/hello.yaml --var name="World" --var style="enthusiastic"
```

Or use the Python API:

```python
from yamlgraph import load_and_compile

graph = load_and_compile("graphs/hello.yaml")
app = graph.compile()
result = app.invoke({"name": "World", "style": "enthusiastic"})
print(result["greeting"])
```

With tracing (when LangSmith is configured via `.env` or env vars):

```python
from yamlgraph import load_and_compile, create_tracer, get_trace_url, inject_tracer_config

graph = load_and_compile("graphs/hello.yaml")
app = graph.compile()
tracer = create_tracer()  # None if LangSmith not configured
result = app.invoke({"name": "World"}, config=inject_tracer_config({}, tracer))
print(get_trace_url(tracer))  # https://smith.langchain.com/o/.../r/...
```

---

## More Examples

```bash
# Content generation pipeline
yamlgraph graph run examples/demos/yamlgraph/graph.yaml --var topic="AI" --var style=casual

# Sentiment-based routing
yamlgraph graph run examples/demos/router/graph.yaml --var message="I love this!"

# Self-correction loop (Reflexion pattern)
yamlgraph graph run examples/demos/reflexion/graph.yaml --var topic="climate change"

# Execution path visualization: capture routes, render the map, overlay the run
YAMLGRAPH_ROUTE_LOG=route.jsonl yamlgraph graph run examples/demos/reflexion/graph.yaml --var topic="AI"
yamlgraph graph export examples/demos/reflexion/graph.yaml --mermaid --overlay route.jsonl

# AI agent with shell tools
yamlgraph graph run examples/demos/git-report/graph.yaml --var input="What changed recently?"

# Web research agent (requires: pip install yamlgraph[websearch])
yamlgraph graph run examples/demos/web-research/graph.yaml --var topic="LangGraph tutorials"

# Show LangSmith trace URL (requires LANGCHAIN_TRACING_V2=true + LANGSMITH_API_KEY)
yamlgraph graph run examples/demos/yamlgraph/graph.yaml --var topic="AI" --share-trace
```

📂 **More examples:** See [examples/README.md](examples/README.md) for the full catalog including:
- Parallel fan-out with map nodes
- Human-in-the-loop interview flows
- Code quality analysis pipelines
- FastAPI integrations

## Documentation

📚 **Start here:** [reference/README.md](reference/README.md) - Complete reference documentation index

### Reading Order

| Level | Document | Description |
|-------|----------|-------------|
| 🟢 Beginner | [Quick Start](reference/quickstart.md) | Create your first pipeline in 5 minutes |
| 🟢 Beginner | [Graph YAML](reference/graph-yaml.md) | Node types, edges, tools, state |
| 🟢 Beginner | [Prompt YAML](reference/prompt-yaml.md) | Schema and template syntax |
| 🟡 Intermediate | [Common Patterns](reference/patterns.md) | Router, loops, agents |
| 🟡 Intermediate | [Map Nodes](reference/map-nodes.md) | Parallel fan-out processing |
| 🟡 Intermediate | [Interrupt Nodes](reference/interrupt-nodes.md) | Human-in-the-loop |
| 🔴 Advanced | [Subgraph Nodes](reference/subgraph-nodes.md) | Modular graph composition |
| 🔴 Advanced | [Async Usage](reference/async-usage.md) | FastAPI integration |
| 🔴 Advanced | [Checkpointers](reference/checkpointers.md) | State persistence |

**More resources:**
- **[Examples](examples/)** - Working demos and production patterns
- **[Feature Requests](feature-requests/)** - Roadmap and planned improvements
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Internal architecture for core developers

## Architecture

🏗️ **For core developers:** See [ARCHITECTURE.md](ARCHITECTURE.md) for:
- Module architecture and data flows
- Extension points (adding node types, providers, tools)
- Testing strategy and patterns
- Code quality rules

See [ARCHITECTURE.md](ARCHITECTURE.md#file-reference) for detailed module line counts and responsibilities.

## Key Patterns

📚 **Full guide:** See [reference/patterns.md](reference/patterns.md) for comprehensive patterns including:
- Linear pipelines with dependencies
- Branching and conditional routing
- Map-reduce parallel processing
- LLM-based routing
- Human-in-the-loop workflows
- Self-correction loops (Reflexion)
- Agent patterns with tools

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes* | Anthropic API key (* if using Anthropic) |
| `MISTRAL_API_KEY` | No | Mistral API key (required if using Mistral) |
| `OPENAI_API_KEY` | No | OpenAI API key (required if using OpenAI) |
| `PROVIDER` | No | Default LLM provider (anthropic/azure/deepseek/google/inception/lmstudio/mistral/openai/replicate/vertex/xai) |
| `ANTHROPIC_MODEL` | No | Anthropic model (default: claude-haiku-4-5) |
| `MISTRAL_MODEL` | No | Mistral model (default: mistral-large-latest) |
| `OPENAI_MODEL` | No | OpenAI model (default: gpt-4o) |
| `REPLICATE_API_TOKEN` | No | Replicate API token |
| `REPLICATE_MODEL` | No | Replicate model (default: ibm-granite/granite-4.0-h-small) |
| `XAI_API_KEY` | No | xAI API key |
| `XAI_MODEL` | No | xAI model (default: grok-4-1-fast-reasoning) |
| `LMSTUDIO_BASE_URL` | No | LM Studio server URL (default: http://localhost:1234/v1) |
| `GOOGLE_API_KEY` | No | Google API key (required if using Google/Gemini) |
| `GOOGLE_MODEL` | No | Google model (default: gemini-2.0-flash) |
| `LMSTUDIO_MODEL` | No | LM Studio model (default: qwen2.5-coder-7b-instruct) |
| `LANGCHAIN_TRACING_V2` | No | Enable LangSmith tracing (`true` to enable) |
| `YAMLGRAPH_ROUTE_LOG` | No | Route decision log (FR-723): `1` = emit JSON route lines on the `yamlgraph.route` logger; a file path = also append raw JSONL for `graph export --overlay` |
| `LANGSMITH_API_KEY` | No | LangSmith API key |
| `LANGCHAIN_ENDPOINT` | No | LangSmith endpoint URL |
| `LANGCHAIN_PROJECT` | No | LangSmith project name |

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/ -v

# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v

# Run with coverage report
pytest tests/ --cov=yamlgraph --cov-report=term-missing

# Run with HTML coverage report
pytest tests/ --cov=yamlgraph --cov-report=html
# Then open htmlcov/index.html
```

See [ARCHITECTURE.md](ARCHITECTURE.md#testing-strategy) for testing patterns and fixtures.

## Development Process

YAMLGraph follows a structured development workflow documented in [the Scripture](.github/copilot-instructions.md):

1. **Research** — Explore alternatives before coding
2. **Plan** — Write a feature request with acceptance criteria
3. **Judge** — Critically review until scope is minimal and clear
4. **Enforce** — TDD, smallest sufficient change
5. **Distill** — Capture lessons in `docs/diary/`

New contributors: read the Scripture before your first PR.

## Security

### Shell Command Injection Protection

Shell tools (defined in `graphs/*.yaml` with `type: tool`) execute commands with variable substitution. All user-provided variable values are sanitized using `shlex.quote()` to prevent shell injection attacks.

```yaml
# In graph YAML - command template is trusted
tools:
  git_log:
    type: shell
    command: "git log --author={author} -n {count}"
```

**Security model:**
- ✅ **Command templates** (from YAML) are trusted configuration
- ✅ **Variable values** (from user input/LLM) are escaped with `shlex.quote()`
- ✅ **Complex types** (lists, dicts) are JSON-serialized then quoted
- ✅ **No `eval()`** - condition expressions parsed with regex, not evaluated

**Example protection:**
```python
# Malicious input is safely escaped
variables = {"author": "$(rm -rf /)"}
# Executed as: git log --author='$(rm -rf /)'  (quoted, harmless)
```

See [yamlgraph/tools/shell.py](yamlgraph/tools/shell.py) for implementation details.

### ⚠️ Security Considerations

**Shell tools execute real commands** on your system. While variables are sanitized:

1. **Command templates are trusted** - Only use shell tools from trusted YAML configs
2. **No sandboxing** - Commands run with your user permissions
3. **Agent autonomy** - Agent nodes may call tools unpredictably
4. **Review tool definitions** - Audit `tools:` section in graph YAML before running

For production deployments, consider:
- Running in a container with limited permissions
- Restricting available tools to read-only operations
- Implementing approval workflows for sensitive operations

## License

[MIT w/ SWC](LICENSE)

Last reviewed: 2026-05-03
