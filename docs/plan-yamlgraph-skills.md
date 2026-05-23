# Plan: YAMLGraph Skills — Dynamic Tool+Prompt Bundles for Agents

**Date:** 2026-05-22
**Origin:** FR-446 diary seed, conversation with Sami
**Status:** Exploration (not an FR yet)

## The Problem

Agent nodes currently bind tools statically at compile time:

```yaml
tools:
  run_ruff: { command: "ruff check {path}" }
  run_tests: { command: "pytest {path}" }
  run_bandit: { command: "bandit -r {path}" }
  git_log: { command: "git log --oneline -n {count}" }
  git_diff: { command: "git diff --stat HEAD~{commits}" }
  web_search: { type: websearch }

nodes:
  analyze:
    type: agent
    prompt: analyzer
    tools: [run_ruff, run_tests, run_bandit, git_log, git_diff, web_search]
    max_iterations: 12
```

**Every tool's description enters the system prompt.** With 8 tools (like `code-analysis`), that's 8 descriptions the LLM must read on every iteration — even when the task only needs 2. At 20+ tools this becomes a real context window cost, and the LLM starts making worse tool-selection decisions due to choice overload.

This mirrors the exact problem Copilot skills solve for editors: always-loaded knowledge vs on-demand knowledge.

## The Concept: Skills as Tool+Prompt Bundles

A **skill** is a reusable YAML file that bundles related tools with a prompt segment and optional schema:

```yaml
# skills/code-quality.yaml
name: code-quality
description: "Analyze code quality: linting, complexity, dead code"

tools:
  run_ruff:
    type: shell
    command: ruff check {path} --output-format=concise 2>&1
    description: "Run ruff linter"
  run_radon:
    type: shell
    command: radon cc {path} -a -s --min C 2>&1
    description: "Check cyclomatic complexity"
  run_vulture:
    type: shell
    command: vulture {path} --min-confidence 80 2>&1
    description: "Detect dead code"

prompt_segment: |
  You have code quality tools available:
  - run_ruff: Fast Python linter (style + correctness)
  - run_radon: Cyclomatic complexity checker (target: < 10)
  - run_vulture: Dead code detector

  Run all three and report findings by severity.
```

```yaml
# skills/security.yaml
name: security
description: "Security scanning and vulnerability detection"

tools:
  run_bandit:
    type: shell
    command: bandit -r {path} -ll -q 2>&1
    description: "Security vulnerability scanner"

prompt_segment: |
  You have security scanning tools. Run bandit and report
  any medium+ severity findings with remediation advice.
```

## Usage in Graph YAML

### Static skill loading (compile-time)

The simplest form — skills as a grouping/reuse mechanism:

```yaml
skills:
  - code-quality        # loads skills/code-quality.yaml
  - security            # loads skills/security.yaml

nodes:
  analyze:
    type: agent
    prompt: analyzer
    skills: [code-quality, security]   # tools + prompt segments merged
    max_iterations: 12
```

At compile time, the agent gets:
- Tools from both skills merged into its tool registry
- Prompt segments appended to its system prompt
- Equivalent to today's flat `tools:` list, but organized and reusable

### Dynamic skill loading (runtime)

The powerful form — skills selected based on state:

```yaml
skills:
  - code-quality
  - security
  - git-history
  - documentation

nodes:
  classify:
    type: router
    prompt: classify_task
    route_field: task_type
    routes:
      quality: analyze_quality
      security: analyze_security
      full: analyze_all

  analyze_quality:
    type: agent
    prompt: analyzer
    skills: [code-quality]          # Only quality tools loaded

  analyze_security:
    type: agent
    prompt: analyzer
    skills: [security]              # Only security tools loaded

  analyze_all:
    type: agent
    prompt: analyzer
    skills: [code-quality, security, git-history]  # Full toolset
```

### State-driven skill selection

```yaml
nodes:
  analyze:
    type: agent
    prompt: analyzer
    skills: "{state.required_skills}"   # List resolved from state
    max_iterations: 12
```

## How It Maps to Existing Architecture

### Compile Pipeline Impact

```
YAML → load_graph_config() → GraphConfig
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼             ▼
           build_state()   parse_tools()  compile_graph()
                                 │
                         ┌───────┴───────┐
                         ▼               ▼
                    tools: {}      skills: {}    ← NEW: skill registry
                         │               │
                         └───────┬───────┘
                                 ▼
                         merged tool set per agent node
```

### Key Extension Points

1. **Skill loader** — `yamlgraph/skills/loader.py`: Parse `skills/*.yaml` files, validate structure, build tool+prompt bundles. Analogous to `load_prompt()`.

