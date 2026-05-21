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
│ • 11 providers: │  │ • JSON Schema   │  │ • resolve_path()│
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
| 2 | Graph Compilation | `graph_loader`, `graph_loader.apply_loop_node_defaults`, `graph_loader.compile_graph`, `graph_loader.detect_loop_nodes`, … | REQ-YG-005 – 008, 220, 239 |
| 3 | Node Execution | `executor`, `executor_async`, `executor_base`, `node_factory/llm_nodes`, … | REQ-YG-009 – 011, 050, 223 |
| 4 | Prompt Execution | `executor.PromptExecutor`, `executor.execute_prompt`, `executor_async`, `executor_base.format_prompt`, … | REQ-YG-012 – 016, 216 |
| 5 | Tool & Agent Integration | `node_factory/tool_nodes`, `tools/agent`, `tools/nodes`, `tools/python_tool`, … | REQ-YG-017 – 020 |
| 6 | Routing & Flow Control | `node_factory/control_nodes`, `routing`, `utils/conditions` | REQ-YG-021 – 023, 214 |
| 7 | State Persistence | `models/state_builder`, `storage/checkpointer`, `storage/checkpointer_factory`, `storage/simple_redis` | REQ-YG-024 – 026 |
| 8 | Error Handling | `error_handlers`, `error_handlers.NodeResult`, `error_handlers.build_skip_error_state`, `error_handlers.check_loop_limit`, … | REQ-YG-027 – 031 |
| 9 | CLI Interface | `cli/__init__`, `cli/__main__`, `cli/deprecation`, `cli/graph_commands`, … | REQ-YG-032 – 035 |
| 10 | Export & Serialization | `cli/graph_commands.cmd_graph_codegen`, `cli/schema_commands`, `storage/export`, `storage/serializers` | REQ-YG-036 – 039 |
| 11 | Subgraph & Map | `map_compiler`, `map_compiler.wrap_for_reducer`, `node_factory/subgraph_nodes` | REQ-YG-040 – 042 |
| 12 | Utilities | `config`, `constants`, `node_factory/base`, `schema_loader`, … | REQ-YG-043 – 046 |
| 13 | LangSmith Tracing | `cli/graph_commands`, `utils/tracing` | REQ-YG-047 |
| 14 | Graph-Level Streaming | `executor_async` | REQ-YG-048 – 049, 065 |
| 15 | Expression Language | `utils/conditions`, `utils/expressions`, `utils/parsing` | REQ-YG-051 – 052 |
| 16 | Linter Cross-Reference | `linter/checks`, `linter/checks_contracts`, `linter/checks_semantic`, `linter/graph_linter`, … | REQ-YG-053 – 054, 069, 114, 408 |
| 17 | Execution Safety Guards | `cli/__init__`, `cli/graph_commands`, `config`, `executor`, … | REQ-YG-055 – 062, 064, 113 |
| 18 | Testing & Quality | `tests/conftest`, `tests/unit/test_requirement_enforcement` | REQ-YG-063 |
| 19 | MCP Server Interface | `mcp_server` | REQ-YG-066 – 068 |
| 20 | Contrib Utilities | `contrib/progress`, `contrib/utils` | REQ-YG-070 – 071 |
| 21 | Diary Digest Tools | `scripts/diary_digest_tools` | REQ-YG-072 |
| 22 | Code Quality Lints | `scripts/lint_inline_llm` | REQ-YG-073 |
| 23 | Skip-If-Exists Truthiness | `node_factory/llm_nodes._should_skip_if_exists` | REQ-YG-074 |
| 24 | Interactive Tool Node | `interactive_tool`, `node_factory/control_nodes`, `utils/conditions` | REQ-YG-075 |
| 25 | Tavily Domain RAG Demo | `examples/demos/tavily_rag` | REQ-YG-076 |
| 26 | Streaming Error Resilience | `executor_async`, `models/streaming` | REQ-YG-077 |
| 28 | Graph-Level Thinking Budget | `yamlgraph/models/graph_schema.py`, `yamlgraph/utils/llm_factory.py` | REQ-YG-083 |
| 30 | Copilot Node | `constants.NodeType.COPILOT`, `models/schemas`, `node_compiler`, `node_factory/copilot_node` | REQ-YG-087, 089, 105, 356 – 357 |
| 31 | Chaplain Diary Append | `examples/copilot/graph.yaml`, `examples/copilot/prompts/summarize.yaml`, `examples/shared/diary` | REQ-YG-090 |
| 32 | eBook Authoring Pipeline | `examples/ebook/nodes/writing.py`, `tests/unit/test_ebook_doctrine_validation.py` | REQ-YG-091 – 092 |
| 33 | Worktree Pipeline | `examples/enforce/graph.yaml`, `scripts/enforce_worktree.sh`, `utils/worktree_helpers` | REQ-YG-106 |
| 34 | Compiled Graph Cache | `executor_async`, `graph_cache` | REQ-YG-107 |
| 36 | Inquisitor Auto-Propose | `.chaplain/inquisitor.sh` | REQ-YG-118 |
| 37 | Architecture Provider Count Guard | `tests/unit/test_architecture_provider_count` | REQ-YG-121 |
| 38 | Post-Merge Finalization | `scripts/finalize_merge.sh`, `tests/unit/test_finalize_merge` | REQ-YG-125 |
| 39 | Inquisitor Commit-Delta Gate | `.chaplain/inquisitor.sh`, `tests/unit/test_inquisitor_gate` | REQ-YG-131 |
| 41 | Clean GIT Env Test Fixture | `tests/conftest.py`, `tests/unit/test_clean_git_env` | REQ-YG-140 |
| 42 | Inquisitor Worktree Gate | `.chaplain/inquisitor.sh`, `tests/unit/test_inquisitor_worktree_gate` | REQ-YG-142 |
| 43 | Copilot Session GC | `scripts/copilot_session_gc.sh`, `tests/unit/test_copilot_session_gc` | REQ-YG-141 |
| 44 | Judge SPLIT Verdict | `examples/copilot/prompts/judge.yaml`, `scripts/chaplain-prompts/judge.md`, `tests/unit/test_judge_split_verdict` | REQ-YG-143 |
| 45 | Diary Reflection Enforcement | `.pre-commit-config.yaml`, `scripts/finalize_merge.sh`, `tests/unit/test_precommit_hooks` | REQ-YG-144 |
| 46 | Diary Import CLI | `tests/unit/test_diary_commands`, `tests/unit/test_diary_importer`, `yamlgraph/cli/diary_commands.py`, `yamlgraph/diary/importer.py` | REQ-YG-122 |
| 47 | Phantom Requirement Detection | `scripts/req_coverage.py`, `tests/unit/test_req_coverage` | REQ-YG-145 |
| 48 | CHANGELOG Removal Completeness | `CHANGELOG.md`, `tests/unit/test_demo_cleanup_changelog` | REQ-YG-146 |
| 49 | Examples Documentation Audit | `examples/README.md`, `tests/unit/test_examples_readme_audit` | REQ-YG-147 |
| 50 | CI CHANGELOG Gate | `.github/workflows/commitlint.yml`, `scripts/gate_artifact_semantics.sh`, `tests/unit/test_ci_changelog_gate` | REQ-YG-148 |
| 51 | Branch Protection Documentation | `CLAUDE.md`, `reference/break-glass.md`, `tests/unit/test_branch_protection_docs` | REQ-YG-149 |
| 53 | CI Conflict Marker Gate | `.github/workflows/commitlint.yml`, `tests/unit/test_ci_conflict_check` | REQ-YG-151 |
| 54 | CI Diary Existence Gate | `.github/workflows/commitlint.yml`, `scripts/gate_artifact_semantics.sh`, `tests/unit/test_ci_diary_gate` | REQ-YG-152 |
| 55 | Chaplain Inbox Documentation | `CLAUDE.md`, `tests/unit/test_claude_md_chaplain_inbox` | REQ-YG-153 |
| 56 | Verification Gate Pattern | `yamlgraph/verification`, `node_factory/llm_nodes`, `linter/checks_contracts` | REQ-YG-154 |
| 57 | Verification Count Range Pydantic | `tests/unit/test_verification`, `yamlgraph/models/__init__`, `yamlgraph/verification` | REQ-YG-155 |
| 59 | Configurable Loop Exit Target | `tests/unit/test_loops`, `yamlgraph/edge_compiler`, `yamlgraph/graph_loader`, `yamlgraph/linter/checks_semantic`, … | REQ-YG-093 |
| 60 | Worktree Venv Corruption Guard | `scripts/enforce_worktree.sh`, `tests/unit/test_worktree_venv_guard`, `yamlgraph/utils/worktree_helpers` | REQ-YG-156 |
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
| 75 | Portable Chaplain (FR-196) | `yamlgraph/tools/python_tool.py`, `.chaplain/graphs/philosopher/tools.py`, `.chaplain/lib/diary.py`, `tests/unit/test_python_nodes.py` | REQ-YG-196 |
| 76 | Horoscope Demo | `examples/demos/horoscope` | REQ-YG-197 |
| 77 | Image Generation Pipeline | `examples/image_pipeline` | REQ-YG-198 |
| 78 | .fi Domain Crawl Demo | `examples/demos/fi-domain-crawl` | REQ-YG-199 |
| 79 | Demo Proof Gate | `scripts/check_demo_proof.sh`, `.github/workflows/commitlint.yml`, `.pre-commit-config.yaml` | REQ-YG-200 |
| 81 | A2A Protocol Server | `a2a_server`, `discovery`, `cli/a2a_commands` | REQ-YG-206 – 213 |
| 82 | Block AI Co-Author Trailers | `scripts/block_ai_coauthor.py`, `.pre-commit-config.yaml` | REQ-YG-215 |
| 83 | Research Agent Demo | `examples/demos/research-agent` | REQ-YG-217 |
| 84 | Import-Linter Architectural Boundary Enforcement | `.importlinter`, `.pre-commit-config.yaml`, `.github/workflows/workflow.yml` | REQ-YG-218 |
| 85 | Dependency Rationale Audit | `scripts/dependency_rationale.py`, `docs/dependency-rationale.yaml`, `.pre-commit-config.yaml` | REQ-YG-219 |
| 86 | Ruff Security Rules | `pyproject.toml`, `docs/confessions.md` | REQ-YG-222 |
| 87 | Ruff C901 Cognitive Complexity Gate | `pyproject.toml`, `docs/confessions.md` | REQ-YG-221 |
| 88 | Google/Vertex Thinking Budget Support | `yamlgraph/utils/llm_factory.py`, `yamlgraph/models/graph_schema.py`, `yamlgraph/linter/checks_providers.py` | REQ-YG-230 |
| 89 | Execution Timing Callback | `yamlgraph/utils/timing_tracker.py`, `yamlgraph/cli/graph_commands.py`, `yamlgraph/cli/__init__.py` | REQ-YG-231 |
| 90 | Graph Bench Command | `yamlgraph/cli/bench_commands.py`, `yamlgraph/cli/graph_commands.py`, `yamlgraph/cli/__init__.py` | REQ-YG-232 |
| 91 | Race Node Type | `yamlgraph/node_factory/race_node.py`, `yamlgraph/constants.py`, `yamlgraph/node_compiler.py`, `yamlgraph/models/graph_schema.py`, … | REQ-YG-233, 269 |
| 92 | Chatterbox TTS Demo | `examples/demos/chatterbox` | REQ-YG-234 |
| 93 | Chatterbox Voice Clone Demo | `examples/demos/chatterbox` | REQ-YG-235, 238 |
| 94 | Compile-Time Pipeline Templates | `yamlgraph/pipeline_template.py`, `yamlgraph/constants.py`, `yamlgraph/graph_loader.py`, `yamlgraph/linter/checks.py`, … | REQ-YG-236 |
| 95 | Parallel Fan-Out Edges | `yamlgraph/edge_compiler.py` | REQ-YG-237 |
| 96 | Per-Node Timeout | `yamlgraph/map_compiler.py`, `yamlgraph/node_compiler.py`, `yamlgraph/models/graph_schema.py`, `yamlgraph/models/schemas.py`, … | REQ-YG-078 |
| 98 | Pipeline Accumulated State | `yamlgraph/models/state_builder.py`, `reference/graph-yaml.md`, `tests/unit/test_state_builder_reducers.py` | REQ-YG-241 |
| 99 | Race and Pipeline Node Type Documentation | `reference/graph-yaml.md`, `reference/getting-started.md` | REQ-YG-240 |
| 100 | Chatterbox Multilingual CLI | `examples/demos/chatterbox` | REQ-YG-242 |
| 101 | A2A Consumer Contrib Client | `yamlgraph/contrib/a2a_client.py`, `yamlgraph/tools/python_tool.py` | REQ-YG-243 |
| 102 | Complete Worktree Teardown Self-Heal | `yamlgraph/utils/worktree_helpers`, `scripts/enforce_worktree.sh`, `scripts/bugfix_worktree.sh`, `tests/unit/test_worktree_teardown_self_heal` | REQ-YG-244 |
| 103 | A2A SDK v1.0 Compatibility | `yamlgraph/a2a_server.py`, `yamlgraph/a2a_message.py`, `yamlgraph/contrib/a2a_client.py`, `yamlgraph/cli/a2a_commands.py` | REQ-YG-245 |
| 104 | A2A Server Reference Documentation | `reference/a2a-server.md`, `reference/cli.md` | REQ-YG-246 |
| 105 | A2A Consumer Phase 2 — Agent Card, Skill Selection & Streaming | `yamlgraph/contrib/a2a_client.py` | REQ-YG-250 – 253 |
| 106 | GitHub Issues Remote Inbox | `.chaplain/watch.sh`, `tests/unit/test_github_issues_remote_inbox` | REQ-YG-247 |
| 107 | Guardrails Pattern Documentation | `reference/patterns.md`, `examples/README.md` | REQ-YG-254 |
| 108 | Changelog REQ Cross-Validation Gate | `scripts/check_changelog_req.py`, `graphs/enforcement/changelog-req-check.yaml`, `.pre-commit-config.yaml`, `.github/workflows/commitlint.yml` | REQ-YG-255 |
| 109 | Harden GitHub Issues Remote Inbox | `.chaplain/watch.sh`, `.chaplain/allowed-authors.txt` | REQ-YG-256 |
| 110 | Diary Index Graph | `examples/demos/diary_index` | REQ-YG-257 |
| 111 | Shared Graph Invocation | `graph_loader` | REQ-YG-258 |
| 113 | Chaplain Research Step | `.chaplain/graphs/watcher-plan` | REQ-YG-260 |
| 114 | Automated Post-Merge Finalization | `.chaplain/lib/finalize_lib.sh`, `.chaplain/watch.sh`, `scripts/finalize_merge.sh`, `tests/unit/test_automated_post_merge_finalization` | REQ-YG-261 |
| 116 | Acceptance Tests Before Enforce | `.chaplain/config/watcher-pipeline-v2.yaml`, `.chaplain/graphs/watcher-plan/step-plan-unified.yaml`, `.chaplain/graphs/watcher-plan/prompts/write-acceptance-tests.yaml`, `.chaplain/graphs/watcher-plan/prompts/judge.yaml`, … | REQ-YG-263 |
| 117 | Race Node parse_json & Content Normalization | `yamlgraph/node_factory/race_node.py`, `yamlgraph/utils/content.py`, `yamlgraph/tools/agent.py` | REQ-YG-264 |
| 118 | Copilot Node Model Selection | `yamlgraph/models/graph_schema.py`, `yamlgraph/node_compiler.py`, `yamlgraph/node_factory/copilot_node.py` | REQ-YG-265 |
| 119 | Race Node Timeout Fix | `yamlgraph/node_factory/race_node.py`, `yamlgraph/node_compiler.py` | REQ-YG-266 |
| 120 | CLI Inter-Run State Chaining | `yamlgraph/cli/__init__.py`, `yamlgraph/cli/graph_commands.py`, `yamlgraph/cli/helpers.py`, `yamlgraph/storage/export.py` | REQ-YG-267 – 268 |
| 121 | Async Race Node with Cancellable Candidates | `yamlgraph/node_factory/race_node.py`, `tests/unit/test_race_node.py` | REQ-YG-270 |
| 122 | Router Node with Candidates Race Support | `yamlgraph/node_factory/llm_nodes.py`, `yamlgraph/utils/validators.py`, `yamlgraph/models/state_builder.py`, `yamlgraph/node_compiler.py`, … | REQ-YG-271 |
| 124 | Watcher2 PR Reuse (FR-275) | `.chaplain/lib/watcher/create_pr.sh`, `tests/unit/test_watcher2_create_pr_reuse.py` | REQ-YG-272 |
| 125 | Pipeline Script Retirement (FR-276) | `.chaplain/scripts/start-system.sh`, `.chaplain/config/watcher-dispatcher.yaml`, `.chaplain/config/watcher-pipeline-v2.yaml`, `.chaplain/lib/watcher/worktree_setup.sh`, … | REQ-YG-276 |
| 126 | Test Speed Optimization | `pyproject.toml`, `tests/chaos_tools.py`, `tests/unit/test_map_node_timeout.py`, `tests/unit/test_race_node.py`, … | REQ-YG-275 |
| 127 | CI Hardening Consolidation | `.github/workflows/workflow.yml`, `.github/workflows/security.yml`, `.github/workflows/commitlint.yml`, `tests/unit/test_ci_hardening_consolidation.py` | REQ-YG-277 |
| 128 | Chaplain Documentation | `.chaplain/README.md`, `tests/unit/test_chaplain_readme_documentation` | REQ-YG-278 |
| 130 | Watcher2 Finalize Pre-commit Optimization | `.chaplain/scripts/start-system.sh`, `tests/unit/test_fr198_watcher2_finalize_optimization.py` | REQ-YG-286 |
| 131 | Anthropic Prompt Caching Support | `yamlgraph/executor_base.py`, `yamlgraph/utils/prompts.py`, `tests/unit/test_prompt_caching_fr276.py`, `tests/unit/test_prompt_caching_demo_fr219.py`, … | REQ-YG-287 – 293, 302 – 306 |
| 132 | Watcher2 CI Resilience | `.chaplain/lib/watcher/wait_ci.sh`, `tests/unit/test_fr279_watcher2_ci_resilience.py` | REQ-YG-294, 298 – 301 |
| 133 | Watcher2 CI Remediation Crash Fix | `.chaplain/scripts/start-system.sh`, `tests/unit/test_fr284_watcher2_ci_remediation_crash_fix.py` | REQ-YG-307 |
| 134 | Watcher2 Changelog Auto-Generation | `.chaplain/scripts/start-system.sh`, `.chaplain/graphs/watcher-enforce/prompts/enforce-critique-and-distill.yaml`, `.chaplain/graphs/watcher-enforce/prompts/enforce-finalize.yaml`, `.chaplain/graphs/watcher-enforce/step-ci-remediate.yaml` | REQ-YG-308 |
| 135 | Watcher2 Forensic Failure Diary | `.chaplain/scripts/start-system.sh`, `.chaplain/graphs/watcher-forensic/`, `.chaplain/lib/diary.py` | REQ-YG-309 |
| 136 | Per-Graph Typed MCP Tools | `yamlgraph/discovery.py`, `yamlgraph/mcp_server.py` | REQ-YG-310 – 314 |
| 137 | Watcher FSM System Startup Script | `.chaplain/scripts/start-system.sh` | REQ-YG-315 |
| 138 | Watcher Pipeline FSM Simplification | `.chaplain/config/watcher-pipeline-v2.yaml`, `.chaplain/graphs/watcher-plan/step-judge-v2.yaml`, `.chaplain/graphs/watcher-enforce/enforce-session.yaml` | REQ-YG-316 |
| 139 | Root README Accuracy Contract | `README.md`, `tests/unit/test_root_readme_accuracy.py` | REQ-YG-317 |
| 140 | Watcher2 Validate Split Fix/Gate | `.chaplain/config/watcher-pipeline-v2.yaml`, `.chaplain/actions/changelog_gen_action.py`, `.chaplain/actions/validate_gate_action.py`, `.chaplain/graphs/watcher-enforce/validate-session.yaml`, … | REQ-YG-318 |
| 141 | Shared FSM Bridge Module | `yamlgraph/utils/fsm/__init__.py`, `yamlgraph/utils/fsm/helpers.py`, `yamlgraph/utils/fsm/event_sender.py`, `yamlgraph/utils/fsm/graph_runner.py`, … | REQ-YG-319 |
| 142 | Skill Export Portable Packaging | `yamlgraph/skill_export.py`, `yamlgraph/skill_export_writer.py`, `yamlgraph/cli/__init__.py`, `yamlgraph/cli/skill_commands.py`, … | REQ-YG-320 – 326 |
| 143 | Agent Export Tool-Scoped Personas | `yamlgraph/skill_export.py`, `yamlgraph/skill_export_writer.py`, `yamlgraph/cli/__init__.py`, `yamlgraph/cli/skill_commands.py`, … | REQ-YG-327 – 332 |
| 145 | Copilot Instrumentation Gap Closure | `scripts/copilot_instrument.sh`, `scripts/extract_copilot_events.py`, `scripts/extract_copilot_events_lib.py`, `docs/copilot-instrumentation-poc.md`, … | REQ-YG-340 – 346 |
| 146 | FSM Snapshot Hooks Phase 2 Subclassing | `yamlgraph/utils/fsm/snapshot.py`, `yamlgraph/utils/fsm/action.py`, `yamlgraph/utils/fsm/graph_runner.py`, `yamlgraph/utils/fsm/__init__.py`, … | REQ-YG-347 |
| 147 | Graph Run JSON Stdout + TypeScript Node Integration | `yamlgraph/cli/__init__.py`, `yamlgraph/cli/graph_commands.py`, `yamlgraph/cli/helpers.py`, `yamlgraph/storage/export.py`, … | REQ-YG-348 – 355 |
| 148 | CI Co-authored-by Trailer Gate | `.github/workflows/commitlint.yml`, `tests/unit/test_fr385_ci_copilot_trailer_gate_red.py`, `CLAUDE.md` | REQ-YG-358 |
| 149 | Prompt Theme Analyzer Demo | `examples/demos/prompt_theme_analyzer/graph.yaml`, `examples/demos/prompt_theme_analyzer/tools.py`, `examples/demos/prompt_theme_analyzer/prompts/classify_theme.yaml`, `examples/demos/prompt_theme_analyzer/prompts/group_themes.yaml`, … | REQ-YG-359 |
| 150 | Philosopher's Book Demo | `examples/demos/philosopher_book/graph.yaml`, `examples/demos/philosopher_book/editorial_graph.yaml`, `examples/demos/philosopher_book/tools.py`, `examples/demos/philosopher_book/prompts/plan_chapter.yaml`, … | REQ-YG-404 – 405 |
| 151 | Graph Lint JSON Output | `yamlgraph/cli/__init__.py`, `yamlgraph/cli/graph_validate.py`, `tests/unit/test_fr406_lint_json_output_red.py`, `ARCHITECTURE.md` | REQ-YG-406 |
| 152 | Watcher2 Dispatcher Audit Cadence | `.chaplain/config/watcher-dispatcher.yaml`, `.chaplain/actions/syncing_inbox_action.py`, `.chaplain/actions/audit_action.py`, `tests/unit/test_fr411_watcher2_dispatcher_inquisitor_audit_cadence.py`, … | REQ-YG-407 |
| 153 | Built-in Questionnaire Gap Utilities | `yamlgraph/tools/questionnaire.py`, `tests/unit/test_fr421_questionnaire_gap_utilities_red.py`, `reference/probe-recap-questionnaire.md`, `ARCHITECTURE.md` | REQ-YG-409 – 410 |
| 156 | WIP Commit Subject Gate | `.pre-commit-config.yaml`, `.github/workflows/commitlint.yml`, `tests/unit/test_fr424_wip_main_gate_red.py`, `CLAUDE.md`, … | REQ-YG-419 |

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

