# YAMLGraph Architecture

> Single source of truth for YAMLGraph architecture, capabilities, and requirements traceability.

## Design Philosophy

### Why YAML-First?

1. **Separation of concerns**: Pipeline logic in YAML, business logic in prompts
2. **No Python required**: Non-developers can create/modify pipelines
3. **Version control friendly**: Diff-able, reviewable configuration
4. **Runtime safety**: Schema validation catches errors before execution

### Why Dynamic State?

Traditional approach requires manual state class definitions:
```python
class MyState(TypedDict):
    topic: str
    generated: str  # Must manually add for each node
```

YAMLGraph generates state automatically from graph config:
```yaml
nodes:
  generate:
    state_key: generated  # ← Auto-added to state
```

**Tradeoffs:**
- ✅ Less boilerplate, faster iteration
- ✅ State always matches graph definition
- ❌ No static type checking in IDE
- ❌ Runtime errors instead of compile-time

### Application Layer Pattern

When building applications with YAMLGraph, use a three-layer architecture:

```
┌─────────────────────────────────────┐
│  Python CLI (demo.py, run_*.py)     │ ← Presentation: colors, REPL, args
├─────────────────────────────────────┤
│  YAML Graphs (*.yaml)               │ ← Logic: LLM, state, checkpoints
├─────────────────────────────────────┤
│  Python Tools (nodes/*.py)          │ ← Side effects: API calls, files
└─────────────────────────────────────┘
```

**Presentation Layer** (Python CLI):
- Argument parsing, terminal colors, interactive prompts
- Thin wrapper around graph execution
- Calls `app.invoke()` and formats output

**Logic Layer** (YAML Graphs):
- All LLM calls, routing, state transitions
- Interrupt nodes for human-in-the-loop
- Map nodes for parallel processing
- Checkpointing and resume capability

**Side Effects Layer** (Python Tools):
- External API calls (Replicate, databases)
- File I/O (image generation, exports)
- Functions that can't be expressed in YAML

**Why this pattern?**
- Graphs are testable, traceable, and resumable
- Python handles UX where YAML can't (colors, stdin)
- Tools isolate non-deterministic operations
- Each layer can evolve independently

### Building APIs on YAMLGraph

The same pattern extends to web APIs:

```
┌─────────────────────────────────────┐
│  FastAPI / Flask                    │ ← HTTP: routes, auth, validation
├─────────────────────────────────────┤
│  YAML Graphs                        │ ← Logic: stateless or with threads
├─────────────────────────────────────┤
│  Python Tools + Storage             │ ← Persistence: DB, S3, queues
└─────────────────────────────────────┘
```

**Key integration points:**

```python
from yamlgraph.graph_loader import compile_graph, load_graph_config

# One-shot execution (stateless)
@app.post("/generate")
def generate(request: GenerateRequest):
    config = load_graph_config("graphs/generate.yaml")
    graph = compile_graph(config).compile()
    result = graph.invoke({"topic": request.topic})
    return {"result": result}

# Multi-turn with threads (stateful)
@app.post("/chat/{thread_id}")
def chat(thread_id: str, message: ChatMessage):
    config = load_graph_config("graphs/chat.yaml")
    checkpointer = get_checkpointer_for_graph(config)
    graph = compile_graph(config).compile(checkpointer=checkpointer)

    run_config = {"configurable": {"thread_id": thread_id}}
    result = graph.invoke(Command(resume=message.content), run_config)
    return {"response": result}
```

See [docs/plan-api-yamlgraph.md](docs/plan-api-yamlgraph.md) for detailed API design patterns.

### Production Example: NPC Encounter

The **examples/npc** directory demonstrates a full production pattern:

```
┌─────────────────────────────────────────────────────────────────┐
│  HTMX Frontend                                                  │
│  • HTML fragments, SSE streaming, minimal JS                    │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI + Session Adapter                                      │
│  • EncounterSession wraps graph with thread_id management       │
│  • Human-in-loop via Command(resume=player_choice)              │
├─────────────────────────────────────────────────────────────────┤
│  YAMLGraph (encounter-multi.yaml)                               │
│  • Map nodes for parallel NPC generation                        │
│  • interrupt_before for player choice points                    │
├─────────────────────────────────────────────────────────────────┤
│  Prompts + Tools                                                │
│  • YAML prompts with Pydantic schemas                           │
│  • Tool functions for game mechanics                            │
└─────────────────────────────────────────────────────────────────┘
```

Key patterns demonstrated:
- **Session Adapter**: `EncounterSession` provides clean API over raw graph
- **Human-in-Loop**: `interrupt_before` + `Command(resume=...)` for player agency
- **Map Nodes**: Parallel fan-out with `Send()` for multi-NPC processing
- **HTMX Integration**: Server-rendered HTML fragments, no client framework

See [examples/npc/architecture.md](examples/npc/architecture.md) for full documentation.

### projects/ vs examples/

| Aspect | `examples/` | `projects/` |
|--------|-------------|-------------|
| **Purpose** | Demonstrate YAMLGraph patterns and capabilities | Standalone applications with domain-specific goals |
| **Requirements** | Framework-scoped (REQ-YG-XXX) | Project-scoped (OC-XXX, IC-XXX, etc.) |
| **Traceability** | Tracked by `scripts/req_coverage.py` | Own traceability, excluded from framework coverage |
| **Tests** | Optional for demos, required for complex examples | Required |
| **Scope** | Illustrate framework features | May diverge from framework patterns for domain reasons |

**Graduation criteria** — An example becomes a project when:
1. It accumulates domain-specific requirements worth tracking independently
2. It needs dedicated test coverage beyond framework validation
3. Its requirements would pollute the framework requirement namespace (see §27 Telco relocation)

---