2. **Agent node factory** — `yamlgraph/tools/agent.py`: `create_agent_node()` currently takes `tools: dict[str, ShellToolConfig]`. Extended to also take `skills: list[SkillConfig]`. Tools from skills are merged into the agent's tool registry. Prompt segments are prepended to the system prompt.

3. **Linter** — `yamlgraph/linter/patterns/agent.py`: Validate that referenced skills exist. Warn if agent has both `tools:` and `skills:` (which is fine but worth noting for clarity).

4. **Graph config model** — `yamlgraph/models/graph_config.py`: Add `skills:` as top-level key (parallel to `tools:`).

### What Doesn't Change

- Tool execution (`ShellToolConfig`, `PythonToolConfig`) — unchanged
- Tool binding (`build_langchain_tool`) — unchanged
- State management — unchanged
- Edge routing — unchanged

Skills are a **compile-time grouping mechanism** that merges into existing tool infrastructure. At runtime, the agent sees flat tools — no new runtime concept.

## Skill File Resolution

Analogous to prompt resolution:

1. If `skills_dir` specified: `{skills_dir}/{skill_name}.yaml`
2. If `prompts_relative: true`: `{graph_dir}/skills/{skill_name}.yaml`
3. Default: `skills/{skill_name}.yaml`

## Relationship to Copilot Skills

| Dimension | Copilot Skills (`.github/skills/`) | YAMLGraph Skills (`skills/`) |
|-----------|-----------------------------------|------------------------------|
| **Consumer** | VS Code / Copilot agent | YAMLGraph agent nodes |
| **Content** | Curated procedural docs | Tools + prompt segment + schema |
| **Loading** | Intent-matched by editor | Declared per agent node in graph YAML |
| **Format** | Markdown with YAML frontmatter | Pure YAML |
| **Purpose** | Reduce manual file reads | Reduce agent context bloat |

The same insight — **load knowledge on demand, not always** — applied at two different levels.

## Export: YAMLGraph Graph → Copilot Skill

The `yamlgraph skill export` command (CAP-142) already packages graphs as portable skills. With native skill support, the export could also:

1. Export a YAMLGraph skill as a Copilot skill (tool descriptions become the skill body)
2. Import a Copilot skill's knowledge as a YAMLGraph prompt segment

This creates a bidirectional bridge between IDE skills and agent skills.

## What This Is NOT

- **Not MCP.** MCP is a transport protocol for tools. Skills are a grouping/composition mechanism. A skill could *contain* MCP tools.
- **Not a new node type.** Skills don't execute. They're compile-time metadata that gets merged into existing node types.
- **Not dynamic at the LLM level.** The LLM doesn't "choose skills." The graph author declares which skills an agent has. (State-driven selection is graph logic, not LLM logic.)

## Open Questions

1. **Skill composition conflicts.** What if two skills define a tool with the same name? Options: (a) error, (b) last-wins, (c) namespace: `quality.run_ruff` vs `security.run_ruff`.

2. **Prompt segment ordering.** When multiple skills contribute prompt segments, what order? Options: (a) declaration order in `skills: [a, b, c]`, (b) alphabetical, (c) explicit `priority` field.

3. **Schema merging.** If a skill defines an output schema, does it merge with the node's prompt schema? Probably not — the node's prompt schema wins, and skill schemas are additive context only.

4. **Skill dependencies.** Should skills declare dependencies on other skills? (`security` requires `code-quality` for context). Probably not — keep it flat. The graph author composes.

5. **Built-in skills.** Ship common skills with YAMLGraph? `code-quality`, `git-analysis`, `web-research`? Or leave to users? Starting with zero built-ins is simpler.

## Estimated Effort

| Component | Effort |
|-----------|--------|
| Skill YAML schema + loader | 1 day |
| Agent node factory integration | 1 day |
| Linter rules (skill validation) | 0.5 day |
| Graph config model extension | 0.5 day |
| Demo + docs | 1 day |
| Tests | 1 day |
| **Total** | **5 days** |

## Research: LangChain/LangGraph Skills Ecosystem (2026-05-22)

**Finding: Skills are a first-class concept across the entire LangChain ecosystem.** This validates the direction.

### LangChain Multi-Agent Skills Pattern

Source: `docs.langchain.com/oss/python/langchain/multi-agent/skills.md`

LangChain defines skills as one of five multi-agent patterns (Router, Skills, Handoffs, Subagents, Custom Workflow). Key characteristics:

- **Prompt-driven specialization**: Skills are *primarily prompts*, not tools. This is the biggest divergence from our plan, which bundles tools+prompts.
- **Progressive disclosure**: The core pattern — load on demand, not upfront. Agent sees lightweight descriptions in system prompt, calls `load_skill("name")` tool to get full content.
- **`AgentMiddleware`**: A middleware class injects skill descriptions into the system prompt and registers the `load_skill` tool. This maps conceptually to YAMLGraph's compile-time skill merging.
- **State tracking**: Custom `AgentState` can track `skills_loaded: list[str]` — enabling tool constraints ("must load sales_analytics before using write_sql_query").
- **Hierarchical skills**: Skills can define sub-skills, creating nested progressive disclosure for large knowledge bases.

Implementation pattern:
```python
class Skill(TypedDict):
    name: str           # Unique identifier
    description: str    # 1-2 sentences (shown in system prompt)
    content: str        # Full instructions (loaded on demand)

@tool
def load_skill(skill_name: str) -> str:
    """Load full skill content into agent context."""
    ...

class SkillMiddleware(AgentMiddleware):
    tools = [load_skill]  # Registers tool automatically
    def wrap_model_call(self, request, handler):
        # Inject skill descriptions into system prompt
        ...
```

### Deep Agents Skills

Source: `docs.langchain.com/oss/python/deepagents/skills.md`

Deep Agents have a more concrete skills spec following [agentskills.io](https://agentskills.io/specification):

- **SKILL.md files** in named directories — YAML frontmatter for metadata, markdown body for instructions
- **Three-step agent behavior**: Match (description check) → Read (load full SKILL.md) → Execute (follow instructions, use assets)
- **Interpreter skills**: Skills can expose importable TypeScript/JavaScript modules via `module:` frontmatter — the agent can `import("@/skills/order-helpers")` for deterministic helpers
- **Source precedence**: `skills=["/a/", "/b/"]` — last wins for same-named skills
- **Subagent isolation**: Main agent skills invisible to subagents; custom subagents get their own `skills` parameter
- **Skills vs Memory**: Skills = task-specific on-demand knowledge; Memory (AGENTS.md) = always-loaded project context

SKILL.md format:
```markdown
---
name: langgraph-docs
description: Use for LangGraph documentation requests
module: index.ts       # Optional: importable code
allowed-tools: fetch_url
---
# langgraph-docs
## Instructions
1. Fetch the documentation index...
```

### LangSmith Platform Skills

Skills are a full CRUD resource in the LangSmith API:
- `POST /skills` — Create a skill with file tree
- `GET/PUT/DELETE /skills/{id}` — Full lifecycle management
- Context Hub for versioning and sharing skills across agents
- Fleet agents use skills as first-class capabilities

### Key Insight: Anthropic's Influence

LangChain's tutorial explicitly cites Anthropic's [Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) work:

> "Progressive disclosure was popularized by Anthropic as a technique for building scalable agent skills systems. This approach uses a three-level architecture (metadata → core content → detailed resources)."

This is the same pattern as Copilot skills: lightweight description → full SKILL.md → referenced assets.

### Implications for YAMLGraph

| Aspect | LangChain Approach | Our Plan | Recommendation |
|--------|-------------------|----------|----------------|
| **Core unit** | Prompt-centric (SKILL.md) | Tool+Prompt bundle | Keep tool bundling — it's our differentiator. LangChain skills are *just prompts* because their agents already have tool registries. YAMLGraph agents don't — tools come from YAML. |
| **Loading** | Runtime via `load_skill` tool call | Compile-time declaration | Support both: compile-time for static graphs, runtime load_skill for dynamic agents |
| **Format** | SKILL.md (markdown + YAML frontmatter) | Pure YAML | Consider supporting SKILL.md format for ecosystem compatibility, plus our native YAML format |
| **State tracking** | `skills_loaded` in agent state | Not planned | Add this — enables powerful patterns like conditional tool access |
| **Spec** | agentskills.io | Custom | Align with agentskills.io where possible — it's becoming a standard |
| **Middleware** | `AgentMiddleware` class | Compile-time merge | Our compile-time approach is simpler and avoids runtime overhead. Good. |

### Revised Design Considerations

1. **Dual format support**: Accept both `skills/code-quality.yaml` (our native, tool-bundling format) and `skills/code-quality/SKILL.md` (agentskills.io compatible, prompt-only). The loader detects which format a skill uses.

2. **Runtime `load_skill` tool**: Add a built-in `load_skill` tool that agents can use for dynamic progressive disclosure. This complements compile-time skill binding.

3. **State tracking**: Add `skills_loaded` to agent state when skills are loaded dynamically. Enable skill-gated tools.

4. **Prompt segment → progressive disclosure**: For large skills, don't dump the entire prompt_segment into the system prompt. Instead, provide a summary and let the agent call `load_skill` for details. This is the three-level architecture: description → summary → full content.

## Next Step

If this direction feels right, submit to `.chaplain/inbox/` as a proposal. The pipeline will generate a proper FR with acceptance criteria and run it through Judge.