**Feature Request:** FR-032

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-005 | Load YAML graph definitions into StateGraphs | `graph_loader`, `graph_loader.load_and_compile` |
| REQ-YG-006 | Validate graph structures (cycle detection, loop defaults) | `graph_loader.detect_loop_nodes`, `graph_loader.apply_loop_node_defaults` |
| REQ-YG-007 | Compile individual nodes | `node_compiler.compile_node`, `node_factory` |
| REQ-YG-008 | Compile full graph configuration | `graph_loader.compile_graph`, `node_compiler.compile_nodes` |
| REQ-YG-220 | Node type registry dispatches compile_node via NODE_TYPE_HANDLERS dict; unknown types raise ValueError (FR-220) | `node_compiler` |
| REQ-YG-239 | Per-node cache field parsed as CacheConfig; resolve_cache_policy converts to LangGraph CachePolicy; passed to graph.add_node() (FR-032) | `models/graph_schema`, `node_compiler` |

### 3. Node Execution

Create executable node functions for LLM, streaming, tool, interrupt, and subgraph behavior.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-009 | Node creation and streaming | `node_factory/llm_nodes`, `node_factory/streaming` |
| REQ-YG-010 | Synchronous LLM factory management | `utils/llm_factory` |
| REQ-YG-011 | Asynchronous LLM factory management | `utils/llm_factory_async` |
| REQ-YG-050 | Per-node and default-level `model` override: graph YAML `model` field flows through `execute_prompt()` to `create_llm()` | `node_factory/llm_nodes`, `executor`, `executor_async`, `executor_base` |
| REQ-YG-223 | LLM node factory decomposed into composable phases: LLMNodeConfig frozen dataclass, resolve_llm_node_config() pure config resolver, _apply_verification(), _resolve_route(), _handle_error() — each independently testable, all below C901=10 (FR-223) | `node_factory/llm_nodes` |

### 4. Prompt Execution

Load prompt YAML, validate variables, format messages, and run LLM calls sync and async.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-012 | Prompt loading and resolution | `utils/prompts` |
| REQ-YG-013 | Variable resolution and template management | `executor_base.format_prompt`, `utils/expressions`, `utils/template` |
| REQ-YG-216 | extract_variables() subtracts set-statement targets in nested blocks (FR-214) | `utils/template` |
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

**Feature Request:** FR-211

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-021 | Control node creation (interrupt, passthrough) | `node_factory/control_nodes` |
| REQ-YG-022 | Conditional routing functions | `routing` |
| REQ-YG-023 | Condition expression evaluation | `utils/conditions` |
| REQ-YG-214 | Router route mapping redirects interrupt targets to *_prepare and subgraph interrupt targets to *__run in conditional edge route mappings (FR-211) | `edge_compiler`, `graph_loader` |

### 7. State Persistence

Checkpointers and Redis storage for resuming pipelines and state history.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-024 | Dynamic state class generation | `models/state_builder` |
| REQ-YG-025 | Checkpointer provisioning | `storage/checkpointer_factory` |
| REQ-YG-026 | State persistence operations (Redis) | `storage/simple_redis`, `storage/checkpointer` |

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
| REQ-YG-408 | hedging_check enforces fallback-token hygiene in production Python by reporting lexical `fallback` usage as FB001, validating confession-backed allowlist mappings (`file:line -> CONF-XXX` with Code=FB001), preserving existing Pattern 1 detection, adding Pattern 2 (`X = expr or fallback`), and running pre-commit scope on both `yamlgraph/` and `scripts/`. | `scripts/hedging_check`, `.pre-commit-config.yaml`, `docs/confessions.md` |

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

### 18. Testing & Quality

Requirement traceability enforcement and testing infrastructure.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-063 | Requirement traceability enforcement: ADR-001 Tier 1 framework tests under `tests/unit` and `tests/integration` must have `@pytest.mark.req`; infrastructure hook tests under `.github/hooks/tests` are excluded by scope contract | `tests/conftest`, `tests/unit/test_requirement_enforcement`, `scripts/req_coverage.py` |

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
| REQ-YG-409 | Built-in questionnaire `detect_gaps(state)` utility returns `{"gaps": sorted_ids, "has_gaps": bool}` for required `schema.fields[].id` values missing from `state["extracted"]`, treating `None` and empty string as missing while ignoring non-required fields. | `yamlgraph/tools/questionnaire.py`, `tests/unit/test_fr421_questionnaire_gap_utilities_red.py` |
| REQ-YG-410 | Built-in questionnaire `normalize_extracted(state)` returns `{}` when `state["extracted"]` is already a dict and returns `{"extracted": {}}` for missing/non-dict values; utility module resolves via existing `type: python` tool wiring. | `yamlgraph/tools/questionnaire.py`, `yamlgraph/tools/python_tool.py`, `tests/unit/test_fr421_questionnaire_gap_utilities_red.py` |
| REQ-YG-411 | Classification validation enforces intent in {legitimate, suspicious, hostile}, danger_level int 1-5 (never 0), category in valid enum; invalid values normalized to safe defaults. | `examples/demos/hook_classifier/actions/classify_action.py`, `tests/unit/test_fr425_hook_classification_daemon_red.py` |
| REQ-YG-412 | Reason code mapping: classified-{intent} for valid intents, classify-error for unknown, classify-timeout for timeout exceptions. | `examples/demos/hook_classifier/actions/classify_action.py`, `tests/unit/test_fr425_hook_classification_daemon_red.py` |
| REQ-YG-413 | Append contract: open(mode='a'), print(json.dumps, flush=True), max 4096 bytes per line, concurrent writers produce no torn lines. | `examples/demos/hook_classifier/actions/classify_action.py`, `tests/unit/test_fr425_hook_classification_daemon_red.py` |
| REQ-YG-414 | Session history capped at 50 entries with 30-min sliding window; FIFO eviction drops oldest first. | `examples/demos/hook_classifier/actions/classify_action.py`, `tests/unit/test_fr425_hook_classification_daemon_red.py` |
| REQ-YG-415 | ClassifyAction on_success validates, logs, updates history; on_error writes deterministic fallback (intent=unknown, danger_level=1, category=error). | `examples/demos/hook_classifier/actions/classify_action.py`, `tests/unit/test_fr425_hook_classification_daemon_red.py` |
| REQ-YG-416 | Adversarial inputs (malformed LLM output, oversized payloads, prompt injection) normalized by validation; no crash, no danger_level=0 bypass. | `examples/demos/hook_classifier/actions/classify_action.py`, `tests/unit/test_fr425_hook_classification_daemon_red.py` |
| REQ-YG-417 | `tools.type: schema_loader` parsing returns typed `SchemaLoaderToolConfig`, enforces exactly one of `path`/`paths_from_state`, and integrates with `type: python` execution to load single graph-relative schema files into `state_key`. | `yamlgraph/tools/schema_loader_tool.py`, `yamlgraph/tools/python_tool.py`, `yamlgraph/graph_loader.py`, `yamlgraph/node_compiler.py`, `tests/unit/test_fr426_schema_loader_tool_type_red.py` |
| REQ-YG-418 | Schema-loader merge mode loads topic schemas from `paths_from_state + schema_dir + suffix`, preserves additive order (existing fields first), deduplicates by `deduplicate_by`, raises explicit missing-file errors, and rejects traversal outside graph root. | `yamlgraph/tools/schema_loader_tool.py`, `yamlgraph/tools/python_tool.py`, `yamlgraph/map_compiler.py`, `tests/unit/test_fr426_schema_loader_tool_type_red.py` |

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
| REQ-YG-356 | Copilot node supports explicit `backend: api` execution via `execute_prompt()`, while preserving default CLI behavior when backend is omitted or `cli`. | `node_factory/copilot_node`, `models/schemas` |
| REQ-YG-357 | Copilot lint rules are backend-aware: API backend warns when no explicit model signal is present and errors when API mode is combined with CLI-only `cli_flags`. | `linter/patterns/copilot`, `node_factory/copilot_node` |

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

Pre-commit hook diary-reflection-check rejects commits when staged docs/diary/ reflection files contain unfilled placeholder text or miss the literal `Seed:` marker.

**Feature Request:** FR-144

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-144 | `diary-reflection-check` pre-commit hook scans staged tracked reflection files for unfilled placeholder text and missing literal `Seed:` markers, then blocks commit; `finalize_merge.sh` creates stubs as untracked files (no `git add` of `docs/diary/`); hook passes when placeholders are filled and `Seed:` is present | `.pre-commit-config.yaml`, `scripts/finalize_merge.sh`, `tests/unit/test_precommit_hooks` |

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

