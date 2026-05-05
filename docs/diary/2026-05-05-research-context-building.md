# Research: The Context Building Problem

**Date:** 2026-05-05
**Author:** Philosopher session
**Status:** Research complete, proposal ready for evaluation

## Problem Statement

Every LLM session starts at zero. The agent sees a codebase for the first time — every time. How do you give a blind agent enough architectural understanding to work competently within the first ~2K tokens of context?

The Chaplain's enforce agent currently spends 3-5 tool calls (grep, read_file, list_dir) just *orienting* itself before doing productive work. This burns tokens, adds latency, and produces non-deterministic starting conditions across runs.

## Landscape of Approaches

| Approach | Mechanism | Who | Strength | Weakness |
|----------|-----------|-----|----------|----------|
| CLAUDE.md / AGENTS.md | Static prose in repo root | Claude Code, Copilot | Always loaded, human-authored | Stale, grows unwieldy, <200 lines recommended |
| Repo Map (Aider) | tree-sitter AST → symbol signatures → graph-rank → top-K | Aider | Adaptive to token budget, shows API surfaces | Only code structure, no intent/architecture |
| Path-scoped rules | Load rules only when touching matching files | Claude Code `.claude/rules/` | Reduces noise | Must be pre-authored per path |
| Auto memory | Agent writes notes for future self | Claude Code | Zero human effort | Unpredictable, not shareable |
| Vectorstore / RAG | Embed chunks → retrieve on query | Various | Scales to any size | Retrieval accuracy varies, no structure |
| Glob + Grep | Shell out, search text | YAMLGraph copilot nodes | Simple, deterministic | No ranking, floods context |
| `/init` flow | Agent explores codebase, proposes CLAUDE.md | Claude Code (new) | Bootstrap from nothing | One-shot, quickly stale |

## How Aider Does It (Repo Map)

Source: https://aider.chat/docs/repomap.html, https://aider.chat/2023/10/22/repomap.html

1. **Parse** all source files with tree-sitter (language-aware AST)
2. **Extract** symbol definitions: classes, functions, methods with signatures
3. **Build** a reference graph: file A imports symbol from file B → edge A→B
4. **Rank** symbols using PageRank-style algorithm (most-referenced = most important)
5. **Select** top-K symbols that fit within configurable token budget (default ~1K tokens)
6. **Output** shows HOW symbols are defined (not just names) — critical source lines

Key insight: the repo map shows the *skeleton* of the codebase — public API surfaces and their interconnections. An agent reading it understands "who depends on whom" without reading implementation details.

## How Claude Code Does It (Memory System)

Source: https://code.claude.com/docs/en/memory

Two complementary systems, both loaded at session start:

### CLAUDE.md (human-written)
- Target: <200 lines per file
- Scope: project, user, or organization
- Content: build commands, conventions, project architecture
- Loading: full file at session start, subdirectory files on-demand
- `@path/to/import` syntax for pulling in additional files
- Path-scoped `.claude/rules/*.md` with glob frontmatter for conditional loading

### Auto Memory (LLM-written)
- Storage: `~/.claude/projects/<project>/memory/MEMORY.md` + topic files
- Loading: first 200 lines of MEMORY.md at session start; topic files on-demand
- Content: build commands, debugging insights, architecture notes, preferences
- Agent decides what's worth remembering; no manual effort

### Key Design Principles
- CLAUDE.md is context, not enforcement — adherence correlates with specificity and brevity
- Specific > vague: "Use 2-space indentation" beats "format code properly"
- Structure matters: markdown headers and bullets scanned like human readers
- Contradictions resolved arbitrarily — consistency across files is critical
- Survives `/compact`: project-root CLAUDE.md re-read from disk after compaction

## What YAMLGraph Does Today

