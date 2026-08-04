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

### Module Organization: Concern Seams and Leaf Modules

The three-layer pattern governs *which layer* code belongs in. A second principle
governs how a single layer's package is split once it grows: **partition by concern
seam, and sink shared primitives into a leaf module so the dependency graph stays a
tree, not a cycle.**

When a module accretes several concerns and crosses the size ceiling (450 lines;
target <400), split it along the seams the code already reveals — not by mechanical
halving. Two failure modes recur when splitting:

1. **The sibling cycle.** Two new modules each need a shared substrate (accessors,
   constants, small pure helpers). Placing those primitives with their *busiest
   caller* makes the two siblings import each other. The fix is never to pick a
   winner: extract the substrate into a **leaf module** that imports neither sibling
   and is imported *by* both. The dependency graph becomes acyclic by construction.
2. **The facade hub.** Leaving re-exports in the emptied module so old call paths
   keep resolving creates a second source of truth and keeps the "split-out" symbols
   referenced from the original (defeating the decoupling). Migrate every call site
   to the new home instead — no compat shims (Commandment 8). The only re-exports
   that survive are those a *test identity contract* requires (`import x as x`).

The `examples/dungeon_master` package is the proving ground. `lifecycle_resolver`
(FR-534) and `turn_state` (FR-536) are leaf modules extracted precisely to dissolve
import cycles: the play loop and the opening gate both depend on turn/chapter
accessors, so those accessors sink below both. A generalized `test_module_size.py`
sweep enforces the ceiling across the whole package, so the drift cannot recur
silently.

A leaf module single-sources a *policy*, but the policy is only honored where it is
*applied*. When a derived value (a filtered roster, an allowed cast) is recomputed at
more than one site, sinking the resolution into one function is necessary but not
sufficient — every site that narrows the value must call it. FR-537's chapter-scoped
cast is the cautionary case: a `resolve_chapter_cast` leaf computes a chapter's focal
cast once, but two roster paths narrow it — the prose-control cast and the per-turn
intents roster built inline in the play loop. Wiring only the first leaves the
measured defect (off-chapter characters animated every turn) untouched, because the
defect lives on the *other* path. This is a SCOPE narrowing (who is in this chapter)
and is deliberately distinct from the lifecycle STATUS gates (is this character
alive/present): a present, reviewed character can still sit out a chapter, so the two
filters compose rather than subsume. Single-source the resolution; apply it at every
narrowing site; let an empty resolution fall back to the prior behavior so the
feature is additive.

| Smell | Cure |
|-------|------|
| Module > 450 lines mixing N concerns | Split along concern seams (use complexity/clone data to find them) |
| Two split siblings import each other | Sink the shared primitives into a leaf module both import |
| Old call paths kept alive by re-exports | Migrate call sites; delete the facade (keep only test-identity aliases) |
| A monkeypatch sets an attribute the call no longer reads | A patch is bound to the symbol's *module home* — retarget when the symbol moves |
| One narrowing point single-sourced but the defect rides another path | Apply the single-sourced policy at *every* site that derives the value, not just the busiest one |

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
│ • 12 providers: │  │ • JSON Schema   │  │ • resolve_path()│
│   Anthropic,    │  └─────────────────┘  └─────────────────┘
│   DeepSeek,     │
│   Google/Gemini,│
│   Inception,    │
│   Mistral,      │
│   OpenAI,       │
│   Replicate,    │
│   RunPod,       │
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
| 1 | CAP-1 Config Loading & Validation | `cli/helpers`, `cli/helpers.GraphLoadError`, `data_loader`, `data_loader.DataFileError`, … | REQ-YG-001 – 004, 546 |
| 2 | CAP-2 Graph Compilation | `graph_loader`, `graph_loader.apply_loop_node_defaults`, `graph_loader.compile_graph`, `graph_loader.detect_loop_nodes`, … | REQ-YG-005 – 008, 220, 239 |
| 3 | CAP-3 Node Execution | `executor`, `executor_async`, `executor_base`, `node_factory/llm_nodes`, … | REQ-YG-009 – 011, 050, 223, 539 – 540 |
| 4 | CAP-4 Prompt Execution | `executor.PromptExecutor`, `executor.execute_prompt`, `executor_async`, `executor_base.format_prompt`, … | REQ-YG-012 – 016, 216, 562 |
| 5 | CAP-5 Tool & Agent Integration | `node_factory/tool_nodes`, `tools/agent`, `tools/graph_tool`, `tools/nodes`, … | REQ-YG-017 – 020, 422, 510 |
| 6 | CAP-6 Routing & Flow Control | `node_factory/control_nodes`, `routing`, `utils/conditions` | REQ-YG-021 – 023, 214, 552 |
| 7 | CAP-7 State Persistence | `models/state_builder`, `storage/checkpointer`, `storage/checkpointer_factory`, `storage/simple_redis` | REQ-YG-024 – 026 |
| 8 | CAP-8 Error Handling | `error_handlers`, `error_handlers.NodeResult`, `error_handlers.build_skip_error_state`, `error_handlers.check_loop_limit`, … | REQ-YG-027 – 031 |
| 9 | CAP-9 CLI Interface | `cli/__init__`, `cli/__main__`, `cli/deprecation`, `cli/graph_commands`, … | REQ-YG-032 – 035 |
| 10 | CAP-10 Export & Serialization | `cli/graph_commands.cmd_graph_codegen`, `cli/schema_commands`, `storage/export`, `storage/serializers` | REQ-YG-036 – 039, 553 |
| 11 | CAP-11 Subgraph & Map | `map_compiler`, `map_compiler.wrap_for_reducer`, `node_factory/subgraph_nodes` | REQ-YG-040 – 042 |
| 12 | CAP-12 Utilities | `config`, `constants`, `node_factory/base`, `schema_loader`, … | REQ-YG-043 – 046 |
| 13 | CAP-13 LangSmith Tracing | `cli/graph_commands`, `utils/tracing` | REQ-YG-047, 547 |
| 14 | CAP-14 Graph-Level Streaming | `executor_async` | REQ-YG-048 – 049, 065, 480 |
| 15 | CAP-15 Expression Language | `utils/conditions`, `utils/expressions`, `utils/parsing` | REQ-YG-051 – 052 |
| 16 | CAP-16 Linter Cross-Reference | `linter/checks`, `linter/checks_contracts`, `linter/checks_semantic`, `linter/graph_linter`, … | REQ-YG-053 – 054, 069, 114, 408 |
| 17 | CAP-17 Execution Safety Guards | `cli/__init__`, `cli/graph_commands`, `config`, `executor`, … | REQ-YG-055 – 062, 064, 113 |
| 18 | CAP-18 Testing & Quality | `tests/conftest`, `tests/unit/test_requirement_enforcement` | REQ-YG-063 |
| 19 | CAP-19 MCP Server Interface | `mcp_server` | REQ-YG-066 – 068 |
| 20 | CAP-20 Contrib Utilities | `contrib/progress`, `contrib/utils` | REQ-YG-070 – 071 |
| 21 | CAP-21 Diary Digest Tools | `scripts/diary_digest_tools` | REQ-YG-072 |
| 22 | CAP-22 Code Quality Lints | `scripts/lint_inline_llm` | REQ-YG-073 |
| 23 | CAP-23 Skip-If-Exists Truthiness | `node_factory/llm_nodes._should_skip_if_exists` | REQ-YG-074 |
| 24 | CAP-24 Interactive Tool Node | `interactive_tool`, `node_factory/control_nodes`, `utils/conditions` | REQ-YG-075 |
| 25 | CAP-25 Tavily Domain RAG Demo | `examples/demos/tavily_rag` | REQ-YG-076 |
| 26 | CAP-26 Streaming Error Resilience | `executor_async`, `models/streaming` | REQ-YG-077 |
| 28 | CAP-28 Graph-Level Thinking Budget | `yamlgraph/models/graph_schema.py`, `yamlgraph/utils/llm_factory.py` | REQ-YG-083 |
| 30 | CAP-30 Copilot Node | `constants.NodeType.COPILOT`, `models/schemas`, `node_compiler`, `node_factory/copilot_node` | REQ-YG-087, 089, 105, 356 – 357 |
| 31 | CAP-31 Chaplain Diary Append | `examples/copilot/graph.yaml`, `examples/copilot/prompts/summarize.yaml`, `examples/shared/diary` | REQ-YG-090 |
| 32 | CAP-32 eBook Authoring Pipeline | `examples/ebook/nodes/writing.py`, `tests/unit/test_ebook_doctrine_validation.py` | REQ-YG-091 – 092 |
| 33 | CAP-33 Worktree Pipeline | `examples/enforce/graph.yaml`, `scripts/enforce_worktree.sh`, `utils/worktree_helpers` | REQ-YG-106 |
| 34 | CAP-34 Compiled Graph Cache | `executor_async`, `graph_cache` | REQ-YG-107 |
| 36 | CAP-36 Inquisitor Auto-Propose | `.chaplain/inquisitor.sh` | REQ-YG-118 |
| 37 | CAP-37 Architecture Provider Count Guard | `tests/unit/test_architecture_provider_count` | REQ-YG-121 |
| 38 | CAP-38 Post-Merge Finalization | `scripts/finalize_merge.sh`, `tests/unit/test_finalize_merge` | REQ-YG-125 |
| 39 | CAP-39 Inquisitor Commit-Delta Gate | `.chaplain/inquisitor.sh`, `tests/unit/test_inquisitor_gate` | REQ-YG-131 |
| 41 | CAP-41 Clean GIT Env Test Fixture | `tests/conftest.py`, `tests/unit/test_clean_git_env` | REQ-YG-140 |
| 42 | CAP-42 Inquisitor Worktree Gate | `.chaplain/inquisitor.sh`, `tests/unit/test_inquisitor_worktree_gate` | REQ-YG-142 |
| 43 | CAP-43 Copilot Session GC | `scripts/copilot_session_gc.sh`, `tests/unit/test_copilot_session_gc` | REQ-YG-141 |
| 44 | CAP-44 Judge SPLIT Verdict | `examples/copilot/prompts/judge.yaml`, `scripts/chaplain-prompts/judge.md`, `tests/unit/test_judge_split_verdict` | REQ-YG-143 |
| 45 | CAP-45 Diary Reflection Enforcement | `.pre-commit-config.yaml`, `scripts/finalize_merge.sh`, `tests/unit/test_precommit_hooks` | REQ-YG-144 |
| 46 | CAP-46 Diary Import CLI | `tests/unit/test_diary_commands`, `tests/unit/test_diary_importer`, `yamlgraph/cli/diary_commands.py`, `yamlgraph/diary/importer.py` | REQ-YG-122 |
| 47 | CAP-47 Phantom Requirement Detection | `scripts/req_coverage.py`, `tests/unit/test_req_coverage` | REQ-YG-145 |
| 48 | CAP-48 CHANGELOG Removal Completeness | `CHANGELOG.md`, `tests/unit/test_demo_cleanup_changelog` | REQ-YG-146 |
| 49 | CAP-49 Examples Documentation Audit | `examples/README.md`, `tests/unit/test_examples_readme_audit` | REQ-YG-147 |
| 50 | CAP-50 CI CHANGELOG Gate | `.github/workflows/commitlint.yml`, `scripts/gate_artifact_semantics.sh`, `tests/unit/test_ci_changelog_gate` | REQ-YG-148 |
| 51 | CAP-51 Branch Protection Documentation | `CLAUDE.md`, `reference/break-glass.md`, `tests/unit/test_branch_protection_docs` | REQ-YG-149 |
| 53 | CAP-53 CI Conflict Marker Gate | `.github/workflows/commitlint.yml`, `tests/unit/test_ci_conflict_check` | REQ-YG-151 |
| 54 | CAP-54 CI Diary Existence Gate | `.github/workflows/commitlint.yml`, `scripts/gate_artifact_semantics.sh`, `tests/unit/test_ci_diary_gate` | REQ-YG-152 |
| 55 | CAP-55 Chaplain Inbox Documentation | `CLAUDE.md`, `tests/unit/test_claude_md_chaplain_inbox` | REQ-YG-153 |
| 56 | CAP-56 Verification Gate Pattern | `yamlgraph/verification`, `node_factory/llm_nodes`, `linter/checks_contracts` | REQ-YG-154 |
| 57 | CAP-57 Verification Count Range Pydantic | `tests/unit/test_verification`, `yamlgraph/models/__init__`, `yamlgraph/verification` | REQ-YG-155 |
| 59 | CAP-59 Configurable Loop Exit Target | `tests/unit/test_loops`, `yamlgraph/edge_compiler`, `yamlgraph/graph_loader`, `yamlgraph/linter/checks_semantic`, … | REQ-YG-093 |
| 60 | CAP-60 Worktree Venv Corruption Guard | `scripts/enforce_worktree.sh`, `tests/unit/test_worktree_venv_guard`, `yamlgraph/utils/worktree_helpers` | REQ-YG-156 |
| 64 | CAP-64 Concurrency Safety Map | `docs/concurrency-safety.md`, `tests/unit/test_concurrency_safety_doc` | REQ-YG-160 |
| 65 | CAP-65 Append-Only Capability Registry | `capabilities/`, `scripts/validate_capabilities.py`, `scripts/req_coverage.py` | REQ-YG-161 |
| 66 | CAP-66 Append-Only Changelog | `changelog/`, `scripts/aggregate_changelog.py`, `scripts/migrate_changelog.py` | REQ-YG-162 |
| 67 | CAP-67 Philosopher Daemon | `examples/philosopher/`, `.chaplain/philosopher.sh` | REQ-YG-184 – 185, 194 |
| 68 | CAP-68 CI Dependency Security Scan | `.github/workflows/security.yml` | REQ-YG-186 |
| 69 | CAP-69 Knowledge Graph Graduation (FR-190) | `.github/copilot-instructions.md` | REQ-YG-187 |
| 70 | CAP-70 Knowledge Graph Graduation (FR-191) | `.github/copilot-instructions.md` | REQ-YG-188 |
| 71 | CAP-71 Release Changelog Sync Gate | `scripts/check_changelog_release_sync.py`, `scripts/release.sh`, `.github/workflows/commitlint.yml`, `.pre-commit-config.yaml`, … | REQ-YG-189 – 191 |
| 72 | CAP-72 Knowledge Graph Mass Graduation (FR-193) | `.github/copilot-instructions.md` | REQ-YG-192 |
| 73 | CAP-73 Philosopher Challenge Node (FR-195) | `examples/philosopher/models.py`, `examples/philosopher/tools.py`, `examples/philosopher/graph.yaml`, `examples/philosopher/prompts/distill.yaml`, … | REQ-YG-193 |
| 74 | CAP-74 FSM Scripture CLAUDE.md (FR-199) | `fsm/CLAUDE.md`, `tests/unit/test_fsm_claude_md_doctrine.py` | REQ-YG-195 |
| 75 | CAP-75 Portable Chaplain (FR-196) | `yamlgraph/tools/python_tool.py`, `.chaplain/graphs/philosopher/tools.py`, `.chaplain/lib/diary.py`, `tests/unit/test_python_nodes.py` | REQ-YG-196, 529 |
| 76 | CAP-76 Horoscope Demo | `examples/demos/horoscope` | REQ-YG-197 |
| 77 | CAP-77 Image Generation Pipeline | `examples/image_pipeline` | REQ-YG-198 |
| 78 | CAP-78 .fi Domain Crawl Demo | `examples/demos/fi-domain-crawl` | REQ-YG-199 |
| 79 | CAP-79 Demo Proof Gate | `scripts/check_demo_proof.sh`, `.github/workflows/commitlint.yml`, `.pre-commit-config.yaml` | REQ-YG-200 |
| 81 | CAP-81 A2A Protocol Server | `a2a_server`, `discovery`, `cli/a2a_commands` | REQ-YG-206 – 213 |
| 82 | CAP-82 Block AI Co-Author Trailers | `scripts/block_ai_coauthor.py`, `.pre-commit-config.yaml` | REQ-YG-215 |
| 83 | CAP-83 Research Agent Demo | `examples/demos/research-agent` | REQ-YG-217 |
| 84 | CAP-84 Import-Linter Architectural Boundary Enforcement | `.importlinter`, `.pre-commit-config.yaml`, `.github/workflows/workflow.yml` | REQ-YG-218 |
| 85 | CAP-85 Dependency Rationale Audit | `scripts/dependency_rationale.py`, `docs/dependency-rationale.yaml`, `.pre-commit-config.yaml` | REQ-YG-219 |
| 86 | CAP-86 Ruff Security Rules | `pyproject.toml`, `docs/confessions.md` | REQ-YG-222 |
| 87 | CAP-87 Ruff C901 Cognitive Complexity Gate | `pyproject.toml`, `docs/confessions.md` | REQ-YG-221 |
| 88 | CAP-88 Google/Vertex Thinking Budget Support | `yamlgraph/utils/llm_factory.py`, `yamlgraph/models/graph_schema.py`, `yamlgraph/linter/checks_providers.py` | REQ-YG-230 |
| 89 | CAP-89 Execution Timing Callback | `yamlgraph/utils/timing_tracker.py`, `yamlgraph/cli/graph_commands.py`, `yamlgraph/cli/__init__.py` | REQ-YG-231 |
| 90 | CAP-90 Graph Bench Command | `yamlgraph/cli/bench_commands.py`, `yamlgraph/cli/graph_commands.py`, `yamlgraph/cli/__init__.py` | REQ-YG-232 |
| 91 | CAP-91 Race Node Type | `yamlgraph/node_factory/race_node.py`, `yamlgraph/constants.py`, `yamlgraph/compile/node_compiler.py`, `yamlgraph/models/graph_schema.py`, … | REQ-YG-233, 269 |
| 92 | CAP-92 Chatterbox TTS Demo | `examples/demos/chatterbox` | REQ-YG-234 |
| 93 | CAP-93 Chatterbox Voice Clone Demo | `examples/demos/chatterbox` | REQ-YG-235, 238 |
| 94 | CAP-94 Compile-Time Pipeline Templates | `yamlgraph/compile/pipeline_template.py`, `yamlgraph/constants.py`, `yamlgraph/compile/graph_loader.py`, `yamlgraph/linter/checks.py`, … | REQ-YG-236 |
| 95 | CAP-95 Parallel Fan-Out Edges | `yamlgraph/compile/edge_compiler.py` | REQ-YG-237 |
| 96 | CAP-96 Per-Node Timeout | `yamlgraph/compile/map_compiler.py`, `yamlgraph/compile/node_compiler.py`, `yamlgraph/models/graph_schema.py`, `yamlgraph/models/schemas.py`, … | REQ-YG-078 |
| 98 | CAP-98 Pipeline Accumulated State | `yamlgraph/models/state_builder.py`, `reference/graph-yaml.md`, `tests/unit/test_state_builder_reducers.py` | REQ-YG-241 |
| 99 | CAP-99 Race and Pipeline Node Type Documentation | `reference/graph-yaml.md`, `reference/getting-started.md` | REQ-YG-240 |
| 100 | CAP-100 Chatterbox Multilingual CLI | `examples/demos/chatterbox` | REQ-YG-242 |
| 101 | CAP-101 A2A Consumer Contrib Client | `yamlgraph/contrib/a2a_client.py`, `yamlgraph/tools/python_tool.py` | REQ-YG-243 |
| 102 | CAP-102 Complete Worktree Teardown Self-Heal | `yamlgraph/utils/worktree_helpers`, `scripts/enforce_worktree.sh`, `scripts/bugfix_worktree.sh`, `tests/unit/test_worktree_teardown_self_heal` | REQ-YG-244 |
| 103 | CAP-103 A2A SDK v1.0 Compatibility | `yamlgraph/a2a/server.py`, `yamlgraph/a2a/message.py`, `yamlgraph/contrib/a2a_client.py`, `yamlgraph/cli/a2a_commands.py` | REQ-YG-245 |
| 104 | CAP-104 A2A Server Reference Documentation | `reference/a2a-server.md`, `reference/cli.md` | REQ-YG-246 |
| 105 | CAP-105 A2A Consumer Phase 2 — Agent Card, Skill Selection & Streaming | `yamlgraph/contrib/a2a_client.py` | REQ-YG-250 – 253 |
| 106 | CAP-106 GitHub Issues Remote Inbox | `.chaplain/watch.sh`, `tests/unit/test_github_issues_remote_inbox` | REQ-YG-247 |
| 107 | CAP-107 Guardrails Pattern Documentation | `reference/patterns.md`, `examples/README.md` | REQ-YG-254 |
| 108 | CAP-108 Changelog REQ Cross-Validation Gate | `scripts/check_changelog_req.py`, `graphs/enforcement/changelog-req-check.yaml`, `.pre-commit-config.yaml`, `.github/workflows/commitlint.yml` | REQ-YG-255 |
| 109 | CAP-109 Harden GitHub Issues Remote Inbox | `.chaplain/watch.sh`, `.chaplain/allowed-authors.txt` | REQ-YG-256 |
| 110 | CAP-110 Diary Index Graph | `examples/demos/diary_index` | REQ-YG-257 |
| 111 | CAP-111 Shared Graph Invocation | `graph_loader` | REQ-YG-258 |
| 113 | CAP-113 Chaplain Research Step | `.chaplain/graphs/watcher-plan` | REQ-YG-260 |
| 114 | CAP-114 Automated Post-Merge Finalization | `.chaplain/lib/finalize_lib.sh`, `.chaplain/watch.sh`, `scripts/finalize_merge.sh`, `tests/unit/test_automated_post_merge_finalization` | REQ-YG-261 |
| 116 | CAP-116 Acceptance Tests Before Enforce | `.chaplain/config/watcher-pipeline-v2.yaml`, `.chaplain/graphs/watcher-plan/step-plan-unified.yaml`, `.chaplain/graphs/watcher-plan/prompts/write-acceptance-tests.yaml`, `.chaplain/graphs/watcher-plan/prompts/judge.yaml`, … | REQ-YG-263 |
| 117 | CAP-117 Race Node parse_json & Content Normalization | `yamlgraph/node_factory/race_node.py`, `yamlgraph/utils/content.py`, `yamlgraph/tools/agent.py` | REQ-YG-264 |
| 118 | CAP-118 Copilot Node Model Selection | `yamlgraph/models/graph_schema.py`, `yamlgraph/compile/node_compiler.py`, `yamlgraph/node_factory/copilot_node.py` | REQ-YG-265 |
| 119 | CAP-119 Race Node Timeout Fix | `yamlgraph/node_factory/race_node.py`, `yamlgraph/compile/node_compiler.py` | REQ-YG-266 |
| 120 | CAP-120 CLI Inter-Run State Chaining | `yamlgraph/cli/__init__.py`, `yamlgraph/cli/graph_commands.py`, `yamlgraph/cli/helpers.py`, `yamlgraph/storage/export.py` | REQ-YG-267 – 268 |
| 121 | CAP-121 Async Race Node with Cancellable Candidates | `yamlgraph/node_factory/race_node.py`, `tests/unit/test_race_node.py` | REQ-YG-270 |
| 122 | CAP-122 Router Node with Candidates Race Support | `yamlgraph/node_factory/llm_nodes.py`, `yamlgraph/utils/validators.py`, `yamlgraph/models/state_builder.py`, `yamlgraph/compile/node_compiler.py`, … | REQ-YG-271 |
| 124 | CAP-124 Watcher2 PR Reuse (FR-275) | `.chaplain/lib/watcher/create_pr.sh`, `tests/unit/test_watcher2_create_pr_reuse.py` | REQ-YG-272 |
| 125 | CAP-125 Pipeline Script Retirement (FR-276) | `.chaplain/scripts/start-system.sh`, `.chaplain/config/watcher-dispatcher.yaml`, `.chaplain/config/watcher-pipeline-v2.yaml`, `.chaplain/lib/watcher/worktree_setup.sh`, … | REQ-YG-276 |
| 126 | CAP-126 Test Speed Optimization | `pyproject.toml`, `tests/chaos_tools.py`, `tests/unit/test_map_node_timeout.py`, `tests/unit/test_race_node.py`, … | REQ-YG-275 |
| 127 | CAP-127 CI Hardening Consolidation | `.github/workflows/workflow.yml`, `.github/workflows/security.yml`, `.github/workflows/commitlint.yml`, `tests/unit/test_ci_hardening_consolidation.py` | REQ-YG-277 |
| 128 | CAP-128 Chaplain Documentation | `.chaplain/README.md`, `tests/unit/test_chaplain_readme_documentation` | REQ-YG-278 |
| 130 | CAP-130 Watcher2 Finalize Pre-commit Optimization | `.chaplain/scripts/start-system.sh`, `tests/unit/test_fr198_watcher2_finalize_optimization.py` | REQ-YG-286 |
| 131 | CAP-131 Anthropic Prompt Caching Support | `yamlgraph/executor_base.py`, `yamlgraph/utils/prompts.py`, `tests/unit/test_prompt_caching_fr276.py`, `tests/unit/test_prompt_caching_demo_fr219.py`, … | REQ-YG-287 – 293, 302 – 306 |
| 132 | CAP-132 Watcher2 CI Resilience | `.chaplain/lib/watcher/wait_ci.sh`, `tests/unit/test_fr279_watcher2_ci_resilience.py` | REQ-YG-294, 298 – 301 |
| 133 | CAP-133 Watcher2 CI Remediation Crash Fix | `.chaplain/scripts/start-system.sh`, `tests/unit/test_fr284_watcher2_ci_remediation_crash_fix.py` | REQ-YG-307 |
| 134 | CAP-134 Watcher2 Changelog Auto-Generation | `.chaplain/scripts/start-system.sh`, `.chaplain/graphs/watcher-enforce/prompts/enforce-critique-and-distill.yaml`, `.chaplain/graphs/watcher-enforce/prompts/enforce-finalize.yaml`, `.chaplain/graphs/watcher-enforce/step-ci-remediate.yaml` | REQ-YG-308 |
| 135 | CAP-135 Watcher2 Forensic Failure Diary | `.chaplain/scripts/start-system.sh`, `.chaplain/graphs/watcher-forensic/`, `.chaplain/lib/diary.py` | REQ-YG-309 |
| 136 | CAP-136 Per-Graph Typed MCP Tools | `yamlgraph/discovery.py`, `yamlgraph/export/mcp.py` | REQ-YG-310 – 314 |
| 137 | CAP-137 Watcher FSM System Startup Script | `.chaplain/scripts/start-system.sh` | REQ-YG-315 |
| 138 | CAP-138 Watcher Pipeline FSM Simplification | `.chaplain/config/watcher-pipeline-v2.yaml`, `.chaplain/graphs/watcher-plan/step-judge-v2.yaml`, `.chaplain/graphs/watcher-enforce/enforce-session.yaml` | REQ-YG-316 |
| 139 | CAP-139 Root README Accuracy Contract | `README.md`, `tests/unit/test_root_readme_accuracy.py` | REQ-YG-317 |
| 140 | CAP-140 Watcher2 Validate Split Fix/Gate | `.chaplain/config/watcher-pipeline-v2.yaml`, `.chaplain/actions/changelog_gen_action.py`, `.chaplain/actions/validate_gate_action.py`, `.chaplain/graphs/watcher-enforce/validate-session.yaml`, … | REQ-YG-318 |
| 141 | CAP-141 Shared FSM Bridge Module | `yamlgraph/utils/fsm/__init__.py`, `yamlgraph/utils/fsm/helpers.py`, `yamlgraph/utils/fsm/event_sender.py`, `yamlgraph/utils/fsm/graph_runner.py`, … | REQ-YG-319 |
| 142 | CAP-142 Skill Export Portable Packaging | `yamlgraph/export/skill.py`, `yamlgraph/export/skill_writer.py`, `yamlgraph/cli/__init__.py`, `yamlgraph/cli/skill_commands.py`, … | REQ-YG-320 – 326 |
| 143 | CAP-143 Agent Export Tool-Scoped Personas | `yamlgraph/export/skill.py`, `yamlgraph/export/skill_writer.py`, `yamlgraph/cli/__init__.py`, `yamlgraph/cli/skill_commands.py`, … | REQ-YG-327 – 332 |
| 145 | CAP-145 Copilot Instrumentation Gap Closure | `scripts/copilot_instrument.sh`, `scripts/extract_copilot_events.py`, `scripts/extract_copilot_events_lib.py`, `docs/copilot-instrumentation-poc.md`, … | REQ-YG-340 – 346 |
| 146 | CAP-146 FSM Snapshot Hooks Phase 2 Subclassing | `yamlgraph/utils/fsm/snapshot.py`, `yamlgraph/utils/fsm/action.py`, `yamlgraph/utils/fsm/graph_runner.py`, `yamlgraph/utils/fsm/__init__.py`, … | REQ-YG-347 |
| 147 | CAP-147 Graph Run JSON Stdout + TypeScript Node Integration | `yamlgraph/cli/__init__.py`, `yamlgraph/cli/graph_commands.py`, `yamlgraph/cli/helpers.py`, `yamlgraph/storage/export.py`, … | REQ-YG-348 – 355 |
| 148 | CAP-148 CI Co-authored-by Trailer Gate | `.github/workflows/commitlint.yml`, `tests/unit/test_fr385_ci_copilot_trailer_gate_red.py`, `CLAUDE.md` | REQ-YG-358 |
| 149 | CAP-149 Prompt Theme Analyzer Demo | `examples/demos/prompt_theme_analyzer/graph.yaml`, `examples/demos/prompt_theme_analyzer/tools.py`, `examples/demos/prompt_theme_analyzer/prompts/classify_theme.yaml`, `examples/demos/prompt_theme_analyzer/prompts/group_themes.yaml`, … | REQ-YG-359 |
| 150 | CAP-150 Philosopher's Book Demo | `examples/demos/philosopher_book/graph.yaml`, `examples/demos/philosopher_book/editorial_graph.yaml`, `examples/demos/philosopher_book/tools.py`, `examples/demos/philosopher_book/prompts/plan_chapter.yaml`, … | REQ-YG-404 – 405 |
| 151 | CAP-151 Graph Lint JSON Output | `yamlgraph/cli/__init__.py`, `yamlgraph/cli/graph_validate.py`, `tests/unit/test_fr406_lint_json_output_red.py`, `ARCHITECTURE.md` | REQ-YG-406 |
| 152 | CAP-152 Watcher2 Dispatcher Audit Cadence | `.chaplain/config/watcher-dispatcher.yaml`, `.chaplain/actions/syncing_inbox_action.py`, `.chaplain/actions/audit_action.py`, `tests/unit/test_fr411_watcher2_dispatcher_inquisitor_audit_cadence.py`, … | REQ-YG-407 |
| 153 | CAP-153 Built-in Questionnaire Gap Utilities | `yamlgraph/tools/questionnaire.py`, `tests/unit/test_fr421_questionnaire_gap_utilities_red.py`, `reference/probe-recap-questionnaire.md`, `ARCHITECTURE.md` | REQ-YG-409 – 410 |
| 154 | CAP-154 Hook Classification Daemon | `examples/demos/hook_classifier/actions/classify_action.py`, `examples/demos/hook_classifier/config/hook-classifier.yaml`, `examples/demos/hook_classifier/graphs/classify-intent.yaml`, `examples/demos/hook_classifier/prompts/classify-tool-intent.yaml`, … | REQ-YG-411 – 416 |
| 155 | CAP-155 Schema Loader Tool Type | `yamlgraph/tools/schema_loader_tool.py`, `yamlgraph/tools/python_tool.py`, `yamlgraph/compile/graph_loader.py`, `yamlgraph/compile/node_compiler.py`, … | REQ-YG-417 – 418 |
| 156 | CAP-156 WIP Commit Subject Gate | `.pre-commit-config.yaml`, `.github/workflows/commitlint.yml`, `tests/unit/test_fr424_wip_main_gate_red.py`, `CLAUDE.md`, … | REQ-YG-419 |
| 157 | CAP-157 Graph Loader Strict Tool Load Fail Fast | `yamlgraph/compile/graph_loader.py`, `tests/unit/test_fr444_graph_loader_tool_load_mode_red.py`, `reference/graph-yaml.md`, `ARCHITECTURE.md` | REQ-YG-420 – 421 |
| 158 | CAP-158 Copilot Skill Promotion | `.github/skills/release-version/SKILL.md`, `.github/skills/chaplain-ops/SKILL.md`, `.github/skills/run-code-analysis/SKILL.md`, `.github/skills/feature-request/SKILL.md`, … | REQ-YG-423 |
| 159 | CAP-159 Standalone Planner Demo | `examples/demos/planner/graph.yaml`, `examples/demos/planner/prompts/planner.yaml`, `examples/demos/planner/tools/write_file.py`, `examples/demos/planner/demo.sh` | REQ-YG-424 |
| 160 | CAP-160 CAP Architecture Auto-Sync | `.pre-commit-config.yaml`, `scripts/aggregate_capabilities.py` | REQ-YG-425 |
| 161 | CAP-161 Standalone Enforcer Demo | `examples/demos/enforcer/graph.yaml`, `examples/demos/enforcer/prompts/enforcer.yaml`, `examples/demos/enforcer/tools/write_file.py`, `examples/demos/enforcer/tools/edit_file.py`, … | REQ-YG-426 |
| 162 | CAP-162 Enforcer Demo Safety Hardening | `examples/demos/enforcer/graph.yaml`, `examples/demos/enforcer/prompts/enforcer.yaml`, `examples/demos/enforcer/tools/write_file.py`, `examples/demos/enforcer/tools/edit_file.py`, … | REQ-YG-427 |
| 163 | CAP-163 CAP Retirement Support | `scripts/req_coverage.py`, `scripts/validate_capabilities.py`, `tests/unit/test_fr466_cap_retirement_support_red.py`, `tests/unit/test_capability_registry.py` | REQ-YG-428 |
| 164 | CAP-164 Structured Output JSON Fallback | `yamlgraph/executor.py`, `yamlgraph/node_factory/race_node.py` | REQ-YG-464 – 465 |
| 165 | CAP-165 Watcher2 Baseline Dead Code Removal | `tests/unit/test_fr278_remove_baseline_dead_code.py` | REQ-YG-466 |
| 166 | CAP-166 Meta Self-Reflective Demo | `examples/demos/meta` | REQ-YG-467 |
| 167 | CAP-167 Dungeon Master Example | `examples/dungeon_master/nodes/story_io` | REQ-YG-429 – 433 |
| 168 | CAP-168 Conditional Edge to Map Node | `yamlgraph/edge_compiler`, `yamlgraph/routing` | REQ-YG-434 |
| 169 | CAP-169 Dungeon Master Web UI | `examples/dungeon_master/api/session`, `examples/dungeon_master/api/routes/story` | REQ-YG-435 – 437 |
| 170 | CAP-170 Dungeon Master Web UI v2 (Journey-First) | `examples/dungeon_master/api/session`, `examples/dungeon_master/api/story_doc`, `examples/dungeon_master/api/routes/story` | REQ-YG-468 – 471 |
| 171 | CAP-171 Executor Plain-Text Content Normalization | `yamlgraph/executor.py`, `yamlgraph/utils/llm_factory_async.py`, `yamlgraph/utils/content.py` | REQ-YG-472 |
| 172 | CAP-172 Prompt-Monolith Linter Check (W026) | `yamlgraph/linter/checks_prompts.py`, `yamlgraph/linter/graph_linter.py` | REQ-YG-473 |
| 173 | CAP-173 Write Data File Tool | `tools/write_data_file_tool` | REQ-YG-474 – 477 |
| 174 | CAP-174 Data Files Glob Support | `data_loader` | REQ-YG-478 – 479 |
| 175 | CAP-175 Novel Fandom Canon Schema | `examples` | REQ-YG-481 – 483, 523 |
| 176 | CAP-176 Novel Fandom Enriched World Model | `examples` | REQ-YG-484 – 486 |
| 177 | CAP-177 Novel Fandom Plot Pathfinder | `examples` | REQ-YG-487 – 488 |
| 178 | CAP-178 Novel Fandom Prose and Close Loop | `examples` | REQ-YG-489 – 491 |
| 179 | CAP-179 Novel Fandom Wiki Core Types | `examples` | REQ-YG-492 – 493 |
| 180 | CAP-180 Novel Fandom World Expansion | `examples` | REQ-YG-494 – 504 |
| 181 | CAP-181 Novel Fandom Genesis Pipeline | `examples/novel_fandom` | REQ-YG-505 – 507 |
| 182 | CAP-182 Agentic Event Deepening | `examples/novel_fandom/nodes/canon_tools.py`, `examples/novel_fandom/nodes/split_thin_by_type.py`, `examples/novel_fandom/prompts/deepen_event_agent.yaml`, `examples/novel_fandom/worldgen.yaml` | REQ-YG-509 |
| 183 | CAP-183 First-Class Verification | `yamlgraph/utils/guard_runtime.py`, `yamlgraph/compile/node_compiler.py`, `yamlgraph/tools/nodes.py`, `yamlgraph/tools/python_tool.py`, … | REQ-YG-511 |
| 184 | CAP-184 Novel Fandom Duplicate Entity Prevention | `examples/novel_fandom` | REQ-YG-512 – 514 |
| 185 | CAP-185 Novel Fandom Ref Integrity Graph-Tool | `examples/novel_fandom` | REQ-YG-515 |
| 186 | CAP-186 Novel Fandom Genesis Self-Correcting Pipeline | `examples/novel_fandom` | REQ-YG-516 |
| 187 | CAP-187 Novel Fandom Semantic Dedup Graph-Tool | `examples/novel_fandom` | REQ-YG-517 |
| 188 | CAP-188 Novel Fandom Agent-First Architecture | `examples/novel_fandom/genesis.yaml`, `examples/novel_fandom/worldgen.yaml`, `examples/novel_fandom/nodes/creation_tools.py`, `examples/novel_fandom/create_character.yaml`, … | REQ-YG-518 – 522 |
| 189 | CAP-189 Worktree CLI Contract | `scripts/worktree.sh`, `scripts/wt`, `tests/unit/test_worktree_cli_red.py` | REQ-YG-524 |
| 191 | CAP-191 Instrumentation Worktree Delegation | `scripts/copilot_instrument.sh`, `tests/unit/test_copilot_instrument_worktree_delegation_red.py` | REQ-YG-526 |
| 192 | CAP-192 Branch Deny Guidance Manual Worktree Lane | `.github/hooks/scripts/pre-command-guard.sh`, `.github/hooks/tests/test_pre_command_guard.py` | REQ-YG-527 |
| 193 | CAP-193 Watcher Wrapper JSON Envelope | `.chaplain/lib/watcher/worktree_setup.sh`, `.chaplain/lib/watcher/worktree_teardown.sh`, `tests/unit/test_watcher_worktree_wrapper_red.py` | REQ-YG-528 |
| 194 | CAP-194 Novel Fandom Plot Threads and Throughlines | `examples` | REQ-YG-530 |
| 195 | CAP-195 Timeframe Recap Demo | `examples` | REQ-YG-531, 534 – 536 |
| 196 | CAP-196 Novel Fandom World Pressure | `examples` | REQ-YG-532 – 533 |
| 197 | CAP-197 Novel Fandom Event Revision | `examples` | REQ-YG-537 – 538 |
| 198 | CAP-198 Persistent Bridge Loop | `yamlgraph/utils/bridge.py`, `yamlgraph/node_factory/race_node.py`, `yamlgraph/node_factory/router_race_node.py` | REQ-YG-541 |
| 199 | CAP-199 Security and Coverage Gate Truth | `scripts/noqa_coverage.py` | REQ-YG-542 |
| 200 | CAP-200 Prompt Request Front Door | `yamlgraph/executor.py`, `yamlgraph/executor_base.py` | REQ-YG-543 |
| 201 | CAP-201 Pre-emptive Module Splits | `yamlgraph/models/graph_schema.py`, `yamlgraph/models/node_schema.py`, `yamlgraph/streaming_events.py`, `yamlgraph/executor_async.py` | REQ-YG-544 |
| 202 | CAP-202 SMT Condition Verification | `yamlgraph/linter/patterns/conditions_smt.py` | REQ-YG-545 |
| 203 | CAP-203 ICPC-2 RFE Classifier Example | `examples/icpc-2-rfe/nodes/build_catalog.py`, `examples/icpc-2-rfe/nodes/catalog.py`, `examples/icpc-2-rfe/nodes/reduce.py` | REQ-YG-548 – 551, 554 – 556 |
| 204 | CAP-204 CWE Vulnerability Classifier Example | `examples/cwe-classifier/nodes/build_catalog.py`, `examples/cwe-classifier/nodes/catalog.py`, `examples/cwe-classifier/nodes/reduce.py`, `examples/cwe-classifier/nodes/crosscheck.py` | REQ-YG-557 – 561 |
| 205 | CAP-205 World Distill Graph | `.chaplain/graphs/world_distill` | REQ-YG-563 |
| 206 | CAP-206 FR Triage Graph | `.chaplain/graphs/fr_triage` | REQ-YG-564 |
| 207 | CAP-207 Loader Error UX | `utils/prompts.check_messages_contract`, `tools/python_tool`, `linter/checks_loader_ux` | REQ-YG-565 |
| 208 | CAP-208 FR Atlas Onboarding Demo | `examples/demos/fr-atlas/nodes/collect.py`, `examples/demos/fr-atlas/nodes/coverage.py`, `examples/demos/fr-atlas/nodes/render.py` | REQ-YG-566 |
| 209 | CAP-209 Root Package Seams | `yamlgraph/a2a`, `yamlgraph/export`, `yamlgraph/compile` | REQ-YG-567 |
| 210 | CAP-210 Edge Shape Classification | `yamlgraph/compile/edge_compiler.py` | REQ-YG-568 |
| 211 | CAP-211 Sole-Route Judge and Review Wrappers | `scripts/judge.sh`, `scripts/review.sh`, `.github/skills/judge-fr/adapters/graph.yaml`, `.github/skills/review-pr/adapters/graph.yaml` | REQ-YG-569 |
| 212 | CAP-212 OpenTelemetry Observability Boundary | `yamlgraph/observability/otel.py`, `yamlgraph/compile/node_otel.py`, `yamlgraph/compile/node_compiler.py`, `yamlgraph/cli/graph_commands.py` | REQ-YG-570 |
| 213 | CAP-213 Example Dependency Taxonomy Generator | `scripts/example_taxonomy_scan.py` | REQ-YG-571 |
| 214 | CAP-214 Direct-Import Dependency Scanner | `scripts/direct_import_scan.py` | REQ-YG-572 |
| 215 | CAP-215 Style-Convert Pipeline | `examples/style_convert` | REQ-YG-573 |
| 216 | CAP-216 Tool Manifests | `tools`, `graph_loader` | REQ-YG-574 |
| 217 | CAP-217 Shared Vision Tool | `examples` | REQ-YG-575 |