GitHub Actions job in commitlint.yml that blocks merge of feat and fix PRs unless changed changelog fragments under changelog/unreleased/ pass substance validation.

**Feature Request:** FR-149

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-148 | `changelog-gate` job in `commitlint.yml` runs `git diff --name-only` against base/head SHAs and fails when no `changelog/unreleased/*.md` fragment is present in diff; each changed fragment must be non-empty, contain YAML front matter with `type:`, and include at least one markdown list item in the body; shared validation is sourced from `scripts/gate_artifact_semantics.sh`; job-level `if` condition restricts to `feat`/`fix` PR titles (skipped for other types); uses `actions/checkout@v4` with `fetch-depth: 0` for full history | `.github/workflows/commitlint.yml`, `scripts/gate_artifact_semantics.sh`, `tests/unit/test_ci_changelog_gate` |

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

CI gate ensuring feat/fix PRs with FR references include a diary reflection file in the diff and that the reflection passes substance validation.

**Feature Request:** FR-158

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-152 | `diary-gate` job in `commitlint.yml` extracts `FR-XXX` from PR title, runs `git diff --name-only` against base/head SHAs, and fails when no `docs/diary/*reflection*fr-{number}*` file is in diff; matching files must be non-empty, exceed 100 bytes, contain at least one markdown `##` header, and include `Seed:` marker; shared validation is sourced from `scripts/gate_artifact_semantics.sh`; skips (passes) when PR title has no FR reference; job-level `if` condition restricts to `feat`/`fix` PR titles; uses `actions/checkout@v4` with `fetch-depth: 0` for full history | `.github/workflows/commitlint.yml`, `scripts/gate_artifact_semantics.sh`, `tests/unit/test_ci_diary_gate` |

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

### 75. Portable Chaplain (FR-196)

PythonToolConfig supports a `path` field for file-path-based tool loading via importlib.util.spec_from_file_location(). Path resolves relative to CWD. Enables .chaplain/ directory portability by bypassing dotted-package import restrictions. Chaplain graphs, prompts, and Python tools relocated from examples/ to .chaplain/graphs/ for self-contained portability.

**Feature Request:** FR-196

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-196 | PythonToolConfig supports path field (mutually exclusive with module) for file-path-based Python tool loading via spec_from_file_location; path resolves relative to CWD; validation rejects both-set and neither-set; parse_python_tools accepts path or module in YAML tool definitions | `yamlgraph/tools/python_tool.py`, `tests/unit/test_python_nodes.py` |

### 76. Horoscope Demo

Parallel daily horoscope generator using map node with static over: list, producing a single Markdown document via exports. Pure YAML, zero Python.

**Feature Request:** FR-201

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-197 | Horoscope demo: map node fans out over 12 zodiac signs in parallel, collects readings, assembles into Markdown document with exports section. Pure YAML graph with co-located prompts, date as runtime variable. | `examples/demos/horoscope` |

### 77. Image Generation Pipeline

End-to-end style-driven image generation pipeline: concept generation via LLM, prompt generation via batch_image_prompts subgraph, save to file, and image generation via Replicate z-image with sidecar files and best-effort EXIF.

**Feature Request:** FR-202

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-198 | Image pipeline graph chains generate_concepts (LLM) → batch_image_prompts (subgraph) → save_prompts (Python tool writing prompts.txt) → generate_images (Python tool calling Replicate z-image with sidecar .txt files and best-effort EXIF embedding). | `examples/image_pipeline`, `tests/unit/test_image_pipeline.py` |

### 78. .fi Domain Crawl Demo

Multi-stage pipeline crawling .fi country-level domains: LLM query planning, DuckDuckGo seed discovery, parallel page crawling via map node, and LLM sitemap summarisation. Demonstrates HTTP tool nodes with map fan-out.

**Feature Request:** FR-205

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-199 | .fi domain crawl demo: plan node produces search queries (parse_json), discover node filters results to .fi TLD, map node crawls pages in parallel (max_items: 10), summarise node produces sitemap overview. crawl_page handles errors gracefully, returns structured dict with title/links/snippet. No new dependencies — uses digest + websearch extras. | `examples/demos/fi-domain-crawl`, `tests/unit/test_fi_domain_crawl.py` |

### 79. Demo Proof Gate

CI gate and pre-commit hook requiring demo-output.log artifact when demos are created or modified, and validating log semantics (not only presence): logs must be non-empty, contain success evidence, and contain no fatal execution markers. Enforces Commandment 2 ("demonstrate with example") at the merge boundary.