| Artifact | Lines | Purpose | Loaded when |
|----------|-------|---------|-------------|
| `CLAUDE.md` | 438 | Build commands, architecture overview, anti-patterns | Every session |
| `.github/copilot-instructions.md` | 189 | Scripture, traps, cures, process doctrine | Every Copilot session |
| `ARCHITECTURE.md` | 2221 | Requirements, capabilities, design philosophy | Referenced, not auto-loaded |
| `reference/getting-started.md` | 232 | Node types, CLI, key patterns (AI context summary) | Referenced by CLAUDE.md |
| Copilot node prompts | varies | Task-specific context (FR path, worktree, branch) | Per-invocation |

**Total context loaded: ~630 lines** (CLAUDE.md + copilot-instructions.md). This tells the agent HOW to behave but not WHERE things are for a specific task.

## The Gap: Nobody Does Tier 2 Well

Context is a spectrum with three tiers:

```
           LOW COST / ALWAYS LOADED          HIGH COST / ON-DEMAND
┌──────────────────┬───────────────────┬────────────────────────────┐
│  Tier 1          │  Tier 2           │  Tier 3                    │
│  CLAUDE.md       │  Context Planner  │  Runtime Grep/Read         │
│  (conventions,   │  (task-relevant   │  (agent explores           │
│   process,       │   module sigs,    │   at will during           │
│   commands)      │   test locations, │   implementation)          │
│                  │   dep graph)      │                            │
│  ~200 lines      │  ~100-200 lines   │  Unbounded                 │
│  ~500 tokens     │  ~500-2000 tokens │  ~5000+ tokens             │
│  Updated: human  │  Updated: CI hook │  Updated: realtime         │
│  Scope: ALL      │  Scope: THIS TASK │  Scope: THIS LINE          │
└──────────────────┴───────────────────┴────────────────────────────┘
```

- **Tier 1** tells the agent HOW to behave (conventions, commands)
- **Tier 2** tells the agent WHERE things are for THIS task (module map, test locations)
- **Tier 3** lets the agent read WHAT the code actually says (full source)

Aider's repo map is Tier 2 but globally ranked, not task-adaptive. Claude Code's path-scoped rules are task-adaptive but manually authored. **The gap is automated, task-adaptive Tier 2.**

## Proposal: The Context Planner

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONTEXT PLANNER PIPELINE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    ┌──────────────┐    ┌────────────────┐        │
│  │  Task    │───▶│  Relevance   │───▶│  Context       │        │
│  │  Input   │    │  Classifier  │    │  Assembler     │        │
│  └──────────┘    └──────────────┘    └────────────────┘        │
│       │                 │                     │                  │
│       │                 ▼                     ▼                  │
│       │          ┌──────────────┐    ┌────────────────┐        │
│       │          │ Module Map   │    │  Assembled     │        │
│       │          │ (static,     │    │  Context Blob  │───────▶│
│       │          │  pre-built)  │    │  (~2K tokens)  │ OUTPUT │
│       │          └──────────────┘    └────────────────┘        │
│       │                 ▲                     ▲                  │
│       │                 │                     │                  │
│       │          ┌──────────────┐    ┌────────────────┐        │
│       └─────────▶│ Dependency   │    │  Test Map      │        │
│                  │ Graph        │    │  (module→test)  │        │
│                  └──────────────┘    └────────────────┘        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Component 1: Module Map (static artifact, generated)

A pre-built YAML index of the codebase. Generated by `scripts/generate_module_map.py` using `ast.parse()`. ~200 lines. Updated by CI or pre-commit hook.

