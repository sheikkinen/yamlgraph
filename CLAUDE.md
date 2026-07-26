# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**YAMLGraph** is a YAML-first framework for building LLM pipelines using LangGraph. The key insight: 60-80% of AI workflows can be defined entirely in YAML (graphs + prompts + schemas) without writing Python code. Built on LangGraph with multi-provider LLM support (Anthropic, Mistral, OpenAI).

For fast repository orientation, use the generated static module map at `reference/module-map.md`.

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

### Submitting Proposals
- Write a markdown file to `.chaplain/inbox/` with a descriptive kebab-case filename (e.g., `refactor-state-builder.md`)
- Content: plain text description of the problem or task — freeform, but actionable
- The FSM runtime (`.chaplain/scripts/start-system.sh`) picks it up and runs Plan → Judge → Enforce → Inquisitor audit automatically
- For new features, a one-paragraph problem statement suffices — the Chaplain generates the FR and PR
- Proposals are consumed on pickup (moved out of inbox); rejected FRs are skipped by the enforce pipeline
- **Remote submission:** Open a GitHub Issue with the `chaplain` label. The runtime inbox sync imports labeled issues into the local inbox automatically, removes the label after import, and closes the issue with a commit reference on successful enforcement.

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

### Reproducible Dependency Governance (FR-761)

`constraints/dev-py312.txt` pins the exact resolved environment CI tests
against — matching the `test`/`core-test` jobs' install command
(`.[dev,digest,websearch,a2a,fsm,verify]`) exactly, so a failure can be
reproduced locally instead of depending on ambient resolver state:

```bash
# Regenerate the constraints artifact (Python 3.12, matching CI)
python3.12 -m venv .venv312 && source .venv312/bin/activate
pip install --upgrade pip
pip install -e ".[dev,digest,websearch,a2a,fsm,verify]"
python -m pip freeze --exclude-editable > constraints/dev-py312.txt

# Reproduce a clean environment from the committed artifact
python3.12 -m venv .venv312 && source .venv312/bin/activate
pip install --upgrade pip
pip install -c constraints/dev-py312.txt -e ".[dev,digest,websearch,a2a,fsm,verify]"

# Run the same dependency CVE scan the CI `security` gate runs
pip-audit --desc --skip-editable --ignore-vuln CVE-2026-3219
```

`pip-audit` is declared in the `dev` extra (FR-761) so this command matches
`.github/workflows/security.yml` byte-for-byte without installing anything
undeclared. The constraints file targets the tested editable dev/security
environment only — it does not pin runtime-only installs.

### Direct-Import Dependency Scan (FR-761)

```bash
# Strict mode: fails on any undeclared core direct import
python scripts/direct_import_scan.py --strict

# Report-only: also lists examples/scripts/tests findings without failing
python scripts/direct_import_scan.py
```