## Module Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Entry Points                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                      │
│  │ cli/        │  │ builder.py  │  │ Python API  │                      │
│  │ (commands)  │  │ (high-level)│  │ (direct)    │                      │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                      │
└─────────┼────────────────┼────────────────┼─────────────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         graph_loader.py                                  │
│  • load_graph_config() - Parse YAML → GraphConfig                       │
│  • compile_graph() - GraphConfig → StateGraph                           │
│  • _compile_edges() - Build edge connections                            │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ node_compiler.py│  │ map_compiler.py │  │ tools/agent.py  │
│ • compile_node()│  │ • Fan-out nodes │  │ • ReAct agents  │
│ • compile_nodes │  │ • Send() API    │  │ • Tool binding  │
│                 │  │ • Collection    │  │ • Max iterations│
└────────┬────────┘  └─────────────────┘  └─────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    node_factory/ (subpackage)                │
│  • llm_nodes.py - LLM and router nodes                      │
│  • control_nodes.py - Interrupt, passthrough                │
│  • subgraph_nodes.py - Nested graph composition             │
│  • tool_nodes.py - Tool call nodes                          │
│  • streaming.py - Token streaming support                   │
│  • base.py - Shared utilities                               │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          executor.py                                     │
│  • execute_prompt() - Load YAML prompt, call LLM, parse output          │
│  • format_prompt() - Variable substitution (simple or Jinja2)           │
│  • Schema resolution from YAML or Pydantic                              │
├──────────────────────────────────────────────────────────────────────────┤
│                        executor_async.py                                 │
│  • execute_prompt_async() - Async LLM calls                             │
│  • execute_prompt_streaming() - Token-by-token streaming                │
│  • run_graph_streaming_native() - Graph-level streaming (FR-029)        │
│  • load_and_compile_async() - Async graph compilation                   │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ llm_factory.py  │  │ schema_loader.py│  │ utils/prompts.py│
│ • Multi-provider│  │ • YAML → Pydantic│ │ • load_prompt() │
│ • 10 providers: │  │ • JSON Schema   │  │ • resolve_path()│
│   Anthropic,    │  └─────────────────┘  └─────────────────┘
│   DeepSeek,     │
│   Google/Gemini,│
│   Inception,    │
│   Mistral,      │
│   OpenAI,       │
│   Replicate,    │
│   Vertex AI,    │
│   xAI, LMStudio │
│ • Caching       │
└─────────────────┘
```

### Sync/Async Design Pattern

The codebase uses a **sync-first with async wrappers** pattern:

| Sync Module | Async Module | Relationship |
|-------------|--------------|--------------|
| `executor.py` | `executor_async.py` | Both use `executor_base.py` for shared logic |
| `llm_factory.py` | `llm_factory_async.py` | Async wraps sync via `run_in_executor` |

**Why this pattern?**
- **No duplication**: Async modules import from sync, adding only async-specific logic
- **Clean sync API**: Users not needing async get a simple, direct API
- **Async-specific features**: Streaming (`async for`), concurrent execution (`asyncio.gather`)
- **LangChain reality**: Underlying LLM clients are sync; async wrapping is appropriate

This is the idiomatic Python approach. An "async-first with `asyncio.run()` sync wrappers"
would add complexity and introduce event loop issues for sync users.

---

## End-to-End Flow

1. CLI loads YAML and validates structure.
2. Graph config is parsed and validated, with optional data file loading.
3. Dynamic state is generated from config.
4. Nodes are compiled into a LangGraph `StateGraph`.
5. Edges and routing are wired, including map and conditional edges.
6. The graph executes with prompt execution, tools, and error handling.
7. Optional persistence and export capture results and state.

Key flow anchors in code:
- Config load and loop defaults: [graph_loader.py](yamlgraph/graph_loader.py#L31) → [graph_loader.py](yamlgraph/graph_loader.py#L96) → [graph_loader.py](yamlgraph/graph_loader.py#L170)
- Compile and wire graph: [graph_loader.py](yamlgraph/graph_loader.py#L339)
- State generation: [state_builder.py](yamlgraph/models/state_builder.py#L127)
- Node compilation: [node_compiler.py](yamlgraph/node_compiler.py#L32) → [node_compiler.py](yamlgraph/node_compiler.py#L148)
- Prompt execution: [executor.py](yamlgraph/executor.py#L32) → [executor_base.py](yamlgraph/executor_base.py#L84)

---

## Capabilities & Requirements Traceability

YAMLGraph capabilities are tracked in individual YAML files under `capabilities/`.
Run `python scripts/aggregate_capabilities.py` to regenerate the sections below.

<!-- BEGIN GENERATED CAPABILITIES -->

### Capability Summary

| # | Capability | Primary Modules | Requirements |
|---|-----------|----------------|--------------|
| 1 | Config Loading & Validation | `cli/helpers`, `cli/helpers.GraphLoadError`, `data_loader`, `data_loader.DataFileError`, … | REQ-YG-001 – 004 |
| 2 | Graph Compilation | `graph_loader`, `graph_loader.apply_loop_node_defaults`, `graph_loader.compile_graph`, `graph_loader.detect_loop_nodes`, … | REQ-YG-005 – 008 |
| 3 | Node Execution | `executor`, `executor_async`, `executor_base`, `node_factory/llm_nodes`, … | REQ-YG-009 – 011, 050 |
| 4 | Prompt Execution | `executor.PromptExecutor`, `executor.execute_prompt`, `executor_async`, `executor_base.format_prompt`, … | REQ-YG-012 – 016 |
| 5 | Tool & Agent Integration | `node_factory/tool_nodes`, `tools/agent`, `tools/nodes`, `tools/python_tool`, … | REQ-YG-017 – 020 |
| 6 | Routing & Flow Control | `node_factory/control_nodes`, `routing`, `utils/conditions`, `edge_compiler` | REQ-YG-021 – 023, 214 |
| 7 | State Persistence | `models/state_builder`, `storage/checkpointer`, `storage/checkpointer_factory`, `storage/simple_redis` | REQ-YG-024 – 026 |
| 8 | Error Handling | `error_handlers`, `error_handlers.NodeResult`, `error_handlers.build_skip_error_state`, `error_handlers.check_loop_limit`, … | REQ-YG-027 – 031 |
| 9 | CLI Interface | `cli/__init__`, `cli/__main__`, `cli/deprecation`, `cli/graph_commands`, … | REQ-YG-032 – 035 |
| 10 | Export & Serialization | `cli/graph_commands.cmd_graph_codegen`, `cli/schema_commands`, `storage/export`, `storage/serializers` | REQ-YG-036 – 039 |
| 11 | Subgraph & Map | `map_compiler`, `map_compiler.wrap_for_reducer`, `node_factory/subgraph_nodes` | REQ-YG-040 – 042 |
| 12 | Utilities | `config`, `constants`, `node_factory/base`, `schema_loader`, … | REQ-YG-043 – 046 |
| 13 | LangSmith Tracing | `cli/graph_commands`, `utils/tracing` | REQ-YG-047 |
| 14 | Graph-Level Streaming | `executor_async` | REQ-YG-048 – 049, 065 |
| 15 | Expression Language | `utils/conditions`, `utils/expressions`, `utils/parsing` | REQ-YG-051 – 052 |
| 16 | Linter Cross-Reference | `linter/checks`, `linter/checks_contracts`, `linter/checks_semantic`, `linter/graph_linter`, … | REQ-YG-053 – 054, 069, 114 |
| 17 | Execution Safety Guards | `cli/__init__`, `cli/graph_commands`, `config`, `executor`, … | REQ-YG-055 – 062, 064, 113 |
| 18 | Testing & Quality | `tests/conftest`, `tests/unit/test_requirement_enforcement` | REQ-YG-063 |
| 19 | MCP Server Interface | `mcp_server` | REQ-YG-066 – 068 |
| 20 | Contrib Utilities | `contrib/progress`, `contrib/utils` | REQ-YG-070 – 071 |
| 21 | Diary Digest Tools | `scripts/diary_digest_tools` | REQ-YG-072 |
| 22 | Code Quality Lints | `scripts/lint_inline_llm` | REQ-YG-073, 221 |
| 23 | Skip-If-Exists Truthiness | `node_factory/llm_nodes._should_skip_if_exists` | REQ-YG-074 |
| 24 | Interactive Tool Node | `interactive_tool`, `node_factory/control_nodes`, `utils/conditions` | REQ-YG-075 |
| 25 | Tavily Domain RAG Demo | `examples/demos/tavily_rag` | REQ-YG-076 |
| 26 | Streaming Error Resilience | `executor_async`, `models/streaming` | REQ-YG-077 |
| 28 | Graph-Level Thinking Budget | `yamlgraph/models/graph_schema.py`, `yamlgraph/utils/llm_factory.py` | REQ-YG-083 |
| 30 | Copilot Node | `constants.NodeType.COPILOT`, `models/schemas`, `node_compiler`, `node_factory/copilot_node` | REQ-YG-087, 089, 105 |
| 31 | Chaplain Diary Append | `examples/copilot/graph.yaml`, `examples/copilot/prompts/summarize.yaml`, `examples/shared/diary` | REQ-YG-090 |
| 32 | eBook Authoring Pipeline | `examples/ebook/nodes/writing.py`, `tests/unit/test_ebook_doctrine_validation.py` | REQ-YG-091 – 092 |
| 33 | Worktree Pipeline | `examples/enforce/graph.yaml`, `scripts/enforce_worktree.sh`, `utils/worktree_helpers` | REQ-YG-106 |
| 34 | Compiled Graph Cache | `executor_async`, `graph_cache` | REQ-YG-107 |
| 35 | Watch→Enforce Integration | `.chaplain/watch.sh`, `scripts/enforce_worktree.sh` | REQ-YG-116 |
| 36 | Inquisitor Auto-Propose | `.chaplain/inquisitor.sh` | REQ-YG-118 |
| 37 | Architecture Provider Count Guard | `tests/unit/test_architecture_provider_count` | REQ-YG-121 |
| 38 | Post-Merge Finalization | `scripts/finalize_merge.sh`, `tests/unit/test_finalize_merge` | REQ-YG-125 |
| 39 | Inquisitor Commit-Delta Gate | `.chaplain/inquisitor.sh`, `tests/unit/test_inquisitor_gate` | REQ-YG-131 |
| 40 | Enforce Pipeline Graph Delegation | `examples/enforce/graph.yaml`, `scripts/enforce_worktree.sh`, `tests/unit/test_enforce_yamlgraphication` | REQ-YG-128 |
| 41 | Clean GIT Env Test Fixture | `tests/conftest.py`, `tests/unit/test_clean_git_env` | REQ-YG-140 |
| 42 | Inquisitor Worktree Gate | `.chaplain/inquisitor.sh`, `tests/unit/test_inquisitor_worktree_gate` | REQ-YG-142 |
| 43 | Copilot Session GC | `scripts/copilot_session_gc.sh`, `tests/unit/test_copilot_session_gc` | REQ-YG-141 |
| 44 | Judge SPLIT Verdict | `examples/copilot/prompts/judge.yaml`, `scripts/chaplain-prompts/judge.md`, `tests/unit/test_judge_split_verdict` | REQ-YG-143 |
| 45 | Diary Reflection Enforcement | `.pre-commit-config.yaml`, `scripts/finalize_merge.sh`, `tests/unit/test_precommit_hooks` | REQ-YG-144 |
| 46 | Diary Import CLI | `tests/unit/test_diary_commands`, `tests/unit/test_diary_importer`, `yamlgraph/cli/diary_commands.py`, `yamlgraph/diary/importer.py` | REQ-YG-122 |
| 47 | Phantom Requirement Detection | `scripts/req_coverage.py`, `tests/unit/test_req_coverage` | REQ-YG-145 |
| 48 | CHANGELOG Removal Completeness | `CHANGELOG.md`, `tests/unit/test_demo_cleanup_changelog` | REQ-YG-146 |
| 49 | Examples Documentation Audit | `examples/README.md`, `tests/unit/test_examples_readme_audit` | REQ-YG-147 |
| 50 | CI CHANGELOG Gate | `.github/workflows/commitlint.yml`, `tests/unit/test_ci_changelog_gate` | REQ-YG-148 |
| 51 | Branch Protection Documentation | `CLAUDE.md`, `reference/break-glass.md`, `tests/unit/test_branch_protection_docs` | REQ-YG-149 |
| 53 | CI Conflict Marker Gate | `.github/workflows/commitlint.yml`, `tests/unit/test_ci_conflict_check` | REQ-YG-151 |
| 54 | CI Diary Existence Gate | `.github/workflows/commitlint.yml`, `tests/unit/test_ci_diary_gate` | REQ-YG-152 |
| 55 | Chaplain Inbox Documentation | `CLAUDE.md`, `tests/unit/test_claude_md_chaplain_inbox` | REQ-YG-153 |
| 56 | Verification Gate Pattern | `yamlgraph/verification`, `node_factory/llm_nodes`, `linter/checks_contracts` | REQ-YG-154 |
| 57 | Verification Count Range Pydantic | `tests/unit/test_verification`, `yamlgraph/models/__init__`, `yamlgraph/verification` | REQ-YG-155 |
| 59 | Configurable Loop Exit Target | `tests/unit/test_loops`, `yamlgraph/edge_compiler`, `yamlgraph/graph_loader`, `yamlgraph/linter/checks_semantic`, … | REQ-YG-093 |
| 60 | Worktree Venv Corruption Guard | `scripts/enforce_worktree.sh`, `tests/unit/test_worktree_venv_guard`, `yamlgraph/utils/worktree_helpers` | REQ-YG-156 |
| 61 | Bugfix Pipeline with Condemning Test | `.chaplain/watch.sh`, `examples/bugfix`, `scripts/bugfix_worktree.sh`, `tests/unit/test_bugfix_pipeline` | REQ-YG-157 |
| 62 | Sequential Enforcement Mode | `.chaplain/watch.sh`, `tests/unit/test_watch_sequential_enforcement` | REQ-YG-158 |
| 64 | Concurrency Safety Map | `docs/concurrency-safety.md`, `tests/unit/test_concurrency_safety_doc` | REQ-YG-160 |
| 65 | Append-Only Capability Registry | `capabilities/`, `scripts/validate_capabilities.py`, `scripts/req_coverage.py` | REQ-YG-161 |
| 66 | Append-Only Changelog | `changelog/`, `scripts/aggregate_changelog.py`, `scripts/migrate_changelog.py` | REQ-YG-162 |
| 67 | Philosopher Daemon | `examples/philosopher/`, `.chaplain/philosopher.sh` | REQ-YG-184 – 185, 194 |
| 68 | CI Dependency Security Scan | `.github/workflows/security.yml` | REQ-YG-186 |
| 69 | Knowledge Graph Graduation (FR-190) | `.github/copilot-instructions.md` | REQ-YG-187 |
| 70 | Knowledge Graph Graduation (FR-191) | `.github/copilot-instructions.md` | REQ-YG-188 |
| 71 | Release Changelog Sync Gate | `scripts/check_changelog_release_sync.py`, `scripts/release.sh`, `.github/workflows/commitlint.yml`, `.pre-commit-config.yaml`, … | REQ-YG-189 – 191 |
| 72 | Knowledge Graph Mass Graduation (FR-193) | `.github/copilot-instructions.md` | REQ-YG-192 |
| 73 | Philosopher Challenge Node (FR-195) | `examples/philosopher/models.py`, `examples/philosopher/tools.py`, `examples/philosopher/graph.yaml`, `examples/philosopher/prompts/distill.yaml`, … | REQ-YG-193 |
| 74 | FSM Scripture CLAUDE.md (FR-199) | `fsm/CLAUDE.md`, `tests/unit/test_fsm_claude_md_doctrine.py` | REQ-YG-195 |
| 75 | Portable Chaplain (FR-196) | `yamlgraph/tools/python_tool.py`, `.chaplain/graphs/`, `.chaplain/lib/diary.py` | REQ-YG-196 |
| 76 | Horoscope Demo (FR-201) | `examples/demos/horoscope` | REQ-YG-197 |
| 77 | Image Generation Pipeline (FR-202) | `examples/image_pipeline` | REQ-YG-198 |
| 78 | .fi Domain Crawl Demo (FR-205) | `examples/demos/fi-domain-crawl` | REQ-YG-199 |
| 79 | Demo Proof Gate (FR-206) | `scripts/check_demo_proof.sh`, `.github/workflows/commitlint.yml` | REQ-YG-200 |
| 80 | Standalone Scripture Template (FR-207) | `projects/scripture-dev/` | REQ-YG-201 – 205 |
| 81 | A2A Protocol Server (FR-208) | `yamlgraph/a2a_server.py`, `yamlgraph/discovery.py`, `yamlgraph/cli/a2a_commands.py` | REQ-YG-206 – 213 |
| 83 | Research Agent Demo (FR-215) | `examples/demos/research-agent` | REQ-YG-217 |
| 84 | Import-Linter Boundaries (FR-218) | `.importlinter`, `.pre-commit-config.yaml`, `.github/workflows/workflow.yml` | REQ-YG-218 |
| 85 | Dependency Rationale Audit (FR-219) | `scripts/dependency_rationale.py`, `docs/dependency-rationale.yaml` | REQ-YG-219 |
| 86 | Ruff Security Rules (FR-222) | `pyproject.toml`, `docs/confessions.md` | REQ-YG-222 |
| 88 | Google/Vertex Thinking Budget (FR-230) | `yamlgraph/utils/llm_factory.py`, `yamlgraph/models/graph_schema.py`, `yamlgraph/linter/checks_providers.py` | REQ-YG-230 |
| 89 | Execution Timing Callback (FR-231) | `yamlgraph/utils/timing_tracker.py`, `yamlgraph/cli/graph_commands.py`, `yamlgraph/cli/__init__.py` | REQ-YG-231 |
| 90 | Graph Bench Command (FR-231) | `yamlgraph/cli/bench_commands.py`, `yamlgraph/cli/graph_commands.py`, `yamlgraph/cli/__init__.py` | REQ-YG-232 |
| 91 | Race Node Type (FR-232) | `yamlgraph/node_factory/race_node.py`, `yamlgraph/constants.py`, `yamlgraph/node_compiler.py`, `yamlgraph/models/graph_schema.py`, `yamlgraph/linter/patterns/race.py` | REQ-YG-233 |
| 92 | Chatterbox TTS Demo (FR-233) | `examples/demos/chatterbox` | REQ-YG-234 |
| 95 | Parallel Fan-Out Edges (FR-234) | `yamlgraph/edge_compiler.py` | REQ-YG-237 |
| 93 | Chatterbox Voice Clone Demo (FR-236) | `examples/demos/chatterbox_clone` | REQ-YG-235 |
| 94 | Compile-Time Pipeline Templates (FR-235) | `yamlgraph/pipeline_template.py`, `yamlgraph/constants.py`, `yamlgraph/graph_loader.py`, `yamlgraph/linter/patterns/pipeline.py` | REQ-YG-236 |
| 96 | Pipeline Accumulated State (FR-238) | `yamlgraph/models/state_builder.py` | REQ-YG-238 |

> Capability numbers are stable identifiers. Gaps (e.g. 27, 29, 52, 58) indicate retired capabilities.

### 1. Config Loading & Validation

Load YAML graph configs, validate schemas, build state models, and ensure graph integrity through linting.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-001 | Load graph configurations from YAML files | `graph_loader.load_graph_config`, `cli/helpers`, `data_loader` |
| REQ-YG-002 | Validate graph configuration schemas and structures | `models/graph_schema`, `utils/validators` |
| REQ-YG-003 | Perform linting and pattern validation | `linter/graph_linter`, `linter/checks`, `linter/patterns/*` |
| REQ-YG-004 | Handle errors during configuration loading | `cli/helpers.GraphLoadError`, `data_loader.DataFileError` |

### 2. Graph Compilation

Transform validated configs into executable StateGraphs with node compilation, edge wiring, and loop detection.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-005 | Load YAML graph definitions into StateGraphs | `graph_loader`, `graph_loader.load_and_compile` |
| REQ-YG-006 | Validate graph structures (cycle detection, loop defaults) | `graph_loader.detect_loop_nodes`, `graph_loader.apply_loop_node_defaults` |
| REQ-YG-007 | Compile individual nodes | `node_compiler.compile_node`, `node_factory` |
| REQ-YG-008 | Compile full graph configuration | `graph_loader.compile_graph`, `node_compiler.compile_nodes` |
| REQ-YG-220 | Node type registry dispatches compile_node via `NODE_TYPE_HANDLERS` dict instead of if/elif; unknown types raise `ValueError` (FR-220) | `node_compiler` |

### 3. Node Execution

Create executable node functions for LLM, streaming, tool, interrupt, and subgraph behavior.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-009 | Node creation and streaming | `node_factory/llm_nodes`, `node_factory/streaming` |
| REQ-YG-010 | Synchronous LLM factory management | `utils/llm_factory` |
| REQ-YG-011 | Asynchronous LLM factory management | `utils/llm_factory_async` |
| REQ-YG-050 | Per-node and default-level `model` override: graph YAML `model` field flows through `execute_prompt()` to `create_llm()` | `node_factory/llm_nodes`, `executor`, `executor_async`, `executor_base` |
| REQ-YG-223 | LLM node factory decomposed into composable phases: `LLMNodeConfig` frozen dataclass, `resolve_llm_node_config()` pure config resolver, `_apply_verification()`, `_resolve_route()`, `_handle_error()` — each independently testable, all below C901=10 (FR-223) | `node_factory/llm_nodes` |
| REQ-YG-230 | `thinking_budget` extended to `google` and `vertex` providers (FR-230): `create_llm` accepts thinking_budget for anthropic/google/vertex; raises for others; `_create_google_llm` and `_create_vertex_llm` forward `thinking_budget` kwarg; temperature not overridden for google/vertex; schema accepts `-1` (Google auto mode), rejects `< -1`; linter W071-1/2/4 scoped to anthropic only; linter W071-3 includes gemini-2.5+/gemini-3+ as thinking-capable | `yamlgraph/utils/llm_factory.py`, `yamlgraph/models/graph_schema.py`, `yamlgraph/linter/checks_providers.py` |

### 4. Prompt Execution

Load prompt YAML, validate variables, format messages, and run LLM calls sync and async.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-012 | Prompt loading and resolution | `utils/prompts` |
| REQ-YG-013 | Variable resolution and template management | `executor_base.format_prompt`, `utils/expressions`, `utils/template` |
| REQ-YG-014 | Synchronous prompt execution | `executor.PromptExecutor`, `executor.execute_prompt` |
| REQ-YG-015 | Asynchronous prompt execution | `executor_async` |
| REQ-YG-016 | JSON extraction from LLM outputs | `utils/json_extract` |

### 5. Tool & Agent Integration

Integrate shell and Python tools into graphs, enable agent loops for tool-calling.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-017 | Dynamic tool node creation | `node_factory/tool_nodes` |
| REQ-YG-018 | Agent-driven tool selection and execution | `tools/agent` |
| REQ-YG-019 | Shell tool integration and execution | `tools/shell`, `tools/nodes` |
| REQ-YG-020 | Python tool integration and execution | `tools/python_tool` |

### 6. Routing & Flow Control

Route across nodes using explicit routes, expression evaluation, and control nodes.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-021 | Control node creation (interrupt, passthrough) | `node_factory/control_nodes` |
| REQ-YG-022 | Conditional routing functions | `routing` |
| REQ-YG-023 | Condition expression evaluation | `utils/conditions` |

### 7. State Persistence

Checkpointers and Redis storage for resuming pipelines and state history.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-024 | Dynamic state class generation | `models/state_builder` |
| REQ-YG-025 | Checkpointer provisioning | `storage/checkpointer_factory` |
| REQ-YG-026 | State persistence operations (Redis) | `storage/simple_redis`, `storage/checkpointer` |
| REQ-YG-196 | Checkpointer string shorthand config | `storage/checkpointer_factory` |

### 8. Error Handling

Error strategies (retry, fallback, skip), sanitization, resilience features.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-027 | Error handling strategies (skip, fail, retry, fallback) | `error_handlers` |
| REQ-YG-028 | Pre-execution validation (requirements, loop limits) | `error_handlers.check_requirements`, `error_handlers.check_loop_limit` |
| REQ-YG-029 | Error state management (NodeResult, skip updates) | `error_handlers.NodeResult`, `error_handlers.build_skip_error_state` |
| REQ-YG-030 | Error schemas and reporting | `models/schemas.PipelineError`, `models/schemas.ErrorType` |
| REQ-YG-031 | Retry capability | `executor_base.is_retryable`, `executor._invoke_with_retry` |

### 9. CLI Interface

Command-line commands for graph validation, execution, info display, schema export.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-032 | CLI entry point and parser setup | `cli/__init__`, `cli/__main__` |
| REQ-YG-033 | Graph command execution and information | `cli/graph_commands` |
| REQ-YG-034 | Deprecation handling for CLI commands | `cli/deprecation` |
| REQ-YG-035 | CLI utilities and schema command dispatch | `cli/helpers`, `cli/schema_commands` |

### 10. Export & Serialization

Export results/states in JSON/Markdown, handle serialization for persistence.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-036 | CLI schema export and access | `cli/schema_commands` |
| REQ-YG-037 | Graph code generation for IDE support | `cli/graph_commands.cmd_graph_codegen` |
| REQ-YG-038 | Export and management of pipeline results/states | `storage/export` |
| REQ-YG-039 | Serialization and deserialization utilities | `storage/serializers` |

### 11. Subgraph & Map

Parallel fan-out and nested subgraph execution.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-040 | Map node compilation | `map_compiler` |
| REQ-YG-041 | Output wrapping for reduction | `map_compiler.wrap_for_reducer` |
| REQ-YG-042 | Subgraph node creation | `node_factory/subgraph_nodes` |

### 12. Utilities

Logging, templating, JSON extraction, environment handling, and shared utilities.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-043 | Configuration and constants management | `config`, `constants` |
| REQ-YG-044 | Schema loading and model building | `schema_loader` |
| REQ-YG-045 | Node factory and resolution | `node_factory/base` |
| REQ-YG-046 | Logging and parsing utilities | `utils/logging`, `utils/parsing` |

### 13. LangSmith Tracing

Observability via LangSmith: trace URL retrieval, public sharing, and tracer injection.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-047 | LangSmith trace URL retrieval and sharing | `utils/tracing`, `cli/graph_commands` |

### 14. Graph-Level Streaming

Stream LLM tokens through the compiled graph pipeline using LangGraph astream(stream_mode="messages"), enabling real-time SSE output.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-048 | Graph-level streaming: run graph with `astream(stream_mode="messages")` yielding LLM tokens | `executor_async` |
| REQ-YG-049 | Streaming with multi-turn: `run_graph_streaming_native()` accepts `Command(resume=...)`, config with thread_id for checkpoint-based resume | `executor_async` |
| REQ-YG-065 | Native LangGraph streaming: `run_graph_streaming_native()` uses `astream(stream_mode="messages")` to stream from ALL LLM nodes, with optional `node_filter` | `executor_async` |

### 15. Expression Language

Value expressions, condition expressions, literal parsing, and resolve_node_variables batch resolution.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-051 | Expression language: value expressions (`{state.path}`, arithmetic, list/dict ops), condition expressions (comparisons, compound AND/OR), literal parsing, `resolve_node_variables` batch resolution | `utils/expressions`, `utils/conditions`, `utils/parsing` |
| REQ-YG-052 | Expression language hardening: quote-aware compound split, right-side state reference resolution, chained arithmetic detection | `utils/conditions`, `utils/expressions` |

### 16. Linter Cross-Reference

Linter cross-reference and semantic checks for edge endpoints, loop limits, state references, and contract warnings.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-053 | Linter cross-reference & semantic checks: edge endpoint validation (E006), loop_limits references (E008), passthrough output (E601), tool_call fields (E701/E702), condition syntax (W801), variable prefix (W007), fallback config (E010), conditional edge type (E802) | `linter/checks`, `linter/graph_linter` |
| REQ-YG-054 | Chaplain audit fixes: `wrap_for_reducer` non-dict return handling, LLM SKIP error recording, linter E011 retry/fallback on tool/python nodes, `prompts_relative` warning | `map_compiler`, `node_factory/llm_nodes`, `linter/checks`, `utils/prompts` |
| REQ-YG-069 | Linter E007: error when `{state.X}` in node `variables`/`output`/`over`/`args`/`input_mapping` references a field not in known state (declared `state:` + node `state_key` + `BUILTIN_STATE_FIELDS` + `COMMON_INPUT_FIELDS` + `data_files` + map `collect`). Promoted from W014 warning to E007 error (FR-110) | `linter/checks_semantic` |
| REQ-YG-114 | Linter W017: warn when node uses `on_error: skip` — silent fallback that drops failures without trace | `linter/checks_contracts`, `linter/graph_linter` |

### 17. Execution Safety Guards

Defense-in-depth guards against infinite loops, unbounded map fan-out, and runaway execution.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-055 | Map fan-out cap: `max_items` per node and `max_map_items` graph-level default, truncate + warn | `map_compiler` |
| REQ-YG-056 | `recursion_limit` exposure via YAML `config:` and CLI `--recursion-limit`, passed to `graph.invoke()` | `graph_loader`, `cli/graph_commands`, `cli/__init__` |
| REQ-YG-057 | `check_loop_limit()` enforced in tool, python, and passthrough nodes (not just LLM) | `tools/nodes`, `tools/python_tool`, `node_factory/control_nodes` |
| REQ-YG-058 | Linter W012: warn when cycle node has no `loop_limits` entry | `linter/checks_semantic`, `linter/graph_linter` |
| REQ-YG-059 | `max_iterations` single source of truth: default 10 everywhere (Pydantic, JSON schema, agent runtime, docs) | `tools/agent`, `models/graph_schema` |
| REQ-YG-060 | `max_tokens` wired from YAML config/node config through `execute_prompt()` to `create_llm()` provider constructor | `config`, `graph_loader`, `llm_factory`, `executor`, `node_factory/llm_nodes` |
| REQ-YG-061 | Global execution timeout via `config.timeout` and CLI `--timeout`, signal.alarm guard on Unix | `graph_loader`, `cli/graph_commands`, `cli/__init__` |
| REQ-YG-062 | Linter W013: warn when map node `over:` is a dynamic expression without `max_items` or `config.max_map_items` | `linter/checks_semantic`, `linter/patterns/map` |
| REQ-YG-064 | Token usage tracking via `TokenUsageCallbackHandler` callback injected at graph-level; accumulates `input_tokens`, `output_tokens`, `total_calls` across all LLM invocations; CLI `--token-usage` flag prints summary | `utils/token_tracker`, `cli/graph_commands`, `cli/__init__` |
| REQ-YG-113 | Linter W015: warn when cycle node has explicit `skip_if_exists: true` | `linter/checks_semantic`, `linter/graph_linter` |
| REQ-YG-231 | Execution timing callback tracks per-call and total wall-clock LLM duration via `ExecutionTimingCallbackHandler`; `on_llm_start`/`on_llm_end` using `time.monotonic`; CLI `--timing` flag injects callback and prints timing summary | `utils/timing_tracker`, `cli/graph_commands`, `cli/__init__` |
| REQ-YG-232 | `yamlgraph graph bench` command runs a graph across `--models provider/model` list; displays comparison table with duration, tokens, status; `--export` saves JSON; `--runs N` repeats each model; per-model errors captured gracefully; `BenchResult` Pydantic model | `cli/bench_commands`, `cli/graph_commands`, `cli/__init__` |
| REQ-YG-233 | `type: race` node fires prompt to all candidates concurrently via `ThreadPoolExecutor`; returns first successful result; remaining cancelled; all-fail triggers `on_error`; `_race_winner` metadata in state; candidates validated ≥2 with provider/model; lint E301–E304; structured output support | `node_factory/race_node`, `constants`, `node_compiler`, `models/graph_schema`, `models/state_builder`, `linter/patterns/race` |
| REQ-YG-234 | Chatterbox TTS demo: map node fans out over 5 languages, collects translations, synthesizes to WAV via `synthesize_audio` python tool with Chatterbox Multilingual TTS. Auto-detects CUDA/CPU. Optional dependency `chatterbox-tts` (FR-233) | `examples/demos/chatterbox` |
| REQ-YG-237 | Parallel fan-out edges: `to: [a, b, c]` without `type: conditional` compiles as parallel fan-out via multiple `add_edge()` calls; handles interrupt node redirect to `_prepare`; handles map node targets via conditional edges; START fan-out uses conditional entry point; existing conditional routing with `type: conditional` unchanged (FR-234) | `edge_compiler` |
| REQ-YG-235 | Chatterbox voice cloning demo: single-path graph accepts text and voice_prompt_path, synthesizes to WAV via `synthesize_cloned_audio` python tool using `ChatterboxTTS` (not `ChatterboxMultilingualTTS`). Device selection follows `cuda > mps > cpu`. Optional dependency `chatterbox-tts` (FR-236) | `examples/demos/chatterbox_clone` |
| REQ-YG-236 | `type: pipeline` meta-node expands at compile time into concrete nodes and sequential edges; `{item.field}` interpolation in prompt, variables, state_key; non-string fields copied verbatim; external edges rewritten to first/last expanded node; lint E401 (empty items), E402 (empty stages), E403 (unresolved item refs), E404 (missing name); `NodeType.PIPELINE` in constants; expansion in `graph_loader` after `expand_interactive_tools` | `pipeline_template`, `constants`, `graph_loader`, `linter/patterns/pipeline`, `linter/checks`, `linter/graph_linter` |
| REQ-YG-238 | `parse_state_config()` handles dict-syntax state definitions `{type: str, reducer: str}`; `REDUCER_MAP` maps `"add"`, `"last_value"`, `"sorted_add"` to their functions; unknown reducer names log a warning; dict syntax without `reducer` key works as type-only; `generate_typeddict_code()` extracts type string from dict-syntax entries via `CODEGEN_TYPE_MAP`; `reference/graph-yaml.md` documents accumulated state pattern with glossary example, sequential execution constraint, and W021 `skip_if_exists: false` requirement (FR-238) | `models/state_builder`, `reference/graph-yaml.md`, `tests/unit/test_state_builder_reducers` |

### 18. Testing & Quality

Requirement traceability enforcement and testing infrastructure.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-063 | Requirement traceability enforcement: `pytest_collection_modifyitems` hook structurally enforces ADR-001 — all tests must have `@pytest.mark.req` | `tests/conftest`, `tests/unit/test_requirement_enforcement` |

### 19. MCP Server Interface

Expose YAMLGraph graphs as MCP (Model Context Protocol) tools for Copilot and other AI assistants.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-066 | MCP server with stdio transport: expose `yamlgraph_list_graphs` and `yamlgraph_run_graph` tools via MCP protocol | `mcp_server` |
| REQ-YG-067 | Graph discovery: scan configured directories for `graph.yaml`, parse headers for name/description/required vars | `mcp_server` |
| REQ-YG-068 | Graph invocation via MCP: compile and invoke any discovered graph with vars, return structured result JSON | `mcp_server` |

### 20. Contrib Utilities

Shared utilities extracted from pipeline patterns. Eliminates copy-paste duplication across projects.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-070 | Contrib utils: `get_map_result()` unwraps single-key `_map_*_sub` dicts; `to_serializable()` converts Pydantic models to dicts recursively | `contrib/utils` |
| REQ-YG-071 | Contrib progress: `SkipReport` reads `state["errors"]` and provides human-readable skip summaries with counts and node names | `contrib/progress` |

### 21. Diary Digest Tools

Scheduled pipeline tools for fetching external developments and appending context-aware diary entries.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-072 | Diary digest: fetch HN/RSS sources, filter by relevance, format diary entries, append to diary.md, no-op when nothing relevant | `scripts/diary_digest_tools` |

### 22. Code Quality Lints

Custom lint checks enforcing architectural patterns beyond standard linters.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-073 | Inline LLM lint: detect scripts with `def main()` that import LLM execution functions without graph loading — flags orchestration code smell | `scripts/lint_inline_llm` |
| REQ-YG-221 | Ruff C901 cognitive complexity gate: `C901` in ruff select with `max-complexity = 15` in `[tool.ruff.lint.mccabe]`; functions above threshold suppressed with `# noqa: C901` and documented in `docs/confessions.md`; CI inherits via existing `ruff check yamlgraph/` (FR-221) | `pyproject.toml`, `docs/confessions.md` |

### 23. Skip-If-Exists Truthiness

skip_if_exists checks truthiness, not existence. Empty collections, empty strings, None, 0, and False do NOT trigger skip.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-074 | skip_if_exists uses truthiness check: `[]`, `""`, `None`, `0`, `False` do not skip; only truthy values skip | `node_factory/llm_nodes._should_skip_if_exists` |

### 24. Interactive Tool Node

Declarative multi-turn stateful tool integration via config-level expansion.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-075 | Interactive tool node: expand `type: interactive_tool` into start/ask/step/end inline nodes with loop condition, max iterations, and interrupt-based user input | `interactive_tool`, `node_factory/control_nodes`, `utils/conditions` |

### 25. Tavily Domain RAG Demo

Domain-scoped RAG using Tavily search API with type:python tool nodes and map fan-out.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-076 | Tavily domain RAG: python tool retrieves context via Tavily API with optional `TAVILY_TARGET_DOMAIN` scoping; simple graph (retrieve→answer) and deep graph (plan→map(retrieve)→synthesize) | `examples/demos/tavily_rag` |

### 26. Streaming Error Resilience

Error propagation, timeout support, and interrupt detection for run_graph_streaming_native(). Yields StreamEvent Pydantic objects for errors and interrupts instead of crashing silently.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-077 | Streaming error resilience: wrap `astream()` with try/except to yield `StreamEvent(type="error")` on exceptions; `asyncio.timeout()` for stall detection; interrupt payload detection via `aget_state()` after stream completes; `yield_events=False` flag for opt-out (raises instead) | `executor_async`, `models/streaming` |

### 28. Graph-Level Thinking Budget

Graph-level and per-node thinking_budget YAML field for Anthropic extended thinking.

**Feature Request:** FR-071

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-083 | `thinking_budget` YAML field on graph `defaults` and per-node; validated as `0` or `≥ 1024`; passed as `thinking={"type":"enabled","budget_tokens":N}` to `ChatAnthropic` with forced `temperature=1` (override before cache key); raises on non-Anthropic provider; included in LLM cache key | `yamlgraph/models/graph_schema.py`, `yamlgraph/utils/llm_factory.py` |

### 30. Copilot Node

New copilot node type that delegates graph processing to Copilot CLI, replacing shell-script orchestration with a first-class YAML-declarable node.

**Feature Request:** FR-082

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-087 | Copilot node executes via CLI backend with configurable flags and timeout; `--silent` always forced; list-based `subprocess.run()` for injection safety; graceful `FileNotFoundError` when copilot binary missing | `node_factory/copilot_node`, `node_compiler`, `constants.NodeType.COPILOT` |
| REQ-YG-089 | Copilot node composes with router, map, and FSM-router patterns; standard node guarantees apply (requires, on_error, skip_if_exists, loop protection) | `node_factory/copilot_node`, `node_compiler` |
| REQ-YG-105 | Copilot node session continuations via `--resume` and `--continue` flags; session ID captured from stderr into `CopilotResult.session_id`; state expression resolution for `cli_flags.resume` | `node_factory/copilot_node`, `models/schemas` |

### 31. Chaplain Diary Append

Extends the Plan-Judge workflow with automatic diary entry creation after each run.

**Feature Request:** FR-090

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-090 | `format_diary_entry()` accepts configurable `prefix` parameter (default "World Digest"); `examples/copilot/graph.yaml` includes `summarize` (LLM) and `write_diary` (Python) nodes; `watch.sh` passes `date` and `diary_prefix` vars | `examples/shared/diary`, `examples/copilot/graph.yaml`, `examples/copilot/prompts/summarize.yaml` |

### 32. eBook Authoring Pipeline

A YAMLGraph pipeline that writes the development pipeline documentation as an eBook.

**Feature Request:** FR-100

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-091 | `write_chapters_tool` writes formatted chapter content to disk; accepts `output_dir` and chapter state variables; creates directory if missing; returns dict with `written` list of paths | `examples/ebook/nodes/writing.py` |
| REQ-YG-092 | Chapter validation detects fabricated doctrine content; `verify_commandments_verbatim()` checks all 10 Commandments appear exactly as in source; returns `{passed, found, missing, fabricated}` dict | `tests/unit/test_ebook_doctrine_validation.py` |

### 33. Worktree Pipeline

Parallel development pipeline via git worktrees, enabling multiple features to be enforced simultaneously without blocking the main working tree.

**Feature Request:** FR-106

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-106 | Worktree helpers derive branch names from FR paths, construct worktree paths under `tmp/worktrees/`, and validate clean working tree before creation; shell script orchestrates worktree lifecycle with trap-based cleanup; 4-phase graph (implement → test/demo → precommit → PR) chains via session continuations | `utils/worktree_helpers`, `scripts/enforce_worktree.sh`, `examples/enforce/graph.yaml` |

### 34. Compiled Graph Cache

Process-global compiled graph cache so load_and_compile_async() results survive module reloads and are shared across all callers within the same Python process.

**Feature Request:** FR-111

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-107 | Process-global `GRAPH_CACHE` dict in installed package; `load_and_compile_async()` uses cache by default with `cache=None` opt-out; `clear_cache()` for test teardown; cache-hit logs at DEBUG, compile logs at INFO | `graph_cache`, `executor_async` |

### 35. Watch→Enforce Integration

Post-graph hook in watch.sh that detects new feature request files via ephemeral find + comm diff, skips rejected FRs, and spawns enforce_worktree.sh in the background.

**Feature Request:** FR-116

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-116 | `watch.sh` snapshots `feature-requests/` before graph execution, diffs after with `comm -13` to detect new FRs, skips rejected FRs (matching `Status.*Rejected`), and spawns `enforce_worktree.sh` via `nohup ... &` with output redirected to `tmp/enforce-<slug>.log`; no state files or Python helpers | `.chaplain/watch.sh`, `scripts/enforce_worktree.sh` |

### 36. Inquisitor Auto-Propose

--propose flag on inquisitor.sh detects violations persisting across consecutive Inquisitor Audit entries and writes targeted fix proposals to .chaplain/inbox/.

**Feature Request:** FR-118

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-118 | `inquisitor.sh --propose` parses flag, gates a second copilot call that reads up to 5 diary audit entries, detects persistent ✗ violations (≥2 consecutive), classifies as micro-fix or structural gap, writes proposal markdown to `.chaplain/inbox/inquisitor-<slug>.md` with filename-based dedup; without `--propose` the audit-only flow is unchanged | `.chaplain/inquisitor.sh` |

### 37. Architecture Provider Count Guard

Cross-check test ensuring the provider count in ARCHITECTURE.md module table matches the actual ProviderType Literal in llm_factory.py.

**Feature Request:** FR-121

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-121 | Test asserts ARCHITECTURE.md module table provider count for `llm_factory.py` equals `len(get_args(ProviderType))`; prevents documentation drift when providers are added or removed | `tests/unit/test_architecture_provider_count` |

### 38. Post-Merge Finalization

Automates three post-merge obligations after a PR from the enforce pipeline is merged: CHANGELOG entry, FR status update, and diary reflection stub.

**Feature Request:** FR-125

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-125 | `scripts/finalize_merge.sh` inserts CHANGELOG entry under `[Unreleased] / ### Added`, updates FR status to `✅ Implemented`, and appends diary reflection stub with Trap/Heuristic/Seed placeholders | `scripts/finalize_merge.sh`, `tests/unit/test_finalize_merge` |

### 39. Inquisitor Commit-Delta Gate

inquisitor.sh commit-delta gate extracts last audit SHA from docs/diary/, counts feat:/fix: commits since that SHA, and aborts when none found.

**Feature Request:** FR-131

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-131 | `inquisitor.sh` commit-delta gate extracts last audit SHA from `docs/diary/`, counts `feat:`/`fix:` commits since that SHA via `git log`, and aborts with clear message when none found; `--force` bypasses gate; gate degrades gracefully on missing diary, unparseable SHA, or first-ever audit; `--propose` respects gate; gate logic is pure shell | `.chaplain/inquisitor.sh`, `tests/unit/test_inquisitor_gate` |

### 40. Enforce Pipeline Graph Delegation

enforce_worktree.sh delegates all LLM orchestration to examples/enforce/graph.yaml instead of inline copilot -p calls, completing the three-layer separation.

**Feature Request:** FR-128

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-128 | `scripts/enforce_worktree.sh` calls `yamlgraph graph run examples/enforce/graph.yaml` with `--var fr_path` and `--var branch`; no inline prompts (`IMPLEMENT_PROMPT`, `TEST_PROMPT`, `FIX_PROMPT`), no `copilot -p` calls, no pre-commit retry loop, no inline git/PR commands remain | `scripts/enforce_worktree.sh`, `examples/enforce/graph.yaml`, `tests/unit/test_enforce_yamlgraphication` |

### 41. Clean GIT Env Test Fixture

Session-scoped autouse pytest fixture strips GIT_* environment variables injected by pre-commit, preventing subprocess bleed into tests that create temporary git repos.

**Feature Request:** FR-140

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-140 | `_clean_git_env` session-scoped autouse fixture strips all `GIT_*` env vars at session start, restores on teardown; no-op when vars absent; prevents pre-commit `GIT_DIR`/`GIT_WORK_TREE` from leaking into subprocess git calls in `tmp_path`-based test repos | `tests/conftest.py`, `tests/unit/test_clean_git_env` |

### 42. Inquisitor Worktree Gate

inquisitor.sh worktree gate detects git worktree context and exits early, suppressing audit and propose phases during enforce pipeline.

**Feature Request:** FR-142

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-142 | `inquisitor.sh` worktree gate checks `-f "$REPO_ROOT/.git"` (file = worktree, directory = main), exits 0 with message when in worktree; `--force` bypasses gate; degrades gracefully when `git rev-parse` fails; gate placed before commit-delta gate (FR-131); pure shell, no Python | `.chaplain/inquisitor.sh`, `tests/unit/test_inquisitor_worktree_gate` |

### 43. Copilot Session GC

Shell script that prunes stale Copilot CLI sessions from ~/.copilot/session-state/ based on age.

**Feature Request:** FR-138

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-141 | `copilot_session_gc.sh` removes session directories older than `--max-age` days (default 7); `--dry-run` lists candidates without deleting; active session (`$COPILOT_SESSION_ID`) is never removed; exits cleanly when directory is missing; idempotent; logs UUID and age for each removed session | `scripts/copilot_session_gc.sh`, `tests/unit/test_copilot_session_gc` |

### 44. Judge SPLIT Verdict

Add a fourth judge verdict (SPLIT) for multi-concern feature requests, enabling decomposition before implementation.

**Feature Request:** FR-136

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-143 | Judge prompts must include `SPLIT` verdict and Scope Count rubric for multi-concern FR decomposition; unit tests verify both prompt sources and conflict fixture behavior | `examples/copilot/prompts/judge.yaml`, `scripts/chaplain-prompts/judge.md`, `tests/unit/test_judge_split_verdict` |

### 45. Diary Reflection Enforcement

Pre-commit hook diary-reflection-check rejects commits when tracked docs/diary/ reflection files contain unfilled placeholder text.

**Feature Request:** FR-144

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-144 | `diary-reflection-check` pre-commit hook scans tracked reflection files for unfilled placeholder text and blocks commit; `finalize_merge.sh` creates stubs as untracked files (no `git add` of `docs/diary/`); hook passes when no placeholders remain | `.pre-commit-config.yaml`, `scripts/finalize_merge.sh`, `tests/unit/test_precommit_hooks` |

### 46. Diary Import CLI

CLI command to import pending diary entries and git report data into docs/diary/ with optional dry-run and source selection.

**Feature Request:** FR-124

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-122 | `yamlgraph diary import` CLI command imports pending diary entries and git reports into `docs/diary/` with `--dry-run` and `--source` flags; shared importer returns structured `ImportResult` list; dry-run does not mutate source files; malformed files reported and exit non-zero; explicit missing `--source` emits warning | `yamlgraph/diary/importer.py`, `yamlgraph/cli/diary_commands.py`, `tests/unit/test_diary_importer`, `tests/unit/test_diary_commands` |

### 47. Phantom Requirement Detection

Detect and reject test markers that reference non-existent requirement IDs.

**Feature Request:** FR-145

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-145 | Phantom requirement detection: `req_coverage.py --strict` rejects `@pytest.mark.req` markers referencing requirement IDs absent from `ALL_REQS` or `ARCHITECTURE.md` | `scripts/req_coverage.py`, `tests/unit/test_req_coverage` |

### 48. CHANGELOG Removal Completeness

CHANGELOG.md [Unreleased] documents significant file removals per Commandment 8.

**Feature Request:** FR-153

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-146 | CHANGELOG.md `[Unreleased]` contains a `### Removed` section documenting stale demo file deletions (commit a0e6f00): `examples/cost-router/poc_granite.py`, `scripts/loopback-poc/` (419 lines); section ordering follows Keep a Changelog convention (Added → Removed → Fixed) | `CHANGELOG.md`, `tests/unit/test_demo_cleanup_changelog` |

### 49. Examples Documentation Audit

Every on-disk example and demo is accurately indexed in examples/README.md with categorized sections and enforced quality bar.

**Feature Request:** FR-135

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-147 | `examples/README.md` lists every demo directory and top-level example on disk; demos are split into Learning / Utility / FR Validation sections; inclusion criteria are documented; each listed entry has a `README.md` and at least one runnable artifact (YAML graph, `demo.sh`, or Python script) | `examples/README.md`, `tests/unit/test_examples_readme_audit` |

### 50. CI CHANGELOG Gate

GitHub Actions job in commitlint.yml that blocks merge of feat and fix PRs unless CHANGELOG.md is modified in the PR diff.

**Feature Request:** FR-149

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-148 | `changelog-gate` job in `commitlint.yml` runs `git diff --name-only` against base/head SHAs and fails when `CHANGELOG.md` is absent from diff; job-level `if` condition restricts to `feat`/`fix` PR titles (skipped for other types); uses `actions/checkout@v4` with `fetch-depth: 0` for full history | `.github/workflows/commitlint.yml`, `tests/unit/test_ci_changelog_gate` |

### 51. Branch Protection Documentation

GitHub branch protection rules on main enforcing squash-merge only, required status checks, and no direct pushes.

**Feature Request:** FR-150

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-149 | `reference/break-glass.md` documents emergency bypass procedure with audit trail requirements; `CLAUDE.md` contains Branch Protection section listing enforced rules, required status checks, and link to break-glass procedure | `reference/break-glass.md`, `CLAUDE.md`, `tests/unit/test_branch_protection_docs` |

### 53. CI Conflict Marker Gate

CI job that fails when unresolved merge conflict markers are found in tracked files, complementing the local check-merge-conflict pre-commit hook.

**Feature Request:** FR-157

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-151 | CI conflict marker gate: The `conflict-check` job in `commitlint.yml` greps tracked files (excluding `.github/`) for conflict marker patterns and fails with non-zero exit when found | `.github/workflows/commitlint.yml`, `tests/unit/test_ci_conflict_check` |

### 54. CI Diary Existence Gate

CI gate ensuring feat/fix PRs with FR references include a diary reflection file in the diff.

**Feature Request:** FR-158

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-152 | `diary-gate` job in `commitlint.yml` extracts `FR-XXX` from PR title, runs `git diff --name-only` against base/head SHAs, and fails when no `docs/diary/*reflection*fr-{number}*` file is in diff; skips (passes) when PR title has no FR reference; job-level `if` condition restricts to `feat`/`fix` PR titles; uses `actions/checkout@v4` with `fetch-depth: 0` for full history | `.github/workflows/commitlint.yml`, `tests/unit/test_ci_diary_gate` |

### 55. Chaplain Inbox Documentation

Document the .chaplain/inbox/ workflow in CLAUDE.md so Claude Code sessions can discover and use the autonomous proposal pipeline.

**Feature Request:** FR-163

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-153 | `CLAUDE.md` contains a "Submitting Proposals" subsection documenting the `.chaplain/inbox/` workflow, matching the canonical source in `.github/copilot-instructions.md` verbatim, placed between the "Development Process" and "Development Commands" sections | `CLAUDE.md`, `tests/unit/test_claude_md_chaplain_inbox` |

### 56. Verification Gate Pattern

Per-node runtime verification with deterministic pattern matching. Checks stated predictions against actual node output.

**Feature Request:** FR-164

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-154 | NodeConfig accepts optional verification field (VerificationConfig) with question, on_fail, and count_range for runtime output validation | `yamlgraph/verification`, `node_factory/llm_nodes`, `linter/checks_contracts` |

### 57. Verification Count Range Pydantic

Count range verification claim parsed into CountRangeClaim Pydantic model with min/max validation.

**Feature Request:** FR-166

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-155 | Count range verification claim parsed into `CountRangeClaim` Pydantic model with `min_count` (int, ge=0), `max_count` (int, ge=0) and `model_validator` enforcing min ≤ max. Inverted ranges raise `ValueError` at parse time. Violation `details` exposes `expected_min`, `expected_max`, `actual_count` for programmatic inspection | `yamlgraph/verification`, `yamlgraph/models/__init__`, `tests/unit/test_verification` |

### 59. Configurable Loop Exit Target

loop_exits graph-level config maps node names to custom exit targets when loop limit is reached.

**Feature Request:** FR-172

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-093 | `loop_exits` graph-level config maps node names to custom exit targets when loop limit is reached. `GraphConfigSchema` validates as `dict[str, str]` with default `{}`. `make_expr_router_fn` accepts optional `loop_exit_target`; when `_loop_limit_reached` is True, returns configured target instead of `END`. Lint rule E009 validates keys exist in `loop_limits` and targets are valid nodes | `yamlgraph/routing`, `yamlgraph/edge_compiler`, `yamlgraph/graph_loader`, `yamlgraph/models/graph_schema`, `yamlgraph/linter/checks_semantic`, `tests/unit/test_loops` |

### 60. Worktree Venv Corruption Guard

Worktree venv corruption guard: validate_venv_health() raises on missing or broken venv, clean_stale_pth_entries() prevents import corruption from dangling editable installs.

**Feature Request:** FR-174

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-156 | Worktree venv corruption guard: `validate_venv_health()` raises `FileNotFoundError` when `.venv` directory is missing, `bin/python` is absent, or not executable (no silent skip). `validate_venv_symlink()` raises `OSError` when worktree `.venv` symlink doesn't resolve. `clean_stale_pth_entries()` removes `.pth`/`.egg-link` files referencing a deleted worktree directory to prevent import corruption from dangling editable installs | `yamlgraph/utils/worktree_helpers`, `scripts/enforce_worktree.sh`, `tests/unit/test_worktree_venv_guard` |

### 61. Bugfix Pipeline with Condemning Test

4-phase pipeline (condemn-fix-verify-submit_pr) for bugfix with condemning test first. Commandment 7 compliance.

**Feature Request:** FR-173

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-157 | Bugfix pipeline with condemning test: 4-phase pipeline (`condemn` → `fix` → `verify` → `submit_pr`) in `examples/bugfix/graph.yaml`. Condemn phase writes failing test against unchanged code (SKIP=pytest). `scripts/bugfix_worktree.sh` orchestrates in isolated worktree. `watch.sh` routes `Type.*Bug` FRs to bugfix pipeline. Each phase has dedicated prompt in `examples/bugfix/prompts/`. README documents Commandment 7 compliance | `examples/bugfix`, `scripts/bugfix_worktree.sh`, `.chaplain/watch.sh`, `tests/unit/test_bugfix_pipeline` |

### 62. Sequential Enforcement Mode

watch.sh runs enforce and bugfix pipelines in the foreground, eliminating merge conflicts on shared files.

**Feature Request:** FR-175

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-158 | Sequential enforcement mode: `watch.sh` runs `enforce_worktree.sh` and `bugfix_worktree.sh` in the foreground (no `nohup &`), capturing exit codes. Non-zero exits log a warning and continue the watch loop. Each pipeline completes before the next inbox item is processed, eliminating merge conflicts on shared files (ARCHITECTURE.md, CHANGELOG.md, req_coverage.py) | `.chaplain/watch.sh`, `tests/unit/test_watch_sequential_enforcement` |

### 64. Concurrency Safety Map

docs/concurrency-safety.md documents every concurrency pattern in YAMLGraph with verdict, model, shared state, and evidence.

**Feature Request:** FR-176

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-160 | Concurrency safety map: `docs/concurrency-safety.md` documents every concurrency pattern in YAMLGraph with verdict (Safe/Conditional/Unsafe), concurrency model, shared mutable state, safety invariant, and file:line evidence. Covers 6 areas: map node fan-out, checkpoint writes, graph cache, inquisitor diary writes, MCP server, async executor. Each entry classifies shared state and serialization mechanism | `docs/concurrency-safety.md`, `tests/unit/test_concurrency_safety_doc` |

### 65. Append-Only Capability Registry

Replace the monolithic CAPABILITIES dict in req_coverage.py with individual YAML files under capabilities/. New FRs add files rather than editing shared artifacts, eliminating merge conflicts on traceability data.

**Feature Request:** FR-178

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-161 | Append-only capability registry: individual YAML files in capabilities/ validated by scripts/validate_capabilities.py pre-commit hook, loaded by scripts/req_coverage.py. New capabilities are added as files, not edits to shared code. Pre-commit hook enforces schema on every commit. | `capabilities/`, `scripts/validate_capabilities.py`, `scripts/req_coverage.py`, `tests/unit/test_capability_registry.py` |

### 66. Append-Only Changelog

Replace monolithic CHANGELOG.md with fragment files under changelog/. Each change adds a markdown fragment with YAML front matter (type, scope, req). scripts/aggregate_changelog.py assembles fragments into CHANGELOG.md on demand. Eliminates merge conflicts on the changelog entirely.

**Feature Request:** FR-179

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-162 | Append-only changelog fragments: individual markdown files in changelog/unreleased/ with YAML front matter (type, scope, req). scripts/aggregate_changelog.py assembles all fragments into CHANGELOG.md grouped by version and type. Pre-commit and CI gates enforce fragment existence for feat/fix PRs. CHANGELOG.md is gitignored and generated on demand. | `changelog/`, `scripts/aggregate_changelog.py`, `scripts/migrate_changelog.py`, `tests/unit/test_changelog_fragments.py` |

### 67. Philosopher Daemon

Automates the Philosopher role by scanning diary entries for recurring patterns (Trap, Heuristic, Seed markers) and proposing graduations to Scripture. On-demand daemon writes proposals to .chaplain/inbox/ for Chaplain to process.

**Feature Request:** FR-184

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-184 | Automated diary pattern scanning and graduation proposals | `examples/philosopher/tools.py`, `examples/philosopher/graph.yaml`, `.chaplain/philosopher.sh` |
| REQ-YG-185 | Copilot node migration with Pydantic-validated JSON extraction | `examples/philosopher/models.py`, `examples/philosopher/tools.py`, `examples/shared/diary.py` |
| REQ-YG-194 | World context loading for philosopher reflection enrichment | `examples/philosopher/tools.py`, `examples/philosopher/graph.yaml`, `examples/philosopher/prompts/reflect.yaml`, `docs/world-context.md` |

### 68. CI Dependency Security Scan

CI workflow that runs pip-audit to scan Python dependencies for known vulnerabilities (CVEs) on every PR and version tag push.

**Feature Request:** FR-187

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-186 | CI workflow runs pip-audit --strict --desc on every PR and version tag push. Produces a 'security' required status check for branch protection. | `.github/workflows/security.yml` |

### 69. Knowledge Graph Graduation (FR-190)

Graduates the infrastructure_self_exempt trap to the Scripture Knowledge Graph in .github/copilot-instructions.md, based on 3 confirmed diary occurrences (audits 94, 95, 97). Names the cognitive blind spot where meta-tooling exempts itself from the quality gates it enforces.

**Feature Request:** FR-190

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-187 | infrastructure_self_exempt trap present in Scripture traps section with exact text, no existing traps/cures/process entries changed | `.github/copilot-instructions.md`, `tests/unit/test_knowledge_graph_fr190.py` |

### 70. Knowledge Graph Graduation (FR-191)

Graduates the plausible_wrong_answer trap in the Scripture Knowledge Graph in .github/copilot-instructions.md, based on 4 confirmed diary occurrences (FR-165, FR-164, FR-184, FR-185). Refines description from variant-specific ("Silent fallback") to pattern-general ("Output passes shape check but is semantically wrong → add assertion beyond type validation").

**Feature Request:** FR-191

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-188 | plausible_wrong_answer trap present in Scripture traps section with exact text, old description removed, no existing traps/cures/process entries changed | `.github/copilot-instructions.md`, `tests/unit/test_knowledge_graph_fr191.py` |

### 71. Release Changelog Sync Gate

Three-layer enforcement preventing changelog release drift: pre-commit hook blocks version bump with orphaned fragments, atomic release script enforces correct ordering, CI tag-push job validates tag-to-changelog alignment.

**Feature Request:** FR-192

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-189 | Pre-commit hook `changelog-release-sync` runs `check_changelog_release_sync.py` which blocks commit when pyproject.toml version field is changed in staged diff AND changelog/unreleased/ contains *.md files (excluding .gitkeep); allows commit when version unchanged or unreleased/ is empty; lists orphaned fragment names in error output. | `scripts/check_changelog_release_sync.py`, `.pre-commit-config.yaml`, `tests/unit/test_changelog_release_sync.py` |
| REQ-YG-190 | Atomic release script `scripts/release.sh` validates unreleased/ has fragments, freezes them to changelog/{VERSION}/, bumps pyproject.toml version, regenerates CHANGELOG.md via aggregate_changelog.py, commits with -F (file-based message to avoid dquote trap), and creates git tag; reference/release-checklist.md documents release.sh as canonical command. | `scripts/release.sh`, `reference/release-checklist.md`, `tests/unit/test_changelog_release_sync.py` |
| REQ-YG-191 | CI `release-hygiene` job in commitlint.yml triggers on tag push (v*), verifies changelog/{VERSION}/ directory exists for the tagged version, and checks for orphaned fragments in changelog/unreleased/; job has if-condition restricting execution to tag push events only. | `.github/workflows/commitlint.yml`, `tests/unit/test_changelog_release_sync.py` |

### 72. Knowledge Graph Mass Graduation (FR-193)

Graduates 8 recurring patterns from diary analysis into the Scripture Knowledge Graph in .github/copilot-instructions.md. Adds 5 process heuristics (automation_inherits_doctrine, changelog_ci_gate, detection_without_enforcement, enforcement_at_merge_boundary, mixed_commits_erode_auditability) and creates a new seeds: section with 3 forward-looking patterns (inquisitor_auto_escalation, req_coverage_as_universal_gate, verification_checkpoint_primitive). Based on Philosopher analysis of 220+ diary entries.

**Feature Request:** FR-193

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-192 | 5 process heuristics added to process: section, new seeds: section added with 3 seed patterns, changelog_ci_gate in process (not seeds), all descriptions are one-liners following key: "trigger → redirect" convention, no existing Knowledge Graph entries changed | `.github/copilot-instructions.md`, `tests/unit/test_knowledge_graph_fr193.py` |

### 73. Philosopher Challenge Node (FR-195)

Adds distill + challenge copilot nodes with unwrap gates to the philosopher graph, creating an adversarial quality gate (devil's advocate) that prevents weak or coincidental patterns from reaching .chaplain/inbox/. Implements ChallengeVerdict Pydantic model, unwrap_distill/unwrap_challenge tool functions, conditional routing on verdict, and distill/challenge prompt YAMLs.

**Feature Request:** FR-195

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-193 | ChallengeVerdict model with verdict/confidence/objections/surviving_arguments, unwrap_distill parses CopilotResult into Proposal or None, unwrap_challenge parses CopilotResult into ChallengeVerdict, write_proposals reads top_candidate, graph topology with conditional edges, distill/challenge prompts, reflect enriched with challenge context | `examples/philosopher/models.py`, `examples/philosopher/tools.py`, `examples/philosopher/graph.yaml`, `examples/philosopher/prompts/`, `tests/unit/test_philosopher.py` |

### 74. FSM Scripture CLAUDE.md (FR-199)

Upgrades fsm/CLAUDE.md (statemachine-engine/CLAUDE.md) from a four-line YAGNI/TDD/DRY/KISS summary to the full YAMLGraph doctrine: The 10 Commandments, Sermon of the Chaplain, Rite of Correction, Agents' prayer, Knowledge Graph of the Diary, FSM path/package adaptation table, and Anti-patterns table. All existing FSM-specific sections (Architecture, Usage Patterns, Communication Architecture, Troubleshooting) are preserved intact. Eliminates doctrine drift between the two codebases that share CI, Scripture, and release flow.

**Feature Request:** FR-199

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-195 | fsm/CLAUDE.md contains all 10 Commandments verbatim, Sermon of the Chaplain, Rite of Correction, Agents' prayer, Knowledge Graph of the Diary (including the_one_law, traps, cures, process, seeds sections), FSM path/package adaptation table mapping yamlgraph constructs to FSM equivalents, Anti-patterns table with FSM-specific wrong/correct pairs, all existing FSM sections preserved, four-line YAGNI/TDD/DRY/KISS block replaced (not duplicated) | `fsm/CLAUDE.md`, `tests/unit/test_fsm_claude_md_doctrine.py` |

<!-- END GENERATED CAPABILITIES -->

### 75. Portable Chaplain (FR-196)

Path-based Python tool loading and Chaplain subsystem portability.

**Feature Request:** FR-196

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-196 | PythonToolConfig supports path field (mutually exclusive with module) for file-path-based Python tool loading via spec_from_file_location; path resolves relative to CWD; validation rejects both-set and neither-set; parse_python_tools accepts path or module in YAML tool definitions | `yamlgraph/tools/python_tool.py`, `tests/unit/test_python_nodes.py` |

---

### 76. Horoscope Demo (FR-201)

Parallel daily horoscope generator using map node with static over: list.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-197 | Map node fans out over 12 zodiac signs in parallel, collects readings, assembles into Markdown document with exports section. Pure YAML graph with co-located prompts, date as runtime variable. | `examples/demos/horoscope`, `tests/integration/test_horoscope_demo.py` |

### 77. Image Generation Pipeline (FR-202)

End-to-end style-driven image generation: concept → subgraph prompt generation → save → Replicate z-image.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-198 | Image pipeline graph chains generate_concepts (LLM) → batch_image_prompts (subgraph) → save_prompts (Python tool writing prompts.txt) → generate_images (Python tool calling Replicate z-image with sidecar .txt files and best-effort EXIF embedding). | `examples/image_pipeline`, `tests/unit/test_image_pipeline.py` |

### 78. .fi Domain Crawl Demo

Multi-stage pipeline for crawling .fi country-level domains: LLM query planning, DuckDuckGo seed discovery, parallel page crawling via map node, and LLM sitemap summarisation.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-199 | .fi domain crawl demo: plan node produces search queries (parse_json), discover node filters to .fi TLD, map node crawls pages in parallel (max_items: 10), summarise node produces sitemap overview. crawl_page handles errors gracefully. No new dependencies. | `examples/demos/fi-domain-crawl`, `tests/unit/test_fi_domain_crawl.py` |

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-200 | `demo-gate` CI job in `commitlint.yml` extracts changed demo directories from `git diff` (excluding `demo-output.log` itself), verifies each has a `demo-output.log` in the diff, exits 1 on missing logs and 0 when no demos changed; job-level `if` condition restricts to `feat`/`fix` PR titles; uses `actions/checkout@v4` with `fetch-depth: 0`; pre-commit hook `demo-proof-check` calls `scripts/check_demo_proof.sh` with identical staged-file logic; `.gitignore` negates `*.log` for `examples/demos/*/demo-output.log`; `CLAUDE.md` documents `demo-gate` in branch protection section; enforcer Phase 2 prompt instructs capturing `demo-output.log` | `scripts/check_demo_proof.sh`, `.github/workflows/commitlint.yml`, `.pre-commit-config.yaml`, `CLAUDE.md`, `tests/unit/test_ci_demo_proof_gate.py` |

### 80. Standalone Scripture Template (FR-207)

Extract governance methodology into standalone template repository (`scripture-dev`).

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-201 | Template parameterization via `scripture.yaml` + `render.sh`: POSIX shell script reads YAML config and applies `sed` substitutions on `_templates/` source files; re-rendering from `_templates/` after config change replaces all `__PLACEHOLDER__` markers with new values | `projects/scripture-dev/render.sh`, `projects/scripture-dev/scripture.yaml`, `projects/scripture-dev/_templates/` |
| REQ-YG-202 | Rendered Scripture (copilot-instructions.md, pre-commit-config, hooks) contains zero framework-specific references (yamlgraph, LangGraph, Pydantic, LangSmith, REQ-YG, LangChain); no YAMLGraph-specific hooks included | `projects/scripture-dev/_templates/.github/copilot-instructions.md`, `projects/scripture-dev/_templates/.pre-commit-config.yaml` |
| REQ-YG-203 | Shell-based changelog aggregation (`aggregate_changelog.sh`) generates CHANGELOG.md from fragment files without Python dependency; Python aggregator (`aggregate_changelog.py`) available as opt-in upgrade | `projects/scripture-dev/scripts/aggregate_changelog.sh`, `projects/scripture-dev/scripts/aggregate_changelog.py` |
| REQ-YG-204 | Configurable requirement traceability: `req_coverage.py` accepts `--prefix` flag (default: `REQ`), no YAMLGraph module imports | `projects/scripture-dev/scripts/req_coverage.py` |
| REQ-YG-205 | Knowledge graph governance template: valid YAML with empty sections for boundaries, traps, cures, process, seeds | `projects/scripture-dev/templates/knowledge-graph.yaml` |
| REQ-YG-206 | `yamlgraph/discovery.py` extracts shared `discover_graphs()` from `mcp_server.py`; both MCP and A2A servers import from it; all existing MCP server tests pass | `yamlgraph/discovery.py`, `yamlgraph/mcp_server.py`, `tests/unit/test_discovery.py` |
| REQ-YG-207 | `yamlgraph/a2a_server.py` discovers graphs using shared `discover_graphs()` and creates `YAMLGraphAgentExecutor` wired to `A2AStarletteApplication` via `DefaultRequestHandler` | `yamlgraph/a2a_server.py`, `tests/unit/test_a2a_server.py` |
| REQ-YG-208 | Agent Card auto-generated from graph YAML metadata (name, description, skills) with streaming=True and no authentication; `build_agent_card()` produces valid `AgentCard` | `yamlgraph/a2a_server.py`, `tests/unit/test_a2a_server.py` |
| REQ-YG-209 | `task/send` invokes graph with variables parsed via Message Parsing Strategy (JSON → key_value → single_input → fallback); missing required vars rejected with `missing_variables` error; `PipelineError` maps to A2A error types | `yamlgraph/a2a_server.py`, `tests/unit/test_a2a_server.py` |
| REQ-YG-210 | `task/get` retrieves task status via `InMemoryTaskStore` (task_id = thread_id) | `yamlgraph/a2a_server.py` |
| REQ-YG-211 | `task/sendSubscribe` streams graph execution via SSE using `run_graph_streaming_native()` | `yamlgraph/a2a_server.py` |
| REQ-YG-212 | `task/cancel` cancels running graph execution via `YAMLGraphAgentExecutor.cancel()` emitting `canceled` TaskState | `yamlgraph/a2a_server.py`, `tests/unit/test_a2a_server.py` |
| REQ-YG-213 | `input-required` state emitted when graph hits `__interrupt__` node | `yamlgraph/a2a_server.py` |
| REQ-YG-214 | Router conditional edge route mapping redirects interrupt node targets to `{name}_prepare` and subgraph interrupt targets to `{name}__run`, while keeping original names as route labels for `make_router_fn` matching (FR-211) | `yamlgraph/edge_compiler`, `yamlgraph/graph_loader` |
| REQ-YG-215 | `scripts/block_ai_coauthor.py` commit-msg hook scans `Co-authored-by:` trailers for AI agent patterns (copilot, claude, chatgpt, gemini, gpt-?[0-9]+, github copilot), exits 1 with penance liturgy on match, exits 0 for clean messages and human co-authors; registered as `block-ai-coauthor` in `.pre-commit-config.yaml` at `commit-msg` stage before `absolution` | `scripts/block_ai_coauthor.py`, `.pre-commit-config.yaml`, `tests/unit/test_precommit_hooks.py` |
| REQ-YG-216 | `extract_variables()` subtracts `{% set %}` assignment targets (including those inside nested `{% for %}`/`{% if %}` blocks) from the undeclared-variables set so that locally-assigned names are never reported as required caller-supplied inputs (FR-214) | `yamlgraph/utils/template.py`, `tests/unit/test_template.py` |
| REQ-YG-217 | Research agent demo: 5-node graph with extract_intent (llm, Pydantic schema), plan_research (agent, discovery tools only), execute_research (agent, all tools), validate_findings (llm, Pydantic schema with gaps/confidence), synthesize_report (llm). Linear flow START→END. prompts_relative: true with local prompts/ directory. Shell tools use placeholder variables. Graph passes yamlgraph lint. (FR-215) | `examples/demos/research-agent`, `tests/unit/test_research_agent_demo.py` |
| REQ-YG-219 | `scripts/dependency_rationale.py` parses `pyproject.toml` core and optional dependencies (stripping version specifiers and extras), loads rationale entries from `docs/dependency-rationale.yaml`, reports undocumented packages in summary mode, and exits 1 in `--strict` when gaps exist; `--detail` prints all rationale entries; registered as `dependency-rationale` pre-commit hook (FR-219) | `scripts/dependency_rationale.py`, `docs/dependency-rationale.yaml`, `.pre-commit-config.yaml`, `tests/unit/test_dependency_rationale.py` |
| REQ-YG-222 | Ruff `S` ruleset (flake8-bandit security checks) enabled in `[tool.ruff.lint] select` in `pyproject.toml`. All 7 existing violations suppressed with `# noqa` and documented in `docs/confessions.md` (CONF-005 through CONF-009, CONF-035, CONF-036). `ruff check --select S yamlgraph/` exits 0. New security-sensitive code is automatically flagged at lint time. (FR-222) | `pyproject.toml`, `docs/confessions.md`, `tests/unit/test_ruff_security.py` |

