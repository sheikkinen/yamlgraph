# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**YAMLGraph** is a YAML-first framework for building LLM pipelines using LangGraph. The key insight: 60-80% of AI workflows can be defined entirely in YAML (graphs + prompts + schemas) without writing Python code. Built on LangGraph with multi-provider LLM support (Anthropic, Mistral, OpenAI).

## Development Process

Before implementing any feature or fix:

### 1. Research First
- Analyze existing solutions and alternatives
- Check if the problem is already solved elsewhere in the codebase
- Review similar patterns in `examples/` and `reference/`

### 2. Plan Before Coding
- Create an implementation plan (feature request or issue)
- Define acceptance criteria upfront
- Estimate effort realistically

### 3. Critical Review
- Plans need multiple iterations
- Challenge assumptions: "Is this the right approach?"
- Get feedback before writing code

### 4. Reflect: Is This Really Needed?
- Documenting patterns is cheaper than new code
- Showing alternatives without implementation often suffices
- Ask: "Does this belong in YAMLGraph, or is it a deployment/application concern?"

> **Example**: URL-based prompt loading was proposed as a 2-day feature. After reflection, we realized documenting deployment patterns (volume mounts, git-sync, ConfigMaps) solved the same problem without adding framework complexity. See `reference/prompt-deployment.md`.

## Development Commands

### Environment Setup
```bash
# Install in development mode
pip install -e ".[dev]"

# Install with optional features
pip install -e ".[dev,redis,websearch,storyboard]"

# Install pre-commit hooks (BOTH required)
pre-commit install
pre-commit install --hook-type commit-msg
```

### Testing
```bash
# Fast unit tests (no coverage report)
pytest tests/unit/ -q --no-cov

# All tests with coverage
pytest tests/ -q

# Specific test file
pytest tests/unit/test_graph_loader.py -v

# Run single test
pytest tests/unit/test_graph_loader.py::test_load_graph_config -v

# Integration tests (require API keys)
pytest tests/integration/ -v

# Coverage HTML report
pytest tests/ --cov=yamlgraph --cov-report=html
# Then open htmlcov/index.html
```

### Linting
```bash
# Check code style
ruff check yamlgraph/

# Auto-fix issues
ruff check --fix yamlgraph/

# Format code
ruff format yamlgraph/
```

### Running Examples
```bash
# CLI execution
yamlgraph graph run graphs/showcase.yaml --var topic="AI" --var style=casual

# List available graphs
yamlgraph graph list

# Validate graph schema
yamlgraph graph validate graphs/*.yaml

# Lint graphs for common issues
yamlgraph graph lint graphs/*.yaml

# Show graph info
yamlgraph graph info graphs/router-demo.yaml
```

## Architecture Overview

### Three-Layer Pattern

YAMLGraph uses a strict separation of concerns:

```
┌─────────────────────────────────┐
│  Presentation (Python CLI/API)  │  ← Args, colors, REPL, HTTP routes
├─────────────────────────────────┤
│  Logic (YAML Graphs)            │  ← LLM calls, routing, state, checkpoints
├─────────────────────────────────┤
│  Side Effects (Python Tools)    │  ← External APIs, file I/O, shell commands
└─────────────────────────────────┘
```

**When building new features:**
- Put LLM orchestration in YAML graphs (`graphs/*.yaml`)
- Put reusable prompts in YAML templates (`prompts/*.yaml`)
- Put external integrations in Python tools (`yamlgraph/tools/` or `examples/*/nodes/`)

### Core Compilation Pipeline

```
YAML file → load_graph_config() → GraphConfig (Pydantic)
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
            build_state_class()  parse_tools()   compile_graph()
                    │                 │                 │
                    ▼                 ▼                 ▼
            Dynamic TypedDict   Tool Registry    StateGraph (LangGraph)
                                                       │
                                              graph.compile()
                                                       │
                                                       ▼
                                              CompiledGraph
```

**Key files:**
- `graph_loader.py` (~385 lines): Orchestrates entire compilation
- `node_factory/` modules: Creates node functions by type (llm, router, map, agent, etc.)
- `models/state_builder.py`: Generates dynamic TypedDict from graph YAML
- `executor.py`: Unified `execute_prompt()` interface for all LLM calls
- `mcp_server.py`: MCP server exposing graphs as Copilot tools (CAP-19)