```yaml
# reference/module-map.yaml (auto-generated)
generated: "2026-05-05T10:00:00Z"
token_estimate: 450

modules:
  yamlgraph/graph_loader.py:
    lines: 385
    exports:
      - "load_graph_config(yaml_path: str | Path) -> GraphConfig"
      - "compile_graph(config: GraphConfig) -> CompiledGraph"
    imports_from: [node_factory, models.config, models.state_builder, utils.llm_factory]
    imported_by: [cli.commands, mcp_server, a2a_server]

  yamlgraph/executor.py:
    lines: 280
    exports:
      - "execute_prompt(prompt_name: str, variables: dict, **kwargs) -> str | BaseModel"
    imports_from: [utils.llm_factory, utils.prompts, models.schemas]
    imported_by: [node_factory.llm_nodes, node_factory.base]

  yamlgraph/node_factory/:
    purpose: "Node creation dispatch — each module handles one node type"
    submodules:
      llm_nodes.py: {exports: [create_llm_node], lines: 180}
      copilot_node.py: {exports: [create_copilot_node], lines: 370}
      router_race_node.py: {exports: [create_router_race_node], lines: 145}
      race_node.py: {exports: [create_race_node], lines: 210}
      subgraph_nodes.py: {exports: [create_subgraph_node, create_map_node], lines: 195}
      control_nodes.py: {exports: [create_passthrough_node, create_gate_node], lines: 90}

test_map:
  graph_loader: [tests/unit/test_graph_loader.py]
  executor: [tests/unit/test_executor.py]
  node_factory.copilot_node: [tests/unit/test_copilot_node.py]
  node_factory.race_node: [tests/unit/test_race_node.py]
  models.state_builder: [tests/unit/test_state_builder.py]
```

**Generation cost:** One 30-line Python script using `ast.parse()`. Runs in <1 second. No external dependencies (tree-sitter optional for richer output, stdlib `ast` sufficient for Python-only codebase).

### Component 2: Relevance Classifier (cheap LLM call)

A small, fast model (haiku/flash) reads task description + module map and selects which files matter:

```yaml
# prompts/context-planner.yaml
system: |
  You are a context selection agent. Given a task description and a module map,
  identify which source files, test files, and documentation are relevant.
  Be precise: include only files the implementing agent will need to read or modify.
  Never include more than 15 files.

user: |
  ## Task
  {{ task_description }}

  ## Module Map
  {{ module_map }}

  ## Available Documentation
  - reference/graph-yaml.md (graph YAML schema, node types, edges)
  - reference/prompt-yaml.md (prompt templates, Jinja2, schemas)
  - reference/getting-started.md (patterns overview)
  - ARCHITECTURE.md (design philosophy, requirements)

  Select the relevant context for this task.

schema:
  name: ContextPlan
  fields:
    source_files:
      type: list[str]
      description: "Source files to read (full paths)"
    test_files:
      type: list[str]
      description: "Test files to read or modify"
    doc_sections:
      type: list[str]
      description: "Documentation files relevant to this task"
    key_symbols:
      type: list[str]
      description: "Functions/classes the agent should understand before starting"
    rationale:
      type: str
      description: "One sentence explaining the selection strategy"
```

**Cost:** ~500 input tokens (task + map) + ~200 output tokens. Flash/haiku: <$0.001. Sub-2 second latency.

### Component 3: Context Assembler (deterministic Python tool)

Takes ContextPlan and builds the context blob:

```python
def assemble_context(state: dict) -> dict:
    """Read selected files, extract key symbols, build context string."""
    plan = state["context_plan"]
    sections = []

    # Source file signatures (exports + docstrings, not full code)
    for path in plan["source_files"]:
        signatures = extract_signatures(path)  # ast.parse → function/class defs
        sections.append(f"## {path}\n{signatures}")

    # Test file names (so agent knows WHERE to write tests)
    for path in plan["test_files"]:
        if Path(path).exists():
            test_names = extract_test_names(path)  # ast.parse → def test_*
            sections.append(f"## {path} (existing tests)\n{test_names}")
        else:
            sections.append(f"## {path} (NEW — create this file)")

    # Doc sections (first 50 lines of relevant docs)
    for doc in plan["doc_sections"]:
        header = read_first_n_lines(doc, 50)
        sections.append(f"## {doc}\n{header}")

    context_blob = "\n\n".join(sections)

    # Budget enforcement: truncate to ~4K tokens if too large
    if estimate_tokens(context_blob) > 4000:
        context_blob = truncate_to_budget(context_blob, 4000)

    return {"assembled_context": context_blob}
```

