# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**YAMLGraph** is a YAML-first framework for building LLM pipelines using LangGraph. The key insight: 60-80% of AI workflows can be defined entirely in YAML (graphs + prompts + schemas) without writing Python code. Built on LangGraph with multi-provider LLM support (Anthropic, Mistral, OpenAI).

For fast repository orientation, use the generated static module map at `reference/module-map.md`.

Doctrine (Scripture, Knowledge Graph, proposal submission, development
process) lives solely in `.github/copilot-instructions.md`, imported here so
Claude Code loads it together with this file:

@.github/copilot-instructions.md

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

Dependency governance (FR-761 constraints artifact, pip-audit, direct-import
scan): see [reference/development-operations.md → Dependency Governance](reference/development-operations.md#dependency-governance-fr-761).

### Testing
```bash
# Ultra-fast parallel tests (skip slow, ~20s on 12 cores)
pytest tests/unit/ -q --no-cov -m "not slow" -n auto

# Run only slow tests
pytest tests/unit/ -q --no-cov -m "slow"

# All tests with coverage
pytest tests/ -q

# Run single test
pytest tests/unit/test_graph_loader.py::test_load_graph_config -v

# Integration tests (require API keys)
pytest tests/integration/ -v
```

### Linting
```bash
ruff check yamlgraph/          # check
ruff check --fix yamlgraph/    # auto-fix
ruff format yamlgraph/         # format
```

### Running Examples
```bash
yamlgraph graph run graphs/showcase.yaml --var topic="AI" --var style=casual
yamlgraph graph list | validate | lint | info
```

## Architecture

Three-layer separation: Presentation (Python CLI/API) / Logic (YAML graphs) / Side Effects (Python tools). LLM orchestration goes in `graphs/*.yaml`, prompts in `prompts/*.yaml`, integrations in `yamlgraph/tools/`. State is auto-generated from `state_key` fields — no manual state classes. Compilation pipeline, node execution flow, and extension points: [ARCHITECTURE.md](ARCHITECTURE.md).

## Critical Rules

1. **YAML prompts only** — never hardcode prompts in Python; use `execute_prompt("name", vars)`. Jinja2 auto-detected when `{{` or `{%` present.
2. **Multi-provider factory** — never import providers directly; use `create_llm(provider=...)` from `yamlgraph.utils.llm_factory`.
3. **Pydantic for all LLM outputs** — inline `schema:` in the prompt YAML (preferred) or shared model in `yamlgraph/models/schemas.py`.
4. **Never mutate state** — node functions return update dicts; LangGraph merges.
5. **Error handling** — `PipelineError.from_exception(e, node=...)`; YAML nodes get `on_error: skip|retry|fail|fallback`.

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

## Code Quality Standards

- **Module size**: target < 400 lines, max 450 — split into submodules
- **TDD**: Red-Green-Refactor mandatory; type hints on all public functions
- **Python 3.11+**: `|` unions; `logging.getLogger(__name__)`; `DeprecationError` for retiring APIs
- **Import boundaries**: three-layer architecture enforced by `import-linter` (`.importlinter`); run `lint-imports`

## Pull Request Conventions

- **PR titles must follow Conventional Commits**: `type(scope): description`; `feat` PRs must reference `FR-XXX` (CI-enforced)
- **Squash merge is the required merge strategy** — the PR title becomes the commit message on the default branch
- Branch protection rules, required status checks, and the full CI-check list: [reference/development-operations.md → Branch Protection](reference/development-operations.md#branch-protection) and [→ CI Checks](reference/development-operations.md#ci-checks)

## Changelog Fragments (FR-179)

`CHANGELOG.md` is **not tracked in git** — generated from fragments. Create a fragment in `changelog/unreleased/` with YAML front matter (`type: feat|fix|removal`, `scope`, optional `req`), body: `- **FR-XXX Title**: Description. (REQ-YG-XXX)`. Generate locally: `python scripts/aggregate_changelog.py > CHANGELOG.md`. Release flow: [reference/release-checklist.md](reference/release-checklist.md).

## Further Reference

- Testing patterns (mock LLM fixtures, integration guards): [ARCHITECTURE.md](ARCHITECTURE.md#testing-strategy)
- Production application pattern (sessions, human-in-loop, map nodes): [examples/npc/architecture.md](examples/npc/architecture.md); demos: `./examples/demos/demo.sh`
- Sync-first core with async wrappers (`executor.py` / `executor_async.py`); use `run_graph_async()` for FastAPI
- Security: user variables sanitized with `shlex.quote()` in `tools/shell.py`; no `eval()`; only YAML config is trusted
- Provider API keys and env-var defaults: [reference/development-operations.md → Key Environment Variables](reference/development-operations.md#key-environment-variables)