### 84. Import-Linter Architectural Boundary Enforcement (FR-218)

Mechanical enforcement of three-layer architecture via `import-linter` contracts.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-218 | `.importlinter` config at repo root declares a `layers` contract with three layers: Presentation (`yamlgraph.cli`), Logic (graph_loader, node_factory, executor, linter, edge_compiler, node_compiler, map_compiler, routing, graph_cache, schema_loader, data_loader, discovery, executor_async, interactive_tool), Side Effects (tools, models, utils, config, constants, storage, contrib, executor_base, error_handlers, verification). `lint-imports` exits 0 on the current codebase. Pre-commit hook and CI step enforce the contract at every commit and PR. (FR-218) | `.importlinter`, `.pre-commit-config.yaml`, `.github/workflows/workflow.yml`, `tests/unit/test_import_linter.py` |

### 86. Ruff Security Rules (FR-222)

Ruff `S` ruleset (flake8-bandit) enabled for automated security linting.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-222 | Ruff `S` ruleset enabled in `[tool.ruff.lint] select`. All 7 existing violations (S104 ×2, S602, S603, S607 ×2, S701) suppressed with `# noqa` and documented in `docs/confessions.md`. `ruff check --select S yamlgraph/` exits 0. (FR-222) | `pyproject.toml`, `docs/confessions.md`, `tests/unit/test_ruff_security.py` |

