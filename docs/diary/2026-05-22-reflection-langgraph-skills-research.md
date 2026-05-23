# Diary: LangGraph Skills Research — Progressive Disclosure as Industry Pattern

**Date:** 2026-05-22
**Context:** Research on LangChain/LangGraph/Deep Agents skills ecosystem to validate YAMLGraph skills plan
**Source:** `docs/plan-yamlgraph-skills.md`

## What Happened

Crawled `docs.langchain.com/llms.txt` (the documentation index — itself a progressive disclosure artifact) and traced three distinct "skills" implementations across the LangChain ecosystem: the multi-agent skills pattern in LangChain Python, the Deep Agents skills spec following `agentskills.io`, and the LangSmith platform CRUD API. All three converge on the same core insight: load knowledge on demand, not upfront.

## Insight: Skills Are Prompts, Not Tools

The most important finding is the gap between our plan and the ecosystem direction. LangChain skills are *primarily prompts*. A skill is a `Skill(TypedDict)` with `name`, `description`, and `content` — all strings, no tool bindings. The agent gets descriptions in its system prompt and calls `load_skill("name")` to retrieve full content as a ToolMessage.

Our plan bundles tools+prompts in a single YAML file. This is actually a stronger abstraction — because YAMLGraph agents get their tools from YAML declarations, not from Python imports. In LangChain's world, tools already exist in a registry; skills just add context about *when to use them*. In YAMLGraph's world, tools are *defined* in the graph YAML, so bundling them with their usage instructions is natural.

**Trap identified: `framework_costume`.** If we adopted LangChain's prompt-only skills pattern, we'd be wearing their abstraction without using the features that justify it. Our tool+prompt bundle is the right fit for YAML-first architecture.

## Insight: Three-Level Architecture Is the Pattern

Anthropic's original skills work (cited by LangChain) defines a three-level progressive disclosure:

1. **Metadata** (always visible): name + 1-2 sentence description
2. **Core content** (loaded on match): full SKILL.md instructions
3. **Detailed resources** (loaded on need): scripts, templates, reference docs

This maps cleanly to our plan:
1. `description:` field in skill YAML → shown in system prompt
2. `prompt_segment:` → loaded when skill is bound to agent
3. `tools:` + referenced files → available during execution

The key realization: for *large* skills, even level 2 should be lazy. Don't dump the entire prompt_segment into the system prompt at compile time. Instead, provide a summary and let the agent `load_skill()` for details. This is where compile-time and runtime approaches meet.

## Insight: agentskills.io as Emerging Standard

Deep Agents follows the [Agent Skills specification](https://agentskills.io/specification). Key constraints worth adopting:

- `description` truncated to 1024 characters (forces discipline)
- `SKILL.md` must be under 10 MB (sanity bound)
- `module:` frontmatter field for importable code
- `allowed-tools:` whitelist — not just "these tools exist" but "only these tools should be used"

The `allowed-tools` pattern is interesting for YAMLGraph. A skill could declare not just what tools it provides, but restrict which other tools the agent should use while that skill's context is active. This is a form of context-dependent capability narrowing — the opposite of our current "merge everything" approach.

## Trap: `working_system_inertia`

Our existing compile-time approach works well for static graphs. The temptation is to declare victory and ship only compile-time skills. But the research shows that runtime `load_skill()` enables patterns that compile-time can't: state-driven skill selection, skill-gated tool access, and progressive disclosure within a single agent turn.

The cost is one additional tool call per skill load (~100-500ms). For long-running agent tasks (code analysis, report generation), this is noise. For latency-sensitive voice or chat agents, it matters. Supporting both modes is the right answer.

## Trap: `continuation_bias`

The research almost derailed into building an implementation plan. The LangChain tutorials are so detailed (complete runnable scripts, middleware patterns, state management) that the pull to "just implement this" was strong. But the task was research and reflection, not implementation. The plan document was updated with findings; the implementation belongs in an FR submitted through the chaplain.

## Revised Mental Model

```
                      LangChain Skills            YAMLGraph Skills
                      ─────────────────           ──────────────────
Core unit:            Prompt text                 Tool+Prompt YAML bundle
Loading:              Runtime (load_skill tool)   Compile-time (graph YAML)
                                                  + Runtime (load_skill tool)
Format:               SKILL.md (markdown)         skill.yaml (native)
                                                  + SKILL.md (compat)
State tracking:       AgentState.skills_loaded    graph state (planned)
Ecosystem spec:       agentskills.io              agentskills.io (aligned)
Progressive levels:   3 (meta → content → assets) 3 (description → segment → tools)
```

Our advantage: tools and prompts live in the same declarative format, so skills can be a *complete* capability unit — not just instructions, but the actual tools to execute them.

Their advantage: runtime flexibility. An agent can decide *during execution* which skills it needs. Our compile-time approach locks this at graph-definition time.

Recommendation: support both. Compile-time for the 80% case. Runtime `load_skill` for dynamic agents.

## Seed

**Seed:** The `agentskills.io` spec and LangChain's `SKILL.md` format create an interesting bidirectional bridge opportunity. `yamlgraph skill export` (CAP-142) already exports graphs as Copilot skills. Could it also export YAMLGraph skills as agentskills.io-compatible SKILL.md directories — making YAMLGraph skills portable to Deep Agents, Claude Code, and any other agent following the spec? The inverse is equally interesting: `yamlgraph skill import` could consume a SKILL.md directory and generate a native skill.yaml, wrapping any `allowed-tools` as shell or python tool definitions. This makes YAMLGraph a skills *compiler* — consuming portable specs and emitting optimized agent-specific bundles.