**Feature Request:** FR-206

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-200 | demo-gate CI job in commitlint.yml extracts changed demo directories from git diff (excluding demo-output.log itself), verifies each has a demo-output.log in the diff, then validates content semantics using shared rules: reject empty logs, reject fatal execution markers (for example Node .* failed, [ERROR], ❌ Error:, exit code [1-9]), and reject logs with no success evidence; exits 1 on violations and 0 when no demos changed; job-level if condition restricts to feat/fix PR titles; uses actions/checkout@v4 with fetch-depth: 0; pre-commit hook demo-proof-check calls scripts/check_demo_proof.sh with identical semantic rules; .gitignore negates *.log for examples/demos/*/demo-output.log; CLAUDE.md documents demo-gate in branch protection section; enforcer Phase 2 prompt instructs capturing demo-output.log | `scripts/check_demo_proof.sh`, `scripts/demo_log_semantics.sh`, `.github/workflows/commitlint.yml`, `.pre-commit-config.yaml`, `.gitignore`, `CLAUDE.md`, `.chaplain/graphs/watcher-enforce/prompts/enforce-test-demo.yaml`, `tests/unit/test_ci_demo_proof_gate.py` |

### 81. A2A Protocol Server

Expose YAMLGraph graphs as A2A (Agent-to-Agent) protocol agents. Supports task lifecycle (send, get, cancel, stream) and auto-generates Agent Cards from graph YAML metadata.

**Feature Request:** FR-208

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-206 | Shared graph discovery: extract discover_graphs() from mcp_server.py into discovery.py; both MCP and A2A servers import from it | `discovery`, `mcp_server` |
| REQ-YG-207 | A2A server discovers graphs using shared discover_graphs() and creates YAMLGraphAgentExecutor wired to A2AStarletteApplication | `a2a_server` |
| REQ-YG-208 | Agent Card auto-generated from graph YAML metadata (name, description, skills) with streaming=True and no authentication | `a2a_server` |
| REQ-YG-209 | Message parsing strategy: JSON → key_value → single_input → fallback; missing required vars rejected; PipelineError maps to A2A error types | `a2a_server` |
| REQ-YG-210 | task/get retrieves task status via InMemoryTaskStore | `a2a_server` |
| REQ-YG-211 | task/sendSubscribe streams graph execution via SSE | `a2a_server` |
| REQ-YG-212 | task/cancel cancels running graph execution | `a2a_server` |
| REQ-YG-213 | input-required state emitted when graph hits __interrupt__ node | `a2a_server` |

### 82. Block AI Co-Author Trailers

Commit-msg hook that detects and blocks AI agent Co-authored-by trailers (Copilot, Claude, ChatGPT, Gemini, GPT-*) before they enter the repository. Prints the offending line(s) and penance liturgy, then exits 1 to block the commit. Human co-authors and clean messages pass silently.

**Feature Request:** FR-212

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-215 | block_ai_coauthor.py commit-msg hook: regex-detects AI agent trailers, exits 1 with offending line + penance liturgy; exits 0 for clean and human-only messages; registered as block-ai-coauthor in pre-commit-config at commit-msg stage before absolution | `scripts/block_ai_coauthor.py`, `.pre-commit-config.yaml`, `tests/unit/test_precommit_hooks.py` |

### 83. Research Agent Demo

5-step agentic research demo: extract intent (llm) → plan research (agent) → execute research (agent) → validate findings (llm) → synthesize report (llm). Demonstrates bounded agent pipelines with least-privilege tool assignment, explicit validation nodes, and structured Pydantic schemas.

**Feature Request:** FR-215

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-217 | Research agent demo: 5-node graph with extract_intent (llm, Pydantic schema), plan_research (agent, discovery tools only), execute_research (agent, all tools), validate_findings (llm, Pydantic schema with gaps/confidence), synthesize_report (llm). Linear flow START→END. prompts_relative: true with local prompts/ directory. Shell tools use placeholder variables. Graph passes yamlgraph lint. | `examples/demos/research-agent`, `tests/unit/test_research_agent_demo.py` |

### 84. Import-Linter Architectural Boundary Enforcement

Mechanical enforcement of the three-layer architecture (Presentation → Logic → Side Effects) via import-linter contracts. Prevents silent degradation of module boundaries by blocking imports that violate declared layer dependencies at pre-commit and CI.

**Feature Request:** FR-218

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-218 | .importlinter config at repo root declares a layers contract with three layers: Presentation (cli), Logic (graph_loader, node_factory, executor, linter, edge_compiler, node_compiler, map_compiler, routing, graph_cache, schema_loader, data_loader, discovery, executor_async, interactive_tool), Side Effects (tools, models, utils, config, constants, storage, contrib, executor_base, error_handlers, verification). lint-imports exits 0 on the current codebase. Pre-commit hook and CI step enforce the contract at every commit and PR. | `.importlinter`, `.pre-commit-config.yaml`, `.github/workflows/workflow.yml`, `tests/unit/test_import_linter.py` |

### 85. Dependency Rationale Audit

Audit script that verifies every pyproject.toml dependency (core and optional) has a documented rationale in docs/dependency-rationale.yaml. Follows the noqa_coverage.py registry-audit pattern. Reports undocumented packages and exits 1 in --strict mode. Registered as pre-commit hook.

**Feature Request:** FR-219

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-219 | dependency_rationale.py parses pyproject.toml core and optional dependencies (stripping version specifiers and extras), loads rationale entries from docs/dependency-rationale.yaml, reports undocumented packages in summary mode, exits 1 in --strict when gaps exist, --detail prints all entries; registered as dependency-rationale pre-commit hook | `scripts/dependency_rationale.py`, `docs/dependency-rationale.yaml`, `.pre-commit-config.yaml`, `tests/unit/test_dependency_rationale.py` |

### 86. Ruff Security Rules

Ruff S ruleset (flake8-bandit) enabled in pyproject.toml for automated security linting. All 7 existing violations (S104, S602, S603, S607, S701) suppressed with documented noqa confessions. New security-sensitive code patterns are automatically flagged at lint time.

**Feature Request:** FR-222

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-222 | Ruff S ruleset enabled in [tool.ruff.lint] select. All 7 existing violations suppressed with # noqa and documented in docs/confessions.md (CONF-005 through CONF-009, CONF-035, CONF-036). ruff check --select S yamlgraph/ exits 0. New security-sensitive code is automatically flagged. | `pyproject.toml`, `docs/confessions.md`, `tests/unit/test_ruff_security.py` |

### 87. Ruff C901 Cognitive Complexity Gate

Enables ruff C901 (mccabe cognitive complexity) in the lint pipeline at threshold 15, closing the gap where radon CC (grade D ≥ 21) misses deeply nested functions. Functions above threshold are suppressed with noqa and documented in docs/confessions.md. CI inherits the rule via existing ruff check yamlgraph/.

**Feature Request:** FR-221

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-221 | C901 in ruff select with max-complexity = 15 in [tool.ruff.lint.mccabe]; functions above threshold suppressed with # noqa: C901 and documented in docs/confessions.md; CI inherits via existing ruff check yamlgraph/ | `pyproject.toml`, `docs/confessions.md`, `tests/unit/test_ruff_c901_gate.py` |

### 88. Google/Vertex Thinking Budget Support

Extends thinking_budget support to google and vertex providers. ChatGoogleGenerativeAI (langchain-google-genai 4.2.0+) accepts thinking_budget as a first-class constructor parameter. Schema validator relaxed to accept -1 (Google automatic mode) and any positive integer. Linter checks W071-1/2/4 scoped to Anthropic only; W071-3 extended with Gemini 2.5+ and Gemini 3 model substrings.

**Feature Request:** FR-230

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-230 | thinking_budget accepted by create_llm for anthropic, google, and vertex; raises ValueError for other providers; _create_google_llm and _create_vertex_llm forward thinking_budget kwarg to ChatGoogleGenerativeAI when non-None; temperature not overridden for google/vertex; schema NodeConfig.thinking_budget accepts -1 (Google auto), rejects < -1; GraphConfigSchema defaults validator aligned; linter W071-1/2/4 scoped to anthropic; linter W071-3 THINKING_CAPABLE_MODELS includes gemini-2.5 and gemini-3 substrings | `yamlgraph/utils/llm_factory.py`, `yamlgraph/models/graph_schema.py`, `yamlgraph/linter/checks_providers.py`, `tests/unit/test_fr230_google_vertex_thinking.py` |

### 89. Execution Timing Callback

LangChain callback handler tracking wall-clock duration of each LLM call in a graph run. Follows the same injection pattern as TokenUsageCallbackHandler. CLI --timing flag displays timing summary after execution.

**Feature Request:** FR-231

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-231 | ExecutionTimingCallbackHandler tracks per-call and total wall-clock LLM duration via on_llm_start/on_llm_end callbacks using time.monotonic; summary() returns total_duration_s, call_count, mean_duration_s; CLI --timing flag injects callback and prints timing summary | `yamlgraph/utils/timing_tracker.py`, `yamlgraph/cli/graph_commands.py`, `yamlgraph/cli/__init__.py`, `tests/unit/test_timing_tracker.py` |

### 90. Graph Bench Command

CLI command that runs a graph across multiple provider/model combinations and displays a side-by-side comparison table of execution time, token usage, and output. Supports --runs N for repetition, --export for JSON output, and --full for detailed output per model.

**Feature Request:** FR-231

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-232 | yamlgraph graph bench command accepts --models provider/model specs, --runs N, --export path, --full; runs graph against each model; captures timing and token usage per model; displays comparison table; per-model errors reported gracefully without aborting other models; BenchResult Pydantic model for structured results | `yamlgraph/cli/bench_commands.py`, `yamlgraph/cli/graph_commands.py`, `yamlgraph/cli/__init__.py`, `tests/unit/test_bench_command.py` |

### 91. Race Node Type

A type: race node that fires the same prompt to N provider/model candidates concurrently via ThreadPoolExecutor and returns the first successful result. Enables sub-second LLM responses for latency-sensitive graphs by hedging across providers. Includes schema validation (≥2 candidates, each with provider or model), _race_winner metadata in state, graph lint checks (E301–E304), and on_error policy support for all-candidates-fail.

**Feature Request:** FR-232

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-233 | type: race node fires prompt to all candidates concurrently using ThreadPoolExecutor; returns first successful result (not just first to complete); remaining candidates cancelled; all-fail triggers on_error policy; _race_winner metadata in state; candidates validated ≥2 entries each with provider or model; graph lint E301-E304; structured output works; NodeType.RACE in constants; NODE_TYPE_HANDLERS registered | `yamlgraph/node_factory/race_node.py`, `yamlgraph/constants.py`, `yamlgraph/node_compiler.py`, `yamlgraph/models/graph_schema.py`, `yamlgraph/models/state_builder.py`, `yamlgraph/linter/patterns/race.py`, `yamlgraph/linter/checks.py`, `tests/unit/test_race_node.py`, `tests/unit/test_linter_patterns_race.py` |
| REQ-YG-269 | Race node must not block on losing candidates after a winner is found. ThreadPoolExecutor shut down with wait=False, cancel_futures=True after returning winner. No with ThreadPoolExecutor context manager pattern. Loser threads terminate naturally; their results are discarded. | `yamlgraph/node_factory/race_node.py`, `tests/unit/test_race_node.py` |

### 92. Chatterbox TTS Demo

Multilingual text-to-speech demo using map node fan-out over 5 languages, Chatterbox Multilingual TTS for audio synthesis, and structured YAML prompts. Produces WAV files for en, es, fi, sv, de.

**Feature Request:** FR-233

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-234 | Chatterbox TTS demo: map node fans out over 5 languages (en, es, fi, sv, de), collects translations via structured output, synthesizes to WAV files via synthesize_audio python tool with Chatterbox Multilingual TTS. Auto-detects CUDA/CPU. Optional dependency chatterbox-tts. | `examples/demos/chatterbox` |

### 93. Chatterbox Voice Clone Demo

Voice cloning demo consolidated into examples/demos/chatterbox/ (FR-237). synthesize_cloned_audio in tools.py uses ChatterboxTTS (chatterbox.tts) with a caller-supplied reference audio clip (audio_prompt_path). Single-path synthesis: text + voice_prompt_path → output.wav. Device auto-detection follows cuda > mps > cpu. clone.yaml provides graph-based invocation; speak.py provides a standalone CLI. Supersedes chatterbox_clone/ (FR-236).

**Feature Request:** FR-237

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-235 | Chatterbox voice cloning demo: synthesize_cloned_audio in examples/demos/chatterbox/tools.py accepts text and voice_prompt_path, synthesizes to WAV via ChatterboxTTS (not ChatterboxMultilingualTTS). Device selection follows cuda > mps > cpu priority chain. clone.yaml graph and speak.py CLI both use this tool. Optional dependency chatterbox-tts. | `examples/demos/chatterbox` |
| REQ-YG-238 | Chatterbox speak CLI: speak.py accepts --ref (reference WAV, required) and positional text; validates ref exists (exit 1 on missing); calls ChatterboxTTS.generate() without language_id; writes to outputs/chatterbox/speak.wav; prints output path to stdout. | `examples/demos/chatterbox` |

### 94. Compile-Time Pipeline Templates

A type: pipeline meta-node that defines a sequence of stages once, iterates over a list of items, and expands to concrete nodes + edges before graph compilation. Eliminates repetitive boilerplate in multi-chapter, multi-phase graphs by 80%+. Includes {item.field} interpolation for stage configs, sequential intra-item and inter-item chaining, external edge rewriting, and linter validation (E401–E404).

**Feature Request:** FR-235

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-236 | type: pipeline meta-node expands at compile time into concrete nodes and sequential edges; {item.field} interpolation in prompt, variables, state_key; non-string fields copied verbatim; external edges rewritten to first/last expanded node; lint E401 (empty items), E402 (empty stages), E403 (unresolved item refs), E404 (missing name); NodeType.PIPELINE in constants; VALID_NODE_TYPES includes pipeline; expansion called in graph_loader after expand_interactive_tools | `yamlgraph/pipeline_template.py`, `yamlgraph/constants.py`, `yamlgraph/graph_loader.py`, `yamlgraph/linter/checks.py`, `yamlgraph/linter/patterns/pipeline.py`, `yamlgraph/linter/graph_linter.py`, `tests/unit/test_pipeline_template.py`, `tests/unit/test_linter_patterns_pipeline.py` |

### 95. Parallel Fan-Out Edges

Parallel fan-out edges allow a single node to fan out to multiple target nodes that execute concurrently, expressed as to: [a, b, c] without type: conditional. The edge compiler adds one add_edge() call per target. Handles interrupt node redirect (_prepare), map node targets (conditional edge with map function), START fan-out (conditional entry point), and END targets. Conditional routing (type: conditional) remains unchanged.

**Feature Request:** FR-234

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-237 | Parallel fan-out edges: to: [a, b, c] without type: conditional compiles as parallel fan-out via multiple add_edge() calls; handles interrupt node redirect to _prepare; handles map node targets via conditional edges; START fan-out uses conditional entry point; existing conditional routing with type: conditional unchanged | `yamlgraph/edge_compiler.py`, `tests/unit/test_parallel_fanout_edges.py` |

### 96. Per-Node Timeout

Per-node timeout bounding for map branches and all node types via ThreadPoolExecutor. Optional float timeout field on NodeConfig wraps node execution in a one-shot ThreadPoolExecutor; on concurrent.futures.TimeoutError a PipelineError with error_type=TIMEOUT_ERROR is returned. Map branches honour timeout in wrap_for_reducer; non-map nodes (llm, router, tool_call, python, agent, race) honour timeout via _maybe_wrap_timeout in node_compiler. Lint warning W203 emitted when a map node contains an agent sub-node without timeout.

**Feature Request:** FR-069

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-078 | Per-node timeout: optional float timeout field on NodeConfig validated as positive; map branch timeout via wrap_for_reducer with ThreadPoolExecutor; non-map node timeout via _maybe_wrap_timeout in node_compiler handlers; TIMEOUT_ERROR error type in ErrorType enum; from_exception classification unchanged (callers pass error_type explicitly); lint warning W203 for map+agent without timeout; except concurrent.futures.TimeoutError before except Exception in both paths | `yamlgraph/map_compiler.py`, `yamlgraph/node_compiler.py`, `yamlgraph/models/graph_schema.py`, `yamlgraph/models/schemas.py`, `yamlgraph/linter/patterns/map.py`, `tests/unit/test_map_node_timeout.py` |

### 98. Pipeline Accumulated State

User-configurable reducers in the YAML state: section and documented accumulated state pattern for pipelines. REDUCER_MAP maps "add", "last_value", "sorted_add" to their functions. parse_state_config() handles dict-syntax {type: str, reducer: str}. generate_typeddict_code() extracts type strings from dict-syntax entries. reference/graph-yaml.md documents the glossary accumulation pattern, sequential execution constraint, and W021 skip_if_exists: false requirement.

**Feature Request:** FR-238

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-241 | parse_state_config() handles dict-syntax state definitions {type: str, reducer: str}; REDUCER_MAP maps "add", "last_value", "sorted_add" to their functions; unknown reducer names log a warning; dict syntax without reducer key works as type-only; generate_typeddict_code() extracts type string from dict-syntax entries via CODEGEN_TYPE_MAP; reference/graph-yaml.md documents accumulated state pattern with glossary example, sequential execution constraint, and W021 skip_if_exists: false requirement | `yamlgraph/models/state_builder.py`, `reference/graph-yaml.md`, `tests/unit/test_state_builder_reducers.py` |

### 99. Race and Pipeline Node Type Documentation

Reference documentation for type: race (FR-232) and type: pipeline (FR-235) node types in reference/graph-yaml.md and reference/getting-started.md. Ensures graph authors can discover and configure these node types through the canonical reference docs.

**Feature Request:** FR-237

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-240 | reference/getting-started.md node type table includes race and pipeline rows; reference/graph-yaml.md has dedicated sections for type: race (purpose, candidates, timeout, state_key, _race_winner, on_error, example) and type: pipeline (purpose, items, stages, expansion semantics, {item.field} interpolation, example); doc examples match demo YAMLs | `reference/graph-yaml.md`, `reference/getting-started.md`, `tests/unit/test_race_pipeline_docs.py` |

### 100. Chatterbox Multilingual CLI

speak.py --lang flag routes to ChatterboxMultilingualTTS for non-English language codes (fi, sv, de, es, …). English path (--lang en, default) preserves the voice-cloning behaviour using ChatterboxTTS + --ref. --ref is incompatible with non-English lang and raises a clear error. Output is always outputs/chatterbox/speak.wav regardless of path. (FR-239)

**Feature Request:** FR-239

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-242 | Chatterbox multilingual CLI: speak.py --lang <code> routes to ChatterboxMultilingualTTS for non-English codes; --ref incompatible with non-English lang (parser.error); --lang en (default) preserves voice-cloning path requiring --ref; output always outputs/chatterbox/speak.wav. | `examples/demos/chatterbox` |

### 101. A2A Consumer Contrib Client

A2A consumer functionality via yamlgraph.contrib.a2a_client.send_a2a_message(), invoked as a type: python node. Sends Jinja2-templated message to external A2A agent via HTTP JSON-RPC (message/send), extracts text artifacts from the response, and returns {"response": text}. Supports timeout, Agent Card fetch, skill validation, and SSE streaming. Configuration via variables: on the python node. Replaces dedicated type: a2a_call (FR-253).

**Feature Request:** FR-240

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-243 | yamlgraph.contrib.a2a_client.send_a2a_message() sends Jinja2-templated message to external A2A agent URL via HTTP JSON-RPC message/send; extracts text artifacts from response; returns {"response": text}; invoked via type: python node with variables: for agent_url, message/message_template, skill, streaming, timeout; supports Agent Card fetch, skill validation, SSE streaming; uses httpx for sync and A2AClient for streaming transport | `yamlgraph/contrib/a2a_client.py`, `yamlgraph/tools/python_tool.py`, `tests/unit/test_a2a_contrib_client.py` |

### 102. Complete Worktree Teardown Self-Heal

Complete worktree teardown self-heal: validate_editable_install() probes import health via sys.executable; enforce_worktree.sh cleanup validates import yamlgraph after .pth cleaning and self-heals with pip install -e; bugfix_worktree.sh reaches FR-174 parity with venv health, symlink validation, .pth cleaning, import validation, and self-heal in cleanup.

**Feature Request:** FR-241

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-244 | validate_editable_install() in worktree_helpers.py probes import health via sys.executable; enforce_worktree.sh cleanup validates import yamlgraph after .pth cleaning and self-heals with pip install -e; bugfix_worktree.sh has FR-174 parity: validate_venv_health before symlink, validate_venv_symlink after symlink, clean_stale_pth_entries in cleanup, import validation, and pip install -e self-heal | `yamlgraph/utils/worktree_helpers`, `scripts/enforce_worktree.sh`, `scripts/bugfix_worktree.sh`, `tests/unit/test_worktree_teardown_self_heal` |

### 103. A2A SDK v1.0 Compatibility

Upgrade a2a-sdk dependency from v0.3 to v1.0 and fix all breaking changes. Protobuf-based types replace Pydantic models; Part construction uses member-name discriminator (no 'kind' field); TextPart class removed; Role/TaskState enums use SCREAMING_SNAKE_CASE; A2AStarletteApplication replaced by Starlette + route factories; EventQueue.close() removed; AgentCard.url field removed; InMemoryTaskStore API requires ServerCallContext; card JSON serialization uses MessageToDict.

**Feature Request:** FR-244

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-245 | A2A SDK v1.0 compatibility: protobuf-based types replace Pydantic models; Part(text=...) replaces Part(root=TextPart(text=...)); TextPart removed; Role.ROLE_USER/ROLE_AGENT replaces Role.user/agent; TaskState.TASK_STATE_* replaces TaskState.*; A2AStarletteApplication replaced by Starlette + create_jsonrpc_routes/create_agent_card_routes; EventQueue.close() removed; AgentCard.url field removed; InMemoryTaskStore.save/get require ServerCallContext; DefaultRequestHandler requires agent_card parameter; kind discriminator removed from JSON-RPC part payloads (member-name discriminator); contrib/a2a_client.py extraction uses key-presence check; a2a_commands.py uses MessageToDict for card JSON serialization | `yamlgraph/a2a_server.py`, `yamlgraph/a2a_message.py`, `yamlgraph/contrib/a2a_client.py`, `yamlgraph/cli/a2a_commands.py`, `tests/unit/test_a2a_server.py`, `tests/unit/test_a2a_message.py`, `tests/unit/test_a2a_commands.py`, `tests/unit/test_a2a_contrib_client.py` |

### 104. A2A Server Reference Documentation

User-facing reference documentation for the A2A protocol server (FR-208/209/225, CAP-81). Covers quickstart, CLI commands, Agent Card generation, message parsing, task lifecycle, error mapping, interrupts, authentication, deployment patterns, and MCP relationship. Also updates reference/cli.md with a2a subcommands and reference/README.md index.

**Feature Request:** FR-246

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-246 | reference/a2a-server.md created with 10 sections: Quickstart, CLI Commands, Agent Card Generation, Message-to-State Mapping, Task Lifecycle, Error Mapping, Interrupt/Human-in-Loop, Authentication, Deployment Patterns, Relationship to MCP Server; reference/cli.md updated with a2a serve and a2a card subcommands; reference/README.md links to a2a-server.md; all examples verified against a2a_server.py, a2a_message.py, cli/a2a_commands.py | `reference/a2a-server.md`, `reference/cli.md`, `tests/unit/test_a2a_server_docs.py` |

### 105. A2A Consumer Phase 2 — Agent Card, Skill Selection & Streaming

A2A consumer features in yamlgraph.contrib.a2a_client: Agent Card discovery via sync httpx.get() to /.well-known/agent.json, ContextVar-scoped caching per graph invocation, skill selection validated against Agent Card skills at runtime, and SSE streaming via A2AClient.send_message_streaming() in a dedicated thread. Replaces dedicated a2a_call node type linter checks (W901/E904) with runtime validation in contrib function (FR-253).

**Feature Request:** FR-248

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-250 | send_a2a_message() fetches Agent Card via sync httpx.get() to {agent_url}/.well-known/agent.json; parsed into SDK AgentCard model via ParseDict; cached per agent_url within graph invocation using ContextVar; cache isolated across invocations; timeout configurable | `yamlgraph/contrib/a2a_client.py`, `tests/unit/test_a2a_contrib_client.py` |
| REQ-YG-251 | skill parameter in state selects a specific agent skill; validated against Agent Card skills at runtime; ValueError raised on skill ID miss with available skills listed in error message; no card fetch when skill not specified | `yamlgraph/contrib/a2a_client.py`, `tests/unit/test_a2a_contrib_client.py` |
| REQ-YG-252 | streaming: true in state uses A2AClient.send_message_streaming() via dedicated thread with own event loop; requires card.capabilities.streaming == True; result returned as complete string; streaming events logged at DEBUG level; transport-only (not FR-030 graph-level streaming) | `yamlgraph/contrib/a2a_client.py`, `tests/unit/test_a2a_contrib_client.py` |
| REQ-YG-253 | Dedicated type: a2a_call node type replaced by type: python + yamlgraph.contrib.a2a_client contrib function; NodeType.A2A_CALL removed from constants; a2a_nodes.py and linter/patterns/a2a.py deleted; W901/E904 linter checks removed (skill/streaming validated at runtime in contrib); FR-252 enables variables: resolution on type: python nodes | `yamlgraph/contrib/a2a_client.py`, `yamlgraph/tools/python_tool.py`, `tests/unit/test_a2a_contrib_client.py` |

### 106. GitHub Issues Remote Inbox

watch.sh syncs open GitHub Issues labeled 'chaplain' into the local inbox, removes the label after import, and closes the issue with a commit reference on successful enforcement. Gracefully degrades when gh CLI is unavailable.

**Feature Request:** FR-243

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-247 | GitHub Issues remote inbox: watch.sh polls for open issues labeled 'chaplain' via two-pass gh CLI (list numbers, then view each), writes .chaplain/inbox/gh-{number}.md, removes the label after import, initializes EXIT_CODE=1 as sentinel before enforcement branches, and closes the originating issue with commit hash on EXIT_CODE=0. Sync is silently skipped when gh is not installed or not authenticated. CLAUDE.md and copilot-instructions.md document remote submission. | `.chaplain/watch.sh`, `CLAUDE.md`, `.github/copilot-instructions.md`, `tests/unit/test_github_issues_remote_inbox` |

### 107. Guardrails Pattern Documentation

Document the input guardrails pattern (echo → validate → respond) as Pattern 11 in reference/patterns.md. References the existing examples/openai_proxy/ implementation as a production example. Updates examples/README.md with a Guardrails category.

**Feature Request:** FR-249

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-254 | Pattern 11 "Input Guardrails" in reference/patterns.md documents the echo → validate → respond pipeline with Problem/Solution sections, valid YAML graph example, Python tool implementations, prompt template, Key Points table, and Related links referencing examples/openai_proxy/; examples/README.md includes a Guardrails category in "By Feature" section | `reference/patterns.md`, `examples/README.md`, `tests/unit/test_guardrails_pattern_docs.py` |

### 108. Changelog REQ Cross-Validation Gate

Validates that changelog fragment req: front-matter values reference correct requirement IDs from the capabilities registry. Mechanical pre-filter for single-REQ capabilities; LLM classifier (Haiku) for multi-REQ capabilities where mechanical disambiguation is impossible.

**Feature Request:** FR-247

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-255 | Changelog REQ cross-validation gate: scripts/check_changelog_req.py parses YAML front-matter req: from changelog/unreleased/*.md, validates each REQ-YG-XXX exists in capabilities/CAP-*.yaml via direct id: lookup (rejects phantoms), skips fragments without req: field; single-REQ CAPs pass mechanically; multi-REQ CAPs deferred to LLM graph graphs/enforcement/changelog-req-check.yaml (Haiku, temperature 0); --strict exits non-zero on failure; --skip-llm runs mechanical-only; pre-commit hook and CI job wired | `scripts/check_changelog_req.py`, `graphs/enforcement/changelog-req-check.yaml`, `.pre-commit-config.yaml`, `.github/workflows/commitlint.yml` |

### 109. Harden GitHub Issues Remote Inbox

Author allowlisting, body size cap (10,000 chars), and forensic author audit header for the GitHub Issues remote inbox (FR-243 hardening). Prevents prompt injection via untrusted issue bodies.

**Feature Request:** FR-251

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-256 | watch.sh gates GitHub Issue import on .chaplain/allowed-authors.txt (one login per line); issues from unlisted authors are skipped with warning, label retained; when file absent all authors accepted; body truncated at BODY_SIZE_CAP (10000) with warning; every imported file starts with <!-- author: @login --> audit header; author login fetched before title/body for early rejection (FR-251) | `.chaplain/watch.sh`, `.chaplain/allowed-authors.txt`, `tests/unit/test_harden_remote_inbox.py` |

### 110. Diary Index Graph

Demo graph that reads diary entries from docs/diary/*.md, extracts structured data (traps, heuristics, seeds, FR references) via map+llm, and produces a cross-reference index at docs/diary-index.yaml. Deterministic Python aggregation, no LLM for counting.

**Feature Request:** FR-254

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-257 | Diary index graph: map node fans out over diary files, LLM extracts traps/heuristics/seeds/FR refs per entry, deterministic Python aggregate_index() builds cross-reference index (traps_index sorted by frequency, seeds_index with dedup, fr_index reverse mapping, heuristics_candidates with 2+ threshold, statistics by category). write_index() persists to docs/diary-index.yaml. Graph lints clean. Inline schema on extraction prompt. model: claude-haiku-4-5 for cost. | `examples/demos/diary_index` |

### 111. Shared Graph Invocation

Shared invoke_graph() function in graph_loader eliminates duplicated graph invocation logic across MCP and A2A servers (FR-255).

**Feature Request:** FR-255

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-258 | invoke_graph(path, variables, config) in graph_loader.py: loads config, compiles graph, invokes synchronously with optional LangGraph run config. MCP and A2A servers delegate to this shared function. | `graph_loader`, `mcp_server`, `a2a_server` |

### 113. Chaplain Research Step

Research guidance in the active watcher-plan runtime. The unified planning step and watcher-plan research prompt gather strategic evidence (existing abstractions, diary precedents, usage evidence, classification signal) so Judge can distinguish technically feasible from strategically warranted (FR-257).

**Feature Request:** FR-257

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-260 | Unified plan step in `.chaplain/graphs/watcher-plan/step-plan-unified.yaml` includes explicit research guidance, while `.chaplain/graphs/watcher-plan/prompts/research.yaml` preserves strategic research instructions (existing abstraction scan, diary precedent check, usage evidence, classification signal); judge prompt in watcher-plan includes strategic classification criteria (framework primitive / contrib / pattern documentation / reject) (FR-257). | `.chaplain/graphs/watcher-plan/step-plan-unified.yaml`, `.chaplain/graphs/watcher-plan/prompts/research.yaml`, `.chaplain/graphs/watcher-plan/prompts/judge.yaml` |

### 114. Automated Post-Merge Finalization

Shared finalization library and watch.sh integration that automatically creates finalization PRs for recently merged feature PRs, eliminating the manual finalize_merge.sh step from the Chaplain pipeline.

**Feature Request:** FR-258

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-261 | Shared library `.chaplain/lib/finalize_lib.sh` provides `extract_fr_metadata`, `create_changelog_fragment`, `update_fr_status`, and `create_diary_stub` functions; `scripts/finalize_merge.sh` sources the library instead of inlining logic; `watch.sh` detects recently merged PRs via timestamp-based `gh pr list` query, creates finalization PRs with changelog fragment, FR status update, and diary stub, enables auto-merge, and skips already-finalized FRs idempotently | `.chaplain/lib/finalize_lib.sh`, `.chaplain/watch.sh`, `scripts/finalize_merge.sh`, `tests/unit/test_automated_post_merge_finalization` |

### 116. Acceptance Tests Before Enforce

Ensure acceptance tests are authored before enforce execution in the active FSM runtime. Setup creates the worktree, the unified plan step includes acceptance-test authoring instructions, Judge evaluates test evidence, and enforce_session executes against that contract.

**Feature Request:** FR-260

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-263 | `setup` action in watcher-pipeline-v2 creates the worktree before plan; unified plan prompt includes acceptance-test authoring protocol using `@pytest.mark.req` tags and RED commit guidance; judge prompt includes criterion 8 for test evidence evaluation; enforce session prompt explicitly preserves acceptance test assertions as the contract for implementation (FR-260). | `.chaplain/config/watcher-pipeline-v2.yaml`, `.chaplain/graphs/watcher-plan/step-plan-unified.yaml`, `.chaplain/graphs/watcher-plan/prompts/write-acceptance-tests.yaml`, `.chaplain/graphs/watcher-plan/prompts/judge.yaml`, `.chaplain/graphs/watcher-enforce/prompts/enforce-session.yaml`, `.chaplain/lib/worktree.py` |

### 117. Race Node parse_json & Content Normalization

Race node _invoke_candidate normalizes response.content to string via shared normalize_content() in yamlgraph/utils/content.py (handles Anthropic list-of-blocks, OpenAI string, None). Race node supports parse_json: true config — skips output_model resolution at factory time and applies extract_json() after content normalization. agent.py imports from shared utility instead of inlining.

**Feature Request:** FR-264

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-264 | Race node _invoke_candidate normalizes response.content to string via shared normalize_content(); supports parse_json: true skipping output_model and applying extract_json(); agent.py uses shared utility | `yamlgraph/node_factory/race_node.py`, `yamlgraph/utils/content.py`, `yamlgraph/tools/agent.py`, `tests/unit/test_race_node.py` |

### 118. Copilot Node Model Selection

Copilot nodes support model as a top-level node config key, consistent with LLM nodes. Falls back to defaults.model from graph metadata when not specified. cli_flags.model continues to work as the highest-priority override. Priority chain: cli_flags.model > node-level model > defaults.model > omit.

**Feature Request:** FR-266

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-265 | NodeConfig has model: str \| None field; create_copilot_node accepts defaults parameter; _compile_copilot_node passes effective_defaults to factory; model resolution follows cli_flags.model > node-level model > defaults.model > omit; CopilotResult.model reflects the resolved model regardless of source | `yamlgraph/models/graph_schema.py`, `yamlgraph/node_compiler.py`, `yamlgraph/node_factory/copilot_node.py`, `tests/unit/test_copilot_node_model_selection.py` |

### 119. Race Node Timeout Fix

Race node applies exactly one timeout mechanism — its native as_completed(timeout=...). The node compiler does not apply _maybe_wrap_timeout to race nodes (nested ThreadPoolExecutors silently drop the return value). On timeout expiry (no candidate succeeds within deadline), the race node produces a structured PipelineError(TIMEOUT_ERROR) and respects on_error configuration. Without on_error, raises AllCandidatesFailedError.

**Feature Request:** FR-267

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-266 | Race node applies exactly one timeout mechanism — its native as_completed(timeout=...); _compile_race_node must NOT call _maybe_wrap_timeout; on timeout expiry (no candidate succeeds within deadline), race node produces PipelineError(TIMEOUT_ERROR) and respects on_error config; without on_error, raises AllCandidatesFailedError; race timeout is total race deadline, not per-candidate | `yamlgraph/node_factory/race_node.py`, `yamlgraph/node_compiler.py`, `tests/unit/test_race_node.py` |

### 120. CLI Inter-Run State Chaining

--import-state and --export-state flags for yamlgraph graph run enabling external orchestrators to chain graph invocations across shell boundaries while preserving state, including CopilotResult.session_id for copilot session resume.

**Feature Request:** FR-269

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-267 | --import-state loads exported JSON as initial graph state; merge order is graph_config.data < imported < --var-file < --var; missing file prints clear error and exits 1; malformed JSON prints clear error and exits 1 | `yamlgraph/cli/__init__.py`, `yamlgraph/cli/graph_commands.py`, `yamlgraph/cli/helpers.py`, `tests/unit/test_cli_inter_run_state_chaining.py` |
| REQ-YG-268 | --export-state writes full post-run state to explicit JSON path using _serialize_state(); creates parent directories; write failures print clear error and exit 1; CopilotResult.session_id survives round-trip and resolves via resolve_state_expression() | `yamlgraph/cli/graph_commands.py`, `yamlgraph/cli/helpers.py`, `yamlgraph/storage/export.py`, `tests/unit/test_cli_inter_run_state_chaining.py` |

### 121. Async Race Node with Cancellable Candidates

Rewrites the race node from ThreadPoolExecutor to asyncio so losing candidates are cooperatively cancelled at await points after a winner is found. Eliminates orphan HTTP connections, loser billing, and interpreter-exit delays from post-win background threads. _run_coro_sync_safe bridges sync node_fn to the async core without event-loop conflicts under both invoke and ainvoke execution paths.

**Feature Request:** FR-271

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-270 | Race node rewired to asyncio: ThreadPoolExecutor removed; _invoke_candidate_async uses await llm.ainvoke(messages); _race_async uses asyncio.wait(FIRST_COMPLETED) to cancel losers after winner; _run_coro_sync_safe bridges sync node_fn to async core without event-loop conflicts; loser asyncio.Task objects cancelled and gathered before node_fn returns; deadline computed once and decremented across wait iterations; on_error: skip preserved; AllCandidatesFailedError raised when all candidates fail without skip | `yamlgraph/node_factory/race_node.py`, `tests/unit/test_race_node.py` |

### 122. Router Node with Candidates Race Support

Extends the router node type to accept an optional `candidates:` list (identical schema to `race`), racing them for the routing decision and cancelling losers via asyncio cooperative cancellation. Routing semantics (route_field, routes, default_route) are unchanged. Eliminates the need for a manual race+python+conditional-edges workaround for low-latency classification on the critical path. Single-provider routers are unaffected.

**Feature Request:** FR-272

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-271 | Router node accepts optional candidates: list (≥2 {provider, model} dicts) for race-based routing: fires prompt concurrently, first-valid result used for routing resolution via _resolve_route; losers cancelled via asyncio.Task.cancel(); timeout: managed by _race_async (no outer _maybe_wrap_timeout); provider: + candidates: mutually exclusive (compile error); on_error: skip rejected at compile time; timeout/all-fail with on_error: fail raises AllCandidatesFailedError, with on_error: fallback/unset routes via default_route + records error; _race_winner metadata set in state; missing route_field in winner falls to default_route (no disqualification); single-provider routers unchanged | `yamlgraph/node_factory/llm_nodes.py`, `yamlgraph/utils/validators.py`, `yamlgraph/models/state_builder.py`, `yamlgraph/node_compiler.py`, `tests/unit/test_router_race.py` |

### 124. Watcher2 PR Reuse (FR-275)

Enhanced create_pr.sh checks for existing PRs before creating new ones, reuses existing PRs to prevent automation failures and manual intervention.

**Feature Request:** FR-275

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-272 | create_pr.sh checks for existing open PRs on $WT_BRANCH using gh pr list --state open --head "$WT_BRANCH" --json number,url,title --jq ".[0] \| select(.number != null)"; if existing PR found, reuses PR number and URL instead of creating new; if no existing PR found, creates new PR as before; sets PR_NUMBER and PR_URL variables correctly in both cases; logs clearly whether reusing or creating; handles network failures gracefully by falling back to creation; updates PR title when different from requested title | `.chaplain/lib/watcher/create_pr.sh`, `tests/unit/test_watcher2_create_pr_reuse.py` |

### 125. Pipeline Script Retirement (FR-276)

Retire obsolete pipeline scripts (watch.sh, enforce_worktree.sh, bugfix_worktree.sh) in favor of the FSM runtime entrypoint start-system.sh as sole orchestrator. Implement forensic failure preservation by keeping failed worktrees and topics for investigation rather than destroying evidence.

**Feature Request:** FR-276

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-276 | All three obsolete scripts (.chaplain/watch.sh, scripts/enforce_worktree.sh, scripts/bugfix_worktree.sh) are deleted from the filesystem; any documentation references to them are updated to point to `.chaplain/scripts/start-system.sh`; start-system.sh is documented as the single entry point; failure paths preserve worktree and topic file in .chaplain/failed/ for forensic inspection; success paths clean up normally (teardown worktree, delete topic); worktree_setup.sh calls git worktree prune to clean orphaned metadata before branch creation; no functional regression (FSM runtime covers all capabilities of old scripts) | `.chaplain/scripts/start-system.sh`, `.chaplain/config/watcher-dispatcher.yaml`, `.chaplain/config/watcher-pipeline-v2.yaml`, `.chaplain/lib/watcher/worktree_setup.sh`, `CLAUDE.md`, `README.md` |

### 126. Test Speed Optimization

Pytest markers and configurable timing to enable faster development cycles. Adds 'slow' marker for tests >1s, configurable TEST_DELAY_SCALE for accelerated timing, and developer commands for selective test execution during rapid iteration.

**Feature Request:** FR-275

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-275 | pytest slow marker infrastructure enables selective test execution. 'slow' marker defined in pyproject.toml for tests taking >1 second; tests using sleep >1s marked with @pytest.mark.slow; pytest -m "not slow" excludes slow tests for fast iteration; pytest -m "slow" runs only slow tests for full validation; CHAOS_DELAY and test timing configurable via TEST_DELAY_SCALE environment variable; development commands documented in CLAUDE.md for ultra-fast, fast, and slow-only execution; test behavior unchanged when no marker filters applied; comprehensive acceptance tests validate marker functionality | `pyproject.toml`, `tests/chaos_tools.py`, `tests/unit/test_map_node_timeout.py`, `tests/unit/test_race_node.py`, `tests/unit/test_fr275_test_speed_optimization.py`, `CLAUDE.md` |

### 127. CI Hardening Consolidation

Consolidate and harden CI/CD workflows with performance optimizations, security improvements, and resource management across all GitHub Actions workflows.

**Feature Request:** FR-196

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-277 | CI hardening consolidation: all workflows have concurrency groups with cancel-in-progress; all setup-python steps include cache: pip; main workflow renamed to "CI"; tag pushes validate version against pyproject.toml; pip-audit has retry mechanism (3 attempts, 30s intervals); test matrix includes Python 3.11 and 3.12; existing job dependencies and triggers preserved; security scan still blocks on vulnerabilities; release process unchanged. | `.github/workflows/workflow.yml`, `.github/workflows/security.yml`, `.github/workflows/commitlint.yml`, `tests/unit/test_ci_hardening_consolidation.py` |

### 128. Chaplain Documentation

Comprehensive documentation for the FSM runtime orchestrator and shell library in .chaplain/README.md covering architecture, usage, and troubleshooting.

**Feature Request:** FR-195

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-278 | `.chaplain/README.md` exists with comprehensive documentation covering: runtime architecture anchored on `.chaplain/scripts/start-system.sh` with dispatcher/pipeline FSM flow across plan/judge/enforce phases, shell library reference for all tools in `.chaplain/lib/watcher/*.sh` (worktree_setup.sh, worktree_teardown.sh, preflight.sh, create_pr.sh, merge_pr.sh, wait_ci.sh, post_merge.sh, inbox_sync.sh, metrics.sh), usage examples for daemon and individual tools, environment variables and configuration, troubleshooting section, architecture details, and cross-references to related files (FR-273, etc.) | `.chaplain/README.md`, `tests/unit/test_chaplain_readme_documentation` |

### 130. Watcher2 Finalize Pre-commit Optimization

Optimize watcher2 finalize step to reduce copilot session invocations by pre-formatting code before pre-commit loops and increasing retry attempts from 3 to 5.

**Feature Request:** FR-198

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-286 | Watcher2 finalize section runs ruff check --fix and ruff format on yamlgraph/ and tests/ directories before entering the pre-commit loop; loop allows 5 attempts (was 3); failure message shows "5 attempts"; git add -A stages files before and after ruff commands; prevents copilot fallback for auto-fixable cascading issues | `.chaplain/scripts/start-system.sh`, `tests/unit/test_fr198_watcher2_finalize_optimization.py` |

### 131. Anthropic Prompt Caching Support

YAML system_segments field with per-segment cache control for token cost optimization. Enables Anthropic prompt caching to reduce costs by 3x for stable context prefixes.

**Feature Request:** FR-219

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-287 | System segments schema validation and parsing | `yamlgraph/utils/prompts.py` |
| REQ-YG-288 | Backward compatibility with scalar system prompts | `yamlgraph/executor_base.py` |
| REQ-YG-289 | Anthropic cache_control injection for cached segments | `yamlgraph/executor_base.py` |
| REQ-YG-290 | Non-Anthropic segment flattening gracefully ignores cache flags | `yamlgraph/executor_base.py` |
| REQ-YG-291 | Async/streaming executor consistency with segments | `yamlgraph/executor_async.py` |
| REQ-YG-292 | Error handling for conflicting system and system_segments fields | `yamlgraph/utils/prompts.py` |
| REQ-YG-293 | Variable substitution and Jinja2 support in segments | `yamlgraph/utils/prompts.py` |
| REQ-YG-302 | Demo structure and files exist in proper format | `examples/demos/prompt-caching/` |
| REQ-YG-303 | Demo graph configuration uses Anthropic provider correctly | `examples/demos/prompt-caching/graph.yaml` |
| REQ-YG-304 | Demo prompts use identical cached system segments | `examples/demos/prompt-caching/prompts/` |
| REQ-YG-305 | Documentation updates explain caching benefits | `reference/prompt-yaml.md`, `examples/demos/prompt-caching/README.md` |
| REQ-YG-306 | Demo execution proof shows realistic output | `examples/demos/prompt-caching/demo-output.log` |

### 132. Watcher2 CI Resilience

Fix wait_ci.sh check ordering and CI resilience patterns for the watcher pipeline. v1 CI remediation artifacts (step-ci-remediate, enforce-ci-remediate) retired by FR-305; v2 handles CI fixes inside enforce_session.

**Feature Request:** FR-279

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-294 | Wait logic checks IN_PROGRESS before FAILURE to avoid premature CI failure | `.chaplain/lib/watcher/wait_ci.sh` |
| REQ-YG-298 | Maximum 2 remediation attempts before escalating to human | `.chaplain/config/watcher-pipeline-v2.yaml` |
| REQ-YG-299 | Remediation covers syntax errors, missing changelog/diary fragments | `.chaplain/graphs/watcher-enforce/enforce-session.yaml` |
| REQ-YG-300 | Existing passing pipelines unaffected by CI resilience changes | `.chaplain/config/watcher-pipeline-v2.yaml` |
| REQ-YG-301 | Test coverage for wait_ci.sh ordering and CI remediation loop | `tests/unit/test_fr279_watcher2_ci_resilience.py` |

### 133. Watcher2 CI Remediation Crash Fix

Fix three bugs in the watcher2 CI remediation loop that cause immediate script crash: missing run ID in gh run view, relative path resolution after cd, and missing error guard.

**Feature Request:** FR-284

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-307 | gh run view --log-failed uses proper run ID from gh run list | `.chaplain/scripts/start-system.sh` |

### 134. Watcher2 Changelog Auto-Generation

Auto-generate changelog fragments in watcher2 pipeline to eliminate manual intervention. Defense-in-depth approach with shell generation, prompt instructions, finalize verification, and CI remediation context. Extracts FR number, derives scope/type, looks up REQ-YG-XXX from capabilities registry, and prevents cross-wiring.

**Feature Request:** FR-283

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-308 | Auto-generate changelog fragments in watcher2 pipeline between critique and finalize steps. Extract FR number from FR_PATH, generate filename with 40-char descriptive suffix, derive type/scope from path, lookup REQ-YG-XXX from capability registry, validate FR number to prevent cross-wiring, create YAML frontmatter and fragment content automatically. | `.chaplain/scripts/start-system.sh (lines 309-341)`, `tests/unit/test_fr283_watcher2_changelog_auto_generation.py` |

### 135. Watcher2 Forensic Failure Diary

Automated forensic analysis for watcher2 failures with structured diary generation. When handle_failure is called, automatically capture failure context (reason, topic content, logs, worktree state), perform LLM-driven root cause analysis, and generate structured diary entries with evidence and recommendations for institutional learning.

**Feature Request:** FR-285

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-309 | Forensic failure analysis shall be automatically invoked on watcher2 handle_failure and generate structured diary entries containing root cause analysis, evidence sources, and prevention recommendations using LLM-driven investigation of failure context, logs, and worktree state | `.chaplain/scripts/start-system.sh (lines 56-89, 98)`, `.chaplain/lib/diary.py (lines 44-67, 100-123)`, `.chaplain/graphs/watcher-forensic/graph.yaml`, `tests/unit/test_fr285_watcher2_forensic_failure_diary.py` |

### 136. Per-Graph Typed MCP Tools

Derive per-graph typed MCP tool definitions from graph YAML metadata (name, description, state) so each graph appears as its own named tool with a typed JSON Schema. Shared schema derivation in discovery.py.

**Feature Request:** FR-291

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-310 | Input/output var separation: discovery excludes state_key targets from input_vars, exposing only user-supplied inputs. | `yamlgraph/discovery.py`, `tests/unit/test_mcp_typed_tools.py` |
| REQ-YG-311 | JSON Schema derivation from state type annotations. Maps str->string, int->integer, float->number, bool->boolean, list->array, dict->object. Parameterized types map to base type. Unknown types fall back to string. | `yamlgraph/discovery.py`, `tests/unit/test_mcp_typed_tools.py` |
| REQ-YG-312 | Per-graph MCP tool registration: each discovered graph registers as its own named MCP tool with typed inputSchema derived from input_vars. | `yamlgraph/mcp_server.py`, `tests/unit/test_mcp_typed_tools.py` |
| REQ-YG-313 | Tool name normalization: graph name hyphens replaced with underscores to produce valid MCP tool names. | `yamlgraph/discovery.py`, `tests/unit/test_mcp_typed_tools.py` |
| REQ-YG-314 | Name collision detection: duplicate tool_name values across discovered graphs raise ValueError at server startup. | `yamlgraph/mcp_server.py`, `tests/unit/test_mcp_typed_tools.py` |

### 137. Watcher FSM System Startup Script

Single startup script for the full watcher FSM system. Starts UI (creates event socket), generates diagrams, launches dispatcher with correct --initial-context in proper sequence. Signal-based cleanup kills all child processes. --inbox DIR overrides inbox directory.

**Feature Request:** FR-296

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-315 | Watcher FSM system startup script: single script starts UI (event socket), generates diagrams, and launches dispatcher with correct --initial-context in proper sequence; cleanup on SIGINT/SIGTERM kills all child processes by PID with pkill fallback; --inbox DIR overrides inbox directory | `.chaplain/scripts/start-system.sh` |

### 138. Watcher Pipeline FSM Simplification

Simplified watcher pipeline v2: 6 operational states (setup, plan, commit_plan, judge, enforce_session, done) + 3 terminals (completed, failed, stopped). Judge uses different model from plan with fresh session. Enforce resumes plan session. Dispatcher flag-gated via pipeline_version.

**Feature Request:** FR-305

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-316 | Simplified watcher pipeline v2 FSM: 6 operational states (setup, plan, commit_plan, judge, enforce_session, done) + 3 terminals (completed, failed, stopped). Judge uses different model from plan with fresh session (no resume). Enforce resumes plan session for full context continuity. Dispatcher flag-gated via pipeline_version context key. | `.chaplain/config/watcher-pipeline-v2.yaml`, `.chaplain/graphs/watcher-plan/step-judge-v2.yaml`, `.chaplain/graphs/watcher-enforce/enforce-session.yaml`, `tests/unit/test_fr305_watcher_pipeline_v2.py` |

### 139. Root README Accuracy Contract

Root README claims stay aligned with implemented provider support and include explicit review freshness metadata via a dedicated unit contract test.

**Feature Request:** FR-313

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-317 | Root `README.md` includes all currently supported provider identifiers (`anthropic`, `azure`, `deepseek`, `google`, `inception`, `lmstudio`, `mistral`, `openai`, `replicate`, `vertex`, `xai`) in provider documentation, contains no hardcoded `all <number> reference docs` wording, and ends with `Last reviewed: 2026-05-03`; contract enforced by `tests/unit/test_root_readme_accuracy.py` (FR-313). | `README.md`, `tests/unit/test_root_readme_accuracy.py` |

### 140. Watcher2 Validate Split Fix/Gate

Split watcher2 post-enforce validation into deterministic micro-remediation fast path (micro_changelog + micro_title), explicit LLM remediation fallback (validate_fix), and deterministic CI-parity gate (validate_gate) with bounded retry semantics before done.

**Feature Request:** FR-316

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-318 | Watcher2 pipeline routes post-enforce flow through deterministic micro_changelog then micro_title then sanity_check then validate_gate; validate_gate performs deterministic pre-commit, commit-title, branch-freshness, and diary-in-diff checks with max-attempt retry contract (pass → done, fix_needed → validate_fix, error → failed). micro-step errors fall back to validate_fix. Both done and validate_gate diary-parity trigger use a shared primary PR title selector: first feat/fix in `origin/main..HEAD`, else first non-docs/non-chore, else first subject. | `.chaplain/config/watcher-pipeline-v2.yaml`, `.chaplain/actions/changelog_gen_action.py`, `.chaplain/actions/validate_gate_action.py`, `.chaplain/lib/watcher/select_primary_pr_title.sh`, `.chaplain/graphs/watcher-enforce/prompts/validate-session.yaml`, `tests/unit/test_fr316_watcher2_validate_split_fix_gate.py`, `tests/unit/test_fr412_watcher2_micro_remediation_fast_path.py`, `tests/unit/test_fr358_watcher2_primary_pr_title_selection.py` |

### 141. Shared FSM Bridge Module

Extract canonical fire-and-forget FSM↔YAMLGraph bridge behavior into `yamlgraph.utils.fsm` and make fsm-router consume it via a thin wrapper.

**Feature Request:** FR-346

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-319 | FSM bridge shared module: `yamlgraph.utils.fsm` package with `YamlgraphAsyncAction`, `extract_event`, `json_safe`, `resolve_context_ref` exported from `yamlgraph.utils.fsm`; fire-and-forget guard semantics; AF_UNIX DGRAM event dispatch; interrupt/event_map/route/success resolution cascade. | `yamlgraph/utils/fsm/__init__.py`, `yamlgraph/utils/fsm/helpers.py`, `yamlgraph/utils/fsm/event_sender.py`, `yamlgraph/utils/fsm/graph_runner.py`, `yamlgraph/utils/fsm/action.py`, `examples/fsm-router/actions/yamlgraph_async_action.py`, `tests/unit/test_fsm_bridge_shared.py` |

### 142. Skill Export Portable Packaging

Add `yamlgraph skill export` to package existing graphs into portable Skills bundles with deterministic filesystem artifacts for skill discovery.

**Feature Request:** FR-348

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-320 | CLI parser registers `yamlgraph skill export` with `--format` and `--output-dir` options and dispatches to skill command handlers. | `yamlgraph/cli/__init__.py`, `yamlgraph/cli/skill_commands.py`, `tests/unit/test_fr348_skill_export_red.py` |
| REQ-YG-321 | Export generates required package artifacts: `SKILL.md`, executable `scripts/run.sh`, `references/`, and `assets/schema.json`. | `yamlgraph/skill_export.py`, `yamlgraph/skill_export_writer.py`, `tests/unit/test_fr348_skill_export_red.py` |
| REQ-YG-322 | `SKILL.md` includes skill metadata, typed input/output sections, and runnable CLI invocation example. | `yamlgraph/skill_export.py`, `yamlgraph/skill_export_writer.py`, `tests/unit/test_fr348_skill_export_red.py` |
| REQ-YG-323 | `assets/schema.json` contains top-level `input` and `output` schema objects derived from graph input vars and output state keys. | `yamlgraph/skill_export.py`, `yamlgraph/skill_export_writer.py`, `tests/unit/test_fr348_skill_export_red.py` |
| REQ-YG-324 | Format variants map to expected paths for `skill-md`, `copilot`, and `cursor` package layouts. | `yamlgraph/skill_export.py`, `yamlgraph/skill_export_writer.py`, `tests/unit/test_fr348_skill_export_red.py` |
| REQ-YG-325 | Export is deterministic and non-LLM with explicit errors for invalid graph input, unsupported format, and target collisions. | `yamlgraph/skill_export.py`, `yamlgraph/skill_export_writer.py`, `yamlgraph/cli/skill_commands.py`, `tests/unit/test_fr348_skill_export_red.py` |
| REQ-YG-326 | CLI/reference docs include `yamlgraph skill export` usage and output layout examples for all format variants. | `reference/cli.md`, `reference/skills-export.md`, `reference/README.md`, `tests/unit/test_fr348_skill_export_red.py` |

### 143. Agent Export Tool-Scoped Personas

Add `agent-md` export format to generate GitHub Copilot `.agent.md` files with YAMLGraph MCP tool scoping from graph metadata.

**Feature Request:** FR-350

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-327 | CLI parser accepts `--format agent-md` for `yamlgraph skill export` and dispatches through existing skill command handlers. | `yamlgraph/cli/__init__.py`, `yamlgraph/cli/skill_commands.py`, `tests/unit/test_fr350_agent_export_red.py` |
| REQ-YG-328 | `agent-md` export writes a single file at `<output-dir>/.github/agents/<skill-name>.agent.md`. | `yamlgraph/skill_export.py`, `yamlgraph/skill_export_writer.py`, `tests/unit/test_fr350_agent_export_red.py` |
| REQ-YG-329 | Generated `.agent.md` frontmatter includes non-empty `description`, `tools: [yamlgraph/*]`, and `model: Claude Sonnet 4`. | `yamlgraph/skill_export.py`, `yamlgraph/skill_export_writer.py`, `tests/unit/test_fr350_agent_export_red.py` |
| REQ-YG-330 | Generated `.agent.md` body includes agent heading, inputs derived from graph schema, and `@agent-name` invocation guidance. | `yamlgraph/skill_export.py`, `yamlgraph/skill_export_writer.py`, `tests/unit/test_fr350_agent_export_red.py` |
| REQ-YG-331 | Export remains deterministic and non-LLM with explicit failures for invalid graph path, unsupported format, and output file collisions. | `yamlgraph/skill_export.py`, `yamlgraph/skill_export_writer.py`, `yamlgraph/cli/skill_commands.py`, `tests/unit/test_fr350_agent_export_red.py` |
| REQ-YG-332 | CLI/reference docs include `agent-md` usage and output layout examples. | `reference/cli.md`, `reference/skills-export.md`, `reference/README.md`, `tests/unit/test_fr350_agent_export_red.py` |

### 145. Copilot Instrumentation Gap Closure

Close FR-362 follow-up instrumentation gaps by hardening runner flags and env, adding before/after git snapshots, and extracting semantic process-mining events with deterministic conformance output.

**Feature Request:** FR-364

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-340 | `scripts/copilot_instrument.sh` includes `--output-format json`, `--log-dir`, and `--log-level debug` in both plan and resumed implement invocations. | `scripts/copilot_instrument.sh`, `tests/unit/test_fr364_copilot_instrumentation_gap_closure_red.py` |
| REQ-YG-341 | Runner exports `COPILOT_OTEL_EXPORTER_TYPE=file`, `COPILOT_OTEL_FILE_EXPORTER_PATH`, and `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true` for each phase. | `scripts/copilot_instrument.sh`, `tests/unit/test_fr364_copilot_instrumentation_gap_closure_red.py` |
| REQ-YG-342 | Runner captures explicit per-phase git snapshots: `git-status-before.txt`, `git-diff-before.patch`, `git-status-after.txt`, and `git-diff-after.patch`. | `scripts/copilot_instrument.sh`, `tests/unit/test_fr364_copilot_instrumentation_gap_closure_red.py` |
| REQ-YG-343 | Extracted event schema includes `source`, `success`, and `details` in all emitted JSONL events. | `scripts/extract_copilot_events.py`, `scripts/extract_copilot_events_lib.py`, `tests/unit/test_fr364_copilot_instrumentation_gap_closure_red.py` |
| REQ-YG-344 | Extractor emits semantic events (`phase_marker`, `test_run`, `lint_run`, `file_create`, `file_edit`, `failure`, `retry`) from observable tool-call telemetry patterns. | `scripts/extract_copilot_events.py`, `scripts/extract_copilot_events_lib.py`, `tests/unit/test_fr364_copilot_instrumentation_gap_closure_red.py` |
| REQ-YG-345 | Extractor supports deterministic conformance table output via `--conformance-table`. | `scripts/extract_copilot_events.py`, `scripts/extract_copilot_events_lib.py`, `tests/unit/test_fr364_copilot_instrumentation_gap_closure_red.py` |
| REQ-YG-346 | Instrumentation documentation separates raw telemetry artifacts from normalized semantic events. | `docs/copilot-instrumentation-poc.md`, `tests/unit/test_fr364_copilot_instrumentation_gap_closure_red.py` |

### 146. FSM Snapshot Hooks Phase 2 Subclassing

Add a typed snapshot boundary and lifecycle hook callbacks to the shared FSM bridge so domains can subclass behavior without forking dispatch flow.

**Feature Request:** FR-369

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-347 | Shared FSM bridge exposes typed snapshot params (`SnapshotParams` + `snapshot_params`) and lifecycle hooks (`pre_snapshot`, `pre_dispatch`, `on_success`, `on_error`) wired through `YamlgraphAsyncAction.execute()` and `run_and_dispatch()` with dispatch suppression support. | `yamlgraph/utils/fsm/snapshot.py`, `yamlgraph/utils/fsm/action.py`, `yamlgraph/utils/fsm/graph_runner.py`, `yamlgraph/utils/fsm/__init__.py`, `tests/unit/test_fr369_fsm_snapshot_hooks_red.py` |

### 147. Graph Run JSON Stdout + TypeScript Node Integration

Add machine-readable JSON stdout mode for `yamlgraph graph run` and a minimal Node.js/TypeScript subprocess demo using `child_process.execFile`.

**Feature Request:** FR-375

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-348 | CLI parser accepts `yamlgraph graph run --json` and defaults the flag to `False` when omitted. | `yamlgraph/cli/__init__.py`, `tests/unit/test_fr375_graph_run_json_stdout_red.py` |
| REQ-YG-349 | On success with `--json`, stdout contains only valid final-state JSON without human-oriented run/result headers or summaries. | `yamlgraph/cli/graph_commands.py`, `tests/unit/test_fr375_graph_run_json_stdout_red.py` |
| REQ-YG-350 | On failure with `--json`, stdout remains empty, error details are written to stderr, and process exits non-zero. | `yamlgraph/cli/graph_commands.py`, `yamlgraph/cli/helpers.py`, `tests/unit/test_fr375_graph_run_json_stdout_red.py` |
| REQ-YG-351 | `--json` mode is non-interactive: if execution returns `__interrupt__`, the command fails fast with non-zero exit and does not prompt for input. | `yamlgraph/cli/graph_commands.py`, `tests/unit/test_fr375_graph_run_json_stdout_red.py` |
| REQ-YG-352 | JSON mode emits full final state without display truncation and reuses existing `_serialize_state()` serialization semantics. | `yamlgraph/cli/graph_commands.py`, `yamlgraph/storage/export.py`, `tests/unit/test_fr375_graph_run_json_stdout_red.py` |
| REQ-YG-353 | JSON mode preserves run input/merge behavior for `--var`, `--var-file`, and `--import-state`, and remains compatible with `--export-state`. | `yamlgraph/cli/graph_commands.py`, `yamlgraph/cli/helpers.py`, `tests/unit/test_fr375_graph_run_json_stdout_red.py` |
| REQ-YG-354 | `examples/demos/typescript-node/` includes runnable Node.js/TypeScript assets where `src/index.ts` uses `execFile` to call `yamlgraph graph run ... --json` and parse stdout JSON. | `examples/demos/typescript-node/`, `tests/unit/test_fr375_typescript_node_demo_red.py` |
| REQ-YG-355 | CLI/examples docs describe `--json` usage and guidance for when to use subprocess JSON mode versus MCP/A2A integration patterns. | `reference/cli.md`, `examples/README.md`, `tests/unit/test_fr375_typescript_node_demo_red.py` |

### 148. CI Co-authored-by Trailer Gate

GitHub Actions job in commitlint.yml that blocks pull requests when any `Co-authored-by:` trailer identities are present in PR commit messages or PR body text.

**Feature Request:** FR-385

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-358 | `copilot-trailer-gate` job in `commitlint.yml` deterministically scans `BASE_SHA..HEAD_SHA` commit messages and `github.event.pull_request.body` for any `Co-authored-by:` trailer line, fails with exit 1 on detection, and passes unchanged PRs otherwise. | `.github/workflows/commitlint.yml`, `tests/unit/test_fr385_ci_copilot_trailer_gate_red.py`, `CLAUDE.md` |

### 149. Prompt Theme Analyzer Demo (CAP-149)

Demo graph showing list -> map -> deterministic aggregate -> llm-group -> write flow for prompt theme analysis with explicit boundary normalization.

**Feature Request:** FR-402

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-359 | YAMLGraph includes `examples/demos/prompt_theme_analyzer/` with a five-node pipeline (`list_prompts -> classify_themes(map) -> aggregate_themes(python) -> group_themes(llm) -> write_report`) where `source_dir` is required, prompt text is truncated at the Python boundary, grouping consumes deterministic aggregated theme counts, and the demo ships with tests, capability traceability, diary reflection, and execution proof via `demo-output.log`. | `examples/demos/prompt_theme_analyzer/graph.yaml`, `examples/demos/prompt_theme_analyzer/tools.py`, `examples/demos/prompt_theme_analyzer/prompts/group_themes.yaml`, `tests/unit/test_fr402_prompt_theme_analyzer_red.py`, `docs/diary/2026-05-16-reflection-fr-402-prompt-theme-analyzer-demo.md` |

### 150. Philosopher's Book Demo

Demo pipeline generating one chapter at a time of a philosophical work on cognitive traps. Plan → write a single chapter using Copilot with diary search tools. Run with --var chapter_num=N. (FR-404)

**Feature Request:** FR-404

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-404 | YAMLGraph includes `examples/demos/philosopher_book/` with a four-node pipeline (load_trap -> plan_chapter(copilot) -> write_chapter(copilot) -> save_chapter) where load_trap loads a single trap by chapter_num, search_diary searches docs/diary/ using case-insensitive substring matching, read_file validates allowed path prefixes and truncates at 8000 chars, and save_chapter writes to output_dir/chapters/. | `examples/demos/philosopher_book/graph.yaml`, `examples/demos/philosopher_book/tools.py`, `tests/unit/test_philosopher_book.py`, `docs/diary/2026-05-16-fr404-philosopher-book.md` |
| REQ-YG-405 | YAMLGraph includes a separate philosopher-book editorial graph that snapshots repo-contained chapter inputs, builds a token-bounded global editorial brief, edits chapters through a type: map LLM pass, writes edited markdown to a separate repo-contained output folder with original filenames preserved, and writes an editorial report with word-count deltas and editorial notes. | `examples/demos/philosopher_book/editorial_graph.yaml`, `examples/demos/philosopher_book/tools.py`, `examples/demos/philosopher_book/prompts/editorial_brief.yaml`, `examples/demos/philosopher_book/prompts/edit_chapter.yaml`, `tests/unit/test_philosopher_book.py`, `docs/diary/2026-05-17-fr405-philosopher-book-editorial-graph.md` |

### 151. Graph Lint JSON Output

Add machine-readable NDJSON output mode for `yamlgraph graph lint` while preserving default human output and existing lint exit-code semantics.

**Feature Request:** FR-406

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-406 | CLI parser accepts `yamlgraph graph lint --json` (default false), JSON mode emits one `LintResult` JSON object per linted file to stdout (NDJSON), routes diagnostics/errors to stderr, and preserves existing lint exit semantics (non-zero when lint errors occur, zero for warnings-only/clean runs). | `yamlgraph/cli/__init__.py`, `yamlgraph/cli/graph_validate.py`, `tests/unit/test_fr406_lint_json_output_red.py` |

### 152. Watcher2 Dispatcher Audit Cadence

Reintegrates inquisitor cadence into watcher-dispatcher so no-topic cycles can trigger `.chaplain/inquisitor.sh --propose` at most once per 24 hours while preserving topic-first routing. (FR-411)

**Feature Request:** FR-411

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-407 | Watcher2 dispatcher includes an `auditing` state and `last_audit_ts` context key; syncing_inbox emits `audit_needed` only when no topic is available and 24h cadence elapsed; audit runs `.chaplain/inquisitor.sh --propose`, updates `last_audit_ts` on success, and routes failures back to idle without stopping the daemon. | `.chaplain/config/watcher-dispatcher.yaml`, `.chaplain/actions/syncing_inbox_action.py`, `.chaplain/actions/audit_action.py`, `tests/unit/test_fr411_watcher2_dispatcher_inquisitor_audit_cadence.py` |

### 153. Built-in Questionnaire Gap Utilities

Adds framework-shipped questionnaire helpers `detect_gaps` and `normalize_extracted` in `yamlgraph.tools.questionnaire` so schema-driven probing loops can reuse deterministic gap detection and extraction normalization through existing `type: python` tool wiring. (FR-421)

**Feature Request:** FR-421

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-409 | `detect_gaps(state)` returns sorted required schema field IDs missing from `state["extracted"]`, treating `None` and empty string as missing and returning `{"gaps": [...], "has_gaps": bool}`. | `yamlgraph/tools/questionnaire.py`, `tests/unit/test_fr421_questionnaire_gap_utilities_red.py` |
| REQ-YG-410 | `normalize_extracted(state)` returns `{}` when `state["extracted"]` is a dict, otherwise returns `{"extracted": {}}`; utility module remains callable via `type: python` tool config. | `yamlgraph/tools/questionnaire.py`, `yamlgraph/tools/python_tool.py`, `tests/unit/test_fr421_questionnaire_gap_utilities_red.py` |

### 154. WIP Commit Subject Gate

Adds deterministic local and CI commit-subject enforcement that blocks the standalone word `wip` (case-insensitive) on the protected main merge path. Local commit-msg checks apply only on branch `main`, while CI scans PR commit subjects in `BASE_SHA..HEAD_SHA`. (FR-424)

**Feature Request:** FR-424

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-419 | Commit subject gate blocks standalone `wip` (case-insensitive) on local `main` commit-msg flow and in CI `wip-gate` pull-request commit ranges (`BASE_SHA..HEAD_SHA`) via deterministic subject scanning, while allowing non-main branches and non-boundary substrings like `swipe`. | `.pre-commit-config.yaml`, `.github/workflows/commitlint.yml`, `tests/unit/test_fr424_wip_main_gate_red.py`, `CLAUDE.md` |

<!-- END GENERATED CAPABILITIES -->

### 75. Portable Chaplain (FR-196)

Path-based Python tool loading and Chaplain subsystem portability.

**Feature Request:** FR-196

| REQ-YG-196 | PythonToolConfig supports path field (mutually exclusive with module) for file-path-based Python tool loading via spec_from_file_location; path resolves relative to CWD; validation rejects both-set and neither-set; parse_python_tools accepts path or module in YAML tool definitions | `yamlgraph/tools/python_tool.py`, `tests/unit/test_python_nodes.py` |

---

### 76. Horoscope Demo (FR-201)

Parallel daily horoscope generator using map node with static over: list.

| REQ-YG-197 | Map node fans out over 12 zodiac signs in parallel, collects readings, assembles into Markdown document with exports section. Pure YAML graph with co-located prompts, date as runtime variable. | `examples/demos/horoscope`, `tests/integration/test_horoscope_demo.py` |

### 77. Image Generation Pipeline (FR-202)

End-to-end style-driven image generation: concept → subgraph prompt generation → save → Replicate z-image.

| REQ-YG-198 | Image pipeline graph chains generate_concepts (LLM) → batch_image_prompts (subgraph) → save_prompts (Python tool writing prompts.txt) → generate_images (Python tool calling Replicate z-image with sidecar .txt files and best-effort EXIF embedding). | `examples/image_pipeline`, `tests/unit/test_image_pipeline.py` |

### 78. .fi Domain Crawl Demo

Multi-stage pipeline for crawling .fi country-level domains: LLM query planning, DuckDuckGo seed discovery, parallel page crawling via map node, and LLM sitemap summarisation.

| REQ-YG-199 | .fi domain crawl demo: plan node produces search queries (parse_json), discover node filters to .fi TLD, map node crawls pages in parallel (max_items: 10), summarise node produces sitemap overview. crawl_page handles errors gracefully. No new dependencies. | `examples/demos/fi-domain-crawl`, `tests/unit/test_fi_domain_crawl.py` |

| REQ-YG-200 | `demo-gate` CI job in `commitlint.yml` extracts changed demo directories from `git diff` (excluding `demo-output.log` itself), verifies each has a `demo-output.log` in the diff, then validates content semantics with shared rules: reject empty logs, reject fatal execution markers (for example `Node .* failed`, `[ERROR]`, `❌ Error:`, `exit code [1-9]`), and reject logs with no success evidence; exits 1 on violations and 0 when no demos changed; job-level `if` condition restricts to `feat`/`fix` PR titles; uses `actions/checkout@v4` with `fetch-depth: 0`; pre-commit hook `demo-proof-check` calls `scripts/check_demo_proof.sh` with identical semantic rules; `.gitignore` negates `*.log` for `examples/demos/*/demo-output.log`; `CLAUDE.md` documents `demo-gate` in branch protection section; enforcer Phase 2 prompt instructs capturing `demo-output.log` | `scripts/check_demo_proof.sh`, `scripts/demo_log_semantics.sh`, `.github/workflows/commitlint.yml`, `.pre-commit-config.yaml`, `CLAUDE.md`, `tests/unit/test_ci_demo_proof_gate.py` |

### 80. Standalone Scripture Template (FR-207)

Extract governance methodology into standalone template repository (`scripture-dev`).

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

| REQ-YG-218 | `.importlinter` config at repo root declares a `layers` contract with three layers: Presentation (`yamlgraph.cli`), Logic (graph_loader, node_factory, executor, linter, edge_compiler, node_compiler, map_compiler, routing, graph_cache, schema_loader, data_loader, discovery, executor_async, interactive_tool), Side Effects (tools, models, utils, config, constants, storage, contrib, executor_base, error_handlers, verification). `lint-imports` exits 0 on the current codebase. Pre-commit hook and CI step enforce the contract at every commit and PR. (FR-218) | `.importlinter`, `.pre-commit-config.yaml`, `.github/workflows/workflow.yml`, `tests/unit/test_import_linter.py` |

### 86. Ruff Security Rules (FR-222)

Ruff `S` ruleset (flake8-bandit) enabled for automated security linting.

| REQ-YG-222 | Ruff `S` ruleset enabled in `[tool.ruff.lint] select`. All 7 existing violations (S104 ×2, S602, S603, S607 ×2, S701) suppressed with `# noqa` and documented in `docs/confessions.md`. `ruff check --select S yamlgraph/` exits 0. (FR-222) | `pyproject.toml`, `docs/confessions.md`, `tests/unit/test_ruff_security.py` |