---

## Key Data Flows

### 1. Graph Compilation

```
YAML file → load_graph_config() → GraphConfig
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
            build_state_class()  parse_tools()   compile_graph()
                    │                 │                 │
                    ▼                 ▼                 ▼
            Dynamic TypedDict   Tool Registry    StateGraph
                                                       │
                                              graph.compile()
                                                       │
                                                       ▼
                                              CompiledGraph
```

### 2. Node Execution

```
CompiledGraph.invoke(state)
         │
         ▼
    Node Function (from node_factory)
         │
         ├──→ check_requirements() - Verify required state keys
         │
         ├──→ check_loop_limit() - Prevent infinite loops
         │
         ├──→ skip_if_exists check - Resume support
         │
         ▼
    execute_prompt(prompt_name, variables, schema)
         │
         ├──→ load_prompt() - Load YAML prompt file
         │
         ├──→ format_prompt() - Substitute variables
         │
         ├──→ create_llm() - Get LLM instance
         │
         └──→ llm.with_structured_output() - Parse to Pydantic
                    │
                    ▼
              Return {state_key: result}
```

### 3. Error Handling

```
Node execution raises Exception
         │
         ▼
    on_error setting?
         │
    ┌────┼────┬────────┬──────────┐
    ▼    ▼    ▼        ▼          ▼
  skip  fail  retry  fallback  default
    │    │      │       │          │
    │    │      │       │          ▼
    │    │      │       │    PipelineError
    │    │      │       │    to state.errors
    │    │      │       │
    │    │      │       ▼
    │    │      │   Try alternate provider
    │    │      │
    │    │      ▼
    │    │   Loop up to max_retries
    │    │
    │    ▼
    │   Raise immediately
    │
    ▼
  Log warning, return {}
```