### Node Execution Flow

Every node follows this pattern (implemented in `node_factory/`):

1. **Pre-checks**: `check_requirements()` verifies required state keys exist
2. **Loop protection**: `check_loop_limit()` prevents infinite cycles
3. **Resume support**: `skip_if_exists` check for checkpointing
4. **Execution**: `execute_prompt()` or custom logic
5. **Return**: Dict with state updates (never mutate state directly)

### Dynamic State Management

**No manual state classes needed.** State is auto-generated from YAML:

```yaml
# graphs/example.yaml
nodes:
  generate:
    state_key: generated  # ← Creates state.generated field automatically
  analyze:
    state_key: analysis   # ← Creates state.analysis field automatically
```

State builder (`models/state_builder.py`) scans all `state_key` fields and generates a TypedDict at runtime.

## Critical Rules

### 1. YAML Prompts Only (Never Hardcode)

**All prompts MUST live in `prompts/*.yaml`:**

```python
# ❌ WRONG - Never hardcode prompts
llm.invoke("Write a summary of {topic}")

# ✅ CORRECT - Use YAML prompts
from yamlgraph.executor import execute_prompt
result = execute_prompt("summarize", {"topic": topic})
```

**Template syntax:**
- Simple: `{variable}` for basic substitution
- Advanced: Jinja2 auto-detected when `{{` or `{%` present
  - Loops: `{% for item in items %}...{% endfor %}`
  - Conditionals: `{% if condition %}...{% endif %}`
  - Filters: `{{ text[:50] }}`, `{{ items | join(", ") }}`

### 2. Multi-Provider LLM Factory (Never Import Directly)

```python
# ❌ WRONG - Direct provider import
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic(model="claude-3")

# ✅ CORRECT - Use factory
from yamlgraph.utils.llm_factory import create_llm
llm = create_llm(provider="anthropic")
```

**Provider selection priority:** Function parameter > YAML metadata > `PROVIDER` env var > default (`anthropic`)

### 3. Pydantic for All LLM Outputs

**Option A: Inline schema in YAML prompt (preferred for graph-specific outputs):**
```yaml
# prompts/analyze.yaml
schema:
  name: Analysis
  fields:
    summary: {type: str, description: "Brief summary"}
    key_points: {type: list[str], description: "Main points"}
```

**Option B: Python model in `yamlgraph/models/schemas.py` (for shared schemas):**
```python
from pydantic import BaseModel, Field

class Analysis(BaseModel):
    summary: str = Field(description="Brief summary")
    key_points: list[str] = Field(description="Main points")
```

### 4. State Updates (Never Mutate)

```python
# ❌ WRONG - Direct mutation
def node_fn(state):
    state["key"] = value
    return state

# ✅ CORRECT - Return update dict
def node_fn(state):
    return {"key": value}
```

LangGraph merges the returned dict into state.

### 5. Error Handling Pattern

```python
from yamlgraph.models import PipelineError

try:
    result = execute_prompt(...)
    return {"state_key": result}
except Exception as e:
    error = PipelineError.from_exception(e, node="node_name")
    errors = list(state.get("errors") or [])
    errors.append(error)
    return {"errors": errors}
```

For YAML-defined nodes, error handling is automatic via `on_error: skip|retry|fail|fallback`.

## Extension Points