### 128. Chaplain Documentation

Comprehensive documentation for the watcher2 pipeline orchestrator and shell library in `.chaplain/README.md` covering architecture, usage, and troubleshooting.

**Feature Request:** FR-195

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-278 | `.chaplain/README.md` exists with comprehensive documentation covering: watcher2 pipeline architecture (4-phase: Plan → Research → Acceptance → Judge → Enforce), shell library reference for all tools in `.chaplain/lib/watcher/*.sh` (worktree_setup.sh, worktree_teardown.sh, preflight.sh, create_pr.sh, merge_pr.sh, wait_ci.sh, post_merge.sh, inbox_sync.sh, metrics.sh), usage examples for daemon and individual tools, environment variables and configuration, troubleshooting section, architecture details, and cross-references to related files (FR-273, etc.) | `.chaplain/README.md`, `tests/unit/test_chaplain_readme_documentation` |
| REQ-YG-287 | System segments schema validation and parsing: YAML prompts support `system_segments` field as list of content/cache objects alongside existing scalar `system` field. Schema validation ensures proper structure and type checking | `yamlgraph/utils/prompts.py` |
| REQ-YG-288 | Backward compatibility with scalar system prompts: Existing `system: "text"` and `system: ["line1", "line2"]` formats continue working unchanged. No breaking changes to existing prompt YAML files | `yamlgraph/executor_base.py` |
| REQ-YG-289 | Anthropic cache_control injection for cached segments: When using Anthropic provider, segments with `cache: true` get `cache_control: {"type": "ephemeral"}` metadata injected into message structure | `yamlgraph/executor_base.py` |
| REQ-YG-290 | Non-Anthropic segment flattening: Non-Anthropic providers (OpenAI, Google, etc.) flatten system_segments into single system message, gracefully ignoring cache flags without error | `yamlgraph/executor_base.py` |
| REQ-YG-291 | Async/streaming executor consistency: Async executor paths (`prepare_messages_async`, streaming) handle system_segments identically to sync paths with same cache behavior | `yamlgraph/executor_async.py` |
| REQ-YG-292 | Error handling for conflicting system fields: Using both `system` and `system_segments` in same prompt raises clear validation error. Empty system_segments list raises validation error | `yamlgraph/utils/prompts.py` |
| REQ-YG-293 | Variable substitution and Jinja2 support in segments: Both simple `{var}` and Jinja2 `{{ var }}` template syntax work within segment content strings, same as scalar system prompts | `yamlgraph/utils/prompts.py` |
| REQ-YG-302 | Demo structure and files exist: Prompt caching demo has complete structure with graph.yaml, prompts/ directory, README.md, and demo-output.log files in proper format | `examples/demos/prompt-caching/` |
| REQ-YG-303 | Demo graph configuration: Demo graph uses Anthropic provider correctly with two LLM nodes following cache optimization pattern | `examples/demos/prompt-caching/graph.yaml` |
| REQ-YG-304 | Demo prompts use identical cached system segments: analyze.yaml and reflect.yaml contain identical cached system_segments with cache: true for cost optimization | `examples/demos/prompt-caching/prompts/` |
| REQ-YG-305 | Documentation updates explain caching benefits: README and reference documentation explain token cost reduction, cache behavior, and usage patterns | `reference/prompt-yaml.md`, `examples/demos/prompt-caching/README.md` |
| REQ-YG-306 | Demo execution proof shows realistic output: demo-output.log contains complete execution trace showing Anthropic API calls and cache effectiveness | `examples/demos/prompt-caching/demo-output.log` |
| REQ-YG-307 | gh run view --log-failed uses proper run ID from gh run list | `.chaplain/scripts/start-system.sh` |
| REQ-YG-308 | Auto-generate changelog fragments in watcher2 pipeline between critique and finalize steps. Extract FR number from FR_PATH, generate filename with 40-char descriptive suffix, derive type/scope from path, lookup REQ-YG-XXX from capability registry, validate FR number to prevent cross-wiring, create YAML frontmatter and fragment content automatically | `.chaplain/scripts/start-system.sh` |
| REQ-YG-309 | Forensic failure analysis shall be automatically invoked on watcher2 handle_failure and generate structured diary entries containing root cause analysis, evidence sources, and prevention recommendations using LLM-driven investigation of failure context, logs, and worktree state | `.chaplain/scripts/start-system.sh`, `.chaplain/lib/diary.py`, `.chaplain/graphs/watcher-forensic/` |
| REQ-YG-294 | Wait logic checks IN_PROGRESS before FAILURE to avoid premature CI failure: wait_ci.sh evaluates IN_PROGRESS status before FAILURE to prevent early termination when slow tests are still running | `.chaplain/lib/watcher/wait_ci.sh` |