### 4. Pipeline Flow

```mermaid
graph TD
    A["📝 generate"] -->|content| B{should_continue}
    B -->|"✓ content exists"| C["🔍 analyze"]
    B -->|"✗ error/empty"| F["🛑 END"]
    C -->|analysis| D["📊 summarize"]
    D -->|final_summary| F

    style A fill:#e1f5fe
    style C fill:#fff3e0
    style D fill:#e8f5e9
    style F fill:#fce4ec
```

**Node Outputs:**

| Node | Output Type | Description |
|------|-------------|-------------|
| `generate` | Inline schema | Title, content, word_count, tags |
| `analyze` | Inline schema | Summary, key_points, sentiment, confidence |
| `summarize` | `str` | Final combined summary |

Output schemas are defined inline in YAML prompt files using the `schema:` block.

### 5. Resume Flow

Pipelines can be resumed from any checkpoint. The resume behavior uses `skip_if_exists`:
nodes check if their output already exists in state and skip LLM calls if so.

```mermaid
graph LR
    subgraph "Resume after 'analyze' completed"
        A1["Load State"] --> B1["analyze (skipped)"] --> C1["summarize"] --> D1["END"]
    end
```

```bash
# Resume an interrupted run (using checkpointer)
yamlgraph graph run graphs/my-graph.yaml --thread abc123
```

