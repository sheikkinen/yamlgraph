# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.3] - 2026-01-18

### Added
- Implementation Agent (`graphs/impl-agent.yaml`) for code analysis
  - Analyzes codebases and generates implementation plans
  - 9 tools: AST analysis, text search, jedi semantic analysis
  - Detects existing implementations before suggesting changes
- Code analysis tools subpackage (`yamlgraph.tools.analysis`)
  - `get_module_structure` - AST-based structure extraction
  - `read_lines`, `search_in_file`, `search_codebase` - text search
  - `find_refs`, `get_callers`, `get_callees` - jedi semantic analysis
  - `list_package_modules` - package module discovery
- `analysis` optional dependency group (`pip install yamlgraph[analysis]`)
- Reference documentation for impl-agent (`reference/impl-agent.md`)

### Changed
- Refactored analysis tools into `yamlgraph/tools/analysis/` subfolder
- Agent nodes now support `max_iterations` config (default 10)

## [0.1.2] - 2026-01-18

### Added
- Graph linter (`yamlgraph graph lint`) for static analysis of YAML graphs
  - Checks: missing state declarations, undefined tools, missing prompts, unreachable nodes, invalid node types
  - Error codes: E001-E005 (errors), W001-W003 (warnings)
- Feature Brainstormer meta-graph (`graphs/feature-brainstorm.yaml`)
  - Analyzes YAMLGraph codebase and proposes new features
  - Uses web search for competitive analysis
  - Outputs prioritized roadmap
- Web search tool (`type: websearch`) with DuckDuckGo integration
- `websearch` optional dependency group (`pip install yamlgraph[websearch]`)
- Sample `web-research.yaml` graph demonstrating web search agent

## [0.1.1] - 2026-01-17

### Added
- `demo.sh` script to run all demos with single command
- Pydantic schema validation for graph configuration (`GraphConfigSchema`, `NodeConfig`, `EdgeConfig`)
- Compile-time validation of condition expressions in edges
- `sorted_add` reducer for guaranteed ordering in map node fan-in
- Consolidated expression resolution in `expressions.py` module
- Comprehensive unit tests for conditions, routing, and expressions
- Security section in README documenting shell injection protection

### Changed
- State is now dynamically generated from YAML config (no manual `state.py` needed)
- Map node results are automatically sorted by `_map_index` during collection
- Config paths (`prompts/`, `graphs/`, `outputs/`, `.env`) now resolve from current working directory instead of package install location

### Removed
- `output_key` node config field - use `state_key` instead
- `should_continue()` routing function - use expression-based conditions
- Legacy `continue`/`end` condition keywords - use expression conditions like `field > value`
- Legacy `mermaid` CLI command - use `graph info` for graph visualization
- `get_graph_mermaid()`, `print_graph_mermaid()`, `export_graph_png()` functions
- `PROJECT_ROOT` config constant - use `WORKING_DIR` instead

### Fixed
- Map node ordering now guaranteed regardless of parallel execution timing
- README architecture documentation updated to reflect dynamic state generation
- `.env` file now correctly loaded from current directory when installed via `pip install yamlgraph`

## [0.1.0] - 2026-01-17

### Added
- YAML-based graph definition with `graphs/*.yaml`
- YAML prompt templates with Jinja2 support
- Multi-provider LLM support (Anthropic, Mistral, OpenAI)
- Node types: `llm`, `router`, `agent`, `tool`, `python`, `map`
- Expression-based conditional routing
- Loop limits with automatic termination
- Map nodes for parallel fan-out/fan-in processing
- Agent nodes with tool calling
- Shell tool execution with `shlex.quote()` sanitization
- SQLite state persistence and checkpointing
- LangSmith integration for observability
- CLI commands: `graph run`, `graph list`, `graph info`, `graph validate`
- Resume support for interrupted pipelines
- JSON export of pipeline runs
- Animated storyboard demo with image generation

### Security
- Shell command variables sanitized with `shlex.quote()`
- Prompt input sanitization for dangerous patterns
- No use of `eval()` for expression evaluation