| REQ-YG-298 | Maximum 2 remediation attempts before escalating to human: CI remediation loop has hard limit to prevent infinite fix attempts and ensure human oversight for complex failures | `.chaplain/scripts/start-system.sh` |
| REQ-YG-299 | Remediation covers syntax errors, missing changelog/diary fragments: Automated fixes handle IndentationError, missing files, and mechanical pre-commit failures but exclude logic errors and security issues | `.chaplain/graphs/watcher-enforce/prompts/enforce-ci-remediate.yaml` |
| REQ-YG-300 | Existing passing pipelines unaffected (backwards compatibility): CI remediation only triggers on actual CI failure; successful pipelines skip remediation entirely with no behavioral changes | `.chaplain/scripts/start-system.sh` |
| REQ-YG-301 | Test coverage for wait_ci.sh ordering and CI remediation loop: Comprehensive test suite validates check ordering fix and remediation loop functionality with stateful mocks | `tests/unit/test_fr279_watcher2_ci_resilience.py` |
| REQ-YG-310 | Input/output var separation: discovery excludes state_key targets from input_vars, exposing only user-supplied inputs | `yamlgraph/discovery.py` |
| REQ-YG-311 | JSON Schema derivation from state type annotations: str→string, int→integer, float→number, bool→boolean, list→array, dict→object; parameterized types map to base type; unknown types fall back to string | `yamlgraph/discovery.py` |
| REQ-YG-312 | Per-graph MCP tool registration: each discovered graph registers as its own named MCP tool with typed inputSchema derived from input_vars | `yamlgraph/mcp_server.py` |
| REQ-YG-313 | Tool name normalization: graph name hyphens replaced with underscores to produce valid MCP tool names | `yamlgraph/discovery.py` |
| REQ-YG-314 | Name collision detection: duplicate tool_name values across discovered graphs raise ValueError at server startup | `yamlgraph/mcp_server.py` |
| REQ-YG-315 | Watcher FSM system startup script: single script starts UI (event socket), generates diagrams, and launches dispatcher with correct `--initial-context` in proper sequence; cleanup on SIGINT/SIGTERM kills all child processes by PID with pkill fallback; `--inbox DIR` overrides inbox directory | `.chaplain/scripts/start-system.sh` |
| REQ-YG-316 | Simplified watcher pipeline v2 FSM: 6 operational states (setup, plan, commit_plan, judge, enforce_session, done) + 3 terminals (completed, failed, stopped). Judge uses different model from plan with fresh session (no resume). Enforce resumes plan session for full context continuity. Dispatcher flag-gated via pipeline_version context key. | `.chaplain/config/watcher-pipeline-v2.yaml`, `.chaplain/graphs/watcher-plan/step-judge-v2.yaml`, `.chaplain/graphs/watcher-enforce/enforce-session.yaml`, `tests/unit/test_fr305_watcher_pipeline_v2.py` |
| REQ-YG-317 | Root `README.md` includes all currently supported provider identifiers (`anthropic`, `azure`, `deepseek`, `google`, `inception`, `lmstudio`, `mistral`, `openai`, `replicate`, `vertex`, `xai`) in provider documentation, contains no hardcoded `all <number> reference docs` phrasing, and ends with `Last reviewed: 2026-05-03`; enforced by dedicated root README contract test (FR-313). | `README.md`, `tests/unit/test_root_readme_accuracy.py` |
| REQ-YG-318 | Watcher2 post-enforce flow inserts deterministic micro-remediation (`micro_changelog`, `micro_title`) before gate validation; micro-step errors fall back to `validate_fix` (LLM remediation); `validate_gate` (deterministic CI-parity gate) enforces pre-commit, commit-title contract, branch freshness vs `origin/main`, and diary-in-diff parity with bounded retry (`pass → done`, `fix_needed → validate_fix`, `error → failed`). Done PR title selection and validate_gate diary-parity trigger use the primary PR title selector policy: first feat/fix in `origin/main..HEAD`, else first non-docs/non-chore, else first subject. | `.chaplain/config/watcher-pipeline-v2.yaml`, `.chaplain/actions/changelog_gen_action.py`, `.chaplain/actions/validate_gate_action.py`, `.chaplain/lib/watcher/select_primary_pr_title.sh`, `.chaplain/graphs/watcher-enforce/prompts/validate-session.yaml`, `tests/unit/test_fr316_watcher2_validate_split_fix_gate.py`, `tests/unit/test_fr358_watcher2_primary_pr_title_selection.py`, `tests/unit/test_fr412_watcher2_micro_remediation_fast_path.py` |
| REQ-YG-319 | FSM bridge shared module: `yamlgraph.utils.fsm` package with `YamlgraphAsyncAction`, `extract_event`, `json_safe`, `resolve_context_ref` exported from `yamlgraph.utils.fsm`; fire-and-forget guard semantics; AF_UNIX DGRAM event dispatch; interrupt/completion-phase/done/event_map/route/success resolution cascade. | `yamlgraph/utils/fsm`, `examples/fsm-router/actions/yamlgraph_async_action.py`, `tests/unit/test_fsm_bridge_shared.py`, `tests/unit/test_fr346_fsm_bridge_shared_module_red.py`, `tests/unit/test_fr391_fsm_phase_aware_event_resolution.py` |
| REQ-YG-320 | CLI parser registers `yamlgraph skill export` with `--format {skill-md,copilot,cursor}` and `--output-dir` options; dispatch routes through `cli/skill_commands.py` | `yamlgraph/cli/__init__.py`, `yamlgraph/cli/skill_commands.py`, `tests/unit/test_fr348_skill_export_red.py` |
| REQ-YG-321 | Skill export creates package artifacts: `SKILL.md`, executable `scripts/run.sh`, `references/`, and `assets/schema.json`; run script includes one `--var key=example` per input | `yamlgraph/skill_export.py`, `yamlgraph/skill_export_writer.py`, `tests/unit/test_fr348_skill_export_red.py` |
| REQ-YG-322 | `SKILL.md` contract includes H1 skill name, description paragraph, `## Inputs` with type+description, `## Outputs` with type list, and `## Run` command example | `yamlgraph/skill_export.py`, `yamlgraph/skill_export_writer.py`, `tests/unit/test_fr348_skill_export_red.py` |
| REQ-YG-323 | `assets/schema.json` contains top-level `input` and `output` JSON Schema objects derived from graph state inputs and node `state_key` outputs | `yamlgraph/skill_export.py`, `yamlgraph/skill_export_writer.py`, `tests/unit/test_fr348_skill_export_red.py` |
| REQ-YG-324 | `--format skill-md|copilot|cursor` writes package to expected directory layouts for each ecosystem | `yamlgraph/skill_export.py`, `yamlgraph/skill_export_writer.py`, `tests/unit/test_fr348_skill_export_red.py` |
| REQ-YG-325 | Export is deterministic and non-LLM; missing/invalid graph, unsupported format, or non-empty existing target directory fail with explicit non-zero errors and no silent overwrite | `yamlgraph/skill_export.py`, `yamlgraph/skill_export_writer.py`, `yamlgraph/cli/skill_commands.py`, `tests/unit/test_fr348_skill_export_red.py` |
| REQ-YG-326 | CLI/reference documentation includes `yamlgraph skill export` usage and format layout examples, and reference index links to skill export guide | `reference/cli.md`, `reference/skills-export.md`, `reference/README.md`, `tests/unit/test_fr348_skill_export_red.py` |
| REQ-YG-327 | CLI parser accepts `yamlgraph skill export ... --format agent-md` and preserves existing export command wiring | `yamlgraph/cli/__init__.py`, `tests/unit/test_fr351_agent_export_red.py` |
| REQ-YG-328 | `--format agent-md` writes exactly one file artifact at `<output-dir>/.github/agents/<skill-name>.agent.md` | `yamlgraph/skill_export.py`, `yamlgraph/skill_export_writer.py`, `tests/unit/test_fr351_agent_export_red.py` |
| REQ-YG-329 | Generated `.agent.md` frontmatter includes graph description and tool scope `tools: [yamlgraph/*]` | `yamlgraph/skill_export_writer.py`, `tests/unit/test_fr351_agent_export_red.py` |
| REQ-YG-330 | Generated `.agent.md` body includes graph-scoped persona and explicit YAMLGraph MCP-only execution instruction | `yamlgraph/skill_export_writer.py`, `tests/unit/test_fr351_agent_export_red.py` |
| REQ-YG-331 | Export fails explicitly for missing graph path, invalid graph YAML, and existing output target collisions; CLI returns non-zero on export errors | `yamlgraph/skill_export.py`, `yamlgraph/cli/skill_commands.py`, `tests/unit/test_fr351_agent_export_red.py` |
| REQ-YG-332 | CLI and skill export reference documentation include `agent-md` usage and `.github/agents/<skill-name>.agent.md` layout | `reference/cli.md`, `reference/skills-export.md`, `tests/unit/test_fr351_agent_export_red.py` |
| REQ-YG-404 | YAMLGraph includes `examples/demos/philosopher_book/` with a four-node pipeline (load_trap → plan_chapter(copilot) → write_chapter(copilot) → save_chapter), where load_trap loads a single trap by chapter_num, diary search and file reading tools are available to copilot nodes, and save_chapter writes the chapter to `output_dir/chapters/`. | `examples/demos/philosopher_book/`, `tests/unit/test_philosopher_book.py` |
| REQ-YG-405 | YAMLGraph includes a separate philosopher-book editorial graph that snapshots repo-contained chapter inputs, builds a token-bounded global editorial brief, edits chapters through a `type: map` LLM pass, writes edited markdown to a separate repo-contained output folder with original filenames preserved, and writes an editorial report with word-count deltas and editorial notes. | `examples/demos/philosopher_book/editorial_graph.yaml`, `examples/demos/philosopher_book/tools.py`, `examples/demos/philosopher_book/prompts/editorial_brief.yaml`, `examples/demos/philosopher_book/prompts/edit_chapter.yaml`, `tests/unit/test_philosopher_book.py` |
| REQ-YG-406 | CLI parser accepts `yamlgraph graph lint --json` (default false), JSON mode emits one `LintResult` JSON object per linted file to stdout (NDJSON), routes diagnostics/errors to stderr, and preserves existing lint exit semantics (non-zero when lint errors occur, zero for warnings-only/clean runs). | `yamlgraph/cli/__init__.py`, `yamlgraph/cli/graph_validate.py`, `tests/unit/test_fr406_lint_json_output_red.py` |
| REQ-YG-407 | Watcher2 dispatcher includes `auditing` cadence routing with in-memory `last_audit_ts`: syncing_inbox emits `audit_needed` only when no topic is available and 24h elapsed, topic_found keeps priority, and audit action runs `.chaplain/inquisitor.sh --propose`, updates `last_audit_ts` on success, and returns `error` non-fatally to idle on failures. | `.chaplain/config/watcher-dispatcher.yaml`, `.chaplain/actions/syncing_inbox_action.py`, `.chaplain/actions/audit_action.py`, `tests/unit/test_fr411_watcher2_dispatcher_inquisitor_audit_cadence.py` |

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