When resumed:
- Nodes with existing outputs are **skipped** (no duplicate LLM calls)
- Only nodes without outputs in state actually run
- State is preserved via SQLite checkpointing

---

## Extension Points

### Tutorial: Adding a New Node (YAML-First Approach)

Let's add a "fact_check" node that verifies generated content.

**Step 1: Create the prompt** (`prompts/fact_check.yaml`):
```yaml
system: |
  You are a fact-checker. Analyze the given content and identify
  claims that can be verified. Assess the overall verifiability.

user: |
  Content to fact-check:
  {content}

  Identify key claims and assess their verifiability.
```

**Step 2: Add the node to your graph** (`graphs/yamlgraph.yaml`):
```yaml
nodes:
  generate:
    type: llm
    prompt: generate
    output_schema:  # Inline schema - no Python model needed!
      title: str
      content: str
    state_key: generated

  fact_check:  # ✨ New node - just YAML!
    type: llm
    prompt: fact_check
    output_schema:  # Define schema inline
      is_accurate: bool
      issues: list[str]
    requires: [generated]
    variables:
      content: generated.content
    state_key: fact_check

edges:
  - from: START
    to: generate
  - from: generate
    to: fact_check
  - from: fact_check
    to: END
```

That's it! No Python node code needed. The graph loader dynamically generates the node function.