> Capability numbers are stable identifiers. Gaps (e.g. 27, 29, 52, 58) indicate retired capabilities.

### 1. CAP-1 Config Loading & Validation

Load YAML graph configs, validate schemas, build state models, and ensure graph integrity through linting.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-001 | Load graph configurations from YAML files | `graph_loader.load_graph_config`, `cli/helpers`, `data_loader` |
| REQ-YG-002 | Validate graph configuration schemas and structures | `models/graph_schema`, `utils/validators` |
| REQ-YG-003 | Perform linting and pattern validation | `linter/graph_linter`, `linter/checks`, `linter/patterns/*` |
| REQ-YG-004 | Handle errors during configuration loading | `cli/helpers.GraphLoadError`, `data_loader.DataFileError` |
| REQ-YG-546 | Passthrough node output/outputs accept literal seeds (FR-721): the schema is dict[str, Any] matching the runtime contract — resolve_template's documented first branch passes non-string values through unchanged, and init nodes legitimately seed state with list/dict/bool literals. Template strings keep validating; literal types round-trip through model_dump unchanged (quoting "[]" would silently corrupt state seeding). Mapping fields (output_mapping, interrupt_output_mapping) remain genuinely string-to-string. Surfaced by ninchat NC-370 pin alignment: 8 ValidationErrors on a graph running correctly in production. | `models/node_schema` |

### 2. CAP-2 Graph Compilation

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

### 3. CAP-3 Node Execution

Create executable node functions for LLM, streaming, tool, interrupt, and subgraph behavior.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-009 | Node creation and streaming | `node_factory/llm_nodes`, `node_factory/streaming` |
| REQ-YG-010 | Synchronous LLM factory management | `utils/llm_factory` |
| REQ-YG-011 | Asynchronous LLM factory management | `utils/llm_factory_async` |
| REQ-YG-050 | Per-node and default-level `model` override: graph YAML `model` field flows through `execute_prompt()` to `create_llm()` | `node_factory/llm_nodes`, `executor`, `executor_async`, `executor_base` |
| REQ-YG-223 | LLM node factory decomposed into composable phases: LLMNodeConfig frozen dataclass, resolve_llm_node_config() pure config resolver, _apply_verification(), _resolve_route(), _handle_error() — each independently testable, all below C901=10 (FR-223) | `node_factory/llm_nodes` |
| REQ-YG-539 | Every provider constructor in llm_providers.py bounds provider work at the client boundary (FR-708): an explicit finite request timeout (default LLM_REQUEST_TIMEOUT=30s, env-overridable, garbage values raise) and bounded retries (max_retries=2) via the wrapper-correct parameter (timeout for the ChatOpenAI/ChatAnthropic/ ChatGoogleGenerativeAI/ChatMistralAI/Azure families, request_timeout for ChatLiteLLM). Caller-supplied kwargs win over the defaults. VERTEX_TRANSPORT=rest\|grpc plumbs transport= into the google and vertex constructors (express and ADC branches); invalid values raise at the boundary. A hung provider endpoint fails within the timeout instead of hanging forever and accumulating transport channels (Fly freeze RCA 2026-07-10). | `utils/llm_providers` |
| REQ-YG-540 | LLM client cache is uniform and env-fingerprinted (FR-712 → FR-713 Part B): one caching rule for every provider — clients live their whole life on the persistent bridge loop (FR-713 Part A), so the loop affinity that condemned cached google-genai clients under the fresh-loop bridge (FR-711 Finding A: ~50% of completed calls errored) is honored by construction, and the FR-712 interim carve-out that excluded google/vertex from the cache is retired. The cache key embeds an env fingerprint (FR-227: construction is env-sensitive) — a common var set every constructor reads (LLM_REQUEST_TIMEOUT) plus a declarative per-provider list (keys, project/location, VERTEX_TRANSPORT); changing a fingerprinted var yields a new client, unchanged env is a cache hit. Vertex participates by same-class inference (FR-712 F4, symmetric: inferred out, inferred in) — witnessed for google by a warm-cached zero-errors-over-10 integration run on the bridge loop; one line to re-exclude if the field ever contradicts. | `utils/llm_factory` |

### 4. CAP-4 Prompt Execution

Load prompt YAML, validate variables, format messages, and run LLM calls sync and async.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-012 | Prompt loading and resolution | `utils/prompts` |
| REQ-YG-013 | Variable resolution and template management | `executor_base.format_prompt`, `utils/expressions`, `utils/template` |
| REQ-YG-216 | extract_variables() subtracts set-statement targets in nested blocks (FR-214) | `utils/template` |
| REQ-YG-014 | Synchronous prompt execution | `executor.PromptExecutor`, `executor.execute_prompt` |
| REQ-YG-015 | Asynchronous prompt execution | `executor_async` |
| REQ-YG-016 | JSON extraction from LLM outputs | `utils/json_extract` |
| REQ-YG-562 | Constraint fidelity through the inline-schema path: a prompt YAML schema built via schema_loader preserves ge/le constraints, defaults, and required fields through model_json_schema() so the JSON Schema is portable to external grammar-enforced runtimes (FR-731 WebLLM spike). The spike instrument is self-evidencing (FR-735): per-run console records, byte-fidelity raw downloads, and a per-session evidence.md in the FR-731 F1 tally shape with computed kill-criterion arithmetic | `schema_loader` |

### 5. CAP-5 Tool & Agent Integration

Integrate shell, Python, and graph tools into graphs, enable agent loops for tool-calling.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-017 | Dynamic tool node creation | `node_factory/tool_nodes` |
| REQ-YG-018 | Agent-driven tool selection and execution | `tools/agent` |
| REQ-YG-019 | Shell tool integration and execution | `tools/shell`, `tools/nodes` |
| REQ-YG-020 | Python tool integration and execution | `tools/python_tool` |
| REQ-YG-422 | Agent node structured output via prompt schema (FR-448) | `tools/agent` |
| REQ-YG-510 | Graph-as-tool in-process pipeline invocation (FR-658) | `tools/graph_tool`, `graph_loader` |

### 6. CAP-6 Routing & Flow Control

Route across nodes using explicit routes, expression evaluation, and control nodes.

**Feature Request:** FR-211

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-021 | Control node creation (interrupt, passthrough) | `node_factory/control_nodes` |
| REQ-YG-022 | Conditional routing functions | `routing` |
| REQ-YG-023 | Condition expression evaluation | `utils/conditions` |
| REQ-YG-214 | Router route mapping redirects interrupt targets to *_prepare and subgraph interrupt targets to *__run in conditional edge route mappings (FR-211) | `edge_compiler`, `graph_loader` |
| REQ-YG-552 | Route decision hook (FR-723). Every routing decision — simple router, expression match, loop-limit exit, map fan-out, no-match fallthrough — emits one JSON line on the public yamlgraph.route logger when opted in (YAMLGRAPH_ROUTE_LOG env or observability.route_log graph flag). Map fan-outs emit map-node name + count, never Send payloads (R-2 privacy). thread_id carried by a contextvar set at run entrypoints, null never fabricated (R-1). Zero serialization when off; emission never raises. | `routing`, `utils/route_log` |

### 7. CAP-7 State Persistence

Checkpointers and Redis storage for resuming pipelines and state history.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-024 | Dynamic state class generation | `models/state_builder` |
| REQ-YG-025 | Checkpointer provisioning | `storage/checkpointer_factory` |
| REQ-YG-026 | State persistence operations (Redis) | `storage/simple_redis`, `storage/checkpointer` |

### 8. CAP-8 Error Handling

Error strategies (retry, fallback, skip), sanitization, resilience features.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-027 | Error handling strategies (skip, fail, retry, fallback) | `error_handlers` |
| REQ-YG-028 | Pre-execution validation (requirements, loop limits) | `error_handlers.check_requirements`, `error_handlers.check_loop_limit` |
| REQ-YG-029 | Error state management (NodeResult, skip updates) | `error_handlers.NodeResult`, `error_handlers.build_skip_error_state` |
| REQ-YG-030 | Error schemas and reporting | `models/schemas.PipelineError`, `models/schemas.ErrorType` |
| REQ-YG-031 | Retry capability | `executor_base.is_retryable`, `executor._invoke_with_retry` |

### 9. CAP-9 CLI Interface

Command-line commands for graph validation, execution, info display, schema export.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-032 | CLI entry point and parser setup | `cli/__init__`, `cli/__main__` |
| REQ-YG-033 | Graph command execution and information | `cli/graph_commands` |
| REQ-YG-034 | Deprecation handling for CLI commands | `cli/deprecation` |
| REQ-YG-035 | CLI utilities and schema command dispatch | `cli/helpers`, `cli/schema_commands` |

### 10. CAP-10 Export & Serialization

Export results/states in JSON/Markdown, handle serialization for persistence.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-036 | CLI schema export and access | `cli/schema_commands` |
| REQ-YG-037 | Graph code generation for IDE support | `cli/graph_commands.cmd_graph_codegen` |
| REQ-YG-038 | Export and management of pipeline results/states | `storage/export` |
| REQ-YG-039 | Serialization and deserialization utilities | `storage/serializers` |
| REQ-YG-553 | Authored-graph Mermaid export (FR-723). graph export --mermaid renders the authored YAML view (typed nodes, condition labels, router routes, loop limits, explicit loop-exit edges); --overlay renders an executed route.jsonl with taken edges and decision ordinals so the ordered route is reconstructible from the render; --diff compares two routes occurrence-aligned per (node, occurrence) naming the seam and Nth firing. Pure stdlib+yaml, no LLM. | `mermaid_export`, `cli/export_commands` |

### 11. CAP-11 Subgraph & Map

Parallel fan-out and nested subgraph execution.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-040 | Map node compilation | `map_compiler` |
| REQ-YG-041 | Output wrapping for reduction | `map_compiler.wrap_for_reducer` |
| REQ-YG-042 | Subgraph node creation | `node_factory/subgraph_nodes` |

### 12. CAP-12 Utilities

Logging, templating, JSON extraction, environment handling, and shared utilities.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-043 | Configuration and constants management | `config`, `constants` |
| REQ-YG-044 | Schema loading and model building | `schema_loader` |
| REQ-YG-045 | Node factory and resolution | `node_factory/base` |
| REQ-YG-046 | Logging and parsing utilities | `utils/logging`, `utils/parsing` |

### 13. CAP-13 LangSmith Tracing

Observability via LangSmith: trace URL retrieval, public sharing, and tracer injection.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-047 | LangSmith trace URL retrieval and sharing | `utils/tracing`, `cli/graph_commands` |
| REQ-YG-547 | Race-loser trace spans close on cancellation (FR-720): the candidate wrapper pre-generates a run_id per ainvoke attempt (passed as config={"run_id": ...} — the handle, since tracing is ambient and no callback handle exists), and on CancelledError enqueues client.update_run with end_time, terminal error ("cancelled: lost race to {provider}/{model}" on the winner path, "cancelled: race timed out" on the FR-707 drain path) and extra.metadata.race_outcome=lost before re-raising. Enqueue-only: the verdict path never waits for losers (FR-707 discipline unchanged). Skipped cleanly when tracing is disabled. Spawned by NC-367 census: 38/38 deployed vertex loser spans pending-forever rendered "cancelled by design" as "hung", taxing every trace-based investigation and blinding FR-711's deployed A/B. | `node_factory/race_node` |

### 14. CAP-14 Graph-Level Streaming

Stream LLM tokens through the compiled graph pipeline using LangGraph astream(stream_mode="messages"), enabling real-time SSE output.

**Feature Request:** FR-633

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-048 | Graph-level streaming: run graph with `astream(stream_mode="messages")` yielding LLM tokens | `executor_async` |
| REQ-YG-049 | Streaming with multi-turn: `run_graph_streaming_native()` accepts `Command(resume=...)`, config with thread_id for checkpoint-based resume | `executor_async` |
| REQ-YG-065 | Native LangGraph streaming: `run_graph_streaming_native()` uses `astream(stream_mode="messages")` to stream from ALL LLM nodes, with optional `node_filter` | `executor_async` |
| REQ-YG-480 | CLI streaming: `yamlgraph graph run --stream` uses `run_graph_streaming_native()` for real-time token output to stdout | `cli` |

### 15. CAP-15 Expression Language

Value expressions, condition expressions, literal parsing, and resolve_node_variables batch resolution.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-051 | Expression language: value expressions (`{state.path}`, arithmetic, list/dict ops), condition expressions (comparisons, compound AND/OR), literal parsing, `resolve_node_variables` batch resolution | `utils/expressions`, `utils/conditions`, `utils/parsing` |
| REQ-YG-052 | Expression language hardening: quote-aware compound split, right-side state reference resolution, chained arithmetic detection | `utils/conditions`, `utils/expressions` |

### 16. CAP-16 Linter Cross-Reference

Linter cross-reference and semantic checks for edge endpoints, loop limits, state references, and contract warnings.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-053 | Linter cross-reference & semantic checks: edge endpoint validation (E006), loop_limits references (E008), passthrough output (E601), tool_call fields (E701/E702), condition syntax (W801), variable prefix (W007), fallback config (E010), conditional edge type (E802) | `linter/checks`, `linter/graph_linter` |
| REQ-YG-054 | Chaplain audit fixes: `wrap_for_reducer` non-dict return handling, LLM SKIP error recording, linter E011 retry/fallback on tool/python nodes, `prompts_relative` warning | `map_compiler`, `node_factory/llm_nodes`, `linter/checks`, `utils/prompts` |
| REQ-YG-069 | Linter E007: error when `{state.X}` in node `variables`/`output`/`over`/`args`/`input_mapping` references a field not in known state (declared `state:` + node `state_key` + `BUILTIN_STATE_FIELDS` + `COMMON_INPUT_FIELDS` + `data_files` + map `collect`). Promoted from W014 warning to E007 error (FR-110) | `linter/checks_semantic` |
| REQ-YG-114 | Linter W017: warn when node uses `on_error: skip` — silent fallback that drops failures without trace | `linter/checks_contracts`, `linter/graph_linter` |
| REQ-YG-408 | hedging_check enforces fallback-token hygiene in production Python by reporting lexical `fallback` usage as FB001, validating confession-backed allowlist mappings (`file:line -> CONF-XXX` with Code=FB001), preserving existing Pattern 1 detection, adding Pattern 2 (`X = expr or fallback`), and running pre-commit scope on both `yamlgraph/` and `scripts/`. | `scripts/hedging_check`, `.pre-commit-config.yaml`, `docs/confessions.md` |

### 17. CAP-17 Execution Safety Guards

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

### 18. CAP-18 Testing & Quality

Requirement traceability enforcement and testing infrastructure.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-063 | Requirement traceability enforcement: `pytest_collection_modifyitems` hook structurally enforces ADR-001 — framework tests in `tests/unit` and `tests/integration` must have `@pytest.mark.req`; infrastructure tests in `.github/hooks/tests` are excluded from this requirement | `tests/conftest`, `tests/unit/test_requirement_enforcement` |

### 19. CAP-19 MCP Server Interface

Expose YAMLGraph graphs as MCP (Model Context Protocol) tools for Copilot and other AI assistants.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-066 | MCP server with stdio transport: expose `yamlgraph_list_graphs` and `yamlgraph_run_graph` tools via MCP protocol | `mcp_server` |
| REQ-YG-067 | Graph discovery: scan configured directories for `graph.yaml`, parse headers for name/description/required vars | `mcp_server` |
| REQ-YG-068 | Graph invocation via MCP: compile and invoke any discovered graph with vars, return structured result JSON | `mcp_server` |

### 20. CAP-20 Contrib Utilities

Shared utilities extracted from pipeline patterns. Eliminates copy-paste duplication across projects.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-070 | Contrib utils: `get_map_result()` unwraps single-key `_map_*_sub` dicts; `to_serializable()` converts Pydantic models to dicts recursively | `contrib/utils` |
| REQ-YG-071 | Contrib progress: `SkipReport` reads `state["errors"]` and provides human-readable skip summaries with counts and node names | `contrib/progress` |

### 21. CAP-21 Diary Digest Tools

Scheduled pipeline tools for fetching external developments and appending context-aware diary entries.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-072 | Diary digest: fetch HN/RSS sources, filter by relevance, format diary entries, append to diary.md, no-op when nothing relevant | `scripts/diary_digest_tools` |

### 22. CAP-22 Code Quality Lints