### Integration: Enforce Pipeline

Current flow:
```
FSM: setup → plan → capture_fr → judge → enforce_session → validate → ...
```

With context planner, the enforce graph becomes:

```yaml
nodes:
  plan_context:
    type: llm
    prompt: context-planner
    model: flash
    variables:
      task_description: "{state.fr_summary}"
      module_map: "{state.module_map}"
    state_key: context_plan

  assemble:
    type: python
    tool: context_assembler
    state_key: assembled_context

  enforce:
    type: copilot
    prompt: enforce-session
    variables:
      fr_path: "{state.fr_path}"
      worktree_dir: "{state.worktree_dir}"
      branch: "{state.branch}"
      codebase_context: "{state.assembled_context}"
    state_key: enforce_result
    timeout: 3600

edges:
  - from: START
    to: plan_context
  - from: plan_context
    to: assemble
  - from: assemble
    to: enforce
  - from: enforce
    to: END
```

The enforce prompt then receives pre-assembled context:

```yaml
user: |
  **Enforce.** Implement the feature request and make all tests pass.

  ## Codebase Context (pre-assembled)
  {{ codebase_context }}

  ## Process
  1. READ — Study {{ fr_path }} completely...
```

## Token Economics

| Metric | Without planner | With planner |
|--------|----------------|--------------|
| Orientation tool calls | 5-8 (grep, read, list) | 0 (pre-assembled) |
| Tokens on exploration | ~3000 | 0 |
| Context planner cost | 0 | ~700 tokens (~$0.001) |
| Assembled context cost | 0 | ~2000 tokens |
| First productive action | ~minute 3 | ~minute 0.5 |
| Orientation determinism | Non-deterministic per run | Consistent (same map → same plan) |

Net effect: fewer expensive tool calls in the main session, more deterministic behavior, faster time-to-first-commit.

## Implementation Variants

### Minimal (today, no new code)

Generate `reference/module-map.md` via script. Add `@reference/module-map.md` to CLAUDE.md. Static Tier 2 — every session gets the same map regardless of task.

### Medium (next sprint)

Add relevance classifier as pre-node in enforce graphs. Dynamic Tier 2 — context adapted per FR.

### Full (later)

Track which context selections correlated with successful vs failed enforce runs. Feed outcomes back to improve the classifier. Self-improving Tier 2.

## Alignment with Scripture

| Principle | How Context Planner Aligns |
|-----------|---------------------------|
| **Commandment 1** (Research before coding) | The planner IS research — an agent researching what the implementing agent needs |
| **Commandment 4** (Honor existing patterns) | Fits existing pattern: LLM node → python tool → copilot node (same as Philosopher graph) |
| **The One Law** (Normalize at boundary) | Normalizes codebase knowledge at the prompt boundary, before it enters the agent's context window |
| **Cure: spec_kill** | Cheapest bug prevented by correct upfront knowledge rather than guess-and-backtrack |
| **Trap: downstream_fix** | Instead of fixing orientation failures downstream, prevents them at entry |

## Open Questions (Seeds)

1. **Sufficiency of ast.parse():** Can the classifier reliably identify relevant files from function signatures alone? Or does it need richer signals — docstrings, type annotations, or cross-reference edges?

2. **Feedback loop:** Can we measure which context plans lead to successful enforcements? If yes, we can build a self-improving selector.

3. **Graph-of-graphs:** If the context planner is itself a YAMLGraph graph, can it plan context for other YAMLGraph graphs? Recursive applicability.

4. **Provider independence:** The module map is static YAML. The classifier can run on any model. The assembler is pure Python. This entire pattern is provider-independent — works with any LLM backend.

5. **Beyond code:** Could the same pattern provide context about *process*? E.g., "for this type of FR, previous successful implementations followed pattern X" — drawing from diary entries and past FRs.