**Step 3 (optional): Define reusable schema** (`yamlgraph/models/schemas.py`):
```python
class FactCheck(BaseModel):
    """Structured fact-checking output."""
    claims: list[str] = Field(description="Claims identified in content")
    verified: bool = Field(description="Whether claims are verifiable")
    confidence: float = Field(ge=0.0, le=1.0, description="Verification confidence")
```

### Tutorial: Adding Conditional Branching

Route to different nodes based on analysis results (all in YAML):

```yaml
edges:
  - from: analyze
    to: rewrite_node
    condition:
      type: field_equals
      field: analysis.sentiment
      value: negative

  - from: analyze
    to: enhance_node
    condition:
      type: field_equals
      field: analysis.sentiment
      value: positive

  - from: analyze
    to: summarize  # Default fallback
```

### Adding a New Node Type

1. **Add to constants.py**:
   ```python
   class NodeType(StrEnum):
       MY_NODE = "my_node"
   ```

2. **Create factory function** in `node_factory.py`:
   ```python
   def create_my_node(node_name: str, node_config: dict) -> Callable:
       def node_fn(state: dict) -> dict:
           # Process state
           return {"result_key": result}
       return node_fn
   ```

3. **Register in node_compiler.py** `compile_node()`:
   ```python
   elif node_type == NodeType.MY_NODE:
       node_fn = create_my_node(node_name, node_config)
       graph.add_node(node_name, node_fn)
   ```