Custom lint checks enforcing architectural patterns beyond standard linters.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-073 | Inline LLM lint: detect scripts with `def main()` that import LLM execution functions without graph loading — flags orchestration code smell | `scripts/lint_inline_llm` |

### 23. CAP-23 Skip-If-Exists Truthiness

skip_if_exists checks truthiness, not existence. Empty collections, empty strings, None, 0, and False do NOT trigger skip.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-074 | skip_if_exists uses truthiness check: `[]`, `""`, `None`, `0`, `False` do not skip; only truthy values skip | `node_factory/llm_nodes._should_skip_if_exists` |

### 24. CAP-24 Interactive Tool Node

Declarative multi-turn stateful tool integration via config-level expansion.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-075 | Interactive tool node: expand `type: interactive_tool` into start/ask/step/end inline nodes with loop condition, max iterations, and interrupt-based user input | `interactive_tool`, `node_factory/control_nodes`, `utils/conditions` |

### 25. CAP-25 Tavily Domain RAG Demo

Domain-scoped RAG using Tavily search API with type:python tool nodes and map fan-out.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-076 | Tavily domain RAG: python tool retrieves context via Tavily API with optional `TAVILY_TARGET_DOMAIN` scoping; simple graph (retrieve→answer) and deep graph (plan→map(retrieve)→synthesize) | `examples/demos/tavily_rag` |

### 26. CAP-26 Streaming Error Resilience

Error propagation, timeout support, and interrupt detection for run_graph_streaming_native(). Yields StreamEvent Pydantic objects for errors and interrupts instead of crashing silently.

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-077 | Streaming error resilience: wrap `astream()` with try/except to yield `StreamEvent(type="error")` on exceptions; `asyncio.timeout()` for stall detection; interrupt payload detection via `aget_state()` after stream completes; `yield_events=False` flag for opt-out (raises instead) | `executor_async`, `models/streaming` |

### 28. CAP-28 Graph-Level Thinking Budget

Graph-level and per-node thinking_budget YAML field for Anthropic extended thinking.

**Feature Request:** FR-071

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-083 | `thinking_budget` YAML field on graph `defaults` and per-node; validated as `0` or `≥ 1024`; passed as `thinking={"type":"enabled","budget_tokens":N}` to `ChatAnthropic` with forced `temperature=1` (override before cache key); raises on non-Anthropic provider; included in LLM cache key | `yamlgraph/models/graph_schema.py`, `yamlgraph/utils/llm_factory.py` |

### 30. CAP-30 Copilot Node

New copilot node type that delegates graph processing to Copilot CLI, replacing shell-script orchestration with a first-class YAML-declarable node.

**Feature Request:** FR-082

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-087 | Copilot node executes via CLI backend with configurable flags and timeout; `--silent` always forced; list-based `subprocess.run()` for injection safety; graceful `FileNotFoundError` when copilot binary missing | `node_factory/copilot_node`, `node_compiler`, `constants.NodeType.COPILOT` |
| REQ-YG-089 | Copilot node composes with router, map, and FSM-router patterns; standard node guarantees apply (requires, on_error, skip_if_exists, loop protection) | `node_factory/copilot_node`, `node_compiler` |
| REQ-YG-105 | Copilot node session continuations via `--resume` and `--continue` flags; session ID captured from stderr into `CopilotResult.session_id`; state expression resolution for `cli_flags.resume` | `node_factory/copilot_node`, `models/schemas` |
| REQ-YG-356 | Copilot node supports explicit `backend: api` execution via `execute_prompt()`, while preserving default CLI behavior when backend is omitted or `cli`. | `node_factory/copilot_node`, `models/schemas` |
| REQ-YG-357 | Copilot lint rules are backend-aware: API backend warns when no explicit model signal is present and errors when API mode is combined with CLI-only `cli_flags`. | `linter/patterns/copilot`, `node_factory/copilot_node` |

### 31. CAP-31 Chaplain Diary Append

Extends the Plan-Judge workflow with automatic diary entry creation after each run.

**Feature Request:** FR-090

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-090 | `format_diary_entry()` accepts configurable `prefix` parameter (default "World Digest"); `examples/copilot/graph.yaml` includes `summarize` (LLM) and `write_diary` (Python) nodes; `watch.sh` passes `date` and `diary_prefix` vars | `examples/shared/diary`, `examples/copilot/graph.yaml`, `examples/copilot/prompts/summarize.yaml` |

### 32. CAP-32 eBook Authoring Pipeline

A YAMLGraph pipeline that writes the development pipeline documentation as an eBook.

**Feature Request:** FR-100

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-091 | `write_chapters_tool` writes formatted chapter content to disk; accepts `output_dir` and chapter state variables; creates directory if missing; returns dict with `written` list of paths | `examples/ebook/nodes/writing.py` |
| REQ-YG-092 | Chapter validation detects fabricated doctrine content; `verify_commandments_verbatim()` checks all 10 Commandments appear exactly as in source; returns `{passed, found, missing, fabricated}` dict | `tests/unit/test_ebook_doctrine_validation.py` |

### 33. CAP-33 Worktree Pipeline

Parallel development pipeline via git worktrees, enabling multiple features to be enforced simultaneously without blocking the main working tree.

**Feature Request:** FR-106

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-106 | Worktree helpers derive branch names from FR paths, construct worktree paths under `tmp/worktrees/`, and validate clean working tree before creation; shell script orchestrates worktree lifecycle with trap-based cleanup; 4-phase graph (implement → test/demo → precommit → PR) chains via session continuations | `utils/worktree_helpers`, `scripts/enforce_worktree.sh`, `examples/enforce/graph.yaml` |

### 34. CAP-34 Compiled Graph Cache

Process-global compiled graph cache so load_and_compile_async() results survive module reloads and are shared across all callers within the same Python process.

**Feature Request:** FR-111

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-107 | Process-global `GRAPH_CACHE` dict in installed package; `load_and_compile_async()` uses cache by default with `cache=None` opt-out; `clear_cache()` for test teardown; cache-hit logs at DEBUG, compile logs at INFO | `graph_cache`, `executor_async` |

### 36. CAP-36 Inquisitor Auto-Propose

--propose flag on inquisitor.sh detects violations persisting across consecutive Inquisitor Audit entries and writes targeted fix proposals to .chaplain/inbox/.

**Feature Request:** FR-118

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-118 | `inquisitor.sh --propose` parses flag, gates a second copilot call that reads up to 5 diary audit entries, detects persistent ✗ violations (≥2 consecutive), classifies as micro-fix or structural gap, writes proposal markdown to `.chaplain/inbox/inquisitor-<slug>.md` with filename-based dedup; without `--propose` the audit-only flow is unchanged | `.chaplain/inquisitor.sh` |

### 37. CAP-37 Architecture Provider Count Guard

Cross-check test ensuring the provider count in ARCHITECTURE.md module table matches the actual ProviderType Literal in llm_factory.py.

**Feature Request:** FR-121

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-121 | Test asserts ARCHITECTURE.md module table provider count for `llm_factory.py` equals `len(get_args(ProviderType))`; prevents documentation drift when providers are added or removed | `tests/unit/test_architecture_provider_count` |

### 38. CAP-38 Post-Merge Finalization

Automates three post-merge obligations after a PR from the enforce pipeline is merged: CHANGELOG entry, FR status update, and diary reflection stub.

**Feature Request:** FR-125

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-125 | `scripts/finalize_merge.sh` inserts CHANGELOG entry under `[Unreleased] / ### Added`, updates FR status to `✅ Implemented`, and appends diary reflection stub with Trap/Heuristic/Seed placeholders | `scripts/finalize_merge.sh`, `tests/unit/test_finalize_merge` |

### 39. CAP-39 Inquisitor Commit-Delta Gate

inquisitor.sh commit-delta gate extracts last audit SHA from docs/diary/, counts feat:/fix: commits since that SHA, and aborts when none found.

**Feature Request:** FR-131

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-131 | `inquisitor.sh` commit-delta gate extracts last audit SHA from `docs/diary/`, counts `feat:`/`fix:` commits since that SHA via `git log`, and aborts with clear message when none found; `--force` bypasses gate; gate degrades gracefully on missing diary, unparseable SHA, or first-ever audit; `--propose` respects gate; gate logic is pure shell | `.chaplain/inquisitor.sh`, `tests/unit/test_inquisitor_gate` |

### 41. CAP-41 Clean GIT Env Test Fixture

Session-scoped autouse pytest fixture strips GIT_* environment variables injected by pre-commit, preventing subprocess bleed into tests that create temporary git repos.

**Feature Request:** FR-140

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-140 | `_clean_git_env` session-scoped autouse fixture strips all `GIT_*` env vars at session start, restores on teardown; no-op when vars absent; prevents pre-commit `GIT_DIR`/`GIT_WORK_TREE` from leaking into subprocess git calls in `tmp_path`-based test repos | `tests/conftest.py`, `tests/unit/test_clean_git_env` |

### 42. CAP-42 Inquisitor Worktree Gate

inquisitor.sh worktree gate detects git worktree context and exits early, suppressing audit and propose phases during enforce pipeline.

**Feature Request:** FR-142

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-142 | `inquisitor.sh` worktree gate checks `-f "$REPO_ROOT/.git"` (file = worktree, directory = main), exits 0 with message when in worktree; `--force` bypasses gate; degrades gracefully when `git rev-parse` fails; gate placed before commit-delta gate (FR-131); pure shell, no Python | `.chaplain/inquisitor.sh`, `tests/unit/test_inquisitor_worktree_gate` |

### 43. CAP-43 Copilot Session GC

Shell script that prunes stale Copilot CLI sessions from ~/.copilot/session-state/ based on age.

**Feature Request:** FR-138

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-141 | `copilot_session_gc.sh` removes session directories older than `--max-age` days (default 7); `--dry-run` lists candidates without deleting; active session (`$COPILOT_SESSION_ID`) is never removed; exits cleanly when directory is missing; idempotent; logs UUID and age for each removed session | `scripts/copilot_session_gc.sh`, `tests/unit/test_copilot_session_gc` |

### 44. CAP-44 Judge SPLIT Verdict

Add a fourth judge verdict (SPLIT) for multi-concern feature requests, enabling decomposition before implementation.

**Feature Request:** FR-136

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-143 | Judge prompts must include `SPLIT` verdict and Scope Count rubric for multi-concern FR decomposition; unit tests verify both prompt sources and conflict fixture behavior | `examples/copilot/prompts/judge.yaml`, `scripts/chaplain-prompts/judge.md`, `tests/unit/test_judge_split_verdict` |

### 45. CAP-45 Diary Reflection Enforcement

Pre-commit hook diary-reflection-check rejects commits when staged docs/diary/ reflection files contain unfilled placeholder text or miss the literal `Seed:` marker.

**Feature Request:** FR-144

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-144 | `diary-reflection-check` pre-commit hook scans staged tracked reflection files for unfilled placeholder text and missing literal `Seed:` markers, then blocks commit; `finalize_merge.sh` creates stubs as untracked files (no `git add` of `docs/diary/`); hook passes when placeholders are filled and `Seed:` is present | `.pre-commit-config.yaml`, `scripts/finalize_merge.sh`, `tests/unit/test_precommit_hooks` |

### 46. CAP-46 Diary Import CLI

CLI command to import pending diary entries and git report data into docs/diary/ with optional dry-run and source selection.

**Feature Request:** FR-124

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-122 | `yamlgraph diary import` CLI command imports pending diary entries and git reports into `docs/diary/` with `--dry-run` and `--source` flags; shared importer returns structured `ImportResult` list; dry-run does not mutate source files; malformed files reported and exit non-zero; explicit missing `--source` emits warning | `yamlgraph/diary/importer.py`, `yamlgraph/cli/diary_commands.py`, `tests/unit/test_diary_importer`, `tests/unit/test_diary_commands` |

### 47. CAP-47 Phantom Requirement Detection

Detect and reject test markers that reference non-existent requirement IDs.

**Feature Request:** FR-145

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-145 | Phantom requirement detection: `req_coverage.py --strict` rejects `@pytest.mark.req` markers referencing requirement IDs absent from `ALL_REQS` or `ARCHITECTURE.md` | `scripts/req_coverage.py`, `tests/unit/test_req_coverage` |

### 48. CAP-48 CHANGELOG Removal Completeness

CHANGELOG.md [Unreleased] documents significant file removals per Commandment 8.

**Feature Request:** FR-153

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-146 | CHANGELOG.md `[Unreleased]` contains a `### Removed` section documenting stale demo file deletions (commit a0e6f00): `examples/cost-router/poc_granite.py`, `scripts/loopback-poc/` (419 lines); section ordering follows Keep a Changelog convention (Added → Removed → Fixed) | `CHANGELOG.md`, `tests/unit/test_demo_cleanup_changelog` |

### 49. CAP-49 Examples Documentation Audit

Every on-disk example and demo is accurately indexed in examples/README.md with categorized sections and enforced quality bar.

**Feature Request:** FR-135

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-147 | `examples/README.md` lists every demo directory and top-level example on disk; demos are split into Learning / Utility / FR Validation sections; inclusion criteria are documented; each listed entry has a `README.md` and at least one runnable artifact (YAML graph, `demo.sh`, or Python script) | `examples/README.md`, `tests/unit/test_examples_readme_audit` |

### 50. CAP-50 CI CHANGELOG Gate

GitHub Actions job in commitlint.yml that blocks merge of feat and fix PRs unless changed changelog fragments under changelog/unreleased/ pass substance validation.

**Feature Request:** FR-149

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-148 | `changelog-gate` job in `commitlint.yml` runs `git diff --name-only` against base/head SHAs and fails when no `changelog/unreleased/*.md` fragment is present in diff; each changed fragment must be non-empty, contain YAML front matter with `type:`, and include at least one markdown list item in the body; shared validation is sourced from `scripts/gate_artifact_semantics.sh`; job-level `if` condition restricts to `feat`/`fix` PR titles (skipped for other types); uses `actions/checkout@v4` with `fetch-depth: 0` for full history | `.github/workflows/commitlint.yml`, `scripts/gate_artifact_semantics.sh`, `tests/unit/test_ci_changelog_gate` |

### 51. CAP-51 Branch Protection Documentation

GitHub branch protection rules on main enforcing squash-merge only, required status checks, and no direct pushes.

**Feature Request:** FR-150

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-149 | `reference/break-glass.md` documents emergency bypass procedure with audit trail requirements; `CLAUDE.md` contains Branch Protection section listing enforced rules, required status checks, and link to break-glass procedure | `reference/break-glass.md`, `CLAUDE.md`, `tests/unit/test_branch_protection_docs` |

### 53. CAP-53 CI Conflict Marker Gate

CI job that fails when unresolved merge conflict markers are found in tracked files, complementing the local check-merge-conflict pre-commit hook.

**Feature Request:** FR-157

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-151 | CI conflict marker gate: The `conflict-check` job in `commitlint.yml` greps tracked files (excluding `.github/`) for conflict marker patterns and fails with non-zero exit when found | `.github/workflows/commitlint.yml`, `tests/unit/test_ci_conflict_check` |

### 54. CAP-54 CI Diary Existence Gate

CI gate ensuring feat/fix PRs with FR references include a diary reflection file in the diff and that the reflection passes substance validation.

**Feature Request:** FR-158

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-152 | `diary-gate` job in `commitlint.yml` extracts `FR-XXX` from PR title, runs `git diff --name-only` against base/head SHAs, and fails when no `docs/diary/*reflection*fr-{number}*` file is in diff; matching files must be non-empty, exceed 100 bytes, contain at least one markdown `##` header, and include `Seed:` marker; shared validation is sourced from `scripts/gate_artifact_semantics.sh`; skips (passes) when PR title has no FR reference; job-level `if` condition restricts to `feat`/`fix` PR titles; uses `actions/checkout@v4` with `fetch-depth: 0` for full history | `.github/workflows/commitlint.yml`, `scripts/gate_artifact_semantics.sh`, `tests/unit/test_ci_diary_gate` |

### 55. CAP-55 Chaplain Inbox Documentation

Document the .chaplain/inbox/ workflow in CLAUDE.md so Claude Code sessions can discover and use the autonomous proposal pipeline.

**Feature Request:** FR-163

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-153 | `CLAUDE.md` contains a "Submitting Proposals" subsection documenting the `.chaplain/inbox/` workflow, matching the canonical source in `.github/copilot-instructions.md` verbatim, placed between the "Development Process" and "Development Commands" sections | `CLAUDE.md`, `tests/unit/test_claude_md_chaplain_inbox` |

### 56. CAP-56 Verification Gate Pattern

Per-node runtime verification with deterministic pattern matching. Checks stated predictions against actual node output.

**Feature Request:** FR-164

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-154 | NodeConfig accepts optional verification field (VerificationConfig) with question, on_fail, and count_range for runtime output validation | `yamlgraph/verification`, `node_factory/llm_nodes`, `linter/checks_contracts` |

### 57. CAP-57 Verification Count Range Pydantic

Count range verification claim parsed into CountRangeClaim Pydantic model with min/max validation.

**Feature Request:** FR-166

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-155 | Count range verification claim parsed into `CountRangeClaim` Pydantic model with `min_count` (int, ge=0), `max_count` (int, ge=0) and `model_validator` enforcing min ≤ max. Inverted ranges raise `ValueError` at parse time. Violation `details` exposes `expected_min`, `expected_max`, `actual_count` for programmatic inspection | `yamlgraph/verification`, `yamlgraph/models/__init__`, `tests/unit/test_verification` |

### 59. CAP-59 Configurable Loop Exit Target

loop_exits graph-level config maps node names to custom exit targets when loop limit is reached.

**Feature Request:** FR-172

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-093 | `loop_exits` graph-level config maps node names to custom exit targets when loop limit is reached. `GraphConfigSchema` validates as `dict[str, str]` with default `{}`. `make_expr_router_fn` accepts optional `loop_exit_target`; when `_loop_limit_reached` is True, returns configured target instead of `END`. Lint rule E009 validates keys exist in `loop_limits` and targets are valid nodes | `yamlgraph/routing`, `yamlgraph/edge_compiler`, `yamlgraph/graph_loader`, `yamlgraph/models/graph_schema`, `yamlgraph/linter/checks_semantic`, `tests/unit/test_loops` |

### 60. CAP-60 Worktree Venv Corruption Guard

Worktree venv corruption guard: validate_venv_health() raises on missing or broken venv, clean_stale_pth_entries() prevents import corruption from dangling editable installs.

**Feature Request:** FR-174

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-156 | Worktree venv corruption guard: `validate_venv_health()` raises `FileNotFoundError` when `.venv` directory is missing, `bin/python` is absent, or not executable (no silent skip). `validate_venv_symlink()` raises `OSError` when worktree `.venv` symlink doesn't resolve. `clean_stale_pth_entries()` removes `.pth`/`.egg-link` files referencing a deleted worktree directory to prevent import corruption from dangling editable installs | `yamlgraph/utils/worktree_helpers`, `scripts/enforce_worktree.sh`, `tests/unit/test_worktree_venv_guard` |

### 64. CAP-64 Concurrency Safety Map

docs/concurrency-safety.md documents every concurrency pattern in YAMLGraph with verdict, model, shared state, and evidence.

**Feature Request:** FR-176

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-160 | Concurrency safety map: `docs/concurrency-safety.md` documents every concurrency pattern in YAMLGraph with verdict (Safe/Conditional/Unsafe), concurrency model, shared mutable state, safety invariant, and file:line evidence. Covers 6 areas: map node fan-out, checkpoint writes, graph cache, inquisitor diary writes, MCP server, async executor. Each entry classifies shared state and serialization mechanism | `docs/concurrency-safety.md`, `tests/unit/test_concurrency_safety_doc` |

### 65. CAP-65 Append-Only Capability Registry

Replace the monolithic CAPABILITIES dict in req_coverage.py with individual YAML files under capabilities/. New FRs add files rather than editing shared artifacts, eliminating merge conflicts on traceability data.

**Feature Request:** FR-178

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-161 | Append-only capability registry: individual YAML files in capabilities/ validated by scripts/validate_capabilities.py pre-commit hook, loaded by scripts/req_coverage.py. New capabilities are added as files, not edits to shared code. Pre-commit hook enforces schema on every commit. | `capabilities/`, `scripts/validate_capabilities.py`, `scripts/req_coverage.py`, `tests/unit/test_capability_registry.py` |

### 66. CAP-66 Append-Only Changelog

Replace monolithic CHANGELOG.md with fragment files under changelog/. Each change adds a markdown fragment with YAML front matter (type, scope, req). scripts/aggregate_changelog.py assembles fragments into CHANGELOG.md on demand. Eliminates merge conflicts on the changelog entirely.

**Feature Request:** FR-179

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-162 | Append-only changelog fragments: individual markdown files in changelog/unreleased/ with YAML front matter (type, scope, req). scripts/aggregate_changelog.py assembles all fragments into CHANGELOG.md grouped by version and type. Pre-commit and CI gates enforce fragment existence for feat/fix PRs. CHANGELOG.md is gitignored and generated on demand. | `changelog/`, `scripts/aggregate_changelog.py`, `scripts/migrate_changelog.py`, `tests/unit/test_changelog_fragments.py` |

### 67. CAP-67 Philosopher Daemon

Automates the Philosopher role by scanning diary entries for recurring patterns (Trap, Heuristic, Seed markers) and proposing graduations to Scripture. On-demand daemon writes proposals to .chaplain/inbox/ for Chaplain to process.

**Feature Request:** FR-184

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-184 | Automated diary pattern scanning and graduation proposals | `examples/philosopher/tools.py`, `examples/philosopher/graph.yaml`, `.chaplain/philosopher.sh` |
| REQ-YG-185 | Copilot node migration with Pydantic-validated JSON extraction | `examples/philosopher/models.py`, `examples/philosopher/tools.py`, `examples/shared/diary.py` |
| REQ-YG-194 | World context loading for philosopher reflection enrichment | `examples/philosopher/tools.py`, `examples/philosopher/graph.yaml`, `examples/philosopher/prompts/reflect.yaml`, `docs/world-context.md` |

### 68. CAP-68 CI Dependency Security Scan

CI workflow that runs pip-audit to scan Python dependencies for known vulnerabilities (CVEs) on every PR and version tag push.

**Feature Request:** FR-187

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-186 | CI workflow runs pip-audit --strict --desc on every PR and version tag push. Produces a 'security' required status check for branch protection. | `.github/workflows/security.yml` |

### 69. CAP-69 Knowledge Graph Graduation (FR-190)

Graduates the infrastructure_self_exempt trap to the Scripture Knowledge Graph in .github/copilot-instructions.md, based on 3 confirmed diary occurrences (audits 94, 95, 97). Names the cognitive blind spot where meta-tooling exempts itself from the quality gates it enforces.

**Feature Request:** FR-190

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-187 | infrastructure_self_exempt trap present in Scripture traps section with exact text, no existing traps/cures/process entries changed | `.github/copilot-instructions.md`, `tests/unit/test_knowledge_graph_fr190.py` |

### 70. CAP-70 Knowledge Graph Graduation (FR-191)

Graduates the plausible_wrong_answer trap in the Scripture Knowledge Graph in .github/copilot-instructions.md, based on 4 confirmed diary occurrences (FR-165, FR-164, FR-184, FR-185). Refines description from variant-specific ("Silent fallback") to pattern-general ("Output passes shape check but is semantically wrong → add assertion beyond type validation").

**Feature Request:** FR-191

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-188 | plausible_wrong_answer trap present in Scripture traps section with exact text, old description removed, no existing traps/cures/process entries changed | `.github/copilot-instructions.md`, `tests/unit/test_knowledge_graph_fr191.py` |

### 71. CAP-71 Release Changelog Sync Gate

Three-layer enforcement preventing changelog release drift: pre-commit hook blocks version bump with orphaned fragments, atomic release script enforces correct ordering, CI tag-push job validates tag-to-changelog alignment.

**Feature Request:** FR-192

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-189 | Pre-commit hook `changelog-release-sync` runs `check_changelog_release_sync.py` which blocks commit when pyproject.toml version field is changed in staged diff AND changelog/unreleased/ contains *.md files (excluding .gitkeep); allows commit when version unchanged or unreleased/ is empty; lists orphaned fragment names in error output. | `scripts/check_changelog_release_sync.py`, `.pre-commit-config.yaml`, `tests/unit/test_changelog_release_sync.py` |
| REQ-YG-190 | Atomic release script `scripts/release.sh` validates unreleased/ has fragments, freezes them to changelog/{VERSION}/, bumps pyproject.toml version, regenerates CHANGELOG.md via aggregate_changelog.py, commits with -F (file-based message to avoid dquote trap), and creates git tag; reference/release-checklist.md documents release.sh as canonical command. | `scripts/release.sh`, `reference/release-checklist.md`, `tests/unit/test_changelog_release_sync.py` |
| REQ-YG-191 | CI `release-hygiene` job in commitlint.yml triggers on tag push (v*), verifies changelog/{VERSION}/ directory exists for the tagged version, and checks for orphaned fragments in changelog/unreleased/; job has if-condition restricting execution to tag push events only. | `.github/workflows/commitlint.yml`, `tests/unit/test_changelog_release_sync.py` |

### 72. CAP-72 Knowledge Graph Mass Graduation (FR-193)

Graduates 8 recurring patterns from diary analysis into the Scripture Knowledge Graph in .github/copilot-instructions.md. Adds 5 process heuristics (automation_inherits_doctrine, changelog_ci_gate, detection_without_enforcement, enforcement_at_merge_boundary, mixed_commits_erode_auditability) and creates a new seeds: section with 3 forward-looking patterns (inquisitor_auto_escalation, req_coverage_as_universal_gate, verification_checkpoint_primitive). Based on Philosopher analysis of 220+ diary entries.

**Feature Request:** FR-193

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-192 | 5 process heuristics added to process: section, new seeds: section added with 3 seed patterns, changelog_ci_gate in process (not seeds), all descriptions are one-liners following key: "trigger → redirect" convention, no existing Knowledge Graph entries changed | `.github/copilot-instructions.md`, `tests/unit/test_knowledge_graph_fr193.py` |

### 73. CAP-73 Philosopher Challenge Node (FR-195)