See [ARCHITECTURE.md](ARCHITECTURE.md#extension-points) for detailed guides on:
- Adding a new node type
- Adding a new LLM provider
- Adding a new tool type

## Code Quality Standards

- **Module size**: Target < 400 lines, max 450 (split into submodules if exceeded)
- **TDD**: Red-Green-Refactor approach mandatory
- **Type hints**: Required on all public functions
- **Python 3.11+**: Use `|` for unions, not `Union[]`
- **Logging**: Use `logging.getLogger(__name__)` (user-facing prints use emojis: 📝 🔍 ✓ ✗ 🚀)
- **Deprecation**: Use `DeprecationError` when marking old APIs during refactoring

## Pull Request Conventions

- **PR titles must follow Conventional Commits**: `type(scope): description` (e.g., `feat(streaming): FR-030 add subgraphs parameter`)
- **Allowed types**: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `ci`, `perf`, `style`, `build`, `revert`
- **`feat` PRs must reference `FR-XXX`** in the title (enforced by CI)
- **Squash merge is the required merge strategy** — the PR title becomes the commit message on the default branch. Repository settings must restrict to squash merge only (Settings → General → Pull Requests)
- CI enforcement via `action-semantic-pull-request@v5` in `.github/workflows/commitlint.yml`
- Local enforcement via `conventional-pre-commit` in `.pre-commit-config.yaml` (commit-msg hook)

## Branch Protection

The `main` branch is protected by GitHub branch protection rules (FR-150). These rules are the **primary enforcement gate** — all other checks (pre-commit hooks, CI workflows) operate within this structure.

### Rules enforced on `main`

| Rule | Setting | Purpose |
|------|---------|---------|
| Require pull request | Enabled (0 approvals) | No direct pushes to `main` |
| Squash merge only | Merge commits and rebase disabled | PR title = commit message; enforces Conventional Commits |
| Required status checks | `commitlint`, `test`, `conflict-check` | PR cannot merge with failing CI |
| Require up to date | Enabled | PRs must be rebased on latest `main` before merge |

### Required status checks

- **`commitlint`** (`.github/workflows/commitlint.yml`): Validates PR title follows Conventional Commits format. `feat` PRs must include `FR-XXX` reference.
- **`test`** (`.github/workflows/workflow.yml`): Runs `pytest` with 80% coverage threshold and `ruff` linting.
- **`conflict-check`** (`.github/workflows/commitlint.yml`): Fails when unresolved merge conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) are found in tracked files (excluding `.github/`). Complements the local `check-merge-conflict` pre-commit hook which is bypassed by server-side squash merges.

### Emergency bypass

Admin overrides are available for legitimate emergencies (broken CI, security hotfix, backup recovery). **Every bypass must be documented** — see [`reference/break-glass.md`](reference/break-glass.md) for the full procedure and audit trail requirements.

## Testing Patterns

See [ARCHITECTURE.md](ARCHITECTURE.md#testing-strategy) for detailed testing patterns including:
- Mock LLM fixtures for unit tests
- Real LLM integration tests with API key guards
- YAML fixture file patterns

## Production Application Pattern

See [examples/npc/architecture.md](examples/npc/architecture.md) for the NPC example demonstrating:
- Session adapters for thread management
- Human-in-loop with `interrupt_before` + `Command(resume=...)`
- Map nodes for parallel processing
- HTMX integration

For standalone demos: `./examples/demos/demo.sh`

## Sync/Async Pattern

The codebase uses **sync-first with async wrappers**:
- Core functions in `executor.py` are synchronous
- Async versions in `executor_async.py` wrap sync functions
- Use `run_graph_async()` for FastAPI integration

## Anti-Patterns to Avoid

| ❌ Wrong | ✅ Correct |
|---------|-----------|
| Hardcoded prompts in Python | YAML templates in `prompts/` |
| Direct provider imports | `create_llm()` factory |
| Untyped dicts | Pydantic models or inline YAML schemas |
| `state["key"] = value` | `return {"key": value}` |
| Silent exceptions | `PipelineError.from_exception()` |
| Files > 400 lines | Refactor into submodules |
| Skip tests | TDD red-green-refactor |

## Security Notes

- **Shell injection protection**: All user variables sanitized with `shlex.quote()` in `tools/shell.py`
- **No eval()**: Condition expressions parsed with regex only
- **Command templates trusted**: Only YAML config is trusted; all runtime variables are escaped

## Key Environment Variables

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Anthropic authentication |
| `GOOGLE_API_KEY` | Google/Gemini authentication |
| `INCEPTION_API_KEY` | Inception Labs Mercury authentication |
| `MISTRAL_API_KEY` | Mistral authentication |
| `OPENAI_API_KEY` | OpenAI authentication |
| `REPLICATE_API_TOKEN` | Replicate authentication |
| `DEEPSEEK_API_KEY` | DeepSeek authentication |
| `XAI_API_KEY` | xAI Grok authentication |
| `LMSTUDIO_BASE_URL` | LM Studio local server URL |
| `PROVIDER` | Default LLM provider (anthropic/deepseek/google/inception/mistral/openai/replicate/xai/lmstudio) |
| `LANGCHAIN_TRACING_V2` | Enable LangSmith observability (true/false) |
| `LANGCHAIN_API_KEY` | LangSmith API key |
| `LANGCHAIN_PROJECT` | LangSmith project name |