4. **Add tests** in `tests/unit/test_my_node.py`

5. **Document** in `reference/graph-yaml.md`

### Adding a New LLM Provider

1. **Add to config.py** `DEFAULT_MODELS`:
   ```python
   DEFAULT_MODELS = {
       "anthropic": os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5"),
       "my_provider": os.getenv("MY_PROVIDER_MODEL", "my-model"),
   }
   ```

2. **Update llm_factory.py**:
   ```python
   elif selected_provider == "my_provider":
       from langchain_my_provider import ChatMyProvider
       llm = ChatMyProvider(model=selected_model, temperature=temperature)
   ```

3. **Add to pyproject.toml** dependencies (optional extra)

4. **Update reference docs** (graph-yaml.md defaults section)

### Adding a New Tool Type

1. **Create parser** in `yamlgraph/tools/my_tool.py`:
   ```python
   def parse_my_tools(tools_config: dict) -> list[BaseTool]:
       """Parse tools with type: my_tool."""
       tools = []
       for name, config in tools_config.items():
           if config.get("type") == "my_tool":
               tools.append(create_my_tool(name, config))
       return tools
   ```

2. **Register in graph_loader.py**:
   ```python
   from yamlgraph.tools.my_tool import parse_my_tools

   # In compile_graph():
   all_tools.extend(parse_my_tools(config.tools))
   ```

3. **Add tests and docs**

---

## Testing Strategy

### Test Categories

| Category | Location | Purpose |
|----------|----------|---------|
| Unit | `tests/unit/` | Single module isolation |
| Integration | `tests/integration/` | Multi-module flows |

### Key Fixtures (conftest.py)

```python
@pytest.fixture
def mock_llm():
    """Mock LLM that returns predictable structured output."""

@pytest.fixture
def temp_graph_file(tmp_path):
    """Create temporary YAML graph files for testing."""

@pytest.fixture
def sample_state():
    """Common test state dictionary."""
```

### Testing Patterns

**1. Mock LLM for unit tests:**
```python
def test_node_execution(mock_llm, monkeypatch):
    monkeypatch.setattr("yamlgraph.executor.create_llm", lambda **k: mock_llm)
    result = execute_prompt("test", {})
    assert result is not None
```

**2. Real LLM for integration tests:**
```python
@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="No API key")
def test_full_pipeline():
    ...
```

**3. YAML fixture files:**
```python
def test_router(tmp_path):
    graph_yaml = tmp_path / "test.yaml"
    graph_yaml.write_text("""
version: "1.0"
nodes:
  classify:
    type: router
    ...
""")
    config = load_graph_config(graph_yaml)
```

### Requirement Traceability (ADR-001)

Every test function is linked to one or more requirements via `@pytest.mark.req`:

```python
@pytest.mark.req("REQ-YG-014", "REQ-YG-031")
def test_invoke_with_retry_succeeds_after_transient_failure(mock_llm):
    ...
```

#### `scripts/req_coverage.py`

Generates a traceability matrix from `@pytest.mark.req` markers using AST parsing.

| Command | Purpose |
|---------|---------|
| `python scripts/req_coverage.py` | Summary: per-capability coverage |
| `python scripts/req_coverage.py --detail` | Full mapping: every test → requirement |
| `python scripts/req_coverage.py --strict` | CI gate: exits non-zero if any REQ uncovered **or undocumented in ARCHITECTURE.md** |

#### Current Coverage (v0.4.21)

```
Requirements: 47/47 covered | Tagged tests: 1341 unique, 1671 test-req pairs

 ✅  1. Config Loading & Validation:  4/4 reqs, 202 tests
 ✅  2. Graph Compilation:            4/4 reqs, 109 tests
 ✅  3. Node Execution:               3/3 reqs,  99 tests
 ✅  4. Prompt Execution:             5/5 reqs, 295 tests
 ✅  5. Tool & Agent Integration:     4/4 reqs,  90 tests
 ✅  6. Routing & Flow Control:       3/3 reqs, 109 tests
 ✅  7. State Persistence:            3/3 reqs, 191 tests
 ✅  8. Error Handling:               5/5 reqs,  82 tests
 ✅  9. CLI Interface:                4/4 reqs,  72 tests
 ✅ 10. Export & Serialization:       4/4 reqs, 169 tests
 ✅ 11. Subgraph & Map:              3/3 reqs,  88 tests
 ✅ 12. Utilities:                    4/4 reqs, 139 tests
 ✅ 13. LangSmith Tracing:           1/1 reqs,  26 tests
```

See `docs/adr/001-test-requirement-traceability.md` for decision rationale.

---

## Code Quality Rules

### Module Size Limits
- **Target**: < 400 lines
- **Maximum**: 500 lines
- **Action**: Split into submodules if exceeded

### Type Hints
- All public functions must have type hints
- Use `|` for unions (Python 3.11+)
- Use `TypedDict` for state dictionaries

### Logging
- Use `logging.getLogger(__name__)`
- User-facing prints use emojis: 📝 🔍 ✓ ✗ 🚀

### Error Handling
```python
from yamlgraph.models import PipelineError

try:
    result = risky_operation()
except Exception as e:
    error = PipelineError.from_exception(e, node="node_name")
    return {"errors": state.get("errors", []) + [error]}
```

---

## Key Design Decisions

### 1. No State Mutation
Nodes return dicts with state updates. Never mutate state directly:
```python
# ❌ Wrong
def node_fn(state):
    state["key"] = value
    return state

# ✅ Correct
def node_fn(state):
    return {"key": value}
```

### 2. YAML Prompts Only
All prompts live in `prompts/*.yaml`. Never hardcode prompts in Python:
```python
# ❌ Wrong
llm.invoke("Generate a summary of {topic}")

# ✅ Correct
execute_prompt("summarize", {"topic": topic})
```

### 3. Factory Pattern for LLMs
Use the factory, not direct imports:
```python
# ❌ Wrong
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic(model="claude-3")

# ✅ Correct
from yamlgraph.utils.llm_factory import create_llm
llm = create_llm(provider="anthropic")
```

### 4. Thread-Safe Caching
LLM instances and loading stacks use thread-local storage:
```python
_llm_cache: dict[tuple, BaseChatModel] = {}
_cache_lock = threading.Lock()

_loading_stack: ContextVar[list[Path]] = ContextVar("loading_stack")
```

---

## File Reference

| File | Purpose | Capabilities |
|------|---------|-------------|
| `graph_loader.py` | YAML → LangGraph compilation | 1, 2 |
| `node_compiler.py` | Node dispatch to factories | 2 |
| `node_factory/` | Node function creation (subpackage) | 3, 5, 6, 11 |
| `node_factory/llm_nodes.py` | LLM and router nodes | 3 |
| `node_factory/streaming.py` | Token streaming support | 3 |
| `node_factory/control_nodes.py` | Interrupt and passthrough nodes | 6 |
| `node_factory/tool_nodes.py` | Tool call nodes | 5 |
| `node_factory/subgraph_nodes.py` | Nested graph composition | 11 |
| `node_factory/base.py` | Shared utilities (resolve_class, output models) | 12 |
| `executor.py` | Sync prompt execution with retry | 4 |
| `executor_base.py` | Shared executor logic (format, messages, retry check) | 4, 8 |
| `executor_async.py` | Async prompt execution and streaming | 4, 14 |
| `map_compiler.py` | Parallel fan-out with Send() | 11 |
| `routing.py` | Edge condition evaluation | 6 |
| `error_handlers.py` | Error strategies (skip, fail, retry, fallback) | 8 |
| `data_loader.py` | Load external data files into state | 1 |
| `schema_loader.py` | YAML schema → Pydantic models | 12 |
| `tools/agent.py` | ReAct agent creation | 5 |
| `tools/shell.py` | Shell tool execution | 5 |
| `tools/python_tool.py` | Python tool integration | 5 |
| `tools/nodes.py` | Tool node creation | 5 |
| `utils/llm_factory.py` | Multi-provider LLM factory (10 providers) | 3 |
| `utils/llm_factory_async.py` | Async LLM factory | 3 |
| `utils/expressions.py` | Template and state path resolution | 4 |
| `utils/conditions.py` | Condition expression evaluation | 6 |
| `utils/prompts.py` | Prompt loading and path resolution | 4 |
| `utils/template.py` | Variable extraction and validation | 4 |
| `utils/json_extract.py` | JSON extraction from LLM text | 4 |
| `utils/validators.py` | Config validation functions | 1 |
| `utils/logging.py` | Structured logging | 12 |
| `utils/parsing.py` | Literal parsing utilities | 12 |
| `utils/sanitize.py` | Input sanitization | 12 |
| `models/state_builder.py` | Dynamic state class generation | 7 |
| `models/graph_schema.py` | Pydantic graph config schema | 1 |
| `models/schemas.py` | PipelineError, ErrorType, GenericReport | 8, 12 |
| `config.py` | Centralized paths and settings | 12 |
| `constants.py` | NodeType, ErrorHandler, EdgeType enums | 12 |
| `storage/checkpointer_factory.py` | Checkpointer provisioning | 7 |
| `storage/checkpointer.py` | State persistence operations | 7 |
| `storage/simple_redis.py` | Redis-based checkpointer | 7 |
| `storage/serializers.py` | Serialization/deserialization helpers | 10 |
| `storage/export.py` | Export results/state to JSON | 10 |
| `linter/graph_linter.py` | Graph linting entry point | 1 |
| `linter/checks.py` | Individual lint checks | 1 |
| `linter/patterns/` | Pattern validators (agent, interrupt, map, router, subgraph) | 1 |
| `cli/__init__.py` | CLI entry point and parser | 9 |
| `cli/graph_commands.py` | graph run, info, codegen | 9, 10 |
| `cli/graph_validate.py` | graph validate, lint | 9 |
| `cli/schema_commands.py` | schema export, path | 10 |
| `cli/helpers.py` | Shared CLI utilities | 9 |
| `cli/deprecation.py` | Deprecated command handling | 9 |

---

## Contributing

1. **Read this doc first** - Understand the architecture
2. **TDD approach** - Write tests before implementation
3. **Small PRs** - One feature per PR
4. **Update docs** - Reference docs and docstrings
5. **Run full test suite**: `pytest tests/ -q`