Adds distill + challenge copilot nodes with unwrap gates to the philosopher graph, creating an adversarial quality gate (devil's advocate) that prevents weak or coincidental patterns from reaching .chaplain/inbox/. Implements ChallengeVerdict Pydantic model, unwrap_distill/unwrap_challenge tool functions, conditional routing on verdict, and distill/challenge prompt YAMLs.

**Feature Request:** FR-195

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-193 | ChallengeVerdict model with verdict/confidence/objections/surviving_arguments, unwrap_distill parses CopilotResult into Proposal or None, unwrap_challenge parses CopilotResult into ChallengeVerdict, write_proposals reads top_candidate, graph topology with conditional edges, distill/challenge prompts, reflect enriched with challenge context | `examples/philosopher/models.py`, `examples/philosopher/tools.py`, `examples/philosopher/graph.yaml`, `examples/philosopher/prompts/`, `tests/unit/test_philosopher.py` |

### 74. CAP-74 FSM Scripture CLAUDE.md (FR-199)

Upgrades fsm/CLAUDE.md (statemachine-engine/CLAUDE.md) from a four-line YAGNI/TDD/DRY/KISS summary to the full YAMLGraph doctrine: The 10 Commandments, Sermon of the Chaplain, Rite of Correction, Agents' prayer, Knowledge Graph of the Diary, FSM path/package adaptation table, and Anti-patterns table. All existing FSM-specific sections (Architecture, Usage Patterns, Communication Architecture, Troubleshooting) are preserved intact. Eliminates doctrine drift between the two codebases that share CI, Scripture, and release flow.

**Feature Request:** FR-199

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-195 | fsm/CLAUDE.md contains all 10 Commandments verbatim, Sermon of the Chaplain, Rite of Correction, Agents' prayer, Knowledge Graph of the Diary (including the_one_law, traps, cures, process, seeds sections), FSM path/package adaptation table mapping yamlgraph constructs to FSM equivalents, Anti-patterns table with FSM-specific wrong/correct pairs, all existing FSM sections preserved, four-line YAGNI/TDD/DRY/KISS block replaced (not duplicated) | `fsm/CLAUDE.md`, `tests/unit/test_fsm_claude_md_doctrine.py` |

### 75. CAP-75 Portable Chaplain (FR-196)

PythonToolConfig supports a `path` field for file-path-based tool loading via importlib.util.spec_from_file_location(). When graph context is available, relative paths resolve from graph root and are confined to graph root. Enables .chaplain/ directory portability by bypassing dotted-package import restrictions with deterministic graph-scoped loading.

**Feature Request:** FR-196

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-196 | PythonToolConfig supports path field (mutually exclusive with module) for file-path-based Python tool loading via spec_from_file_location; path resolves relative to graph_root when provided and both relative/absolute out-of-root paths are rejected; validation rejects both-set and neither-set; parse_python_tools accepts path or module in YAML tool definitions | `yamlgraph/tools/python_tool.py`, `tests/unit/test_python_nodes.py` |
| REQ-YG-529 | All chaplain graph configs under .chaplain/graphs/ compile and their declared python tools resolve at load time (FR-699); the philosopher write_diary proxy resolves .chaplain/lib/diary.py; verified by unit witness tests so loader-semantics changes condemn config drift at pre-commit instead of pipeline runtime | `.chaplain/graphs`, `tests/unit/test_chaplain_graph_compile.py` |

### 76. CAP-76 Horoscope Demo

Parallel daily horoscope generator using map node with static over: list, producing a single Markdown document via exports. Pure YAML, zero Python.

**Feature Request:** FR-201

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-197 | Horoscope demo: map node fans out over 12 zodiac signs in parallel, collects readings, assembles into Markdown document with exports section. Pure YAML graph with co-located prompts, date as runtime variable. | `examples/demos/horoscope` |

### 77. CAP-77 Image Generation Pipeline

End-to-end style-driven image generation pipeline: concept generation via LLM, prompt generation via batch_image_prompts subgraph, save to file, and image generation via Replicate z-image with sidecar files and best-effort EXIF.

**Feature Request:** FR-202

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-198 | Image pipeline graph chains generate_concepts (LLM) → batch_image_prompts (subgraph) → save_prompts (Python tool writing prompts.txt) → generate_images (Python tool calling Replicate z-image with sidecar .txt files and best-effort EXIF embedding). | `examples/image_pipeline`, `tests/unit/test_image_pipeline.py` |

### 78. CAP-78 .fi Domain Crawl Demo

Multi-stage pipeline crawling .fi country-level domains: LLM query planning, DuckDuckGo seed discovery, parallel page crawling via map node, and LLM sitemap summarisation. Demonstrates HTTP tool nodes with map fan-out.

**Feature Request:** FR-205

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-199 | .fi domain crawl demo: plan node produces search queries (parse_json), discover node filters results to .fi TLD, map node crawls pages in parallel (max_items: 10), summarise node produces sitemap overview. crawl_page handles errors gracefully, returns structured dict with title/links/snippet. No new dependencies — uses digest + websearch extras. | `examples/demos/fi-domain-crawl`, `tests/unit/test_fi_domain_crawl.py` |

### 79. CAP-79 Demo Proof Gate

CI gate and pre-commit hook requiring demo-output.log artifact when demos are created or modified, and validating log semantics (not only presence): logs must be non-empty, contain success evidence, and contain no fatal execution markers. Enforces Commandment 2 ("demonstrate with example") at the merge boundary.

**Feature Request:** FR-206

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-200 | demo-gate CI job in commitlint.yml extracts changed demo directories from git diff (excluding demo-output.log itself), verifies each has a demo-output.log in the diff, then validates content semantics using shared rules: reject empty logs, reject fatal execution markers (for example Node .* failed, [ERROR], ❌ Error:, exit code [1-9]), and reject logs with no success evidence; exits 1 on violations and 0 when no demos changed; job-level if condition restricts to feat/fix PR titles; uses actions/checkout@v4 with fetch-depth: 0; pre-commit hook demo-proof-check calls scripts/check_demo_proof.sh with identical semantic rules; .gitignore negates *.log for examples/demos/*/demo-output.log; CLAUDE.md documents demo-gate in branch protection section; enforcer Phase 2 prompt instructs capturing demo-output.log | `scripts/check_demo_proof.sh`, `scripts/demo_log_semantics.sh`, `.github/workflows/commitlint.yml`, `.pre-commit-config.yaml`, `.gitignore`, `CLAUDE.md`, `.chaplain/graphs/watcher-enforce/prompts/enforce-test-demo.yaml`, `tests/unit/test_ci_demo_proof_gate.py` |

### 81. CAP-81 A2A Protocol Server

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

### 82. CAP-82 Block AI Co-Author Trailers

Commit-msg hook that detects and blocks AI agent Co-authored-by trailers (Copilot, Claude, ChatGPT, Gemini, GPT-*) before they enter the repository. Prints the offending line(s) and penance liturgy, then exits 1 to block the commit. Human co-authors and clean messages pass silently.

**Feature Request:** FR-212

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-215 | block_ai_coauthor.py commit-msg hook: regex-detects AI agent trailers, exits 1 with offending line + penance liturgy; exits 0 for clean and human-only messages; registered as block-ai-coauthor in pre-commit-config at commit-msg stage before final-summary | `scripts/block_ai_coauthor.py`, `.pre-commit-config.yaml`, `tests/unit/test_precommit_hooks.py` |

### 83. CAP-83 Research Agent Demo

5-step agentic research demo: extract intent (llm) → plan research (agent) → execute research (agent) → validate findings (llm) → synthesize report (llm). Demonstrates bounded agent pipelines with least-privilege tool assignment, explicit validation nodes, and structured Pydantic schemas.

**Feature Request:** FR-215

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-217 | Research agent demo: 5-node graph with extract_intent (llm, Pydantic schema), plan_research (agent, discovery tools only), execute_research (agent, all tools), validate_findings (llm, Pydantic schema with gaps/confidence), synthesize_report (llm). Linear flow START→END. prompts_relative: true with local prompts/ directory. Shell tools use placeholder variables. Graph passes yamlgraph lint. | `examples/demos/research-agent`, `tests/unit/test_research_agent_demo.py` |

### 84. CAP-84 Import-Linter Architectural Boundary Enforcement

Mechanical enforcement of the three-layer architecture (Presentation → Logic → Side Effects) via import-linter contracts. Prevents silent degradation of module boundaries by blocking imports that violate declared layer dependencies at pre-commit and CI.

**Feature Request:** FR-218

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-218 | .importlinter config at repo root declares a layers contract with three layers: Presentation (cli), Logic (graph_loader, node_factory, executor, linter, edge_compiler, node_compiler, map_compiler, routing, graph_cache, schema_loader, data_loader, discovery, executor_async, interactive_tool), Side Effects (tools, models, utils, config, constants, storage, contrib, executor_base, error_handlers, verification). lint-imports exits 0 on the current codebase. Pre-commit hook and CI step enforce the contract at every commit and PR. | `.importlinter`, `.pre-commit-config.yaml`, `.github/workflows/workflow.yml`, `tests/unit/test_import_linter.py` |

### 85. CAP-85 Dependency Rationale Audit

Audit script that verifies every pyproject.toml dependency (core and optional) has a documented rationale in docs/dependency-rationale.yaml. Follows the noqa_coverage.py registry-audit pattern. Reports undocumented packages and exits 1 in --strict mode. Registered as pre-commit hook.

**Feature Request:** FR-219

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-219 | dependency_rationale.py parses pyproject.toml core and optional dependencies (stripping version specifiers and extras), loads rationale entries from docs/dependency-rationale.yaml, reports undocumented packages in summary mode, exits 1 in --strict when gaps exist, --detail prints all entries; registered as dependency-rationale pre-commit hook | `scripts/dependency_rationale.py`, `docs/dependency-rationale.yaml`, `.pre-commit-config.yaml`, `tests/unit/test_dependency_rationale.py` |

### 86. CAP-86 Ruff Security Rules

Ruff S ruleset (flake8-bandit) enabled in pyproject.toml for automated security linting. All 7 existing violations (S104, S602, S603, S607, S701) suppressed with documented noqa confessions. New security-sensitive code patterns are automatically flagged at lint time.

**Feature Request:** FR-222

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-222 | Ruff S ruleset enabled in [tool.ruff.lint] select. All 7 existing violations suppressed with # noqa and documented in docs/confessions.md (CONF-005 through CONF-009, CONF-035, CONF-036). ruff check --select S yamlgraph/ exits 0. New security-sensitive code is automatically flagged. | `pyproject.toml`, `docs/confessions.md`, `tests/unit/test_ruff_security.py` |

### 87. CAP-87 Ruff C901 Cognitive Complexity Gate

Enables ruff C901 (mccabe cognitive complexity) in the lint pipeline at threshold 15, closing the gap where radon CC (grade D ≥ 21) misses deeply nested functions. Functions above threshold are suppressed with noqa and documented in docs/confessions.md. CI inherits the rule via existing ruff check yamlgraph/.

**Feature Request:** FR-221

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-221 | C901 in ruff select with max-complexity = 15 in [tool.ruff.lint.mccabe]; functions above threshold suppressed with # noqa: C901 and documented in docs/confessions.md; CI inherits via existing ruff check yamlgraph/ | `pyproject.toml`, `docs/confessions.md`, `tests/unit/test_ruff_c901_gate.py` |

### 88. CAP-88 Google/Vertex Thinking Budget Support

Extends thinking_budget support to google and vertex providers. ChatGoogleGenerativeAI (langchain-google-genai 4.2.0+) accepts thinking_budget as a first-class constructor parameter. Schema validator relaxed to accept -1 (Google automatic mode) and any positive integer. Linter checks W071-1/2/4 scoped to Anthropic only; W071-3 extended with Gemini 2.5+ and Gemini 3 model substrings.

**Feature Request:** FR-230

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-230 | thinking_budget accepted by create_llm for anthropic, google, and vertex; raises ValueError for other providers; _create_google_llm and _create_vertex_llm forward thinking_budget kwarg to ChatGoogleGenerativeAI when non-None; temperature not overridden for google/vertex; schema NodeConfig.thinking_budget accepts -1 (Google auto), rejects < -1; GraphConfigSchema defaults validator aligned; linter W071-1/2/4 scoped to anthropic; linter W071-3 THINKING_CAPABLE_MODELS includes gemini-2.5 and gemini-3 substrings | `yamlgraph/utils/llm_factory.py`, `yamlgraph/models/graph_schema.py`, `yamlgraph/linter/checks_providers.py`, `tests/unit/test_fr230_google_vertex_thinking.py` |

### 89. CAP-89 Execution Timing Callback

LangChain callback handler tracking wall-clock duration of each LLM call in a graph run. Follows the same injection pattern as TokenUsageCallbackHandler. CLI --timing flag displays timing summary after execution.

**Feature Request:** FR-231

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-231 | ExecutionTimingCallbackHandler tracks per-call and total wall-clock LLM duration via on_llm_start/on_llm_end callbacks using time.monotonic; summary() returns total_duration_s, call_count, mean_duration_s; CLI --timing flag injects callback and prints timing summary | `yamlgraph/utils/timing_tracker.py`, `yamlgraph/cli/graph_commands.py`, `yamlgraph/cli/__init__.py`, `tests/unit/test_timing_tracker.py` |

### 90. CAP-90 Graph Bench Command

CLI command that runs a graph across multiple provider/model combinations and displays a side-by-side comparison table of execution time, token usage, and output. Supports --runs N for repetition, --export for JSON output, and --full for detailed output per model.

**Feature Request:** FR-231

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-232 | yamlgraph graph bench command accepts --models provider/model specs, --runs N, --export path, --full; runs graph against each model; captures timing and token usage per model; displays comparison table; per-model errors reported gracefully without aborting other models; BenchResult Pydantic model for structured results | `yamlgraph/cli/bench_commands.py`, `yamlgraph/cli/graph_commands.py`, `yamlgraph/cli/__init__.py`, `tests/unit/test_bench_command.py` |

### 91. CAP-91 Race Node Type

A type: race node that fires the same prompt to N provider/model candidates concurrently via ThreadPoolExecutor and returns the first successful result. Enables sub-second LLM responses for latency-sensitive graphs by hedging across providers. Includes schema validation (≥2 candidates, each with provider or model), _race_winner metadata in state, graph lint checks (E301–E304), and on_error policy support for all-candidates-fail.

**Feature Request:** FR-232

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-233 | type: race node fires prompt to all candidates concurrently using ThreadPoolExecutor; returns first successful result (not just first to complete); remaining candidates cancelled; all-fail triggers on_error policy; _race_winner metadata in state; candidates validated ≥2 entries each with provider or model; graph lint E301-E304; structured output works; NodeType.RACE in constants; NODE_TYPE_HANDLERS registered | `yamlgraph/node_factory/race_node.py`, `yamlgraph/constants.py`, `yamlgraph/compile/node_compiler.py`, `yamlgraph/models/graph_schema.py`, `yamlgraph/models/state_builder.py`, `yamlgraph/linter/patterns/race.py`, `yamlgraph/linter/checks.py`, `tests/unit/test_race_node.py`, `tests/unit/test_linter_patterns_race.py` |
| REQ-YG-269 | Race node must not block on losing candidates after a winner is found. ThreadPoolExecutor shut down with wait=False, cancel_futures=True after returning winner. No with ThreadPoolExecutor context manager pattern. Loser threads terminate naturally; their results are discarded. | `yamlgraph/node_factory/race_node.py`, `tests/unit/test_race_node.py` |

### 92. CAP-92 Chatterbox TTS Demo

Multilingual text-to-speech demo using map node fan-out over 5 languages, Chatterbox Multilingual TTS for audio synthesis, and structured YAML prompts. Produces WAV files for en, es, fi, sv, de.

**Feature Request:** FR-233

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-234 | Chatterbox TTS demo: map node fans out over 5 languages (en, es, fi, sv, de), collects translations via structured output, synthesizes to WAV files via synthesize_audio python tool with Chatterbox Multilingual TTS. Auto-detects CUDA/CPU. Optional dependency chatterbox-tts. | `examples/demos/chatterbox` |

### 93. CAP-93 Chatterbox Voice Clone Demo

Voice cloning demo consolidated into examples/demos/chatterbox/ (FR-237). synthesize_cloned_audio in tools.py uses ChatterboxTTS (chatterbox.tts) with a caller-supplied reference audio clip (audio_prompt_path). Single-path synthesis: text + voice_prompt_path → output.wav. Device auto-detection follows cuda > mps > cpu. clone.yaml provides graph-based invocation; speak.py provides a standalone CLI. Supersedes chatterbox_clone/ (FR-236).

**Feature Request:** FR-237

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-235 | Chatterbox voice cloning demo: synthesize_cloned_audio in examples/demos/chatterbox/tools.py accepts text and voice_prompt_path, synthesizes to WAV via ChatterboxTTS (not ChatterboxMultilingualTTS). Device selection follows cuda > mps > cpu priority chain. clone.yaml graph and speak.py CLI both use this tool. Optional dependency chatterbox-tts. | `examples/demos/chatterbox` |
| REQ-YG-238 | Chatterbox speak CLI: speak.py accepts --ref (reference WAV, required) and positional text; validates ref exists (exit 1 on missing); calls ChatterboxTTS.generate() without language_id; writes to outputs/chatterbox/speak.wav; prints output path to stdout. | `examples/demos/chatterbox` |

### 94. CAP-94 Compile-Time Pipeline Templates

A type: pipeline meta-node that defines a sequence of stages once, iterates over a list of items, and expands to concrete nodes + edges before graph compilation. Eliminates repetitive boilerplate in multi-chapter, multi-phase graphs by 80%+. Includes {item.field} interpolation for stage configs, sequential intra-item and inter-item chaining, external edge rewriting, and linter validation (E401–E404).

**Feature Request:** FR-235

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-236 | type: pipeline meta-node expands at compile time into concrete nodes and sequential edges; {item.field} interpolation in prompt, variables, state_key; non-string fields copied verbatim; external edges rewritten to first/last expanded node; lint E401 (empty items), E402 (empty stages), E403 (unresolved item refs), E404 (missing name); NodeType.PIPELINE in constants; VALID_NODE_TYPES includes pipeline; expansion called in graph_loader after expand_interactive_tools | `yamlgraph/compile/pipeline_template.py`, `yamlgraph/constants.py`, `yamlgraph/compile/graph_loader.py`, `yamlgraph/linter/checks.py`, `yamlgraph/linter/patterns/pipeline.py`, `yamlgraph/linter/graph_linter.py`, `tests/unit/test_pipeline_template.py`, `tests/unit/test_linter_patterns_pipeline.py` |

### 95. CAP-95 Parallel Fan-Out Edges

Parallel fan-out edges allow a single node to fan out to multiple target nodes that execute concurrently, expressed as to: [a, b, c] without type: conditional. The edge compiler adds one add_edge() call per target. Handles interrupt node redirect (_prepare), map node targets (conditional edge with map function), START fan-out (conditional entry point), and END targets. Conditional routing (type: conditional) remains unchanged.

**Feature Request:** FR-234

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-237 | Parallel fan-out edges: to: [a, b, c] without type: conditional compiles as parallel fan-out via multiple add_edge() calls; handles interrupt node redirect to _prepare; handles map node targets via conditional edges; START fan-out uses conditional entry point; existing conditional routing with type: conditional unchanged | `yamlgraph/compile/edge_compiler.py`, `tests/unit/test_parallel_fanout_edges.py` |

### 96. CAP-96 Per-Node Timeout

Per-node timeout bounding for map branches and all node types via ThreadPoolExecutor. Optional float timeout field on NodeConfig wraps node execution in a one-shot ThreadPoolExecutor; on concurrent.futures.TimeoutError a PipelineError with error_type=TIMEOUT_ERROR is returned. Map branches honour timeout in wrap_for_reducer; non-map nodes (llm, router, tool_call, python, agent, race) honour timeout via _maybe_wrap_timeout in node_compiler. Lint warning W203 emitted when a map node contains an agent sub-node without timeout.

**Feature Request:** FR-069

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-078 | Per-node timeout: optional float timeout field on NodeConfig validated as positive; map branch timeout via wrap_for_reducer with ThreadPoolExecutor; non-map node timeout via _maybe_wrap_timeout in node_compiler handlers; TIMEOUT_ERROR error type in ErrorType enum; from_exception classification unchanged (callers pass error_type explicitly); lint warning W203 for map+agent without timeout; except concurrent.futures.TimeoutError before except Exception in both paths | `yamlgraph/compile/map_compiler.py`, `yamlgraph/compile/node_compiler.py`, `yamlgraph/models/graph_schema.py`, `yamlgraph/models/schemas.py`, `yamlgraph/linter/patterns/map.py`, `tests/unit/test_map_node_timeout.py` |

### 98. CAP-98 Pipeline Accumulated State

User-configurable reducers in the YAML state: section and documented accumulated state pattern for pipelines. REDUCER_MAP maps "add", "last_value", "sorted_add" to their functions. parse_state_config() handles dict-syntax {type: str, reducer: str}. generate_typeddict_code() extracts type strings from dict-syntax entries. reference/graph-yaml.md documents the glossary accumulation pattern, sequential execution constraint, and W021 skip_if_exists: false requirement.

**Feature Request:** FR-238

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-241 | parse_state_config() handles dict-syntax state definitions {type: str, reducer: str}; REDUCER_MAP maps "add", "last_value", "sorted_add" to their functions; unknown reducer names log a warning; dict syntax without reducer key works as type-only; generate_typeddict_code() extracts type string from dict-syntax entries via CODEGEN_TYPE_MAP; reference/graph-yaml.md documents accumulated state pattern with glossary example, sequential execution constraint, and W021 skip_if_exists: false requirement | `yamlgraph/models/state_builder.py`, `reference/graph-yaml.md`, `tests/unit/test_state_builder_reducers.py` |

### 99. CAP-99 Race and Pipeline Node Type Documentation

Reference documentation for type: race (FR-232) and type: pipeline (FR-235) node types in reference/graph-yaml.md and reference/getting-started.md. Ensures graph authors can discover and configure these node types through the canonical reference docs.

**Feature Request:** FR-237

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-240 | reference/getting-started.md node type table includes race and pipeline rows; reference/graph-yaml.md has dedicated sections for type: race (purpose, candidates, timeout, state_key, _race_winner, on_error, example) and type: pipeline (purpose, items, stages, expansion semantics, {item.field} interpolation, example); doc examples match demo YAMLs | `reference/graph-yaml.md`, `reference/getting-started.md`, `tests/unit/test_race_pipeline_docs.py` |

### 100. CAP-100 Chatterbox Multilingual CLI

speak.py --lang flag routes to ChatterboxMultilingualTTS for non-English language codes (fi, sv, de, es, …). English path (--lang en, default) preserves the voice-cloning behaviour using ChatterboxTTS + --ref. --ref is incompatible with non-English lang and raises a clear error. Output is always outputs/chatterbox/speak.wav regardless of path. (FR-239)

**Feature Request:** FR-239

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-242 | Chatterbox multilingual CLI: speak.py --lang <code> routes to ChatterboxMultilingualTTS for non-English codes; --ref incompatible with non-English lang (parser.error); --lang en (default) preserves voice-cloning path requiring --ref; output always outputs/chatterbox/speak.wav. | `examples/demos/chatterbox` |

### 101. CAP-101 A2A Consumer Contrib Client

A2A consumer functionality via yamlgraph.contrib.a2a_client.send_a2a_message(), invoked as a type: python node. Sends Jinja2-templated message to external A2A agent via HTTP JSON-RPC (message/send), extracts text artifacts from the response, and returns {"response": text}. Supports timeout, Agent Card fetch, skill validation, and SSE streaming. Configuration via variables: on the python node. Replaces dedicated type: a2a_call (FR-253).

**Feature Request:** FR-240

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-243 | yamlgraph.contrib.a2a_client.send_a2a_message() sends Jinja2-templated message to external A2A agent URL via HTTP JSON-RPC message/send; extracts text artifacts from response; returns {"response": text}; invoked via type: python node with variables: for agent_url, message/message_template, skill, streaming, timeout; supports Agent Card fetch, skill validation, SSE streaming; uses httpx for sync and A2AClient for streaming transport | `yamlgraph/contrib/a2a_client.py`, `yamlgraph/tools/python_tool.py`, `tests/unit/test_a2a_contrib_client.py` |

### 102. CAP-102 Complete Worktree Teardown Self-Heal

Complete worktree teardown self-heal: validate_editable_install() probes import health via sys.executable; enforce_worktree.sh cleanup validates import yamlgraph after .pth cleaning and self-heals with pip install -e; bugfix_worktree.sh reaches FR-174 parity with venv health, symlink validation, .pth cleaning, import validation, and self-heal in cleanup.

**Feature Request:** FR-241

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-244 | validate_editable_install() in worktree_helpers.py probes import health via sys.executable; enforce_worktree.sh cleanup validates import yamlgraph after .pth cleaning and self-heals with pip install -e; bugfix_worktree.sh has FR-174 parity: validate_venv_health before symlink, validate_venv_symlink after symlink, clean_stale_pth_entries in cleanup, import validation, and pip install -e self-heal | `yamlgraph/utils/worktree_helpers`, `scripts/enforce_worktree.sh`, `scripts/bugfix_worktree.sh`, `tests/unit/test_worktree_teardown_self_heal` |

### 103. CAP-103 A2A SDK v1.0 Compatibility

Upgrade a2a-sdk dependency from v0.3 to v1.0 and fix all breaking changes. Protobuf-based types replace Pydantic models; Part construction uses member-name discriminator (no 'kind' field); TextPart class removed; Role/TaskState enums use SCREAMING_SNAKE_CASE; A2AStarletteApplication replaced by Starlette + route factories; EventQueue.close() removed; AgentCard.url field removed; InMemoryTaskStore API requires ServerCallContext; card JSON serialization uses MessageToDict.

**Feature Request:** FR-244

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-245 | A2A SDK v1.0 compatibility: protobuf-based types replace Pydantic models; Part(text=...) replaces Part(root=TextPart(text=...)); TextPart removed; Role.ROLE_USER/ROLE_AGENT replaces Role.user/agent; TaskState.TASK_STATE_* replaces TaskState.*; A2AStarletteApplication replaced by Starlette + create_jsonrpc_routes/create_agent_card_routes; EventQueue.close() removed; AgentCard.url field removed; InMemoryTaskStore.save/get require ServerCallContext; DefaultRequestHandler requires agent_card parameter; kind discriminator removed from JSON-RPC part payloads (member-name discriminator); contrib/a2a_client.py extraction uses key-presence check; a2a_commands.py uses MessageToDict for card JSON serialization | `yamlgraph/a2a/server.py`, `yamlgraph/a2a/message.py`, `yamlgraph/contrib/a2a_client.py`, `yamlgraph/cli/a2a_commands.py`, `tests/unit/test_a2a_server.py`, `tests/unit/test_a2a_message.py`, `tests/unit/test_a2a_commands.py`, `tests/unit/test_a2a_contrib_client.py` |

### 104. CAP-104 A2A Server Reference Documentation

User-facing reference documentation for the A2A protocol server (FR-208/209/225, CAP-81). Covers quickstart, CLI commands, Agent Card generation, message parsing, task lifecycle, error mapping, interrupts, authentication, deployment patterns, and MCP relationship. Also updates reference/cli.md with a2a subcommands and reference/README.md index.

**Feature Request:** FR-246

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-246 | reference/a2a-server.md created with 10 sections: Quickstart, CLI Commands, Agent Card Generation, Message-to-State Mapping, Task Lifecycle, Error Mapping, Interrupt/Human-in-Loop, Authentication, Deployment Patterns, Relationship to MCP Server; reference/cli.md updated with a2a serve and a2a card subcommands; reference/README.md links to a2a-server.md; all examples verified against a2a_server.py, a2a_message.py, cli/a2a_commands.py | `reference/a2a-server.md`, `reference/cli.md`, `tests/unit/test_a2a_server_docs.py` |

### 105. CAP-105 A2A Consumer Phase 2 — Agent Card, Skill Selection & Streaming

A2A consumer features in yamlgraph.contrib.a2a_client: Agent Card discovery via sync httpx.get() to /.well-known/agent.json, ContextVar-scoped caching per graph invocation, skill selection validated against Agent Card skills at runtime, and SSE streaming via A2AClient.send_message_streaming() in a dedicated thread. Replaces dedicated a2a_call node type linter checks (W901/E904) with runtime validation in contrib function (FR-253).

**Feature Request:** FR-248

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-250 | send_a2a_message() fetches Agent Card via sync httpx.get() to {agent_url}/.well-known/agent.json; parsed into SDK AgentCard model via ParseDict; cached per agent_url within graph invocation using ContextVar; cache isolated across invocations; timeout configurable | `yamlgraph/contrib/a2a_client.py`, `tests/unit/test_a2a_contrib_client.py` |
| REQ-YG-251 | skill parameter in state selects a specific agent skill; validated against Agent Card skills at runtime; ValueError raised on skill ID miss with available skills listed in error message; no card fetch when skill not specified | `yamlgraph/contrib/a2a_client.py`, `tests/unit/test_a2a_contrib_client.py` |
| REQ-YG-252 | streaming: true in state uses A2AClient.send_message_streaming() via dedicated thread with own event loop; requires card.capabilities.streaming == True; result returned as complete string; streaming events logged at DEBUG level; transport-only (not FR-030 graph-level streaming) | `yamlgraph/contrib/a2a_client.py`, `tests/unit/test_a2a_contrib_client.py` |
| REQ-YG-253 | Dedicated type: a2a_call node type replaced by type: python + yamlgraph.contrib.a2a_client contrib function; NodeType.A2A_CALL removed from constants; a2a_nodes.py and linter/patterns/a2a.py deleted; W901/E904 linter checks removed (skill/streaming validated at runtime in contrib); FR-252 enables variables: resolution on type: python nodes | `yamlgraph/contrib/a2a_client.py`, `yamlgraph/tools/python_tool.py`, `tests/unit/test_a2a_contrib_client.py` |

### 106. CAP-106 GitHub Issues Remote Inbox

watch.sh syncs open GitHub Issues labeled 'chaplain' into the local inbox, removes the label after import, and closes the issue with a commit reference on successful enforcement. Gracefully degrades when gh CLI is unavailable.

**Feature Request:** FR-243

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-247 | GitHub Issues remote inbox: watch.sh polls for open issues labeled 'chaplain' via two-pass gh CLI (list numbers, then view each), writes .chaplain/inbox/gh-{number}.md, removes the label after import, initializes EXIT_CODE=1 as sentinel before enforcement branches, and closes the originating issue with commit hash on EXIT_CODE=0. Sync is silently skipped when gh is not installed or not authenticated. CLAUDE.md and copilot-instructions.md document remote submission. | `.chaplain/watch.sh`, `CLAUDE.md`, `.github/copilot-instructions.md`, `tests/unit/test_github_issues_remote_inbox` |

### 107. CAP-107 Guardrails Pattern Documentation

Document the input guardrails pattern (echo → validate → respond) as Pattern 11 in reference/patterns.md. References the existing examples/openai_proxy/ implementation as a production example. Updates examples/README.md with a Guardrails category.

**Feature Request:** FR-249

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-254 | Pattern 11 "Input Guardrails" in reference/patterns.md documents the echo → validate → respond pipeline with Problem/Solution sections, valid YAML graph example, Python tool implementations, prompt template, Key Points table, and Related links referencing examples/openai_proxy/; examples/README.md includes a Guardrails category in "By Feature" section | `reference/patterns.md`, `examples/README.md`, `tests/unit/test_guardrails_pattern_docs.py` |

### 108. CAP-108 Changelog REQ Cross-Validation Gate

Validates that changelog fragment req: front-matter values reference correct requirement IDs from the capabilities registry. Mechanical pre-filter for single-REQ capabilities; LLM classifier (Haiku) for multi-REQ capabilities where mechanical disambiguation is impossible.

**Feature Request:** FR-247

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-255 | Changelog REQ cross-validation gate: scripts/check_changelog_req.py parses YAML front-matter req: from changelog/unreleased/*.md, validates each REQ-YG-XXX exists in capabilities/CAP-*.yaml via direct id: lookup (rejects phantoms), skips fragments without req: field; single-REQ CAPs pass mechanically; multi-REQ CAPs deferred to LLM graph graphs/enforcement/changelog-req-check.yaml (Haiku, temperature 0); --strict exits non-zero on failure; --skip-llm runs mechanical-only; pre-commit hook and CI job wired | `scripts/check_changelog_req.py`, `graphs/enforcement/changelog-req-check.yaml`, `.pre-commit-config.yaml`, `.github/workflows/commitlint.yml` |

### 109. CAP-109 Harden GitHub Issues Remote Inbox

Author allowlisting, body size cap (10,000 chars), and forensic author audit header for the GitHub Issues remote inbox (FR-243 hardening). Prevents prompt injection via untrusted issue bodies.

**Feature Request:** FR-251

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-256 | watch.sh gates GitHub Issue import on .chaplain/allowed-authors.txt (one login per line); issues from unlisted authors are skipped with warning, label retained; when file absent all authors accepted; body truncated at BODY_SIZE_CAP (10000) with warning; every imported file starts with <!-- author: @login --> audit header; author login fetched before title/body for early rejection (FR-251) | `.chaplain/watch.sh`, `.chaplain/allowed-authors.txt`, `tests/unit/test_harden_remote_inbox.py` |

### 110. CAP-110 Diary Index Graph

Demo graph that reads diary entries from docs/diary/*.md, extracts structured data (traps, heuristics, seeds, FR references) via map+llm, and produces a cross-reference index at docs/diary-index.yaml. Deterministic Python aggregation, no LLM for counting.

**Feature Request:** FR-254

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-257 | Diary index graph: map node fans out over diary files, LLM extracts traps/heuristics/seeds/FR refs per entry, deterministic Python aggregate_index() builds cross-reference index (traps_index sorted by frequency, seeds_index with dedup, fr_index reverse mapping, heuristics_candidates with 2+ threshold, statistics by category). write_index() persists to docs/diary-index.yaml. Graph lints clean. Inline schema on extraction prompt. model: claude-haiku-4-5 for cost. | `examples/demos/diary_index` |

### 111. CAP-111 Shared Graph Invocation

Shared invoke_graph() function in graph_loader eliminates duplicated graph invocation logic across MCP and A2A servers (FR-255).

**Feature Request:** FR-255

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-258 | invoke_graph(path, variables, config) in graph_loader.py: loads config, compiles graph, invokes synchronously with optional LangGraph run config. MCP and A2A servers delegate to this shared function. | `graph_loader`, `mcp_server`, `a2a_server` |

### 113. CAP-113 Chaplain Research Step

Research guidance in the active watcher-plan runtime. The unified planning step and watcher-plan research prompt gather strategic evidence (existing abstractions, diary precedents, usage evidence, classification signal) so Judge can distinguish technically feasible from strategically warranted (FR-257).

**Feature Request:** FR-257

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-260 | Unified plan step in `.chaplain/graphs/watcher-plan/step-plan-unified.yaml` includes explicit research guidance, while `.chaplain/graphs/watcher-plan/prompts/research.yaml` preserves strategic research instructions (existing abstraction scan, diary precedent check, usage evidence, classification signal); judge prompt in watcher-plan includes strategic classification criteria (framework primitive / contrib / pattern documentation / reject) (FR-257). | `.chaplain/graphs/watcher-plan/step-plan-unified.yaml`, `.chaplain/graphs/watcher-plan/prompts/research.yaml`, `.chaplain/graphs/watcher-plan/prompts/judge.yaml` |

### 114. CAP-114 Automated Post-Merge Finalization

Shared finalization library and watch.sh integration that automatically creates finalization PRs for recently merged feature PRs, eliminating the manual finalize_merge.sh step from the Chaplain pipeline.

**Feature Request:** FR-258

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-261 | Shared library `.chaplain/lib/finalize_lib.sh` provides `extract_fr_metadata`, `create_changelog_fragment`, `update_fr_status`, and `create_diary_stub` functions; `scripts/finalize_merge.sh` sources the library instead of inlining logic; `watch.sh` detects recently merged PRs via timestamp-based `gh pr list` query, creates finalization PRs with changelog fragment, FR status update, and diary stub, enables auto-merge, and skips already-finalized FRs idempotently | `.chaplain/lib/finalize_lib.sh`, `.chaplain/watch.sh`, `scripts/finalize_merge.sh`, `tests/unit/test_automated_post_merge_finalization` |

### 116. CAP-116 Acceptance Tests Before Enforce

Ensure acceptance tests are authored before enforce execution in the active FSM runtime. Setup creates the worktree, the unified plan step includes acceptance-test authoring instructions, Judge evaluates test evidence, and enforce_session executes against that contract.

**Feature Request:** FR-260

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-263 | `setup` action in watcher-pipeline-v2 creates the worktree before plan; unified plan prompt includes acceptance-test authoring protocol using `@pytest.mark.req` tags and RED commit guidance; judge prompt includes criterion 8 for test evidence evaluation; enforce session prompt explicitly preserves acceptance test assertions as the contract for implementation (FR-260). | `.chaplain/config/watcher-pipeline-v2.yaml`, `.chaplain/graphs/watcher-plan/step-plan-unified.yaml`, `.chaplain/graphs/watcher-plan/prompts/write-acceptance-tests.yaml`, `.chaplain/graphs/watcher-plan/prompts/judge.yaml`, `.chaplain/graphs/watcher-enforce/prompts/enforce-session.yaml`, `.chaplain/lib/worktree.py` |

### 117. CAP-117 Race Node parse_json & Content Normalization

Race node _invoke_candidate normalizes response.content to string via shared normalize_content() in yamlgraph/utils/content.py (handles Anthropic list-of-blocks, OpenAI string, None). Race node supports parse_json: true config — skips output_model resolution at factory time and applies extract_json() after content normalization. agent.py imports from shared utility instead of inlining.

**Feature Request:** FR-264

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-264 | Race node _invoke_candidate normalizes response.content to string via shared normalize_content(); supports parse_json: true skipping output_model and applying extract_json(); agent.py uses shared utility | `yamlgraph/node_factory/race_node.py`, `yamlgraph/utils/content.py`, `yamlgraph/tools/agent.py`, `tests/unit/test_race_node.py` |

### 118. CAP-118 Copilot Node Model Selection

Copilot nodes support model as a top-level node config key, consistent with LLM nodes. Falls back to defaults.model from graph metadata when not specified. cli_flags.model continues to work as the highest-priority override. Priority chain: cli_flags.model > node-level model > defaults.model > omit.

**Feature Request:** FR-266

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-265 | NodeConfig has model: str \| None field; create_copilot_node accepts defaults parameter; _compile_copilot_node passes effective_defaults to factory; model resolution follows cli_flags.model > node-level model > defaults.model > omit; CopilotResult.model reflects the resolved model regardless of source | `yamlgraph/models/graph_schema.py`, `yamlgraph/compile/node_compiler.py`, `yamlgraph/node_factory/copilot_node.py`, `tests/unit/test_copilot_node_model_selection.py` |

### 119. CAP-119 Race Node Timeout Fix

Race node applies exactly one timeout mechanism — its native as_completed(timeout=...). The node compiler does not apply _maybe_wrap_timeout to race nodes (nested ThreadPoolExecutors silently drop the return value). On timeout expiry (no candidate succeeds within deadline), the race node produces a structured PipelineError(TIMEOUT_ERROR) and respects on_error configuration. Without on_error, raises AllCandidatesFailedError.

**Feature Request:** FR-267

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-266 | Race node applies exactly one timeout mechanism — its native as_completed(timeout=...); _compile_race_node must NOT call _maybe_wrap_timeout; on timeout expiry (no candidate succeeds within deadline), race node produces PipelineError(TIMEOUT_ERROR) and respects on_error config; without on_error, raises AllCandidatesFailedError; race timeout is total race deadline, not per-candidate | `yamlgraph/node_factory/race_node.py`, `yamlgraph/compile/node_compiler.py`, `tests/unit/test_race_node.py` |

### 120. CAP-120 CLI Inter-Run State Chaining

--import-state and --export-state flags for yamlgraph graph run enabling external orchestrators to chain graph invocations across shell boundaries while preserving state, including CopilotResult.session_id for copilot session resume.

**Feature Request:** FR-269

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-267 | --import-state loads exported JSON as initial graph state; merge order is graph_config.data < imported < --var-file < --var; missing file prints clear error and exits 1; malformed JSON prints clear error and exits 1 | `yamlgraph/cli/__init__.py`, `yamlgraph/cli/graph_commands.py`, `yamlgraph/cli/helpers.py`, `tests/unit/test_cli_inter_run_state_chaining.py` |
| REQ-YG-268 | --export-state writes full post-run state to explicit JSON path using _serialize_state(); creates parent directories; write failures print clear error and exit 1; CopilotResult.session_id survives round-trip and resolves via resolve_state_expression() | `yamlgraph/cli/graph_commands.py`, `yamlgraph/cli/helpers.py`, `yamlgraph/storage/export.py`, `tests/unit/test_cli_inter_run_state_chaining.py` |

### 121. CAP-121 Async Race Node with Cancellable Candidates

Rewrites the race node from ThreadPoolExecutor to asyncio so losing candidates are cooperatively cancelled at await points after a winner is found. Eliminates orphan HTTP connections, loser billing, and interpreter-exit delays from post-win background threads. _run_coro_sync_safe bridges sync node_fn to the async core without event-loop conflicts under both invoke and ainvoke execution paths.

**Feature Request:** FR-271

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-270 | Race node rewired to asyncio: ThreadPoolExecutor removed; _invoke_candidate_async uses await llm.ainvoke(messages); _race_async uses asyncio.wait(FIRST_COMPLETED) to cancel losers after winner; _run_coro_sync_safe bridges sync node_fn to async core without event-loop conflicts; loser asyncio.Task objects cancelled and gathered before node_fn returns; deadline computed once and decremented across wait iterations; on_error: skip preserved; AllCandidatesFailedError raised when all candidates fail without skip | `yamlgraph/node_factory/race_node.py`, `tests/unit/test_race_node.py` |

### 122. CAP-122 Router Node with Candidates Race Support

Extends the router node type to accept an optional `candidates:` list (identical schema to `race`), racing them for the routing decision and cancelling losers via asyncio cooperative cancellation. Routing semantics (route_field, routes, default_route) are unchanged. Eliminates the need for a manual race+python+conditional-edges workaround for low-latency classification on the critical path. Single-provider routers are unaffected.

**Feature Request:** FR-272

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-271 | Router node accepts optional candidates: list (≥2 {provider, model} dicts) for race-based routing: fires prompt concurrently, first-valid result used for routing resolution via _resolve_route; losers cancelled via asyncio.Task.cancel(); timeout: managed by _race_async (no outer _maybe_wrap_timeout); provider: + candidates: mutually exclusive (compile error); on_error: skip rejected at compile time; timeout/all-fail with on_error: fail raises AllCandidatesFailedError, with on_error: fallback/unset routes via default_route + records error; _race_winner metadata set in state; missing route_field in winner falls to default_route (no disqualification); single-provider routers unchanged | `yamlgraph/node_factory/llm_nodes.py`, `yamlgraph/utils/validators.py`, `yamlgraph/models/state_builder.py`, `yamlgraph/compile/node_compiler.py`, `tests/unit/test_router_race.py` |

### 124. CAP-124 Watcher2 PR Reuse (FR-275)

Enhanced create_pr.sh checks for existing PRs before creating new ones, reuses existing PRs to prevent automation failures and manual intervention.

**Feature Request:** FR-275

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-272 | create_pr.sh checks for existing open PRs on $WT_BRANCH using gh pr list --state open --head "$WT_BRANCH" --json number,url,title --jq ".[0] \| select(.number != null)"; if existing PR found, reuses PR number and URL instead of creating new; if no existing PR found, creates new PR as before; sets PR_NUMBER and PR_URL variables correctly in both cases; logs clearly whether reusing or creating; handles network failures gracefully by falling back to creation; updates PR title when different from requested title | `.chaplain/lib/watcher/create_pr.sh`, `tests/unit/test_watcher2_create_pr_reuse.py` |

### 125. CAP-125 Pipeline Script Retirement (FR-276)

Retire obsolete pipeline scripts (watch.sh, enforce_worktree.sh, bugfix_worktree.sh) in favor of the FSM runtime entrypoint start-system.sh as sole orchestrator. Implement forensic failure preservation by keeping failed worktrees and topics for investigation rather than destroying evidence.

**Feature Request:** FR-276

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-276 | All three obsolete scripts (.chaplain/watch.sh, scripts/enforce_worktree.sh, scripts/bugfix_worktree.sh) are deleted from the filesystem; any documentation references to them are updated to point to `.chaplain/scripts/start-system.sh`; start-system.sh is documented as the single entry point; failure paths preserve worktree and topic file in .chaplain/failed/ for forensic inspection; success paths clean up normally (teardown worktree, delete topic); worktree_setup.sh calls git worktree prune to clean orphaned metadata before branch creation; no functional regression (FSM runtime covers all capabilities of old scripts) | `.chaplain/scripts/start-system.sh`, `.chaplain/config/watcher-dispatcher.yaml`, `.chaplain/config/watcher-pipeline-v2.yaml`, `.chaplain/lib/watcher/worktree_setup.sh`, `CLAUDE.md`, `README.md` |

### 126. CAP-126 Test Speed Optimization

Pytest markers and configurable timing to enable faster development cycles. Adds 'slow' marker for tests >1s, configurable TEST_DELAY_SCALE for accelerated timing, and developer commands for selective test execution during rapid iteration.

**Feature Request:** FR-275

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-275 | pytest slow marker infrastructure enables selective test execution. 'slow' marker defined in pyproject.toml for tests taking >1 second; tests using sleep >1s marked with @pytest.mark.slow; pytest -m "not slow" excludes slow tests for fast iteration; pytest -m "slow" runs only slow tests for full validation; CHAOS_DELAY and test timing configurable via TEST_DELAY_SCALE environment variable; development commands documented in CLAUDE.md for ultra-fast, fast, and slow-only execution; test behavior unchanged when no marker filters applied; comprehensive acceptance tests validate marker functionality | `pyproject.toml`, `tests/chaos_tools.py`, `tests/unit/test_map_node_timeout.py`, `tests/unit/test_race_node.py`, `tests/unit/test_fr275_test_speed_optimization.py`, `CLAUDE.md` |

### 127. CAP-127 CI Hardening Consolidation

Consolidate and harden CI/CD workflows with performance optimizations, security improvements, and resource management across all GitHub Actions workflows.

**Feature Request:** FR-196

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-277 | CI hardening consolidation: all workflows have concurrency groups with cancel-in-progress; all setup-python steps include cache: pip; main workflow renamed to "CI"; tag pushes validate version against pyproject.toml; pip-audit has retry mechanism (3 attempts, 30s intervals); test matrix includes Python 3.11 and 3.12; existing job dependencies and triggers preserved; security scan still blocks on vulnerabilities; release process unchanged. | `.github/workflows/workflow.yml`, `.github/workflows/security.yml`, `.github/workflows/commitlint.yml`, `tests/unit/test_ci_hardening_consolidation.py` |

### 128. CAP-128 Chaplain Documentation

Comprehensive documentation for the FSM runtime orchestrator and shell library in .chaplain/README.md covering architecture, usage, and troubleshooting.

**Feature Request:** FR-195

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-278 | `.chaplain/README.md` exists with comprehensive documentation covering: runtime architecture anchored on `.chaplain/scripts/start-system.sh` with dispatcher/pipeline FSM flow across plan/judge/enforce phases, shell library reference for all tools in `.chaplain/lib/watcher/*.sh` (worktree_setup.sh, worktree_teardown.sh, preflight.sh, create_pr.sh, merge_pr.sh, wait_ci.sh, post_merge.sh, inbox_sync.sh, metrics.sh), usage examples for daemon and individual tools, environment variables and configuration, troubleshooting section, architecture details, and cross-references to related files (FR-273, etc.) | `.chaplain/README.md`, `tests/unit/test_chaplain_readme_documentation` |

### 130. CAP-130 Watcher2 Finalize Pre-commit Optimization

Optimize watcher2 finalize step to reduce copilot session invocations by pre-formatting code before pre-commit loops and increasing retry attempts from 3 to 5.

**Feature Request:** FR-198

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-286 | Watcher2 finalize section runs ruff check --fix and ruff format on yamlgraph/ and tests/ directories before entering the pre-commit loop; loop allows 5 attempts (was 3); failure message shows "5 attempts"; git add -A stages files before and after ruff commands; prevents copilot fallback for auto-fixable cascading issues | `.chaplain/scripts/start-system.sh`, `tests/unit/test_fr198_watcher2_finalize_optimization.py` |

### 131. CAP-131 Anthropic Prompt Caching Support

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

### 132. CAP-132 Watcher2 CI Resilience

Fix wait_ci.sh check ordering and CI resilience patterns for the watcher pipeline. v1 CI remediation artifacts (step-ci-remediate, enforce-ci-remediate) retired by FR-305; v2 handles CI fixes inside enforce_session.

**Feature Request:** FR-279

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-294 | Wait logic checks IN_PROGRESS before FAILURE to avoid premature CI failure | `.chaplain/lib/watcher/wait_ci.sh` |
| REQ-YG-298 | Maximum 2 remediation attempts before escalating to human | `.chaplain/config/watcher-pipeline-v2.yaml` |
| REQ-YG-299 | Remediation covers syntax errors, missing changelog/diary fragments | `.chaplain/graphs/watcher-enforce/enforce-session.yaml` |
| REQ-YG-300 | Existing passing pipelines unaffected by CI resilience changes | `.chaplain/config/watcher-pipeline-v2.yaml` |
| REQ-YG-301 | Test coverage for wait_ci.sh ordering and CI remediation loop | `tests/unit/test_fr279_watcher2_ci_resilience.py` |

### 133. CAP-133 Watcher2 CI Remediation Crash Fix

Fix three bugs in the watcher2 CI remediation loop that cause immediate script crash: missing run ID in gh run view, relative path resolution after cd, and missing error guard.

**Feature Request:** FR-284

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-307 | gh run view --log-failed uses proper run ID from gh run list | `.chaplain/scripts/start-system.sh` |

### 134. CAP-134 Watcher2 Changelog Auto-Generation

Auto-generate changelog fragments in watcher2 pipeline to eliminate manual intervention. Defense-in-depth approach with shell generation, prompt instructions, finalize verification, and CI remediation context. Extracts FR number, derives scope/type, looks up REQ-YG-XXX from capabilities registry, and prevents cross-wiring.

**Feature Request:** FR-283

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-308 | Auto-generate changelog fragments in watcher2 pipeline between critique and finalize steps. Extract FR number from FR_PATH, generate filename with 40-char descriptive suffix, derive type/scope from path, lookup REQ-YG-XXX from capability registry, validate FR number to prevent cross-wiring, create YAML frontmatter and fragment content automatically. | `.chaplain/scripts/start-system.sh (lines 309-341)`, `tests/unit/test_fr283_watcher2_changelog_auto_generation.py` |

### 135. CAP-135 Watcher2 Forensic Failure Diary

Automated forensic analysis for watcher2 failures with structured diary generation. When handle_failure is called, automatically capture failure context (reason, topic content, logs, worktree state), perform LLM-driven root cause analysis, and generate structured diary entries with evidence and recommendations for institutional learning.

**Feature Request:** FR-285

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-309 | Forensic failure analysis shall be automatically invoked on watcher2 handle_failure and generate structured diary entries containing root cause analysis, evidence sources, and prevention recommendations using LLM-driven investigation of failure context, logs, and worktree state | `.chaplain/scripts/start-system.sh (lines 56-89, 98)`, `.chaplain/lib/diary.py (lines 44-67, 100-123)`, `.chaplain/graphs/watcher-forensic/graph.yaml`, `tests/unit/test_fr285_watcher2_forensic_failure_diary.py` |

### 136. CAP-136 Per-Graph Typed MCP Tools

Derive per-graph typed MCP tool definitions from graph YAML metadata (name, description, state) so each graph appears as its own named tool with a typed JSON Schema. Shared schema derivation in discovery.py.

**Feature Request:** FR-291

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-310 | Input/output var separation: discovery excludes state_key targets from input_vars, exposing only user-supplied inputs. | `yamlgraph/discovery.py`, `tests/unit/test_mcp_typed_tools.py` |
| REQ-YG-311 | JSON Schema derivation from state type annotations. Maps str->string, int->integer, float->number, bool->boolean, list->array, dict->object. Parameterized types map to base type. Unknown types fall back to string. | `yamlgraph/discovery.py`, `tests/unit/test_mcp_typed_tools.py` |
| REQ-YG-312 | Per-graph MCP tool registration: each discovered graph registers as its own named MCP tool with typed inputSchema derived from input_vars. | `yamlgraph/export/mcp.py`, `tests/unit/test_mcp_typed_tools.py` |
| REQ-YG-313 | Tool name normalization: graph name hyphens replaced with underscores to produce valid MCP tool names. | `yamlgraph/discovery.py`, `tests/unit/test_mcp_typed_tools.py` |
| REQ-YG-314 | Name collision detection: duplicate tool_name values across discovered graphs raise ValueError at server startup. | `yamlgraph/export/mcp.py`, `tests/unit/test_mcp_typed_tools.py` |

### 137. CAP-137 Watcher FSM System Startup Script

Single startup script for the full watcher FSM system. Starts UI (creates event socket), generates diagrams, launches dispatcher with correct --initial-context in proper sequence. Signal-based cleanup kills all child processes. --inbox DIR overrides inbox directory.

**Feature Request:** FR-296

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-315 | Watcher FSM system startup script: single script starts UI (event socket), generates diagrams, and launches dispatcher with correct --initial-context in proper sequence; cleanup on SIGINT/SIGTERM kills all child processes by PID with pkill fallback; --inbox DIR overrides inbox directory | `.chaplain/scripts/start-system.sh` |

### 138. CAP-138 Watcher Pipeline FSM Simplification

Simplified watcher pipeline v2: 6 operational states (setup, plan, commit_plan, judge, enforce_session, done) + 3 terminals (completed, failed, stopped). Judge uses different model from plan with fresh session. Enforce resumes plan session. Dispatcher flag-gated via pipeline_version.

**Feature Request:** FR-305

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-316 | Simplified watcher pipeline v2 FSM: 6 operational states (setup, plan, commit_plan, judge, enforce_session, done) + 3 terminals (completed, failed, stopped). Judge uses different model from plan with fresh session (no resume). Enforce resumes plan session for full context continuity. Dispatcher flag-gated via pipeline_version context key. | `.chaplain/config/watcher-pipeline-v2.yaml`, `.chaplain/graphs/watcher-plan/step-judge-v2.yaml`, `.chaplain/graphs/watcher-enforce/enforce-session.yaml`, `tests/unit/test_fr305_watcher_pipeline_v2.py` |

### 139. CAP-139 Root README Accuracy Contract

Root README claims stay aligned with implemented provider support and include explicit review freshness metadata via a dedicated unit contract test.

**Feature Request:** FR-313

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-317 | Root `README.md` includes all currently supported provider identifiers (`anthropic`, `azure`, `deepseek`, `google`, `inception`, `lmstudio`, `mistral`, `openai`, `replicate`, `vertex`, `xai`) in provider documentation, contains no hardcoded `all <number> reference docs` wording, and ends with `Last reviewed: 2026-05-03`; contract enforced by `tests/unit/test_root_readme_accuracy.py` (FR-313). | `README.md`, `tests/unit/test_root_readme_accuracy.py` |

### 140. CAP-140 Watcher2 Validate Split Fix/Gate

Split watcher2 post-enforce validation into deterministic micro-remediation fast path (micro_changelog + micro_title), explicit LLM remediation fallback (validate_fix), and deterministic CI-parity gate (validate_gate) with bounded retry semantics before done.

**Feature Request:** FR-316

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-318 | Watcher2 pipeline routes post-enforce flow through deterministic micro_changelog then micro_title then sanity_check then validate_gate; validate_gate performs deterministic pre-commit, commit-title, branch-freshness, and diary-in-diff checks with max-attempt retry contract (pass → done, fix_needed → validate_fix, error → failed). micro-step errors fall back to validate_fix. Both done and validate_gate diary-parity trigger use a shared primary PR title selector: first feat/fix in `origin/main..HEAD`, else first non-docs/non-chore, else first subject. | `.chaplain/config/watcher-pipeline-v2.yaml`, `.chaplain/actions/changelog_gen_action.py`, `.chaplain/actions/validate_gate_action.py`, `.chaplain/lib/watcher/select_primary_pr_title.sh`, `.chaplain/graphs/watcher-enforce/prompts/validate-session.yaml`, `tests/unit/test_fr316_watcher2_validate_split_fix_gate.py`, `tests/unit/test_fr412_watcher2_micro_remediation_fast_path.py`, `tests/unit/test_fr358_watcher2_primary_pr_title_selection.py` |

### 141. CAP-141 Shared FSM Bridge Module

Extract canonical fire-and-forget FSM↔YAMLGraph bridge behavior into `yamlgraph.utils.fsm` and make fsm-router consume it via a thin wrapper. Ownership ruling (FR-755, 2026-07-21): contrib tier repeating pattern, supported for reuse but outside YAMLGraph core API identity.

**Feature Request:** FR-346

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-319 | FSM bridge shared module: `yamlgraph.utils.fsm` package with `YamlgraphAsyncAction`, `extract_event`, `json_safe`, `resolve_context_ref` exported from `yamlgraph.utils.fsm`; fire-and-forget guard semantics; AF_UNIX DGRAM event dispatch; interrupt/event_map/route/success resolution cascade. | `yamlgraph/utils/fsm/__init__.py`, `yamlgraph/utils/fsm/helpers.py`, `yamlgraph/utils/fsm/event_sender.py`, `yamlgraph/utils/fsm/graph_runner.py`, `yamlgraph/utils/fsm/action.py`, `examples/fsm-router/actions/yamlgraph_async_action.py`, `tests/unit/test_fsm_bridge_shared.py` |

### 142. CAP-142 Skill Export Portable Packaging

Add `yamlgraph skill export` to package existing graphs into portable Skills bundles with deterministic filesystem artifacts for skill discovery.

**Feature Request:** FR-348

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-320 | CLI parser registers `yamlgraph skill export` with `--format` and `--output-dir` options and dispatches to skill command handlers. | `yamlgraph/cli/__init__.py`, `yamlgraph/cli/skill_commands.py`, `tests/unit/test_fr348_skill_export_red.py` |
| REQ-YG-321 | Export generates required package artifacts: `SKILL.md`, executable `scripts/run.sh`, `references/`, and `assets/schema.json`. | `yamlgraph/export/skill.py`, `yamlgraph/export/skill_writer.py`, `tests/unit/test_fr348_skill_export_red.py` |
| REQ-YG-322 | `SKILL.md` includes skill metadata, typed input/output sections, and runnable CLI invocation example. | `yamlgraph/export/skill.py`, `yamlgraph/export/skill_writer.py`, `tests/unit/test_fr348_skill_export_red.py` |
| REQ-YG-323 | `assets/schema.json` contains top-level `input` and `output` schema objects derived from graph input vars and output state keys. | `yamlgraph/export/skill.py`, `yamlgraph/export/skill_writer.py`, `tests/unit/test_fr348_skill_export_red.py` |
| REQ-YG-324 | Format variants map to expected paths for `skill-md`, `copilot`, and `cursor` package layouts. | `yamlgraph/export/skill.py`, `yamlgraph/export/skill_writer.py`, `tests/unit/test_fr348_skill_export_red.py` |
| REQ-YG-325 | Export is deterministic and non-LLM with explicit errors for invalid graph input, unsupported format, and target collisions. | `yamlgraph/export/skill.py`, `yamlgraph/export/skill_writer.py`, `yamlgraph/cli/skill_commands.py`, `tests/unit/test_fr348_skill_export_red.py` |
| REQ-YG-326 | CLI/reference docs include `yamlgraph skill export` usage and output layout examples for all format variants. | `reference/cli.md`, `reference/skills-export.md`, `reference/README.md`, `tests/unit/test_fr348_skill_export_red.py` |

### 143. CAP-143 Agent Export Tool-Scoped Personas

Add `agent-md` export format to generate GitHub Copilot `.agent.md` files with YAMLGraph MCP tool scoping from graph metadata.

**Feature Request:** FR-350

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-327 | CLI parser accepts `--format agent-md` for `yamlgraph skill export` and dispatches through existing skill command handlers. | `yamlgraph/cli/__init__.py`, `yamlgraph/cli/skill_commands.py`, `tests/unit/test_fr350_agent_export_red.py` |
| REQ-YG-328 | `agent-md` export writes a single file at `<output-dir>/.github/agents/<skill-name>.agent.md`. | `yamlgraph/export/skill.py`, `yamlgraph/export/skill_writer.py`, `tests/unit/test_fr350_agent_export_red.py` |
| REQ-YG-329 | Generated `.agent.md` frontmatter includes non-empty `description`, `tools: [yamlgraph/*]`, and `model: Claude Sonnet 4`. | `yamlgraph/export/skill.py`, `yamlgraph/export/skill_writer.py`, `tests/unit/test_fr350_agent_export_red.py` |
| REQ-YG-330 | Generated `.agent.md` body includes agent heading, inputs derived from graph schema, and `@agent-name` invocation guidance. | `yamlgraph/export/skill.py`, `yamlgraph/export/skill_writer.py`, `tests/unit/test_fr350_agent_export_red.py` |
| REQ-YG-331 | Export remains deterministic and non-LLM with explicit failures for invalid graph path, unsupported format, and output file collisions. | `yamlgraph/export/skill.py`, `yamlgraph/export/skill_writer.py`, `yamlgraph/cli/skill_commands.py`, `tests/unit/test_fr350_agent_export_red.py` |
| REQ-YG-332 | CLI/reference docs include `agent-md` usage and output layout examples. | `reference/cli.md`, `reference/skills-export.md`, `reference/README.md`, `tests/unit/test_fr350_agent_export_red.py` |

### 145. CAP-145 Copilot Instrumentation Gap Closure

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

### 146. CAP-146 FSM Snapshot Hooks Phase 2 Subclassing

Add a typed snapshot boundary and lifecycle hook callbacks to the shared FSM bridge so domains can subclass behavior without forking dispatch flow.

**Feature Request:** FR-369

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-347 | Shared FSM bridge exposes typed snapshot params (`SnapshotParams` + `snapshot_params`) and lifecycle hooks (`pre_snapshot`, `pre_dispatch`, `on_success`, `on_error`) wired through `YamlgraphAsyncAction.execute()` and `run_and_dispatch()` with dispatch suppression support. | `yamlgraph/utils/fsm/snapshot.py`, `yamlgraph/utils/fsm/action.py`, `yamlgraph/utils/fsm/graph_runner.py`, `yamlgraph/utils/fsm/__init__.py`, `tests/unit/test_fr369_fsm_snapshot_hooks_red.py` |

### 147. CAP-147 Graph Run JSON Stdout + TypeScript Node Integration

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

### 148. CAP-148 CI Co-authored-by Trailer Gate

GitHub Actions job in commitlint.yml that blocks pull requests when any `Co-authored-by:` trailer identities are present in PR commit messages or PR body text.

**Feature Request:** FR-385

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-358 | `copilot-trailer-gate` job in `commitlint.yml` deterministically scans `BASE_SHA..HEAD_SHA` commit messages and `github.event.pull_request.body` for any `Co-authored-by:` trailer line, fails with exit 1 on detection, and passes unchanged PRs otherwise. | `.github/workflows/commitlint.yml`, `tests/unit/test_fr385_ci_copilot_trailer_gate_red.py`, `CLAUDE.md` |

### 149. CAP-149 Prompt Theme Analyzer Demo

Demo graph showing list -> map -> deterministic aggregate -> llm-group -> write flow for prompt theme analysis with explicit boundary normalization.

**Feature Request:** FR-402

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-359 | YAMLGraph includes `examples/demos/prompt_theme_analyzer/` with a five-node pipeline (`list_prompts -> classify_themes(map) -> aggregate_themes(python) -> group_themes(llm) -> write_report`) where `source_dir` is required, prompt text is truncated at the Python boundary, grouping consumes deterministic aggregated theme counts, and the demo ships with tests, capability traceability, diary reflection, and execution proof via `demo-output.log`. | `examples/demos/prompt_theme_analyzer/graph.yaml`, `examples/demos/prompt_theme_analyzer/tools.py`, `examples/demos/prompt_theme_analyzer/prompts/group_themes.yaml`, `tests/unit/test_fr402_prompt_theme_analyzer_red.py`, `docs/diary/2026-05-16-reflection-fr-402-prompt-theme-analyzer-demo.md` |

### 150. CAP-150 Philosopher's Book Demo

Demo pipeline generating one chapter at a time of a philosophical work on cognitive traps. Plan → write a single chapter using Copilot with diary search tools. Run with --var chapter_num=N. (FR-404)

**Feature Request:** FR-404

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-404 | YAMLGraph includes `examples/demos/philosopher_book/` with a four-node pipeline (load_trap -> plan_chapter(copilot) -> write_chapter(copilot) -> save_chapter) where load_trap loads a single trap by chapter_num, search_diary searches docs/diary/ using case-insensitive substring matching, read_file validates allowed path prefixes and truncates at 8000 chars, and save_chapter writes to output_dir/chapters/. | `examples/demos/philosopher_book/graph.yaml`, `examples/demos/philosopher_book/tools.py`, `tests/unit/test_philosopher_book.py`, `docs/diary/2026-05-16-fr404-philosopher-book.md` |
| REQ-YG-405 | YAMLGraph includes a separate philosopher-book editorial graph that snapshots repo-contained chapter inputs, builds a token-bounded global editorial brief, edits chapters through a type: map LLM pass, writes edited markdown to a separate repo-contained output folder with original filenames preserved, and writes an editorial report with word-count deltas and editorial notes. | `examples/demos/philosopher_book/editorial_graph.yaml`, `examples/demos/philosopher_book/tools.py`, `examples/demos/philosopher_book/prompts/editorial_brief.yaml`, `examples/demos/philosopher_book/prompts/edit_chapter.yaml`, `tests/unit/test_philosopher_book.py`, `docs/diary/2026-05-17-fr405-philosopher-book-editorial-graph.md` |

### 151. CAP-151 Graph Lint JSON Output

Add machine-readable NDJSON output mode for `yamlgraph graph lint` while preserving default human output and existing lint exit-code semantics.

**Feature Request:** FR-406

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-406 | CLI parser accepts `yamlgraph graph lint --json` (default false), JSON mode emits one `LintResult` JSON object per linted file to stdout (NDJSON), routes diagnostics/errors to stderr, and preserves existing lint exit semantics (non-zero when lint errors occur, zero for warnings-only/clean runs). | `yamlgraph/cli/__init__.py`, `yamlgraph/cli/graph_validate.py`, `tests/unit/test_fr406_lint_json_output_red.py` |

### 152. CAP-152 Watcher2 Dispatcher Audit Cadence

Reintegrates inquisitor cadence into watcher-dispatcher so no-topic cycles can trigger `.chaplain/inquisitor.sh --propose` at most once per 24 hours while preserving topic-first routing. (FR-411)

**Feature Request:** FR-411

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-407 | Watcher2 dispatcher includes an `auditing` state and `last_audit_ts` context key; syncing_inbox emits `audit_needed` only when no topic is available and 24h cadence elapsed; audit runs `.chaplain/inquisitor.sh --propose`, updates `last_audit_ts` on success, and routes failures back to idle without stopping the daemon. | `.chaplain/config/watcher-dispatcher.yaml`, `.chaplain/actions/syncing_inbox_action.py`, `.chaplain/actions/audit_action.py`, `tests/unit/test_fr411_watcher2_dispatcher_inquisitor_audit_cadence.py` |

### 153. CAP-153 Built-in Questionnaire Gap Utilities

Adds framework-shipped questionnaire helpers `detect_gaps` and `normalize_extracted` in `yamlgraph.tools.questionnaire` so schema-driven probing loops can reuse deterministic gap detection and extraction normalization through existing `type: python` tool wiring. (FR-421)

**Feature Request:** FR-421

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-409 | `detect_gaps(state)` returns sorted required schema field IDs missing from `state["extracted"]`, treating `None` and empty string as missing and returning `{"gaps": [...], "has_gaps": bool}`. | `yamlgraph/tools/questionnaire.py`, `tests/unit/test_fr421_questionnaire_gap_utilities_red.py` |
| REQ-YG-410 | `normalize_extracted(state)` returns `{}` when `state["extracted"]` is a dict, otherwise returns `{"extracted": {}}`; utility module remains callable via `type: python` tool config. | `yamlgraph/tools/questionnaire.py`, `yamlgraph/tools/python_tool.py`, `tests/unit/test_fr421_questionnaire_gap_utilities_red.py` |

### 154. CAP-154 Hook Classification Daemon

Warm FSM daemon that classifies VS Code Copilot hook events using YAMLGraph LLM pipeline. Async classify-and-log pattern: fire-and-forget DGRAM to statemachine engine, LLM classifies intent/danger, results appended to JSONL audit log. Phase A: demo-only in examples/demos/hook_classifier/. (FR-425)

**Feature Request:** FR-425

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-411 | Classification validation enforces intent in {legitimate, suspicious, hostile}, danger_level int 1-5 (never 0), and category in valid enum set; invalid values are normalized to safe defaults (unknown/1/normal). | `examples/demos/hook_classifier/actions/classify_action.py`, `tests/unit/test_fr425_hook_classification_daemon_red.py` |
| REQ-YG-412 | Reason code mapping returns classified-{intent} for valid intents and classify-error for unknown/missing intent; classify-timeout for timeout exceptions. | `examples/demos/hook_classifier/actions/classify_action.py`, `tests/unit/test_fr425_hook_classification_daemon_red.py` |
| REQ-YG-413 | Append contract uses open(mode='a') with print(json.dumps(..., ensure_ascii=True), flush=True); entries exceeding 4096 bytes truncate detail field; concurrent writers produce no torn lines. | `examples/demos/hook_classifier/actions/classify_action.py`, `tests/unit/test_fr425_hook_classification_daemon_red.py` |
| REQ-YG-414 | Session history capped at max 50 entries with 30-minute sliding window; FIFO eviction drops oldest entries first. | `examples/demos/hook_classifier/actions/classify_action.py`, `tests/unit/test_fr425_hook_classification_daemon_red.py` |
| REQ-YG-415 | ClassifyAction on_success validates classification, appends to JSONL log, and updates session history; on_error writes deterministic fallback with intent=unknown, danger_level=1, category=error. | `examples/demos/hook_classifier/actions/classify_action.py`, `tests/unit/test_fr425_hook_classification_daemon_red.py` |
| REQ-YG-416 | Adversarial inputs (malformed LLM output, oversized payloads, prompt injection in command text) are normalized by validation layer; no crash, no bypass of danger_level=0 sentinel prohibition. | `examples/demos/hook_classifier/actions/classify_action.py`, `tests/unit/test_fr425_hook_classification_daemon_red.py` |

### 155. CAP-155 Schema Loader Tool Type

Add built-in tools.type=schema_loader for deterministic graph-relative schema loading and merge-by-topic behavior in type: python nodes without project-local loader functions. (FR-426)

**Feature Request:** FR-426

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-417 | parse_schema_loader_tools recognizes type: schema_loader entries, enforces exactly-one-of path/paths_from_state plus required state_key, and supports single-file schema loading into the configured state key via python tool runtime integration. | `yamlgraph/tools/schema_loader_tool.py`, `yamlgraph/tools/python_tool.py`, `yamlgraph/compile/graph_loader.py`, `yamlgraph/compile/node_compiler.py`, `tests/unit/test_fr426_schema_loader_tool_type_red.py` |
| REQ-YG-418 | Merge mode loads schema files from paths_from_state topics under schema_dir with suffix, preserves additive ordering (existing fields first), deduplicates by deduplicate_by, and enforces graph-root path safety including traversal rejection and graph-relative resolution independent of process CWD. | `yamlgraph/tools/schema_loader_tool.py`, `yamlgraph/tools/python_tool.py`, `yamlgraph/compile/map_compiler.py`, `tests/unit/test_fr426_schema_loader_tool_type_red.py` |

### 156. CAP-156 WIP Commit Subject Gate

Adds deterministic local and CI commit-subject enforcement that blocks the standalone word `wip` (case-insensitive) on the protected main merge path. Local commit-msg checks apply only on branch `main`, while CI scans PR commit subjects in `BASE_SHA..HEAD_SHA`. (FR-424)

**Feature Request:** FR-424

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-419 | Commit subject gate blocks standalone `wip` (case-insensitive) on local `main` commit-msg flow and in CI `wip-gate` pull-request commit ranges (`BASE_SHA..HEAD_SHA`) via deterministic subject scanning, while allowing non-main branches and non-boundary substrings like `swipe`. | `.pre-commit-config.yaml`, `.github/workflows/commitlint.yml`, `tests/unit/test_fr424_wip_main_gate_red.py`, `CLAUDE.md` |

### 157. CAP-157 Graph Loader Strict Tool Load Fail Fast

Graph compilation enforces explicit Python tool loading policy with strict fail-fast default and warn-mode opt-out for partial registries.

**Feature Request:** FR-444

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-420 | Graph compilation defaults to strict Python tool loading and raises a compile-time ValueError when any Python tool import/symbol load fails, reporting each failed tool and root cause in one actionable error. | `yamlgraph/compile/graph_loader.py`, `tests/unit/test_fr444_graph_loader_tool_load_mode_red.py` |
| REQ-YG-421 | Graph config supports config.tool_load_mode: warn to preserve warn-and-continue behavior: failed Python tools emit warnings during compile and unresolved tools surface as runtime Unknown tool errors in tool_call nodes. | `yamlgraph/compile/graph_loader.py`, `tests/unit/test_fr444_graph_loader_tool_load_mode_red.py`, `reference/graph-yaml.md` |

### 158. CAP-158 Copilot Skill Promotion

Promote reference docs to Copilot Skills (.github/skills/) for on-demand loading in VS Code Copilot Chat.

**Feature Request:** FR-446

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-423 | Five Tier 1 skills: release-version, chaplain-ops, run-code-analysis, feature-request (FR-446), and the graph-authoring end-to-end workflow skill (FR-765). Each skill is a self-contained SKILL.md with applyTo patterns and tool restrictions; graph-authoring adds a doctrine.md workflow contract (input closure, precedent search, artifact report, local validation, escalation, anti-patterns) composing reference/graph-yaml.md and reference/prompt-yaml.md as syntax references (the author-graph / author-prompt intermediary skills were retired 2026-07-29; their unique content folded into the reference docs), plus an executable adapter route (FR-765 round 2): a thin copilot-node adapter graph and pointer prompt launched by the scripts/author.sh operator wrapper, verified by the tmp/draft-authoring-report.md artifact contract, never exit code. | `.github/skills/release-version/SKILL.md`, `.github/skills/chaplain-ops/SKILL.md`, `.github/skills/run-code-analysis/SKILL.md`, `.github/skills/feature-request/SKILL.md`, `.github/skills/graph-authoring/SKILL.md`, `.github/skills/graph-authoring/doctrine.md`, `.github/skills/graph-authoring/adapters/README.md`, `.github/skills/graph-authoring/adapters/graph.yaml`, `.github/skills/graph-authoring/adapters/prompts/author.yaml`, `scripts/author.sh` |

### 159. CAP-159 Standalone Planner Demo

Standalone FR planner demo using agent node with 5 task-shaped tools (4 shell + 1 python). Transforms rough topic files into structured feature requests. Portable — runs without VS Code runtime.

**Feature Request:** FR-452

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-424 | Planner demo has 5 tools (read_file, search, list_dir, git_log, write_file), agent node with max_iterations 15, PlanResult schema with 6 fields, write_file as python tool, no hardcoded model, and produces a FR file at tmp/plan-output.md. | `examples/demos/planner/graph.yaml`, `examples/demos/planner/prompts/planner.yaml`, `examples/demos/planner/tools/write_file.py`, `examples/demos/planner/demo.sh` |

### 160. CAP-160 CAP Architecture Auto-Sync

Pre-commit hook that auto-regenerates the capabilities section of ARCHITECTURE.md when capabilities/*.yaml files change. Follows the ruff-format auto-fix pattern: modifies file, pre-commit detects unstaged change and fails, developer stages.

**Feature Request:** FR-460

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-425 | cap-architecture-sync pre-commit hook triggers on capabilities/*.yaml and aggregate script changes, runs aggregate_capabilities.py, exits 0, and does not pass filenames. | `.pre-commit-config.yaml`, `scripts/aggregate_capabilities.py` |

### 161. CAP-161 Standalone Enforcer Demo

Standalone FR enforcer demo using agent node with 10 task-shaped tools (7 shell + 3 python). Implements planned and judged feature requests. Portable — runs without VS Code runtime. Completes the plan→judge→enforce trilogy.

**Feature Request:** FR-462

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-426 | Enforcer demo has 10 tools (read_file, search, list_dir, git_log, git_diff, lint, run_tests, write_file, edit_file, run_command), agent node with max_iterations 25, ImplementationResult schema with 4 fields, write_file/edit_file as path-restricted python tools, no hardcoded model, and produces structured implementation result. | `examples/demos/enforcer/graph.yaml`, `examples/demos/enforcer/prompts/enforcer.yaml`, `examples/demos/enforcer/tools/write_file.py`, `examples/demos/enforcer/demo.sh` |

### 162. CAP-162 Enforcer Demo Safety Hardening

Safety hardening of the enforcer demo: path-restricted write_file/edit_file, git_commit removed (separation of concerns), run_command honeypot for telemetry, git_log/lint/git_diff tools added. 10 tools total (7 shell + 3 python).

**Feature Request:** FR-463

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-427 | Enforcer demo has 10 tools (7 shell + 3 python), no git_commit, path-restricted write_file and edit_file, run_command honeypot, git_log/lint/git_diff shell tools, ImplementationResult schema with 4 fields (no commit_hash), and explicit to: END edge. | `examples/demos/enforcer/graph.yaml`, `examples/demos/enforcer/prompts/enforcer.yaml`, `examples/demos/enforcer/tools/write_file.py`, `examples/demos/enforcer/tools/edit_file.py`, `examples/demos/enforcer/tools/run_command.py` |

### 163. CAP-163 CAP Retirement Support

Add status: retired support to capability YAML files. req_coverage.py excludes retired CAPs from coverage checks. validate_capabilities.py accepts retired files with relaxed field requirements. Establishes the retirement lifecycle pattern.

**Feature Request:** FR-466

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-428 | CAP YAML files accept optional status: retired field (default active). req_coverage.py excludes retired CAP REQs from coverage and strict checks. validate_capabilities.py accepts retired files with empty modules/requirements. Tombstone RETIRED_CAPS dict preserved for deleted-file ID reservation. | `scripts/req_coverage.py`, `scripts/validate_capabilities.py`, `tests/unit/test_fr466_cap_retirement_support_red.py`, `tests/unit/test_capability_registry.py` |

### 164. CAP-164 Structured Output JSON Fallback

When with_structured_output() fails (provider rejects response_format), fall back to extract_json() + model_validate(). Extends FR-456 pattern from agent.py to executor.py and race_node.py.

**Feature Request:** FR-464

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-464 | Executor falls back to JSON extraction when structured output rejected | `yamlgraph/executor.py` |
| REQ-YG-465 | Race node falls back to JSON extraction when structured output rejected | `yamlgraph/node_factory/race_node.py` |

### 165. CAP-165 Watcher2 Baseline Dead Code Removal

Remove all FR-277 watcher2 baseline checkpointing dead code: Python modules, packages, graphs, tests, capability registrations, and documentation references.

**Feature Request:** FR-278

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-466 | All baseline-related Python modules, packages, graphs, tests, capability registrations, architecture references, and documentation references are removed. No import errors from removal. No baseline references remain in Python or YAML files. Ruff check passes after removal. | `tests/unit/test_fr278_remove_baseline_dead_code.py` |

### 166. CAP-166 Meta Self-Reflective Demo

Demo graph that applies a natural-language verb to a code artifact — including the demo's own graph YAML. A read_file shell tool feeds a tool node, then an LLM node transforms the source per the verb and returns typed output (MetaResult). A typed, traced homage to the 2023 meta.js trick (node meta 'explain structure' ./meta.js), correcting its trust-by-default flaws: YAML prompt instead of hardcoded string, inline schema for typed output, shlex-escaped shell tool, output kept in state rather than piped to disk.

**Feature Request:** FR-464

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-467 | Meta demo: two-node graph (load tool node + transform llm node). read_file shell tool (cat {file}) reads the target into state.source; transform llm node applies state.verb to state.source via the meta_transform prompt and writes typed MetaResult (summary, findings, suggested_code) to state.result. State declares verb and target as str inputs. transform requires source (no LLM call before read). No hardcoded model — PROVIDER/MODEL env fallthrough. Self-referential run (target = the graph's own YAML) is the headline. demo.sh accepts verb and target and runs the graph with --json. Graph lints clean. | `examples/demos/meta` |

### 167. CAP-167 Dungeon Master Example

RETIRED by FR-474. The v1 turn-loop / preplan narrative example was detached to examples/dungeon_master/purgatory/ as a reference parts bin when the DM example was restarted around a single proven loop (synopsis -> plot). Its governed test moved with it (purgatory/tests/test_dungeon_master.py), so REQ-YG-429..433 are no longer covered from the governed tree by design. Turn-based book / dungeon-master narrative example. Fuses the eBook preplanning spine with the NPC parallel turn loop and a turn-level DM steering interrupt (accept/edit/nudge/retry/next-chapter/end).

**Feature Request:** FR-466

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-429 | Preplan graph compiles and runs from a premise variable | `examples/dungeon_master/nodes/story_io` |
| REQ-YG-430 | Preplan emits a valid story.json with synopsis, plot, chapters, cast | `examples/dungeon_master/nodes/story_io.save_story_tool` |
| REQ-YG-431 | plan_all map fans out one tagged plan per cast member | `examples/dungeon_master/nodes/story_io` |
| REQ-YG-432 | weave produces a non-empty beat attributing actions by character name | `examples/dungeon_master/nodes/story_io` |
| REQ-YG-433 | DM turn loop honors accept/edit/nudge/retry/next-chapter/end | `examples/dungeon_master/nodes/story_io.parse_dm_tool`, `examples/dungeon_master/nodes/story_io.commit_beat_tool` |

### 168. CAP-168 Conditional Edge to Map Node

A conditional (expression) edge whose target is a `map` node compiles to a single router on the source node. The router returns the map's Send fan-out when the matching condition selects the map target, preserving per-item parallelism and the collect reducer, while other branches (including END) route normally. Mixing an unconditional edge to a map node with conditional edges on the same source is rejected at compile time (dual-router guard).

**Feature Request:** FR-467

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-434 | Conditional edge to a map node compiles to one router that fans out via Send; an unconditional+conditional dual map router is rejected, and the interrupt loop terminates on its END branch. | `yamlgraph/edge_compiler._add_conditional_edges`, `yamlgraph/routing.make_expr_router_fn` |

### 169. CAP-169 Dungeon Master Web UI

RETIRED by FR-470 (CAP-170). The v1 eager-weave board surfaced only the final woven beat after preplan. v2 is journey-first (synopsis review -> outline browse -> on-demand beat generation), superseding this interaction model. The turn-loop machinery (turn-loop.yaml, compose_dm_input) remains for the CLI. FastAPI + HTMX web board over the dungeon-master example. A stateless DMSession adapter preplans a story and drives the checkpointed turn loop beat-by-beat through HTTP, composing the six DM actions (accept/edit/nudge/retry/next-chapter/end) into the existing parse_dm grammar. Pure Layer-1 presentation reusing nodes/story_io.py untouched.

**Feature Request:** FR-468

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-435 | FastAPI app + stateless DMSession drive preplan and turn over HTTP; GET / returns 200, POST /story/preplan advances the turn loop to the first interrupt and returns a beat, POST /story/turn with accept advances, end completes (is_complete via state.next), with a process-stable checkpointer and per-session story files | `examples/dungeon_master/api/session`, `examples/dungeon_master/api/routes/story` |
| REQ-YG-436 | Storybook templates render via HTMX swaps; fragments contain the story banner (logline, chapter progress, turn/beat counter), the draft_beat card, the six DM controls, and a completion panel when the session ends | `examples/dungeon_master/api/routes/story` |
| REQ-YG-437 | End-to-end scripted web session (preplan -> steer -> end) recorded to a demo log and documented in the example README Web UI section | `examples/dungeon_master/api/session` |

### 170. CAP-170 Dungeon Master Web UI v2 (Journey-First)

RETIRED by FR-474. The journey-first outline/beat board described here was over-scoped before its core loop was proven; it is detached to examples/dungeon_master/purgatory/. v2 restarts as an ungoverned prototype (FR-474 J3: no CAP/REQ/gates until the loop earns them), so REQ-YG-468..471 are intentionally uncovered. A successor FR re-lights governance on promotion. Journey-first redesign of the dungeon-master web board, superseding CAP-169. The DM reads and shapes the synopsis before any prose exists (FR-470), browses and edits the chapter/beat outline with a navigable breadcrumb (FR-471), and generates a chosen beat on demand (FR-472). A per-session story document (story_doc over story.json) is the source of truth; the v1 turn-loop checkpointer is gone from the web path (turn-loop.yaml remains for the CLI).

**Feature Request:** FR-470

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-468 | Preplan stops at the skeleton (no eager weave) and renders a synopsis card with a single editable text block (one prose paragraph) shared with the beat view; regenerate re-invokes the synopsis prompt, edit persists the paragraph to the story document, and accept marks it reviewed and advances to the outline | `examples/dungeon_master/api/session`, `examples/dungeon_master/api/story_doc`, `examples/dungeon_master/api/routes/story`, `examples/dungeon_master/api/templates/components/text_block.html` |
| REQ-YG-469 | The outline lists chapters as navigation links; opening a chapter lazily materializes its beat stubs once (a materialized guard makes revisits idempotent and preserves DM edits); chapter summaries and beat stubs are editable and persist to the story document; a breadcrumb links back to the outline and names the current chapter | `examples/dungeon_master/api/session`, `examples/dungeon_master/api/story_doc`, `examples/dungeon_master/api/routes/story` |
| REQ-YG-470 | For a planned beat, Generate beat runs the stateless weave-beat.yaml graph (plan_all map over cast → weave → normalize_beat; no checkpointer, no interrupt, no loop) and yields editable prose with status generated; Accept persists the prose (verbatim or edited), appends it to the chapter file via append_beat_to_chapter, and flips status to committed; generation targets the chosen beat (arbitrary chapter/beat), not a forced forward order | `examples/dungeon_master/api/session`, `examples/dungeon_master/api/story_doc`, `examples/dungeon_master/api/routes/story`, `examples/dungeon_master/weave-beat`, `examples/dungeon_master/nodes/story_io` |
| REQ-YG-471 | The shared editable-prose card (synopsis and woven beat) is iterable: it shows the text in edit mode (autosaving on change), a 3-line prompt textarea, and Iterate + Accept controls. Iterate runs the shared refine prompt ("apply <prompt> to <text>"), replaces the text, and re-renders; an empty prompt is a pure save. Iterating a beat always yields status generated and never writes the chapter file (only Accept commits); Accept ignores the prompt field | `examples/dungeon_master/api/session`, `examples/dungeon_master/api/routes/story`, `examples/dungeon_master/api/templates/components/text_block.html` |

### 171. CAP-171 Executor Plain-Text Content Normalization

The synchronous and asynchronous plain-text invoke paths normalize response.content to a string via the shared normalize_content() utility (yamlgraph/utils/content.py), matching the structured-output fallback that already normalized (FR-264). Without this, providers that return content as a list of part-dicts — notably Google Gemini 2.5+/3.x on Vertex, which attaches thought-signature parts — leak the raw Python list into graph state instead of a clean string. Completes FR-264's boundary normalization for executor.PromptExecutor and utils/llm_factory_async.invoke_async.

**Feature Request:** FR-476

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-472 | executor.PromptExecutor._invoke_with_retry (sync, no output_model) and utils/llm_factory_async.invoke_async (async, no output_model) normalize response.content to str via shared normalize_content(); list-of-parts content from Gemini-on-Vertex (with thought-signature parts) is collapsed to a string rather than leaked raw into state | `yamlgraph/executor.py`, `yamlgraph/utils/llm_factory_async.py`, `yamlgraph/utils/content.py`, `tests/unit/test_executor_retry.py` |

### 172. CAP-172 Prompt-Monolith Linter Check (W026)

A static graph-lint check, W026, flags a prompt that asks one LLM call to make too many independent judgements at once — the attention-overload anti-pattern FR-584 proved empirically costs accuracy (a single L5 prompt fusing ~12 jobs starved its load-bearing salience judgement) and FR-585 decomposes. check_prompt_complexity is graph-driven (reuses the node -> prompt-path resolution) and warning-severity only: it never changes lint exit semantics. Two complementary detectors: W026-1 counts top-level fields in an inline schema/output_schema (default threshold 4, exposed as a field_threshold function parameter — no lint-config file); W026-2 matches a small curated set of prose phrases (enumerated multi-output and global cross-unit constraints). Calibrated against the plot_modeller 7-prompt audit: fires on the four monoliths (assign_pre_eff, assign_causality, assign_affects, extract_agents) and stays silent on the two clean prompts (extract_glosses, classify_kinds).

**Feature Request:** FR-586

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-473 | check_prompt_complexity emits W026 at warning severity when a prompt fuses too many independent judgements — via inline-schema top-level field count (>= field_threshold, default 4) or curated prose phrases (enumerated multi-output, global cross-unit constraint); calibrated to fire on the four plot_modeller monoliths and stay silent on the two clean prompts; graph lint exit semantics unchanged | `yamlgraph/linter/checks_prompts.py`, `yamlgraph/linter/graph_linter.py`, `tests/unit/test_linter_prompt_monolith.py` |

### 173. CAP-173 Write Data File Tool

Built-in write_data_file tool type that writes structured data (dict/list) to a YAML file within the workspace. Symmetric counterpart to data_files read directive. Graph-relative path resolution, atomic writes, path traversal guard, and self-modification guard via compile-time closure.

**Feature Request:** FR-625

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-474 | parse_write_data_file_tools() extracts tools with type: write_data_file from YAML tools section and returns WriteDataFileToolConfig instances. | `tools/write_data_file_tool` |
| REQ-YG-475 | write_data_file tool writes structured data to a YAML file at a graph-relative path, creating parent directories as needed. Atomic write via tempfile + os.replace. | `tools/write_data_file_tool` |
| REQ-YG-476 | write_data_file tool rejects absolute paths and path traversal (.. segments) that escape the graph root directory. | `tools/write_data_file_tool` |
| REQ-YG-477 | write_data_file tool refuses to overwrite the graph file itself or files under its prompts_dir (self-modification guard via compile-time closure). | `tools/write_data_file_tool` |

### 174. CAP-174 Data Files Glob Support

Extends the data_files directive to accept glob patterns (e.g. wiki/*.yaml), loading all matching files into state as a dict keyed by filename stem. Completes read-write symmetry with write_data_file tool.

**Feature Request:** FR-629

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-478 | data_files with glob metacharacters (* ? [) expands the pattern via Path.glob() and returns a dict keyed by filename stem. Empty matches return empty dict. Files sorted alphabetically for deterministic ordering. | `data_loader` |
| REQ-YG-479 | data_files glob rejects ** (recursive) patterns with a clear DataFileError. Glob patterns that escape graph directory raise DataFileError. Symlinks escaping graph dir are silently skipped. | `data_loader` |

### 175. CAP-175 Novel Fandom Canon Schema

Typed, multi-entity fiction canon for the novel_fandom example application. Pydantic-backed page schemas (Character, Event, Faction, Location) with lane-based immutability (static/dynamic) enforced by a reference-integrity gate. Hand-authored seed canon with cross-linked references and no orphans.

**Feature Request:** FR-637

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-481 | Pydantic models (Character, Event, Faction, Location) validate canon pages. Each model enforces required fields: id, type, lane, references. Character has goals, personality, faction, relationships with typed valence. Event has participants, consequences, valid_from/valid_to for bi-temporal history. | `examples` |
| REQ-YG-482 | Reference-integrity gate rejects pages with orphan references (references that don't resolve to existing canon page ids). Reuses FR-628 gate logic with lane-immutability extension. | `examples` |
| REQ-YG-483 | Lane-immutability gate rejects writes to existing lane:static pages. Dynamic pages (lane:dynamic) can be updated. Gate checks lane field on the existing page and rejects if static and page already exists. | `examples` |
| REQ-YG-523 | Event schema carries an optional integer `sequence` field giving a global total order across all events (FR-690). Optional at the Pydantic layer so genesis/create_event keep validating; mandatory for the Floodmark canon via check_event_sequence, which enforces completeness (every event sequenced), uniqueness (no shared sequence), and year/sequence consistency (a later year never receives an earlier sequence). Arithmetic check, not an LLM task. | `examples` |

### 176. CAP-176 Novel Fandom Enriched World Model

Enriched fiction canon schema extending CAP-175 (FR-637). Adds motivation triad (driving_force/wants/needs/fears/arc_summary/role) and reactive triggers to Character, atmosphere and sensory detail to Location, and a new Rule page type for world constraints. All new fields optional with defaults. Gate validates Rule pages identically to existing types.

**Feature Request:** FR-640

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-484 | Character model extended with role, driving_force, wants, needs, fears, arc_summary, and triggers fields — all optional with defaults. Existing Character pages validate unchanged. | `examples` |
| REQ-YG-485 | Location model extended with location_type, atmosphere, sensory, and significance fields — all optional with defaults. Existing Location pages validate unchanged. | `examples` |
| REQ-YG-486 | Rule page type added to schema and PAGE_MODELS registry. Fields: type, id, lane, domain, title, description, references. Gate validates Rule pages for orphan references and lane immutability identically to other page types. | `examples` |

### 177. CAP-177 Novel Fandom Plot Pathfinder

Plot pathfinder for the novel_fandom example. Given a timeline window and character roster, deterministically retrieves open tensions from canon (unmet goals, fears, internal conflicts, unresolved edges, triggers), then an LLM proposes dramatic beats that traverse those tensions. A gate verifies every beat references only existing canon entities. Traversal-not-invention: the pathfinder creates no new entities.

**Feature Request:** FR-638

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-487 | retrieve_window deterministically filters canon by window and roster, returning roster pages with open tensions (unmet goals, fears, wants≠needs conflicts, unresolved relationship edges, triggers) and applicable world rules. No LLM, no mocks needed for testing. | `examples` |
| REQ-YG-488 | Path gate checks all beat references (actors, references, edge targets) resolve to existing canon entity ids. Beats with orphan references are rejected. Traversal-not-invention enforced. | `examples` |

### 178. CAP-178 Novel Fandom Prose and Close Loop

Prose drafting and close loop for the novel_fandom example. Maps plot path beats to chapter prose (S7), gates prose for entity leaks via LLM-extracted mentions, then extracts edge-level delta ops from chapters and applies them to the dynamic canon (S8). Invariants: carry-forward floor (zero ops = no change), invalidate-not-delete (bi-temporal), lane guard (static pages immutable), target validation (ops must reference existing entities).

**Feature Request:** FR-639

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-489 | apply_deltas supports add_event, add_edge, update_valence, and invalidate_edge operations on the dynamic canon. Each op type individually tested. | `examples` |
| REQ-YG-490 | Carry-forward floor: zero delta ops leave the dynamic canon unchanged. Lane guard: ops targeting lane:static pages are rejected. Target validation: ops referencing non-existent entities are rejected. | `examples` |
| REQ-YG-491 | Invalidate-not-delete: contradicting facts set valid_to on the existing edge, never delete. Bi-temporal reconciliation preserves history. Prose mention gate: extracted entity mentions from prose are checked against canon, non-canon mentions rejected. | `examples` |

### 179. CAP-179 Novel Fandom Wiki Core Types

Premise and Synopsis page types for the novel_fandom canon. Premise is the thematic seed (text, genre_tags, era, themes). Synopsis is full-disclosure reveal-all prose expanding the premise. Both follow the standard canon contract (id, type, lane, references) and are validated by the existing ref_gate. Seed canon includes hand-authored premise and synopsis pages.

**Feature Request:** FR-642

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-492 | Premise page type validates correctly: accepts valid premise data with text field, rejects missing text and invalid lane values, registered in PAGE_MODELS. Seed canon contains at least one premise page. | `examples` |
| REQ-YG-493 | Synopsis page type validates correctly: accepts valid synopsis data with text field, rejects missing text and invalid lane values, registered in PAGE_MODELS. Seed synopsis references premise and passes ref_gate. | `examples` |

### 180. CAP-180 Novel Fandom World Expansion

World expansion pipeline for novel_fandom. Deepens thin entities via LLM, extracts red links (new entity mentions that lack wiki pages), creates skeleton pages for red links, and loops until depth budget is reached. Pipeline decides what to deepen (deterministic thinness filter), LLM generates content, gate validates references. No LLM diagnoses gaps.

**Feature Request:** FR-643v2

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-494 | Schema additions for world expansion: Character has backstory field, all page models have depth field (default 0), depth roundtrips through dict serialization. Seed canon pages are lane:dynamic. worldgen.yaml graph exists and lints clean with all loop_limits specified. | `examples` |
| REQ-YG-495 | World expansion nodes: select_thin identifies thin entities by structural field checks sorted by thin_score, collect_red_links deduplicates new entities by id and filters existing pages, validate_pages gate checks references against merged canon, persist_pages validates against Pydantic models before atomic write, reload_canon reads canon dir at runtime. | `examples` |
| REQ-YG-496 | Reflexion step (FR-646): reflect LLM node reviews canon summaries after deepening and identifies concepts mentioned in prose but lacking pages. missing_entities from reflection merge into collect_red_links alongside new_entities from deepening. Prompt sends page summaries, not full JSON. | `examples` |
| REQ-YG-497 | Event propagation pre-pass (FR-647): anchor_events Python node runs once before the worldgen loop, computing per-character event context with spatial scoping (world/regional/local) and age arithmetic from absolute dates (Character.birth_year, Event.year). Premise gains calendar_note. Deepen prompt enriched with event timeline for characters. | `examples` |
| REQ-YG-498 | Obsidian wiki output (FR-648): render_wiki.py converts canon YAML pages to Obsidian-compatible markdown with YAML frontmatter and body sections. References rendered as [[wiki_links]], relationships as linked lists, prose fields as markdown sections (not frontmatter). Standalone script. | `examples` |
| REQ-YG-499 | Persist boundary normalization (FR-649): normalize_page coerces LLM-varied shapes to schema-expected shapes before Pydantic validation. Covers relationship key variants, participant dicts, consequence dicts, reference dicts, scalar-to-list coercion, Rule.domain default, _map_index strip. Pages that still fail validation are persisted with warning (not dropped). | `examples` |
| REQ-YG-500 | Canon type subfolders (FR-650): canon pages organized into subfolders by type field (canon/character/, canon/event/, etc.). reload_canon and render_wiki use rglob for recursive reading. persist_pages writes into type subfolders with atomic tempfile in same directory. Skeleton exists-check uses rglob across subfolders. ref_gate produces type-prefixed save_path. | `examples` |
| REQ-YG-501 | Deepen temporal fields (FR-651): deepen prompt instructs LLM to set birth_year and role on characters, and year/scope/affected_locations on events, enabling timeline queries. | `examples` |
| REQ-YG-502 | Role enum normalization (FR-652): normalize_page coerces freetext character role to valid enum (protagonist/antagonist/supporting/minor), defaulting to 'supporting'. | `examples` |
| REQ-YG-503 | Robust deepen output (FR-653): persist_pages handles flat-dict deepen results (no updated_page wrapper) by using the result dict itself as the page when it contains id and type fields. | `examples` |
| REQ-YG-504 | Seed depth-0 thin bonus (FR-654): select_thin adds +2 to thin_score for pages with depth 0 or missing depth, prioritizing seed pages for deepening before newly generated skeletons. | `examples` |

### 181. CAP-181 Novel Fandom Genesis Pipeline

Premise-driven world bootstrapping via stub pipeline (FR-667): synopsis (LLM) → stubs (LLM) → validate → persist. Produces minimal entity stubs for worldgen enrichment. FR-655, FR-664, FR-667.

**Feature Request:** FR-655

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-505 | genesis.yaml graph loads premise from file, generates synopsis, and produces entity stubs via generate_stubs LLM node. Validate node checks referential integrity before persist. | `examples/novel_fandom` |
| REQ-YG-506 | generate_stubs prompt converts synopsis into structured stub entities with minimal fields, referential integrity constraint, and typed schema output. | `examples/novel_fandom` |
| REQ-YG-507 | persist_genesis node flattens structured_world output, validates referential integrity (FR-664), and writes each entity to canon/{type}/ via existing persist_pages logic. | `examples/novel_fandom` |

### 182. CAP-182 Agentic Event Deepening

FR-657: Worldgen event-deepening via agent node with canon lookup tools. Events routed to agent with lookup_canon_page, list_canon_ids, and validate_draft tools. Other entity types use existing LLM map node. split_thin_by_type partitions thin_entities by type for routing.

**Feature Request:** FR-657

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-509 | canon_tools.py implements lookup_canon_page (returns YAML + calendar header), list_canon_ids (all IDs with types), validate_draft (returns {valid, errors} checking year sign, participant existence, duplicate IDs). split_thin_by_type partitions thin_entities into thin_events and thin_other. worldgen.yaml routes events to agent node with tools, other types to existing LLM map node. Graph lints clean. | `examples/novel_fandom/nodes/canon_tools.py`, `examples/novel_fandom/nodes/split_thin_by_type.py`, `examples/novel_fandom/worldgen.yaml`, `tests/unit/test_fr657_agentic_event_deepening.py` |

### 183. CAP-183 First-Class Verification

Verification as a first-class DSL construct (FR-677). Guards, previously honored only on llm/router/copilot nodes, are extended to all side-effect node types (shell tool, python, agent) with a compile-time matrix that rejects guards declared on node types that cannot honor them (map, race, subgraph, tool_call, passthrough, interrupt). Side-effect nodes raise GuardHaltError on on_fail=halt (and on exhausted retries) rather than returning an error-state dict, making violations loud at the boundary where they occur. Adds a graph-level verify: block that runs terminal checks before END, and a `graph run --gate` flag that lints before executing and blocks on error-severity issues.

**Feature Request:** FR-677

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-511 | Node guard parity and compile-time matrix. extract_guard_rules / enforce_pre_guards / enforce_post_guards live in the bottom-tier utils.guard_runtime module so Layer-3 tool factories may share the guard contract without crossing import boundaries. Shell tool, python, and agent nodes evaluate guards.pre before execution (halt raises GuardHaltError, skip returns a skip-error state, warn logs) and guards.post after execution (halt raises, retry re-executes bounded by max_retries, warn logs, pass returns output unchanged). Guard halts are not swallowed by on_error=skip. compile_node rejects guards declared on node types outside GUARD_SUPPORTED_TYPES (llm, router, copilot, tool, python, agent) by raising GraphConfigError. | `yamlgraph/utils/guard_runtime.py`, `yamlgraph/compile/node_compiler.py`, `yamlgraph/tools/nodes.py`, `yamlgraph/tools/python_tool.py`, `yamlgraph/tools/agent.py`, `tests/unit/test_fr677_node_guards.py` |

### 184. CAP-184 Novel Fandom Duplicate Entity Prevention

Three-layer defense against duplicate entities in novel_fandom: FR-664 genesis referential integrity gate, FR-665 worldgen semantic entity deduplication, FR-667 genesis stub pipeline. Prevents orphan IDs at genesis boundary and catches parallel-invention duplicates in worldgen map nodes.

**Feature Request:** FR-664

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-512 | validate_referential_integrity checks all cross-reference fields (relationships.to, participants, references, members, affected_locations) resolve to defined entity IDs. Returns orphan_ids list and violations. Warn-only in persist_genesis. | `examples/novel_fandom` |
| REQ-YG-513 | Genesis stub pipeline uses 2 LLM calls (synopsis + stubs). Retired prompts deleted (genesis_roster, genesis_character, structure_world). parse_roster removed. generate_stubs prompt produces minimal entity stubs with referential integrity constraint. | `examples/novel_fandom` |
| REQ-YG-514 | dedup_entities node in worldgen between collect and create_skeletons. Deterministic pass merges possessive variants, the_ prefixes, and stop-word prefix matches. LLM pass gated on red_link_count > 5. Reference rewriting updates dropped IDs in deepened pages. | `examples/novel_fandom` |

### 185. CAP-185 Novel Fandom Ref Integrity Graph-Tool

FR-683: Referential integrity validation extracted to standalone ref_integrity.py and wrapped as ref_check.yaml graph-tool. Wired to worldgen deepen_events agent. Eliminates importlib hack (validate_genesis.py deleted).

**Feature Request:** FR-683

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-515 | validate_referential_integrity extracted to ref_integrity.py, callable as graph-tool (ref_check.yaml) and direct import. JSON-string input normalization at graph-tool boundary. | `examples/novel_fandom` |

### 186. CAP-186 Novel Fandom Genesis Self-Correcting Pipeline

FR-685: Gate-route-fix loop in genesis.yaml. Validate node writes gate_result, conditional edge routes to fix_stubs LLM on orphans, loops back to validate with loop_limits: 3. Happy path stays at 2 LLM calls; each repair round adds 1.

**Feature Request:** FR-685

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-516 | Genesis validate gate uses ref_check (FR-683) to detect orphans. Conditional edge routes to fix_stubs LLM node for repair. persist_genesis retains defense-in-depth warn-only check. | `examples/novel_fandom` |

### 187. CAP-187 Novel Fandom Semantic Dedup Graph-Tool

FR-684: LLM-based semantic entity deduplication as graph-tool. semantic_dedup.yaml compares entity summaries with negative examples. Threshold router in worldgen. dedup_check registered for deepen_events agent. TODO stub and _LLM_DEDUP_THRESHOLD removed from dedup_entities.py.

**Feature Request:** FR-684

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-517 | Semantic dedup graph-tool with LLM prompt including false-positive negative example. Threshold router (>5) in worldgen routes to subgraph → apply_merge_map. dedup_check for agent prevention. | `examples/novel_fandom` |

### 188. CAP-188 Novel Fandom Agent-First Architecture

Genesis and worldgen rewritten as agent nodes that create entities one at a time via tool calls. Graph-tools for semantic validation. Primary showcase for FR-658 type: graph tools called from agent nodes.

**Feature Request:** FR-686

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-518 | Genesis uses a single agent node with creation tools; no type: llm nodes for entity generation. | `examples/novel_fandom/genesis.yaml` |
| REQ-YG-519 | Each create_* tool validates the entity and persists to canon atomically, returning a single-line confirmation or error. | `examples/novel_fandom/nodes/creation_tools.py`, `examples/novel_fandom/create_character.yaml` |
| REQ-YG-520 | Worldgen uses a single agent node with deepen/create tools; no map nodes for entity processing. | `examples/novel_fandom/worldgen.yaml` |
| REQ-YG-521 | Graph-tools (ref_check, dedup_check) self-load canon data; agent passes only IDs or summaries, not full entity data. | `examples/novel_fandom/ref_check.yaml`, `examples/novel_fandom/semantic_dedup.yaml` |
| REQ-YG-522 | Deterministic terminal gate runs ref_check on full canon after agent completion, surfacing orphan refs in final output. | `examples/novel_fandom/nodes/creation_tools.py` |

### 189. CAP-189 Worktree CLI Contract

Canonical executor-neutral worktree lifecycle command in scripts/worktree.sh with verbs new, spike, list, and rm, plus scripts/wt alias wrapper.

**Feature Request:** FR-698

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-524 | scripts/worktree.sh provides new/spike/list/rm lifecycle verbs, usage output, and scripts/wt delegates to canonical command. Spike teardown enforces --note policy and appends notes log. | `scripts/worktree.sh`, `scripts/wt`, `tests/unit/test_worktree_cli_red.py` |

### 191. CAP-191 Instrumentation Worktree Delegation

scripts/copilot_instrument.sh delegates disposable worktree creation and teardown to scripts/worktree.sh instead of private git worktree lifecycle logic.

**Feature Request:** FR-698

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-526 | Copilot instrumentation script uses shared scripts/worktree.sh for create/remove lifecycle and no longer includes direct git worktree add/remove lifecycle commands. | `scripts/copilot_instrument.sh`, `tests/unit/test_copilot_instrument_worktree_delegation_red.py` |

### 192. CAP-192 Branch Deny Guidance Manual Worktree Lane

Pre-command guard branch-create denial guidance includes manual isolated worktree lane command scripts/worktree.sh new <name>.

**Feature Request:** FR-698

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-527 | Branch-create denial text includes manual isolated-work guidance "scripts/worktree.sh new <name>" while keep deny/allow behavior unchanged. | `.github/hooks/scripts/pre-command-guard.sh`, `.github/hooks/tests/test_pre_command_guard.py` |

### 193. CAP-193 Watcher Wrapper JSON Envelope

Watcher worktree setup/teardown wrappers delegate to scripts/worktree.sh while preserving setup JSON envelope keys for FSM context mapping.

**Feature Request:** FR-698

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-528 | worktree_setup.sh forwards topic/prefix/work-dir to scripts/worktree.sh new --json and preserves wt_dir/wt_branch/main_dir/work_dir output contract. worktree_teardown.sh delegates to scripts/worktree.sh rm --dir. | `.chaplain/lib/watcher/worktree_setup.sh`, `.chaplain/lib/watcher/worktree_teardown.sh`, `tests/unit/test_watcher_worktree_wrapper_red.py` |

### 194. CAP-194 Novel Fandom Plot Threads and Throughlines

Derived story layer for the novel_fandom example: plot threads (decomposition by conflict) and throughlines (decomposition by character), extracted from canon by an LLM pipeline and validated by pure mechanical gates. Threads carry a raise/release event ledger walked in `sequence` order (FR-690); throughlines walk a character's emotional deltas over the events they appear in. Gates are arithmetic set/ledger checks, not LLM tasks.

**Feature Request:** FR-691

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-530 | Story gates validate threads and throughlines against canon. Citation integrity: every carrier/source/raise/release id resolves to a canon id. Ledger walk: for each thread, walking its raise/release events in FR-690 sequence order, a release without a prior open raise fails, and status=released requires a non-empty releases list. Cap and distinctness: at most eight threads, each with a distinct carrier set and non-empty opposition. Id stability: regeneration preserves ids for persisting threads and lists every dropped prior id with a reason (no-op on first run). Throughlines: every entry cites a canon event carrying a sequence, entries walk in non-decreasing sequence order, each throughline has at least one slack point or an explicit arc_taut claim, and a major character's arc may not be zero-delta. All gates are pure functions returning {valid, violations}; arithmetic, not LLM tasks. | `examples` |

### 195. CAP-195 Timeframe Recap Demo

Example graph (examples/demos/recap/) that answers "what changed in this repository in a given timeframe?" for any git repository. Deterministic collection via `type: tool` shell nodes (git log --since, --numstat, convention pathspecs); exactly one LLM node synthesizes workstreams, orphan changes (commits without FR/issue references, prompt/graph edits without changelog fragments), and hotspots. YAMLGraph-specific conventions (feature-requests/, changelog/unreleased/) are optional enrichment — a repository without them yields "convention not detected" template input, never an error or hallucinated findings. Mechanizes the Scripture's changelog_first_diagnostic cure as a runnable graph.

**Feature Request:** FR-700

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-531 | The recap demo graph loads, lints clean, and has exactly one LLM node (synthesize) with all collection done by `type: tool` nodes. All git commands use `git -C {repo_path}` (portable to any repo, no reflog syntax, no cwd assumptions). Commit collection is capped (-n 300) with truncation surfaced to the prompt via Jinja2. A repo_path that is not a git repository fails loudly (tool node on_error: fail raises); missing convention paths yield empty output without error. The synthesis prompt uses an inline schema (workstreams, orphans, hotspots) with file-kind partitioning and convention detection done by Jinja2 path heuristics in the template, not by the model (W026-clean: judgement fields only). | `examples` |
| REQ-YG-534 | Disposition axis and mechanized orphan detection (FR-702). fr_statuses tool collects verbatim FR Status lines at HEAD via anchored git grep (^**Status, -m 1 per file); git grep exit 1 (no matches / no convention) is normalized to success at the boundary while exit >=2 (not a repo) fails loudly. Workstream lines carry verbatim [Status: ...] tags — the model never infers disposition. Commit reference detection is a deterministic type:python pre-pass (nodes/partition.py, pattern (FR\|NC)-[0-9]+\|#[0-9]+ anywhere in subject) splitting commits into referenced/unreferenced state keys; mid-subject references can no longer be flagged as orphans. Schema stays at three fields (W026). | `examples` |
| REQ-YG-535 | Status join as deterministic post-pass (FR-703). attach_statuses runs after synthesize: parses fr_statuses grep lines to an id->status map (path and **Status:** prefix stripped, duplicate id first-wins) and appends [Status: ...] to each workstream line by joining ALL FR/NC ids found (finditer, IGNORECASE) — single tag when statuses agree, per-id tags when they differ, [no FR status] when no id resolves, untouched when the line names no id. The post-pass normalizes recap at its boundary (dict or Pydantic model). The synthesis prompt carries no disposition instructions and no fr_statuses input; it does carry a full-id formatting bound (no range/slash shorthand) so mechanical extraction cannot be starved. The model can no longer fail the join. | `examples` |
| REQ-YG-536 | Orphans bypass the model (FR-704). finalize_recap post-pass copies the unreferenced commit lines bit-exact into recap.orphans (zero model transit — kills the reproducible one-character hash corruption 703b72d->703b72e observed in two field runs) and appends deterministic convention orphans: graph/prompt-path churn entries when the window added no changelog fragment. The synthesis schema carries only judgement fields (workstreams, hotspots); the prompt has no orphan or copy instructions and no unreferenced input. Integration asserts the orphan hash field by exact equality — tolerant matching is for LLM output and orphans no longer are. | `examples` |

### 196. CAP-196 Novel Fandom World Pressure

Deficit-driven world-building layer for the novel_fandom example: an additive pass that grows canon with antagonistic structure (kinship trees, a trade network) bounded by the FR-691 plot threads. Two pure mechanical gates enforce the pass: admission (a newly created entity must cite the live thread(s) it pressurizes) and kinship reciprocity (a directed kinship edge must be acknowledged by a reverse edge). Gates are set-membership checks, not LLM tasks. Schema gains an optional `pressurizes` field on world entities.

**Feature Request:** FR-692

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-532 | World-pressure admission gate. A newly created world entity is admitted only if it carries a non-empty `pressurizes` list and every cited thread id resolves to a live plot thread. Entities citing zero threads, a missing `pressurizes` key, or a nonexistent thread id are rejected; each violation names the offending entity and (for dangling citations) the missing id. Runs over the pass's candidate entities only — pre-existing canon is exempt from retroactive citation. Schema carries an optional `pressurizes` field (default empty) on Character, Faction, and Location so pre-existing pages validate. Pure function returning {valid, violations}. | `examples` |
| REQ-YG-533 | Kinship reciprocity gate. For every directed relationship `A --kind--> B` whose kind is in a bounded reciprocal-kind set (mother, father, clanmate), some reverse edge `B --*--> A` of any kind must exist — reciprocity means mutual acknowledgment, not identical reverse kind. Non-reciprocal-kind edges are ignored. Each violation names the source, target, and kind. The FR-692 repair adds the reverse edges additively to canon. Pure function returning {valid, violations}. | `examples` |

### 197. CAP-197 Novel Fandom Event Revision

Latent-thread closure layer for the novel_fandom example: an additive pass that gives every latent plot thread on-page events (a raise and a release) or an explicit waiver. Three pure mechanical gates enforce it — latent closure, waiver integrity, and byte-identity of pre-existing event files — and the create_event tool is taught to emit a total-order `sequence` value (FR-690) so revision events carry it while genesis/worldgen creates that omit it still validate. Gates are set/dict computation, not LLM tasks.

**Feature Request:** FR-693

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-537 | Latent-thread closure and waiver integrity. Every thread with status=latent must carry a non-empty raises AND releases list, or its id must appear in the waiver set — the exit condition is zero unwaived latents, not zero latents. Each waiver must name a live thread id (ref check against the current thread set) and carry a non-empty reason and decided_by; dangling or under-documented waivers are violations. Non-latent threads are ignored. Pure functions returning {valid, violations}. | `examples` |
| REQ-YG-538 | Additive event revision. The create_event tool emits an optional `sequence` field when supplied (int total order, FR-690) and omits it otherwise so genesis/worldgen creates keep validating. A byte-identity gate over pre-existing event-file snapshots ({id: bytes} before/after) flags any pre-existing file whose bytes changed or that vanished; new files are permitted (revision is additive-only). Pure functions returning {valid, violations}. | `examples` |

### 198. CAP-198 Persistent Bridge Loop

One long-lived event loop thread (yamlgraph-bridge-loop) owned by the graph runtime bridges all sync→async node work (race, router-race, future async paths), replacing the per-invocation daemon-thread + asyncio.run() topology. Eliminates per-call thread churn and fresh-loop SDK reconnects (FR-711: anthropic Δp50 +0.527 s → +0.073 s locally) and makes the FR-707 shutdown-blocker and FR-712 loop-affinity defect classes unreachable by construction. The verdict-first contract, CLEANUP_GRACE drain bound, and RuntimeError-on-budget-breach semantics are preserved unchanged.

**Feature Request:** FR-713

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-541 | Persistent bridge loop substrate. Exactly ONE yamlgraph-bridge-loop daemon thread across N sequential bridge invocations; started lazily on first use, never at import; os.register_at_fork resets the loop handle and the LLM cache (with fresh locks) so a fork after warm-up gets a fresh lazy loop in the child; a dead loop thread is restarted lazily with a WARNING. The post-verdict drain is scoped to the invocation's own tasks (ContextVar task bucket via loop task factory) — concurrent invocations never wait on or WARN about each other's tasks. On verdict_budget breach the bridge cancels the submitted work so the abandoned coroutine cannot outlive cancellation + CLEANUP_GRACE (FR-708 leak-lifetime bound preserved). Client construction happens on the caller thread, never on the shared loop (head-of-line blocking); per-candidate construction failures are pre-errors in race accounting, not node failures. | `yamlgraph/utils/bridge.py`, `yamlgraph/node_factory/race_node.py`, `tests/unit/test_fr713_persistent_bridge.py` |

### 199. CAP-199 Security and Coverage Gate Truth

Every documented quality claim has an enforcing gate. Bandit (medium+ severity) runs in pre-commit over yamlgraph/; all suppressions use # nosec markers confessed in docs/confessions.md exactly like ruff noqa (the confession scanner counts both dialects). The coverage threshold documented in CLAUDE.md equals the value enforced by pytest --cov-fail-under.

**Feature Request:** FR-714

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-542 | Gate-truth alignment (FR-714). The bandit pre-commit hook blocks medium+ severity findings; the five standing suppressions (B701 prompt-template jinja, 2x B104 dev-server bind defaults, B108 FSM socket prefix, B602 shell tool) carry nosec markers with confession entries. scripts/noqa_coverage.py counts nosec markers (specific and blanket) alongside noqa; an unconfessed nosec fails --strict. The documented coverage threshold in CLAUDE.md matches the enforced --cov-fail-under value (85; measured 90.36% on 2026-07-12). | `scripts/noqa_coverage.py`, `tests/unit/test_fr714_bandit_gate.py` |

### 200. CAP-200 Prompt Request Front Door

The prompt-execution front door takes one typed object. PromptRequest (frozen dataclass in executor_base) is the single source of truth for the execution parameter set; execute_prompt keeps its public keyword signature as a thin constructor, PromptExecutor.execute consumes the object, and the async front door's parameter set is a subset of the dataclass fields. Signature-parity witnesses make three-places drift (the max_tokens/thinking_budget history) structurally impossible.

**Feature Request:** FR-715

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-543 | PromptRequest signature parity (FR-715). execute_prompt's keyword parameters equal PromptRequest's field names exactly; defaults are defined once on the dataclass and mirrored by the public signature; PromptExecutor.execute accepts only the request object; execute_prompt_async's parameters are a subset of the field set. The jscpd clone between execute_prompt and PromptExecutor.execute is deleted and must not return. | `yamlgraph/executor.py`, `yamlgraph/executor_base.py`, `tests/unit/test_fr715_prompt_request.py` |

### 201. CAP-201 Pre-emptive Module Splits

Size-gate pressure relieved at chosen seams before the 450 gate forces an unplanned split under deadline pressure. graph_schema.py bisected into node-config models (node_schema.py) and graph-level models; public names re-exported unchanged from yamlgraph.models. The stream-event translation loop extracted from run_graph_streaming_native (was CC 17) into streaming_events.py as pure functions, isolating the FR-057..060 streaming scar tissue in a small module.

**Feature Request:** FR-716

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-544 | Module splits at chosen seams (FR-716). node_schema.py holds SubgraphNodeConfig + NodeConfig; graph_schema.py holds EdgeConfig + GraphConfigSchema (< 300 lines); yamlgraph.models re-exports are unchanged. run_graph_streaming_native is below CC 10; translate_message_event in streaming_events.py is a pure function handling subgraph-wrapped and plain message events, node filtering, and FR-058 chunk filtering (tool-call and non-string content dropped); no function in streaming_events reaches CC 10; executor_async.py is below the 400 warn line. | `yamlgraph/models/node_schema.py`, `yamlgraph/streaming_events.py`, `tests/unit/test_fr716_module_splits.py` |

### 202. CAP-202 SMT Condition Verification

Z3-backed linter check family (W803 gap, W804 overlap, W805 shadowed) over expression-edge guard groups. Conditions translate to QF_LRA + equality formulas via the EXISTING condition grammar, with a per-operator encoding faithful to evaluate_comparison's None semantics (comparisons are None→False; ==/!= are None-exempt). Every violation carries a concrete counterexample state. z3-solver is an optional extra (verify); absent z3 yields one skip notice. Solver calls are timeout-bounded.

**Feature Request:** FR-719

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-545 | SMT condition verification (FR-719). Per source node's expression-edge group: W803 fires with a counterexample model (numeric or <missing>) when some state falls through to silent END; groups with an unconditional edge are W803-exempt; W804 reports pairwise-overlapping guards with a witness; W805 reports guards shadowed by earlier guards. Encoding per Judgement F1 table: comparisons carry Not(is_none), == null / != null map to the is_none companion, != lit is Or(is_none, v != lit). Unquoted right-side identifiers encode as variables iff they are known state keys, else string literals (F2). Mixed-sort groups, missing z3, and solver timeouts each produce ONE info notice, never a false verdict. Every emitted counterexample replays true through evaluate_condition (faithfulness witness). | `yamlgraph/linter/patterns/conditions_smt.py`, `tests/unit/test_fr719_conditions_smt.py` |

### 203. CAP-203 ICPC-2 RFE Classifier Example

Map/reason/reduce YAMLGraph example classifying freeform encounter transcripts into ICPC-2 Reason-for-Encounter codes. Cluster fan-out (17 chapters x components 1 and 7, max 34 items) over a catalog GENERATED locally from the Tier-1 ICPC-2e-v7.0 source (Judgement A1: the repo ships the builder with URL + sha256 pin, never the Wonca- copyrighted data); per-cluster LLM verdicts validate at the python reducer boundary; ranking is fully deterministic.

**Feature Request:** FR-722

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-548 | Catalog builder + provenance (FR-722). parse_claml derives rows from Class elements: component from the SuperClass code suffix (<chapter>.<component>), cluster_id = <chapter>-C<component>; chapter headers and process codes (components 2-6) are excluded (phase-1 purge list); every row carries source_tier=1, source_reference=ICPC-2e-v7.0/<code>, provenance_status=verified assigned mechanically. verify_source refuses a zip whose sha256 differs from the pinned digest. | `examples/icpc-2-rfe/nodes/build_catalog.py` |
| REQ-YG-549 | Catalog loader (FR-722). load_rfe_catalog groups rows into chapter x component clusters each carrying its code list; provisional rows are excluded unless include_provisional is set (F6 production-mode default); a missing generated catalog raises FileNotFoundError naming build_catalog.py (A1: usable only after the user-run build step). | `examples/icpc-2-rfe/nodes/catalog.py` |
| REQ-YG-550 | Reducer determinism (FR-722). Candidates validate against a Pydantic model at the reducer boundary (bad shape raises, names the candidate); evidence spans must be substrings of the raw transcript (F3); ranking is verdict rank then confidence then code (total order); multi-label via secondary; no match yields an explicit low_confidence result naming best partials (AC-06); output meta declares catalog_version and catalog_coverage. | `examples/icpc-2-rfe/nodes/reduce.py` |
| REQ-YG-551 | Process codes phase 2 (FR-724). Builder includes components 2-6 process rubrics (chapter "-") as PROC-C<n> clusters, chapter headers still excluded; reducer F4 rule: a process-code match outranks a chapter-code match for RFE primacy (deliberate, witnessed - never asciibetical accident); reducer F1: chapter_context is derived in code as the best-ranked non-process candidate and attached only when the primary is a process code; coverage meta declares components 1-7. | `examples/icpc-2-rfe/nodes/build_catalog.py`, `examples/icpc-2-rfe/nodes/reduce.py` |
| REQ-YG-554 | Labeled crosscheck harness (FR-725). Labels live beside file-based fixtures in data/labeled/ and require rationale plus valid_for_components; evaluate_result enforces primary_any_of, must_include (any surfaced slot including chapter_context and best_partial), must_not_include (primary and secondary only) and tri-state low_confidence_expected; a coverage mismatch between label and result skips loudly by name; archives attribute by fixture basename only (stdin runs never attributed); agreement reports raw k-of-n counts with no significance computation. | `examples/icpc-2-rfe/nodes/crosscheck.py` |
| REQ-YG-555 | Process-code discipline and combined-code composition (FR-727). META_PROCESS_CODES {-43,-46,-48,-69} — encounter-form descriptors and junk drawers, pinned from a full read of all 40 rubric titles — demote match to partial_match at validation time (evidence preserved in best_partial, never primary/secondary; project curation lives in reduce.py, not the generated Tier-1 catalog); genuine process requests (-50, -62) stay primary-capable; process primaries gain combined_code composed mechanically from chapter_context (K86 + -50 = K50; chapter A when contextless); chapter primaries get no combined_code. | `examples/icpc-2-rfe/nodes/reduce.py` |
| REQ-YG-556 | Chapter-code inflation discipline (FR-730). Chapter cap = {Z10} only (empty inclusion list, pure system descriptor - A13/A23/A29 verified genuinely stateable and stay uncapped, A13 an accepted named residual); same-chapter symptom-over-diagnosis mechanizes ICPC practical rule 3 (a component-7 match demotes to partial when a component-1 match exists in the same chapter, P03 demotes P76; no cross-chapter demotion, no demotion without a competing symptom); composition context eligibility is non-process, non-capped, non-Z-chapter with component-7 diseases preferred over component-1 symptoms (opposite of RFE primacy - composition anchors to the problem managed); genuine Z RFEs (Z05) remain classifiable. | `examples/icpc-2-rfe/nodes/reduce.py` |

### 204. CAP-204 CWE Vulnerability Classifier Example

Second instance of the coded-classification pattern (reference/patterns/coded-classification.md): map/reason/reduce YAMLGraph example classifying free-text vulnerability descriptions into CWE weakness codes. View-699 category fan-out (40 categories of which 39 brief — CAT-1225 Documentation Issues is entirely Prohibited and drops out; 399 live members, 345 candidates after the build-time Prohibited strip) over a catalog GENERATED locally from cwec_v4.20.xml (versioned URL + sha256 pin; MITRE CWE is free with attribution); per-cluster LLM verdicts validate at the python reducer boundary; ranking is fully deterministic; the crosscheck harness scores against NVD gold labels partitioned by MITRE's own Mapping_Notes usage.

**Feature Request:** FR-733

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-557 | Catalog builder + provenance (FR-733). parse_cwec derives rows from Weakness elements of cwec_v4.20.xml (Deprecated skipped: 969 total, 944 live); cluster_ids = CAT-<category id> for each view-699 Has_Member (multi-membership duplicates the code into every member cluster; other View_IDs never count); Prohibited codes keep their catalog row but get NO cluster membership — stripped from candidacy at BUILD time, never shown to the model (F3); every row carries abstraction, mapping_usage, ChildOf parents, source_tier=1, source_reference=cwec_v4.20/<code>; coverage meta declares view 699 / candidates 345 / excluded_prohibited 54 / catalog_total 944 (F1); check_pins asserts two-level usage counts (catalog-wide live 58/44/93, in-population 54/5/13 — F5, corrected at enforce: the judgement's 83 counted Deprecated rows) so a catalog bump is loud; verify_source refuses a zip whose sha256 differs from the versioned pin (cwec_latest is a moving pointer). | `examples/cwe-classifier/nodes/build_catalog.py` |
| REQ-YG-558 | Catalog loader (FR-733). load_cwe_clusters groups rows into view-699 category clusters via each row's cluster_ids (multi-membership rows appear in every member cluster; Prohibited rows, having no memberships, never reach a brief); briefs render code — title \| description only (F4: Description-only; caps are code-side, usage/abstraction never shown to the model); a missing generated catalog raises FileNotFoundError naming build_catalog.py. | `examples/cwe-classifier/nodes/catalog.py` |
| REQ-YG-559 | Reducer determinism (FR-733). Candidates validate against a Pydantic model at the reducer boundary; evidence spans align to the input description via the icpc _align_span discipline (case-fold + quote-strip + difflib repair >= 0.85, below the floor raises); bare numeric codes repair to CWE-<n> when the prefixed form is in the catalog (sigil analog), anything else — including Prohibited codes, absent from all clusters — raises not-in-catalog; Discouraged match claims demote to partial_match with evidence preserved (capped, primary/secondary unreachable); Allowed-with-Review matches stay primary-capable flagged review:true (analyst-assistance posture — review is an outcome, not a demotion); lowest-abstraction guard: a match whose ChildOf descendant (transitive, catalog-derived) is also matched demotes to partial, lone Class matches survive (F2 both directions); per-code dedup keeps best-ranked; no match yields explicit low_confidence naming best partials; meta carries catalog_version and the builder's coverage block. | `examples/cwe-classifier/nodes/reduce.py` |
| REQ-YG-560 | NVD-gold crosscheck harness (FR-733). Labels live beside fixture descriptions in data/labeled/ (cve_id + nvd_cwes + provenance rationale comment, rejected without one); evaluate_result scores surfaced codes against nvd_cwes PARTITIONED by MITRE usage (judgement addendum): a miss on an Allowed/Review gold code is our_miss and fails; a miss on a Discouraged/Prohibited gold code is label_questionable and never fails alone; a fixture whose ENTIRE gold set violates MITRE guidance is gold_unscoreable (passed=None, our primary reported for human read — the "more specific Allowed code than NVD's Discouraged label" success narrative); usage is computed from the generated catalog at evaluation time, committed label files stay raw provenance; agreement reports raw k-of-n counts, no significance. | `examples/cwe-classifier/nodes/crosscheck.py` |
| REQ-YG-561 | Boundary run-mortality fixes (FR-734). Off-population claims — real catalog rows without view-699 membership, volunteered by the model from prior knowledge — divert to meta.off_population_claims (code, usage, verdict, confidence, best-effort spans; unalignable spans recorded raw with span_unverified, never fatal for meta-tier claims); classification slots stay population-only (FR-733 AC-02 pin preserved verbatim); nonexistent codes still raise. Span alignment repairs interior omissions: matching blocks (size >= 3) with character coverage >= 0.85 of the claim, all inside one plausible window (<= max(2x span, span+40)), repair to the true contiguous description window restoring elided text verbatim; scattered fabrications exceed the window cap and raise. Loader returns the merged dict {cwe_clusters, usage_index} covering all catalog rows including Prohibited non-members. | `examples/cwe-classifier/nodes/reduce.py`, `examples/cwe-classifier/nodes/catalog.py` |

### 205. CAP-205 World Distill Graph

Doctrine-infrastructure graph (.chaplain/graphs/world_distill) that refreshes docs/world-context.md — the philosopher's world-grounding input, stale since 2026-03-13. Curated ecosystem feeds (RSS + HN keyword-filtered) → single distill LLM node with inline schema → dated markdown file. Zero-yield raises at both boundaries (Commandment 6); distill input capped at title + source + 500-char excerpt per article (F3).

**Feature Request:** FR-744

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-563 | world_distill graph: fetch from curated ecosystem feed config, per-feed failure tolerated but zero total yield raises ValueError; prepare_distill_input caps each article at title + source + 500-char excerpt; distill LLM node uses inline schema (highlights, themes, open_questions); write_context renders dated header ("Last updated: YYYY-MM-DD") + prose sections and REFUSES an empty distill result. now.py displays the world pointer with age and STALE label past 14 days. | `.chaplain/graphs/world_distill` |

### 206. CAP-206 FR Triage Graph

Doctrine-infrastructure graph (.chaplain/graphs/fr_triage) running the mechanizable checklist tier on a Proposed FR: canon pass (≤3 one-line answers), pre-mortem witnesses (≤5 single lines), value-prop check. Output appended INSIDE the FR as dispositionable [pending] claims — never a verdict, never a Status change (authority_is_not_a_checklist). Reminder-only hook line at FR creation; disposition gate fires only at Status Judged+ with pending claims. Kill criterion: reviewed after the 10th judged FR carrying triage; survival must be earned in the calibration ledger (FR-745 F2).

**Feature Request:** FR-745

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-564 | fr_triage graph: triage prompt with inline schema (canon_answers list ≤3, pre_mortem_witnesses list ≤5, value_prop_check) at haiku-class model; append_triage writes a "## Triage" section with [pending] markers and REFUSES to modify the Status line or append to a non-Proposed FR; empty triage output raises (zero-yield, Commandment 6); triage_gate blocks commits where an FR's Status is Judged-or-later while [pending] triage claims remain. | `.chaplain/graphs/fr_triage` |

### 207. CAP-207 Loader Error UX

Boundary errors at the config-parsing layer name their fix (FR-747; the two FR-744 field incidents). A prompt YAML using a `messages:` role list raises the prompt contract in load_prompt (parsed-structure detection: top-level key AND absent system:/user: — never text grep); a `module:` import failure hints `path: <mod>.py` only when the file exists next to the graph (verified existence, never speculation); `graph lint` surfaces both defects pre-run (E006/E008).

**Feature Request:** FR-747

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-565 | Loader error UX: load_prompt/load_prompt_path raise an actionable ValueError on a messages: role-list prompt (both conditions, parsed structure); python_tool ImportError gains the path: hint only when <module>.py exists under graph_root, otherwise the error is unchanged; lint E006 flags the messages contract and E008 flags module: shadowed by a graph-local file, with no false positives on valid prompts using a `messages` variable. | `utils/prompts`, `tools/python_tool`, `linter/checks_loader_ux` |

### 208. CAP-208 FR Atlas Onboarding Demo

Portable onboarding atlas demo (examples/demos/fr-atlas): renders any project's feature-requests/ corpus as a newcomer narrative — 8-15 theme arcs ordered by last git activity, module axis joined mechanically (CAP registry where present, path regex otherwise), a 3-paragraph story opener whose input is the taxonomy never the raw corpus, and a graveyard section of rejected FRs. Pipeline copies the recap discipline: deterministic collection, three bounded LLM judgements (chunk themes, merge, story), code-side joins with count-in == count-out asserted.

**Feature Request:** FR-748

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-566 | FR Atlas deterministic spine (FR-748). Collector: population id = filename stem, never a prefix regex (unprefixed elder files are population members — the graveyard exemplars); TEMPLATE.md and *.judgement.md companions excluded and counted in parse_notes; headerless files reported by id, never dropped; digests carry verbatim Status line, first-word status_bucket with visible other, and a Problem/Summary excerpt; a missing feature-requests/ dir raises naming the path. Chunker: every population id appears in exactly one chunk. Coverage post-pass: themes referencing unknown ids raise; duplicate assignments keep the first occurrence; unassigned ids land in an explicit misc theme; total assigned count equals population count (silent join drops impossible). Render: graveyard section lists exactly the rejected-bucket FRs with verbatim status lines. | `examples/demos/fr-atlas/nodes/collect.py`, `examples/demos/fr-atlas/nodes/coverage.py`, `examples/demos/fr-atlas/nodes/render.py` |

### 209. CAP-209 Root Package Seams

Layer 2's implicit module clusters are named packages with enforced boundaries: a2a/ (protocol server + message translation), export/ (skills + MCP), compile/ (YAML-to-LangGraph pipeline). Import-linter contracts make the seams load-bearing — a2a and export are leaf consumers the linter and compile pipeline never import; compile never imports the leaf surfaces. Moves are rename-witnessed; public top-level re-exports are unchanged.

**Feature Request:** FR-717

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-567 | Root-package seams (FR-717). yamlgraph.a2a, yamlgraph.export and yamlgraph.compile exist as packages holding their clusters (module names preserved in compile/); .importlinter carries a2a-seam, export-seam and compile-seam forbidden contracts plus the collapsed three-layer contract; lint-imports keeps >= 5 contracts; root yamlgraph/*.py module count <= 17; deep import paths updated repo-wide (code, tests, capabilities, confessions, hedging allowlist, docs). | `yamlgraph/a2a`, `yamlgraph/export`, `yamlgraph/compile`, `tests/unit/test_fr717_seams.py` |

### 210. CAP-210 Edge Shape Classification

Edge compilation is classify-then-dispatch: classify_edge names every edge form as an explicit EdgeShape (START, PARALLEL_FANOUT, MAP_TO_MAP, TO_MAP, FROM_MAP, ROUTER_CONDITIONAL, EXPRESSION, PLAIN — PLAIN is a member, not a fall-through claim), and per-shape compilers are registered in a dispatch table. An unnameable shape (fan-out list with a condition but no type: conditional — previously compiled with the condition silently dropped) raises naming the edge. The condition-map assembly for router and expression edges is extracted as pure functions, unit-testable without a compiled graph.

**Feature Request:** FR-718

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-568 | Edge-shape classification (FR-718). classify_edge is pure and exhaustive over the EdgeShape enum (member set asserted, so a new shape must register itself); classification order preserves the FR-467/FR-234/FR-060 semantics (conditional-to-map is EXPRESSION; map-to-map ignores condition; interrupt redirect precedes membership tests). A condition on an untyped fan-out list raises ValueError naming the edge instead of silently dropping the condition. No function in edge_compiler reaches CC 10. build_expression_route_mapping and build_router_route_mapping are pure (FR-467 sub-node routing, END always reachable, FR-211 interrupt and subgraph-interrupt redirects). | `yamlgraph/compile/edge_compiler.py`, `tests/unit/test_fr718_edge_shapes.py` |

### 211. CAP-211 Sole-Route Judge and Review Wrappers

The judge and review governance pipelines execute through exactly one operational route each: scripts/judge.sh and scripts/review.sh (ports of csap NC-415/NC-413). Each wrapper serializes runs with an atomic mkdir lock (10-minute stale detection, holder metadata, cleanup on exit), blocks re-entry via lineage sentinels (JUDGE_EXECUTION / REVIEW_EXECUTION), resolves the yamlgraph executor explicitly (YAMLGRAPH_BIN, then PATH, then uv run — failing loudly otherwise), and verifies completion by artifact contract, never exit code: the judge draft must contain a "**Verdict:**" line; the review draft must open with "**Merge verdict:**" on line one. The wrappers contain zero judging or reviewing doctrine — the YAMLGraph adapter graphs under .github/skills/{judge-fr,review-pr}/adapters/ remain the sole execution routes.

**Feature Request:** FR-758

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-569 | Sole-route judge/review wrapper contract (FR-758). Both wrappers exit 64 on usage error and 66 on missing FR; exit 70 when the matching lineage sentinel is set (re-entry guard); exit 73 when a fresh lock is held (printing holder metadata) and 75 on a stale lock (never auto-removing it); remove their lock on exit. The executor resolution order is YAMLGRAPH_BIN over PATH yamlgraph over uv, exiting 69 when none resolves. The artifact contract exits 65 when the draft is missing/empty, when the judge draft lacks a "**Verdict:**" line, or when the review draft's line one is not "**Merge verdict:**"; a conforming artifact from a successful graph run yields exit 0. Contract witnessed by stubbed YAMLGRAPH_BIN tests (no API keys, no real graph execution) plus one recorded manual smoke per wrapper in FR-758. | `scripts/judge.sh`, `scripts/review.sh`, `tests/unit/test_fr758_judge_review_wrappers.py` |

### 212. CAP-212 OpenTelemetry Observability Boundary

Opt-in, vendor-neutral OpenTelemetry span schema for graph-run and node-execution tracing. Disabled by default (no OTEL import, no spans, no behavior change). Enabled via YAMLGRAPH_OTEL_EXPORT=otlp; fails fast before any node executes when enabled but the `otel` extra is not installed. Emits one yamlgraph.graph.run span per invocation with a shared UUIDv7 run identity, sha256 variables hash (never raw values), and success|error|interrupted outcome; child yamlgraph.node.execute spans per node with node name/type, state keys-written (names only), and optional exception-class-name-only error attribute. Node spans are wrapped generically in node_compiler.py (llm, router, tool, python, agent, tool_call, race, passthrough, copilot, subgraph) via node_otel.py, mirroring the node_timeout.py wrapping pattern. LangSmith tracing is unaffected — this boundary is a parallel, vendor-neutral exporter path.

**Feature Request:** FR-759

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-570 | OTEL observability boundary (FR-759). is_otel_enabled() is a pure env-var check (YAMLGRAPH_OTEL_EXPORT=="otlp") that imports nothing; graph_run_span()/node_execution_span() no-op when disabled; OtelExtraMissingError raised before any node executes when enabled but opentelemetry is unavailable; enabled path emits yamlgraph.graph.run (yamlgraph.run.id, yamlgraph.graph.name, yamlgraph.thread.id optional, yamlgraph.variables.hash, yamlgraph.run.outcome) and child yamlgraph.node.execute (yamlgraph.node.name, yamlgraph.node.type, yamlgraph.state.keys_written, yamlgraph.node.error optional) spans sharing one trace id with correct parent/child linkage; variables_hash() is deterministic sha256 of canonical sorted-key JSON and never contains raw values. | `yamlgraph/observability/otel.py`, `yamlgraph/compile/node_otel.py`, `yamlgraph/compile/node_compiler.py`, `yamlgraph/cli/graph_commands.py`, `tests/unit/test_otel_observability.py` |

### 213. CAP-213 Example Dependency Taxonomy Generator

scripts/example_taxonomy_scan.py mechanically discovers every example root under examples/ (every directory at any nesting depth is independently evaluated; a directory qualifies when it contains a structural graph YAML — top-level mapping with a `nodes` mapping key — a Python file with an `if __name__ == "__main__"` guard, or a README.md with a fenced runnable usage command; noise/hidden directories are pruned) and classifies each as extra-backed (every third-party import resolves to a distribution declared in pyproject.toml; the owning extra(s) are recorded) or externally-provisioned (at least one import remains undeclared; the specific package is cited, never silently added to pyproject.toml per FR-762 C-4). Reuses FR-761's scanner internals (import extraction, distribution resolution, PEP 503 normalization) rather than reimplementing them. Local sibling-module imports (the sys.path-insert fixture idiom common in example tests, e.g. `import tools`) are recognized as local, not third-party. Writes examples/dependency-taxonomy.yaml as the generated allowlist; --check mode fails when the committed file drifts from a fresh discovery run.

**Feature Request:** FR-762

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-571 | Example dependency taxonomy contract (FR-762). Root discovery is mechanical: every directory under examples/ at any nesting depth is independently evaluated (nested roots get their own rows even inside another qualifying root); noise and hidden directories are pruned. A candidate becomes a root if it has a structural graph YAML (parsed document is a mapping with a top-level `nodes` mapping key — substring matches on `nodes:` are insufficient, per PR #464 review P1), a Python file with an `if __name__ == "__main__":` guard, or a README.md containing a fenced code block with a recognizable runnable command (python, yamlgraph, pytest, uvicorn, node, npm, docker, make, curl, or go as first token) — mere README existence is not sufficient. Classification has exactly two states, no third: extra-backed (owning extra(s) recorded, None when core-only) or externally-provisioned (specific undeclared distribution cited). Local per-example modules imported via sys.path-insert (matching a .py stem or subdirectory name anywhere under the same root) are excluded from third-party classification. build_taxonomy() and classify_root() accept overridable examples_root/pyproject_path/ repo_root so tests exercise isolated fixture trees, never the live repo. Root discovery is scoped to the git-tracked tree (FR-763): when examples/ sits inside a git work tree, the tracked file set is obtained once from git (never by reimplementing .gitignore semantics) and root markers are evaluated against git-tracked files only, so gitignored generator outputs (e.g. examples/yamlgraph_gen/outputs/*) and untracked half-added examples never become taxonomy rows. Outside a git work tree the scanner warns and falls back to the raw filesystem walk; an unexpected git failure inside a work tree is raised, not silently swallowed. | `scripts/example_taxonomy_scan.py`, `tests/unit/test_example_taxonomy_scan.py` |

### 214. CAP-214 Direct-Import Dependency Scanner

scripts/direct_import_scan.py walks yamlgraph/ (core, strict) plus examples/, scripts/, tests/ (report-only) via AST, extracting every third-party top-level import (including nested/lazy imports inside functions and try/except blocks) and verifying each resolved distribution is declared somewhere in pyproject.toml — core dependencies OR any optional extra, never charging an optional-extra import to core (FR-761 C-4). Distribution-name comparison is PEP 503-normalized (langchain_anthropic == langchain-anthropic). A small, explicit PENDING_GAPS table tracks imports already dispositioned to a sibling FR (FR-760's langchain-core, FR-762's litellm/starlette/ protobuf) so the gate blocks only genuinely new undeclared core imports. --strict exits 1 on any non-pending core failure; report-only findings never fail the gate.

**Feature Request:** FR-761

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-572 | Direct-import scanner contract (FR-761). AST-based extraction catches nested/lazy imports, not just top-level statements. stdlib modules (via sys.stdlib_module_names) and first-party top-level packages are excluded. Import names are resolved to distribution names via an alias table (yaml->pyyaml, google-> protobuf, bs4->beautifulsoup4, z3->z3-solver, etc.) then compared against declared dependencies using PEP 503 normalization so underscore/hyphen variants match. yamlgraph/ imports are core (strict); examples/, scripts/, tests/ are report-only and never fail --strict. PENDING_GAPS entries are always reported but never block --strict, and a stale entry becomes harmless once its owning FR declares the dependency (no code change required — it simply stops matching the undeclared branch). scan() accepts overridable repo_root/pyproject_path/core_roots/report_only_roots/pending_gaps so tests exercise isolated fixture trees, never the live repo. | `scripts/direct_import_scan.py`, `tests/unit/test_direct_import_scan.py` |

### 215. CAP-215 Style-Convert Pipeline

Sibling example to image_pipeline that restyles an existing prompt file into a single target art style. It loads one prompt per nonblank line, rewrites each prompt's medium/style/artist references via a Mistral-pinned map node with a structured prompt_text schema, and reuses image_pipeline's save_prompts_node to write a one-prompt-per-line output file. It is fail-fast: if any conversion branch fails, a validate_conversions gate aborts the run before save_prompts writes, so N in == N out or nothing is written.

**Feature Request:** FR-764

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-573 | Style-convert graph chains load_prompts (Python tool reading UTF-8 text, one prompt per nonblank line, stripping only leading "N. " enumerators, raising ValueError on missing/empty input and never writing the source) → convert_styles (map over prompts, LLM sub-node pinned to Mistral on the graph node with a structured schema exposing prompt_text: str) → validate_conversions (fail-fast gate that raises if any branch failed) → save_prompts (reused examples.image_pipeline.nodes.save_prompts.save_prompts_node, unchanged) → END. Successful runs preserve exact prompt count; a branch failure aborts the run before save_prompts writes, so no partial output file is produced. | `examples/style_convert`, `tests/unit/test_style_convert.py` |

### 216. CAP-216 Tool Manifests

Tool declarations reusable across graphs via manifest files: a `manifest:` key in a `tools:` entry loads a typed manifest YAML and translates it into the equivalent inline shell/python/graph tool declaration at graph load. Translation only — no new execution engine (FR-768).

**Feature Request:** FR-768

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-574 | `tools.<name>.manifest` resolves relative to the referencing graph; runtime paths inside a manifest resolve relative to the manifest file. Manifest YAML is validated through typed models at graph load: missing files, invalid YAML, unknown runtime types, unknown/conflicting fields, and tool-key/name mismatches fail before invocation. Shell, python (path and module), and graph runtimes translate to configs equivalent to their inline declarations; inline declarations load unchanged. | `tools`, `graph_loader` |

### 217. CAP-217 Shared Vision Tool

Multimodal image→text capability in examples/shared: describe_image() sends a local image or URL plus an instruction through a create_llm() chat model and returns a validated ImageDescription (title, description, tags, optional QA verdict). Provider allowlist (google, anthropic) enforced before invocation; no success-shaped fallbacks (FR-769).

**Feature Request:** FR-769

| Requirement | Description | Key Modules |
|------------|-------------|-------------|
| REQ-YG-575 | describe_image(image, instruction, *, provider, model) accepts a local path (base64 data-URL content part; missing file raises naming the path) or URL (passed through as URL content part), builds a multimodal message with the instruction as text part, constructs the model via create_llm() only, and validates output into ImageDescription. Unsupported providers raise ValueError naming the provider and the supported set before any LLM invocation; malformed output raises a validation error rather than returning a partial result. | `examples` |

<!-- END GENERATED CAPABILITIES -->

### 75. Portable Chaplain (FR-196)

Path-based Python tool loading and Chaplain subsystem portability.

**Feature Request:** FR-196

| REQ-YG-196 | PythonToolConfig supports path field (mutually exclusive with module) for file-path-based Python tool loading via spec_from_file_location; when graph_root is provided, relative paths resolve from graph root and both relative/absolute out-of-root paths are rejected; validation rejects both-set and neither-set; parse_python_tools accepts path or module in YAML tool definitions | `yamlgraph/tools/python_tool.py`, `tests/unit/test_python_nodes.py` |

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
| `utils/llm_factory.py` | Multi-provider LLM factory (12 providers) | 3 |
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