ADR-001 defines explicit traceability tiers:

1. **Tier 1 (framework tests):** `tests/unit/` and `tests/integration/` require
   `@pytest.mark.req("REQ-YG-XXX")` on each test.
2. **Tier 2 (infrastructure hook tests):** `.github/hooks/tests/` is explicitly
   exempt from REQ-YG markers because these tests validate hook operational
   guards, not framework capability requirements.
3. **Tier 3 (demo/proof docs):** no REQ marker mandate.

Tier 1 tests are linked to one or more requirements via `@pytest.mark.req`:

```python
@pytest.mark.req("REQ-YG-014", "REQ-YG-031")
def test_invoke_with_retry_succeeds_after_transient_failure(mock_llm):
    ...
```

#### `scripts/req_coverage.py`

Generates a traceability matrix from `@pytest.mark.req` markers using AST
parsing for Tier 1 framework scope only (`tests/unit`, `tests/integration`).
Infrastructure hook tests under `.github/hooks/tests` are intentionally excluded.

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
| `utils/llm_factory.py` | Multi-provider LLM factory (11 providers) | 3 |
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
| `cli/skill_commands.py` | skill export dispatch | 9, 10 |
| `cli/helpers.py` | Shared CLI utilities | 9 |
| `cli/deprecation.py` | Deprecated command handling | 9 |
| `skill_export.py` | Portable skill package generation | 10 |
| `skill_export_writer.py` | Portable skill package file writers | 10 |

---

## Contributing

1. **Read this doc first** - Understand the architecture
2. **TDD approach** - Write tests before implementation
3. **Small PRs** - One feature per PR
4. **Update docs** - Reference docs and docstrings
5. **Run full test suite**: `pytest tests/ -q`