### Testing
```bash
# Ultra-fast parallel tests (skip slow, ~20s on 12 cores)
pytest tests/unit/ -q --no-cov -m "not slow" -n auto

# Ultra-fast tests sequential (skip slow, ~42s)
pytest tests/unit/ -q --no-cov -m "not slow"

# Fast unit tests (no coverage report)
pytest tests/unit/ -q --no-cov

# Core-only unit tests (exclude process-coupled modules)
pytest tests/unit/ -m "not process" -q --no-cov

# Run only slow tests
pytest tests/unit/ -q --no-cov -m "slow"

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
- **Import boundaries**: Three-layer architecture enforced by `import-linter` (`.importlinter` config). Run `lint-imports` to check. Layer 3 (tools, models, utils) must not import Layer 2 (graph_loader, executor) or Layer 1 (cli).

## Pull Request Conventions

- **PR titles must follow Conventional Commits**: `type(scope): description` (e.g., `feat(streaming): FR-030 add subgraphs parameter`)
- **Allowed types**: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `ci`, `perf`, `style`, `build`, `revert`
- **`feat` PRs must reference `FR-XXX`** in the title (enforced by CI)
- **Squash merge is the required merge strategy** — the PR title becomes the commit message on the default branch. Repository settings must restrict to squash merge only (Settings → General → Pull Requests)
- CI enforcement via `action-semantic-pull-request@v5` in `.github/workflows/commitlint.yml`
- Local enforcement via `conventional-pre-commit` in `.pre-commit-config.yaml` (commit-msg hook)

## Changelog Fragments (FR-179)

`CHANGELOG.md` is **not tracked in git** — it is generated from fragment files on demand. This eliminates merge conflicts entirely.

### Writing a changelog entry

Create a fragment file in `changelog/unreleased/` with YAML front matter:

```markdown
---
type: feat
scope: graph
req: REQ-YG-162
---
- **FR-179 Append-Only Changelog**: Description of the change. (REQ-YG-162)
```

- `type`: `feat` → Added, `fix` → Fixed, `removal` → Removed
- `scope`: short scope identifier (e.g., `graph`, `cli`, `streaming`)
- `req`: optional requirement ID (omit if none)

### Generating CHANGELOG.md locally

```bash
python scripts/aggregate_changelog.py > CHANGELOG.md
```

### Release workflow

```bash
VERSION="0.4.62"
mkdir -p "changelog/${VERSION}"
mv changelog/unreleased/*.md "changelog/${VERSION}/"
python scripts/aggregate_changelog.py > CHANGELOG.md
git add changelog/
git commit -m "chore(release): ${VERSION} changelog freeze"
```

For the full bump → commit → push → tag flow including pre-commit hook cascade handling, see [`reference/release-checklist.md`](reference/release-checklist.md).

## Branch Protection

The `main` branch is protected by GitHub branch protection rules (FR-150). These rules are the **primary enforcement gate** — all other checks (pre-commit hooks, CI workflows) operate within this structure.

### Rules enforced on `main`

| Rule | Setting | Purpose |
|------|---------|---------|
| Require pull request | Enabled (0 approvals) | No direct pushes to `main` |
| Squash merge only | Merge commits and rebase disabled | PR title = commit message; enforces Conventional Commits |
| Required status checks | `commitlint`, `test`, `conflict-check`, `copilot-trailer-gate`, `wip-gate`, `changelog-gate`, `changelog-req-gate`, `demo-gate`, `diary-gate`, `security` | PR cannot merge with failing CI |
| Require up to date | Enabled | PRs must be rebased on latest `main` before merge |

### Required status checks

- **`commitlint`** (`.github/workflows/commitlint.yml`): Validates PR title follows Conventional Commits format. `feat` PRs must include `FR-XXX` reference.
- **`test`** (`.github/workflows/workflow.yml`): Runs `pytest` with 85% coverage threshold (measured 90.36% on 2026-07-12; gate raised from 70 by FR-714) and `ruff` linting.
- **`conflict-check`** (`.github/workflows/commitlint.yml`): Fails when unresolved merge conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) are found in tracked files (excluding `.github/`). Complements the local `check-merge-conflict` pre-commit hook which is bypassed by server-side squash merges.
- **`copilot-trailer-gate`** (`.github/workflows/commitlint.yml`): Blocks PRs when any `Co-authored-by:` trailer identities appear in PR commit messages or PR body text.
- **`wip-gate`** (`.github/workflows/commitlint.yml`): Blocks PRs when any commit subject in `BASE_SHA..HEAD_SHA` contains standalone `wip` (case-insensitive).
- **`changelog-gate`** (`.github/workflows/commitlint.yml`): Blocks `feat`/`fix` PRs unless a changelog fragment exists in `changelog/unreleased/` (FR-179).
- **`changelog-req-gate`** (`.github/workflows/commitlint.yml`): Validates changelog fragment `req:` front-matter references valid REQ-YG-XXX IDs in the capabilities registry. Mechanical pre-filter for single-REQ CAPs; multi-REQ CAPs deferred (FR-247).
- **`diary-gate`** (`.github/workflows/commitlint.yml`): Blocks `feat`/`fix` PRs with `FR-XXX` reference unless a diary reflection file exists in the diff.
- **`demo-gate`** (`.github/workflows/commitlint.yml`): Blocks `feat`/`fix` PRs that modify files under `examples/demos/<name>/` unless a `demo-output.log` is included in the diff, proving the demo was executed (FR-206).
- **`security`** (`.github/workflows/security.yml`): Validates installed dependencies have no known vulnerabilities (CVEs) via `pip-audit`.

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
| `GOOGLE_CLOUD_PROJECT` | GCP project for Vertex AI (`provider: vertex`) |
| `GOOGLE_CLOUD_LOCATION` | Vertex AI region (default: `us-central1`) |
| `VERTEX_MODEL` | Default model for Vertex AI provider (default: `gemini-2.0-flash`) |
| `VERTEX_API_KEY` | Vertex AI Express mode API key; when set, skips project/location (ADC) and authenticates via key only |
| `INCEPTION_API_KEY` | Inception Labs Mercury authentication |
| `MISTRAL_API_KEY` | Mistral authentication |
| `OPENAI_API_KEY` | OpenAI authentication |
| `REPLICATE_API_TOKEN` | Replicate authentication |
| `DEEPSEEK_API_KEY` | DeepSeek authentication |
| `XAI_API_KEY` | xAI Grok authentication |
| `LMSTUDIO_BASE_URL` | LM Studio local server URL |
| `AZURE_AI_ENDPOINT` | Azure AI Foundry endpoint URL |
| `AZURE_AI_API_KEY` | Azure AI API key |
| `AZURE_MODEL` | Default Azure model/deployment name (default: `gpt-4o`) |
| `YAMLGRAPH_OTEL_DIR` | Optional directory for per-node copilot OTel files (`<dir>/<node_name>.otel.jsonl`); when set, `_execute_cli` exports `COPILOT_OTEL_FILE_EXPORTER_PATH` per node |
| `YAMLGRAPH_OTEL_EXPORT` | OpenTelemetry span export (FR-759): `otlp` enables graph-run/node-execution spans (requires `pip install "yamlgraph[otel]"`; fails fast if extra missing). Unset = true no-op. See `reference/otel-observability.md` |
| `YAMLGRAPH_ROUTE_LOG` | Route decision log opt-in (FR-723): `1` emits one JSON line per routing decision on the public `yamlgraph.route` logger; a file path also appends raw JSONL for `graph export --overlay` |
| `PROVIDER` | Default LLM provider (anthropic/azure/deepseek/google/inception/mistral/openai/replicate/xai/lmstudio) |
| `LANGCHAIN_TRACING_V2` | Enable LangSmith observability (true/false) |
| `LANGCHAIN_API_KEY` | LangSmith API key |
| `LANGCHAIN_PROJECT` | LangSmith project name |
