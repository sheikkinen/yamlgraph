# Reflection: Agent SDK Research → Context Building → Existing Capabilities

**Date:** 2026-05-05
**Author:** Philosopher session (Copilot + human)
**Scope:** Agent SDK feasibility, context building problem, `type: agent` rediscovery

## Trap

`working_system_inertia` — inverted. We were so focused on what the copilot CLI *lacks* (custom tools, hooks, structured output) that we reached for an external framework (Claude Agent SDK) instead of checking what YAMLGraph already provides. The `type: agent` node has had LangChain tool-calling loop support since CAP-05, with shell and python tools declared in YAML.

## What Happened

### Thread 1: Agent SDK Research

Investigated the Claude Agent SDK (v0.1.73). Discovered it's a Python wrapper around a **bundled opaque Claude Code binary** — subprocess transport only, locked to Anthropic, no model switching. This invalidated the "no CLI dependency" claim; it just bundles a *different* CLI binary.

Scripture reflection caught the `framework_costume` trap before it could take hold: don't wrap deterministic pipelines in an autonomous agent framework.

### Thread 2: Spike Landed (FR-329, PR #331)

Scoped correctly: standalone `examples/agent-sdk-planner/plan.py` (389 lines) with two custom tools (`next_fr_number`, `read_fr_template`) and a `PostToolUse` audit hook. Chaplain enforced it, PR merged.

The spike was immediately dog-fooded: `python examples/agent-sdk-planner/plan.py .chaplain/failed/gh-308.md` ran successfully and produced FR-330 — a real bug fix proposal about stale branch cleanup on retry.

### Thread 3: Context Building Problem

The deeper realization: the tool doesn't matter (copilot CLI vs Agent SDK vs anything). The real problem is that every agent sees the codebase blind. Research across Aider (tree-sitter repo maps), Claude Code (CLAUDE.md + auto memory), and YAMLGraph's current approach revealed a three-tier model:

- **Tier 1** (static, always loaded): HOW to behave — CLAUDE.md, copilot-instructions.md (~630 lines)
- **Tier 2** (task-adaptive): WHERE things are for THIS task — nobody does this well
- **Tier 3** (runtime, on-demand): WHAT the code says — grep/read at runtime

Proposed the **Context Planner**: module map (generated from `ast.parse()`) + relevance classifier (cheap LLM call) + deterministic assembler. Filed issue #330 for the minimal variant (static module map).

### Thread 4: `type: agent` Rediscovery

Human feedback: "there is agent keyword in yamlgraph. check." Found `type: agent` in `yamlgraph/tools/agent.py` — a full LangChain tool-calling loop that already supports python + shell tools, provider-independent, max_iterations, tool_results_key. The spike's 389 lines reimplemented what YAMLGraph already provides.

## Root Cause

The spike reached for Agent SDK because copilot CLI can't use custom tools. But the answer was already in the codebase: `type: agent` gives an LLM access to python tools via LangChain's StructuredTool. No external binary needed. Provider-independent.

The root cause was **searching outward before searching inward** — violating Commandment 1 (research before coding) at the framework level. We researched Agent SDK extensively but didn't audit our own node type registry.

## What Worked

- Scripture traps (`framework_costume`, `working_system_inertia`) caught two wrong turns before they became code
- Scoping the spike to `examples/` kept the runtime surface immutable — even though the spike proved unnecessary, it caused no harm
- The spike DID prove that `next_fr_number` and `read_fr_template` eliminate real failure modes (FR number collisions, template hallucination)
- Human feedback ("check existing") course-corrected before a feature request was filed for the wrong integration

## Revised Recommendation

| Chaplain Step | Current | Recommended | Why |
|---|---|---|---|
| **plan** | `type: copilot` (cli) | `type: agent` with python tools | `next_fr_number` + `read_fr_template` eliminate bugs. Provider-independent. |
| **judge** | `type: copilot` (cli) | Keep as-is | Simple prompt→verdict. No tools needed. |
| **enforce** | `type: copilot` (cli) | Keep as-is | Needs full IDE toolset (read/write/bash). Only copilot provides this. |
| **validate** | `type: copilot` (cli) | Keep as-is | Same — needs file editing + terminal. |
| **sanity** | `type: copilot` (cli) | Keep as-is | Reads code + writes diary. Needs file access. |

Agent SDK: **deferred**. The only unique value (PostToolUse hooks, budget control) is nice-to-have, not blocking. The plan step doesn't need it; the enforce step needs IDE tools that both copilot CLI and Agent SDK provide equivalently.

## Insight

The session followed a natural narrowing:

```
Agent SDK (wide)
  → framework_costume trap → scope to spike
    → spike landed → tools proven
      → type: agent exists → Agent SDK unnecessary for plan step
        → real value = two Python functions + static module map
```

A 389-line spike and a full research session distilled to: **two 10-line Python functions and a generated module map**. The cheapest code is unwritten code (Commandment 1). The spike's value was not the code — it was the proof that the problem was already solvable with existing infrastructure.

## Seed

The `type: agent` node uses LangChain's tool-calling protocol (in-process). The `type: copilot` node uses subprocess stdout. These are incompatible tool contracts. What would a **unified tool protocol** look like — where the same Python tool declared in the graph's `tools:` section is callable from `type: agent` (LangChain StructuredTool), `type: copilot` (injected into prompt context), and hypothetically MCP (registered as MCP tool)? The tools are declared once; the transport adapts. This would make the plan step's `next_fr_number` available to the enforce step's copilot agent without duplicating the function.
